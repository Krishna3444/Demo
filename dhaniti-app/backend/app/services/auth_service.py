"""
auth_service.py — user lifecycle logic (register / login / passwords / profile).

Password policy, legacy-hash migration, and email↔user lookups live here so
the routes stay thin.
"""

from __future__ import annotations

import datetime as dt
import re
import uuid
from typing import Optional

from .. import config
from ..database import get_connection
from ..security.authentication import (
    create_access_token,
    get_user_by_email,
    hash_password,
    needs_rehash,
    public_user,
    revoke_session,
    verify_password,
)
from . import email_service, otp_service

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def validate_email(email: str) -> Optional[str]:
    email = (email or "").strip().lower()
    if not email:
        return "Email address is required."
    if len(email) > 254 or not EMAIL_RE.match(email):
        return "Invalid email address."
    return None


def validate_password(password: str) -> Optional[str]:
    if not password or not isinstance(password, str):
        return "Password is required."
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if len(password) > 128:
        return "Password must be at most 128 characters long."
    if not re.search(r"[A-Za-z]", password):
        return "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one number."
    return None


def validate_name(name: str) -> Optional[str]:
    name = (name or "").strip()
    if not name:
        return "Name is required."
    if len(name) < 2:
        return "Name must be at least 2 characters long."
    if len(name) > 120:
        return "Name must be at most 120 characters long."
    return None


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #
def register_user(name: str, email: str, password: str, role: str = "Credit Analyst") -> dict:
    """Create an unverified user and issue an email-verification OTP."""
    email = email.strip().lower()
    existing = get_user_by_email(email)
    if existing:
        # Generic-ish message: do not confirm whether the address exists.
        raise ValueError("An account with this email already exists. Try signing in instead.")

    user_id = f"USR-{uuid.uuid4().hex[:8].upper()}"
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO users (user_id, email, name, avatar_url, role, password_hash,
                               salt, oauth_provider, oauth_id, is_verified, created_at, updated_at)
            VALUES (?, ?, ?, NULL, ?, ?, NULL, 'local', NULL, 0, ?, ?)
            """,
            (user_id, email, name.strip(), role, hash_password(password), now, now),
        )
        conn.commit()
    finally:
        conn.close()

    code, ttl = otp_service.generate_otp(user_id, email, "email_verification")
    email_service.send_otp_email(email, code, "email_verification", ttl)
    email_service.send_welcome_email(email, name.strip())

    user = get_user_by_email(email)
    return {"user": public_user(user), "ttl_minutes": ttl}


# --------------------------------------------------------------------------- #
# Login
# --------------------------------------------------------------------------- #
def authenticate(email_or_username: str, password: str, remember: bool = False) -> dict:
    """Verify credentials. Transparently upgrades legacy SHA-256 hashes."""
    identifier = (email_or_username or "").strip().lower()
    user = get_user_by_email(identifier)

    # Allow the local part of the email as a username convenience ONLY when
    # it maps to exactly one user (keeps the old "admin" style working).
    if user is None and identifier and "@" not in identifier:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM users WHERE lower(substr(email, 1, instr(email, '@') - 1)) = ?",
                (identifier,),
            ).fetchall()
        finally:
            conn.close()
        if rows and len(rows) == 1:
            user = dict(rows[0])

    if user is None or not verify_password(password, user.get("password_hash"), user.get("salt")):
        # Same message for unknown user and wrong password (no enumeration).
        raise ValueError("Invalid email or password.")

    if not user.get("is_verified"):
        # Re-issue a verification code and tell the UI to verify first.
        code, ttl = otp_service.generate_otp(user["user_id"], user["email"], "email_verification")
        email_service.send_otp_email(user["email"], code, "email_verification", ttl)
        raise UnverifiedEmailError(user["email"])

    # Transparent hash upgrade (legacy SHA-256 → Argon2).
    if needs_rehash(user.get("password_hash")):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE users SET password_hash = ?, salt = NULL, updated_at = ? WHERE user_id = ?",
                (hash_password(password), dt.datetime.now(dt.timezone.utc).isoformat(), user["user_id"]),
            )
            conn.commit()
        finally:
            conn.close()

    token, _ = create_access_token(user["user_id"], remember=remember)
    touch_last_login(user["user_id"])
    user = get_user_by_id_or_raise(user["user_id"])
    return {"token": token, "user": public_user(user)}


class UnverifiedEmailError(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__("Email not verified")


def get_user_by_id_or_raise(user_id: str) -> dict:
    from ..security.authentication import get_user_by_id

    user = get_user_by_id(user_id)
    if user is None:
        raise ValueError("User no longer exists.")
    return user


def touch_last_login(user_id: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET last_login_at = ? WHERE user_id = ?",
            (dt.datetime.now(dt.timezone.utc).isoformat(), user_id),
        )
        conn.commit()
    finally:
        conn.close()


def logout(token: str) -> bool:
    return revoke_session(token)


# --------------------------------------------------------------------------- #
# OTP login
# --------------------------------------------------------------------------- #
def send_login_otp(email: str, purpose: str = "login") -> dict:
    """Issue an OTP to an existing account (login or password-reset flows)."""
    email = (email or "").strip().lower()
    user = get_user_by_email(email)
    # Always answer identically — never reveal whether the email exists.
    generic = {
        "message": "If an account exists for that email, a verification code has been sent.",
        "expiresInMinutes": config.OTP_TTL_MINUTES,
    }
    if user is None:
        return generic

    purpose = purpose if purpose in ("login", "password_reset") else "login"
    code, ttl = otp_service.generate_otp(user["user_id"], user["email"], purpose)
    email_service.send_otp_email(user["email"], code, purpose, ttl)
    return generic


def verify_otp_and_issue_session(email: str, code: str, purpose: str, remember: bool = False) -> dict:
    """Verify an OTP; for login/email_verification purposes, sign the user in."""
    email = (email or "").strip().lower()
    user = get_user_by_email(email)
    if user is None:
        raise ValueError("Invalid verification code.")

    ok, message = otp_service.verify_otp(user["user_id"], purpose, code)
    if not ok:
        raise ValueError(message)

    if purpose == "email_verification":
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE users SET is_verified = 1, updated_at = ? WHERE user_id = ?",
                (dt.datetime.now(dt.timezone.utc).isoformat(), user["user_id"]),
            )
            conn.commit()
        finally:
            conn.close()

    token, _ = create_access_token(user["user_id"], remember=remember)
    touch_last_login(user["user_id"])
    user = get_user_by_id_or_raise(user["user_id"])
    return {"token": token, "user": public_user(user)}


def verify_reset_otp(email: str, code: str) -> str:
    """Verify the password-reset OTP and return a short-lived reset token."""
    email = (email or "").strip().lower()
    user = get_user_by_email(email)
    if user is None:
        raise ValueError("Invalid verification code.")
    ok, message = otp_service.verify_otp(user["user_id"], "password_reset", code)
    if not ok:
        raise ValueError(message)
    token, _ = create_access_token(
        user["user_id"], token_type="reset", ttl_minutes=config.RESET_TOKEN_TTL_MINUTES
    )
    return token


def reset_password(reset_token: str, new_password: str) -> None:
    """Set a new password using a reset token issued after OTP verification."""
    from ..security.authentication import decode_token

    err = validate_password(new_password)
    if err:
        raise ValueError(err)
    payload = decode_token(reset_token, expected_type="reset")
    if payload is None:
        raise ValueError("Reset link is invalid or has expired. Please start again.")
    user_id = payload.get("sub", "")
    user = get_user_by_id_or_raise(user_id)
    if verify_password(new_password, user.get("password_hash"), user.get("salt")):
        raise ValueError("New password must be different from your current password.")
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = NULL, is_verified = 1, updated_at = ? WHERE user_id = ?",
            (hash_password(new_password), dt.datetime.now(dt.timezone.utc).isoformat(), user_id),
        )
        # Security: kill every active session after a password change.
        conn.execute(
            "UPDATE sessions SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
            (dt.datetime.now(dt.timezone.utc).isoformat(), user_id),
        )
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Profile
# --------------------------------------------------------------------------- #
def update_profile(user_id: str, name: Optional[str] = None, avatar_url: Optional[str] = None) -> dict:
    """Update the signed-in user's profile fields."""
    user = get_user_by_id_or_raise(user_id)
    updates: list[tuple[str, object]] = []
    if name is not None:
        err = validate_name(name)
        if err:
            raise ValueError(err)
        updates.append(("name", name.strip()))
    if avatar_url is not None:
        avatar_url = avatar_url.strip()
        if avatar_url and not avatar_url.startswith(("http://", "https://")):
            raise ValueError("Avatar URL must start with http:// or https://.")
        if len(avatar_url) > 500:
            raise ValueError("Avatar URL is too long.")
        updates.append(("avatar_url", avatar_url or None))
    if updates:
        sets = ", ".join(f"{field} = ?" for field, _ in updates)
        values = [value for _, value in updates]
        conn = get_connection()
        try:
            conn.execute(
                f"UPDATE users SET {sets}, updated_at = ? WHERE user_id = ?",
                (*values, dt.datetime.now(dt.timezone.utc).isoformat(), user_id),
            )
            conn.commit()
        finally:
            conn.close()
    return public_user(get_user_by_id_or_raise(user_id))


def change_password(user_id: str, current_password: str, new_password: str) -> None:
    user = get_user_by_id_or_raise(user_id)
    if not verify_password(current_password, user.get("password_hash"), user.get("salt")):
        raise ValueError("Current password is incorrect.")
    err = validate_password(new_password)
    if err:
        raise ValueError(err)
    if verify_password(new_password, user.get("password_hash"), user.get("salt")):
        raise ValueError("New password must be different from your current password.")
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = NULL, updated_at = ? WHERE user_id = ?",
            (hash_password(new_password), dt.datetime.now(dt.timezone.utc).isoformat(), user_id),
        )
        conn.commit()
    finally:
        conn.close()
