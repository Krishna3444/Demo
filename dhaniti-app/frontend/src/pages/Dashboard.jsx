import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { itemsApi } from "../api/items.js";
import { useAuth } from "../context/AuthContext.jsx";
import KpiCards from "../components/KpiCards.jsx";
import Charts from "../components/Charts.jsx";
import Insights from "../components/Insights.jsx";
import DataQuality from "../components/DataQuality.jsx";
import ApplicationsTable from "../components/ApplicationsTable.jsx";

export default function Dashboard() {
  const { currentUser, canWrite } = useAuth();
  const [tab, setTab] = useState("overview");
  const [kpis, setKpis] = useState(null);
  const [charts, setCharts] = useState(null);
  const [insights, setInsights] = useState(null);
  const [dq, setDq] = useState(null);
  const [filters, setFilters] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      itemsApi.kpis(),
      itemsApi.charts(),
      itemsApi.insights(),
      itemsApi.dataQuality(),
      itemsApi.filters(),
    ]).then(([k, c, i, d, f]) => {
      setKpis(k);
      setCharts(c);
      setInsights(i);
      setDq(d);
      setFilters(f);
    }).catch((e) => setError(e.message));
  }, []);

  const firstName = (currentUser?.name || "there").split(/[\s(]/)[0];

  return (
    <>
      <div className="container-fluid px-3 px-md-4 pt-3">
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
          <div>
            <h4 className="mb-0">Welcome, {firstName}</h4>
            <p className="text-muted small mb-0">
              Here is what is happening with the education-loan portfolio today.
            </p>
          </div>
          <Link to="/applications" className="btn btn-sm btn-outline-dhaniti">
            <i className="bi bi-table me-1" aria-hidden="true" />
            Manage applications
          </Link>
        </div>
      </div>

      {error && (
        <div className="container-fluid px-3 px-md-4">
          <div className="alert alert-danger mt-2">{error}</div>
        </div>
      )}

      <ul className="nav nav-tabs mb-3 px-3 px-md-4 pt-2">
        <li className="nav-item">
          <button className={`nav-link ${tab === "overview" ? "active" : ""}`} onClick={() => setTab("overview")}>
            Overview
          </button>
        </li>
        <li className="nav-item">
          <button className={`nav-link ${tab === "applications" ? "active" : ""}`} onClick={() => setTab("applications")}>
            Applications
            {kpis && <span className="badge bg-secondary ms-2">{kpis.totalApplications}</span>}
          </button>
        </li>
        <li className="nav-item">
          <button className={`nav-link ${tab === "insights" ? "active" : ""}`} onClick={() => setTab("insights")}>
            Insights
            {insights && <span className="badge bg-secondary ms-2">{insights.length}</span>}
          </button>
        </li>
        <li className="nav-item">
          <button className={`nav-link ${tab === "data-quality" ? "active" : ""}`} onClick={() => setTab("data-quality")}>
            Data Quality
            {dq && <span className="badge bg-warning text-dark ms-2">{dq.totalIssues}</span>}
          </button>
        </li>
      </ul>

      <div className="container-fluid px-3 px-md-4">
        {tab === "overview" && (
          <>
            <div className="card section-card">
              <div className="card-header">
                Key Metrics
                {kpis && <span className="badge bg-secondary ms-2">{kpis.totalApplications}</span>}
              </div>
              <div className="card-body">
                {kpis ? <KpiCards kpis={kpis} /> : (
                  <div className="text-center text-muted py-4">
                    <div className="spinner-border" role="status"></div>
                  </div>
                )}
              </div>
            </div>

            <div className="card section-card">
              <div className="card-header">Distribution Charts</div>
              <div className="card-body">
                {charts ? <Charts charts={charts} /> : (
                  <div className="text-center text-muted py-4">
                    <div className="spinner-border" role="status"></div>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {tab === "applications" && (
          <div className="card section-card">
            <div className="card-header d-flex flex-wrap justify-content-between align-items-center gap-2">
              <span>
                Applications
                {kpis && <span className="badge bg-secondary ms-2">{kpis.totalApplications}</span>}
              </span>
              {!canWrite && <span className="badge text-bg-secondary">Read-only role</span>}
            </div>
            <div className="card-body">
              <ApplicationsTable filters={filters} />
            </div>
          </div>
        )}

        {tab === "insights" && (
          <div className="card section-card">
            <div className="card-header">
              Business Insights
              {insights && <span className="badge bg-secondary ms-2">{insights.length}</span>}
            </div>
            <div className="card-body">
              {insights ? <Insights insights={insights} /> : (
                <div className="text-center text-muted py-4">
                  <div className="spinner-border" role="status"></div>
                </div>
              )}
            </div>
          </div>
        )}

        {tab === "data-quality" && (
          <div className="card section-card">
            <div className="card-header">
              Data-Quality Issues
              {dq && <span className="badge bg-warning text-dark ms-2">{dq.totalIssues}</span>}
            </div>
            <div className="card-body">
              {dq ? <DataQuality dq={dq} /> : (
                <div className="text-center text-muted py-4">
                  <div className="spinner-border" role="status"></div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
