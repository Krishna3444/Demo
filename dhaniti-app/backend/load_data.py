"""
load_data.py
============

Loads the four supplied CSVs into a SQLite database with data-quality
cleaning applied. The database is the single source of truth for all
downstream analytics and for the dashboard.

Data-quality cleaning applied here:
  1. WHITESPACE_COURSE_NAME   — trim trailing whitespace on course_name
                                (e.g. EDU1065 has "MBA " instead of "MBA")
  2. WHITESPACE_CHANNEL       — trim trailing whitespace on application_channel
                                (e.g. EDU1121 has "Website " instead of "Website")
  3. INSTITUTION_NAME_NORMALISED — replace institution_name with the canonical
                                name from institutions.csv (matched by institution_id).
                                Fixes EDU1032 ("Central Inst. of Data Science"
                                → "Central Institute of Data Science").
  4. STATE_TYPO_FIXED         — map state typos to canonical Indian states
                                via a known-state lookup (fixes EDU1134 "Telengana"
                                → "Telangana").
  5. MISSING_CREDIT_SCORE     — keep blank credit_score as NULL (EDU1092),
                                and exclude NULLs from averages.

Risk flags (also persisted for analytics):
  - LOAN_EXCEEDS_FEE            : loan_amount_requested_inr > course_fee_inr
  - OBLIGATIONS_EXCEED_INCOME   : existing_monthly_obligations_inr > parent_monthly_income_inr

Attention Level (illustrative, rule-based — NOT a real underwriting policy):
  - High Attention    : credit_score missing OR credit_score < 650
                         OR monthly obligations > 50% of parent income
  - Review Required   : credit_score 650–724 OR obligations 30–50% of income
  - Low Attention     : credit_score ≥ 725 AND obligations < 30% of income

Run:
    python load_data.py
"""

from __future__ import annotations

import csv
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths — works both inside the original project layout and when shipped as
# a standalone bundle (with `data/` next to this file).
# --------------------------------------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR).startswith("/home/z/my-project/scripts/dhaniti/"):
    # Original project location
    UPLOAD_DIR = Path("/home/z/my-project/upload")
    DOWNLOAD_DIR = Path("/home/z/my-project/download/dhaniti")
else:
    # Standalone bundle — data/ folder is next to this script
    UPLOAD_DIR = BASE_DIR / "data"
    DOWNLOAD_DIR = BASE_DIR
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DOWNLOAD_DIR / "dhaniti_loans.db"
APPS_CSV = UPLOAD_DIR / "education_loan_applications.csv"
INST_CSV = UPLOAD_DIR / "institutions.csv"
COURSE_CSV = UPLOAD_DIR / "courses.csv"

# --------------------------------------------------------------------------- #
# Canonical lookups
# --------------------------------------------------------------------------- #
KNOWN_STATES = {
    "Tamil Nadu", "Telangana", "Karnataka", "Andhra Pradesh",
    "Maharashtra", "Kerala", "Rajasthan", "Delhi",
}
STATE_TYPO_MAP = {
    "Telengana": "Telangana",
    "Telegana": "Telangana",
    "Tamilnadu": "Tamil Nadu",
    "Karnatak": "Karnataka",
    "Keral": "Kerala",
}


def compute_attention_level(
    credit_score: int | None,
    parent_monthly_income: int,
    existing_obligations: int,
) -> str:
    """Illustrative rule-based attention level (NOT real underwriting policy)."""
    if credit_score is None:
        return "High Attention"
    dti = (
        existing_obligations / parent_monthly_income
        if parent_monthly_income > 0
        else 1.0
    )
    if credit_score < 650 or dti > 0.5:
        return "High Attention"
    if credit_score < 725 or dti > 0.3:
        return "Review Required"
    return "Low Attention"


# --------------------------------------------------------------------------- #
# CSV helpers
# --------------------------------------------------------------------------- #
def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Return (headers, rows). Rows preserve raw cell values (no trimming) so
    whitespace issues can be detected downstream."""
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows_raw = list(reader)
    if not rows_raw:
        return [], []
    headers = rows_raw[0]
    rows = [dict(zip(headers, r)) for r in rows_raw[1:] if r]
    return headers, rows


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #
SCHEMA_SQL = """
DROP TABLE IF EXISTS loan_applications;
DROP TABLE IF EXISTS institutions;
DROP TABLE IF EXISTS courses;

