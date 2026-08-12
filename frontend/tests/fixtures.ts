// playwright-bdd wiring. Steps run through the @playwright/test runner (so you
// get UI mode, trace viewer, watch, etc.) while specs stay in Gherkin.
//
// These tests hit a *real* Django backend backed by a dedicated throwaway SQLite
// DB (see playwright.config.ts). The `resetState` fixture is `auto: true`, so the
// backend is wiped before every scenario — giving each one an isolated, clean DB.
import { test as base, createBdd } from 'playwright-bdd'

import { resetBackend } from './support/backend'

export const test = base.extend<{ resetState: void }>({
  resetState: [
    async ({ page }, use) => {
      await resetBackend(page)
      await use()
    },
    { auto: true },
  ],
})

export const { Given, When, Then } = createBdd(test)
