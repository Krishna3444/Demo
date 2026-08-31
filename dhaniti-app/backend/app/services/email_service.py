"""
email_service.py — transactional email delivery.

Two transports:
  1. SMTP (production): configured via SMTP_HOST / SMTP_PORT / SMTP_USERNAME /
     SMTP_PASSWORD / SMTP_FROM / SMTP_USE_TLS in the environment.
  2. Local outbox (development fallback): when SMTP is not configured,
     messages are written as `.eml` files under backend/logs/emails/ and the
     content is echoed to the server log. This keeps the OTP flow fully
     functional (real codes, real verification) for local testing without
     external credentials.

The OTP code itself is ALWAYS generated and verified by otp_service; this
module is only the transport.
"""

from __future__ import annotations

import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from .. import config

logger = logging.getLogger("dhaniti.email")


def send_email(to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
    """Send an email. Returns True on successful hand-off to the transport."""
    if not to_email or "@" not in to_email:
        logger.warning("Refusing to send to invalid address: %r", to_email)
        return False

    if config.SMTP_CONFIGURED:
        return _send_via_smtp(to_email, subject, html_body, text_body)
    return _write_to_outbox(to_email, subject, html_body, text_body)


def _build_message(to_email: str, subject: str, html_body: str, text_body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(text_body or "Please view this email in an HTML-capable client.")
    msg.add_alternative(html_body, subtype="html")
    return msg


def _send_via_smtp(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    msg = _build_message(to_email, subject, html_body, text_body)
    try:
        if config.SMTP_USE_TLS and config.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
        try:
            if config.SMTP_USE_TLS and config.SMTP_PORT != 465:
                server.starttls()
            if config.SMTP_USERNAME:
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)
        finally:
            server.quit()
        logger.info("Email sent to %s via SMTP: %s", _mask(to_email), subject)
        return True
    except Exception as exc:  # noqa: BLE001 — never crash the API over email
        logger.error("SMTP delivery failed (%s → %s): %s", _mask(to_email), subject, exc)
        return False


def _write_to_outbox(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    config.EMAIL_OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = config.EMAIL_OUTBOX_DIR / f"{stamp}-{to_email.replace('@', '_at_')}.eml"
    try:
        msg = _build_message(to_email, subject, html_body, text_body)
        path.write_bytes(msg.as_bytes())
    except OSError as exc:
        logger.error("Could not write outbox email: %s", exc)
        return False
    logger.info(
        "[DEV OUTBOX] Email for %s (%s) written to %s "
        "(configure SMTP_* variables to send real email)",
        _mask(to_email),
        subject,
        path.name,
    )
    return True


def _mask(email: str) -> str:
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        return f"{local[:1]}***@{domain}"
    return f"{local[:2]}***@{domain}"


# --------------------------------------------------------------------------- #
# Templates
# --------------------------------------------------------------------------- #
def _shell(title: str, body_html: str) -> str:
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;
                background:#f8fafc;padding:24px;">
      <div style="max-width:520px;margin:0 auto;background:#ffffff;
                  border-radius:12px;overflow:hidden;
                  box-shadow:0 4px 24px rgba(15,118,110,0.12);">
        <div style="background:linear-gradient(135deg,#0f766e 0%,#134e4a 100%);
                    padding:20px 28px;color:#ffffff;">
          <div style="font-size:20px;font-weight:700;">Dhaniti</div>
          <div style="font-size:13px;opacity:.85;">Education Loan Dashboard</div>
        </div>
        <div style="padding:28px;color:#1f2937;font-size:15px;line-height:1.6;">
          {body_html}
        </div>
        <div style="padding:16px 28px;background:#f1f5f9;color:#64748b;
                    font-size:12px;">
          This is an automated message from the Dhaniti Education Loan Dashboard.
          If you did not request it, you can safely ignore this email.
        </div>
      </div>
    </div>
    """


def send_otp_email(to_email: str, code: str, purpose: str, ttl_minutes: int) -> bool:
    pretty_purpose = {
        "login": "sign in",
        "email_verification": "verify your email",
        "password_reset": "reset your password",
    }.get(purpose, purpose.replace("_", " "))

    body = f"""
      <p style="margin:0 0 12px;">Hi,</p>
      <p style="margin:0 0 16px;">
        Use the verification code below to {pretty_purpose}.
        It expires in <strong>{ttl_minutes} minutes</strong>.
      </p>
      <div style="text-align:center;margin:24px 0;">
        <span style="display:inline-block;font-size:32px;font-weight:700;
                     letter-spacing:10px;color:#0f766e;background:#ecfdf5;
                     border:1px dashed #14b8a6;border-radius:10px;padding:12px 20px;">
          {code}
        </span>
      </div>
      <p style="margin:0;color:#64748b;font-size:13px;">
        If you did not request this code, no action is needed —
        it will stop working after it expires.
      </p>
    """
    return send_email(
        to_email,
        f"Dhaniti verification code: {code}",
        _shell("Verification code", body),
        text_body=f"Your Dhaniti verification code is {code}. It expires in {ttl_minutes} minutes.",
    )


def send_welcome_email(to_email: str, name: str) -> bool:
    body = f"""
      <p style="margin:0 0 12px;">Welcome aboard, {name}!</p>
      <p style="margin:0 0 16px;">
        Your Dhaniti Education Loan Dashboard account has been created.
        Use your verification code to activate it and start exploring the
        loan-portfolio analytics.
      </p>
    """
    return send_email(
        to_email,
        "Welcome to the Dhaniti Dashboard",
        _shell("Welcome", body),
        text_body=f"Welcome to Dhaniti, {name}! Your account has been created.",
    )
