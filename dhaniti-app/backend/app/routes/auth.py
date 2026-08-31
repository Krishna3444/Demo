"""
routes/auth.py — authentication endpoints.

All request/response bodies use camelCase to stay consistent with the
existing frontend API client. Error responses use the shape:

    {"error": "human readable message", "details": ["optional", "details"]}

Rate limiting protects login / OTP / register / reset endpoints.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from .. import config
from ..security.authentication import client_ip, get_current_user
from ..services import auth_service, rate_limiter
from ..services.auth_service import UnverifiedEmailError

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# --------------------------------------------------------------------------- #
# Rate limiters (in-memory sliding windows)
# --------------------------------------------------------------------------- #
login_limiter = rate_limiter.RateLimiter(config.LOGIN_RATE_MAX, config.LOGIN_RATE_WINDOW_SECONDS)
otp_send_email_limiter = rate_limiter.RateLimiter(config.OTP_SEND_RATE_MAX, config.OTP_SEND_RATE_WINDOW_SECONDS)
otp_send_ip_limiter = rate_limiter.RateLimiter(config.OTP_SEND_RATE_MAX * 3, config.OTP_SEND_RATE_WINDOW_SECONDS)
otp_verify_limiter = rate_limiter.RateLimiter(config.OTP_VERIFY_RATE_MAX, config.OTP_VERIFY_RATE_WINDOW_SECONDS)
register_limiter = rate_limiter.RateLimiter(config.REGISTER_RATE_MAX, config.REGISTER_RATE_WINDOW_SECONDS)
reset_limiter = rate_limiter.RateLimiter(config.PASSWORD_RESET_RATE_MAX, config.PASSWORD_RESET_RATE_WINDOW_SECONDS)


def _rate_limit(limiter: rate_limiter.RateLimiter, key: str) -> None:
    allowed, retry_after = limiter.check(key)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many attempts. Please try again in {retry_after // 60 or 1} minute(s).",
            headers={"Retry-After": str(retry_after)},
        )


# --------------------------------------------------------------------------- #
# Request / response models
# --------------------------------------------------------------------------- #
class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)
    confirmPassword: Optional[str] = None


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)
    remember: bool = False


class SendOtpRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    purpose: str = Field(default="login", pattern="^(login|password_reset|email_verification)$")


class VerifyOtpRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    code: str = Field(min_length=1, max_length=12)
    purpose: str = Field(default="login", pattern="^(login|email_verification)$")
    remember: bool = False


class VerifyResetOtpRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    code: str = Field(min_length=1, max_length=12)


class ResetPasswordRequest(BaseModel):
    resetToken: str = Field(min_length=10)
    newPassword: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    currentPassword: str = Field(min_length=1, max_length=128)
    newPassword: str = Field(min_length=1, max_length=128)


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    avatarUrl: Optional[str] = Field(default=None, max_length=500)


class ResendVerificationRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)


# --------------------------------------------------------------------------- #
# Register
# --------------------------------------------------------------------------- #
@router.post("/register", status_code=201)
def register(payload: RegisterRequest, request: Request):
    _rate_limit(register_limiter, f"register:{client_ip(request)}")

    email = payload.email.strip().lower()
    for err in (
        auth_service.validate_name(payload.name),
        auth_service.validate_email(email),
        auth_service.validate_password(payload.password),
    ):
        if err:
            raise HTTPException(status_code=422, detail=err)
    if payload.confirmPassword is not None and payload.confirmPassword != payload.password:
        raise HTTPException(status_code=422, detail="Passwords do not match.")

    try:
        result = auth_service.register_user(payload.name, email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "message": "Account created. We sent a verification code to your email.",
        "user": result["user"],
        "expiresInMinutes": result["ttl_minutes"],
    }


# --------------------------------------------------------------------------- #
# Login (email + password)
# --------------------------------------------------------------------------- #
@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response):
    _rate_limit(login_limiter, f"login:{client_ip(request)}:{payload.email.strip().lower()}")

    try:
        result = auth_service.authenticate(payload.email, payload.password, remember=payload.remember)
    except UnverifiedEmailError as exc:
        raise HTTPException(
            status_code=403,
            detail="Your email is not verified yet. We sent you a new verification code.",
            headers={"X-Auth-Error": "email_unverified"},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    login_limiter.reset(f"login:{client_ip(request)}:{payload.email.strip().lower()}")
    return {"token": result["token"], "user": result["user"]}


# --------------------------------------------------------------------------- #
# Current user / profile
# --------------------------------------------------------------------------- #
@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return auth_service.public_user(user)


@router.put("/me")
def update_me(payload: ProfileUpdateRequest, user: dict = Depends(get_current_user)):
    try:
        updated = auth_service.update_profile(user["user_id"], name=payload.name, avatar_url=payload.avatarUrl)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return updated


@router.post("/change-password", status_code=204)
def change_password(payload: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    _rate_limit(login_limiter, f"chpw:{user['user_id']}")
    try:
        auth_service.change_password(user["user_id"], payload.currentPassword, payload.newPassword)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(status_code=204)


# --------------------------------------------------------------------------- #
# Logout
# --------------------------------------------------------------------------- #
@router.post("/logout")
def logout(request: Request, user: dict = Depends(get_current_user)):
    token = getattr(request.state, "token", None)
    revoked = auth_service.logout(token) if token else False
    return {"message": "Signed out successfully.", "revoked": revoked}


# --------------------------------------------------------------------------- #
# OTP flows
# --------------------------------------------------------------------------- #
@router.post("/send-otp")
def send_otp(payload: SendOtpRequest, request: Request):
    email = payload.email.strip().lower()
    if auth_service.validate_email(email):
        raise HTTPException(status_code=422, detail="Invalid email address.")

    purpose = payload.purpose
    if purpose == "email_verification":
        # Only for existing unverified accounts (re-verification).
        user = auth_service.get_user_by_email(email)
        if user is None:
            return {
                "message": "If an account exists for that email, a verification code has been sent.",
                "expiresInMinutes": config.OTP_TTL_MINUTES,
            }
        if user.get("is_verified"):
            raise HTTPException(status_code=409, detail="This email is already verified. Please sign in.")

    _rate_limit(otp_send_email_limiter, f"otp-email:{email}")
    _rate_limit(otp_send_ip_limiter, f"otp-ip:{client_ip(request)}")

    return auth_service.send_login_otp(email, purpose=purpose)


@router.post("/verify-otp")
def verify_otp(payload: VerifyOtpRequest, request: Request):
    email = payload.email.strip().lower()
    _rate_limit(otp_verify_limiter, f"otp-verify:{email}")

    purpose = payload.purpose
    if purpose == "password_reset":
        raise HTTPException(status_code=422, detail="Use the reset-password flow for password resets.")

    try:
        result = auth_service.verify_otp_and_issue_session(email, payload.code, purpose, remember=payload.remember)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    otp_verify_limiter.reset(f"otp-verify:{email}")
    return result


@router.post("/verify-reset-otp")
def verify_reset_otp(payload: VerifyResetOtpRequest, request: Request):
    """Step 1 of forgot-password: verify the emailed code, get a reset token."""
    email = payload.email.strip().lower()
    _rate_limit(otp_verify_limiter, f"otp-verify:{email}")
    try:
        reset_token = auth_service.verify_reset_otp(email, payload.code)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    otp_verify_limiter.reset(f"otp-verify:{email}")
    return {
        "resetToken": reset_token,
        "message": "Code verified. Choose a new password.",
        "expiresInMinutes": config.RESET_TOKEN_TTL_MINUTES,
    }


@router.post("/reset-password", status_code=200)
def reset_password(payload: ResetPasswordRequest, request: Request):
    _rate_limit(reset_limiter, f"reset:{client_ip(request)}")
    try:
        auth_service.reset_password(payload.resetToken, payload.newPassword)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"message": "Password updated. You can now sign in with your new password."}


@router.post("/resend-verification")
def resend_verification(payload: ResendVerificationRequest, request: Request):
    email = payload.email.strip().lower()
    if auth_service.validate_email(email):
        raise HTTPException(status_code=422, detail="Invalid email address.")
    _rate_limit(otp_send_email_limiter, f"otp-email:{email}")
    _rate_limit(otp_send_ip_limiter, f"otp-ip:{client_ip(request)}")

    user = auth_service.get_user_by_email(email)
    if user is None or user.get("is_verified"):
        return {"message": "If an unverified account exists for that email, a new code has been sent."}

    from ..services import otp_service, email_service

    code, ttl = otp_service.generate_otp(user["user_id"], user["email"], "email_verification")
    email_service.send_otp_email(user["email"], code, "email_verification", ttl)
    return {"message": "A new verification code has been sent.", "expiresInMinutes": ttl}
