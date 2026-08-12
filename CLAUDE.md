# CLAUDE.md

## What this repo is

`django-vue-base` is a **reusable starter template**, not a product. Its goal is
to be cloned as the starting point for new projects so the initial plumbing
(Django + DRF backend, Vue 3 frontend, and a type-safe bridge between them) is
already done. Keep changes generic and template-worthy — avoid app-specific
features that a consumer of the template wouldn't want.

## Stack

- **Backend**: Django 5.2, Django REST Framework, drf-spectacular (OpenAPI),
  django-cors-headers, django-environ. SQLite by default (`DATABASE_URL` for
  anything else).
- **Frontend**: Vue 3 + Vite 7 + **TypeScript**.
- **API client**: a typed SDK generated from the backend's OpenAPI schema by
  `@hey-api/openapi-ts` (see below).
- **Package manager**: **pnpm only — never use npm/yarn.**

## Layout

```
backend/    Django project: config/ (settings, urls), api/ (example app),
            accounts/ (session-cookie auth: /api/auth/…)
            openapi.json  <- exported schema, committed
frontend/   Vue 3 + Vite + TS
            src/api/generated/  <- generated SDK, committed, DO NOT hand-edit
            src/api/index.ts    <- client config: base URL, credentials, CSRF interceptor
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
pnpm build          # runs vue-tsc type-check, then vite build
pnpm type-check
```

Run both at once from the project root: `mprocs`.

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

## Conventions

- Backend settings are env-driven via django-environ; add new config as env vars
  with sane defaults, and document them in `backend/.env.example`. Never commit a
  real `.env` or secrets.
- Frontend is strict TypeScript. Configure the API base URL only in
  `src/api/index.ts` (via `VITE_API_BASE_URL`, empty in dev so the proxy works).

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
