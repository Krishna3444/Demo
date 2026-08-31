import React from "react";
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="d-flex flex-column align-items-center justify-content-center text-center" style={{ minHeight: "70vh" }}>
      <h1 className="display-1 fw-bold text-dhaniti mb-0">404</h1>
      <h4 className="mb-2">Page not found</h4>
      <p className="text-muted mb-4" style={{ maxWidth: 420 }}>
        The page you are looking for doesn&apos;t exist or may have been moved.
        Check the address or head back to your dashboard.
      </p>
      <div className="d-flex gap-2">
        <Link to="/dashboard" className="btn btn-dhaniti">
          <i className="bi bi-house-door me-1" aria-hidden="true" />
          Go to dashboard
        </Link>
        <Link to="/login" className="btn btn-outline-secondary">Sign in</Link>
      </div>
    </div>
  );
}
