"""OTP tests: generation, verification, expiry, attempts, reuse, rate limits, password reset."""

from __future__ import annotations

import datetime as dt
import uuid

from app import config
from app.database import get_connection


def _email():
    return f"otp-{uuid.uuid4().hex[:10]}@example.com"


def _register_and_verify(client, captured_emails, email):
    client.post("/api/auth/register", json={"name": "Otp User", "email": email, "password": "Passw0rd123"})
    code = next(c["code"] for c in captured_emails if c["email"] == email and c["purpose"] == "email_verification")
    resp = client.post("/api/auth/verify-otp", json={"email": email, "code": code, "purpose": "email_verification"})
    assert resp.status_code == 200, resp.text
    return resp.json()


class TestOtpLogin:
    def test_send_and_verify_login_otp(self, client, captured_emails):
        resp = client.post("/api/auth/send-otp", json={"email": "admin@dhaniti.ai", "purpose": "login"})
        assert resp.status_code == 200
        # Response is generic — never reveals whether the account exists.
        assert "code" not in resp.json()
        code = next(c["code"] for c in captured_emails if c["purpose"] == "login")
        assert len(code) == config.OTP_LENGTH and code.isdigit()

        verify = client.post("/api/auth/verify-otp", json={
            "email": "admin@dhaniti.ai", "code": code, "purpose": "login",
        })
        assert verify.status_code == 200
        assert verify.json()["token"]

    def test_send_otp_unknown_email_is_generic(self, client, captured_emails):
        """Unknown email → same response shape, no code actually sent."""
        email = "ghost@nowhere.example"
        resp = client.post("/api/auth/send-otp", json={"email": email, "purpose": "login"})
        assert resp.status_code == 200
        assert not any(c["email"] == email for c in captured_emails)

    def test_wrong_otp(self, client, captured_emails):
        client.post("/api/auth/send-otp", json={"email": "admin@dhaniti.ai", "purpose": "login"})
        real = next(c["code"] for c in captured_emails if c["purpose"] == "login")
        wrong = "000000" if real != "000000" else "111111"
        resp = client.post("/api/auth/verify-otp", json={
            "email": "admin@dhaniti.ai", "code": wrong, "purpose": "login",
        })
        assert resp.status_code == 401

    def test_otp_single_use(self, client, captured_emails):
        email = "admin@dhaniti.ai"
        client.post("/api/auth/send-otp", json={"email": email, "purpose": "login"})
        code = next(c["code"] for c in captured_emails if c["purpose"] == "login")
        first = client.post("/api/auth/verify-otp", json={"email": email, "code": code, "purpose": "login"})
        assert first.status_code == 200
        second = client.post("/api/auth/verify-otp", json={"email": email, "code": code, "purpose": "login"})
        assert second.status_code == 401

    def test_otp_max_attempts(self, client, captured_emails):
        email = "admin@dhaniti.ai"
        client.post("/api/auth/send-otp", json={"email": email, "purpose": "login"})
        real = next(c["code"] for c in captured_emails if c["purpose"] == "login")
        wrong = "000000" if real != "000000" else "111111"
        last_status = None
        for _ in range(config.OTP_MAX_ATTEMPTS):
            last_status = client.post("/api/auth/verify-otp", json={
                "email": email, "code": wrong, "purpose": "login",
            }).status_code
        assert last_status == 401
        # The real code is now dead too (too many wrong attempts).
        resp = client.post("/api/auth/verify-otp", json={"email": email, "code": real, "purpose": "login"})
        assert resp.status_code == 401
        assert "Too many" in resp.json()["error"] or "new code" in resp.json()["error"]

    def test_otp_expired(self, client, captured_emails):
        email = "admin@dhaniti.ai"
        client.post("/api/auth/send-otp", json={"email": email, "purpose": "login"})
        code = next(c["code"] for c in captured_emails if c["purpose"] == "login")

        # Force-expire the stored code.
        conn = get_connection()
        try:
            past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)).isoformat()
            conn.execute(
                "UPDATE otp_codes SET expires_at = ? WHERE used = 0", (past,)
            )
            conn.commit()
        finally:
            conn.close()

        resp = client.post("/api/auth/verify-otp", json={"email": email, "code": code, "purpose": "login"})
        assert resp.status_code == 401
        assert "expired" in resp.json()["error"].lower()

    def test_otp_hashed_at_rest(self, client, captured_emails):
        """The plaintext code must never be stored in the database."""
        client.post("/api/auth/send-otp", json={"email": "admin@dhaniti.ai", "purpose": "login"})
        code = next(c["code"] for c in captured_emails if c["purpose"] == "login")
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT code_hash FROM otp_codes WHERE used = 0 ORDER BY id DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()
        assert row is not None
        assert code not in row["code_hash"]
        assert row["code_hash"].startswith("$argon2")

    def test_resend_invalidates_previous_code(self, client, captured_emails):
        email = "admin@dhaniti.ai"
        client.post("/api/auth/send-otp", json={"email": email, "purpose": "login"})
        first = next(c["code"] for c in captured_emails if c["purpose"] == "login")
        client.post("/api/auth/send-otp", json={"email": email, "purpose": "login"})
        second = next(c["code"] for c in captured_emails if c["purpose"] == "login" and c["code"] != first)
        # Old code no longer works.
        resp = client.post("/api/auth/verify-otp", json={"email": email, "code": first, "purpose": "login"})
        assert resp.status_code == 401
        # New code does.
        resp = client.post("/api/auth/verify-otp", json={"email": email, "code": second, "purpose": "login"})
        assert resp.status_code == 200

    def test_send_otp_rate_limited(self, client):
        email = "underwriter@dhaniti.ai"
        statuses = [
            client.post("/api/auth/send-otp", json={"email": email, "purpose": "login"}).status_code
            for _ in range(config.OTP_SEND_RATE_MAX + 1)
        ]
        assert 429 in statuses


