"""
authentication.py — password hashing, JWT session tokens, and RBAC guards.

Security properties:
  * Passwords are hashed with Argon2id (argon2-cffi).
  * Legacy SHA-256(salt+password) hashes from the earlier prototype are
    still verifiable; on successful login the hash is transparently
    upgraded to Argon2 (no user action required, no data loss).
  * JWTs reference a server-side `sessions` row (sha256(token)); sessions
    can be revoked at logout and expire server-side as well as in the JWT.
  * Roles: "Credit Analyst" is read-only; Admin/Underwriter/Risk Officer
    may create/update/delete. DELETE is further restricted to Admin roles.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import uuid
from typing import Any, Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .. import config
from ..database import get_connection

# --------------------------------------------------------------------------- #
# Password hashing
# --------------------------------------------------------------------------- #
_ph = PasswordHasher(
    time_cost=3,       # iterations
    memory_cost=65536, # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash a password with Argon2id."""
    return _ph.hash(password)


def _legacy_sha256(password: str, salt: str) -> str:
    """The SHA-256(salt + password) scheme used by the earlier prototype."""
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: Optional[str], salt: Optional[str]) -> bool:
    """Verify a password against an Argon2 hash (or legacy SHA-256 hash)."""
    if not password or not password_hash:
        return False
    if password_hash.startswith("$argon2"):
        try:
            return _ph.verify(password_hash, password)
        except (VerifyMismatchError, InvalidHashError, ValueError):
            return False
    # Legacy scheme
    if salt:
        return hmac.compare_digest(password_hash, _legacy_sha256(password, salt))
    return False


def needs_rehash(password_hash: Optional[str]) -> bool:
    """True when the stored hash is legacy SHA-256 (needs Argon2 upgrade)."""
    return bool(password_hash) and not password_hash.startswith("$argon2")


# --------------------------------------------------------------------------- #
# Token helpers
# --------------------------------------------------------------------------- #
def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    user_id: str,
    *,
    remember: bool = False,
    token_type: str = "access",
    ttl_minutes: Optional[int] = None,
) -> tuple[str, dt.datetime]:
    """Create a signed JWT for `user_id` and persist its session row.

    Returns (token, expires_at). For token_type == "access" a `sessions`
    row is created so the token can be revoked at logout.
    """
    hours = config.JWT_TTL_REMEMBER_HOURS if remember else config.JWT_TTL_HOURS
    if ttl_minutes is not None:
        expires_at = _utcnow() + dt.timedelta(minutes=ttl_minutes)
    else:
        expires_at = _utcnow() + dt.timedelta(hours=hours)
    payload = {
        "sub": user_id,
        "jti": uuid.uuid4().hex,
        "type": token_type,
        "iat": int(_utcnow().timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    if token_type == "access":
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO sessions (user_id, token_hash, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, _token_hash(token), expires_at.isoformat(), _utcnow().isoformat()),
            )
            conn.commit()
        finally:
            conn.close()
    return token, expires_at


def decode_token(token: str, expected_type: str = "access") -> Optional[dict]:
    """Decode + signature-check a JWT. Returns the payload or None."""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload


def revoke_session(token: str) -> bool:
    """Mark the session row for `token` as revoked (logout)."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE sessions SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
            (_utcnow().isoformat(), _token_hash(token)),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# User helpers
# --------------------------------------------------------------------------- #
def get_user_by_id(user_id: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def public_user(user: dict) -> dict:
    """Serialise a user row for API responses (never leaks hashes).

    Keys are camelCase to match the rest of the API contract consumed by
    the React frontend (currentUser.userId, currentUser.avatarUrl, ...).
    """
    return {
        "userId": user.get("user_id"),
        "email": user.get("email"),
        "name": user.get("name"),
        "avatarUrl": user.get("avatar_url"),
        "role": user.get("role"),
        "oauthProvider": user.get("oauth_provider"),
        "isVerified": bool(user.get("is_verified")),
        "hasPassword": bool(user.get("password_hash")),
    }


def user_session_valid(token: str) -> Optional[dict]:
    """Validate a full access token: JWT signature + server-side session."""
    payload = decode_token(token, expected_type="access")
    if not payload:
        return None
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_id, expires_at, revoked_at FROM sessions WHERE token_hash = ?",
            (_token_hash(token),),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        # Token signed by us but no session row (e.g. DB reset) → invalid.
        return None
    if row["revoked_at"] is not None:
        return None
    try:
        expires = dt.datetime.fromisoformat(row["expires_at"])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=dt.timezone.utc)
        if expires < _utcnow():
            return None
    except ValueError:
        return None
    return payload


# --------------------------------------------------------------------------- #
# FastAPI dependencies
# --------------------------------------------------------------------------- #
_bearer_scheme = HTTPBearer(auto_error=False, description="JWT access token")


def _extract_token(request: Request, credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    """Bearer header first; fall back to ?token= query for download links."""
    if credentials and credentials.credentials:
        return credentials.credentials
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    qp_token = request.query_params.get("token")
    return qp_token or None


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict:
    """Require a valid, non-revoked session. Returns the user row."""
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    payload = user_session_valid(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please sign in again.")
    request.state.token = token
    request.state.token_payload = payload
    user = get_user_by_id(payload.get("sub", ""))
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[dict]:
    token = _extract_token(request, credentials)
    if not token:
        return None
    payload = user_session_valid(token)
    if not payload:
        return None
    request.state.token = token
    return get_user_by_id(payload.get("sub", ""))


def require_write_role(user: dict = Depends(get_current_user)) -> dict:
    """Write operations (create/update/delete) are denied to read-only roles.

    Role model (matches the documented demo setup):
      * Credit Analyst → read-only access to the portfolio
      * Underwriter / Risk Officer / Admin → full CRUD access
    """
    if user.get("role") in config.READ_ONLY_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Your role is read-only. You need Underwriter, Risk Officer or Admin permissions to modify records.",
        )
    return user


def client_ip(request: Request) -> str:
    """Best-effort client IP (proxy-aware)."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
