import { defineConfig, devices } from '@playwright/test'
import { defineBddConfig } from 'playwright-bdd'

// Generate Playwright spec files from the Gherkin features + step definitions.
const testDir = defineBddConfig({
  features: 'tests/features/**/*.feature',
  steps: ['tests/fixtures.ts', 'tests/steps/**/*.ts'],
})

// Dedicated ports for e2e so the suite never collides with (or talks to) the
// normal dev stack (frontend :5173 → backend :8000, dev DB).
const FRONTEND_PORT = 5273
const BACKEND_PORT = 8001
const BASE_URL = `http://localhost:${FRONTEND_PORT}`
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`
const E2E_ORIGINS = `${BASE_URL},http://127.0.0.1:${FRONTEND_PORT}`

export default defineConfig({
  testDir,
  // Real backend + one shared SQLite DB → run serially and reset the DB before
  // each scenario (see tests/fixtures.ts) so tests stay isolated.
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: 'html',
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      // Fresh throwaway SQLite DB + migrations, then a real Django server with
      // the /api/test/ support endpoints enabled (E2E_MODE).
      command:
        'rm -f db.e2e.sqlite3 && .venv/bin/python manage.py migrate --no-input && ' +
        `.venv/bin/python manage.py runserver 127.0.0.1:${BACKEND_PORT}`,
      cwd: '../backend',
      url: `${BACKEND_URL}/api/health/`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        DATABASE_URL: 'sqlite:///db.e2e.sqlite3',
        E2E_MODE: 'True',
        DEBUG: 'True',
        CSRF_TRUSTED_ORIGINS: E2E_ORIGINS,
        CORS_ALLOWED_ORIGINS: E2E_ORIGINS,
        FRONTEND_URL: BASE_URL,
        // The reset flow "sends" an email; the dummy backend discards it. This
        // also avoids the ~5s one-time socket.getfqdn() the console backend does
        // when it builds the first message (which would race step timeouts). The
        // suite reads reset tokens via /api/test/password-reset-token/ instead.
        EMAIL_BACKEND: 'django.core.mail.backends.dummy.EmailBackend',
      },
    },
    {
      // Vite dev server for the e2e run, proxying /api to the e2e backend.
      command: `pnpm dev --port ${FRONTEND_PORT} --strictPort`,
      url: BASE_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: { VITE_API_PROXY_TARGET: BACKEND_URL },
    },
  ],
})
