# Dhaniti API Reference

Base URL (development): `http://localhost:5000`

- Interactive docs: **`/docs`** (Swagger UI) · **`/redoc`**
- All responses are JSON.
- Error shape (every non-2xx response):

```json
{ "error": "Human-readable message", "details": ["optional", "field details"] }
```

- Authentication: send `Authorization: Bearer <token>` on protected routes.
- Rate-limited endpoints answer `429` with a `Retry-After` header.

---

## 1. Authentication

### POST /api/auth/register — create an account

Public · rate-limited (10/hour per IP)

```json
{ "name": "Rahul Verma", "email": "rahul@example.com",
  "password": "Passw0rd123", "confirmPassword": "Passw0rd123" }
```

**201** — the account is created (unverified) and a verification code is emailed:

```json
{ "message": "Account created. We sent a verification code to your email.",
  "user": { "userId": "USR-…", "email": "rahul@example.com", "name": "Rahul Verma",
            "avatarUrl": null, "role": "Credit Analyst", "oauthProvider": "local",
            "isVerified": false, "hasPassword": true },
  "expiresInMinutes": 10 }
```

Errors: `422` (invalid name/email/weak password/mismatch), `409` (email exists),
`429` (rate limited). Password rules: ≥ 8 chars, at least one letter + one number.

---

### POST /api/auth/login — email + password

Public · rate-limited (5 per 15 min per IP+email)

```json
{ "email": "admin@dhaniti.ai", "password": "DhanitiAdmin@123", "remember": false }
```

**200**:

```json
{ "token": "eyJhbGciOi…", "user": { "userId": "USR-ADMIN-01", "…": "…" } }
```

Errors: `401` (invalid email or password — identical message for unknown
accounts), `403` (email not verified — a new verification code is sent),
`422`, `429`. `remember: true` extends the session from 8 h to 30 days.

*Legacy alias:* `POST /api/login` accepts `{"username", "password"}` where
username may be the email local-part (e.g. `admin`).

---

### POST /api/auth/logout — revoke the session

**Requires auth**

**200**: `{ "message": "Signed out successfully.", "revoked": true }`

The token is added to the revocation list; subsequent calls with it return `401`.

---

### GET /api/auth/me — current user

**Requires auth** · **200**: the user object (same shape as login).
Errors: `401` (missing/invalid/expired/revoked token).

*Legacy alias:* `GET /api/whoami` → `{ "username", "name", "role" }`.

---

### PUT /api/auth/me — update profile

**Requires auth**

```json
{ "name": "New Name", "avatarUrl": "https://…" }
```

**200**: updated user object. Errors: `422` (invalid values).

---

### POST /api/auth/change-password

**Requires auth** · rate-limited

```json
{ "currentPassword": "…", "newPassword": "…" }
```

**204** on success. Errors: `422` (wrong current password / weak new password /
same as old).

---

## 2. OTP flows

### POST /api/auth/send-otp — request a code

Public · rate-limited (3 per 10 min per email, 9 per 10 min per IP)

```json
{ "email": "user@example.com", "purpose": "login" }
```

`purpose`: `login` | `password_reset` | `email_verification`.

**200** (identical whether or not the account exists — no enumeration):

```json
{ "message": "If an account exists for that email, a verification code has been sent.",
  "expiresInMinutes": 10 }
```

The code (6 digits) is emailed only — it is **never** in any API response.
Issuing a new code invalidates the previous one.

---

### POST /api/auth/verify-otp — verify & sign in

Public · rate-limited (10 per 15 min per email)

```json
{ "email": "user@example.com", "code": "123456", "purpose": "login", "remember": false }
```

`purpose`: `login` (sign in) or `email_verification` (activate account).

**200**: `{ "token": "…", "user": { … } }`
Errors: `401` (wrong code / expired / no active code / too many attempts),
`422`, `429`. Codes are single-use and lock out after 5 wrong attempts.

---

### POST /api/auth/verify-reset-otp — step 1 of password reset

Public · rate-limited

```json
{ "email": "user@example.com", "code": "123456" }
```

**200**: `{ "resetToken": "eyJ…", "message": "Code verified. Choose a new password.",
"expiresInMinutes": 15 }`

---

### POST /api/auth/reset-password — step 2 of password reset

Public · rate-limited (3 per 15 min per IP)

```json
{ "resetToken": "eyJ…", "newPassword": "BrandNew789" }
```

**200**: `{ "message": "Password updated. You can now sign in with your new password." }`

All active sessions for the user are revoked. Errors: `422` (invalid/expired
token, weak password), `429`.

---

### POST /api/auth/resend-verification

Public · rate-limited. `{ "email": "…" }` → **200** with a generic message.

---

## 3. OAuth (Google / GitHub)

| Method | Path                        | Auth | Description                                             |
| ------ | --------------------------- | ---- | ------------------------------------------------------- |
| GET    | `/auth/google`              | –    | 302 → Google consent screen (with CSRF `state`)          |
| GET    | `/auth/google/callback`     | –    | Exchanges code, finds/creates the user, 302 → SPA        |
| GET    | `/auth/github`              | –    | 302 → GitHub authorization                               |
| GET    | `/auth/github/callback`     | –    | Same pattern                                             |
| GET    | `/api/auth/oauth/providers` | –    | `{ "google": true, "github": false }` (configured?)      |
| POST   | `/api/auth/oauth/exchange`  | –    | Swap the one-time code for a session                     |

