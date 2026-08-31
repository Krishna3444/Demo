"""
LEGACY — original Flask prototype (superseded by the FastAPI app in app/).

This file is kept for reference only. The active API server is:

    uvicorn app.main:app --port 5000      (from the backend/ directory)

To run this legacy server anyway (from backend/):

    python legacy_flask/app.py
"""

import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))



from __future__ import annotations

import os
import datetime as dt
import json
from functools import wraps
from pathlib import Path

import jwt
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import analysis
import load_data  # noqa: F401  (importing ensures DB exists on first run)

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR.parent / "static"
DB_PATH = BASE_DIR.parent.parent / "dhaniti_loans.db"

# Demo credentials — DO NOT use in production.
# In a real app these would be hashed (bcrypt/argon2) and stored in a DB.
DEFAULT_USERS = {
    "admin": {
        "password": "dhaniti123",
        "name": "Dhaniti Admin",
        "role": "admin",
    },
    "analyst": {
        "password": "analyst456",
        "name": "Credit Analyst",
        "role": "analyst",
    },
}

JWT_SECRET = os.environ.get("DHANITI_JWT_SECRET", "dhaniti-dev-secret-change-me")
JWT_ALG = "HS256"
JWT_TTL_HOURS = 8

app = Flask(__name__, static_folder=None)
CORS(app)  # allow Vite dev server during development

