import React from "react";

/**
 * Generic confirmation modal (used for delete confirmation).
 */
export default function ConfirmModal({ show, title, message, confirmLabel = "Delete", confirmClass = "btn-danger", loading = false, onConfirm, onCancel }) {
  if (!show) return null;
  return (
    <div className="modal fade show d-block" tabIndex={-1} role="dialog" style={{ background: "rgba(15,23,42,0.45)" }}>
      <div className="modal-dialog modal-dialog-centered" role="document">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              <i className="bi bi-exclamation-triangle text-danger me-2" aria-hidden="true" />
              {title}
            </h5>
            <button type="button" className="btn-close" aria-label="Close" onClick={onCancel} disabled={loading} />
          </div>
          <div className="modal-body">
            <p className="mb-0">{message}</p>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-outline-secondary" onClick={onCancel} disabled={loading}>
              Cancel
            </button>
            <button type="button" className={`btn ${confirmClass}`} onClick={onConfirm} disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
                  Deleting…
                </>
              ) : (
                confirmLabel
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
