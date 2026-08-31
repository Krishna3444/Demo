import React, { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { authApi } from "../api/auth.js";
import { ApiError } from "../api/client.js";

export default function Login() {
  const { login, notice, setNotice, isAuthenticated } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [providers, setProviders] = useState({ google: false, github: false });

  useEffect(() => {
    authApi
      .oauthProviders()
      .then(setProviders)
      .catch(() => setProviders({ google: false, github: false }));
  }, []);

  // Already signed in? Straight to the dashboard.
  useEffect(() => {
    if (isAuthenticated) {
      navigate(location.state?.from || "/dashboard", { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  useEffect(() => {
    if (notice) {
      setApiError(notice);
      setNotice("");
    }
  }, [notice, setNotice]);

  function validate() {
    const next = {};
    if (!email.trim()) next.email = "Email address is required.";
    else if (!/^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/.test(email.trim()))
      next.email = "Invalid email address.";
    if (!password) next.password = "Password is required.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setApiError("");
    if (!validate()) return;
    setLoading(true);
    try {
      await login(email.trim(), password, remember);
      toast.success("Login successful. Welcome back!");
      navigate(location.state?.from || "/dashboard", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        // Unverified email → the backend sent a fresh verification code.
        setApiError(err.message);
        setTimeout(() => navigate("/verify-otp", { state: { email: email.trim(), purpose: "email_verification" } }), 900);
      } else {
        setApiError(err.message || "Login failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  function handleOtpLogin() {
    if (!email.trim()) {
      setErrors({ email: "Enter your email above first, then use the code login." });
      return;
    }
    navigate("/verify-otp", { state: { email: email.trim(), purpose: "login", sendNow: true } });
  }

  const providerClick = (path) => {
    if (!window.location.origin.startsWith("http")) return;
    window.location.href = path;
  };

  const providerDisabled = (key) => !providers[key];

  return (
    <div className="login-wrapper">
      <div className="card login-card">
        <div className="card-header text-center">
          <div className="d-flex align-items-center justify-content-center gap-2 mb-2">
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                width: 40,
                height: 40,
                borderRadius: 10,
                background: "linear-gradient(135deg, #0f766e 0%, #134e4a 100%)",
                color: "white",
                fontWeight: 700,
                fontSize: 20,
              }}
            >
              D
            </span>
            <h4 className="mb-0 text-dhaniti">Dhaniti</h4>
          </div>
          <p className="text-muted small mb-0">Education Loan Dashboard</p>
          <h5 className="mt-3 mb-0 fw-semibold">Welcome Back</h5>
          <p className="text-muted small">Sign in to continue to your dashboard</p>
        </div>

        <div className="card-body p-4">
          {apiError && (
            <div className="alert alert-danger py-2" role="alert" data-testid="login-error">
              {apiError}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <div className="mb-3">
              <label htmlFor="email" className="form-label">Email</label>
              <input
                type="email"
                className={`form-control ${errors.email ? "is-invalid" : ""}`}
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
                placeholder="you@company.com"
                disabled={loading}
              />
              {errors.email && <div className="invalid-feedback">{errors.email}</div>}
            </div>

            <div className="mb-3">
              <label htmlFor="password" className="form-label d-flex justify-content-between">
                Password
              </label>
              <div className="input-group">
                <input
                  type={showPassword ? "text" : "password"}
                  className={`form-control ${errors.password ? "is-invalid" : ""}`}
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  placeholder="Your password"
                  disabled={loading}
                />
                <button
                  className="btn btn-outline-secondary"
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={-1}
                >
                  <i className={`bi ${showPassword ? "bi-eye-slash" : "bi-eye"}`} aria-hidden="true" />
                </button>
                {errors.password && <div className="invalid-feedback d-block">{errors.password}</div>}
              </div>
            </div>

            <div className="d-flex justify-content-between align-items-center mb-4">
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="remember"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                />
                <label className="form-check-label small" htmlFor="remember">Remember me</label>
              </div>
              <Link to="/forgot-password" className="small">Forgot password?</Link>
            </div>

            <button type="submit" className="btn btn-dhaniti w-100" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
                  Logging in…
                </>
              ) : (
                "LOGIN"
              )}
            </button>
          </form>

          <div className="d-flex align-items-center my-3">
            <hr className="flex-grow-1" />
            <span className="px-2 text-muted small">OR</span>
            <hr className="flex-grow-1" />
          </div>

          <div className="d-grid gap-2">
            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={() => providerClick("/auth/google")}
              disabled={providerDisabled("google")}
              title={providerDisabled("google") ? "Google sign-in is not configured on this server" : "Continue with Google"}
            >
              <svg width="16" height="16" viewBox="0 0 18 18" aria-hidden="true" className="me-2">
                <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62z"/>
                <path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33A8.99 8.99 0 0 0 9 18z"/>
                <path fill="#FBBC05" d="M3.97 10.72a5.4 5.4 0 0 1 0-3.44V4.95H.96a9 9 0 0 0 0 8.1l3.01-2.33z"/>
                <path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.59C13.46.89 11.43 0 9 0A8.99 8.99 0 0 0 .96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58z"/>
              </svg>
              Continue with Google
            </button>
            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={() => providerClick("/auth/github")}
              disabled={providerDisabled("github")}
              title={providerDisabled("github") ? "GitHub sign-in is not configured on this server" : "Continue with GitHub"}
            >
              <i className="bi bi-github me-2" aria-hidden="true" />
              Continue with GitHub
            </button>
            <button type="button" className="btn btn-outline-dhaniti" onClick={handleOtpLogin}>
              <i className="bi bi-shield-lock me-2" aria-hidden="true" />
              Login with OTP
            </button>
          </div>

          <p className="text-center small mt-4 mb-0">
            Don&apos;t have an account? <Link to="/register">Register</Link>
          </p>
        </div>

        <div className="card-footer text-center text-muted small py-2">
          <details className="text-start">
            <summary className="cursor-pointer">Demo credentials (development)</summary>
            <div className="mt-2">
              <div><code>admin@dhaniti.ai</code> / <code>DhanitiAdmin@123</code> — Admin</div>
              <div><code>underwriter@dhaniti.ai</code> / <code>Underwriter@123</code> — Underwriter</div>
              <div><code>analyst@dhaniti.ai</code> / <code>Analyst@123</code> — read-only</div>
            </div>
          </details>
        </div>
      </div>
    </div>
  );
}
