import { test, expect } from '@playwright/test'

test.describe('Direct Login Flow', () => {

  test('user can login with email and password', async ({ page }) => {

    // 1. Open Login page
    await page.goto('/')

    // 2. Verify Login button is visible
    await expect(
      page.getByRole('button', {
        name: 'LOGIN',
        exact: true
      })
    ).toBeVisible()

    // 3. Enter email
    await page
      .getByPlaceholder('you@company.com')
      .fill('analyst@dhaniti.ai')

    // 4. Enter password
    await page
      .locator('input[type="password"]')
      .fill('Analyst@123')

    // 5. Click LOGIN
    await page.getByRole('button', {
      name: 'LOGIN',
      exact: true
    }).click()

    // 6. Wait for navigation/API response
    await page.waitForTimeout(1000)

    // 7. Verify Dashboard
    await expect(
      page.getByText(/dashboard/i).first()
    ).toBeVisible({
      timeout: 10000
    })

    // 8. Optional: verify we are no longer on login page
    await expect(
      page.getByRole('button', {
        name: 'LOGIN',
        exact: true
      })
    ).not.toBeVisible()
  })
})
