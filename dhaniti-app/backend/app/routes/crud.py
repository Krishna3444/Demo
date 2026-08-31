"""
routes/crud.py — loan application CRUD endpoints.

Compatibility contract with the ORIGINAL Flask backend (preserved so the
existing React dashboard keeps working unchanged):

  GET    /api/applications          ?search&status&courseId&institutionId&attentionLevel&sortBy&sortDir
                                    → {count, data:[camelCase rows]}
                                    (new: optional &page&pageSize → {count, page, pageSize, totalPages, data})
  GET    /api/applications/{id}     → camelCase row | 404
  POST   /api/applications          → 201 camelCase row (body is camelCase)
  PATCH  /api/applications/{id}     → {application_id, applicationStatus}
  PUT    /api/applications/{id}     → camelCase row (full/partial update)
  DELETE /api/applications/{id}     → {success, message, application_id}

New in this upgrade:
  * every endpoint requires a valid session (401 otherwise)
  * write endpoints enforce role-based authorization (403 for read-only roles)
  * optional pagination
  * full update (PUT) + delete (DELETE) + richer validation (422 with details)
  * attention level / data-quality flags recomputed on every write, exactly
    like the original load_data.py rules
"""

from __future__ import annotations

import datetime as dt
import json
import re
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import get_db
from ..security.authentication import get_current_user, require_write_role

router = APIRouter(prefix="/api/applications", tags=["Applications (CRUD)"])

VALID_STATUSES = ["Submitted", "Under Review", "Approved", "Rejected"]
VALID_ATTENTION = ["Low Attention", "Review Required", "High Attention"]
SORTABLE_FIELDS = {"applicationDate", "loanAmountRequestedInr", "creditScore"}

# --------------------------------------------------------------------------- #
# Pydantic payload models (camelCase, matching the existing frontend)
# --------------------------------------------------------------------------- #


class ApplicationCreate(BaseModel):
    studentName: str = Field(min_length=2, max_length=200)
    age: int = Field(ge=16, le=100)
    studentState: str = Field(min_length=2, max_length=100)
    institutionId: str = Field(min_length=1, max_length=50)
    courseId: str = Field(min_length=1, max_length=50)
    loanAmountRequestedInr: int = Field(ge=10000, le=1_000_000_000)
    parentMonthlyIncomeInr: int = Field(ge=0, le=1_000_000_000)
    existingMonthlyObligationsInr: int = Field(ge=0, le=1_000_000_000)
    creditScore: Optional[int] = Field(default=None, ge=300, le=900)
    employmentType: str = Field(min_length=2, max_length=100)
    applicationChannel: str = Field(min_length=2, max_length=100)
    applicationStatus: Optional[str] = None
    applicationDate: Optional[str] = None


class ApplicationUpdate(BaseModel):
    studentName: Optional[str] = Field(default=None, min_length=2, max_length=200)
    age: Optional[int] = Field(default=None, ge=16, le=100)
    studentState: Optional[str] = Field(default=None, min_length=2, max_length=100)
    institutionId: Optional[str] = Field(default=None, min_length=1, max_length=50)
    courseId: Optional[str] = Field(default=None, min_length=1, max_length=50)
    loanAmountRequestedInr: Optional[int] = Field(default=None, ge=10000, le=1_000_000_000)
    parentMonthlyIncomeInr: Optional[int] = Field(default=None, ge=0, le=1_000_000_000)
    existingMonthlyObligationsInr: Optional[int] = Field(default=None, ge=0, le=1_000_000_000)
    creditScore: Optional[int] = Field(default=None, ge=300, le=900)
    employmentType: Optional[str] = Field(default=None, min_length=2, max_length=100)
    applicationChannel: Optional[str] = Field(default=None, min_length=2, max_length=100)
    applicationStatus: Optional[str] = None
    applicationDate: Optional[str] = None


class StatusPatch(BaseModel):
    applicationStatus: str = Field(min_length=1, max_length=50)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def serialize_row(row) -> Optional[dict[str, Any]]:
    """sqlite row → camelCase dict identical to analysis.get_applications()."""
    if row is None:
        return None
    r = dict(row)
    try:
        flags = json.loads(r["data_quality_flags"]) if r["data_quality_flags"] else []
    except (TypeError, json.JSONDecodeError):
        flags = []
    return {
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
        "debtToIncomeRatio": round(r["debt_to_income_ratio"], 3) if r["debt_to_income_ratio"] is not None else None,
        "loanToFeeRatio": round(r["loan_to_fee_ratio"], 3) if r["loan_to_fee_ratio"] is not None else None,
    }


