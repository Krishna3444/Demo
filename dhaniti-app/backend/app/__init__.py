"""
Dhaniti backend package (FastAPI).

Structure:
    app/main.py               - FastAPI application entry point
    app/config.py             - environment-driven configuration
    app/database.py           - SQLite connection + schema migrations
    app/routes/               - API routers (auth, oauth, crud, analytics)
    app/services/             - business services (auth, otp, email, rate limiter)
    app/security/             - password hashing, JWT sessions, RBAC
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the backend/ directory importable (for `import analysis` /
# `import load_data`) no matter where uvicorn is launched from.
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)
