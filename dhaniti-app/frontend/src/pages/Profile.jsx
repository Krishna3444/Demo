import React, { useState } from "react";
import { authApi } from "../api/auth.js";
import { ApiError } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useToast } from "../context/ToastContext.jsx";

const PROVIDER_LABEL = { local: "Email & password", google: "Google", github: "GitHub" };

export default function Profile() {
  const { currentUser, refreshUser } = useAuth();
  const toast = useToast();

  const [profile, setProfile] = useState({
    name: currentUser?.name || "",
    avatarUrl: currentUser?.avatarUrl || "",
  });
  const [profileErrors, setProfileErrors] = useState({});
  const [profileError, setProfileError] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);

  const [pw, setPw] = useState({ currentPassword: "", newPassword: "", confirm: "" });
  const [pwErrors, setPwErrors] = useState({});
  const [pwError, setPwError] = useState("");
  const [savingPw, setSavingPw] = useState(false);

  if (!currentUser) return null;

  async function saveProfile(e) {
    e.preventDefault();
    setProfileError("");
    const errors = {};
    if (!profile.name.trim() || profile.name.trim().length < 2) errors.name = "Name must be at least 2 characters long.";
    if (profile.avatarUrl && !/^https?:\/\//.test(profile.avatarUrl.trim())) errors.avatarUrl = "Avatar URL must start with http:// or https://.";
    setProfileErrors(errors);
    if (Object.keys(errors).length) return;

    setSavingProfile(true);
    try {
      await authApi.updateProfile({ name: profile.name.trim(), avatarUrl: profile.avatarUrl.trim() });
      await refreshUser();
      toast.success("Profile updated successfully.");
    } catch (err) {
      setProfileError(err instanceof ApiError && err.details?.length ? `${err.message} ${err.details.join(" ")}` : err.message);
    } finally {
      setSavingProfile(false);
    }
  }

  async function changePassword(e) {
    e.preventDefault();
    setPwError("");
    const errors = {};
    if (!pw.currentPassword) errors.currentPassword = "Current password is required.";
    if (!pw.newPassword || pw.newPassword.length < 8 || !/[A-Za-z]/.test(pw.newPassword) || !/\d/.test(pw.newPassword))
      errors.newPassword = "New password needs 8+ characters with at least one letter and one number.";
    if (pw.confirm !== pw.newPassword) errors.confirm = "Passwords do not match.";
    setPwErrors(errors);
    if (Object.keys(errors).length) return;

    setSavingPw(true);
    try {
      await authApi.changePassword(pw.currentPassword, pw.newPassword);
      toast.success("Password changed successfully.");
      setPw({ currentPassword: "", newPassword: "", confirm: "" });
    } catch (err) {
      setPwError(err.message);
    } finally {
      setSavingPw(false);
    }
  }

  const initials = (currentUser.name || "?").split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase();

  return (
    <div className="container py-4" style={{ maxWidth: 900 }}>
      <h4 className="mb-1">Profile</h4>
      <p className="text-muted small">Manage your account details and password.</p>

      <div className="row g-4">
        {/* Identity card */}
        <div className="col-12 col-lg-4">
          <div className="card section-card h-100">
            <div className="card-body text-center">
              {currentUser.avatarUrl ? (
                <img src={currentUser.avatarUrl} alt="Avatar" className="rounded-circle mb-3" style={{ width: 96, height: 96, objectFit: "cover" }} />
              ) : (
                <div
                  className="rounded-circle mx-auto mb-3 d-flex align-items-center justify-content-center bg-dhaniti text-white"
                  style={{ width: 96, height: 96, fontSize: 34, fontWeight: 700 }}
                >
                  {initials}
                </div>
              )}
              <h5 className="mb-1">{currentUser.name}</h5>
              <p className="text-muted small mb-2">{currentUser.email}</p>
              <span className="badge text-bg-dark">{currentUser.role}</span>
              <hr />
              <dl className="text-start small mb-0">
                <div className="d-flex justify-content-between">
                  <dt className="text-muted fw-normal">Sign-in method</dt>
                  <dd className="mb-1">{PROVIDER_LABEL[currentUser.oauthProvider] || currentUser.oauthProvider}</dd>
                </div>
                <div className="d-flex justify-content-between">
                  <dt className="text-muted fw-normal">Email verified</dt>
                  <dd className="mb-1">
                    {currentUser.isVerified ? (
                      <span className="text-success"><i className="bi bi-check-circle-fill me-1" aria-hidden="true" />Yes</span>
                    ) : (
                      <span className="text-warning">Pending</span>
                    )}
                  </dd>
                </div>
                <div className="d-flex justify-content-between">
                  <dt className="text-muted fw-normal">User ID</dt>
                  <dd className="mb-0 font-monospace" style={{ fontSize: "0.72rem" }}>{currentUser.userId}</dd>
                </div>
              </dl>
            </div>
          </div>
        </div>

        {/* Edit profile + password */}
        <div className="col-12 col-lg-8">
          <div className="card section-card mb-4">
            <div className="card-header">Edit profile</div>
            <div className="card-body">
              {profileError && <div className="alert alert-danger py-2">{profileError}</div>}
              <form onSubmit={saveProfile} noValidate>
                <div className="mb-3">
                  <label htmlFor="p-name" className="form-label">Full name</label>
                  <input
                    id="p-name"
                    className={`form-control ${profileErrors.name ? "is-invalid" : ""}`}
                    value={profile.name}
                    onChange={(e) => setProfile((p) => ({ ...p, name: e.target.value }))}
                    disabled={savingProfile}
                  />
                  {profileErrors.name && <div className="invalid-feedback">{profileErrors.name}</div>}
                </div>
                <div className="mb-3">
                  <label htmlFor="p-avatar" className="form-label">Avatar URL <span className="text-muted small">(optional)</span></label>
                  <input
                    id="p-avatar"
                    className={`form-control ${profileErrors.avatarUrl ? "is-invalid" : ""}`}
                    value={profile.avatarUrl}
                    onChange={(e) => setProfile((p) => ({ ...p, avatarUrl: e.target.value }))}
                    placeholder="https://…"
                    disabled={savingProfile}
                  />
                  {profileErrors.avatarUrl && <div className="invalid-feedback">{profileErrors.avatarUrl}</div>}
                </div>
                <button className="btn btn-dhaniti" disabled={savingProfile}>
                  {savingProfile ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
                      Saving…
                    </>
                  ) : "Save changes"}
                </button>
              </form>
            </div>
          </div>

          {currentUser.hasPassword !== false && (
            <div className="card section-card">
              <div className="card-header">Change password</div>
              <div className="card-body">
                {pwError && <div className="alert alert-danger py-2">{pwError}</div>}
                <form onSubmit={changePassword} noValidate>
                  <div className="mb-3">
                    <label htmlFor="cp-current" className="form-label">Current password</label>
                    <input
                      type="password"
                      id="cp-current"
                      className={`form-control ${pwErrors.currentPassword ? "is-invalid" : ""}`}
                      value={pw.currentPassword}
                      onChange={(e) => setPw((p) => ({ ...p, currentPassword: e.target.value }))}
                      autoComplete="current-password"
                      disabled={savingPw}
                    />
                    {pwErrors.currentPassword && <div className="invalid-feedback">{pwErrors.currentPassword}</div>}
                  </div>
                  <div className="row">
                    <div className="col-12 col-md-6 mb-3">
                      <label htmlFor="cp-new" className="form-label">New password</label>
                      <input
                        type="password"
                        id="cp-new"
                        className={`form-control ${pwErrors.newPassword ? "is-invalid" : ""}`}
                        value={pw.newPassword}
                        onChange={(e) => setPw((p) => ({ ...p, newPassword: e.target.value }))}
                        autoComplete="new-password"
                        disabled={savingPw}
                      />
                      {pwErrors.newPassword && <div className="invalid-feedback">{pwErrors.newPassword}</div>}
                    </div>
                    <div className="col-12 col-md-6 mb-3">
                      <label htmlFor="cp-confirm" className="form-label">Confirm new password</label>
                      <input
                        type="password"
                        id="cp-confirm"
                        className={`form-control ${pwErrors.confirm ? "is-invalid" : ""}`}
                        value={pw.confirm}
                        onChange={(e) => setPw((p) => ({ ...p, confirm: e.target.value }))}
                        autoComplete="new-password"
                        disabled={savingPw}
                      />
                      {pwErrors.confirm && <div className="invalid-feedback">{pwErrors.confirm}</div>}
                    </div>
                  </div>
                  <button className="btn btn-outline-dhaniti" disabled={savingPw}>
                    {savingPw ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
                        Updating…
                      </>
                    ) : "Update password"}
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