def calculate_attention_level(credit_score: Optional[int], income: int, obligations: int) -> str:
    """Identical rules to load_data.py / the original Flask backend."""
    if credit_score is None or credit_score < 650:
        return "High Attention"
    if income <= 0:
        return "High Attention"
    dti = obligations / income if income > 0 else 1.0
    if dti > 0.5:
        return "High Attention"
    if credit_score < 725 or dti > 0.3:
        return "Review Required"
    return "Low Attention"


def calculate_derived_fields(
    credit_score: Optional[int], income: int, obligations: int,
    loan_amount: int, course_fee: int,
) -> tuple[Optional[float], Optional[float], str, str]:
    dti = (obligations / income) if income and income > 0 else None
    loan_to_fee = (loan_amount / course_fee) if course_fee and course_fee > 0 else None
    attention = calculate_attention_level(credit_score, income, obligations)
    flags: list[str] = []
    if obligations > income:
        flags.append("OBLIGATIONS_EXCEED_INCOME")
    if credit_score is None:
        flags.append("MISSING_CREDIT_SCORE")
    if course_fee and loan_amount > course_fee:
        flags.append("LOAN_EXCEEDS_FEE")
    return dti, loan_to_fee, attention, json.dumps(flags)


def _fetch_application(db, application_id: str):
    return db.execute(
        "SELECT * FROM loan_applications WHERE application_id = ?", (application_id,)
    ).fetchone()


def _next_application_id(db) -> str:
    row = db.execute(
        "SELECT application_id FROM loan_applications ORDER BY application_id DESC LIMIT 1"
    ).fetchone()
    if not row:
        return "EDU1001"
    match = re.match(r"^EDU(\d+)$", row["application_id"])
    return f"EDU{int(match.group(1)) + 1}" if match else "EDU1001"


def _validate_references(db, institution_id: str, course_id: str, errors: list[str]) -> tuple[Optional[Any], Optional[Any]]:
    inst = db.execute(
        "SELECT institution_id, institution_name FROM institutions WHERE institution_id = ?",
        (institution_id,),
    ).fetchone()
    course = db.execute(
        "SELECT course_id, course_name, domain, typical_fee_inr FROM courses WHERE course_id = ?",
        (course_id,),
    ).fetchone()
    if inst is None:
        errors.append(f"Unknown institutionId: {institution_id}")
    if course is None:
        errors.append(f"Unknown courseId: {course_id}")
    return inst, course


def _validate_application_date(value: Optional[str], errors: list[str], field: str) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if not DATE_RE.match(value):
        errors.append(f"{field} must be an ISO date (YYYY-MM-DD).")
        return None
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{field} is not a valid calendar date.")
        return None
    return value


