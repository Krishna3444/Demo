"""
database.py — SQLite connection management + schema migrations.

Fixes from the previous (broken) FastAPI attempt:
  * The old database.py pointed at a hard-coded Windows path
    (C:\\Users\\user\\Downloads\\...). We now resolve the database relative
    to the project root, overridable via the DATABASE_PATH env var.

Migrations are idempotent: they add missing tables/columns without ever
dropping or rewriting existing data. A timestamped backup of the database
file is taken before the first migration runs.
"""

from __future__ import annotations

import shutil
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Iterator

from . import config

# SQLite module defaults to serialised writes, but we still guard the
# migration routine against concurrent invocation inside one process.
_migration_lock = threading.Lock()
_migrated = False


def get_connection() -> sqlite3.Connection:
    """Open a connection to the Dhaniti SQLite database."""
    path = Path(config.DATABASE_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"SQLite database not found at {path}. "
            "Run `python load_data.py` in the backend directory to create it, "
            "or set DATABASE_PATH to the correct location."
        )
    connection = sqlite3.connect(str(path), check_same_thread=False, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency yielding a SQLite connection."""
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()


# --------------------------------------------------------------------------- #
# Migrations
# --------------------------------------------------------------------------- #
MIGRATIONS: list[tuple[str, str]] = [
    # (migration_id, sql)
    # 001 — OTP verification codes (hashed, expiring, attempt-limited)
    (
        "001_create_otp_codes",
        """
        CREATE TABLE IF NOT EXISTS otp_codes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            email       TEXT NOT NULL,
            purpose     TEXT NOT NULL,             -- login | email_verification | password_reset
            code_hash   TEXT NOT NULL,
            expires_at  TEXT NOT NULL,
            attempts    INTEGER NOT NULL DEFAULT 0,
            used        INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL
        )
        """,
    ),
    # 002 — Server-side sessions (hashed JWTs → revocable logout)
    (
        "002_create_sessions",
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            token_hash  TEXT NOT NULL UNIQUE,
            expires_at  TEXT NOT NULL,
            revoked_at  TEXT,
            created_at  TEXT NOT NULL
        )
        """,
    ),
    # 003 — One-time exchange codes used to hand a session token to the
    #       frontend after an OAuth callback without exposing it in a URL.
    (
        "003_create_auth_codes",
        """
        CREATE TABLE IF NOT EXISTS auth_codes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code_hash   TEXT NOT NULL UNIQUE,
            user_id     TEXT NOT NULL,
            expires_at  TEXT NOT NULL,
            used_at     TEXT,
            created_at  TEXT NOT NULL
        )
        """,
    ),
    # 004 — users.is_verified (email verification) + updated_at
    (
        "004_users_is_verified",
        "ALTER TABLE users ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 1",
    ),
    (
        "005_users_updated_at",
        "ALTER TABLE users ADD COLUMN updated_at TEXT",
    ),
]


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    return row is not None


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    return column in columns


