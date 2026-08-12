"""URL configuration for the django-vue-base project."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("api.urls")),
]

# Test-support endpoints for the Playwright e2e suite. Gated behind E2E_MODE so
# they never exist in a normal deployment (see api/e2e_views.py).
if settings.E2E_MODE:
    urlpatterns += [path("api/test/", include("api.e2e_urls"))]