# --------------------------------------------------------------------------- #
# READ — list (Flask-compatible + optional pagination)
# --------------------------------------------------------------------------- #
@router.get("")
def list_applications(
    search: Optional[str] = Query(default=None, max_length=200),
    status: Optional[str] = Query(default=None),
    courseId: Optional[str] = Query(default=None, alias="courseId"),
    institutionId: Optional[str] = Query(default=None, alias="institutionId"),
    attentionLevel: Optional[str] = Query(default=None, alias="attentionLevel"),
    sortBy: str = Query(default="applicationDate"),
    sortDir: str = Query(default="desc"),
    page: Optional[int] = Query(default=None, ge=1, le=100000),
    pageSize: Optional[int] = Query(default=None, ge=1, le=500),
    db=Depends(get_db),
    user: dict = Depends(get_current_user),
):
    rows = db.execute(
        "SELECT * FROM loan_applications ORDER BY application_id"
    ).fetchall()
    items = [serialize_row(r) for r in rows]

    # ---- filters (same semantics as the Flask original) ----
    q = (search or "").strip().lower()
    if q:
        items = [r for r in items if q in r["id"].lower() or q in r["studentName"].lower()]
    if status and status != "all":
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=422, detail=f"status must be one of {VALID_STATUSES}")
        items = [r for r in items if r["applicationStatus"] == status]
    if courseId and courseId != "all":
        items = [r for r in items if r["courseId"] == courseId]
    if institutionId and institutionId != "all":
        items = [r for r in items if r["institutionId"] == institutionId]
    if attentionLevel and attentionLevel != "all":
        if attentionLevel not in VALID_ATTENTION:
            raise HTTPException(status_code=422, detail=f"attentionLevel must be one of {VALID_ATTENTION}")
        items = [r for r in items if r["attentionLevel"] == attentionLevel]

    # ---- sort ----
    if sortBy not in SORTABLE_FIELDS:
        raise HTTPException(
            status_code=422,
            detail=f"sortBy must be one of {sorted(SORTABLE_FIELDS)}",
        )
    reverse = sortDir.lower() != "asc"
    if sortBy == "creditScore":
        items.sort(key=lambda r: (r["creditScore"] if r["creditScore"] is not None else -1), reverse=reverse)
    elif sortBy == "loanAmountRequestedInr":
        items.sort(key=lambda r: r["loanAmountRequestedInr"], reverse=reverse)
    else:
        items.sort(key=lambda r: r["applicationDate"], reverse=reverse)

    # ---- pagination (optional; absent → legacy full-list behaviour) ----
    total = len(items)
    if page is None and pageSize is None:
        return {"count": total, "data": items}

    page = page or 1
    pageSize = pageSize or 20
    start = (page - 1) * pageSize
    data = items[start:start + pageSize]
    return {
        "count": total,
        "page": page,
        "pageSize": pageSize,
        "totalPages": (total + pageSize - 1) // pageSize,
        "data": data,
    }


