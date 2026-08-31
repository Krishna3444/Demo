"""
conftest.py — pytest fixtures.

The test suite runs against a TEMPORARY COPY of the SQLite database so the
real data is never touched. OTP emails are captured in-memory (no SMTP /
outbox dependency) and rate-limiter state is reset between tests.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
LIVE_DB = PROJECT_ROOT / "dhaniti_loans.db"

# Point the app at a throwaway database BEFORE any app module is imported.
_tmpdir = tempfile.mkdtemp(prefix="dhaniti-tests-")
TEST_DB = Path(_tmpdir) / "test_dhaniti.db"
if LIVE_DB.exists():
    shutil.copy2(LIVE_DB, TEST_DB)
os.environ["DATABASE_PATH"] = str(TEST_DB)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient  # noqa: E402

from app.database import init_app_database  # noqa: E402
from app.main import app  # noqa: E402
from app.routes import auth as auth_routes  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _prepare_database():
    """Run migrations once for the copied test database."""
    init_app_database()
    yield
    shutil.rmtree(_tmpdir, ignore_errors=True)


@pytest.fixture()
def client():
    """FastAPI test client with clean rate-limiter state."""
    for limiter in (
        auth_routes.login_limiter,
        auth_routes.otp_send_email_limiter,
        auth_routes.otp_send_ip_limiter,
        auth_routes.otp_verify_limiter,
        auth_routes.register_limiter,
        auth_routes.reset_limiter,
    ):
        limiter._events.clear()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def captured_emails(monkeypatch):
    """Capture OTP emails in memory: list of (email, code, purpose)."""
    captured: list[dict] = []

    def fake_send_otp(to_email, code, purpose, ttl_minutes):
        captured.append({"email": to_email, "code": code, "purpose": purpose, "ttl": ttl_minutes})
        return True

    def fake_send_welcome(to_email, name):
        return True

    from app.services import email_service

    monkeypatch.setattr(email_service, "send_otp_email", fake_send_otp)
    monkeypatch.setattr(email_service, "send_welcome_email", fake_send_welcome)
    return captured


@pytest.fixture()
def admin_token(client):
    """A session token for the demo admin (write access)."""
    resp = client.post("/api/auth/login", json={
        "email": "admin@dhaniti.ai",
        "password": "DhanitiAdmin@123",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


@pytest.fixture()
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture()
def analyst_token(client):
    """A session token for the read-only demo analyst."""
    resp = client.post("/api/auth/login", json={
        "email": "analyst@dhaniti.ai",
        "password": "Analyst@123",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


@pytest.fixture()
def analyst_headers(analyst_token):
    return {"Authorization": f"Bearer {analyst_token}"}
