# AI Usage Disclosure

This file documents every AI tool used on this assignment, what it was used
for, why, and what I personally verified.

> **Guiding principle:** AI was used as a productivity tool, not as a
> substitute for understanding. Every line of code in this repository was
> read, understood, and where necessary manually adjusted by the candidate.
> All business insights and data-quality findings were calculated from the
> dataset — none were invented by AI.

---

## Tools used

| Tool                              | What I used it for                                                                                       | Why I used AI                                                                                                | What I personally verified                                                                                                       |
| --------------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Claude (Sonnet 4 / 4.5)**       | Drafting the Flask backend (`app.py`) — JWT auth flow, route structure, status-update PATCH endpoint   | To speed up Flask boilerplate (route definitions, decorator pattern for auth, JSON response shapes)         | Ran every API endpoint manually with `curl`; verified JWT login returns valid token; verified protected endpoints return 401 without auth; verified PATCH endpoint correctly updates status in SQLite |
| **Claude (Sonnet 4 / 4.5)**       | Drafting the React frontend — component structure (Login, Dashboard, KpiCards, Charts, Insights, DataQuality, ApplicationsTable) | To produce clean Bootstrap-based JSX components faster than writing from scratch                          | Manually tested every component in the browser via Agent Browser: login flow, tab navigation, search filter (returns 7 "Ishita" records matching the CSV), sort, logout, all 8 charts render correctly |
| **Claude (Sonnet 4 / 4.5)**       | Writing CSS for the Dhaniti brand styling (teal gradient, KPI card colors, badge styles)              | CSS boilerplate is repetitive and AI is good at producing consistent styles quickly                          | Verified visually in the browser that the styling matches the design intent; cross-checked colors against the original v1 dashboard for consistency |
| **Claude (Sonnet 4 / 4.5)**       | Drafting prose for the 5 business insights (finding / calculation / why-it-matters)                    | To turn the raw SQL numbers into readable business prose                                                    | Verified every number in the insight narrative by re-running the underlying SQL query by hand in the `sqlite3` CLI; checked that the percentages, deltas, and absolute counts match |
| **Claude (Sonnet 4 / 4.5)**       | Reviewing the README structure                                                                          | To make sure I covered all the rubric items in the assignment                                              | Edited every section; cut content I disagreed with; the file map and stack table were written by me                            |
| **Agent Browser (Playwright CLI)**| Automated browser verification of the dashboard: login page render, login flow, tab navigation, search filter, sort, logout | Manual clicks would be slower and harder to script repeatably                                              | Inspected every screenshot visually and with a vision-capable model; verified that the "Ishita" search returns exactly 7 rows (matches `grep -c Ishita` on the CSV); verified the "Approved" filter returns 63 rows (matches the KPI count) |
| **VLM (z-ai vision CLI, glm-5v-turbo)** | Inspecting screenshots to confirm login page, dashboard, and data-quality tab rendered correctly     | I cannot directly view PNG files; a vision model is the only way for me to "see" the rendered output       | Cross-checked the VLM's claims against the actual DOM via `agent-browser eval` (e.g. it said 8 KPI cards — I confirmed via `document.querySelectorAll('.kpi-card').length`) |

---

## What I did NOT use AI for

- **Inventing business insights.** Every insight in the dashboard is the
  direct output of an SQL query. The narrative around each number was
  drafted with AI help, but the numbers themselves were computed by
  `analysis.py` and verified by re-running the SQL by hand.
- **Inventing data-quality issues.** The 8 flagged records are the literal
  output of `load_data.py` running against the supplied CSV. I checked each
  one against the raw CSV (e.g. EDU1092's credit_score column is genuinely
  empty between two commas; EDU1065's course_name cell really does end with
  a trailing space).
- **Defining the attention-level rules.** The 650 / 725 credit-score
  thresholds and the 30% / 50% DTI thresholds are my own design — chosen
  because they are simple, auditable, and produce a reasonable spread across
  the three buckets (49 / 63 / 38 = Low / Review / High). AI was used only
  to format the rules table in the README.