CREATE TABLE institutions (
    institution_id     TEXT PRIMARY KEY,
    institution_name   TEXT NOT NULL,
    city               TEXT NOT NULL,
    state              TEXT NOT NULL,
    institution_type   TEXT NOT NULL
);

CREATE TABLE courses (
    course_id          TEXT PRIMARY KEY,
    course_name        TEXT NOT NULL,
    domain             TEXT NOT NULL,
    typical_fee_inr    INTEGER NOT NULL,
    duration_months    INTEGER NOT NULL
);

CREATE TABLE loan_applications (
    application_id                     TEXT PRIMARY KEY,
    student_name                       TEXT NOT NULL,
    age                                 INTEGER NOT NULL,
    student_state                      TEXT NOT NULL,
    institution_id                     TEXT NOT NULL,
    institution_name                   TEXT NOT NULL,           -- denormalised snapshot
    course_id                          TEXT NOT NULL,
    course_name                        TEXT NOT NULL,           -- denormalised snapshot
    course_domain                      TEXT NOT NULL,
    course_fee_inr                     INTEGER NOT NULL,
    loan_amount_requested_inr           INTEGER NOT NULL,
    parent_monthly_income_inr          INTEGER NOT NULL,
    existing_monthly_obligations_inr   INTEGER NOT NULL,
    credit_score                       INTEGER,                 -- nullable (EDU1092 is missing)
    employment_type                    TEXT NOT NULL,
    application_date                   TEXT NOT NULL,           -- ISO YYYY-MM-DD
    application_status                 TEXT NOT NULL,
    application_channel                TEXT NOT NULL,
    data_quality_flags                 TEXT NOT NULL,           -- JSON array of issue codes
    attention_level                    TEXT NOT NULL,           -- Low/Review/High
    debt_to_income_ratio               REAL,                    -- derived
    loan_to_fee_ratio                  REAL,                    -- derived
    FOREIGN KEY (institution_id) REFERENCES institutions(institution_id),
    FOREIGN KEY (course_id)      REFERENCES courses(course_id)
);

