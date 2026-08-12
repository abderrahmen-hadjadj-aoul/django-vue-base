# django-vue-base

Starter template for new projects using **Django + Django REST Framework** on
the backend and **Vue 3 (Vite)** on the frontend. Clone it to skip the initial
plumbing.

## Stack

| Layer     | Tech                                                     |
| --------- | -------------------------------------------------------- |
| Backend   | Django 5.2, Django REST Framework, drf-spectacular, django-cors-headers, django-environ |
| Frontend  | Vue 3, Vite 7, **TypeScript**                            |
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
    │   ├── App.vue         # demo: health status + item list/create
    │   └── main.ts
    ├── openapi-ts.config.ts  # @hey-api generator config
    └── vite.config.ts        # proxies /api -> Django during dev
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

- `GET  /api/health/` → `{"status": "ok"}`
- `GET/POST /api/items/`, `GET/PUT/PATCH/DELETE /api/items/{id}/`
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
