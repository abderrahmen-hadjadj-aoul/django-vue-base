"""Test-support endpoints for the Playwright e2e suite.

These are mounted ONLY when ``settings.E2E_MODE`` is True (see config/urls.py),
so they do not exist in a normal/production deployment. They let the browser
tests drive a *real* backend against a dedicated throwaway SQLite database:
reset all data, seed users/items, establish a session, and mint a valid
password-reset token.

Every view is ``AllowAny`` and CSRF-exempt because the test harness calls them
directly (not through the SPA's cookie/CSRF flow). This is obviously unsafe for
production — which is exactly why the whole module is gated behind E2E_MODE.
"""
from django.contrib.auth import get_user_model, login
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Item

User = get_user_model()

# Default password set on users created via /login-as/ (and seeded users that
# omit one). Kept in sync with E2E_PASSWORD in frontend/tests/support/backend.ts.
DEFAULT_PASSWORD = "e2e-session-secret-8842"


class E2EView(APIView):
    """Base for the test-support views. Auth is disabled entirely: the harness
    calls these directly, and leaving DRF's SessionAuthentication on would run
    its CSRF check whenever a session cookie is present (e.g. after login-as),
    rejecting the request even though the view is csrf_exempt."""

    authentication_classes: list = []
    permission_classes = [AllowAny]


def _upsert_user(email: str, password: str, **fields) -> "User":
    """Create or update a user keyed by email (stored in username too, matching
    RegisterSerializer) and set a known password."""
    email = email.strip().lower()
    user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
    user.email = email
    for key, value in fields.items():
        setattr(user, key, value)
    user.set_password(password)
    user.is_active = True
    user.save()
    return user


@method_decorator(csrf_exempt, name="dispatch")
class ResetView(E2EView):
    """Wipe all test-relevant data so each scenario starts from a clean slate."""

    def post(self, request: Request) -> Response:
        Item.objects.all().delete()
        User.objects.all().delete()
        Session.objects.all().delete()
        return Response({"detail": "State reset."})


@method_decorator(csrf_exempt, name="dispatch")
class SeedUserView(E2EView):
    """Create a user (without logging in) — for "a registered user…" steps."""

    def post(self, request: Request) -> Response:
        user = _upsert_user(
            request.data["email"],
            request.data.get("password") or DEFAULT_PASSWORD,
            first_name=request.data.get("first_name", ""),
            last_name=request.data.get("last_name", ""),
        )
        return Response({"id": user.pk, "email": user.email}, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class LoginAsView(E2EView):
    """Create the user if needed and start a session — for "I am logged in as…".

    Sets the session cookie on the response; since the harness calls this through
    the page's request context, the browser becomes authenticated.
    """

    def post(self, request: Request) -> Response:
        user = _upsert_user(
            request.data["email"], request.data.get("password") or DEFAULT_PASSWORD
        )
        login(request, user)
        return Response({"id": user.pk, "email": user.email})


@method_decorator(csrf_exempt, name="dispatch")
class SeedItemView(E2EView):
    """Create an Item owned by a user — for "an item named X already exists".

    Items are owner-scoped, so the harness must say who owns the seeded item.
    The owner is upserted (with the known default password, so they can also log
    in), matching how /login-as/ provisions users.
    """

    def post(self, request: Request) -> Response:
        # get_or_create (not _upsert_user): re-hashing an existing user's
        # password would rotate their session auth hash and log them out — which
        # matters when seeding items for the already-logged-in current user.
        email = request.data["owner"].strip().lower()
        owner, created = User.objects.get_or_create(
            username=email, defaults={"email": email}
        )
        if created:
            owner.set_password(DEFAULT_PASSWORD)
            owner.is_active = True
            owner.save()
        item = Item.objects.create(
            owner=owner,
            name=request.data["name"],
            description=request.data.get("description", ""),
        )
        return Response({"id": item.pk, "name": item.name}, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class PasswordResetTokenView(E2EView):
    """Return a real (uid, token) pair so a test can open a valid reset link."""

    def post(self, request: Request) -> Response:
        user = User.objects.get(username=request.data["email"].strip().lower())
        return Response(
            {
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user),
            }
        )
