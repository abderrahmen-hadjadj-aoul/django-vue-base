// Reusable steps for navigation and asserting on DOM nodes. Every element is
// addressed by its `data-testid` (via Playwright's getByTestId) so the specs
// don't break when copy or markup changes.
//
// Preconditions ("a registered user…", "I am logged in as…") are set up against
// the real backend through its /api/test/ endpoints (see support/backend.ts).
import { expect } from '@playwright/test'

import { Given, When, Then } from '../fixtures'
import { loginAs, seedUser } from '../support/backend'

// Human-friendly page names → routes, so features read naturally.
const PAGES: Record<string, string> = {
  home: '/',
  login: '/login',
  register: '/register',
  account: '/account',
  'forgot password': '/forgot-password',
  'reset password': '/reset-password',
}

function pathFor(name: string): string {
  const path = PAGES[name.toLowerCase()]
  if (!path) throw new Error(`Unknown page "${name}". Known: ${Object.keys(PAGES).join(', ')}`)
  return path
}

// A fresh browser context starts logged out, so this is just an explicit marker.
Given('I am not logged in', async ({ page }) => {
  void page
})

// Create the user and open a real session (sets the session cookie in the
// browser context) so the router guard lets protected pages through.
Given('I am logged in as {string}', async ({ page }, email: string) => {
  await loginAs(page, email)
})

Given(
  'a registered user with email {string} and password {string}',
  async ({ page }, email: string, password: string) => {
    await seedUser(page, email, password)
  },
)

When('I visit the {string} page', async ({ page }, name: string) => {
  await page.goto(pathFor(name))
})

// Raw path variant for URLs that carry query params (e.g. reset links).
When('I visit {string}', async ({ page }, path: string) => {
  await page.goto(path)
})

When('I fill in {string} with {string}', async ({ page }, testid: string, value: string) => {
  await page.getByTestId(testid).fill(value)
})

When('I click {string}', async ({ page }, testid: string) => {
  await page.getByTestId(testid).click()
})

Then('I should be on the {string} page', async ({ page }, name: string) => {
  await expect(page).toHaveURL(new RegExp(`${pathFor(name).replace('/', '\\/')}(\\?|$)`))
})

Then('I should see {string}', async ({ page }, testid: string) => {
  await expect(page.getByTestId(testid)).toBeVisible()
})

Then('I should not see {string}', async ({ page }, testid: string) => {
  await expect(page.getByTestId(testid)).toHaveCount(0)
})

Then('{string} should contain {string}', async ({ page }, testid: string, text: string) => {
  await expect(page.getByTestId(testid)).toContainText(text)
})
