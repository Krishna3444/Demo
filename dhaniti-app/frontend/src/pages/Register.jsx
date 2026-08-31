import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../api/auth.js";
import { ApiError } from "../api/client.js";
import { useToast } from "../context/ToastContext.jsx";

const PASSWORD_RULES = [
  { id: "length", label: "At least 8 characters", test: (p) => p.length >= 8 },
  { id: "letter", label: "At least one letter", test: (p) => /[A-Za-z]/.test(p) },
  { id: "number", label: "At least one number", test: (p) => /\d/.test(p) },
];

export default function Register() {
  const navigate = useNavigate();
  const toast = useToast();

  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  function validate() {
    const next = {};
    if (!form.name.trim()) next.name = "Name is required.";
    else if (form.name.trim().length < 2) next.name = "Name must be at least 2 characters long.";
    if (!form.email.trim()) next.email = "Email address is required.";
    else if (!/^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/.test(form.email.trim()))
      next.email = "Invalid email address.";
    if (!form.password) next.password = "Password is required.";
    else if (PASSWORD_RULES.some((r) => !r.test(form.password)))
      next.password = "Password must meet the required security rules.";
    if (form.confirm !== form.password) next.confirm = "Passwords do not match.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setApiError("");
    if (!validate()) return;
    setLoading(true);
    try {
      await authApi.register(form.name.trim(), form.email.trim(), form.password, form.confirm);
      toast.success("Account created — check your email for the verification code.");
      navigate("/verify-otp", {
        state: { email: form.email.trim(), purpose: "email_verification" },
      });
    } catch (err) {
      setApiError(err instanceof ApiError && err.details.length ? `${err.message} ${err.details.join(" ")}` : err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-wrapper">
      <div className="card login-card">
        <div className="card-header text-center">
          <h4 className="mb-0 text-dhaniti">Create your account</h4>
          <p className="text-muted small mb-0 mt-1">
            Join the Dhaniti Education Loan Dashboard
          </p>
        </div>

        <div className="card-body p-4">
          {apiError && <div className="alert alert-danger py-2" role="alert">{apiError}</div>}

          <form onSubmit={handleSubmit} noValidate>
            <div className="mb-3">
              <label htmlFor="name" className="form-label">Full name</label>
              <input
                type="text"
                className={`form-control ${errors.name ? "is-invalid" : ""}`}
                id="name"
                value={form.name}
                onChange={set("name")}
                autoComplete="name"
                disabled={loading}
              />
              {errors.name && <div className="invalid-feedback">{errors.name}</div>}
            </div>

            <div className="mb-3">
              <label htmlFor="reg-email" className="form-label">Email</label>
              <input
                type="email"
                className={`form-control ${errors.email ? "is-invalid" : ""}`}
                id="reg-email"
                value={form.email}
                onChange={set("email")}
                autoComplete="username"
                disabled={loading}
              />
              {errors.email && <div className="invalid-feedback">{errors.email}</div>}
            </div>

            <div className="mb-3">
              <label htmlFor="reg-password" className="form-label">Password</label>
              <div className="input-group">
                <input
                  type={showPassword ? "text" : "password"}
                  className={`form-control ${errors.password ? "is-invalid" : ""}`}
                  id="reg-password"
                  value={form.password}
                  onChange={set("password")}
                  autoComplete="new-password"
                  disabled={loading}
                />
                <button
                  className="btn btn-outline-secondary"
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  tabIndex={-1}
                  aria-label="Toggle password visibility"
                >
                  <i className={`bi ${showPassword ? "bi-eye-slash" : "bi-eye"}`} aria-hidden="true" />
                </button>
              </div>
              {errors.password && <div className="invalid-feedback d-block">{errors.password}</div>}
              <div className="password-rules mt-2">
                {PASSWORD_RULES.map((rule) => (
                  <div key={rule.id} className={`small ${rule.test(form.password) ? "text-success" : "text-muted"}`}>
                    <i className={`bi ${rule.test(form.password) ? "bi-check-circle-fill" : "bi-circle"} me-1`} aria-hidden="true" />
                    {rule.label}
                  </div>
                ))}
              </div>
            </div>

            <div className="mb-4">
              <label htmlFor="reg-confirm" className="form-label">Confirm password</label>
              <input
                type={showPassword ? "text" : "password"}
                className={`form-control ${errors.confirm ? "is-invalid" : ""}`}
                id="reg-confirm"
                value={form.confirm}
                onChange={set("confirm")}
                autoComplete="new-password"
                disabled={loading}
              />
              {errors.confirm && <div className="invalid-feedback">{errors.confirm}</div>}
            </div>

            <button type="submit" className="btn btn-dhaniti w-100" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
                  Creating account…
                </>
              ) : (
                "Create account"
              )}
            </button>
          </form>

          <p className="text-center small mt-4 mb-0">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
