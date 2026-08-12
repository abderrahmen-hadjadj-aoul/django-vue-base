# django-vue-base

Starter template for new projects using **Django + Django REST Framework** on
the backend and **Vue 3 (Vite)** on the frontend. Clone it to skip the initial
plumbing.

## Stack

| Layer     | Tech                                                     |
| --------- | -------------------------------------------------------- |
| Backend   | Django 5.2, Django REST Framework, drf-spectacular, django-cors-headers, django-environ |
| Frontend  | Vue 3, Vite 7, **TypeScript**, Tailwind CSS v4           |
| API client | Typed SDK generated from the OpenAPI schema by [@hey-api/openapi-ts](https://heyapi.dev) |
| Package manager (frontend) | **pnpm** (do not use npm)              |
| Database  | SQLite by default, any `DATABASE_URL` supported          |

## Layout

```
django-vue-base/
├── backend/            # Django project
│   ├── config/         # settings, urls, wsgi/asgi
│   ├── api/            # example app: health check + Item CRUD
│   ├── requirements.txt
│   └── .env.example
└── frontend/           # Vue 3 + Vite + TypeScript app
    ├── src/
    │   ├── api/
    │   │   ├── generated/  # typed SDK generated from the schema (do not edit)
    │   │   └── index.ts    # configures the client base URL, re-exports the SDK
    │   ├── assets/main.css # Tailwind entry: @import + @theme tokens + shared classes
    │   ├── App.vue         # demo: health status + item list/create
    │   └── main.ts
    ├── openapi-ts.config.ts  # @hey-api generator config
    └── vite.config.ts        # Tailwind + Vue plugins; proxies /api -> Django in dev
```

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit SECRET_KEY etc.
python manage.py migrate
python manage.py runserver    # http://127.0.0.1:8000
```

Example endpoints:

- `GET  /api/health/` → `{"status": "ok"}` (public)
- `GET/POST /api/items/`, `GET/PUT/PATCH/DELETE /api/items/{id}/` (**auth required**)
- Auth (`/api/auth/`): `csrf/`, `register/`, `login/`, `logout/`, `me/`,
  `password/change/`, `password/reset/`, `password/reset/confirm/`
- `GET  /api/schema/` → OpenAPI schema · `/api/docs/` → Swagger UI
- `/admin/` (run `python manage.py createsuperuser` first)

## Frontend setup

```bash
cd frontend
pnpm install
pnpm dev        # http://localhost:5173
```

`pnpm dev` proxies any `/api/*` request to Django at `http://127.0.0.1:8000`,
so run the backend alongside it. For production builds:

```bash
pnpm build      # outputs to frontend/dist/
pnpm preview
```

Set `VITE_API_BASE_URL` at build time if the API is served from a different
origin in production.

## Styling (Tailwind CSS v4)

The frontend is styled with **Tailwind CSS v4**, wired in through the
`@tailwindcss/vite` plugin — so it compiles automatically during `pnpm dev` and
`pnpm build` with no extra step. Tailwind v4 is configured **entirely in CSS**:
there is no `tailwind.config.js` and no PostCSS setup.

Everything lives in `frontend/src/assets/main.css`:

```css
@import 'tailwindcss';

@theme {
  --color-brand: #42b883; /* → bg-brand, text-brand, border-brand, … */
}

@layer components {
  .input { @apply w-full rounded-md border … ; }  /* shared form primitives */
  .btn   { @apply … ; }
}
```

- **Style components with utility classes** directly in the templates — there are
  no `<style>` blocks.
- **Rebrand by editing the `@theme` token** (`--color-brand`), not by hard-coding
  hex values; it regenerates the `*-brand` utilities everywhere.
- Add a class to `@layer components` only when a pattern genuinely repeats
  (as `.input`/`.btn` do for the auth forms); otherwise prefer raw utilities.

## Typed API client

The frontend talks to Django through a **typed SDK generated from the backend's
OpenAPI schema**, so the client always matches the API and mismatches surface at
compile time. Usage:

```ts
import { itemsList, itemsCreate, type Item } from '@/api'

const { data, error } = await itemsList()      // data: PaginatedItemList
await itemsCreate({ body: { name: 'Widget' } }) // body is type-checked
```

Regenerate whenever the API changes — two steps:

```bash
# 1) export the schema from Django (writes backend/openapi.json)
cd backend && python manage.py spectacular --format openapi-json --file openapi.json

# 2) regenerate the TypeScript client from it
cd ../frontend && pnpm generate:api
```

Both `backend/openapi.json` and `frontend/src/api/generated/` are committed so a
fresh clone builds without running the backend. The base URL is configured once
in `src/api/index.ts` (from `VITE_API_BASE_URL`, empty by default so the dev
proxy handles it).

## Authentication

The template ships with **session-cookie authentication** (Django sessions +
CSRF), which is the natural fit for a first-party SPA served from the same
origin as the API. DRF defaults to `IsAuthenticated`, so **new endpoints are
private unless they opt out** with `permission_classes = [AllowAny]` (see the
`health` view and the auth endpoints).

Backend pieces live in the `accounts` app (`/api/auth/…`): register, login,
logout, current-user (`me`), password change, and a password reset flow (request
+ confirm). Password-reset emails use the console backend by default (printed to
the terminal); configure `EMAIL_BACKEND`/SMTP for production.

**Credentials are email + password — there is no username.** The template keeps
Django's default User model but stores the (lowercased) email in the `username`
field as well, so Django's built-in auth works and the email stays unique. If a
project needs a separate username, swap in a custom `AUTH_USER_MODEL`.

How the cookie flow works:

1. The SPA calls `GET /api/auth/csrf/` once on startup to receive the readable
   `csrftoken` cookie.
2. The API client sends credentials on every request and echoes the token back
   in the `X-CSRFToken` header on unsafe methods (configured once in
   `frontend/src/api/index.ts`).
3. `login`/`register` start a session; `logout` ends it.

Frontend integration uses **vue-router** with a route guard plus a small auth
store:

```
frontend/src/
├── stores/auth.ts   # reactive user state + login/register/logout/... actions
├── router/index.ts  # routes + guard (redirects to /login when unauthenticated)
└── views/           # HomeView (protected) + Login/Register/Forgot/Reset/Account
```

New env vars (see `backend/.env.example`): `CSRF_TRUSTED_ORIGINS`,
`FRONTEND_URL`, `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`, `SESSION_COOKIE_SECURE`,
`CSRF_COOKIE_SECURE`.

## Typical workflow

Run both servers in two terminals (backend on `:8000`, frontend on `:5173`),
then open http://localhost:5173. The demo page shows the backend health badge
and lets you create/list `Item` records through the API.

Or start both at once with [mprocs](https://github.com/pvolok/mprocs) from the
project root (config in `mprocs.yaml`):

```bash
mprocs
```

## Renaming for a new project

- Rename the `api` app (or add your own apps) and update `INSTALLED_APPS`.
- Update `name` in `frontend/package.json`.
- Generate a fresh `SECRET_KEY` and keep it in `.env` (never commit it).
