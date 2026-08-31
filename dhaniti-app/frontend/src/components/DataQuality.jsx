import React from "react";
import { attentionClass } from "../api.js";

export default function DataQuality({ dq }) {
  if (!dq) return null;
  return (
    <div>
      <div className="d-flex gap-2 flex-wrap mb-3">
        <span className="dq-pill dq-flag">{dq.affectedApplications} applications affected</span>
        <span className="dq-pill dq-flag">{dq.totalIssues} total flags</span>
        <span className="small text-muted align-self-center">
          All issues were detected and either cleaned or flagged during load (see <code>load_data.py</code>).
        </span>
      </div>
      <div className="table-responsive" style={{ maxHeight: 480 }}>
        <table className="table table-sm table-bordered table-apps mb-0">
          <thead>
            <tr>
              <th>Application ID</th>
              <th>Student</th>
              <th>Flag</th>
              <th>Description</th>
              <th>Raw value</th>
              <th>Cleaned / stored</th>
              <th>Attention</th>
            </tr>
          </thead>
          <tbody>
            {dq.issues.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center text-muted fst-italic py-4">
                  No data-quality issues detected.
                </td>
              </tr>
            ) : (
              dq.issues.map((i, idx) => (
                <tr key={idx}>
                  <td><strong>{i.applicationId}</strong></td>
                  <td>{i.studentName}</td>
                  <td><code>{i.flag}</code></td>
                  <td>{i.description}</td>
                  <td><code>{i.rawValue || "\u2014"}</code></td>
                  <td><code>{i.cleanedValue || "\u2014"}</code></td>
                  <td><span className={`dq-pill ${attentionClass(i.attentionLevel)}`}>{i.attentionLevel}</span></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="mt-3 p-3 bg-light rounded border">
        <strong>Flag legend</strong>
        <div className="row mt-2">
          {dq.flagLegend.map((f, i) => (
            <div className="col-12 col-md-6 mb-2" key={i}>
              <code className="me-2">{f.code}</code>
              <span className="small text-muted">{f.description}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
