# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 02-full-flow.spec.js >> Dhaniti - Full Application E2E Flow >> User can sort applications by loan
- Location: e2e\02-full-flow.spec.js:295:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('button', { name: /loan/i })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByRole('button', { name: /loan/i })

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
- alert:
  - strong: Success
  - text: Login successful. Welcome back!
  - button "Close"
```

# Test source

```ts
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
> 301 |     await expect(loanButton).toBeVisible()
      |                              ^ Error: expect(locator).toBeVisible() failed
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
  324 | 
  325 |     await page.waitForTimeout(500)
  326 |   })
  327 | 
  328 | 
  329 |   // ==========================================
  330 |   // 12. SORT BY DATE
  331 |   // ==========================================
  332 | 
  333 |   test('User can sort applications by date', async ({ page }) => {
  334 | 
  335 |     const dateButton = page.getByRole('button', {
  336 |       name: /date/i
  337 |     })
  338 | 
  339 |     await expect(dateButton).toBeVisible()
  340 | 
  341 |     await dateButton.click()
  342 | 
  343 |     await page.waitForTimeout(500)
  344 |   })
  345 | 
  346 | 
  347 |   // ==========================================
  348 |   // 13. PAGINATION
  349 |   // ==========================================
  350 | 
  351 |   test('User can navigate application pages', async ({ page }) => {
  352 | 
  353 |     const nextButton = page.getByRole('button', {
  354 |       name: /next/i
  355 |     })
  356 | 
  357 |     if (await nextButton.count() === 0) {
  358 |       console.log(
  359 |         'Next page button not available.'
  360 |       )
  361 | 
  362 |       test.skip(
  363 |         true,
  364 |         'Pagination button not found'
  365 |       )
  366 | 
  367 |       return
  368 |     }
  369 | 
  370 |     await expect(nextButton).toBeVisible()
  371 | 
  372 |     await nextButton.click()
  373 | 
  374 |     await page.waitForTimeout(500)
  375 |   })
  376 | 
  377 | 
  378 |   // ==========================================
  379 |   // 14. LOGOUT
  380 |   // ==========================================
  381 | 
  382 |   test('User can logout', async ({ page }) => {
  383 | 
  384 |     const logoutButton = page.getByRole('button', {
  385 |       name: /logout|log out|sign out/i
  386 |     }).first()
  387 | 
  388 |     if (await logoutButton.count() === 0) {
  389 | 
  390 |       test.skip(
  391 |         true,
  392 |         'Logout button not found'
  393 |       )
  394 | 
  395 |       return
  396 |     }
  397 | 
  398 |     await logoutButton.click()
  399 | 
  400 |     await expect(
  401 |       page.getByPlaceholder('you@company.com')
```