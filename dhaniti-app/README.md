# Dhaniti Education Loan Dashboard — React + Bootstrap + FastAPI + SQLite

> Internal analytics prototype for the Dhaniti intern technical assignment.
> All records in the dataset are **synthetic** and must not be treated as real
> customer or underwriting data.

A full-stack application that lets an internal Dhaniti user:

- **Sign in securely** — email + password (Argon2id), **Google / GitHub OAuth**, or **email OTP** codes
- **Register** with email verification, recover passwords via emailed reset codes
- Manage a **session-based** account (server-revocable JWTs, real logout)
- View headline KPIs, 8 charts, 5 calculated business insights and a data-quality panel
- **Create / read / update / delete** loan applications with validation, pagination,
  search, filters, sorting, confirm-modals and toast notifications
- Work from desktop, tablet or mobile (Bootstrap 5 responsive)

---

## 1. Architecture

```
                    ┌─────────────────────────────┐
                    │   React 18 + Bootstrap 5    │
                    │   (Vite build, SPA)         │
                    └──────────────┬──────────────┘
                                   │  HTTP (Bearer JWT)
                                   ▼
        ┌────────────────────────────────────────────────┐
        │  FastAPI backend  (backend/app, port 5000)     │
        │                                                │
        │  /api/auth/*    register, login, OTP, reset    │
        │  /auth/google|github   OAuth 2.0 redirects     │
        │  /api/applications     CRUD (role-protected)   │
        │  /api/kpis|charts|insights|data-quality|filters│
        │  /            serves the built React app       │
        └───────────────┬────────────────────────────────┘
                        │  parameterized SQL (sqlite3)
                        ▼
        ┌────────────────────────────────────────────────┐
        │  SQLite (dhaniti_loans.db)                     │
        │  institutions · courses · loan_applications    │
        │  users · sessions · otp_codes · auth_codes     │
        └────────────────────────────────────────────────┘
```

**One API server (Python / FastAPI).** The original Flask prototype is preserved
at `backend/legacy_flask/app.py` for reference but is no longer the entrypoint —
its endpoints were ported 1:1 (same paths, same camelCase response shapes), so
the existing React dashboard code kept working throughout the upgrade.

Interactive API docs (auto-generated): **/docs** (Swagger UI) and **/redoc**.

### Project layout

```
dhaniti-app/
├── start.sh                          # start / stop / status launcher
├── dhaniti_loans.db                  # SQLite database (live data)
├── backend/
│   ├── app/                          # FastAPI application package
│   │   ├── main.py                   # entry point, CORS, error shape, static serving
│   │   ├── config.py                 # env-driven configuration + .env loader
│   │   ├── database.py               # connections + idempotent migrations
│   │   ├── routes/
│   │   │   ├── auth.py               # register/login/me/logout/OTP/reset
│   │   │   ├── oauth.py              # Google + GitHub OAuth flows
│   │   │   ├── crud.py               # loan-application CRUD
│   │   │   └── analytics.py          # kpis/charts/insights/dq/filters
│   │   ├── services/
│   │   │   ├── auth_service.py       # user lifecycle logic
│   │   │   ├── otp_service.py        # secure codes (hashed, expiring)
│   │   │   ├── email_service.py      # SMTP + dev outbox transport
│   │   │   └── rate_limiter.py       # sliding-window limiter
│   │   └── security/
│   │       └── authentication.py     # Argon2, JWT sessions, RBAC
│   ├── analysis.py                   # unchanged SQL analytics module
│   ├── load_data.py                  # CSV → SQLite loader (original)
│   ├── legacy_flask/app.py           # original Flask server (reference)
│   ├── tests/                        # pytest suite (58 tests)
│   ├── data/                          # source CSVs
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── api/{client,auth,items}.js # API layer (+ api.js compat shim)
    │   ├── context/                   # AuthContext, ToastContext
    │   ├── components/                # Navbar, ProtectedRoute, OtpInput,
    │   │                              # ApplicationsTable (+CRUD modals),
    │   │                              # KpiCards, Charts, Insights, DataQuality
    │   └── pages/                     # Login, Register, VerifyOtp,
    │                                  # ForgotPassword, ResetPassword,
    │                                  # OAuthCallback, Dashboard,
    │                                  # Applications, Profile, NotFound
    └── .env.example
```

