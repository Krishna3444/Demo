# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 02-full-flow.spec.js >> Dhaniti - Full Application E2E Flow >> User can edit an application
- Location: e2e\02-full-flow.spec.js:219:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('tbody tr').first()
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('tbody tr').first()

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
  219 |   test('User can edit an application', async ({ page }) => {
  220 | 
  221 |     const firstRow = page.locator('tbody tr').first()
  222 | 
> 223 |     await expect(firstRow).toBeVisible()
      |                            ^ Error: expect(locator).toBeVisible() failed
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
  265 |     const firstRow = page.locator('tbody tr').first()
  266 | 
  267 |     await expect(firstRow).toBeVisible()
  268 | 
  269 |     const buttons = firstRow.getByRole('button')
  270 | 
  271 |     const buttonCount = await buttons.count()
  272 | 
  273 |     expect(buttonCount).toBeGreaterThanOrEqual(3)
  274 | 
  275 |     // Delete = third button
  276 |     const deleteButton = buttons.nth(2)
  277 | 
  278 |     await expect(deleteButton).toBeVisible()
  279 | 
  280 |     // Handle browser confirmation
  281 |     page.once('dialog', async dialog => {
  282 |       await dialog.accept()
  283 |     })
  284 | 
  285 |     await deleteButton.click()
  286 | 
  287 |     await page.waitForTimeout(1000)
  288 |   })
  289 | 
  290 | 
  291 |   // ==========================================
  292 |   // 10. SORT BY LOAN
  293 |   // ==========================================
  294 | 
  295 |   test('User can sort applications by loan', async ({ page }) => {
  296 | 
  297 |     const loanButton = page.getByRole('button', {
  298 |       name: /loan/i
  299 |     })
  300 | 
  301 |     await expect(loanButton).toBeVisible()
  302 | 
  303 |     await loanButton.click()
  304 | 
  305 |     await page.waitForTimeout(500)
  306 | 
  307 |     await expect(loanButton).toBeVisible()
  308 |   })
  309 | 
  310 | 
  311 |   // ==========================================
  312 |   // 11. SORT BY CREDIT
  313 |   // ==========================================
  314 | 
  315 |   test('User can sort applications by credit', async ({ page }) => {
  316 | 
  317 |     const creditButton = page.getByRole('button', {
  318 |       name: /credit/i
  319 |     })
  320 | 
  321 |     await expect(creditButton).toBeVisible()
  322 | 
  323 |     await creditButton.click()
```