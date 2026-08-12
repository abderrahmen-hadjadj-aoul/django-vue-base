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
- **Frontend**: Vue 3 + Vite 7 + **TypeScript**, styled with **shadcn-vue**
  (Reka UI components) on **Tailwind CSS v4**.
- **API client**: a typed SDK generated from the backend's OpenAPI schema by
  `@hey-api/openapi-ts` (see below).
- **Package manager**: **pnpm only — never use npm/yarn.**

## Layout

```
backend/    Django project: config/ (settings, urls), api/ (example app),
            accounts/ (session-cookie auth: /api/auth/…)
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
