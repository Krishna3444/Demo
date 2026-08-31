import React, { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { authApi } from "../api/auth.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useToast } from "../context/ToastContext.jsx";

/**
 * Landing page after an OAuth provider redirects back:
 *   /oauth/callback?code=<one-time-code>&status=success
 *   /oauth/callback?status=error&message=...
 *
 * The one-time code is exchanged for the real session token via
 * POST /api/auth/oauth/exchange (so the JWT never appears in a URL).
 */
export default function OAuthCallback() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();
  const { applySession } = useAuth();
  const [error, setError] = useState("");
  const exchanged = useRef(false);

  useEffect(() => {
    if (exchanged.current) return;
    exchanged.current = true;

    const status = params.get("status");
    const code = params.get("code");
    const message = params.get("message");

    if (status === "error") {
      setError(message || "OAuth sign-in failed. Please try again.");
      return;
    }
    if (!code) {
      setError("Missing sign-in code. Please start the sign-in flow again.");
      return;
    }

    (async () => {
      try {
        const { token, user } = await authApi.oauthExchange(code);
        applySession(token, user);
        toast.success(`Welcome, ${user.name}!`);
        navigate("/dashboard", { replace: true });
      } catch (err) {
        setError(err.message || "Could not complete OAuth sign-in.");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="login-wrapper">
      <div className="card login-card" style={{ maxWidth: 420 }}>
        <div className="card-body p-4 text-center">
          {error ? (
            <>
              <div
                className="mx-auto mb-3 d-flex align-items-center justify-content-center"
                style={{ width: 52, height: 52, borderRadius: 14, background: "#fef2f2", color: "#dc2626", fontSize: 24 }}
              >
                <i className="bi bi-x-circle" aria-hidden="true" />
              </div>
              <h5 className="fw-semibold mb-2">Sign-in failed</h5>
              <p className="text-muted small">{error}</p>
              <Link to="/login" className="btn btn-dhaniti w-100 mt-2">
                Back to sign in
              </Link>
            </>
          ) : (
            <>
              <div className="spinner-border text-dhaniti mb-3" role="status" aria-hidden="true" style={{ width: 44, height: 44 }} />
              <h5 className="fw-semibold mb-1">Completing sign-in…</h5>
              <p className="text-muted small mb-0">Verifying your identity with the provider.</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
