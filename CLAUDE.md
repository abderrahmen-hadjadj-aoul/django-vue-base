# CLAUDE.md

## What this repo is

`django-vue-base` is a **reusable starter template**, not a product. Its goal is
to be cloned as the starting point for new projects so the initial plumbing
(Django + DRF backend, Vue 3 frontend, and a type-safe bridge between them) is
already done. Keep changes generic and template-worthy — avoid app-specific
features that a consumer of the template wouldn't want.

## Git workflow

- **Commit directly to `main` and push there** — no feature branches, no PRs for
  routine work. `main` is the single working branch; there is no `master`.

## Stack

- **Backend**: Django 5.2, Django REST Framework, drf-spectacular (OpenAPI),
  django-cors-headers, django-environ. SQLite by default (`DATABASE_URL` for
  anything else).
- **Frontend**: Vue 3 + Vite 7 + **TypeScript**, styled with **shadcn-vue**
  (Reka UI components) on **Tailwind CSS v4**.
- **API client**: a typed SDK generated from the backend's OpenAPI schema by
  `@hey-api/openapi-ts` (see below).
- **Package manager**: **pnpm only — never use npm/yarn.**

## Layout

```
backend/    Django project: config/ (settings, urls), api/ (example app),
            accounts/ (session-cookie auth: /api/auth/…)
            <app>/services.py  <- business logic (see "Business logic" below)
            openapi.json  <- exported schema, committed
frontend/   Vue 3 + Vite + TS + shadcn-vue (Reka UI) + Tailwind CSS v4
            src/api/generated/  <- generated SDK, committed, DO NOT hand-edit
            src/api/index.ts    <- client config: base URL, credentials, CSRF interceptor
            src/components/ui/   <- shadcn-vue components (owned, editable): button, input, card, label
            src/lib/utils.ts     <- cn() class-merge helper (clsx + tailwind-merge)
            components.json      <- shadcn-vue CLI config (for `add`)
            src/assets/main.css <- Tailwind entry + shadcn design tokens (:root/.dark, @theme inline)
            src/stores/auth.ts  <- reactive auth store (useAuth)
            src/router/         <- vue-router + auth route guard
            src/views/          <- HomeView (protected) + auth pages
            openapi-ts.config.ts
mprocs.yaml Runs both dev servers together
```

## Commands

Backend (from `backend/`, venv activated):
```bash
python3 -m venv .venv && source .venv/bin/activate   # first time
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver          # :8000
python manage.py test
```

Frontend (from `frontend/`):
```bash
pnpm install
pnpm dev            # :5173, proxies /api -> :8000
pnpm build          # vite build only (no type-check — see below)
pnpm type-check     # vue-tsc --noEmit; run this regularly, see below
```

Run both at once from the project root: `mprocs`. `mprocs` also runs a
`frontend-typecheck` proc (`pnpm type-check`) alongside the dev servers.

**Run `pnpm type-check` regularly to verify your work is correct.** The
production `pnpm build` no longer runs `vue-tsc` (type-checking was removed from
the live build so builds are fast and don't fail on type errors). That means
type errors won't surface at build time — so run `pnpm type-check` (from
`frontend/`) after changing any TypeScript/Vue code, and rely on the
`frontend-typecheck` proc in `mprocs` during development.

## The typed API client (important)

The frontend never hand-writes fetch calls; it imports generated functions from
`@/api` (e.g. `itemsList`, `itemsCreate`, `type Item`). This keeps the client in
lockstep with the backend and catches drift at compile time.

**Whenever you change the API (serializers, viewsets, routes), regenerate:**
```bash
cd backend  && python manage.py spectacular --format openapi-json --file openapi.json
cd frontend && pnpm generate:api
```
Both `backend/openapi.json` and `frontend/src/api/generated/` are committed on
purpose so a fresh clone builds without a running backend. Never edit files
under `src/api/generated/` by hand — they are overwritten.

New DRF endpoints should produce a clean schema. For non-serializer responses
(like the `health` view), add `@extend_schema(...)` so the generated types stay
accurate.

