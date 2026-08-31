"""
otp_service.py — secure one-time verification codes.

Guarantees:
  * Codes are generated with `secrets` (cryptographically secure).
  * Only an Argon2 HASH of the code is stored — the plaintext code exists
    solely inside the outgoing email.
  * Codes expire (default 10 minutes) and are single-use.
  * Each code allows at most OTP_MAX_ATTEMPTS wrong guesses before it is
    invalidated (brute-force protection).
  * Old codes for the same (user, purpose) are invalidated when a new one
    is issued.
"""

from __future__ import annotations

import datetime as dt
import secrets
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from .. import config
from ..database import get_connection

_ph = PasswordHasher(time_cost=2, memory_cost=32768, parallelism=4)

VALID_PURPOSES = {"login", "email_verification", "password_reset"}


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _iso(dt_value: dt.datetime) -> str:
    return dt_value.isoformat()


def generate_otp(user_id: str, email: str, purpose: str) -> tuple[str, int]:
    """Create a new OTP for (user, purpose). Returns (code, ttl_minutes)."""
    if purpose not in VALID_PURPOSES:
        raise ValueError(f"Unsupported OTP purpose: {purpose}")

    code = "".join(secrets.choice("0123456789") for _ in range(config.OTP_LENGTH))
    expires_at = _utcnow() + dt.timedelta(minutes=config.OTP_TTL_MINUTES)

    conn = get_connection()
    try:
        # Invalidate previous active codes for the same user + purpose.
        conn.execute(
            """
            UPDATE otp_codes
               SET used = 1
             WHERE user_id = ? AND purpose = ? AND used = 0
            """,
            (user_id, purpose),
        )
        conn.execute(
            """
            INSERT INTO otp_codes (user_id, email, purpose, code_hash, expires_at, attempts, used, created_at)
            VALUES (?, ?, ?, ?, ?, 0, 0, ?)
            """,
            (user_id, email, purpose, _ph.hash(code), _iso(expires_at), _iso(_utcnow())),
        )
        conn.commit()
    finally:
        conn.close()
    return code, config.OTP_TTL_MINUTES


def verify_otp(user_id: str, purpose: str, code: str) -> tuple[bool, str]:
    """Verify a submitted code.

    Returns (ok, message). Increments the attempt counter on every wrong
    guess; the code dies after OTP_MAX_ATTEMPTS failures or on expiry.
    """
    code = (code or "").strip()
    if not code or not code.isdigit() or len(code) != config.OTP_LENGTH:
        return False, f"Enter the complete {config.OTP_LENGTH}-digit verification code."

    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id, code_hash, expires_at, attempts, used
              FROM otp_codes
             WHERE user_id = ? AND purpose = ? AND used = 0
             ORDER BY id DESC
             LIMIT 1
            """,
            (user_id, purpose),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return False, "No active verification code found. Please request a new one."

    try:
        expires = dt.datetime.fromisoformat(row["expires_at"])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return False, "Stored verification code is corrupt. Please request a new one."

    if expires < _utcnow():
        _mark_used(user_id, purpose)
        return False, "This verification code has expired. Please request a new one."

    if row["attempts"] >= config.OTP_MAX_ATTEMPTS:
        _mark_used(user_id, purpose)
        return False, "Too many incorrect attempts. Please request a new code."

    # Constant-ish time verification of the Argon2 hash.
    try:
        matches = _ph.verify(row["code_hash"], code)
    except (VerifyMismatchError, InvalidHashError, ValueError):
        matches = False

    if not matches:
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?",
                (row["id"],),
            )
            conn.commit()
        finally:
            conn.close()
        remaining = config.OTP_MAX_ATTEMPTS - (row["attempts"] + 1)
        if remaining <= 0:
            return False, "Too many incorrect attempts. Please request a new code."
        return False, f"Incorrect verification code. {remaining} attempt(s) remaining."

    # Success → single-use: burn the code.
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE otp_codes SET used = 1, attempts = attempts + 1 WHERE id = ?",
            (row["id"],),
        )
        conn.commit()
    finally:
        conn.close()
    return True, "Verification successful."


def _mark_used(user_id: str, purpose: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE otp_codes SET used = 1 WHERE user_id = ? AND purpose = ? AND used = 0",
            (user_id, purpose),
        )
        conn.commit()
    finally:
        conn.close()


def purge_expired() -> int:
    """Delete expired/burned codes older than 24h. Returns rows removed."""
    cutoff = _iso(_utcnow() - dt.timedelta(hours=24))
    conn = get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM otp_codes WHERE expires_at < ? OR (used = 1 AND created_at < ?)",
            (cutoff, cutoff),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def latest_code_expires_in_seconds(user_id: str, purpose: str) -> Optional[int]:
    """Seconds until the newest active code expires (for UI countdowns)."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT expires_at FROM otp_codes
             WHERE user_id = ? AND purpose = ? AND used = 0
             ORDER BY id DESC LIMIT 1
            """,
            (user_id, purpose),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    try:
        expires = dt.datetime.fromisoformat(row["expires_at"])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=dt.timezone.utc)
        remaining = (expires - _utcnow()).total_seconds()
        return max(int(remaining), 0)
    except ValueError:
        return None
