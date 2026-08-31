import React from "react";
import { formatINR, statusClass, attentionClass } from "../api/items.js";

function Row({ label, value }) {
  return (
    <div className="col-12 col-md-6 mb-2">
      <div className="small text-muted">{label}</div>
      <div className="fw-medium">{value ?? "—"}</div>
    </div>
  );
}

/** Read-only details modal for a loan application. */
export default function ItemViewModal({ show, item, onClose, onEdit, canWrite }) {
  if (!show || !item) return null;

  return (
    <div className="modal fade show d-block" tabIndex={-1} role="dialog" style={{ background: "rgba(15,23,42,0.45)" }} aria-modal="true">
      <div className="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable" role="document">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title d-flex align-items-center gap-2">
              <i className="bi bi-file-earmark-text text-dhaniti" aria-hidden="true" />
              Application <span className="text-dhaniti">{item.id}</span>
            </h5>
            <button type="button" className="btn-close" aria-label="Close" onClick={onClose} />
          </div>

          <div className="modal-body">
            <div className="d-flex flex-wrap gap-2 mb-3">
              <span className={`dq-pill ${statusClass(item.applicationStatus)}`}>{item.applicationStatus}</span>
              <span className={`dq-pill ${attentionClass(item.attentionLevel)}`}>{item.attentionLevel}</span>
              {item.dataQualityFlags?.map((flag) => (
                <span key={flag} className="dq-pill dq-flag" title={flag}>{flag.replaceAll("_", " ").toLowerCase()}</span>
              ))}
            </div>

            <div className="row">
              <Row label="Student name" value={item.studentName} />
              <Row label="Age" value={item.age} />
              <Row label="State" value={item.studentState} />
              <Row label="Employment type" value={item.employmentType} />
              <Row label="Institution" value={`${item.institutionName} (${item.institutionId})`} />
              <Row label="Course" value={`${item.courseName} — ${item.courseDomain} (${item.courseId})`} />
              <Row label="Course fee" value={formatINR(item.courseFeeInr)} />
              <Row label="Loan requested" value={formatINR(item.loanAmountRequestedInr)} />
              <Row label="Parent monthly income" value={formatINR(item.parentMonthlyIncomeInr)} />
              <Row label="Existing obligations" value={formatINR(item.existingMonthlyObligationsInr)} />
              <Row label="Credit score" value={item.creditScore ?? "N/A (missing)"} />
              <Row label="Debt-to-income ratio" value={item.debtToIncomeRatio !== null && item.debtToIncomeRatio !== undefined ? `${(item.debtToIncomeRatio * 100).toFixed(1)}%` : "—"} />
              <Row label="Loan-to-fee ratio" value={item.loanToFeeRatio !== null && item.loanToFeeRatio !== undefined ? `${(item.loanToFeeRatio * 100).toFixed(1)}%` : "—"} />
              <Row label="Application date" value={item.applicationDate} />
              <Row label="Channel" value={item.applicationChannel} />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-outline-secondary" onClick={onClose}>Close</button>
            {canWrite && (
              <button type="button" className="btn btn-dhaniti" onClick={onEdit}>
                <i className="bi bi-pencil-square me-1" aria-hidden="true" />
                Edit
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