## Frontend E2E tests (Gherkin via playwright-bdd)

BDD-style browser tests live in `frontend/tests/`. Specs are Gherkin, but they
run through the **`@playwright/test` runner** via **`playwright-bdd`** (which
generates Playwright spec files from the `.feature` files). That's what gives us
Playwright **UI mode**, the trace viewer, parallel workers, etc. — plain
`@cucumber/cucumber` can't do those.

```
frontend/tests/features/     Gherkin .feature specs (login, register, home, …)
frontend/tests/steps/        step defs — createBdd() Given/When/Then, getByTestId-based
frontend/tests/fixtures.ts   playwright-bdd test + `resetState` fixture (auto, resets DB)
frontend/tests/support/backend.ts  helpers hitting the /api/test/ support endpoints
frontend/playwright.config.ts      defineBddConfig + the two webServers
frontend/.features-gen/      generated specs (git-ignored) — never edit
backend/api/e2e_views.py     the /api/test/ endpoints (gated behind E2E_MODE)
```

- Run: `pnpm test:e2e` (`bddgen && playwright test`, headless). Debug/iterate with
  `pnpm test:e2e:ui` → **Playwright UI mode**
  (https://playwright.dev/docs/test-ui-mode: watch, time-travel, pick locators).
  `pnpm test:e2e:report` opens the last HTML report. `mprocs` exposes `e2e` and
  `e2e-ui` as `autostart: false` procs you start on demand.
- **These tests hit the REAL Django API + DB — nothing is mocked.** Playwright's
  `webServer` starts two dedicated servers just for e2e, isolated from the dev
  stack: a Django backend on **:8001** against a throwaway **`backend/db.e2e.sqlite3`**
  (recreated + migrated each run) with `E2E_MODE=True`, and a Vite frontend on
  **:5273** that proxies `/api` → :8001 (via `VITE_API_PROXY_TARGET`). `baseURL`
  is `http://localhost:5273`.
- **Test-support endpoints** live in `backend/api/e2e_views.py` under `/api/test/`
  and are mounted **only when `E2E_MODE=True`** (see `config/urls.py`) — they never
  exist in a normal deployment. They reset the DB and seed users/items/sessions/
  reset-tokens for the harness. They set `authentication_classes = []` so DRF's
  `SessionAuthentication` doesn't CSRF-reject them once a session cookie exists.
  **Never set `E2E_MODE=True` in production** (unauthenticated + destructive).
- **Isolation:** real backend + one shared DB ⇒ `workers: 1` (serial) and the
  `resetState` fixture (`auto: true` in `tests/fixtures.ts`) wipes the DB before
  every scenario. Step preconditions call the support endpoints via
  `tests/support/backend.ts`: `seedUser` ("a registered user…"), `loginAs`
  ("I am logged in as…", sets the session cookie through `page.request`), `seedItem`,
  `passwordResetLink` (mints a real uid+token). `E2E_PASSWORD` there must match
  `DEFAULT_PASSWORD` in `e2e_views.py`.
- The e2e backend uses the **dummy email backend** (set in `playwright.config.ts`):
  the reset flow's first real email send otherwise blocks ~5s on `socket.getfqdn()`
  and races step timeouts. Tests read reset tokens via the support endpoint, not email.
- **Address DOM nodes by `data-testid`** (Playwright `getByTestId`), not text or
  CSS. Views carry testids for anything a test touches; add one when you add
  interactive markup. shadcn `Input`/`Button` forward `data-testid` (fallthrough
  attrs) to their root element.
- Steps read fixtures by destructuring: `Given('…', async ({ page }) => …)`.
  `createBdd()` must be built on `test` imported from **playwright-bdd** (extended
  in `tests/fixtures.ts`), not `@playwright/test`. Step fns must declare the
  fixtures arg first even if unused (playwright-bdd arity check).
- **Gotcha — Vite watcher vs generated/report files.** `bddgen` writes
  `.features-gen/` and Playwright writes `playwright-report/` / `test-results/`
  while the Vite server runs; if its watcher sees those writes it full-reloads the
  app mid-scenario and wipes state. `vite.config.ts` ignores all three in
  `server.watch.ignored`, and they're git-ignored.
- Browsers: `pnpm exec playwright install chromium` once after install. These
  endpoints don't appear in `openapi.json` (schema is generated with `E2E_MODE`
  off), so no client regeneration is needed for them.