# --------------------------------------------------------------------------- #
# READ — single
# --------------------------------------------------------------------------- #
@router.get("/{application_id}")
def get_application(
    application_id: str,
    db=Depends(get_db),
    user: dict = Depends(get_current_user),
):
    row = _fetch_application(db, application_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return serialize_row(row)


# --------------------------------------------------------------------------- #
# CREATE
# --------------------------------------------------------------------------- #
@router.post("", status_code=201)
def create_application(
    payload: ApplicationCreate,
    db=Depends(get_db),
    user: dict = Depends(require_write_role),
):
    errors: list[str] = []
    inst, course = _validate_references(db, payload.institutionId, payload.courseId, errors)
    application_date = payload.applicationDate or dt.date.today().isoformat()
    if payload.applicationDate is not None:
        application_date = _validate_application_date(payload.applicationDate, errors, "applicationDate") or dt.date.today().isoformat()

    status = payload.applicationStatus or "Submitted"
    if status not in VALID_STATUSES:
        errors.append(f"applicationStatus must be one of {VALID_STATUSES}")

    if errors:
        raise HTTPException(status_code=422, detail="; ".join(errors))

    assert inst is not None and course is not None  # validated above

    income = payload.parentMonthlyIncomeInr
    obligations = payload.existingMonthlyObligationsInr
    loan_amount = payload.loanAmountRequestedInr
    dti, loan_to_fee, attention, flags_json = calculate_derived_fields(
        payload.creditScore, income, obligations, loan_amount, course["typical_fee_inr"]
    )

    new_id = _next_application_id(db)
    db.execute(
        """
        INSERT INTO loan_applications (
            application_id, student_name, age, student_state,
            institution_id, institution_name, course_id, course_name, course_domain, course_fee_inr,
            loan_amount_requested_inr, parent_monthly_income_inr, existing_monthly_obligations_inr,
            credit_score, employment_type, application_date, application_status, application_channel,
            data_quality_flags, attention_level, debt_to_income_ratio, loan_to_fee_ratio
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            new_id, payload.studentName.strip(), payload.age, payload.studentState.strip(),
            inst["institution_id"], inst["institution_name"],
            course["course_id"], course["course_name"], course["domain"], course["typical_fee_inr"],
            loan_amount, income, obligations,
            payload.creditScore, payload.employmentType.strip(), application_date, status,
            payload.applicationChannel.strip(),
            flags_json, attention, dti, loan_to_fee,
        ),
    )
    db.commit()

    row = _fetch_application(db, new_id)
    created = serialize_row(row)
    # Keep the legacy Flask response keys alongside the full record.
    created["application_id"] = new_id
    return created


# --------------------------------------------------------------------------- #
# UPDATE — status only (legacy PATCH)
# --------------------------------------------------------------------------- #
@router.patch("/{application_id}")
def patch_status(
    application_id: str,
    payload: StatusPatch,
    db=Depends(get_db),
    user: dict = Depends(require_write_role),
):
    if payload.applicationStatus not in VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"applicationStatus must be one of: {VALID_STATUSES}",
        )
    row = _fetch_application(db, application_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    db.execute(
        "UPDATE loan_applications SET application_status = ? WHERE application_id = ?",
        (payload.applicationStatus, application_id),
    )
    db.commit()
    return {"application_id": application_id, "applicationStatus": payload.applicationStatus}


# --------------------------------------------------------------------------- #
# UPDATE — full/partial (PUT)
# --------------------------------------------------------------------------- #
@router.put("/{application_id}")
def update_application(
    application_id: str,
    payload: ApplicationUpdate,
    db=Depends(get_db),
    user: dict = Depends(require_write_role),
):
    existing = _fetch_application(db, application_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Application not found")
    current = dict(existing)
    updates = payload.model_dump(exclude_unset=True)

    student_name = updates.get("studentName", current["student_name"])
    age = updates.get("age", current["age"])
    student_state = updates.get("studentState", current["student_state"])
    institution_id = updates.get("institutionId", current["institution_id"])
    course_id = updates.get("courseId", current["course_id"])
    loan_amount = updates.get("loanAmountRequestedInr", current["loan_amount_requested_inr"])
    income = updates.get("parentMonthlyIncomeInr", current["parent_monthly_income_inr"])
    obligations = updates.get("existingMonthlyObligationsInr", current["existing_monthly_obligations_inr"])
    credit_score = updates.get("creditScore", current["credit_score"])
    employment_type = updates.get("employmentType", current["employment_type"])
    application_channel = updates.get("applicationChannel", current["application_channel"])
    application_date = updates.get("applicationDate", current["application_date"])
    application_status = updates.get("applicationStatus", current["application_status"])

    errors: list[str] = []
    inst, course = _validate_references(db, institution_id, course_id, errors)
    application_date = _validate_application_date(application_date, errors, "applicationDate")
    if application_status not in VALID_STATUSES:
        errors.append(f"applicationStatus must be one of {VALID_STATUSES}")
    if errors:
        raise HTTPException(status_code=422, detail="; ".join(errors))

    assert inst is not None and course is not None

    dti, loan_to_fee, attention, flags_json = calculate_derived_fields(
        credit_score, income, obligations, loan_amount, course["typical_fee_inr"]
    )

    db.execute(
        """
        UPDATE loan_applications SET
            student_name = ?, age = ?, student_state = ?,
            institution_id = ?, institution_name = ?,
            course_id = ?, course_name = ?, course_domain = ?, course_fee_inr = ?,
            loan_amount_requested_inr = ?, parent_monthly_income_inr = ?,
            existing_monthly_obligations_inr = ?,
            credit_score = ?, employment_type = ?, application_date = ?,
            application_status = ?, application_channel = ?,
            data_quality_flags = ?, attention_level = ?,
            debt_to_income_ratio = ?, loan_to_fee_ratio = ?
        WHERE application_id = ?
        """,
        (
            str(student_name).strip(), age, str(student_state).strip(),
            inst["institution_id"], inst["institution_name"],
            course["course_id"], course["course_name"], course["domain"], course["typical_fee_inr"],
            loan_amount, income, obligations,
            credit_score, str(employment_type).strip(), application_date,
            application_status, str(application_channel).strip(),
            flags_json, attention, dti, loan_to_fee,
            application_id,
        ),
    )
    db.commit()
    return serialize_row(_fetch_application(db, application_id))


# --------------------------------------------------------------------------- #
# DELETE
# --------------------------------------------------------------------------- #
@router.delete("/{application_id}")
def delete_application(
    application_id: str,
    db=Depends(get_db),
    user: dict = Depends(require_write_role),
):
    row = _fetch_application(db, application_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    db.execute("DELETE FROM loan_applications WHERE application_id = ?", (application_id,))
    db.commit()
    return {
        "success": True,
        "message": f"Application {application_id} deleted.",
        "application_id": application_id,
    }
