"""
Django settings for the django-vue-base project.

Values are read from environment variables (see .env.example) via django-environ,
so the same settings file works for local development and production.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:5173", "http://127.0.0.1:5173"]),
    CSRF_TRUSTED_ORIGINS=(list, ["http://localhost:5173", "http://127.0.0.1:5173"]),
    FRONTEND_URL=(str, "http://localhost:5173"),
    EMAIL_BACKEND=(str, "django.core.mail.backends.console.EmailBackend"),
    DEFAULT_FROM_EMAIL=(str, "webmaster@localhost"),
    SESSION_COOKIE_SECURE=(bool, False),
    CSRF_COOKIE_SECURE=(bool, False),
    # Enables the /api/test/ support endpoints used by the Playwright e2e suite.
    # NEVER set this to True in production — the endpoints reset the DB and log in
    # as arbitrary users without authentication. See api/e2e_views.py.
    E2E_MODE=(bool, False),
)

# Read a .env file if present (never commit real secrets).
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-change-me-in-production-please-use-an-env-var",
)

DEBUG = env("DEBUG")

# Test-support endpoints (api/test/…) are wired up in config/urls.py only when
# this is on. Driven by the Playwright e2e run; must stay False in production.
E2E_MODE = env("E2E_MODE")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    # Local apps
    "accounts",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# Database
# Configured via the DATABASE_URL env var; defaults to local SQLite.
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    ),
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Secure by default: endpoints require authentication unless they opt out
    # with an explicit `permission_classes = [AllowAny]` (see accounts.views and
    # the health check).
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # OpenAPI schema generation (drf-spectacular).
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# drf-spectacular: metadata for the generated OpenAPI schema.
SPECTACULAR_SETTINGS = {
    "TITLE": "django-vue-base API",
    "DESCRIPTION": "API for the django-vue-base project.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}


# CORS (django-cors-headers) — allow the Vite dev server during development.
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
# Session-cookie auth needs the browser to send cookies on cross-origin XHR.
# (In dev the Vite proxy makes requests same-origin, but this keeps a
# cross-origin production frontend working too.)
CORS_ALLOW_CREDENTIALS = True


# Session & CSRF (session-cookie authentication)
# CSRF_TRUSTED_ORIGINS must list the frontend origin(s) so unsafe requests from
# the SPA are accepted. Cookies are marked Secure in production (set the two
# *_COOKIE_SECURE env vars to True behind HTTPS).
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")
# The SPA reads the CSRF cookie via JS to echo it back in the X-CSRFToken header,
# so it must not be HttpOnly.
CSRF_COOKIE_HTTPONLY = False


# Email (used by the password-reset flow). Defaults to the console backend, which
# prints emails to the terminal — configure a real SMTP backend in production.
EMAIL_BACKEND = env("EMAIL_BACKEND")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

# Base URL of the frontend, used to build links in emails (e.g. password reset).
FRONTEND_URL = env("FRONTEND_URL").rstrip("/")