Flow:

```
React login → GET /auth/google → Google → GET /auth/google/callback
   → 302 {FRONTEND_URL}/oauth/callback?code=<one-time-code>
   → POST /api/auth/oauth/exchange {"code": …} → { "token", "user" }
```

The browser only ever sees the 60-second single-use exchange code — the JWT
never appears in a URL. User matching: provider+id → verified email (link) →
create. Unconfigured providers return **503** (never a fake success).

Configure in `backend/.env`:

```env
GOOGLE_CLIENT_ID=…            GOOGLE_CLIENT_SECRET=…
GITHUB_CLIENT_ID=…            GITHUB_CLIENT_SECRET=…
OAUTH_REDIRECT_BASE=http://localhost:5000
FRONTEND_URL=http://localhost:5173
```

Google redirect URI: `{OAUTH_REDIRECT_BASE}/auth/google/callback` ·
GitHub callback URL: `{OAUTH_REDIRECT_BASE}/auth/github/callback`.

---

## 4. Loan applications (CRUD)

All routes **require a valid session**. Write routes additionally require a
non-read-only role (`Admin`, `Underwriter`, `Risk Officer`) → `403` otherwise.

### GET /api/applications — list

Query params (all optional, original-compatible):

| Param            | Example           | Notes                                   |
| ---------------- | ----------------- | --------------------------------------- |
| `search`         | `priya`           | matches App ID or student name          |
| `status`         | `Approved`        | Submitted / Under Review / Approved / Rejected |
| `courseId`       | `CRS001`          |                                         |
| `institutionId`  | `INS003`          |                                         |
| `attentionLevel` | `High Attention`  |                                         |
| `sortBy`         | `applicationDate` | applicationDate / loanAmountRequestedInr / creditScore |
| `sortDir`        | `desc`            | asc / desc                              |
| `page`,`pageSize`| `1`,`10`          | NEW — omit both for the legacy full list|

**200** (legacy shape): `{ "count": 151, "data": [ …rows… ] }`
(with paging): `{ "count", "page", "pageSize", "totalPages", "data" }`

Row shape (camelCase, identical to the original Flask API):

```json
{ "id": "EDU1001", "studentName": "…", "age": 21, "studentState": "Karnataka",
  "institutionId": "INS001", "institutionName": "…", "courseId": "CRS001",
  "courseName": "MBA", "courseDomain": "Management", "courseFeeInr": 850000,
  "loanAmountRequestedInr": 1500000, "parentMonthlyIncomeInr": 120000,
  "existingMonthlyObligationsInr": 15000, "creditScore": 710,
  "employmentType": "Salaried", "applicationDate": "2025-04-01",
  "applicationStatus": "Approved", "applicationChannel": "Website",
  "dataQualityFlags": [], "attentionLevel": "Review Required",
  "debtToIncomeRatio": 0.125, "loanToFeeRatio": 1.765 }
```

### GET /api/applications/:id

**200** row · **404** not found.

### POST /api/applications — create

Body = the camelCase fields (studentName, age 16–100, studentState,
institutionId, courseId, loanAmountRequestedInr ≥ 10000, incomes ≥ 0,
creditScore 300–900 optional, employmentType, applicationChannel).

**201** created row (includes legacy `application_id` key).
Errors: `422` (validation / unknown institution or course), `403` (read-only
role), `401`. Attention level + data-quality flags are recomputed server-side.

### PATCH /api/applications/:id — status only

`{ "applicationStatus": "Approved" }` → **200**
`{ "application_id": "EDU1001", "applicationStatus": "Approved" }`
Errors: `422` (invalid status), `404`, `401`, `403`.

### PUT /api/applications/:id — full/partial update

Any subset of the create fields (+ `applicationStatus`, `applicationDate`).
Unspecified fields keep their values. **200** updated row.
Errors: `422`, `404`, `401`, `403`.

### DELETE /api/applications/:id

**200** `{ "success": true, "message": "Application EDU… deleted.",
"application_id": "EDU…" }` · **404**, **401**, **403`.
The UI always asks for confirmation before calling this.

---

## 5. Analytics (unchanged endpoints, now auth-protected)

| Method | Path                | Response highlights                                       |
| ------ | ------------------- | --------------------------------------------------------- |
| GET    | `/api/kpis`         | totalApplications, approved, underReview, rejected, …     |
| GET    | `/api/charts`       | 8 chart datasets (status, domain, course, institution, …) |
| GET    | `/api/insights`     | 5 calculated insights                                     |
| GET    | `/api/data-quality` | issue rows + flag legend + totalIssues                    |
| GET    | `/api/filters`      | institutions / courses / statuses for dropdowns           |
| GET    | `/api/health`       | public liveness probe                                     |

All require a session (401 otherwise).

---

## 6. Status codes

| Code | Meaning                                                      |
| ---- | ------------------------------------------------------------ |
| 200/201/204 | success (201 create, 204 no content)                   |
| 400  | malformed request                                            |
| 401  | missing / invalid / expired / revoked session                |
| 403  | authenticated but not allowed (read-only role, unverified)   |
| 404  | record not found                                             |
| 409  | conflict (duplicate email, already verified)                 |
| 422  | validation error (`details[]` lists fields)                  |
| 429  | rate limited (`Retry-After` header)                          |
| 500  | server error (generic message, no internals)                 |
| 503  | OAuth provider not configured                                |
