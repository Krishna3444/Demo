import React from "react";

export default function Insights({ insights }) {
  if (!insights) return null;
  return (
    <div className="row g-3">
      {insights.map((i) => (
        <div className="col-12 col-md-6 col-xl-4" key={i.id}>
          <div className="card insight-card">
            <div className="card-body p-3">
              <div className="d-flex justify-content-between align-items-start gap-2 mb-2">
                <h5 className="card-title mb-0" style={{ fontSize: "0.92rem", fontWeight: 600 }}>
                  {i.title}
                </h5>
                {i.metric && (
                  <span className="metric-pill">{i.metric}</span>
                )}
              </div>
              <p className="finding mb-3">{i.finding}</p>
              <div className="calc-box mb-2">
                <strong>How calculated:</strong> {i.calculation}
              </div>
              <div className="why-box">{i.whyItMatters}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
