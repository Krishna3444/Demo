"""Authentication tests: register, login, session, logout, errors, rate limits."""

from __future__ import annotations

import uuid


def _email():
    return f"test-{uuid.uuid4().hex[:10]}@example.com"


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #
class TestRegister:
    def test_register_valid(self, client, captured_emails):
        email = _email()
        resp = client.post("/api/auth/register", json={
            "name": "Test User", "email": email,
            "password": "Passw0rd123", "confirmPassword": "Passw0rd123",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["user"]["email"] == email
        assert body["user"]["isVerified"] in (True, False, 0, 1)
        # A verification code was "sent".
        assert any(c["email"] == email and c["purpose"] == "email_verification" for c in captured_emails)
        # The API response never contains the OTP itself.
        import json as _json
        assert "code" not in body and "otp" not in _json.dumps(body).lower()

    def test_register_duplicate_email(self, client, captured_emails):
        email = _email()
        payload = {"name": "Dup User", "email": email, "password": "Passw0rd123"}
        assert client.post("/api/auth/register", json=payload).status_code == 201
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code == 409

    def test_register_weak_password(self, client):
        resp = client.post("/api/auth/register", json={
            "name": "Weak", "email": _email(), "password": "short",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post("/api/auth/register", json={
            "name": "Bad Email", "email": "not-an-email", "password": "Passw0rd123",
        })
        assert resp.status_code == 422

    def test_register_password_mismatch(self, client):
        resp = client.post("/api/auth/register", json={
            "name": "Mismatch", "email": _email(),
            "password": "Passw0rd123", "confirmPassword": "Different1",
        })
        assert resp.status_code == 422

    def test_register_missing_fields(self, client):
        assert client.post("/api/auth/register", json={"email": _email()}).status_code == 422


# --------------------------------------------------------------------------- #
# Login
# --------------------------------------------------------------------------- #
class TestLogin:
    def test_login_valid(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "admin@dhaniti.ai", "password": "DhanitiAdmin@123",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["token"]
        assert body["user"]["email"] == "admin@dhaniti.ai"
        assert "password_hash" not in body["user"]

    def test_login_wrong_password(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "admin@dhaniti.ai", "password": "wrong-password",
        })
        assert resp.status_code == 401

    def test_login_unknown_user(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "ghost@nowhere.com", "password": "whatever1",
        })
        assert resp.status_code == 401
        # Same message as wrong password → no user enumeration.
        known = client.post("/api/auth/login", json={
            "email": "admin@dhaniti.ai", "password": "wrong-password",
        })
        assert resp.json()["error"] == known.json()["error"]

    def test_login_missing_credentials(self, client):
        assert client.post("/api/auth/login", json={}).status_code == 422

    def test_login_rate_limited(self, client):
        email = "admin@dhaniti.ai"
        for _ in range(5):
            client.post("/api/auth/login", json={"email": email, "password": "nope"})
        resp = client.post("/api/auth/login", json={"email": email, "password": "DhanitiAdmin@123"})
        assert resp.status_code == 429

    def test_legacy_login_endpoint_alias(self, client):
        """The original Flask endpoint /api/login keeps working."""
        resp = client.post("/api/login", json={"username": "admin", "password": "DhanitiAdmin@123"})
        assert resp.status_code == 200
        assert resp.json()["token"]


# --------------------------------------------------------------------------- #
# Session / me / logout
# --------------------------------------------------------------------------- #
class TestSession:
    def test_me(self, client, admin_headers):
        resp = client.get("/api/auth/me", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "admin@dhaniti.ai"

    def test_me_without_token(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_me_garbage_token(self, client):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
        assert resp.status_code == 401

    def test_protected_endpoints_require_auth(self, client):
        for path in ("/api/kpis", "/api/charts", "/api/applications", "/api/filters"):
            assert client.get(path).status_code == 401, path

    def test_logout_revokes_session(self, client, admin_headers, admin_token):
        assert client.get("/api/auth/me", headers=admin_headers).status_code == 200
        resp = client.post("/api/auth/logout", headers=admin_headers)
        assert resp.status_code == 200
        # Token no longer works.
        assert client.get("/api/auth/me", headers=admin_headers).status_code == 401

    def test_whoami_alias(self, client, admin_headers):
        resp = client.get("/api/whoami", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["role"] == "Admin"

    def test_update_profile(self, client, admin_headers):
        resp = client.put("/api/auth/me", headers=admin_headers, json={"name": "Renamed Admin"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Admin"

    def test_change_password(self, client, captured_emails):
        email = _email()
        client.post("/api/auth/register", json={"name": "Ch Pw", "email": email, "password": "Passw0rd123"})
        code = next(c["code"] for c in captured_emails if c["email"] == email)
        resp = client.post("/api/auth/verify-otp", json={"email": email, "code": code, "purpose": "email_verification"})
        token = resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        ok = client.post("/api/auth/change-password", headers=headers,
                         json={"currentPassword": "Passw0rd123", "newPassword": "NewPass456"})
        assert ok.status_code == 204
        # Old password rejected, new one works.
        assert client.post("/api/auth/login", json={"email": email, "password": "Passw0rd123"}).status_code == 401
        assert client.post("/api/auth/login", json={"email": email, "password": "NewPass456"}).status_code == 200
