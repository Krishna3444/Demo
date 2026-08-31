"""
routes/analytics.py — read-only analytics endpoints.

These are the ORIGINAL Flask endpoints, moved to FastAPI 1:1. The SQL lives
in the unchanged `analysis.py` module, so every number the existing React
dashboard shows stays exactly the same:

  GET /api/kpis           GET /api/charts        GET /api/insights
  GET /api/data-quality   GET /api/filters

All of them now require a valid session token (they already did in Flask —
that behaviour is preserved).
"""

from __future__ import annotations

import analysis  # top-level module in backend/ (unchanged SQL analytics)
from fastapi import APIRouter, Depends

from ..database import get_db
from ..security.authentication import get_current_user

router = APIRouter(prefix="/api", tags=["Analytics"])


@router.get("/kpis")
def kpis(db=Depends(get_db), user: dict = Depends(get_current_user)):
    return analysis.get_kpis(db)


@router.get("/charts")
def charts(db=Depends(get_db), user: dict = Depends(get_current_user)):
    return analysis.get_charts(db)


@router.get("/insights")
def insights(db=Depends(get_db), user: dict = Depends(get_current_user)):
    return analysis.get_insights(db)


@router.get("/data-quality")
def data_quality(db=Depends(get_db), user: dict = Depends(get_current_user)):
    return analysis.get_data_quality(db)


@router.get("/filters")
def filters(db=Depends(get_db), user: dict = Depends(get_current_user)):
    return analysis.get_filter_options(db)
