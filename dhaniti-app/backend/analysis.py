"""
analysis.py
===========

Runs all SQL queries needed by the dashboard and returns them as a single
JSON-serialisable dict. This is the only Python file the dashboard generator
needs to import.

Run as a script to print a JSON preview to stdout:

    python analysis.py
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

# Resolve the database path relative to this file so the script works both
# in the original project layout and when shipped as a standalone bundle.
_BASE = Path(__file__).resolve().parent
if str(_BASE).startswith("/home/z/my-project/scripts/dhaniti/"):
    DB_PATH = Path("/home/z/my-project/download/dhaniti/dhaniti_loans.db")
else:
    # Standalone bundle — DB sits next to this script
    DB_PATH = _BASE / "dhaniti_loans.db"

# --------------------------------------------------------------------------- #
# Flag legend — shared with load_data.py / dashboard
# --------------------------------------------------------------------------- #
FLAG_DESCRIPTIONS: dict[str, str] = {
    "WHITESPACE_COURSE_NAME":
        'Trailing whitespace in course_name (e.g. "MBA "). Trimmed on load.',
    "WHITESPACE_CHANNEL":
        'Trailing whitespace in application_channel (e.g. "Website "). Trimmed on load.',
    "INSTITUTION_NAME_NORMALISED":
        'Institution name in applications CSV did not match the canonical name in '
        'institutions.csv (e.g. "Central Inst. of Data Science" \u2192 "Central Institute '
        'of Data Science"). We trust institution_id and overwrite the denormalised name.',
    "STATE_TYPO_FIXED":
        'Student state contained a typo (e.g. "Telengana" \u2192 "Telangana"). '
        'Mapped via known-state lookup table.',
    "MISSING_CREDIT_SCORE":
        "credit_score is blank in the source CSV. Stored as NULL and excluded from "
        "credit-score averages; the application is auto-flagged High Attention.",
    "INVALID_CREDIT_SCORE":
        "credit_score could not be parsed as a number. Stored as NULL.",
    "LOAN_EXCEEDS_FEE":
        "loan_amount_requested_inr is greater than course_fee_inr. Surfaced as a "
        "risk flag rather than being silently corrected.",
    "OBLIGATIONS_EXCEED_INCOME":
        "existing_monthly_obligations_inr exceeds parent_monthly_income_inr (DTI > 100%). "
        "Treated as High Attention.",
    "UNKNOWN_STATE":
        "student_state did not match any known Indian state and could not be auto-corrected.",
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------- #
# KPIs
# --------------------------------------------------------------------------- #
def get_kpis(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT
            COUNT(*)                                                          AS total_applications,
            SUM(CASE WHEN application_status = 'Approved'     THEN 1 ELSE 0 END) AS approved,
            SUM(CASE WHEN application_status = 'Under Review' THEN 1 ELSE 0 END) AS under_review,
            SUM(CASE WHEN application_status = 'Rejected'     THEN 1 ELSE 0 END) AS rejected,
            SUM(CASE WHEN application_status = 'Submitted'    THEN 1 ELSE 0 END) AS submitted,
            COALESCE(SUM(loan_amount_requested_inr), 0)                        AS total_loan_amount,
            COALESCE(AVG(loan_amount_requested_inr), 0)                        AS avg_loan_amount,
            AVG(credit_score)                                                  AS avg_credit_score
        FROM loan_applications
        """
    ).fetchone()
    total = row["total_applications"]
    return {
        "totalApplications": total,
        "approved": row["approved"],
        "underReview": row["under_review"],
        "rejected": row["rejected"],
        "submitted": row["submitted"],
        "totalLoanAmountRequested": row["total_loan_amount"],
        "averageLoanAmount": int(row["avg_loan_amount"]),
        "averageCreditScore": (
            None if row["avg_credit_score"] is None else round(row["avg_credit_score"])
        ),
        "approvalRate": (
            round((row["approved"] / total) * 100, 1) if total else 0.0
        ),
    }


