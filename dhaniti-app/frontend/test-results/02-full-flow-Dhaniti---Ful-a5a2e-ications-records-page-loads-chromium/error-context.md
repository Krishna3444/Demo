# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 02-full-flow.spec.js >> Dhaniti - Full Application E2E Flow >> Applications records page loads
- Location: e2e\02-full-flow.spec.js:62:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByPlaceholder('Search by App ID or student name...')
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for getByPlaceholder('Search by App ID or student name...')

```

```yaml
- navigation:
  - link "D Dhaniti":
    - /url: /dashboard
  - list:
    - listitem:
      - link "Dashboard":
        - /url: /dashboard
    - listitem:
      - link "Applications":
        - /url: /applications
    - listitem:
      - link "Profile":
        - /url: /profile
  - text: Credit Analyst David Kumar (Credit Analyst)
  - button "Logout"
- main:
  - heading "Welcome, David" [level=4]
  - paragraph: Here is what is happening with the education-loan portfolio today.
  - link "Manage applications":
    - /url: /applications
  - list:
    - listitem:
      - button "Overview"
    - listitem:
      - button "Applications 151"
    - listitem:
      - button "Insights 5"
    - listitem:
      - button "Data Quality 8"
  - text: Key Metrics 151 Total Applications 151 All records in dataset Approved 71 47% approval rate Under Review 50 Active in pipeline Rejected 15 Declined by rule Submitted 15 Awaiting first review Total Loan Requested ₹7.54 Cr Sum of loan_amount_requested_inr Avg Loan Amount ₹5.00 L Per application Avg Credit Score 696 Excludes missing Distribution Charts
  - heading "Applications by Status" [level=5]
  - img
  - heading "Applications by Course Domain" [level=5]
  - img
  - heading "Applications by Course" [level=5]
  - img
  - heading "Applications by Institution" [level=5]
  - img
  - heading "Monthly Trend (Stacked by Status)" [level=5]
  - img
  - heading "Credit-Score Distribution" [level=5]
  - img
  - heading "Avg Loan Amount by Course" [level=5]
  - img
  - heading "Applications by Acquisition Channel" [level=5]
  - img
- contentinfo: Dhaniti Education Loan Dashboard · React + Bootstrap + FastAPI + SQLite · All records are synthetic. Do not treat as real customer or underwriting data.
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test'
  2   | 
  3   | test.describe('Dhaniti - Full Application E2E Flow', () => {
  4   | 
  5   |   const email = 'analyst@dhaniti.ai'
  6   |   const password = 'Analyst@123'
  7   | 
  8   |   // ==========================================
  9   |   // LOGIN
  10  |   // ==========================================
  11  | 
  12  |   test.beforeEach(async ({ page }) => {
  13  | 
  14  |     await page.goto('/')
  15  | 
  16  |     await expect(
  17  |       page.getByPlaceholder('you@company.com')
  18  |     ).toBeVisible({ timeout: 10000 })
  19  | 
  20  |     await page
  21  |       .getByPlaceholder('you@company.com')
  22  |       .fill(email)
  23  | 
  24  |     await page
  25  |       .locator('input[type="password"]')
  26  |       .fill(password)
  27  | 
  28  |     await page.getByRole('button', {
  29  |       name: 'LOGIN',
  30  |       exact: true
  31  |     }).click()
  32  | 
  33  |     // Dashboard
  34  |     await expect(
  35  |       page.getByText(/dashboard/i).first()
  36  |     ).toBeVisible({
  37  |       timeout: 15000
  38  |     })
  39  |   })
  40  | 
  41  | 
  42  |   // ==========================================
  43  |   // 1. DASHBOARD
  44  |   // ==========================================
  45  | 
  46  |   test('Dashboard loads successfully', async ({ page }) => {
  47  | 
  48  |     await expect(
  49  |       page.getByText(/dashboard/i).first()
  50  |     ).toBeVisible()
  51  | 
  52  |     await expect(
  53  |       page.locator('body')
  54  |     ).not.toHaveText('')
  55  |   })
  56  | 
  57  | 
  58  |   // ==========================================
  59  |   // 2. APPLICATIONS / RECORDS PAGE
  60  |   // ==========================================
  61  | 
  62  |   test('Applications records page loads', async ({ page }) => {
  63  | 
  64  |     // Search input from your screenshot
  65  |     await expect(
  66  |       page.getByPlaceholder(
  67  |         'Search by App ID or student name...'
  68  |       )
> 69  |     ).toBeVisible({
      |       ^ Error: expect(locator).toBeVisible() failed
  70  |       timeout: 10000
  71  |     })
  72  | 
  73  |     // Add Record button
  74  |     await expect(
  75  |       page.getByRole('button', {
  76  |         name: /add record/i
  77  |       })
  78  |     ).toBeVisible()
  79  | 
  80  |     // Applications count
  81  |     await expect(
  82  |       page.getByText(/showing.*applications/i)
  83  |     ).toBeVisible()
  84  |   })
  85  | 
  86  | 
  87  |   // ==========================================
  88  |   // 3. SEARCH
  89  |   // ==========================================
  90  | 
  91  |   test('User can search applications', async ({ page }) => {
  92  | 
  93  |     const search = page.getByPlaceholder(
  94  |       'Search by App ID or student name...'
  95  |     )
  96  | 
  97  |     await search.fill('EDU1151')
  98  | 
  99  |     await page.waitForTimeout(5000)
  100 | 
  101 |     // Verify matching application
  102 |     await expect(
  103 |       page.getByText('EDU1151')
  104 |     ).toBeVisible()
  105 |   })
  106 | 
  107 | 
  108 |   // ==========================================
  109 |   // 4. CLEAR SEARCH
  110 |   // ==========================================
  111 | 
  112 |   test('User can change application search', async ({ page }) => {
  113 | 
  114 |     const search = page.getByPlaceholder(
  115 |       'Search by App ID or student name...'
  116 |     )
  117 | 
  118 |     await search.fill('Keerthi Reddy')
  119 | 
  120 |     await page.waitForTimeout(500)
  121 | 
  122 |     await expect(
  123 |       page.getByText('Keerthi Reddy')
  124 |     ).toBeVisible()
  125 |   })
  126 | 
  127 | 
  128 |   // ==========================================
  129 |   // 5. FILTER
  130 |   // ==========================================
  131 | 
  132 |   test('User can filter applications by status', async ({ page }) => {
  133 | 
  134 |     const statusSelect = page.getByRole('combobox').first()
  135 | 
  136 |     await expect(statusSelect).toBeVisible()
  137 | 
  138 |     await statusSelect.click()
  139 | 
  140 |     // Select Approved if available
  141 |     const approved = page.getByText(
  142 |       'Approved',
  143 |       { exact: true }
  144 |     ).last()
  145 | 
  146 |     if (await approved.count() > 0) {
  147 |       await approved.click()
  148 |     }
  149 | 
  150 |     await page.waitForTimeout(500)
  151 |   })
  152 | 
  153 | 
  154 |   // ==========================================
  155 |   // 6. ADD RECORD
  156 |   // ==========================================
  157 | 
  158 |   test('User can open Add Record form', async ({ page }) => {
  159 | 
  160 |     const addRecord = page.getByRole('button', {
  161 |       name: /add record/i
  162 |     })
  163 | 
  164 |     await expect(addRecord).toBeVisible()
  165 | 
  166 |     await addRecord.click()
  167 | 
  168 |     await page.waitForTimeout(500)
  169 | 
```