---

## 2. Technology stack

| Layer      | Choice                                   | Why                                              |
| ---------- | ---------------------------------------- | ------------------------------------------------ |
| Frontend   | **React 18 + Bootstrap 5 + React Router**| Responsive UI, minimal boilerplate               |
| Icons      | **Bootstrap Icons**                      | Lightweight icon set matching the UI framework   |
| Charts     | **Chart.js 4** via `react-chartjs-2`     | Same charting as the original dashboard          |
| Backend    | **FastAPI** (Python 3.10+)              | Async, typed, auto API docs, dependency injection|
| Auth       | **JWT (PyJWT) + server-side sessions**   | Stateless tokens that can still be revoked      |
| Passwords  | **Argon2id** (argon2-cffi)               | Modern memory-hard KDF (legacy SHA-256 hashes are verified and transparently upgraded on login) |
| OTP        | **secrets-generated 6-digit codes, Argon2-hashed at rest** | Real verification without storing plaintext |
| Email      | **SMTP** (any provider) / dev file outbox | Works locally without credentials               |
| OAuth      | **Google + GitHub** (Authorization Code + state) | Real provider flows, secrets server-side only |
| Database   | **SQLite** (stdlib `sqlite3`)            | Single file, zero-config, portable              |
| Analytics  | Hand-written SQL (`analysis.py`)         | Every number is auditable                        |
| Build tool | **Vite 5+**                              | Fast dev server, optimized production build     |

---

## 3. How to run

### Requirements

- **Python 3.10+**
- **Node.js 18+** and **npm** (only needed to rebuild the frontend; a build is included)

### Quick start

```bash
cd dhaniti-app

# 1. (Optional) Build the React frontend — only if you changed React code
cd frontend
npm install
npm run build          # outputs to ../backend/static/
cd ..

# 2. Set up the Python backend (once)
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment (see backend/.env.example)
cp .env.example .env          # then edit values as needed

# 4. Load CSV data into SQLite (only needed once / to reset)
python load_data.py

# 5. Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000
# OR from the project root:
# cd .. && ./start.sh start
```

Then open **http://localhost:5000** — the login page is served by the backend.
The Vite dev server (`npm run dev` in `frontend/`, port 5173) proxies
`/api` and `/auth` to the backend for hot-reload development.

**Development convenience:** when `SMTP_*` variables are not configured,
emails (including OTP codes) are written to `backend/logs/emails/*.eml`
instead of being sent — the full register / OTP / reset flows can be tested
locally without an email provider.

### Demo credentials (development seed)

| Email                       | Password          | Role          | Access            |
| --------------------------- | ----------------- | ------------- | ----------------- |
| `admin@dhaniti.ai`          | `DhanitiAdmin@123`| Admin         | Full CRUD         |
| `underwriter@dhaniti.ai`    | `Underwriter@123` | Underwriter   | Full CRUD         |
| `analyst@dhaniti.ai`        | `Analyst@123`     | Credit Analyst| Read-only         |

New self-registered and OAuth accounts get the **Credit Analyst** (read-only)
role. Roles are enforced **server-side** (403) and reflected in the UI.

---

## 4. Authentication & security

- **Passwords** are hashed with **Argon2id**. The previous prototype's
  SHA-256(salt+password) hashes are still accepted and transparently upgraded
  to Argon2 on the next successful login (no user action required).
- **Sessions**: login issues a signed JWT that references a server-side
  `sessions` row (only a SHA-256 of the token is stored). Logout revokes the
  session — the token is dead immediately, even before its expiry.
  "Remember me" extends the TTL from 8 hours to 30 days.
- **OTP codes** are generated with `secrets`, stored **Argon2-hashed**,
  expire after 10 minutes, allow at most 5 wrong attempts, are single-use,
  and are invalidated when a new code is issued. They are sent by email only —
  never returned by the API.
