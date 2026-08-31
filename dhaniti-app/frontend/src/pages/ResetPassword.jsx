import React, { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { authApi } from "../api/auth.js";
import { ApiError } from "../api/client.js";
import { useToast } from "../context/ToastContext.jsx";

const RULES = [
  { id: "length", label: "At least 8 characters", test: (p) => p.length >= 8 },
  { id: "letter", label: "At least one letter", test: (p) => /[A-Za-z]/.test(p) },
  { id: "number", label: "At least one number", test: (p) => /\d/.test(p) },
];

export default function ResetPassword() {
  const location = useLocation();
  const navigate = useNavigate();
  const toast = useToast();

  const resetToken = location.state?.resetToken || "";
  const email = location.state?.email || "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!resetToken) navigate("/forgot-password", { replace: true });
  }, [resetToken, navigate]);

  function validate() {
    const next = {};
    if (!password) next.password = "New password is required.";
    else if (RULES.some((r) => !r.test(password))) next.password = "Password must meet the required security rules.";
    if (confirm !== password) next.confirm = "Passwords do not match.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setApiError("");
    if (!validate()) return;
    setLoading(true);
    try {
      await authApi.resetPassword(resetToken, password);
      setDone(true);
      toast.success("Password updated. Sign in with your new password.");
      setTimeout(() => navigate("/login", { replace: true }), 1800);
    } catch (err) {
      setApiError(err instanceof ApiError ? err.message : "Could not reset the password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-wrapper">
      <div className="card login-card" style={{ maxWidth: 420 }}>
        <div className="card-header text-center">
          <h5 className="mb-0 fw-semibold">Choose a new password</h5>
          {email && <p className="text-muted small mb-0 mt-1">for {email}</p>}
        </div>

        <div className="card-body p-4">
          {apiError && <div className="alert alert-danger py-2" role="alert">{apiError}</div>}
          {done && (
            <div className="alert alert-success py-2" role="alert">
              Password updated successfully — redirecting to sign in…
            </div>
          )}

          {!done && (
            <form onSubmit={handleSubmit} noValidate>
              <div className="mb-3">
                <label htmlFor="np" className="form-label">New password</label>
                <input
                  type="password"
                  className={`form-control ${errors.password ? "is-invalid" : ""}`}
                  id="np"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                  disabled={loading}
                />
                {errors.password && <div className="invalid-feedback">{errors.password}</div>}
                <div className="password-rules mt-2">
                  {RULES.map((rule) => (
                    <div key={rule.id} className={`small ${rule.test(password) ? "text-success" : "text-muted"}`}>
                      <i className={`bi ${rule.test(password) ? "bi-check-circle-fill" : "bi-circle"} me-1`} aria-hidden="true" />
                      {rule.label}
                    </div>
                  ))}
                </div>
              </div>

              <div className="mb-4">
                <label htmlFor="npc" className="form-label">Confirm new password</label>
                <input
                  type="password"
                  className={`form-control ${errors.confirm ? "is-invalid" : ""}`}
                  id="npc"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  autoComplete="new-password"
                  disabled={loading}
                />
                {errors.confirm && <div className="invalid-feedback">{errors.confirm}</div>}
              </div>

              <button type="submit" className="btn btn-dhaniti w-100" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
                    Saving…
                  </>
                ) : (
                  "Set new password"
                )}
              </button>
            </form>
          )}

          <p className="text-center small mt-4 mb-0">
            <Link to="/login">Back to sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
