import React, { useEffect, useState } from "react";
import { itemsApi } from "../api/items.js";
import { useAuth } from "../context/AuthContext.jsx";
import ApplicationsTable from "../components/ApplicationsTable.jsx";

/** Dedicated CRUD page for loan applications. */
export default function Applications() {
  const { canWrite } = useAuth();
  const [filters, setFilters] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    itemsApi
      .filters()
      .then(setFilters)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="container-fluid px-3 px-md-4 py-3">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <div>
          <h4 className="mb-0">
            Loan Applications
            {!canWrite && <span className="badge text-bg-secondary ms-2">Read-only role</span>}
          </h4>
          <p className="text-muted small mb-0">
            Create, view, update and delete education-loan applications.
          </p>
        </div>
      </div>

      {error && <div className="alert alert-danger py-2">{error}</div>}

      <div className="card section-card">
        <div className="card-body">
          {filters ? (
            <ApplicationsTable filters={filters} />
          ) : (
            !error && (
              <div className="text-center text-muted py-5">
                <div className="spinner-border" role="status"></div>
                <p className="mt-2 mb-0">Loading filters…</p>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
