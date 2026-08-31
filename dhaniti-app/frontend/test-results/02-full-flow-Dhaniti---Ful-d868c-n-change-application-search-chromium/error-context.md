# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 02-full-flow.spec.js >> Dhaniti - Full Application E2E Flow >> User can change application search
- Location: e2e\02-full-flow.spec.js:112:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByPlaceholder('Search by App ID or student name...')

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - navigation [ref=e4]:
    - generic [ref=e5]:
      - link "D Dhaniti" [ref=e6] [cursor=pointer]:
        - /url: /dashboard
        - generic [ref=e7]: D
        - generic [ref=e8]: Dhaniti
      - generic [ref=e9]:
        - list [ref=e10]:
          - listitem [ref=e11]:
            - link "Dashboard" [ref=e12] [cursor=pointer]:
              - /url: /dashboard
          - listitem [ref=e13]:
            - link "Applications" [ref=e14] [cursor=pointer]:
              - /url: /applications
          - listitem [ref=e15]:
            - link "Profile" [ref=e16] [cursor=pointer]:
              - /url: /profile
        - generic [ref=e17]:
          - generic [ref=e18]: Credit Analyst
          - generic [ref=e19]: David Kumar (Credit Analyst)
          - button "Logout" [ref=e20] [cursor=pointer]:
            - generic [ref=e21]: 
            - text: Logout
  - main [ref=e22]:
    - generic [ref=e24]:
      - generic [ref=e25]:
        - heading "Welcome, David" [level=4] [ref=e26]
        - paragraph [ref=e27]: Here is what is happening with the education-loan portfolio today.
      - link "Manage applications" [ref=e28] [cursor=pointer]:
        - /url: /applications
        - generic [ref=e29]: 
        - text: Manage applications
    - list [ref=e30]:
      - listitem [ref=e31]:
        - button "Overview" [ref=e32] [cursor=pointer]
      - listitem [ref=e33]:
        - button "Applications 151" [ref=e34] [cursor=pointer]:
          - text: Applications
          - generic [ref=e35]: "151"
      - listitem [ref=e36]:
        - button "Insights 5" [ref=e37] [cursor=pointer]:
          - text: Insights
          - generic [ref=e38]: "5"
      - listitem [ref=e39]:
        - button "Data Quality 8" [ref=e40] [cursor=pointer]:
          - text: Data Quality
          - generic [ref=e41]: "8"
    - generic [ref=e42]:
      - generic [ref=e43]:
        - generic [ref=e44]:
          - text: Key Metrics
          - generic [ref=e45]: "151"
        - generic [ref=e47]:
          - generic [ref=e50]:
            - generic [ref=e51]: Total Applications
            - generic [ref=e52]: "151"
            - generic [ref=e53]: All records in dataset
          - generic [ref=e56]:
            - generic [ref=e57]: Approved
            - generic [ref=e58]: "71"
            - generic [ref=e59]: 47% approval rate
          - generic [ref=e62]:
            - generic [ref=e63]: Under Review
            - generic [ref=e64]: "50"
            - generic [ref=e65]: Active in pipeline
          - generic [ref=e68]:
            - generic [ref=e69]: Rejected
            - generic [ref=e70]: "15"
            - generic [ref=e71]: Declined by rule
          - generic [ref=e74]:
            - generic [ref=e75]: Submitted
            - generic [ref=e76]: "15"
            - generic [ref=e77]: Awaiting first review
          - generic [ref=e80]:
            - generic [ref=e81]: Total Loan Requested
            - generic [ref=e82]: ₹7.54 Cr
            - generic [ref=e83]: Sum of loan_amount_requested_inr
          - generic [ref=e86]:
            - generic [ref=e87]: Avg Loan Amount
            - generic [ref=e88]: ₹5.00 L
            - generic [ref=e89]: Per application
          - generic [ref=e92]:
            - generic [ref=e93]: Avg Credit Score
            - generic [ref=e94]: "696"
            - generic [ref=e95]: Excludes missing
      - generic [ref=e96]:
        - generic [ref=e97]: Distribution Charts
        - generic [ref=e99]:
          - heading "Applications by Status" [level=5] [ref=e103]
          - heading "Applications by Course Domain" [level=5] [ref=e109]
          - heading "Applications by Course" [level=5] [ref=e115]
          - heading "Applications by Institution" [level=5] [ref=e121]
          - heading "Monthly Trend (Stacked by Status)" [level=5] [ref=e127]
          - heading "Credit-Score Distribution" [level=5] [ref=e133]
          - heading "Avg Loan Amount by Course" [level=5] [ref=e139]
          - heading "Applications by Acquisition Channel" [level=5] [ref=e145]
  - contentinfo [ref=e148]: Dhaniti Education Loan Dashboard · React + Bootstrap + FastAPI + SQLite · All records are synthetic. Do not treat as real customer or underwriting data.
```

# Test source

```ts
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
  69  |     ).toBeVisible({
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
> 118 |     await search.fill('Keerthi Reddy')
      |                  ^ Error: locator.fill: Test timeout of 30000ms exceeded.
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
  170 |     // Form should appear
  171 |     const inputs = page.locator(
  172 |       'input:visible, textarea:visible, select:visible'
  173 |     )
  174 | 
  175 |     const inputCount = await inputs.count()
  176 | 
  177 |     console.log(
  178 |       'Add Record form inputs:',
  179 |       inputCount
  180 |     )
  181 | 
  182 |     expect(inputCount).toBeGreaterThan(0)
  183 |   })
  184 | 
  185 | 
  186 |   // ==========================================
  187 |   // 7. READ / VIEW RECORD
  188 |   // ==========================================
  189 | 
  190 |   test('User can view an application', async ({ page }) => {
  191 | 
  192 |     // Find first row
  193 |     const firstRow = page.locator('tbody tr').first()
  194 | 
  195 |     await expect(firstRow).toBeVisible({
  196 |       timeout: 10000
  197 |     })
  198 | 
  199 |     // View button - first action button
  200 |     const viewButton = firstRow.getByRole('button').first()
  201 | 
  202 |     await expect(viewButton).toBeVisible()
  203 | 
  204 |     await viewButton.click()
  205 | 
  206 |     await page.waitForTimeout(500)
  207 | 
  208 |     // Verify something opened
  209 |     await expect(
  210 |       page.locator('body')
  211 |     ).not.toHaveText('')
  212 |   })
  213 | 
  214 | 
  215 |   // ==========================================
  216 |   // 8. EDIT RECORD
  217 |   // ==========================================
  218 | 
```