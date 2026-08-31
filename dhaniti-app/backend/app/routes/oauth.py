"""
routes/oauth.py — REAL OAuth 2.0 login (Google + GitHub).

Flow (Google shown; GitHub is identical in shape):

    React login page
        └─ GET /auth/google                      → 302 to accounts.google.com
              └─ user authorizes
                    └─ GET /auth/google/callback?code&state
                          ├─ state validated (CSRF protection)
                          ├─ code exchanged for an access token (server-side)
                          ├─ provider userinfo fetched
                          ├─ user found/created in SQLite (users table)
                          ├─ revocable session JWT created
                          └─ 302 to FRONTEND/oauth/callback?code=<one-time-code>
                                └─ POST /api/auth/oauth/exchange {code}
                                      └─ {token, user} → React dashboard

Security properties:
  * Client secrets NEVER reach the browser; they live in env vars.
  * `state` is random, server-issued, single-use and expiring (CSRF guard).
  * The session JWT is never placed in a redirect URL — the browser only
    receives a 60-second single-use exchange code.
  * Unconfigured providers return a clear 503 (never a fake success).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import secrets
import threading
from typing import Optional
from urllib.parse import quote, urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from .. import config
from ..database import get_connection
from ..security.authentication import (
    create_access_token,
    get_user_by_email,
    public_user,
    decode_token,
)
from ..services import auth_service

router = APIRouter(tags=["OAuth"])

# --------------------------------------------------------------------------- #
# In-memory OAuth state store (CSRF protection)
# --------------------------------------------------------------------------- #
_states: dict[str, float] = {}
_states_lock = threading.Lock()
_STATE_SWEEP_INTERVAL = 50


def _new_state() -> str:
    state = secrets.token_urlsafe(32)
    now = dt.datetime.now(dt.timezone.utc).timestamp()
    with _states_lock:
        # Opportunistic cleanup.
        if len(_states) % _STATE_SWEEP_INTERVAL == 0:
            stale = [k for k, v in _states.items() if now - v > config.OAUTH_STATE_TTL_SECONDS]
            for key in stale:
                _states.pop(key, None)
        _states[state] = now
    return state


def _consume_state(state: Optional[str]) -> bool:
    if not state:
        return False
    with _states_lock:
        issued_at = _states.pop(state, None)
    if issued_at is None:
        return False
    age = dt.datetime.now(dt.timezone.utc).timestamp() - issued_at
    return age <= config.OAUTH_STATE_TTL_SECONDS


# --------------------------------------------------------------------------- #
# One-time exchange codes (short-lived, hashed at rest)
# --------------------------------------------------------------------------- #
def _issue_auth_code(user_id: str) -> str:
    code = secrets.token_urlsafe(32)
    expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=config.AUTH_CODE_TTL_SECONDS)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO auth_codes (code_hash, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (
                hashlib.sha256(code.encode()).hexdigest(),
                user_id,
                expires_at.isoformat(),
                dt.datetime.now(dt.timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return code


def _consume_auth_code(code: str) -> Optional[str]:
    code_hash = hashlib.sha256((code or "").encode()).hexdigest()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_id, expires_at, used_at FROM auth_codes WHERE code_hash = ?",
            (code_hash,),
        ).fetchone()
        if row is None or row["used_at"] is not None:
            return None
        try:
            expires = dt.datetime.fromisoformat(row["expires_at"])
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=dt.timezone.utc)
            if expires < dt.datetime.now(dt.timezone.utc):
                return None
        except ValueError:
            return None
        conn.execute(
            "UPDATE auth_codes SET used_at = ? WHERE code_hash = ?",
            (dt.datetime.now(dt.timezone.utc).isoformat(), code_hash),
        )
        conn.commit()
        return row["user_id"]
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Provider availability
# --------------------------------------------------------------------------- #
def provider_status() -> dict:
    return {
        "google": bool(config.GOOGLE_CLIENT_ID and config.GOOGLE_CLIENT_SECRET),
        "github": bool(config.GITHUB_CLIENT_ID and config.GITHUB_CLIENT_SECRET),
    }


@router.get("/api/auth/oauth/providers")
def oauth_providers():
    """Which OAuth providers are configured on this backend."""
    return provider_status()


# --------------------------------------------------------------------------- #
# Provider identity → Dhaniti user
# --------------------------------------------------------------------------- #
def _find_or_create_oauth_user(
    provider: str, provider_user_id: str, email: str, name: str, avatar_url: Optional[str]
) -> dict:
    email = (email or "").strip().lower()
    if not email:
        raise HTTPException(status_code=422, detail="Your OAuth provider did not share an email address.")

    conn = get_connection()
    try:
        # 1) Exact provider + provider_user_id match.
        row = conn.execute(
            "SELECT * FROM users WHERE oauth_provider = ? AND oauth_id = ?",
            (provider, provider_user_id),
        ).fetchone()
        if row is not None:
            return dict(row)

        # 2) Same email → sign that user in and link this identity.
        row = conn.execute(
            "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email,)
        ).fetchone()
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        if row is not None:
            conn.execute(
                "UPDATE users SET oauth_provider = ?, oauth_id = ?, is_verified = 1, updated_at = ? WHERE user_id = ?",
                (provider, provider_user_id, now, row["user_id"]),
            )
            conn.commit()
            updated = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (row["user_id"],)
            ).fetchone()
            return dict(updated)

        # 3) Brand-new user.
        user_id = f"USR-{secrets.token_hex(4).upper()}"
        conn.execute(
            """
            INSERT INTO users (user_id, email, name, avatar_url, role, password_hash,
                               salt, oauth_provider, oauth_id, is_verified, created_at, updated_at, last_login_at)
            VALUES (?, ?, ?, ?, 'Credit Analyst', NULL, NULL, ?, ?, 1, ?, ?, ?)
            """,
            (user_id, email, name or email.split("@")[0], avatar_url, provider, provider_user_id, now, now, now),
        )
        conn.commit()
        created = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(created)
    finally:
        conn.close()


def _finish_oauth(request: Request, user: dict) -> RedirectResponse:
    """Create the session and bounce the browser to the frontend."""
    token, _ = create_access_token(user["user_id"], remember=False)
    auth_service.touch_last_login(user["user_id"])
    # Revoke later not needed: the token is handed over via one-time code.
    code = _issue_auth_code(user["user_id"])
    redirect = f"{config.FRONTEND_URL}/oauth/callback?{urlencode({'code': code, 'status': 'success'})}"
    return RedirectResponse(url=redirect, status_code=302)


def _oauth_error(message: str) -> RedirectResponse:
    redirect = f"{config.FRONTEND_URL}/oauth/callback?{urlencode({'status': 'error', 'message': message})}"
    return RedirectResponse(url=redirect, status_code=302)


# --------------------------------------------------------------------------- #
# Google
# --------------------------------------------------------------------------- #
@router.get("/auth/google")
def google_authorize():
    if not (config.GOOGLE_CLIENT_ID and config.GOOGLE_CLIENT_SECRET):
        raise HTTPException(status_code=503, detail="Google OAuth is not configured on this server. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": f"{config.OAUTH_REDIRECT_BASE}/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": _new_state(),
        "access_type": "offline",
        "prompt": "select_account",
    }
    return RedirectResponse(url=f"{config.GOOGLE_AUTH_URL}?{urlencode(params)}", status_code=302)


@router.get("/auth/google/callback")
def google_callback(request: Request):
    if not (config.GOOGLE_CLIENT_ID and config.GOOGLE_CLIENT_SECRET):
        return _oauth_error("Google OAuth is not configured on this server.")
    params = request.query_params
    if params.get("error"):
        return _oauth_error("Google sign-in was cancelled or failed.")
    if not _consume_state(params.get("state")):
        return _oauth_error("Invalid or expired OAuth state. Please try signing in again.")

    code = params.get("code")
    if not code:
        return _oauth_error("Google did not return an authorization code.")

    try:
        with httpx.Client(timeout=15) as client:
            token_resp = client.post(
                config.GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": config.GOOGLE_CLIENT_ID,
                    "client_secret": config.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": f"{config.OAUTH_REDIRECT_BASE}/auth/google/callback",
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            token_resp.raise_for_status()
            access_token = token_resp.json().get("access_token")
            if not access_token:
                return _oauth_error("Google token exchange failed.")

            profile_resp = client.get(
                config.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_resp.raise_for_status()
            profile = profile_resp.json()
    except httpx.HTTPError:
        return _oauth_error("Could not reach Google. Please try again.")

    if not profile.get("email_verified", profile.get("email")):
        return _oauth_error("Google reports this email as unverified.")

    try:
        user = _find_or_create_oauth_user(
            provider="google",
            provider_user_id=f"google-{profile.get('sub', profile.get('user_id', ''))}",
            email=profile.get("email", ""),
            name=profile.get("name") or profile.get("email", "").split("@")[0],
            avatar_url=profile.get("picture"),
        )
    except HTTPException as exc:
        return _oauth_error(exc.detail)
    return _finish_oauth(request, user)


# --------------------------------------------------------------------------- #
# GitHub
# --------------------------------------------------------------------------- #
@router.get("/auth/github")
def github_authorize():
    if not (config.GITHUB_CLIENT_ID and config.GITHUB_CLIENT_SECRET):
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured on this server. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.")
    params = {
        "client_id": config.GITHUB_CLIENT_ID,
        "redirect_uri": f"{config.OAUTH_REDIRECT_BASE}/auth/github/callback",
        "scope": "read:user user:email",
        "state": _new_state(),
    }
    return RedirectResponse(url=f"{config.GITHUB_AUTH_URL}?{urlencode(params)}", status_code=302)


@router.get("/auth/github/callback")
def github_callback(request: Request):
    if not (config.GITHUB_CLIENT_ID and config.GITHUB_CLIENT_SECRET):
        return _oauth_error("GitHub OAuth is not configured on this server.")
    params = request.query_params
    if params.get("error"):
        return _oauth_error("GitHub sign-in was cancelled or failed.")
    if not _consume_state(params.get("state")):
        return _oauth_error("Invalid or expired OAuth state. Please try signing in again.")

    code = params.get("code")
    if not code:
        return _oauth_error("GitHub did not return an authorization code.")

    try:
        with httpx.Client(timeout=15) as client:
            token_resp = client.post(
                config.GITHUB_TOKEN_URL,
                data={
                    "client_id": config.GITHUB_CLIENT_ID,
                    "client_secret": config.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": f"{config.OAUTH_REDIRECT_BASE}/auth/github/callback",
                },
                headers={"Accept": "application/json"},
            )
            token_resp.raise_for_status()
            access_token = token_resp.json().get("access_token")
            if not access_token:
                return _oauth_error("GitHub token exchange failed.")

            profile_resp = client.get(
                config.GITHUB_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
            )
            profile_resp.raise_for_status()
            profile = profile_resp.json()

            email = (profile.get("email") or "").lower()
            if not email:
                emails_resp = client.get(
                    config.GITHUB_EMAILS_URL,
                    headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
                )
                emails_resp.raise_for_status()
                for entry in emails_resp.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = entry.get("email", "").lower()
                        break
    except httpx.HTTPError:
        return _oauth_error("Could not reach GitHub. Please try again.")

    try:
        user = _find_or_create_oauth_user(
            provider="github",
            provider_user_id=f"github-{profile.get('id', '')}",
            email=email,
            name=profile.get("name") or profile.get("login") or (email.split("@")[0] if email else ""),
            avatar_url=profile.get("avatar_url"),
        )
    except HTTPException as exc:
        return _oauth_error(exc.detail)
    return _finish_oauth(request, user)


# --------------------------------------------------------------------------- #
# Exchange the one-time code for a session (called by the React app)
# --------------------------------------------------------------------------- #
class ExchangeRequest(BaseModel):
    code: str = Field(min_length=10, max_length=200)


@router.post("/api/auth/oauth/exchange")
def exchange_code(payload: ExchangeRequest):
    user_id = _consume_auth_code(payload.code.strip())
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="This sign-in code is invalid, already used, or expired. Please sign in again.",
        )
    token, _ = create_access_token(user_id, remember=False)
    from ..security.authentication import get_user_by_id

    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists.")
    return {"token": token, "user": public_user(user)}


# --------------------------------------------------------------------------- #
# Legacy cleanup helper (called on startup)
# --------------------------------------------------------------------------- #
def purge_auth_codes() -> int:
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)).isoformat()
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM auth_codes WHERE created_at < ?", (cutoff,))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
