import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const ROLE_BADGE = {
  Admin: "text-bg-danger",
  Underwriter: "text-bg-info",
  "Risk Officer": "text-bg-warning",
  "Credit Analyst": "text-bg-secondary",
};

export default function Navbar() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  const initials = (currentUser?.name || "?")
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dhaniti app-navbar sticky-top">
      <div className="container-fluid px-3 px-md-4">
        <NavLink className="navbar-brand d-flex align-items-center gap-2" to="/dashboard">
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 34,
              height: 34,
              borderRadius: 9,
              background: "rgba(255,255,255,0.15)",
              fontWeight: 700,
              fontSize: 17,
            }}
          >
            D
          </span>
          <span className="d-none d-sm-inline">Dhaniti</span>
        </NavLink>

        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#mainNav"
          aria-controls="mainNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon" />
        </button>

        <div className="collapse navbar-collapse" id="mainNav">
          <ul className="navbar-nav me-auto mb-2 mb-lg-0">
            <li className="nav-item">
              <NavLink className="nav-link" to="/dashboard">Dashboard</NavLink>
            </li>
            <li className="nav-item">
              <NavLink className="nav-link" to="/applications">Applications</NavLink>
            </li>
            <li className="nav-item">
              <NavLink className="nav-link" to="/profile">Profile</NavLink>
            </li>
          </ul>

          <div className="d-flex align-items-center gap-2 flex-wrap">
            {currentUser && (
              <>
                <span className={`badge ${ROLE_BADGE[currentUser.role] || "text-bg-secondary"}`}>
                  {currentUser.role}
                </span>
                <span className="d-none d-md-inline text-white-50 small">
                  {currentUser.name}
                </span>
                {currentUser.avatarUrl ? (
                  <img
                    src={currentUser.avatarUrl}
                    alt=""
                    className="rounded-circle"
                    style={{ width: 32, height: 32, objectFit: "cover" }}
                  />
                ) : (
                  <span
                    className="rounded-circle d-inline-flex align-items-center justify-content-center"
                    style={{ width: 32, height: 32, background: "rgba(255,255,255,0.18)", fontWeight: 600 }}
                    title={currentUser.name}
                  >
                    {initials}
                  </span>
                )}
                <button className="btn btn-sm btn-outline-light" onClick={handleLogout}>
                  <i className="bi bi-box-arrow-right me-1" aria-hidden="true" />
                  Logout
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