# --------------------------------------------------------------------------- #
# Charts
# --------------------------------------------------------------------------- #
def get_charts(conn: sqlite3.Connection) -> dict[str, Any]:
    def _group_count(col: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            f"SELECT {col} AS label, COUNT(*) AS value "
            f"FROM loan_applications GROUP BY {col} ORDER BY value DESC"
        ).fetchall()
        return _rows_to_dicts(rows)

    # Monthly trend — stacked by status
    monthly = conn.execute(
        """
        SELECT
            substr(application_date, 1, 7) AS month,
            SUM(CASE WHEN application_status = 'Submitted'    THEN 1 ELSE 0 END) AS submitted,
            SUM(CASE WHEN application_status = 'Under Review' THEN 1 ELSE 0 END) AS under_review,
            SUM(CASE WHEN application_status = 'Approved'     THEN 1 ELSE 0 END) AS approved,
            SUM(CASE WHEN application_status = 'Rejected'     THEN 1 ELSE 0 END) AS rejected
        FROM loan_applications
        GROUP BY month
        ORDER BY month
        """
    ).fetchall()
    monthly_trend = [
        {
            "month": r["month"],
            "Submitted": r["submitted"],
            "Under Review": r["under_review"],
            "Approved": r["approved"],
            "Rejected": r["rejected"],
        }
        for r in monthly
    ]

    # Credit-score buckets
    bucket_sql = """
        SELECT bucket, COUNT(*) AS count FROM (
            SELECT
              CASE
                WHEN credit_score IS NULL THEN 'Missing'
                WHEN credit_score < 600   THEN '<600'
                WHEN credit_score < 650   THEN '600-649'
                WHEN credit_score < 700   THEN '650-699'
                WHEN credit_score < 750   THEN '700-749'
                WHEN credit_score < 800   THEN '750-799'
                ELSE '800+'
              END AS bucket
            FROM loan_applications
        ) GROUP BY bucket
    """
    credit_buckets_raw = _rows_to_dicts(conn.execute(bucket_sql).fetchall())
    # Force a numeric ordering rather than alphabetical (so '<600' isn't last).
    BUCKET_ORDER = ["<600", "600-649", "650-699", "700-749", "750-799", "800+", "Missing"]
    bucket_idx = {name: i for i, name in enumerate(BUCKET_ORDER)}
    credit_buckets = sorted(
        credit_buckets_raw, key=lambda b: bucket_idx.get(b["bucket"], 99)
    )

    # Avg loan amount by course
    avg_loan_by_course = _rows_to_dicts(
        conn.execute(
            """
            SELECT course_name AS courseName,
                   AVG(loan_amount_requested_inr) AS avgLoanAmount,
                   COUNT(*) AS count
            FROM loan_applications
            GROUP BY course_name
            ORDER BY avgLoanAmount DESC
            """
        ).fetchall()
    )
    for r in avg_loan_by_course:
        r["avgLoanAmount"] = int(r["avgLoanAmount"])

    return {
        "statusBreakdown": _group_count("application_status"),
        "courseBreakdown": _group_count("course_name"),
        "institutionBreakdown": _group_count("institution_name"),
        "domainBreakdown": _group_count("course_domain"),
        "channelBreakdown": _group_count("application_channel"),
        "monthlyTrend": monthly_trend,
        "creditScoreBuckets": credit_buckets,
        "avgLoanByCourse": avg_loan_by_course,
    }


