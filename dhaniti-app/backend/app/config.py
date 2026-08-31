"""
config.py — environment-driven configuration for the Dhaniti backend.

All secrets (JWT secret, OAuth client secrets, SMTP credentials) MUST come
from environment variables or a `.env` file placed in the `backend/`
directory. Sensible development fallbacks exist ONLY for local runs and are
clearly flagged; production deployments must set real values.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
BACKEND_DIR = Path(__file__).resolve().parent.parent          # backend/
PROJECT_ROOT = BACKEND_DIR.parent                             # dhaniti-app/
STATIC_DIR = BACKEND_DIR / "static"                           # built React app
LOG_DIR = BACKEND_DIR / "logs"
EMAIL_OUTBOX_DIR = LOG_DIR / "emails"


def _load_dotenv() -> None:
    """Tiny .env loader (no external dependency).

    Loads `backend/.env` if present. Existing environment variables always
    take precedence over file values.
    """
    env_file = BACKEND_DIR / ".env"
    if not env_file.exists():
        return
    try:
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        # Unreadable .env — fall back to process environment only.
        pass


_load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = _env(name)
    if not raw:
        return list(default)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _env_int(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except ValueError:
        return default


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #
DATABASE_PATH = Path(
    _env("DATABASE_PATH", str(PROJECT_ROOT / "dhaniti_loans.db"))
)

# --------------------------------------------------------------------------- #
# Security / JWT
# --------------------------------------------------------------------------- #
_env_secret = _env("SECRET_KEY") or _env("JWT_SECRET")
if not _env_secret:
    # Development fallback: random per-process secret (sessions will not
    # survive restarts) unless a fixed secret is provided. In production
    # ALWAYS set SECRET_KEY in the environment / .env file.
    _env_secret = "dev-" + secrets.token_hex(24)

SECRET_KEY = _env_secret
JWT_ALGORITHM = "HS256"
JWT_TTL_HOURS = _env_int("JWT_TTL_HOURS", 8)
JWT_TTL_REMEMBER_HOURS = _env_int("JWT_TTL_REMEMBER_HOURS", 24 * 30)  # "remember me"
RESET_TOKEN_TTL_MINUTES = _env_int("RESET_TOKEN_TTL_MINUTES", 15)

IS_PRODUCTION = _env_bool("PRODUCTION", default=False)
if IS_PRODUCTION and SECRET_KEY.startswith("dev-"):
    # Fail fast in production when no real secret was configured.
    raise RuntimeError(
        "SECRET_KEY must be set to a strong random value in production. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

# --------------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------------- #
CORS_ORIGINS = _env_list(
    "CORS_ORIGINS",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
)

# --------------------------------------------------------------------------- #
# OAuth (Google + GitHub)
# --------------------------------------------------------------------------- #
GOOGLE_CLIENT_ID = _env("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = _env("GOOGLE_CLIENT_SECRET")

GITHUB_CLIENT_ID = _env("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = _env("GITHUB_CLIENT_SECRET")

# Base URL where THIS backend is reachable (used to build OAuth callback URLs).
OAUTH_REDIRECT_BASE = _env(
    "OAUTH_REDIRECT_BASE", "http://localhost:8000"
).rstrip("/")

# Where to send the browser after a successful OAuth callback.
FRONTEND_URL = _env("FRONTEND_URL", "http://localhost:5173").rstrip("/")

OAUTH_STATE_TTL_SECONDS = _env_int("OAUTH_STATE_TTL_SECONDS", 600)
AUTH_CODE_TTL_SECONDS = _env_int("AUTH_CODE_TTL_SECONDS", 60)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USERINFO_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"

# --------------------------------------------------------------------------- #
# OTP / Email
# --------------------------------------------------------------------------- #
OTP_LENGTH = _env_int("OTP_LENGTH", 6)
OTP_TTL_MINUTES = _env_int("OTP_TTL_MINUTES", 10)
OTP_MAX_ATTEMPTS = _env_int("OTP_MAX_ATTEMPTS", 5)

SMTP_HOST = _env("SMTP_HOST")
SMTP_PORT = _env_int("SMTP_PORT", 587)
SMTP_USERNAME = _env("SMTP_USERNAME")
SMTP_PASSWORD = _env("SMTP_PASSWORD")
SMTP_FROM = _env("SMTP_FROM", "no-reply@dhaniti.local")
SMTP_USE_TLS = _env_bool("SMTP_USE_TLS", default=True)

# When SMTP is not configured, emails (including OTP codes) are written to
# backend/logs/emails/*.eml so the flow can be tested end-to-end locally.
SMTP_CONFIGURED = bool(SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD)

# --------------------------------------------------------------------------- #
# Rate limiting (in-memory sliding window)
# --------------------------------------------------------------------------- #
LOGIN_RATE_MAX = _env_int("LOGIN_RATE_MAX", 5)             # attempts
LOGIN_RATE_WINDOW_SECONDS = _env_int("LOGIN_RATE_WINDOW_SECONDS", 15 * 60)

OTP_SEND_RATE_MAX = _env_int("OTP_SEND_RATE_MAX", 3)       # sends
OTP_SEND_RATE_WINDOW_SECONDS = _env_int("OTP_SEND_RATE_WINDOW_SECONDS", 10 * 60)

OTP_VERIFY_RATE_MAX = _env_int("OTP_VERIFY_RATE_MAX", 10)
OTP_VERIFY_RATE_WINDOW_SECONDS = _env_int("OTP_VERIFY_RATE_WINDOW_SECONDS", 15 * 60)

REGISTER_RATE_MAX = _env_int("REGISTER_RATE_MAX", 10)
REGISTER_RATE_WINDOW_SECONDS = _env_int("REGISTER_RATE_WINDOW_SECONDS", 60 * 60)

PASSWORD_RESET_RATE_MAX = _env_int("PASSWORD_RESET_RATE_MAX", 3)
PASSWORD_RESET_RATE_WINDOW_SECONDS = _env_int("PASSWORD_RESET_RATE_WINDOW_SECONDS", 15 * 60)

# --------------------------------------------------------------------------- #
# Roles
# --------------------------------------------------------------------------- #
READ_ONLY_ROLES = {"Credit Analyst"}
ADMIN_ROLES = {"Admin"}
WRITE_ROLES = {"Admin", "Underwriter", "Risk Officer"}

APP_NAME = "Dhaniti Education Loan Dashboard"
API_TITLE = "Dhaniti API"
API_VERSION = "2.0.0"
