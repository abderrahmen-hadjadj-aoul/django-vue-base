"""Test-support routes, mounted under /api/test/ only when settings.E2E_MODE."""
from django.urls import path

from .e2e_views import (
    LoginAsView,
    PasswordResetTokenView,
    ResetView,
    SeedItemView,
    SeedUserView,
)

urlpatterns = [
    path("reset/", ResetView.as_view(), name="e2e-reset"),
    path("users/", SeedUserView.as_view(), name="e2e-seed-user"),
    path("login-as/", LoginAsView.as_view(), name="e2e-login-as"),
    path("items/", SeedItemView.as_view(), name="e2e-seed-item"),
    path(
        "password-reset-token/",
        PasswordResetTokenView.as_view(),
        name="e2e-password-reset-token",
    ),
]