CREATE INDEX idx_apps_status       ON loan_applications(application_status);
CREATE INDEX idx_apps_course      ON loan_applications(course_id);
CREATE INDEX idx_apps_institution ON loan_applications(institution_id);
CREATE INDEX idx_apps_attention   ON loan_applications(attention_level);
"""


def main() -> None:
    # 1. Load CSVs
    _, inst_rows = read_csv(INST_CSV)
    _, course_rows = read_csv(COURSE_CSV)
    _, app_rows = read_csv(APPS_CSV)

    print(f"[load] {len(inst_rows)} institutions, {len(course_rows)} courses, {len(app_rows)} applications")

    # 2. Canonical institution-name lookup (so we can fix EDU1032)
    canonical_inst_name = {r["institution_id"]: r["institution_name"] for r in inst_rows}

    # 3. (Re)create database
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)

    # 4. Insert institutions
    conn.executemany(
        """INSERT INTO institutions
           (institution_id, institution_name, city, state, institution_type)
           VALUES (?, ?, ?, ?, ?)""",
        [
            (r["institution_id"], r["institution_name"].strip(), r["city"].strip(),
             r["state"].strip(), r["institution_type"].strip())
            for r in inst_rows
        ],
    )

    # 5. Insert courses
    conn.executemany(
        """INSERT INTO courses
           (course_id, course_name, domain, typical_fee_inr, duration_months)
           VALUES (?, ?, ?, ?, ?)""",
        [
            (r["course_id"], r["course_name"].strip(), r["domain"].strip(),
             int(r["typical_fee_inr"]), int(r["duration_months"]))
            for r in course_rows
        ],
    )

    # 6. Insert applications — with cleaning + flags
    flagged_count = 0
    app_params: list[tuple] = []

    for r in app_rows:
        flags: list[str] = []

        # 6a. Whitespace on course_name
        raw_course_name = r["course_name"]
        clean_course_name = raw_course_name.strip()
        if raw_course_name != clean_course_name:
            flags.append("WHITESPACE_COURSE_NAME")

        # 6b. Whitespace on application_channel
        raw_channel = r["application_channel"]
        clean_channel = raw_channel.strip()
        if raw_channel != clean_channel:
            flags.append("WHITESPACE_CHANNEL")

        # 6c. Normalise institution_name using institution_id
        institution_id = r["institution_id"]
        raw_inst_name = r["institution_name"]
        canonical_name = canonical_inst_name.get(institution_id, raw_inst_name)
        if raw_inst_name != canonical_name:
            flags.append("INSTITUTION_NAME_NORMALISED")

        # 6d. State typo fix
        raw_state = r["student_state"]
        clean_state = raw_state
        if raw_state not in KNOWN_STATES:
            if raw_state in STATE_TYPO_MAP:
                clean_state = STATE_TYPO_MAP[raw_state]
                flags.append("STATE_TYPO_FIXED")
            else:
                flags.append("UNKNOWN_STATE")

        # 6e. Missing / invalid credit_score
        raw_cs = (r["credit_score"] or "").strip()
        credit_score: int | None
        if raw_cs == "":
            credit_score = None
            flags.append("MISSING_CREDIT_SCORE")
        else:
            try:
                # CSV stores scores like "639.0" — parse as float then int
                credit_score = int(float(raw_cs))
            except ValueError:
                credit_score = None
                flags.append("INVALID_CREDIT_SCORE")

        # 6f. Numeric sanity checks
        loan_amount = int(r["loan_amount_requested_inr"])
        course_fee = int(r["course_fee_inr"])
        parent_income = int(r["parent_monthly_income_inr"])
        obligations = int(r["existing_monthly_obligations_inr"])
        if loan_amount > course_fee:
            flags.append("LOAN_EXCEEDS_FEE")
        if obligations > parent_income:
            flags.append("OBLIGATIONS_EXCEED_INCOME")

        # 6g. Attention level
        attention = compute_attention_level(credit_score, parent_income, obligations)

        # 6h. Derived ratios
        dti = obligations / parent_income if parent_income > 0 else None
        ltf = loan_amount / course_fee if course_fee > 0 else None

        if flags:
            flagged_count += 1

        app_params.append((
            r["application_id"],
            r["student_name"].strip(),
            int(r["age"]),
            clean_state,
            institution_id,
            canonical_name,
            r["course_id"],
            clean_course_name,
            r["course_domain"].strip(),
            course_fee,
            loan_amount,
            parent_income,
            obligations,
            credit_score,
            r["employment_type"].strip(),
            r["application_date"],
            r["application_status"].strip(),
            clean_channel,
            json.dumps(flags),
            attention,
            dti,
            ltf,
        ))

    conn.executemany(
        """INSERT INTO loan_applications
           (application_id, student_name, age, student_state, institution_id,
            institution_name, course_id, course_name, course_domain, course_fee_inr,
            loan_amount_requested_inr, parent_monthly_income_inr,
            existing_monthly_obligations_inr, credit_score, employment_type,
            application_date, application_status, application_channel,
            data_quality_flags, attention_level,
            debt_to_income_ratio, loan_to_fee_ratio)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        app_params,
    )

    conn.commit()

    # 7. Sanity report
    total = conn.execute("SELECT COUNT(*) FROM loan_applications").fetchone()[0]
    flagged = conn.execute(
        "SELECT COUNT(*) FROM loan_applications WHERE data_quality_flags != '[]'"
    ).fetchone()[0]
    by_status = conn.execute(
        "SELECT application_status, COUNT(*) FROM loan_applications GROUP BY application_status"
    ).fetchall()
    by_attention = conn.execute(
        "SELECT attention_level, COUNT(*) FROM loan_applications GROUP BY attention_level"
    ).fetchall()

    print(f"[load] Inserted {total} applications ({flagged} had data-quality flags).")
    print("[load] Status distribution:")
    for s, c in by_status:
        print(f"        {s:14s}  {c}")
    print("[load] Attention distribution:")
    for a, c in by_attention:
        print(f"        {a:18s}  {c}")
    print(f"[load] Database saved to: {DB_PATH}")

    conn.close()


if __name__ == "__main__":
    main()