## Authentication (session cookies)

- Auth lives in the `accounts` app under `/api/auth/…` (register, login, logout,
  me, password change, password reset request/confirm). It uses Django's session
  auth with CSRF — no tokens — because the SPA is first-party/same-origin.
- **Credentials are email + password; there is no username.** We keep Django's
  default User model but store the email in the `username` field too (see
  `RegisterSerializer.create`), so `authenticate()`/`login()` work unchanged and
  email uniqueness is enforced by username's unique constraint. Emails are
  normalized to lowercase on register and login (username matching is
  case-sensitive, emails are not). `username` is never exposed by the API — treat
  email as the sole identity. If you ever need a real username field, switch to a
  custom `AUTH_USER_MODEL` instead of undoing this.
- **DRF default permission is `IsAuthenticated`.** New endpoints are private by
  default; add `permission_classes = [AllowAny]` to opt out (as `health` and the
  auth views do). When you add a public endpoint, remember this.
- CSRF: the frontend calls `authCsrfRetrieve()` on startup, and the client
  interceptor in `src/api/index.ts` sends `credentials: 'include'` plus the
  `X-CSRFToken` header on unsafe methods. Don't hand-write fetch calls that skip
  this. Tests use `APIClient(enforce_csrf_checks=True)` to mirror the browser.
- Frontend state is `useAuth()` in `src/stores/auth.ts` (a reactive singleton,
  deliberately not Pinia to keep deps light). The router guard in `src/router/`
  calls `bootstrap()` once, then redirects unauthenticated users to `/login`.
- Password reset emails go through Django's email backend (console by default —
  see `EMAIL_BACKEND`); links are built from `FRONTEND_URL` and point at the
  `/reset-password?uid=…&token=…` route.
- After changing any auth serializer/view, regenerate the schema + client (same
  two-step flow as above) so the frontend stays typed.

## Business logic (service layer)

Complex business logic goes in a per-app **`services.py`** — plain functions
that hold domain rules and side effects (creating records, sending email,
calling external APIs, multi-step workflows in a `transaction.atomic()`). The
layering is **fat services, thin views, thin serializers**:

- **View**: parse the request, call one service function, map the result or a
  domain exception to an HTTP response. Nothing else.
- **Serializer**: validation and request/response shape only. Keep field-level
  rules here (they drive the OpenAPI schema), but don't put orchestration or
  side effects in them.
- **Service**: the actual business rules. Raises domain exceptions; the view
  translates them to responses. Testable directly, without HTTP/DRF plumbing.
- **Model**: only invariants intrinsic to one entity (a `@property`, `clean()`).
  Cross-model workflows belong in a service, not a fat model.

**Add a service only when logic actually appears — don't scaffold passthrough
services.** `accounts/services.py` is the reference example (user creation,
password-reset token minting/email, reset confirmation). The `api` app has
**no** service on purpose: `ItemViewSet` is stock `ModelViewSet` CRUD with no
custom logic, so a service there would just wrap the ORM and hide nothing. When
an app grows real rules, that's the moment to introduce its `services.py`.

## Backend tests (Django-style Gherkin)

