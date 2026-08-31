import React, { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import OtpInput from "../components/OtpInput.jsx";
import { authApi } from "../api/auth.js";
import { ApiError } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useToast } from "../context/ToastContext.jsx";

const PURPOSE_META = {
  login: { title: "Enter Verification Code", subtitle: "We sent a login verification code to:", cta: "Verify & Sign In" },
  email_verification: { title: "Verify Your Email", subtitle: "We sent a verification code to:", cta: "Verify Email" },
  password_reset: { title: "Enter Verification Code", subtitle: "We sent a password-reset code to:", cta: "Continue" },
};

export default function VerifyOtp() {
  const location = useLocation();
  const navigate = useNavigate();
  const toast = useToast();
  const { applySession } = useAuth();

  const email = (location.state?.email || "").trim();
  const purpose = location.state?.purpose || "login";
  const sendNow = Boolean(location.state?.sendNow);
  const meta = PURPOSE_META[purpose] || PURPOSE_META.login;

  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [secondsLeft, setSecondsLeft] = useState(120);
  const [resent, setResent] = useState(0);
  const sentRef = useRef(false);

  // Users must arrive with an email in state.
  useEffect(() => {
    if (!email) navigate("/login", { replace: true });
  }, [email, navigate]);

  // Optionally auto-send the code when arriving from "Login with OTP".
  useEffect(() => {
    if (sendNow && email && !sentRef.current) {
      sentRef.current = true;
      (async () => {
        setSending(true);
        try {
          await authApi.sendOtp(email, purpose === "email_verification" ? "login" : purpose);
          toast.info(`Verification code sent to ${email}`);
        } catch (err) {
          setError(err.message);
        } finally {
          setSending(false);
        }
      })();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sendNow, email]);

  // Countdown timer.
  useEffect(() => {
    if (secondsLeft <= 0) return;
    const timer = setInterval(() => setSecondsLeft((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(timer);
  }, [secondsLeft]);

  const mm = String(Math.floor(secondsLeft / 60)).padStart(2, "0");
  const ss = String(secondsLeft % 60).padStart(2, "0");

  async function handleVerify(submitted) {
    if (!submitted || submitted.length < 6) {
      setError("Enter the complete verification code.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      if (purpose === "password_reset") {
        const { resetToken } = await authApi.verifyResetOtp(email, submitted);
        navigate("/reset-password", { state: { email, resetToken } });
      } else {
        const { token, user } = await authApi.verifyOtp(email, submitted, purpose);
        applySession(token, user);
        toast.success("Verification successful. Welcome!");
        navigate("/dashboard", { replace: true });
      }
    } catch (err) {
      setError(err instanceof ApiError && err.details?.length ? `${err.message}` : err.message);
      setCode("");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    if (resent >= 3) {
      setError("Too many resend requests. Please wait before requesting another code.");
      return;
    }
    setError("");
    setSending(true);
    try {
      const sendPurpose = purpose === "email_verification" ? "email_verification" : purpose === "password_reset" ? "password_reset" : "login";
      await authApi.sendOtp(email, sendPurpose === "email_verification" ? "login" : sendPurpose);
      setResent((r) => r + 1);
      setSecondsLeft(120);
      setCode("");
      toast.success("A new verification code has been sent.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="login-wrapper">
      <div className="card login-card" style={{ maxWidth: 420 }}>
        <div className="card-header text-center">
          <div
            className="mx-auto mb-2 d-flex align-items-center justify-content-center"
            style={{
              width: 48,
              height: 48,
              borderRadius: 14,
              background: "linear-gradient(135deg, #0f766e 0%, #134e4a 100%)",
              color: "white",
              fontSize: 22,
            }}
          >
            <i className="bi bi-shield-check" aria-hidden="true" />
          </div>
          <h5 className="mb-0 fw-semibold">{meta.title}</h5>
          <p className="text-muted small mb-0 mt-1">{meta.subtitle}</p>
          <p className="fw-medium mb-0 mt-1">{email}</p>
        </div>

        <div className="card-body p-4">
          {error && <div className="alert alert-danger py-2" role="alert">{error}</div>}

          <OtpInput
            value={code}
            onChange={setCode}
            onComplete={handleVerify}
            disabled={loading || sending}
          />

          <button
            className="btn btn-dhaniti w-100 mt-4"
            disabled={loading || sending || code.length < 6}
            onClick={() => handleVerify(code)}
          >
            {loading ? (
              <>
                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
                Verifying…
              </>
            ) : (
              "Verify"
            )}
          </button>

          <p className="text-center text-muted small mt-3 mb-2">
            Code expires in:{" "}
            <span className="fw-semibold text-dhaniti" data-testid="otp-countdown">
              {mm}:{ss}
            </span>
          </p>

          <hr />
          <p className="text-center text-muted small mb-1">Didn&apos;t receive it?</p>
          <div className="text-center">
            <button
              className="btn btn-sm btn-outline-dhaniti"
              onClick={handleResend}
              disabled={sending || resent >= 3 || secondsLeft > 90}
            >
              {sending ? (
                <>
                  <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true" />
                  Sending code…
                </>
              ) : (
                "Resend Code"
              )}
            </button>
            {resent >= 3 && (
              <div className="small text-danger mt-2">Maximum resends reached — please try again later.</div>
            )}
          </div>

          <p className="text-center small mt-4 mb-0">
            <Link to="/login">
              <i className="bi bi-arrow-left me-1" aria-hidden="true" />
              Back to sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
