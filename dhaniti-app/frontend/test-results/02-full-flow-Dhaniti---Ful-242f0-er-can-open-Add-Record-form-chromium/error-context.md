# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 02-full-flow.spec.js >> Dhaniti - Full Application E2E Flow >> User can open Add Record form
- Location: e2e\02-full-flow.spec.js:158:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('button', { name: /add record/i })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByRole('button', { name: /add record/i })

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
> 164 |     await expect(addRecord).toBeVisible()
      |                             ^ Error: expect(locator).toBeVisible() failed
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
  219 |   test('User can edit an application', async ({ page }) => {
  220 | 
  221 |     const firstRow = page.locator('tbody tr').first()
  222 | 
  223 |     await expect(firstRow).toBeVisible()
  224 | 
  225 |     // Screenshot shows:
  226 |     // 1 = View
  227 |     // 2 = Edit
  228 |     // 3 = Delete
  229 | 
  230 |     const buttons = firstRow.getByRole('button')
  231 | 
  232 |     const buttonCount = await buttons.count()
  233 | 
  234 |     console.log(
  235 |       'Action buttons in first row:',
  236 |       buttonCount
  237 |     )
  238 | 
  239 |     expect(buttonCount).toBeGreaterThanOrEqual(2)
  240 | 
  241 |     // Edit = second button
  242 |     await buttons.nth(1).click()
  243 | 
  244 |     await page.waitForTimeout(500)
  245 | 
  246 |     // Verify edit form
  247 |     const inputs = page.locator(
  248 |       'input:visible, textarea:visible, select:visible'
  249 |     )
  250 | 
  251 |     await expect(
  252 |       inputs.first()
  253 |     ).toBeVisible({
  254 |       timeout: 5000
  255 |     })
  256 |   })
  257 | 
  258 | 
  259 |   // ==========================================
  260 |   // 9. DELETE RECORD
  261 |   // ==========================================
  262 | 
  263 |   test('User can delete an application', async ({ page }) => {
  264 | 
```