Backend tests are plain `APITestCase` methods run by `manage.py test` — **no
pytest, no BDD framework, no `.feature` files** (that machinery is the
frontend's e2e suite only). We borrow only the Gherkin *vocabulary* to structure
each test, via a docstring and comment markers:

- **One test method = one scenario.** Its docstring is `"""Scenario: <name>."""`
- **Structure the body with uppercase `# GIVEN` / `# WHEN` / `# THEN` / `# AND`
  comments**, in that order, each on its own line above the code it introduces.
  `# GIVEN` = setup/preconditions, `# WHEN` = the action under test, `# THEN` =
  assertions, `# AND` = a follow-on step of the same kind. A method may repeat
  `# WHEN`/`# THEN` for a multi-step flow (e.g. login then logout).
- The keywords are **only comments** — nothing enforces them, so keep them
  honest: the code under a `# WHEN` should be the action, under a `# THEN` the
  assertions. When a step needs no code (a fresh test DB already satisfies a
  `# GIVEN`), keep the comment and note why.

```python
def test_login_logout(self) -> None:
    """Scenario: A registered user can log in and then out."""
    # GIVEN a registered user
    User.objects.create_user("carol@example.com", "carol@example.com", "s3cret-pass-99")
    # WHEN she logs in with the right credentials
    resp = self.client.post(reverse("login"), {...}, format="json", **self._csrf_headers())
    # THEN a session is established
    self.assertEqual(resp.status_code, status.HTTP_200_OK)
```

`accounts/tests.py` and `api/tests.py` are the reference examples. This keeps the
narrative benefit of Gherkin with zero tooling cost; if a suite ever outgrows it,
reach for the frontend's playwright-bdd pattern rather than adding pytest-bdd here.

## Conventions

- Backend settings are env-driven via django-environ; add new config as env vars
  with sane defaults, and document them in `backend/.env.example`. Never commit a
  real `.env` or secrets.
- Frontend is strict TypeScript. Configure the API base URL only in
  `src/api/index.ts` (via `VITE_API_BASE_URL`, empty in dev so the proxy works).

## Styling (shadcn-vue + Tailwind CSS v4)

- **UI components are shadcn-vue** — copy-in components (MIT) built on **Reka UI**
  and Tailwind. They live in `src/components/ui/` (`button`, `input`, `card`,
  `label`) and are **owned by this repo**, not `node_modules`: edit them freely.
  Import via `@/components/ui/button`, etc. Every component uses `cn()` from
  `@/lib/utils` to merge classes, so callers can pass a `class` prop.
- **Why not PrimeVue:** we evaluated it and backed out — **PrimeVue v5 ships a
  license check** that renders an "Invalid PrimeUI License" banner (v4 was MIT).
  shadcn-vue has no runtime library and no license.
- **Add components with the CLI:** `pnpm dlx shadcn-vue@latest add <name>`.
  Config lives in `components.json` (style `new-york`, base color `neutral`, CSS
  variables on). Don't reintroduce `primevue`/`@primeuix/*`.
- **Tailwind v4 is configured entirely in CSS — no `tailwind.config.js`, no
  PostCSS.** The `@tailwindcss/vite` plugin auto-detects classes.
  `src/assets/main.css` is the single entry: `@import 'tailwindcss'`, the shadcn
  design tokens as CSS variables under `:root` / `.dark`, and an `@theme inline`
  block mapping them to utilities (`bg-primary`, `text-muted-foreground`, …).
- **Rebrand by editing the oklch token values** in `:root` / `.dark` (e.g.
  `--primary`), not by hard-coding colors in templates. Dark mode is a `.dark`
  class on a root element (`@custom-variant dark`).
- **Style with utility classes in views.** View components carry no `<style>`
  blocks; keep it that way. `tw-animate-css` is imported for animation utilities.
- No build step to remember — Tailwind compiles through Vite for both `pnpm dev`
  and `pnpm build`.

## Gotchas (learned the hard way)

- **Python venvs are not relocatable.** If the repo moves, delete `.venv` and
  recreate it — `source .venv/bin/activate` silently no-ops with a stale path.
- **pnpm blocks esbuild's build script.** Approval lives in
  `frontend/pnpm-workspace.yaml` as `allowBuilds: { esbuild: true }` (the
  `onlyBuiltDependencies` key was NOT honored by the installed pnpm).
- **TypeScript is pinned to 5.x**, not the 7.x native port — vue-tsc/@hey-api
  aren't reliably compatible with TS 7 yet.
- `@hey-api/client-fetch` shows a deprecation warning but is what the current
  generator emits; it works. Revisit on a heyapi upgrade.
- Environment here runs Python 3.14 and Node via mise; Django 5.2 supports it.
