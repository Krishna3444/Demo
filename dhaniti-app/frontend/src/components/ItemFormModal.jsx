import React, { useEffect, useMemo, useState } from "react";
import { itemsApi, formatINR } from "../api/items.js";
import { ApiError } from "../api/client.js";
import { useToast } from "../context/ToastContext.jsx";

const STATES = ["Andhra Pradesh", "Delhi", "Karnataka", "Kerala", "Maharashtra", "Rajasthan", "Tamil Nadu", "Telangana", "Gujarat", "Uttar Pradesh", "West Bengal", "Bihar", "Madhya Pradesh", "Punjab", "Haryana", "Odisha", "Assam", "Jharkhand", "Chhattisgarh", "Uttarakhand", "Himachal Pradesh", "Goa", "Jammu and Kashmir"];
const EMPLOYMENT = ["Salaried", "Self-Employed", "Business", "Pensioner"];
const CHANNELS = ["Website", "Online", "Branch", "Agent", "Campus Drive", "Counsellor", "Institution Referral", "Partner Referral"];
const STATUSES = ["Submitted", "Under Review", "Approved", "Rejected"];

const EMPTY_FORM = {
  studentName: "",
  age: "",
  studentState: "Karnataka",
  institutionId: "",
  courseId: "",
  loanAmountRequestedInr: "",
  parentMonthlyIncomeInr: "",
  existingMonthlyObligationsInr: "",
  creditScore: "",
  employmentType: "Salaried",
  applicationChannel: "Website",
  applicationStatus: "Submitted",
  applicationDate: "",
};

/**
 * Create / Edit modal for loan applications.
 *   mode === "create"  → POST /api/applications
 *   mode === "edit"    → PUT  /api/applications/:id (pre-filled)
 */
