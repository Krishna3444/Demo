# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 02-full-flow.spec.js >> Dhaniti - Full Application E2E Flow >> User can create a record
- Location: e2e\02-full-flow.spec.js:83:3

# Error details

```
Error: locator.click: Test ended.
Call log:
  - waiting for getByText(/add|create/i).first()

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test'
  2   | 
  3   | test.describe('Dhaniti - Full Application E2E Flow', () => {
  4   | 
  5   |   
  6   | 
  7   |   test.beforeEach(async ({ page }) => {
  8   | 
  9   |     // ==============================
  10  |     // LOGIN
  11  |     // ==============================
  12  | 
  13  |     await page.goto('/')
  14  | 
  15  |     await expect(
  16  |       page.getByPlaceholder('you@company.com')
  17  |     ).toBeVisible()
  18  | 
  19  |     await page
  20  |       .getByPlaceholder('you@company.com')
  21  |       .fill('analyst@dhaniti.ai')
  22  | 
  23  |     await page
  24  |       .locator('input[type="password"]')
  25  |       .fill('Analyst@123')
  26  | 
  27  |     await page.getByRole('button', {
  28  |       name: 'LOGIN',
  29  |       exact: true
  30  |     }).click()
  31  | 
  32  |     // Wait for dashboard
  33  |     await expect(
  34  |       page.getByText(/dashboard/i).first()
  35  |     ).toBeVisible({
  36  |       timeout: 10000
  37  |     })
  38  |   })
  39  | 
  40  | 
  41  |   // ==========================================
  42  |   // 1. DASHBOARD
  43  |   // ==========================================
  44  | 
  45  |   test('Dashboard loads successfully', async ({ page }) => {
  46  | 
  47  |     await expect(
  48  |       page.getByText(/dashboard/i).first()
  49  |     ).toBeVisible()
  50  | 
  51  |     // Check that dashboard contains content
  52  |     await expect(
  53  |       page.locator('body')
  54  |     ).not.toHaveText('')
  55  |   })
  56  | 
  57  | 
  58  |   // ==========================================
  59  |   // 2. NAVIGATION
  60  |   // ==========================================
  61  | 
  62  |   test('User can navigate through application', async ({ page }) => {
  63  | 
  64  |     const links = page.getByRole('link')
  65  | 
  66  |     const linkCount = await links.count()
  67  | 
  68  |     console.log('Navigation links:', linkCount)
  69  | 
  70  |     expect(linkCount).toBeGreaterThan(0)
  71  | 
  72  |     // Check visible navigation
  73  |     await expect(
  74  |       page.getByText(/dashboard/i).first()
  75  |     ).toBeVisible()
  76  |   })
  77  | 
  78  | 
  79  |   // ==========================================
  80  |   // 3. CREATE
  81  |   // ==========================================
  82  | 
  83  |   test('User can create a record', async ({ page }) => {
  84  | 
  85  |     // Change this selector to your actual CRUD page
> 86  |     await page.getByText(/add|create/i).first().click()
      |                                                 ^ Error: locator.click: Test ended.
  87  | 
  88  |     // Fill form
  89  |     const inputs = page.locator('input:visible')
  90  | 
  91  |     const inputCount = await inputs.count()
  92  | 
  93  |     console.log('Create form inputs:', inputCount)
  94  | 
  95  |     expect(inputCount).toBeGreaterThan(0)
  96  | 
  97  |     // Example
  98  |     if (inputCount > 0) {
  99  |       await inputs.first().fill('E2E Test Record')
  100 |     }
  101 | 
  102 |     // Submit
  103 |     await page.getByRole('button', {
  104 |       name: /save|create|submit/i
  105 |     }).click()
  106 | 
  107 |     // Verify record appears
  108 |     await expect(
  109 |       page.getByText('E2E Test Record')
  110 |     ).toBeVisible({
  111 |       timeout: 10000
  112 |     })
  113 |   })
  114 | 
  115 | 
  116 |   // ==========================================
  117 |   // 4. READ
  118 |   // ==========================================
  119 | 
  120 |   test('User can view records', async ({ page }) => {
  121 | 
  122 |     // Verify records/table exists
  123 |     const tables = page.locator('table')
  124 | 
  125 |     if (await tables.count() > 0) {
  126 |       await expect(tables.first()).toBeVisible()
  127 |     }
  128 | 
  129 |     // Verify page has content
  130 |     await expect(
  131 |       page.locator('body')
  132 |     ).not.toHaveText('')
  133 |   })
  134 | 
  135 | 
  136 |   // ==========================================
  137 |   // 5. UPDATE
  138 |   // ==========================================
  139 | 
  140 |   test('User can update a record', async ({ page }) => {
  141 | 
  142 |     // Find Edit button
  143 |     const editButton = page.getByRole('button', {
  144 |       name: /edit/i
  145 |     }).first()
  146 | 
  147 |     if (await editButton.count() === 0) {
  148 |       test.skip(true, 'Edit button not available on this page')
  149 |     }
  150 | 
  151 |     await editButton.click()
  152 | 
  153 |     // Find visible input
  154 |     const input = page.locator('input:visible').last()
  155 | 
  156 |     await input.fill('E2E Updated Record')
  157 | 
  158 |     // Save
  159 |     await page.getByRole('button', {
  160 |       name: /save|update|submit/i
  161 |     }).click()
  162 | 
  163 |     // Verify update
  164 |     await expect(
  165 |       page.getByText('E2E Updated Record')
  166 |     ).toBeVisible({
  167 |       timeout: 10000
  168 |     })
  169 |   })
  170 | 
  171 | 
  172 |   // ==========================================
  173 |   // 6. DELETE
  174 |   // ==========================================
  175 | 
  176 |   test('User can delete a record', async ({ page }) => {
  177 | 
  178 |     const deleteButton = page.getByRole('button', {
  179 |       name: /delete/i
  180 |     }).first()
  181 | 
  182 |     if (await deleteButton.count() === 0) {
  183 |       test.skip(true, 'Delete button not available on this page')
  184 |     }
  185 | 
  186 |     await deleteButton.click()
```