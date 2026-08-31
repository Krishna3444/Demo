import React from "react";
import { formatINRCompact } from "../api.js";

export default function KpiCards({ kpis }) {
  if (!kpis) return null;
  const total = kpis.totalApplications || 0;
  const cards = [
    { label: "Total Applications", value: total.toLocaleString("en-IN"), sub: "All records in dataset", cls: "accent-total" },
    { label: "Approved", value: kpis.approved, sub: `${kpis.approvalRate}% approval rate`, cls: "accent-approved" },
    { label: "Under Review", value: kpis.underReview, sub: "Active in pipeline", cls: "accent-review" },
    { label: "Rejected", value: kpis.rejected, sub: "Declined by rule", cls: "accent-rejected" },
    { label: "Submitted", value: kpis.submitted, sub: "Awaiting first review", cls: "accent-total" },
    { label: "Total Loan Requested", value: formatINRCompact(kpis.totalLoanAmountRequested), sub: "Sum of loan_amount_requested_inr", cls: "accent-amount" },
    { label: "Avg Loan Amount", value: formatINRCompact(kpis.averageLoanAmount), sub: "Per application", cls: "accent-amount" },
    { label: "Avg Credit Score", value: kpis.averageCreditScore !== null ? kpis.averageCreditScore : "\u2014", sub: "Excludes missing", cls: "accent-total" },
  ];

  return (
    <div className="row g-3">
      {cards.map((c, i) => (
        <div className="col-6 col-md-4 col-lg-3 col-xl-2" key={i}>
          <div className={`card kpi-card ${c.cls}`}>
            <div className="card-body p-3">
              <div className="kpi-label">{c.label}</div>
              <div className="kpi-value">{c.value}</div>
              <div className="kpi-sub">{c.sub}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
