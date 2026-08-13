// Helpers that drive the real backend's test-support endpoints (/api/test/…,
// enabled by E2E_MODE). Requests go through the page's request context — which
// shares the browser's cookie jar — so `loginAs` establishes a session the
// subsequent page navigations will use.
import type { Page } from '@playwright/test'

// Password set on users created via loginAs / seedUser (when none is given).
// Must match DEFAULT_PASSWORD in backend/api/e2e_views.py.
export const E2E_PASSWORD = 'e2e-session-secret-8842'

async function post(page: Page, path: string, data: Record<string, unknown>) {
  const res = await page.request.post(path, { data })
  if (!res.ok()) {
    throw new Error(`POST ${path} → ${res.status()}: ${await res.text()}`)
  }
  return res
}

/** Wipe all users/items/sessions so a scenario starts from a clean slate. */
export const resetBackend = (page: Page) => post(page, '/api/test/reset/', {})

/** Create a user without logging in ("a registered user…"). */
export const seedUser = (page: Page, email: string, password: string) =>
  post(page, '/api/test/users/', { email, password })

// The email of the last user we logged in as, so item-seeding steps can default
// ownership to "the current user" without repeating the email in the feature.
let currentUser: string | null = null

/** Create the user if needed and start a session ("I am logged in as…"). */
export const loginAs = (page: Page, email: string) => {
  currentUser = email
  return post(page, '/api/test/login-as/', { email, password: E2E_PASSWORD })
}

/** Create an owner-scoped Item ("an item named X already exists"). Defaults the
 *  owner to the currently logged-in user; pass `owner` to seed someone else's. */
export const seedItem = (page: Page, name: string, owner?: string) => {
  const ownerEmail = owner ?? currentUser
  if (!ownerEmail) {
    throw new Error('seedItem: no owner given and no user is logged in')
  }
  return post(page, '/api/test/items/', { name, owner: ownerEmail })
}

/** Mint a real reset link (uid+token) so a test can open a valid one. */
export async function passwordResetLink(page: Page, email: string): Promise<string> {
  const res = await post(page, '/api/test/password-reset-token/', { email })
  const { uid, token } = (await res.json()) as { uid: string; token: string }
  return `/reset-password?uid=${uid}&token=${token}`
}