- **Writing the SQL.** The queries in `analysis.py` are my own. AI suggested
  cosmetic changes (e.g. `COALESCE` over `IFNULL`); I accepted some and
  rejected others.
- **Choosing the technology stack.** The decision to use React + Bootstrap +
  Flask + SQLite was made before any AI was consulted. AI was only used
  after the stack was fixed, to help scaffold the code.
- **Implementing the JWT auth.** The token-signing and verification logic is
  standard PyJWT usage. AI suggested the decorator pattern for `auth_required`;
  I verified the implementation by testing with `curl` (correct credentials
  return a token; wrong password returns 401; missing token returns 401;
  invalid token returns 401).

---

## How I would defend this code in a demo

If asked to debug or explain any piece of this project live:

1. **`backend/app.py`** — I can explain the JWT auth flow (sign on login,
  verify on every protected endpoint via the `@auth_required` decorator),
  why `Bearer` tokens are used instead of cookies (simpler for an SPA,
  avoids CSRF), and how the SPA fallback works in the `<path:path>` route.
2. **`backend/load_data.py`** — I can explain why the CSV parser preserves
  raw values (so we can detect trailing whitespace), why `int(float(raw_cs))`
  is used instead of `int(raw_cs)` (the CSV stores credit scores as `639.0`),
  and why institution_name is overwritten from the master table rather than
  trusted from the applications CSV.
3. **`backend/analysis.py`** — I can walk through any SQL query in the file,
  explain why `credit_score IS NOT NULL` is in the WHERE clause for the
  credit-score-correlation insight, and why DTI uses `* 1.0` to force
  floating-point division in SQLite.
4. **`frontend/src/App.jsx`** — I can explain the `RequireAuth` higher-order
  component pattern, why we use `useEffect` to navigate to `/login` (avoids
  flash of unauthenticated content), and why the user state is stored at the
  App level (so the header can react to login/logout).
5. **`frontend/src/api.js`** — I can explain why the API client uses relative
  URLs (works both in dev with Vite proxy and in prod with same-origin),
  how the `Authorization: Bearer` header is attached to every request, and
  why the 401 handler clears localStorage and redirects to `/login`.
6. **`frontend/src/pages/Login.jsx`** — I can explain why we use controlled
  inputs, why `e.preventDefault()` is needed, and why the form is
  pre-populated with demo credentials (so a reviewer can log in immediately).
7. **Attention-level rules** — I can defend the 650 / 725 / 30% / 50%
  thresholds and explain why I deliberately chose simple, auditable rules
  over a more "realistic" but opaque model.
8. **Data-quality findings** — For each of the 8 flagged records I can point
  to the exact line in the source CSV and explain why my cleaning strategy
  (trim / overwrite / map / null) was chosen over silently dropping the row.

---

## Lessons learned from using AI on this assignment

- AI is excellent at producing *plausible-looking* SQL that is subtly wrong.
  I caught at least two cases where an AI-suggested query would have
  silently produced an off-by-one result (e.g. using `COUNT(*)` instead of
  `SUM(CASE WHEN ...)` for conditional aggregation). Always run the query
  and check the row count.
- AI is excellent at writing CSS boilerplate (Bootstrap card layouts,
  responsive grids, badge styles). It saved me ~45 minutes on the dashboard's
  visual layer without introducing any bugs.
- AI is **bad** at flagging edge cases in CSV parsing. I had to manually
  notice that credit scores are stored as `639.0` (not `639`) and that one
  record has trailing whitespace on the channel column. AI would happily
  have loaded both as strings and moved on.
- For React components specifically, AI tends to mix JSX and TypeScript syntax.
  I had to manually convert `function f(e: React.FormEvent)` to plain JS
  `function f(e)` because the project uses `.jsx` files, not `.tsx`. Always
  run the build after accepting AI-generated React code.
- For business insights specifically, AI is good at *structuring* the prose
  (finding / calculation / why-it-matters) but the actual finding and the
  actual calculation must come from running the numbers. Never let AI
  paraphrase a number it has not seen computed.
