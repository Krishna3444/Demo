# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 02-full-flow.spec.js >> Dhaniti - Complete E2E Flow >> Login → Applications → Search → Filter → Add → View → Edit → Delete → Logout
- Location: e2e\02-full-flow.spec.js:8:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: 'Applications', exact: true })

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
          - generic [ref=e18]: Admin
          - generic [ref=e19]: Lead
          - generic "Lead" [ref=e20]: L
          - button "Logout" [ref=e21] [cursor=pointer]:
            - generic [ref=e22]: 
            - text: Logout
  - main [ref=e23]:
    - generic [ref=e25]:
      - generic [ref=e26]:
        - heading "Welcome, Lead" [level=4] [ref=e27]
        - paragraph [ref=e28]: Here is what is happening with the education-loan portfolio today.
      - link "Manage applications" [ref=e29] [cursor=pointer]:
        - /url: /applications
        - generic [ref=e30]: 
        - text: Manage applications
    - list [ref=e31]:
      - listitem [ref=e32]:
        - button "Overview" [ref=e33] [cursor=pointer]
      - listitem [ref=e34]:
        - button "Applications 151" [ref=e35] [cursor=pointer]:
          - text: Applications
          - generic [ref=e36]: "151"
      - listitem [ref=e37]:
        - button "Insights 5" [ref=e38] [cursor=pointer]:
          - text: Insights
          - generic [ref=e39]: "5"
      - listitem [ref=e40]:
        - button "Data Quality 8" [ref=e41] [cursor=pointer]:
          - text: Data Quality
          - generic [ref=e42]: "8"
    - generic [ref=e43]:
      - generic [ref=e44]:
        - generic [ref=e45]:
          - text: Key Metrics
          - generic [ref=e46]: "151"
        - generic [ref=e48]:
          - generic [ref=e51]:
            - generic [ref=e52]: Total Applications
            - generic [ref=e53]: "151"
            - generic [ref=e54]: All records in dataset
          - generic [ref=e57]:
            - generic [ref=e58]: Approved
            - generic [ref=e59]: "71"
            - generic [ref=e60]: 47% approval rate
          - generic [ref=e63]:
            - generic [ref=e64]: Under Review
            - generic [ref=e65]: "50"
            - generic [ref=e66]: Active in pipeline
          - generic [ref=e69]:
            - generic [ref=e70]: Rejected
            - generic [ref=e71]: "15"
            - generic [ref=e72]: Declined by rule
          - generic [ref=e75]:
            - generic [ref=e76]: Submitted
            - generic [ref=e77]: "15"
            - generic [ref=e78]: Awaiting first review
          - generic [ref=e81]:
            - generic [ref=e82]: Total Loan Requested
            - generic [ref=e83]: ₹7.54 Cr
            - generic [ref=e84]: Sum of loan_amount_requested_inr
          - generic [ref=e87]:
            - generic [ref=e88]: Avg Loan Amount
            - generic [ref=e89]: ₹5.00 L
            - generic [ref=e90]: Per application
          - generic [ref=e93]:
            - generic [ref=e94]: Avg Credit Score
            - generic [ref=e95]: "696"
            - generic [ref=e96]: Excludes missing
      - generic [ref=e97]:
        - generic [ref=e98]: Distribution Charts
        - generic [ref=e100]:
          - heading "Applications by Status" [level=5] [ref=e104]
          - heading "Applications by Course Domain" [level=5] [ref=e110]
          - heading "Applications by Course" [level=5] [ref=e116]
          - heading "Applications by Institution" [level=5] [ref=e122]
          - heading "Monthly Trend (Stacked by Status)" [level=5] [ref=e128]
          - heading "Credit-Score Distribution" [level=5] [ref=e134]
          - heading "Avg Loan Amount by Course" [level=5] [ref=e140]
          - heading "Applications by Acquisition Channel" [level=5] [ref=e146]
  - contentinfo [ref=e149]: Dhaniti Education Loan Dashboard · React + Bootstrap + FastAPI + SQLite · All records are synthetic. Do not treat as real customer or underwriting data.
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test'
  2   | 
  3   | test.describe('Dhaniti - Complete E2E Flow', () => {
  4   | 
  5   |   const email = 'admin@dhaniti.ai'
  6   |   const password = 'DhanitiAdmin@123'
  7   | 
  8   |   test('Login → Applications → Search → Filter → Add → View → Edit → Delete → Logout', async ({
  9   |     page
  10  |   }) => {
  11  | 
  12  |     // =====================================================
  13  |     // 1. LOGIN PAGE
  14  |     // =====================================================
  15  | 
  16  |     await page.goto('/')
  17  | 
  18  |     await expect(
  19  |       page.getByPlaceholder('you@company.com')
  20  |     ).toBeVisible({
  21  |       timeout: 15000
  22  |     })
  23  | 
  24  |     console.log('Login page loaded')
  25  | 
  26  | 
  27  |     // =====================================================
  28  |     // 2. ENTER EMAIL
  29  |     // =====================================================
  30  | 
  31  |     await page
  32  |       .getByPlaceholder('you@company.com')
  33  |       .fill(email)
  34  | 
  35  |     console.log('Email entered')
  36  | 
  37  | 
  38  |     // =====================================================
  39  |     // 3. ENTER PASSWORD
  40  |     // =====================================================
  41  | 
  42  |     await page
  43  |       .locator('input[type="password"]')
  44  |       .fill(password)
  45  | 
  46  |     console.log('Password entered')
  47  | 
  48  | 
  49  |     // =====================================================
  50  |     // 4. LOGIN
  51  |     // =====================================================
  52  | 
  53  |     await page.getByRole('button', {
  54  |       name: 'LOGIN',
  55  |       exact: true
  56  |     }).click()
  57  | 
  58  |     console.log('Login clicked')
  59  | 
  60  | 
  61  |     // =====================================================
  62  |     // 5. WAIT FOR APPLICATION PAGE
  63  |     // =====================================================
  64  |     await page.getByRole('button', {
  65  |       name: 'Applications',
  66  |       exact: true
> 67  |     }).click()
      |        ^ Error: locator.click: Test timeout of 30000ms exceeded.
  68  | 
  69  | 
  70  |     
  71  | 
  72  |     console.log('Application page loaded')
  73  | 
  74  | 
  75  |     // =====================================================
  76  |     // 6. VERIFY APPLICATION TABLE
  77  |     // =====================================================
  78  | 
  79  |     await expect(
  80  |       page.getByText(/Showing.*applications/i)
  81  |     ).toBeVisible()
  82  | 
  83  |     console.log('Application list loaded')
  84  | 
  85  | 
  86  |     // =====================================================
  87  |     // 7. VERIFY ADD RECORD BUTTON
  88  |     // =====================================================
  89  | 
  90  |     const addRecordButton = page.getByRole('button', {
  91  |       name: /Add Record/i
  92  |     })
  93  | 
  94  |     await expect(addRecordButton).toBeVisible()
  95  | 
  96  |     console.log('Add Record button found')
  97  | 
  98  | 
  99  |     // =====================================================
  100 |     // 8. SEARCH APPLICATION
  101 |     // =====================================================
  102 | 
  103 |     const search = page.getByPlaceholder(
  104 |       'Search by App ID or student name...'
  105 |     )
  106 | 
  107 |     await search.fill('EDU1151')
  108 | 
  109 |     // Wait for React/API filtering
  110 |     await page.waitForTimeout(1000)
  111 | 
  112 |     await expect(
  113 |       page.getByText('EDU1151', {
  114 |         exact: true
  115 |       })
  116 |     ).toBeVisible()
  117 | 
  118 |     console.log('Search test passed')
  119 | 
  120 | 
  121 |     // =====================================================
  122 |     // 9. CLEAR SEARCH
  123 |     // =====================================================
  124 | 
  125 |     await search.fill('')
  126 | 
  127 |     await page.waitForTimeout(1000)
  128 | 
  129 |     console.log('Search cleared')
  130 | 
  131 | 
  132 |     // =====================================================
  133 |     // 10. OPEN ADD RECORD
  134 |     // =====================================================
  135 | 
  136 |     await addRecordButton.click()
  137 | 
  138 |     console.log('Add Record clicked')
  139 | 
  140 |     await page.waitForTimeout(500)
  141 | 
  142 | 
  143 |     // =====================================================
  144 |     // 11. VERIFY ADD RECORD FORM
  145 |     // =====================================================
  146 | 
  147 |     const visibleInputs = page.locator(
  148 |       'input:visible, textarea:visible, select:visible'
  149 |     )
  150 | 
  151 |     const inputCount = await visibleInputs.count()
  152 | 
  153 |     console.log(
  154 |       'Visible form fields:',
  155 |       inputCount
  156 |     )
  157 | 
  158 |     expect(inputCount).toBeGreaterThan(0)
  159 | 
  160 | 
  161 |     // =====================================================
  162 |     // 12. CLOSE ADD RECORD FORM
  163 |     // =====================================================
  164 | 
  165 |     // Look for common close buttons
  166 |     const closeButton = page.getByRole('button', {
  167 |       name: /close|cancel/i
```