export default function ItemFormModal({ show, mode, item, filters, onClose, onSaved }) {
  const toast = useToast();
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [saving, setSaving] = useState(false);

  const isEdit = mode === "edit";

  useEffect(() => {
    if (!show) return;
    setApiError("");
    setErrors({});
    if (isEdit && item) {
      setForm({
        studentName: item.studentName || "",
        age: item.age ?? "",
        studentState: item.studentState || "",
        institutionId: item.institutionId || "",
        courseId: item.courseId || "",
        loanAmountRequestedInr: item.loanAmountRequestedInr ?? "",
        parentMonthlyIncomeInr: item.parentMonthlyIncomeInr ?? "",
        existingMonthlyObligationsInr: item.existingMonthlyObligationsInr ?? "",
        creditScore: item.creditScore ?? "",
        employmentType: item.employmentType || "Salaried",
        applicationChannel: item.applicationChannel || "Website",
        applicationStatus: item.applicationStatus || "Submitted",
        applicationDate: item.applicationDate || "",
      });
    } else {
      setForm({ ...EMPTY_FORM, institutionId: filters?.institutions?.[0]?.id || "", courseId: filters?.courses?.[0]?.id || "" });
    }
  }, [show, isEdit, item, filters]);

  const selectedCourse = useMemo(
    () => (filters?.courses || []).find((c) => c.id === form.courseId),
    [filters, form.courseId]
  );

  const set = (key) => (e) => {
    const value = e.target.value;
    setForm((f) => ({ ...f, [key]: value }));
    setErrors((prev) => ({ ...prev, [key]: undefined }));
  };

  function validate() {
    const next = {};
    if (!form.studentName.trim() || form.studentName.trim().length < 2) next.studentName = "Student name is required (min 2 characters).";
    const age = Number(form.age);
    if (!form.age || Number.isNaN(age) || age < 16 || age > 100) next.age = "Age must be between 16 and 100.";
    if (!form.studentState) next.studentState = "State is required.";
    if (!form.institutionId) next.institutionId = "Select an institution.";
    if (!form.courseId) next.courseId = "Select a course.";
    const loan = Number(form.loanAmountRequestedInr);
    if (!form.loanAmountRequestedInr || Number.isNaN(loan) || loan < 10000) next.loanAmountRequestedInr = "Loan amount must be at least ₹10,000.";
    const income = Number(form.parentMonthlyIncomeInr);
    if (form.parentMonthlyIncomeInr === "" || Number.isNaN(income) || income < 0) next.parentMonthlyIncomeInr = "Parent monthly income is required.";
    const obligations = Number(form.existingMonthlyObligationsInr);
    if (form.existingMonthlyObligationsInr === "" || Number.isNaN(obligations) || obligations < 0) next.existingMonthlyObligationsInr = "Existing obligations are required.";
    if (form.creditScore !== "" && form.creditScore !== null && form.creditScore !== undefined) {
      const score = Number(form.creditScore);
      if (Number.isNaN(score) || score < 300 || score > 900) next.creditScore = "Credit score must be between 300 and 900 (or leave blank).";
    }
    if (!form.employmentType) next.employmentType = "Employment type is required.";
    if (!form.applicationChannel) next.applicationChannel = "Application channel is required.";
    if (isEdit) {
      if (!form.applicationStatus || !STATUSES.includes(form.applicationStatus)) next.applicationStatus = "Select a valid status.";
      if (!form.applicationDate || !/^\d{4}-\d{2}-\d{2}$/.test(form.applicationDate)) next.applicationDate = "Application date must be YYYY-MM-DD.";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  function buildPayload() {
    const payload = {
      studentName: form.studentName.trim(),
      age: Number(form.age),
      studentState: form.studentState,
      institutionId: form.institutionId,
      courseId: form.courseId,
      loanAmountRequestedInr: Number(form.loanAmountRequestedInr),
      parentMonthlyIncomeInr: Number(form.parentMonthlyIncomeInr),
      existingMonthlyObligationsInr: Number(form.existingMonthlyObligationsInr),
      creditScore: form.creditScore === "" || form.creditScore === null ? null : Number(form.creditScore),
      employmentType: form.employmentType,
      applicationChannel: form.applicationChannel,
    };
    if (isEdit) {
      payload.applicationStatus = form.applicationStatus;
      payload.applicationDate = form.applicationDate;
    }
    return payload;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setApiError("");
    if (!validate()) return;
    setSaving(true);
    try {
      if (isEdit) {
        await itemsApi.updateItem(item.id, buildPayload());
        toast.success(`Record ${item.id} updated successfully.`);
      } else {
        const created = await itemsApi.createItem(buildPayload());
        toast.success(`Record ${created.id} created successfully.`);
      }
      onSaved();
    } catch (err) {
      if (err instanceof ApiError && err.details?.length) {
        setApiError(`${err.message} ${err.details.join(" ")}`);
      } else {
        setApiError(err.message || "Unable to save record.");
      }
    } finally {
      setSaving(false);
    }
  }

  if (!show) return null;

  const invalid = (field) => (errors[field] ? "is-invalid" : "");

  return (
    <div className="modal fade show d-block" tabIndex={-1} role="dialog" style={{ background: "rgba(15,23,42,0.45)" }} aria-modal="true">
      <div className="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable" role="document">
        <div className="modal-content">
          <form onSubmit={handleSubmit} noValidate>
            <div className="modal-header">
              <h5 className="modal-title">
                <i className={`bi ${isEdit ? "bi-pencil-square" : "bi-plus-circle"} text-dhaniti me-2`} aria-hidden="true" />
                {isEdit ? `Edit Application ${item?.id}` : "New Loan Application"}
              </h5>
              <button type="button" className="btn-close" aria-label="Close" onClick={onClose} disabled={saving} />
            </div>

            <div className="modal-body">
              {apiError && <div className="alert alert-danger py-2" role="alert">{apiError}</div>}

              <div className="row g-3">
                <div className="col-12 col-md-6">
                  <label className="form-label" htmlFor="f-name">Student name *</label>
                  <input id="f-name" className={`form-control ${invalid("studentName")}`} value={form.studentName} onChange={set("studentName")} disabled={saving} />
                  {errors.studentName && <div className="invalid-feedback">{errors.studentName}</div>}
                </div>

                <div className="col-6 col-md-3">
                  <label className="form-label" htmlFor="f-age">Age *</label>
                  <input id="f-age" type="number" min={16} max={100} className={`form-control ${invalid("age")}`} value={form.age} onChange={set("age")} disabled={saving} />
                  {errors.age && <div className="invalid-feedback">{errors.age}</div>}
                </div>

                <div className="col-6 col-md-3">
                  <label className="form-label" htmlFor="f-state">State *</label>
                  <select id="f-state" className={`form-select ${invalid("studentState")}`} value={form.studentState} onChange={set("studentState")} disabled={saving}>
                    {STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                <div className="col-12 col-md-6">
                  <label className="form-label" htmlFor="f-inst">Institution *</label>
                  <select id="f-inst" className={`form-select ${invalid("institutionId")}`} value={form.institutionId} onChange={set("institutionId")} disabled={saving}>
                    <option value="">Select institution…</option>
                    {(filters?.institutions || []).map((i) => <option key={i.id} value={i.id}>{i.name} ({i.id})</option>)}
                  </select>
                  {errors.institutionId && <div className="invalid-feedback">{errors.institutionId}</div>}
                </div>

                <div className="col-12 col-md-6">
                  <label className="form-label" htmlFor="f-course">Course *</label>
                  <select id="f-course" className={`form-select ${invalid("courseId")}`} value={form.courseId} onChange={set("courseId")} disabled={saving}>
                    <option value="">Select course…</option>
                    {(filters?.courses || []).map((c) => <option key={c.id} value={c.id}>{c.name} — {c.domain}{c.typicalFeeInr ? ` (fee ${formatINR(c.typicalFeeInr)})` : ""}</option>)}
                  </select>
                  {errors.courseId && <div className="invalid-feedback">{errors.courseId}</div>}
                </div>

                <div className="col-6 col-md-4">
                  <label className="form-label" htmlFor="f-loan">Loan requested (₹) *</label>
                  <input id="f-loan" type="number" min={10000} step={10000} className={`form-control ${invalid("loanAmountRequestedInr")}`} value={form.loanAmountRequestedInr} onChange={set("loanAmountRequestedInr")} disabled={saving} />
                  {errors.loanAmountRequestedInr && <div className="invalid-feedback">{errors.loanAmountRequestedInr}</div>}
                  {selectedCourse?.typicalFeeInr && Number(form.loanAmountRequestedInr) > selectedCourse.typicalFeeInr && (
                    <div className="form-text text-warning"><i className="bi bi-exclamation-triangle me-1" aria-hidden="true" />Exceeds typical fee ({formatINR(selectedCourse.typicalFeeInr)}) — will be flagged.</div>
                  )}
                </div>

                <div className="col-6 col-md-4">
                  <label className="form-label" htmlFor="f-income">Parent income (₹/mo) *</label>
                  <input id="f-income" type="number" min={0} step={1000} className={`form-control ${invalid("parentMonthlyIncomeInr")}`} value={form.parentMonthlyIncomeInr} onChange={set("parentMonthlyIncomeInr")} disabled={saving} />
                  {errors.parentMonthlyIncomeInr && <div className="invalid-feedback">{errors.parentMonthlyIncomeInr}</div>}
                </div>

                <div className="col-6 col-md-4">
                  <label className="form-label" htmlFor="f-obl">Existing obligations (₹/mo) *</label>
                  <input id="f-obl" type="number" min={0} step={500} className={`form-control ${invalid("existingMonthlyObligationsInr")}`} value={form.existingMonthlyObligationsInr} onChange={set("existingMonthlyObligationsInr")} disabled={saving} />
                  {errors.existingMonthlyObligationsInr && <div className="invalid-feedback">{errors.existingMonthlyObligationsInr}</div>}
                </div>

                <div className="col-6 col-md-4">
                  <label className="form-label" htmlFor="f-score">Credit score</label>
                  <input id="f-score" type="number" min={300} max={900} placeholder="300–900 (optional)" className={`form-control ${invalid("creditScore")}`} value={form.creditScore ?? ""} onChange={set("creditScore")} disabled={saving} />
                  {errors.creditScore && <div className="invalid-feedback">{errors.creditScore}</div>}
                </div>

                <div className="col-6 col-md-4">
                  <label className="form-label" htmlFor="f-emp">Employment type *</label>
                  <select id="f-emp" className={`form-select ${invalid("employmentType")}`} value={form.employmentType} onChange={set("employmentType")} disabled={saving}>
                    {EMPLOYMENT.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                <div className="col-6 col-md-4">
                  <label className="form-label" htmlFor="f-chan">Channel *</label>
                  <select id="f-chan" className={`form-select ${invalid("applicationChannel")}`} value={form.applicationChannel} onChange={set("applicationChannel")} disabled={saving}>
                    {CHANNELS.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                {isEdit && (
                  <>
                    <div className="col-6 col-md-6">
                      <label className="form-label" htmlFor="f-status">Status *</label>
                      <select id="f-status" className={`form-select ${invalid("applicationStatus")}`} value={form.applicationStatus} onChange={set("applicationStatus")} disabled={saving}>
                        {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </div>
                    <div className="col-6 col-md-6">
                      <label className="form-label" htmlFor="f-date">Application date *</label>
                      <input id="f-date" type="date" className={`form-control ${invalid("applicationDate")}`} value={form.applicationDate} onChange={set("applicationDate")} disabled={saving} />
                      {errors.applicationDate && <div className="invalid-feedback">{errors.applicationDate}</div>}
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <button type="button" className="btn btn-outline-secondary" onClick={onClose} disabled={saving}>Cancel</button>
              <button type="submit" className="btn btn-dhaniti" disabled={saving}>
                {saving ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
                    Saving…
                  </>
                ) : isEdit ? "Save changes" : "Create record"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
