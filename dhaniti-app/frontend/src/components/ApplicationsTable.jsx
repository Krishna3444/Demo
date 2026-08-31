import React, { useEffect, useState } from "react";
import { itemsApi, formatINR, statusClass, attentionClass } from "../api/items.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import ConfirmModal from "./ConfirmModal.jsx";
import ItemFormModal from "./ItemFormModal.jsx";
import ItemViewModal from "./ItemViewModal.jsx";

const STATUS_OPTIONS = ["Submitted", "Under Review", "Approved", "Rejected"];
const PAGE_SIZE = 10;

export default function ApplicationsTable({ filters }) {
  const toast = useToast();
  const { canWrite } = useAuth();

  const [apps, setApps] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [course, setCourse] = useState("all");
  const [inst, setInst] = useState("all");
  const [att, setAtt] = useState("all");
  const [sortBy, setSortBy] = useState("applicationDate");
  const [sortDir, setSortDir] = useState("desc");

  const [editingId, setEditingId] = useState(null);
  const [editStatus, setEditStatus] = useState("");
  const [statusSaving, setStatusSaving] = useState(false);

  // Modals
  const [viewItem, setViewItem] = useState(null);
  const [formModal, setFormModal] = useState({ show: false, mode: "create", item: null });
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  function buildQuery(extra = {}) {
    const params = {
      search,
      status,
      courseId: course,
      institutionId: inst,
      attentionLevel: att,
      sortBy,
      sortDir,
      page: extra.page ?? page,
      pageSize: PAGE_SIZE,
      ...extra,
    };
    const search_ = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "" && value !== "all") {
        search_.set(key, value);
      }
    });
    return search_.toString();
  }

  async function loadRows(queryString = buildQuery()) {
    setLoading(true);
    try {
      const res = await itemsApi.getItems(
        Object.fromEntries(new URLSearchParams(queryString))
      );
      setApps(res.data || []);
      setTotal(res.count ?? (res.data || []).length);
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      loadRows(buildQuery({ page: 1 }));
    }, 250); // debounce search typing
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, status, course, inst, att, sortBy, sortDir]);

  useEffect(() => {
    if (page > 1) loadRows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  function toggleSort(col) {
    if (sortBy === col) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortBy(col);
      setSortDir("desc");
    }
  }

  async function saveStatus(app) {
    setStatusSaving(true);
    try {
      await itemsApi.updateStatus(app.id, editStatus);
      toast.success(`Updated ${app.id} \u2192 ${editStatus}`);
      setEditingId(null);
      await loadRows();
    } catch (e) {
      toast.error(`Error updating status: ${e.message}`);
    } finally {
      setStatusSaving(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await itemsApi.deleteItem(deleteTarget.id);
      toast.success(`Record ${deleteTarget.id} deleted successfully.`);
      setDeleteTarget(null);
      // If we deleted the last row on the last page, step back one page.
      if (apps.length === 1 && page > 1) {
        setPage(page - 1);
      } else {
        await loadRows();
      }
    } catch (e) {
      toast.error(`Error deleting record: ${e.message}`);
    } finally {
      setDeleting(false);
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const from = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const to = Math.min(page * PAGE_SIZE, total);

  return (
    <div>
      {/* Toolbar */}
      <div className="row g-2 mb-3 align-items-center">
        <div className="col-12 col-md-3">
          <div className="input-group input-group-sm">
            <span className="input-group-text"><i className="bi bi-search" aria-hidden="true" /></span>
            <input
              type="search"
              className="form-control"
              placeholder="Search by App ID or student name…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search applications"
            />
          </div>
        </div>
        <div className="col-6 col-md-2">
          <select className="form-select form-select-sm" value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filter by status">
            <option value="all">All statuses</option>
            {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="col-6 col-md-2">
          <select className="form-select form-select-sm" value={course} onChange={(e) => setCourse(e.target.value)} aria-label="Filter by course">
            <option value="all">All courses</option>
            {filters?.courses?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="col-6 col-md-2">
          <select className="form-select form-select-sm" value={inst} onChange={(e) => setInst(e.target.value)} aria-label="Filter by institution">
            <option value="all">All institutions</option>
            {filters?.institutions?.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
          </select>
        </div>
        <div className="col-6 col-md-2">
          <select className="form-select form-select-sm" value={att} onChange={(e) => setAtt(e.target.value)} aria-label="Filter by attention level">
            <option value="all">All attention levels</option>
            <option value="Low Attention">Low Attention</option>
            <option value="Review Required">Review Required</option>
            <option value="High Attention">High Attention</option>
          </select>
        </div>
        <div className="col-12 col-md-1 d-flex gap-1">
          <button type="button" className={`sort-btn ${sortBy === "loanAmountRequestedInr" ? "active" : ""}`} onClick={() => toggleSort("loanAmountRequestedInr")} title="Sort by loan amount">
            Loan {sortBy === "loanAmountRequestedInr" ? (sortDir === "asc" ? "\u2191" : "\u2193") : "\u2195"}
          </button>
          <button type="button" className={`sort-btn ${sortBy === "creditScore" ? "active" : ""}`} onClick={() => toggleSort("creditScore")} title="Sort by credit score">
            Credit {sortBy === "creditScore" ? (sortDir === "asc" ? "\u2191" : "\u2193") : "\u2195"}
          </button>
          <button type="button" className={`sort-btn ${sortBy === "applicationDate" ? "active" : ""}`} onClick={() => toggleSort("applicationDate")} title="Sort by application date">
            Date {sortBy === "applicationDate" ? (sortDir === "asc" ? "\u2191" : "\u2193") : "\u2195"}
          </button>
        </div>
        {canWrite && (
          <div className="col-12 col-md-12 text-md-end">
            <button type="button" className="btn btn-sm btn-dhaniti" onClick={() => setFormModal({ show: true, mode: "create", item: null })}>
              <i className="bi bi-plus-circle me-1" aria-hidden="true" />
              Add Record
            </button>
          </div>
        )}
      </div>

      {error && <div className="alert alert-danger py-2 mb-3">Error: {error}</div>}

      <div className="text-muted small mb-2" data-testid="rows-summary">
        {loading ? "Loading records…" : `Showing ${from}\u2013${to} of ${total} applications`}
      </div>

      <div className="table-responsive" style={{ maxHeight: 560 }}>
        <table className="table table-sm table-hover table-apps align-middle">
          <thead>
            <tr>
              <th>App ID</th>
              <th>Student</th>
              <th className="d-none d-md-table-cell">Institution</th>
              <th className="d-none d-lg-table-cell">Course</th>
              <th className="text-num">Loan (\u20b9)</th>
              <th className="text-num d-none d-md-table-cell">Credit</th>
              <th>Status</th>
              <th className="d-none d-lg-table-cell">Attention</th>
              <th className="d-none d-lg-table-cell">Date</th>
              <th className="text-center" style={{ width: 130 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {apps.length === 0 && !loading ? (
              <tr>
                <td colSpan={10} className="text-center text-muted fst-italic py-4">
                  No applications match the current filters.
                </td>
              </tr>
            ) : (
              apps.map((a) => (
                <tr key={a.id}>
                  <td><strong>{a.id}</strong></td>
                  <td>
                    <div>{a.studentName}</div>
                    <div className="small text-muted d-md-none">{a.institutionName}</div>
                  </td>
                  <td className="d-none d-md-table-cell">{a.institutionName}</td>
                  <td className="d-none d-lg-table-cell">{a.courseName}</td>
                  <td className="text-num">{formatINR(a.loanAmountRequestedInr)}</td>
                  <td className="text-num d-none d-md-table-cell">
                    {a.creditScore !== null ? a.creditScore : <em style={{ color: "#9ca3af" }}>N/A</em>}
                  </td>
                  <td>
                    {editingId === a.id ? (
                      <div className="d-flex align-items-center gap-1">
                        <select
                          className="form-select form-select-sm py-0"
                          style={{ width: 110 }}
                          value={editStatus}
                          onChange={(e) => setEditStatus(e.target.value)}
                          disabled={statusSaving}
                        >
                          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                        </select>
                        <button type="button" className="btn btn-sm btn-success py-0 px-1" onClick={() => saveStatus(a)} disabled={statusSaving} title="Save">
                          <i className="bi bi-check" aria-hidden="true" />
                        </button>
                        <button type="button" className="btn btn-sm btn-secondary py-0 px-1" onClick={() => setEditingId(null)} disabled={statusSaving} title="Cancel">
                          <i className="bi bi-x" aria-hidden="true" />
                        </button>
                      </div>
                    ) : (
                      <span
                        className={`dq-pill ${statusClass(a.applicationStatus)}`}
                        style={{ cursor: canWrite ? "pointer" : "default" }}
                        onClick={() => {
                          if (!canWrite) return;
                          setEditingId(a.id);
                          setEditStatus(a.applicationStatus);
                        }}
                        title={canWrite ? "Click to update status" : "Read-only role"}
                      >
                        {a.applicationStatus}
                      </span>
                    )}
                  </td>
                  <td className="d-none d-lg-table-cell">
                    <span className={`dq-pill ${attentionClass(a.attentionLevel)}`}>{a.attentionLevel}</span>
                  </td>
                  <td className="d-none d-lg-table-cell">{a.applicationDate}</td>
                  <td className="text-center">
                    <div className="btn-group btn-group-sm" role="group" aria-label={`Actions for ${a.id}`}>
                      <button type="button" className="btn btn-outline-secondary" onClick={() => setViewItem(a)} title="View details">
                        <i className="bi bi-eye" aria-hidden="true" />
                      </button>
                      {canWrite && (
                        <>
                          <button type="button" className="btn btn-outline-primary" onClick={() => setFormModal({ show: true, mode: "edit", item: a })} title="Edit record">
                            <i className="bi bi-pencil" aria-hidden="true" />
                          </button>
                          <button type="button" className="btn btn-outline-danger" onClick={() => setDeleteTarget(a)} title="Delete record">
                            <i className="bi bi-trash" aria-hidden="true" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <nav aria-label="Applications pagination" className="mt-3">
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-2">
          <span className="text-muted small">
            Page {page} of {totalPages}
          </span>
          <ul className="pagination pagination-sm mb-0">
            <li className={`page-item ${page <= 1 ? "disabled" : ""}`}>
              <button className="page-link" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} aria-label="Previous page">
                <i className="bi bi-chevron-left" aria-hidden="true" />
              </button>
            </li>
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 2)
              .map((p, idx, arr) => (
                <React.Fragment key={p}>
                  {idx > 0 && arr[idx - 1] !== p - 1 && (
                    <li className="page-item disabled"><span className="page-link">…</span></li>
                  )}
                  <li className={`page-item ${p === page ? "active" : ""}`}>
                    <button className="page-link" onClick={() => setPage(p)} aria-current={p === page ? "page" : undefined}>
                      {p}
                    </button>
                  </li>
                </React.Fragment>
              ))}
            <li className={`page-item ${page >= totalPages ? "disabled" : ""}`}>
              <button className="page-link" onClick={() => setPage((p2) => Math.min(totalPages, p2 + 1))} disabled={page >= totalPages} aria-label="Next page">
                <i className="bi bi-chevron-right" aria-hidden="true" />
              </button>
            </li>
          </ul>
        </div>
      </nav>

      {/* Modals */}
      <ItemViewModal
        show={Boolean(viewItem)}
        item={viewItem}
        onClose={() => setViewItem(null)}
        onEdit={() => {
          const item = viewItem;
          setViewItem(null);
          setFormModal({ show: true, mode: "edit", item });
        }}
        canWrite={canWrite}
      />

      <ItemFormModal
        show={formModal.show}
        mode={formModal.mode}
        item={formModal.item}
        filters={filters}
        onClose={() => setFormModal({ show: false, mode: "create", item: null })}
        onSaved={async () => {
          setFormModal({ show: false, mode: "create", item: null });
          await loadRows();
        }}
      />

      <ConfirmModal
        show={Boolean(deleteTarget)}
        title="Delete Application?"
        message={
          deleteTarget
            ? `Are you sure you want to permanently delete application ${deleteTarget.id} (${deleteTarget.studentName})? This cannot be undone.`
            : ""
        }
        confirmLabel="Delete"
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