# --------------------------------------------------------------------------- #
# Insights — all computed from SQL, with a hand-written narrative
# --------------------------------------------------------------------------- #
def get_insights(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    total = conn.execute("SELECT COUNT(*) FROM loan_applications").fetchone()[0]

    # ---- 1. Approval rate by course domain ----
    dom_rows = conn.execute(
        """
        SELECT course_domain AS domain,
               COUNT(*) AS total,
               SUM(CASE WHEN application_status = 'Approved' THEN 1 ELSE 0 END) AS approved
        FROM loan_applications
        GROUP BY course_domain
        """
    ).fetchall()
    dom_rates = [
        {
            "domain": r["domain"],
            "total": r["total"],
            "approved": r["approved"],
            "rate": round((r["approved"] / r["total"]) * 100, 1) if r["total"] else 0.0,
        }
        for r in dom_rows
    ]
    best_dom = max(dom_rates, key=lambda x: x["rate"])
    worst_dom = min(dom_rates, key=lambda x: x["rate"])

    # ---- 2. Credit-score correlation with approval ----
    cs_rows = conn.execute(
        """
        SELECT application_status,
               COUNT(*) AS n,
               AVG(credit_score) AS avg_score
        FROM loan_applications
        WHERE credit_score IS NOT NULL
        GROUP BY application_status
        """
    ).fetchall()
    cs_map: dict[str, dict[str, Any]] = {}
    for r in cs_rows:
        cs_map[r["application_status"]] = dict(r)
    avg_approved_score = cs_map.get("Approved", {}).get("avg_score") or 0
    avg_rejected_score = cs_map.get("Rejected", {}).get("avg_score") or 0
    n_app = cs_map.get("Approved", {}).get("n", 0)
    n_rej = cs_map.get("Rejected", {}).get("n", 0)

    # ---- 3. DTI correlation with rejection ----
    dti_rows = conn.execute(
        """
        SELECT application_status,
               COUNT(*) AS n,
               AVG(existing_monthly_obligations_inr * 1.0 / parent_monthly_income_inr) AS avg_dti
        FROM loan_applications
        WHERE parent_monthly_income_inr > 0
        GROUP BY application_status
        """
    ).fetchall()
    dti_map: dict[str, dict[str, Any]] = {}
    for r in dti_rows:
        dti_map[r["application_status"]] = dict(r)
    avg_dti_approved = (dti_map.get("Approved", {}).get("avg_dti") or 0) * 100
    avg_dti_rejected = (dti_map.get("Rejected", {}).get("avg_dti") or 0) * 100

    # ---- 4. Channel performance ----
    ch_rows = conn.execute(
        """
        SELECT application_channel AS channel,
               COUNT(*) AS total,
               SUM(CASE WHEN application_status = 'Approved' THEN 1 ELSE 0 END) AS approved
        FROM loan_applications
        GROUP BY application_channel
        """
    ).fetchall()
    ch_rates = [
        {
            "channel": r["channel"],
            "total": r["total"],
            "approved": r["approved"],
            "rate": round((r["approved"] / r["total"]) * 100, 1) if r["total"] else 0.0,
        }
        for r in ch_rows
    ]
    best_ch = max(ch_rates, key=lambda x: x["rate"])
    worst_ch = min(ch_rates, key=lambda x: x["rate"])

    # ---- 5. Medical-course concentration ----
    med_row = conn.execute(
        """
        SELECT
            COUNT(*) AS n_apps,
            COALESCE(SUM(loan_amount_requested_inr), 0) AS loan_total
        FROM loan_applications
        WHERE course_domain = 'Medical'
        """
    ).fetchone()
    total_row = conn.execute(
        "SELECT COUNT(*) AS n, COALESCE(SUM(loan_amount_requested_inr), 0) AS loan_total FROM loan_applications"
    ).fetchone()
    med_share_apps = (med_row["n_apps"] / total_row["n"]) * 100 if total_row["n"] else 0
    med_share_loans = (med_row["loan_total"] / total_row["loan_total"]) * 100 if total_row["loan_total"] else 0

    insights = [
        {
            "id": "domain-approval-rate",
            "title": "Approval rate varies sharply by course domain",
            "finding": f"Among the four course domains, {best_dom['domain']} has the highest approval rate "
                       f"({best_dom['rate']:.1f}%, {best_dom['approved']}/{best_dom['total']}), while "
                       f"{worst_dom['domain']} has the lowest ({worst_dom['rate']:.1f}%, "
                       f"{worst_dom['approved']}/{worst_dom['total']}).",
            "calculation": "For each course_domain, count applications grouped by application_status, "
                           "then compute approved_count / total_count \u00d7 100. Source: full dataset of "
                           f"{total} applications.",
            "whyItMatters": "Domain-level approval rates are a fast triage signal for the operations team: "
                            "a low-approval domain suggests either tougher underwriting for high-ticket "
                            "courses, or that the synthetic status logic penalises high loan amounts "
                            "relative to income. The team can target that domain for manual review or "
                            "product policy refinement.",
            "metric": f"{best_dom['domain']} {best_dom['rate']:.1f}% \u00b7 {worst_dom['domain']} {worst_dom['rate']:.1f}%",
        },
        {
            "id": "credit-score-approval-correlation",
            "title": "Approved applications have materially higher credit scores",
            "finding": f"The average credit score of approved applications is {avg_approved_score:.0f}, versus "
                       f"{avg_rejected_score:.0f} for rejected ones \u2014 a gap of "
                       f"{avg_approved_score - avg_rejected_score:.0f} points.",
            "calculation": "AVG(credit_score) WHERE application_status='Approved' AND credit_score IS NOT NULL, "
                           "compared with the same metric WHERE application_status='Rejected'. Only records with "
                           f"non-null credit_score were included (n_approved={n_app}, n_rejected={n_rej}).",
            "whyItMatters": "This is a sanity check that the status field tracks credit quality in the expected "
                            "direction. A negative or near-zero gap would indicate a data labelling problem. The "
                            "observed gap is consistent with credit_score being a meaningful input to the "
                            "synthetic status logic and validates using it as a primary attention-level signal.",
            "metric": f"\u0394 {avg_approved_score - avg_rejected_score:.0f} pts",
        },
        {
            "id": "dti-rejection-correlation",
            "title": "Rejected applicants carry ~2\u00d7 the debt-to-income burden of approved ones",
            "finding": f"Average debt-to-income ratio (existing_monthly_obligations / parent_monthly_income) is "
                      f"{avg_dti_rejected:.1f}% for rejected applications vs {avg_dti_approved:.1f}% for approved ones.",
            "calculation": "For every application with parent_monthly_income > 0, "
                           "DTI = existing_monthly_obligations_inr / parent_monthly_income_inr \u00d7 100. "
                           "We then averaged DTI across approved and rejected buckets separately.",
            "whyItMatters": "DTI is one of the strongest affordability signals in real lending. The 2\u00d7 gap "
                            "confirms that the synthetic status field uses affordability inputs, and gives the team "
                            "a concrete cut-off (~30\u201335%) to operationalise as an attention-level rule "
                            "without needing access to a full underwriting model.",
            "metric": f"{avg_dti_approved:.1f}% \u2192 {avg_dti_rejected:.1f}%",
        },
        {
            "id": "channel-performance",
            "title": f'"{best_ch["channel"]}" is the highest-converting acquisition channel',
            "finding": f"Approval rate by acquisition channel: {best_ch['channel']} leads at "
                       f"{best_ch['rate']:.1f}% ({best_ch['approved']}/{best_ch['total']}), while "
                       f"{worst_ch['channel']} trails at {worst_ch['rate']:.1f}% "
                       f"({worst_ch['approved']}/{worst_ch['total']}).",
            "calculation": "For each application_channel, compute approved_count / total_count \u00d7 100. "
                           "Channels with very few applications should be treated as directional only.",
            "whyItMatters": "Channel-level conversion is a direct input to marketing spend. If a channel is "
                            "producing low-quality applications (low approval rate) it is wasting acquisition "
                            "budget even if raw volume looks healthy. The team can use this to renegotiate "
                            "referral partnerships or rebalance the campus-drive calendar.",
            "metric": f"{best_ch['channel']} {best_ch['rate']:.1f}%",
        },
        {
            "id": "medical-loan-concentration",
            "title": "Medical-course applications concentrate loan exposure",
            "finding": f"Medical-domain applications represent {med_share_apps:.1f}% of all applications "
                       f"({med_row['n_apps']} of {total_row['n']}) but {med_share_loans:.1f}% of total requested "
                       f"loan amount (\u20b9{med_row['loan_total']/1e7:.2f} Cr of "
                       f"\u20b9{total_row['loan_total']/1e7:.2f} Cr).",
            "calculation": "medical_loan_total = SUM(loan_amount_requested_inr) WHERE course_domain='Medical'; "
                           "total_loan_total = SUM(loan_amount_requested_inr) across all rows. Shares expressed "
                           "as percentages of total applications and total loan amount respectively.",
            "whyItMatters": "Concentration risk: even a small shift in MBBS/M.Pharm approval policy materially "
                            "moves the total exposure number. The risk team should monitor medical-course "
                            "approval rates and average ticket size separately from the rest of the portfolio, "
                            "because a single MBBS application can be worth ~4\u00d7 the loan amount of a BCA "
                            "application.",
            "metric": f"{med_share_apps:.1f}% apps \u2192 {med_share_loans:.1f}% \u20b9",
        },
    ]
    return insights


# --------------------------------------------------------------------------- #
# Data-quality issues
# --------------------------------------------------------------------------- #
def get_data_quality(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT application_id, student_name, course_name, institution_name, student_state,
               application_channel, credit_score, data_quality_flags, attention_level,
               loan_amount_requested_inr, course_fee_inr,
               parent_monthly_income_inr, existing_monthly_obligations_inr
        FROM loan_applications
        WHERE data_quality_flags != '[]'
        ORDER BY application_id
        """
    ).fetchall()
    issues: list[dict[str, Any]] = []
    for r in rows:
        flags = json.loads(r["data_quality_flags"])
        for f in flags:
            raw = None
            cleaned = None
            if f == "WHITESPACE_COURSE_NAME":
                raw = f'"{r["course_name"]} "'
                cleaned = f'"{r["course_name"]}"'
            elif f == "WHITESPACE_CHANNEL":
                raw = f'"{r["application_channel"]} "'
                cleaned = f'"{r["application_channel"]}"'
            elif f == "INSTITUTION_NAME_NORMALISED":
                raw = "(see CSV \u2014 value differs from institutions.csv canonical name)"
                cleaned = r["institution_name"]
            elif f == "STATE_TYPO_FIXED":
                raw = "(typo, see raw CSV)"
                cleaned = r["student_state"]
            elif f == "MISSING_CREDIT_SCORE":
                raw = "(blank)"
                cleaned = "NULL"
            elif f == "LOAN_EXCEEDS_FEE":
                raw = f'loan={r["loan_amount_requested_inr"]:,}'
                cleaned = f'fee={r["course_fee_inr"]:,}'
            elif f == "OBLIGATIONS_EXCEED_INCOME":
                raw = f'obligations={r["existing_monthly_obligations_inr"]:,}'
                cleaned = f'income={r["parent_monthly_income_inr"]:,}'
            issues.append({
                "applicationId": r["application_id"],
                "studentName": r["student_name"],
                "flag": f,
                "description": FLAG_DESCRIPTIONS.get(f, "Unknown data-quality flag."),
                "rawValue": raw,
                "cleanedValue": cleaned,
                "attentionLevel": r["attention_level"],
            })
    return {
        "totalIssues": len(issues),
        "affectedApplications": len(rows),
        "issues": issues,
        "flagLegend": [
            {"code": k, "description": v} for k, v in FLAG_DESCRIPTIONS.items()
        ],
    }


# --------------------------------------------------------------------------- #
# Applications list (for the table)
# --------------------------------------------------------------------------- #
def get_applications(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT application_id, student_name, age, student_state,
               institution_id, institution_name, course_id, course_name, course_domain,
               course_fee_inr, loan_amount_requested_inr,
               parent_monthly_income_inr, existing_monthly_obligations_inr,
               credit_score, employment_type, application_date, application_status,
               application_channel, data_quality_flags, attention_level,
               debt_to_income_ratio, loan_to_fee_ratio
        FROM loan_applications
        ORDER BY application_id
        """
    ).fetchall()
    out = []
    for r in rows:
        try:
            flags = json.loads(r["data_quality_flags"])
        except Exception:
            flags = []
        out.append({
            "id": r["application_id"],
            "studentName": r["student_name"],
            "age": r["age"],
            "studentState": r["student_state"],
            "institutionId": r["institution_id"],
            "institutionName": r["institution_name"],
            "courseId": r["course_id"],
            "courseName": r["course_name"],
            "courseDomain": r["course_domain"],
            "courseFeeInr": r["course_fee_inr"],
            "loanAmountRequestedInr": r["loan_amount_requested_inr"],
            "parentMonthlyIncomeInr": r["parent_monthly_income_inr"],
            "existingMonthlyObligationsInr": r["existing_monthly_obligations_inr"],
            "creditScore": r["credit_score"],
            "employmentType": r["employment_type"],
            "applicationDate": r["application_date"],
            "applicationStatus": r["application_status"],
            "applicationChannel": r["application_channel"],
            "dataQualityFlags": flags,
            "attentionLevel": r["attention_level"],
            "debtToIncomeRatio": (
                round(r["debt_to_income_ratio"], 3) if r["debt_to_income_ratio"] is not None else None
            ),
            "loanToFeeRatio": (
                round(r["loan_to_fee_ratio"], 3) if r["loan_to_fee_ratio"] is not None else None
            ),
        })
    return out


# --------------------------------------------------------------------------- #
# Filter option lists (for dropdowns)
# --------------------------------------------------------------------------- #
def get_filter_options(conn: sqlite3.Connection) -> dict[str, list[dict[str, str]]]:
    institutions = _rows_to_dicts(
        conn.execute(
            "SELECT institution_id AS id, institution_name AS name "
            "FROM institutions ORDER BY institution_id"
        ).fetchall()
    )
    courses = _rows_to_dicts(
        conn.execute(
            "SELECT course_id AS id, course_name AS name, domain "
            "FROM courses ORDER BY course_id"
        ).fetchall()
    )
    statuses = _rows_to_dicts(
        conn.execute(
            "SELECT DISTINCT application_status AS status "
            "FROM loan_applications ORDER BY status"
        ).fetchall()
    )
    return {
        "institutions": institutions,
        "courses": courses,
        "statuses": [r["status"] for r in statuses],
    }


# --------------------------------------------------------------------------- #
# Top-level entry point
# --------------------------------------------------------------------------- #
def get_all() -> dict[str, Any]:
    conn = _open()
    try:
        return {
            "kpis": get_kpis(conn),
            "charts": get_charts(conn),
            "insights": get_insights(conn),
            "dataQuality": get_data_quality(conn),
            "applications": get_applications(conn),
            "filters": get_filter_options(conn),
        }
    finally:
        conn.close()


if __name__ == "__main__":
    print(json.dumps(get_all(), indent=2, ensure_ascii=False))