# --------------------------------------------------------------------------- #
# Auth helpers
# --------------------------------------------------------------------------- #
def make_token(username: str) -> str:
    payload = {
        "sub": username,
        "iat": int(dt.datetime.utcnow().timestamp()),
        "exp": int((dt.datetime.utcnow() + dt.timedelta(hours=JWT_TTL_HOURS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth[7:]
        username = verify_token(token)
        if not username:
            return jsonify({"error": "Invalid or expired token"}), 401
        request.current_user = username
        return f(*args, **kwargs)
    return wrapper


# --------------------------------------------------------------------------- #
# Auth endpoints
# --------------------------------------------------------------------------- #
@app.post("/api/login")
def login():
    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    user = DEFAULT_USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "Invalid username or password"}), 401
    token = make_token(username)
    return jsonify({
        "token": token,
        "user": {"username": username, "name": user["name"], "role": user["role"]},
    })


@app.get("/api/whoami")
@auth_required
def whoami():
    user = DEFAULT_USERS.get(request.current_user)
    return jsonify({
        "username": request.current_user,
        "name": user["name"] if user else "Unknown",
        "role": user["role"] if user else "unknown",
    })


# --------------------------------------------------------------------------- #
# Data endpoints (all require auth)
# --------------------------------------------------------------------------- #
@app.get("/api/kpis")
@auth_required
def get_kpis():
    return jsonify(analysis.get_kpis(analysis._open()))


@app.get("/api/charts")
@auth_required
def get_charts():
    return jsonify(analysis.get_charts(analysis._open()))


@app.get("/api/insights")
@auth_required
def get_insights():
    return jsonify(analysis.get_insights(analysis._open()))


@app.get("/api/data-quality")
@auth_required
def get_data_quality():
    return jsonify(analysis.get_data_quality(analysis._open()))


@app.get("/api/filters")
@auth_required
def get_filters():
    return jsonify(analysis.get_filter_options(analysis._open()))


@app.get("/api/applications")
@auth_required
def get_applications():
    # Reuse the full list, then filter/sort in-process (SQLite would also work
    # but for 150 rows this is simpler and avoids query-injection concerns).
    rows = analysis.get_applications(analysis._open())
    q = (request.args.get("search") or "").strip().lower()
    status = request.args.get("status") or "all"
    course = request.args.get("courseId") or "all"
    inst = request.args.get("institutionId") or "all"
    att = request.args.get("attentionLevel") or "all"
    sort_by = request.args.get("sortBy") or "applicationDate"
    sort_dir = request.args.get("sortDir") or "desc"

    if q:
        rows = [r for r in rows if q in r["id"].lower() or q in r["studentName"].lower()]
    if status != "all":
        rows = [r for r in rows if r["applicationStatus"] == status]
    if course != "all":
        rows = [r for r in rows if r["courseId"] == course]
    if inst != "all":
        rows = [r for r in rows if r["institutionId"] == inst]
    if att != "all":
        rows = [r for r in rows if r["attentionLevel"] == att]

    reverse = (sort_dir == "desc")
    if sort_by == "creditScore":
        rows.sort(key=lambda r: (r["creditScore"] if r["creditScore"] is not None else -1), reverse=reverse)
    elif sort_by == "loanAmountRequestedInr":
        rows.sort(key=lambda r: r["loanAmountRequestedInr"], reverse=reverse)
    elif sort_by == "applicationDate":
        rows.sort(key=lambda r: r["applicationDate"], reverse=reverse)
    return jsonify({"count": len(rows), "data": rows})


@app.get("/api/applications/<app_id>")
@auth_required
def get_one_application(app_id: str):
    conn = analysis._open()
    row = conn.execute(
        "SELECT * FROM loan_applications WHERE application_id = ?", (app_id,)
    ).fetchone()
    if not row:
        return jsonify({"error": "Application not found"}), 404
    # Reuse the serializer by reading from get_applications and filtering
    all_apps = analysis.get_applications(conn)
    match = next((a for a in all_apps if a["id"] == app_id), None)
    return jsonify(match)


@app.patch("/api/applications/<app_id>")
@auth_required
def update_status(app_id: str):
    body = request.get_json(silent=True) or {}
    new_status = body.get("applicationStatus")
    allowed = ["Submitted", "Under Review", "Approved", "Rejected"]
    if new_status not in allowed:
        return jsonify({"error": f"applicationStatus must be one of: {allowed}"}), 422
    conn = analysis._open()
    cur = conn.execute(
        "UPDATE loan_applications SET application_status = ? WHERE application_id = ?",
        (new_status, app_id),
    )
    conn.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Application not found"}), 404
    return jsonify({"application_id": app_id, "applicationStatus": new_status})


@app.post("/api/applications")
@auth_required
def create_application():
    body = request.get_json(silent=True) or {}
    required = ["studentName", "age", "studentState", "institutionId", "courseId",
                "loanAmountRequestedInr", "parentMonthlyIncomeInr",
                "existingMonthlyObligationsInr", "employmentType", "applicationChannel"]
    errors = []
    for f in required:
        if body.get(f) in (None, ""):
            errors.append(f"{f} is required")
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 422

    # Resolve institution & course snapshots
    conn = analysis._open()
    inst = conn.execute(
        "SELECT * FROM institutions WHERE institution_id = ?", (body["institutionId"],)
    ).fetchone()
    if not inst:
        return jsonify({"error": "Unknown institutionId"}), 422
    course = conn.execute(
        "SELECT * FROM courses WHERE course_id = ?", (body["courseId"],)
    ).fetchone()
    if not course:
        return jsonify({"error": "Unknown courseId"}), 422

    # Generate next ID
    last = conn.execute(
        "SELECT application_id FROM loan_applications ORDER BY application_id DESC LIMIT 1"
    ).fetchone()
    next_num = 1151
    if last:
        import re
        m = re.match(r"^EDU(\d+)$", last["application_id"])
        if m:
            next_num = int(m.group(1)) + 1
    new_id = f"EDU{next_num}"

    credit_score = body.get("creditScore")
    if credit_score is not None:
        try:
            credit_score = int(float(credit_score))
        except (TypeError, ValueError):
            credit_score = None

    # Compute attention level (mirror of load_data.py)
    parent_income = int(body["parentMonthlyIncomeInr"])
    obligations = int(body["existingMonthlyObligationsInr"])
    dti = obligations / parent_income if parent_income > 0 else 1.0
    if credit_score is None or credit_score < 650 or dti > 0.5:
        attention = "High Attention"
    elif credit_score < 725 or dti > 0.3:
        attention = "Review Required"
    else:
        attention = "Low Attention"

    flags = []
    if credit_score is None:
        flags.append("MISSING_CREDIT_SCORE")
    if int(body["loanAmountRequestedInr"]) > course["typical_fee_inr"]:
        flags.append("LOAN_EXCEEDS_FEE")
    if obligations > parent_income:
        flags.append("OBLIGATIONS_EXCEED_INCOME")

    today = dt.date.today().isoformat()
    conn.execute(
        """INSERT INTO loan_applications
           (application_id, student_name, age, student_state, institution_id, institution_name,
            course_id, course_name, course_domain, course_fee_inr,
            loan_amount_requested_inr, parent_monthly_income_inr, existing_monthly_obligations_inr,
            credit_score, employment_type, application_date, application_status, application_channel,
            data_quality_flags, attention_level, debt_to_income_ratio, loan_to_fee_ratio)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            new_id, body["studentName"].strip(), int(body["age"]), body["studentState"].strip(),
            body["institutionId"], inst["institution_name"],
            body["courseId"], course["course_name"], course["domain"], course["typical_fee_inr"],
            int(body["loanAmountRequestedInr"]), parent_income, obligations,
            credit_score, body["employmentType"], today, "Submitted", body["applicationChannel"],
            json.dumps(flags), attention, dti, int(body["loanAmountRequestedInr"]) / course["typical_fee_inr"] if course["typical_fee_inr"] else None,
        ),
    )
    conn.commit()
    return jsonify({"application_id": new_id, "applicationStatus": "Submitted", "attentionLevel": attention}), 201


# --------------------------------------------------------------------------- #
# Static frontend serving (production build)
# --------------------------------------------------------------------------- #
@app.get("/")
def index():
    if (STATIC_DIR / "index.html").exists():
        return send_from_directory(STATIC_DIR, "index.html")
    return jsonify({
        "message": "Dhaniti API is running. Build the React frontend (cd frontend && npm run build) and copy dist/ to backend/static/ to serve the dashboard.",
        "endpoints": ["/api/login", "/api/kpis", "/api/charts", "/api/insights", "/api/data-quality", "/api/applications"],
    }), 200


@app.get("/<path:path>")
def static_files(path: str):
    # SPA fallback: serve static assets, fall back to index.html for client-side routes
    if (STATIC_DIR / path).exists():
        return send_from_directory(STATIC_DIR, path)
    if (STATIC_DIR / "index.html").exists():
        return send_from_directory(STATIC_DIR, "index.html")
    return jsonify({"error": "Not found"}), 404


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Ensure DB exists before serving
    if not DB_PATH.exists():
        print("[app] Database not found — running load_data.py first...")
        load_data.main()
    port = int(os.environ.get("PORT", 5000))
    print(f"[app] Dhaniti dashboard backend running on http://localhost:{port}")
    print(f"[app] Default login: admin / dhaniti123")
    app.run(host="0.0.0.0", port=port, debug=False)