- **Password reset** uses an emailed code → short-lived (15 min) reset token →
  new password. All active sessions are revoked after a password change.
- **OAuth (Google / GitHub)**: real Authorization-Code flows with server-side
  `state` CSRF protection. Client secrets never reach the browser. After the
  provider callback, the browser receives only a **60-second single-use
  exchange code**; the React app swaps it for the session token via
  `POST /api/auth/oauth/exchange`, so the JWT never appears in a URL.
- **Rate limiting** (sliding window): login 5/15 min per IP+email, OTP send
  3/10 min per email, OTP verify 10/15 min, registration 10/h, reset 3/15 min.
- **RBAC**: `Credit Analyst` is read-only; `Underwriter`, `Risk Officer` and
  `Admin` may create/update/delete.
- **SQL injection**: every query is parameterized.
- **Error hygiene**: responses use `{error, details}`; stack traces, database
  errors and internals are never exposed. Email existence is never confirmed
  (identical responses for unknown accounts).
- **Secrets** come from environment variables / `.env` (never committed —
  see `.gitignore`). `PRODUCTION=true` refuses to boot with a dev secret.

### Security checklist

- [x] Passwords hashed (Argon2id; legacy hashes auto-upgraded)
- [x] OAuth secrets in environment variables
- [x] OTPs hashed, expiring, attempt-limited, single-use
- [x] Login + OTP endpoints rate limited
- [x] Protected endpoints require a valid, non-revoked session
- [x] Role-based authorization on write endpoints (403 for read-only roles)
- [x] Parameterized SQL everywhere
- [x] CORS restricted to configured origins
- [x] Sensitive errors never exposed
- [x] `.env` git-ignored; `.env.example` documents every variable
- [x] Session/token revocation at logout and password change
- [x] HTTPS recommended for production (see §10)

---

## 5. Database / data model

Original tables are **unchanged** — `institutions` (12), `courses` (10),
`loan_applications` (151 records preserved through the upgrade).
The `users` table (added by the previous prototype) is kept with its
original columns; migrations only **added** `is_verified` and `updated_at`.

New tables (created by idempotent migrations on first boot, with an
automatic timestamped backup of the DB file):

| Table         | Purpose                                                        |
| ------------- | -------------------------------------------------------------- |
| `otp_codes`   | hashed verification codes (purpose, expiry, attempts, used)    |
| `sessions`    | sha256(JWT) → user, expiry, revocation time (real logout)      |
| `auth_codes`  | one-time 60s codes handing the session to the SPA after OAuth  |
| `schema_migrations` | applied migration ids                                    |

`loan_applications`, `institutions`, `courses` keep their original schema
(see §5 of the previous README / `load_data.py` for column docs). The unused
empty `applications` table left by an earlier attempt was dropped; no data
was in it.

### Migrations

Migrations run automatically at server startup (and can be run standalone):

```bash
cd backend && python -c "from app.database import init_app_database; init_app_database()"
```

