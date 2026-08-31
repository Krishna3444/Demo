import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../api/auth.js";
import { useToast } from "../context/ToastContext.jsx";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const toast = useToast();
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!email.trim()) {
      setFieldError("Email address is required.");
      return;
    }
    if (!/^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/.test(email.trim())) {
      setFieldError("Invalid email address.");
      return;
    }
    setFieldError("");
    setLoading(true);
    try {
      await authApi.sendOtp(email.trim(), "password_reset");
      toast.info("If that email is registered, a reset code is on its way.");
      navigate("/verify-otp", { state: { email: email.trim(), purpose: "password_reset" } });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
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
            <i className="bi bi-key" aria-hidden="true" />
          </div>
          <h5 className="mb-0 fw-semibold">Forgot your password?</h5>
          <p className="text-muted small mb-0 mt-1">
            Enter your account email and we&apos;ll send you a verification code
            to choose a new password.
          </p>
        </div>

        <div className="card-body p-4">
          {error && <div className="alert alert-danger py-2" role="alert">{error}</div>}

          <form onSubmit={handleSubmit} noValidate>
            <div className="mb-4">
              <label htmlFor="fp-email" className="form-label">Email</label>
              <input
                type="email"
                className={`form-control ${fieldError ? "is-invalid" : ""}`}
                id="fp-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
                disabled={loading}
                placeholder="you@company.com"
              />
              {fieldError && <div className="invalid-feedback">{fieldError}</div>}
            </div>

            <button type="submit" className="btn btn-dhaniti w-100" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
                  Sending code…
                </>
              ) : (
                "Send reset code"
              )}
            </button>
          </form>

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
