# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 02-full-flow.spec.js >> Dhaniti - Full Application E2E Flow >> Logged out user cannot access dashboard
- Location: e2e\02-full-flow.spec.js:412:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByPlaceholder('you@company.com')
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for getByPlaceholder('you@company.com')

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
  402 |     ).toBeVisible({
  403 |       timeout: 10000
  404 |     })
  405 |   })
  406 | 
  407 | 
  408 |   // ==========================================
  409 |   // 15. PROTECTED ROUTE
  410 |   // ==========================================
  411 | 
  412 |   test('Logged out user cannot access dashboard', async ({
  413 |     page
  414 |   }) => {
  415 | 
  416 |     const logoutButton = page.getByRole('button', {
  417 |       name: /logout|log out|sign out/i
  418 |     }).first()
  419 | 
  420 |     if (await logoutButton.count() > 0) {
  421 |       await logoutButton.click()
  422 |     }
  423 | 
  424 |     await page.waitForTimeout(500)
  425 | 
  426 |     await page.goto('/dashboard')
  427 | 
  428 |     await expect(
  429 |       page.getByPlaceholder('you@company.com')
> 430 |     ).toBeVisible({
      |       ^ Error: expect(locator).toBeVisible() failed
  431 |       timeout: 10000
  432 |     })
  433 |   })
  434 | 
  435 | })
  436 | 
```