They are idempotent (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN`
guarded), take a backup before the first change
(`dhaniti_loans.backup-YYYYMMDD-HHMMSS.db`), and were verified against a copy
of the live database before touching it.

---

## 6. REST API

Full request/response documentation: **[API.md](API.md)** and the live
Swagger UI at `/docs`. Summary:

### Authentication

| Method | Path                          | Description                                |
| ------ | ----------------------------- | ------------------------------------------ |
| POST   | `/api/auth/register`          | Create account (sends verification code)   |
| POST   | `/api/auth/login`             | Email + password login (also `/api/login`) |
| POST   | `/api/auth/logout`            | Revoke the current session                 |
| GET    | `/api/auth/me`                | Current user (also `/api/whoami`)          |
| PUT    | `/api/auth/me`                | Update name / avatar                       |
| POST   | `/api/auth/change-password`   | Change password (authenticated)            |
| POST   | `/api/auth/send-otp`          | Email a login / reset code                 |
| POST   | `/api/auth/verify-otp`        | Verify code → session (login / verify)     |
| POST   | `/api/auth/verify-reset-otp`  | Verify code → reset token                  |
| POST   | `/api/auth/reset-password`    | Set a new password with a reset token      |
| POST   | `/api/auth/resend-verification` | Resend email-verification code           |
| GET    | `/api/auth/oauth/providers`   | Which OAuth providers are configured       |

### OAuth

| Method | Path                            | Description                            |
| ------ | ------------------------------- | -------------------------------------- |
| GET    | `/auth/google`                  | Start Google OAuth (302 to Google)     |
| GET    | `/auth/google/callback`         | Google callback → redirect to SPA      |
| GET    | `/auth/github`                  | Start GitHub OAuth                    |
| GET    | `/auth/github/callback`         | GitHub callback → redirect to SPA      |
| POST   | `/api/auth/oauth/exchange`      | One-time code → {token, user}          |

### CRUD (loan applications — all require a session)

| Method | Path                       | Description                                   |
| ------ | -------------------------- | --------------------------------------------- |
| GET    | `/api/applications`        | List + search/filter/sort (+ optional paging) |
| GET    | `/api/applications/:id`    | Single application                            |
| POST   | `/api/applications`        | Create (write role required)                  |
| PATCH  | `/api/applications/:id`    | Update status (write role required)           |
| PUT    | `/api/applications/:id`    | Full/partial update (write role required)     |
| DELETE | `/api/applications/:id`    | Delete (write role required)                  |

### Analytics (all require a session — unchanged from the original app)

`GET /api/kpis` · `GET /api/charts` · `GET /api/insights` ·
`GET /api/data-quality` · `GET /api/filters`

---

## 7. Attention Level rules (illustrative — NOT real underwriting policy)

Unchanged from the original prototype; recomputed on every create/update:

| Level              | Trigger                                                                |
| ------------------ | ---------------------------------------------------------------------- |
| **High Attention** | credit_score missing OR < 650 OR obligations > 50% of income            |
| **Review Required**| credit_score 650–724 OR obligations 30–50% of income                    |
| **Low Attention**  | credit_score ≥ 725 AND obligations < 30% of income                      |

---

## 8. Data-quality issues identified and handled

Unchanged — 8 issues across 8 applications, each stored as a code in
`data_quality_flags` (see the Data Quality tab in the dashboard):
`OBLIGATIONS_EXCEED_INCOME` (EDU1008, EDU1019), `INSTITUTION_NAME_NORMALISED`
(EDU1032), `WHITESPACE_COURSE_NAME` (EDU1065), `MISSING_CREDIT_SCORE`
(EDU1092), `WHITESPACE_CHANNEL` (EDU1121), `STATE_TYPO_FIXED` (EDU1134),
`LOAN_EXCEEDS_FEE` (EDU1143).

---

## 9. Testing

```bash
cd backend
python -m pytest tests/ -v        # 58 tests: auth, OTP, CRUD, RBAC, compat
bash tests/smoke.sh               # end-to-end smoke test against a running server
```

Coverage highlights (see `tests/`):

- **Auth**: valid/invalid/missing login, unknown-user vs wrong-password
  identical errors, rate limiting, logout revocation, profile update,
  password change (old password invalidated)
- **OTP**: delivery, correct/incorrect code, expiry, single-use, max-attempt
  lockout, code hashed at rest, resend invalidates the previous code, full
  forgot-password → reset flow, registration → verification → login
- **CRUD**: create (valid/invalid/missing data, unknown references), read
  (list/search/pagination/single/404), update (PATCH status + PUT full),
  delete (+ 404 on repeat), 401 without a token, 403 for read-only roles,
  original analytics response shapes preserved

The database used by the test suite is a **temporary copy**; live data is
never touched.

---

## 10. Production deployment notes

1. **Secrets** — generate a strong `SECRET_KEY`
   (`python -c "import secrets; print(secrets.token_hex(32))"`) and set it in
   the environment (not in the repo). Set `PRODUCTION=true` so the app refuses
   to boot with placeholder secrets.
2. **HTTPS** — terminate TLS at a reverse proxy (nginx / Caddy / Traefik /
   a cloud load balancer) and forward to uvicorn. Cookies and redirects rely
   on the proxy's `X-Forwarded-For` / `X-Forwarded-Proto` headers.
3. **WSGI server** — run multiple workers behind the proxy:
   `uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 5000`.
   NOTE: the in-memory rate limiter is per-process; for multi-worker
   deployments swap it for Redis (interface is a drop-in).
4. **Email** — configure real SMTP credentials (`SMTP_*`), e.g. SendGrid,
   Resend, SES or Gmail app passwords. Until configured, mail is written to
   `backend/logs/emails/`.
5. **OAuth** — register redirect URIs with the providers:
   `https://your-domain/auth/google/callback` and
   `/auth/github/callback`; set `OAUTH_REDIRECT_BASE` and `FRONTEND_URL`
   accordingly.
6. **CORS** — set `CORS_ORIGINS` to your exact frontend origins.
7. **Database** — SQLite in WAL mode is fine for this workload; back up the
   `.db` file on a schedule (migrations already do ad-hoc backups before
   schema changes). PostgreSQL would be a drop-in migration path at scale.
8. **Logs** — uvicorn logs to stdout; pipe them into your log aggregator.

---

## 11. Key assumptions

1. The dataset is small (151 rows) — SQLite is the right tool; PostgreSQL is a
   drop-in replacement if scale becomes a concern.
2. `application_status` is the source of truth for approval metrics.
3. `parent_monthly_income_inr = 0` means "no declared income" (flagged, not dropped).
4. Attention Level rules are illustrative, not Dhaniti's real policy.
5. Loan applications are **portfolio-wide**, not per-user; authorization is
   role-based (read vs write) rather than record-ownership-based.
6. One linked OAuth identity per user (the existing `users` schema stores
   `oauth_provider` / `oauth_id`); signing in with a second provider using a
   verified email re-links the identity.
7. The JWT lives in `localStorage` (Bearer-token architecture inherited from
   the original app — CSRF-safe); a hardened deployment can move refresh
   credentials to HTTP-only cookies.

---

## 12. Known limitations

1. Rate limiting is in-memory (per-process) — swap in Redis for multi-worker.
2. One OAuth identity per user (see assumptions).
3. No audit log of status changes yet.
4. No CSV/Excel export or bulk updates yet.
5. Credit-score buckets are hard-coded at 50-point intervals.

---

## 13. What was upgraded vs preserved

| Preserved (unchanged)                          | Upgraded / added                                   |
| ---------------------------------------------- | -------------------------------------------------- |
| `analysis.py` SQL analytics module             | Flask → FastAPI migration (same endpoints/shapes)  |
| `load_data.py` CSV loader + cleaning           | Real auth: Argon2 passwords, revocable sessions    |
| All 151 loan records + institutions + courses  | Registration with email verification               |
| Existing React components (KPIs/charts/…)      | Google + GitHub OAuth (real flows)                 |
| camelCase API contract of the original app     | OTP login + forgot/reset password via email        |
| Attention-level + data-quality rule logic      | Full CRUD UI + APIs with RBAC                      |
| Legacy `/api/login`, `/api/whoami` aliases     | Rate limiting, pagination, toasts, 404, profile    |
| `start.sh` start/stop/status interface         | pytest suite (58) + smoke tests (32)               |

---

## 14. Verification performed

- 58/58 pytest tests pass (`backend/tests/`)
- 32/32 API smoke tests pass (`backend/tests/smoke.sh`)
- Browser-verified end-to-end (agent-browser): login (wrong + correct),
  dashboard + all 8 charts, applications CRUD (create → view → edit →
  delete with cancel), pagination, search/filters/sort, read-only role
  hides write controls, registration + OTP verification, OTP login,
  forgot-password + reset + re-login, logout revocation, protected-route
  redirects, 404 page, mobile (390 px) layout, zero console errors.
- OAuth flows verified to the extent possible without provider credentials:
  unconfigured providers return a clean 503 and the UI disables the buttons;
  the flow itself (state, exchange codes, redirects) is fully implemented
  and covered by the exchange-code logic. Add real credentials to activate.