class TestEmailVerification:
    def test_register_then_verify_then_login(self, client, captured_emails):
        email = _email()
        # Registered user cannot login before verifying.
        resp = client.post("/api/auth/login", json={"email": email, "password": "Passw0rd123"})
        assert resp.status_code == 401

        session = _register_and_verify(client, captured_emails, email)
        assert session["token"]
        assert session["user"]["email"] == email

        # After verification, password login works.
        resp = client.post("/api/auth/login", json={"email": email, "password": "Passw0rd123"})
        assert resp.status_code == 200

    def test_unverified_login_returns_403_and_resends_code(self, client, captured_emails):
        email = _email()
        client.post("/api/auth/register", json={"name": "Unverified", "email": email, "password": "Passw0rd123"})
        resp = client.post("/api/auth/login", json={"email": email, "password": "Passw0rd123"})
        assert resp.status_code == 403
        # A fresh verification code was issued.
        codes = [c for c in captured_emails if c["email"] == email and c["purpose"] == "email_verification"]
        assert len(codes) >= 2


class TestPasswordReset:
    def test_full_reset_flow(self, client, captured_emails):
        email = _email()
        _register_and_verify(client, captured_emails, email)

        # 1. request reset code
        resp = client.post("/api/auth/send-otp", json={"email": email, "purpose": "password_reset"})
        assert resp.status_code == 200
        code = next(c["code"] for c in captured_emails if c["email"] == email and c["purpose"] == "password_reset")

        # 2. verify code → get reset token
        resp = client.post("/api/auth/verify-reset-otp", json={"email": email, "code": code})
        assert resp.status_code == 200
        reset_token = resp.json()["resetToken"]
        assert reset_token

        # 3. set new password
        resp = client.post("/api/auth/reset-password", json={
            "resetToken": reset_token, "newPassword": "BrandNew789",
        })
        assert resp.status_code == 200

        # 4. old password dead, new password works
        assert client.post("/api/auth/login", json={"email": email, "password": "Passw0rd123"}).status_code == 401
        assert client.post("/api/auth/login", json={"email": email, "password": "BrandNew789"}).status_code == 200

    def test_reset_with_garbage_token(self, client):
        resp = client.post("/api/auth/reset-password", json={
            "resetToken": "x" * 40, "newPassword": "BrandNew789",
        })
        assert resp.status_code == 422

    def test_reset_weak_password(self, client, captured_emails):
        email = _email()
        _register_and_verify(client, captured_emails, email)
        client.post("/api/auth/send-otp", json={"email": email, "purpose": "password_reset"})
        code = next(c["code"] for c in captured_emails if c["email"] == email and c["purpose"] == "password_reset")
        token = client.post("/api/auth/verify-reset-otp", json={"email": email, "code": code}).json()["resetToken"]
        resp = client.post("/api/auth/reset-password", json={"resetToken": token, "newPassword": "short"})
        assert resp.status_code == 422
