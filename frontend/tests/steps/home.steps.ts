// Steps specific to the protected HomeView (health badge + items CRUD) and a
// couple of auth-flow helpers that need backend-seeded state.
import { expect } from '@playwright/test'

import { Given, When, Then } from '../fixtures'
import { E2E_PASSWORD, passwordResetLink, seedItem } from '../support/backend'

// The real backend is assumed reachable (Playwright waits for its health check
// before the suite starts), so this is a readability marker only.
Given('the backend health is {string}', async ({ page }, _status: string) => {
  void page
})

Given('an item named {string} already exists', async ({ page }, name: string) => {
  await seedItem(page, name)
})

// The account's current password is whatever loginAs set (E2E_PASSWORD), so
// steps don't have to hard-code that magic value in the .feature files.
When('I fill in my current password', async ({ page }) => {
  await page.getByTestId('account-old-password').fill(E2E_PASSWORD)
})

// Fetch a real uid+token for the user and open the reset link with them.
When('I open the password reset link for {string}', async ({ page }, email: string) => {
  await page.goto(await passwordResetLink(page, email))
})

Then('I should see {int} item(s)', async ({ page }, count: number) => {
  await expect(page.getByTestId('item')).toHaveCount(count)
})

Then('the item list should contain {string}', async ({ page }, name: string) => {
  await expect(page.getByTestId('item-list')).toContainText(name)
})
