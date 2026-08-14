"""
Django settings for the django-vue-base project.

Every value is read from an environment variable with **no default** — see
`config/env.py`, which loads `.env`, validates that every required variable is
defined, prints a startup report, and fails closed (raises) if any are missing.
Copy `.env.example` to `.env` and fill in every value.
"""

import sys
from pathlib import Path

from config.env import load_env

BASE_DIR = Path(__file__).resolve().parent.parent

# Load + validate all required environment variables. Prints a report to stderr
# and raises ImproperlyConfigured (listing every missing var) if any are absent.
ENV = load_env(BASE_DIR)

SECRET_KEY = ENV["SECRET_KEY"]

DEBUG = ENV["DEBUG"]

# Test-support endpoints (api/test/…) are wired up in config/urls.py only when
# this is on. Driven by the Playwright e2e run; must stay False in production.
E2E_MODE = ENV["E2E_MODE"]

ALLOWED_HOSTS = ENV["ALLOWED_HOSTS"]


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
    "audit",
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
# Configured via the required DATABASE_URL env var (e.g. sqlite:///db.sqlite3).
DATABASES = {
    "default": ENV["DATABASE_URL"],
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Test-only speedups. Only apply when running `manage.py test` — production
# keeps its secure/real defaults.
if "test" in sys.argv:
    # Swap Django's deliberately-slow default password hasher (PBKDF2, ~1M
    # iterations) for MD5. Auth tests hash/verify passwords on nearly every
    # case, so this cuts the suite's CPU time dramatically.
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    # Use the in-memory email backend so tests can read mail.outbox without a
    # network connection.
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    # Building any email's Message-ID header calls socket.getfqdn(), which can
    # block for seconds on machines whose hostname has no reverse-DNS entry
    # (that's the whole reason the reset test was slow). Prime Django's cached
    # DNS name so the lookup never runs during tests.
    from django.core.mail import message as _mail_message

    _mail_message.DNS_NAME._fqdn = "localhost"


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
CORS_ALLOWED_ORIGINS = ENV["CORS_ALLOWED_ORIGINS"]
# Session-cookie auth needs the browser to send cookies on cross-origin XHR.
# (In dev the Vite proxy makes requests same-origin, but this keeps a
# cross-origin production frontend working too.)
CORS_ALLOW_CREDENTIALS = True


# Session & CSRF (session-cookie authentication)
# CSRF_TRUSTED_ORIGINS must list the frontend origin(s) so unsafe requests from
# the SPA are accepted. Cookies are marked Secure in production (set the two
# *_COOKIE_SECURE env vars to True behind HTTPS).
CSRF_TRUSTED_ORIGINS = ENV["CSRF_TRUSTED_ORIGINS"]
SESSION_COOKIE_SECURE = ENV["SESSION_COOKIE_SECURE"]
CSRF_COOKIE_SECURE = ENV["CSRF_COOKIE_SECURE"]
# The SPA reads the CSRF cookie via JS to echo it back in the X-CSRFToken header,
# so it must not be HttpOnly.
CSRF_COOKIE_HTTPONLY = False


# Email (used by the password-reset flow). Use the console backend
# (django.core.mail.backends.console.EmailBackend) in dev to print emails to the
# terminal; configure a real SMTP backend in production.
EMAIL_BACKEND = ENV["EMAIL_BACKEND"]
DEFAULT_FROM_EMAIL = ENV["DEFAULT_FROM_EMAIL"]

# Base URL of the frontend, used to build links in emails (e.g. password reset).
FRONTEND_URL = ENV["FRONTEND_URL"].rstrip("/")


# Audit logging (see the `audit` app). Every view records one AuditLog row per
# request — any method, including GET — via the write-ahead pair
# `audit.services.begin_request` (before the action) and `finalize_request`
# (after, in the action's transaction). Each caller builds the audit body itself,
# including only the fields that are safe to log; the service stores it verbatim.
AUDIT_LOG_ENABLED = ENV["AUDIT_LOG_ENABLED"]
# Bodies larger than this (bytes) are noted but not stored, to bound row size.
AUDIT_MAX_BODY_BYTES = ENV["AUDIT_MAX_BODY_BYTES"]