def run_migrations(backup: bool = True) -> list[str]:
    """Apply pending idempotent migrations. Returns applied migration ids.

    Always call this BEFORE the server starts serving requests. A backup of
    the database file is created the first time a change is actually needed.
    """
    global _migrated
    with _migration_lock:
        conn = get_connection()
        applied: list[str] = []
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id          TEXT PRIMARY KEY,
                    applied_at  TEXT NOT NULL
                )
                """
            )
            conn.commit()

            already = {
                row[0]
                for row in conn.execute("SELECT id FROM schema_migrations")
            }

            needs_change = any(
                mid not in already and (
                    mid.startswith("004") or mid.startswith("005")
                    and _table_exists(conn, "users")
                )
                for mid, _ in MIGRATIONS
            )
            # Simpler & safer: consider backup needed when any migration is pending.
            pending = [(mid, sql) for mid, sql in MIGRATIONS if mid not in already]
            if backup and pending and not _migrated:
                src = Path(config.DATABASE_PATH)
                if src.exists():
                    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                    dst = src.with_name(f"{src.stem}.backup-{stamp}{src.suffix}")
                    shutil.copy2(src, dst)
                    print(f"[migrate] Backup created: {dst.name}")

            for mid, sql in MIGRATIONS:
                if mid in already:
                    continue
                if mid == "004_users_is_verified" and not _table_exists(conn, "users"):
                    # users table is created by ensure_users below; record and skip.
                    conn.execute(
                        "INSERT INTO schema_migrations (id, applied_at) VALUES (?, ?)",
                        (mid, datetime.utcnow().isoformat()),
                    )
                    conn.commit()
                    applied.append(mid)
                    continue
                if mid == "005_users_updated_at":
                    if not _table_exists(conn, "users") or _column_exists(
                        conn, "users", "updated_at"
                    ):
                        conn.execute(
                            "INSERT INTO schema_migrations (id, applied_at) VALUES (?, ?)",
                            (mid, datetime.utcnow().isoformat()),
                        )
                        conn.commit()
                        applied.append(mid)
                        continue
                try:
                    conn.execute(sql)
                except sqlite3.OperationalError as exc:
                    # "duplicate column name" → already applied out-of-band.
                    if "duplicate column" not in str(exc):
                        raise
                conn.execute(
                    "INSERT INTO schema_migrations (id, applied_at) VALUES (?, ?)",
                    (mid, datetime.utcnow().isoformat()),
                )
                conn.commit()
                applied.append(mid)

            _migrated = True
            return applied
        finally:
            conn.close()


# --------------------------------------------------------------------------- #
# Users bootstrap (demo accounts, idempotent)
# --------------------------------------------------------------------------- #
def ensure_users() -> None:
    """Make sure the `users` table exists and demo accounts are usable.

    The demo users previously stored SHA-256(salt+password) hashes created by
    an earlier prototype with passwords nobody can recover. We re-seed ONLY
    the three documented demo accounts with fresh Argon2 hashes of the
    documented demo passwords. Real registered users (and OAuth users) are
    never touched.
    """
    from .security.authentication import hash_password  # local import: avoid cycle

    conn = get_connection()
    try:
        if not _table_exists(conn, "users"):
            conn.execute(
                """
                CREATE TABLE users (
                    user_id       TEXT PRIMARY KEY,
                    email         TEXT UNIQUE NOT NULL,
                    name          TEXT NOT NULL,
                    avatar_url    TEXT,
                    role          TEXT NOT NULL DEFAULT 'Credit Analyst',
                    password_hash TEXT,
                    salt          TEXT,
                    oauth_provider TEXT DEFAULT 'local',
                    oauth_id      TEXT,
                    is_verified   INTEGER NOT NULL DEFAULT 1,
                    created_at    TEXT NOT NULL,
                    updated_at    TEXT,
                    last_login_at TEXT
                )
                """
            )
            conn.commit()

        demo_accounts = [
            ("USR-ADMIN-01", "admin@dhaniti.ai", "Alex Rivera (Lead Underwriter)", "Admin", "DhanitiAdmin@123"),
            ("USR-UNDR-02", "underwriter@dhaniti.ai", "Sarah Chen (Senior Underwriter)", "Underwriter", "Underwriter@123"),
            ("USR-ANLY-03", "analyst@dhaniti.ai", "David Kumar (Credit Analyst)", "Credit Analyst", "Analyst@123"),
        ]
        now = datetime.utcnow().isoformat()
        for user_id, email, name, role, password in demo_accounts:
            row = conn.execute(
                "SELECT user_id, password_hash FROM users WHERE email = ?", (email,)
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO users (user_id, email, name, role, password_hash,
                                       salt, oauth_provider, is_verified, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, NULL, 'local', 1, ?, ?)
                    """,
                    (user_id, email, name, role, hash_password(password), now, now),
                )
            elif not row["password_hash"] or not row["password_hash"].startswith("$argon2"):
                # Demo account with unknown/legacy hash → re-seed documented password.
                conn.execute(
                    "UPDATE users SET password_hash = ?, salt = NULL, is_verified = 1, updated_at = ? WHERE email = ?",
                    (hash_password(password), now, email),
                )
        # Existing users get is_verified=1 (they were active before this column existed).
        conn.execute("UPDATE users SET is_verified = 1 WHERE is_verified IS NULL")
        conn.commit()
    finally:
        conn.close()


def init_app_database() -> None:
    """Run migrations + ensure users exist. Called on application startup."""
    applied = run_migrations(backup=True)
    if applied:
        print(f"[migrate] Applied {len(applied)} migration(s): {', '.join(applied)}")
    else:
        print("[migrate] Schema up to date — no changes needed")
    ensure_users()
