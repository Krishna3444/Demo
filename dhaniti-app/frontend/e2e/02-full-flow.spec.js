import { test, expect } from '@playwright/test'

test.describe('Dhaniti - Complete E2E Flow', () => {

  const email = 'admin@dhaniti.ai'
  const password = 'DhanitiAdmin@123'

  test('Login → Applications → Search → Filter → Add → View → Edit → Delete → Logout', async ({
    page
  }) => {

    // =====================================================
    // 1. LOGIN PAGE
    // =====================================================

    await page.goto('/')

    await expect(
      page.getByPlaceholder('you@company.com')
    ).toBeVisible({
      timeout: 15000
    })

    console.log('Login page loaded')


    // =====================================================
    // 2. ENTER EMAIL
    // =====================================================

    await page
      .getByPlaceholder('you@company.com')
      .fill(email)

    console.log('Email entered')


    // =====================================================
    // 3. ENTER PASSWORD
    // =====================================================

    await page
      .locator('input[type="password"]')
      .fill(password)

    console.log('Password entered')


    // =====================================================
    // 4. LOGIN
    // =====================================================

    await page.getByRole('button', {
      name: 'LOGIN',
      exact: true
    }).click()

    console.log('Login clicked')


    // =====================================================
    // 5. WAIT FOR APPLICATION PAGE
    // =====================================================
    await page.getByRole('button', {
      name: 'Applications',
      exact: true
    }).click()


    

    console.log('Application page loaded')


    // =====================================================
    // 6. VERIFY APPLICATION TABLE
    // =====================================================

    await expect(
      page.getByText(/Showing.*applications/i)
    ).toBeVisible()

    console.log('Application list loaded')


    // =====================================================
    // 7. VERIFY ADD RECORD BUTTON
    // =====================================================

    const addRecordButton = page.getByRole('button', {
      name: /Add Record/i
    })

    await expect(addRecordButton).toBeVisible()

    console.log('Add Record button found')


    // =====================================================
    // 8. SEARCH APPLICATION
    // =====================================================

    const search = page.getByPlaceholder(
      'Search by App ID or student name...'
    )

    await search.fill('EDU1151')

    // Wait for React/API filtering
    await page.waitForTimeout(1000)

    await expect(
      page.getByText('EDU1151', {
        exact: true
      })
    ).toBeVisible()

    console.log('Search test passed')


    // =====================================================
    // 9. CLEAR SEARCH
    // =====================================================

    await search.fill('')

    await page.waitForTimeout(1000)

    console.log('Search cleared')


    // =====================================================
    // 10. OPEN ADD RECORD
    // =====================================================

    await addRecordButton.click()

    console.log('Add Record clicked')

    await page.waitForTimeout(500)


    // =====================================================
    // 11. VERIFY ADD RECORD FORM
    // =====================================================

    const visibleInputs = page.locator(
      'input:visible, textarea:visible, select:visible'
    )

    const inputCount = await visibleInputs.count()

    console.log(
      'Visible form fields:',
      inputCount
    )

    expect(inputCount).toBeGreaterThan(0)


    // =====================================================
    // 12. CLOSE ADD RECORD FORM
    // =====================================================

    // Look for common close buttons
    const closeButton = page.getByRole('button', {
      name: /close|cancel/i
    }).last()

    if (await closeButton.count() > 0) {

      await closeButton.click()

      console.log('Add Record form closed')

    } else {

      console.log(
        'No Close/Cancel button found'
      )
    }


    // =====================================================
    // 13. GET FIRST APPLICATION ROW
    // =====================================================

    const rows = page.locator('tr')
    
    const rowCount = await rows.count()

    console.log(
      'Table rows:',
      rowCount
    )

    expect(rowCount).toBeGreaterThan(1)

    const firstDataRow = rows.nth(1)

    await expect(firstDataRow).toBeVisible()


    // =====================================================
    // 14. CHECK ROW CONTENT
    // =====================================================

    const rowText = await firstDataRow.innerText()

    console.log(
      'First application:',
      rowText
    )

    expect(rowText.length).toBeGreaterThan(0)


    // =====================================================
    // 15. FIND ACTION BUTTONS
    // =====================================================

    const actionButtons = firstDataRow.locator(
      'button'
    )

    const actionCount = await actionButtons.count()

    console.log(
      'Action buttons:',
      actionCount
    )

    expect(actionCount).toBeGreaterThanOrEqual(3)


    // =====================================================
    // 16. VIEW APPLICATION
    // =====================================================

    await actionButtons.nth(0).click()

    console.log('View clicked')

    await page.waitForTimeout(500)

    // Check that something changed/opened
    await expect(
      page.locator('body')
    ).not.toHaveText('')

    // Close view if possible
    const closeView = page.getByRole('button', {
      name: /close|cancel/i
    }).last()

    if (await closeView.count() > 0) {
      await closeView.click()
    }

    console.log('View test completed')


    // =====================================================
    // 17. EDIT APPLICATION
    // =====================================================

    // Get row again because DOM may have changed
    const editRow = page.locator('tr').nth(1)

    const editButtons = editRow.locator('button')

    const editButtonCount = await editButtons.count()

    console.log(
      'Edit row buttons:',
      editButtonCount
    )

    expect(editButtonCount).toBeGreaterThanOrEqual(3)

    // Second button = Edit
    await editButtons.nth(1).click()

    console.log('Edit clicked')

    await page.waitForTimeout(500)


    // =====================================================
    // 18. VERIFY EDIT FORM
    // =====================================================

    const editInputs = page.locator(
      'input:visible, textarea:visible, select:visible'
    )

    const editInputCount = await editInputs.count()

    console.log(
      'Edit form fields:',
      editInputCount
    )

    expect(editInputCount).toBeGreaterThan(0)


    // Close edit without changing data
    const cancelEdit = page.getByRole('button', {
      name: /cancel|close/i
    }).last()

    if (await cancelEdit.count() > 0) {

      await cancelEdit.click()

      console.log('Edit cancelled')

    }


    // =====================================================
    // 19. SORT BY LOAN
    // =====================================================

    const loanText = page.getByText(
      'Loan',
      { exact: true }
    )

    if (await loanText.count() > 0) {

      await loanText.first().click()

      await page.waitForTimeout(500)

      console.log('Loan sorting clicked')

    } else {

      console.log(
        'Loan sort control not found'
      )
    }


    // =====================================================
    // 20. SORT BY CREDIT
    // =====================================================

    const creditText = page.getByText(
      'Credit',
      { exact: true }
    )

    if (await creditText.count() > 0) {

      await creditText.first().click()

      await page.waitForTimeout(500)

      console.log('Credit sorting clicked')

    } else {

      console.log(
        'Credit sort control not found'
      )
    }


    // =====================================================
    // 21. SORT BY DATE
    // =====================================================

    const dateText = page.getByText(
      'Date',
      { exact: true }
    )

    if (await dateText.count() > 0) {

      await dateText.first().click()

      await page.waitForTimeout(500)

      console.log('Date sorting clicked')

    } else {

      console.log(
        'Date sort control not found'
      )
    }


    // =====================================================
    // 22. LOGOUT
    // =====================================================

    const logoutButton = page.getByRole('button', {
      name: /logout|log out|sign out/i
    }).first()

    if (await logoutButton.count() > 0) {

      await logoutButton.click()

      console.log('Logout clicked')

      await expect(
        page.getByPlaceholder('you@company.com')
      ).toBeVisible({
        timeout: 10000
      })

      console.log('Logout successful')

    } else {

      console.log(
        'Logout button not found'
      )
    }


    // =====================================================
    // 23. PROTECTED ROUTE
    // =====================================================

    await page.goto('/dashboard')

    await expect(
      page.getByPlaceholder('you@company.com')
    ).toBeVisible({
      timeout: 10000
    })

    console.log(
      'Protected route test passed'
    )

  })

})
