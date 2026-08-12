# django-vue-base

Starter template for new projects using **Django + Django REST Framework** on
the backend and **Vue 3 (Vite)** on the frontend. Clone it to skip the initial
plumbing.

## Stack

| Layer     | Tech                                                     |
| --------- | -------------------------------------------------------- |
| Backend   | Django 5.2, Django REST Framework, django-cors-headers, django-environ |
| Frontend  | Vue 3, Vite 7                                            |
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
└── frontend/           # Vue 3 + Vite app
    ├── src/
    │   ├── api.js      # tiny fetch wrapper for the DRF API
    │   └── App.vue     # demo: health status + item list/create
    └── vite.config.js  # proxies /api -> Django during dev
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
