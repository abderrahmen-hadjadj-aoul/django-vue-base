"""Session-cookie authentication endpoints.

The frontend is a first-party SPA served from the same origin (via the Vite dev
proxy in development), so we use Django's built-in session authentication with
CSRF protection rather than tokens. The flow is:

1. The SPA calls ``GET /api/auth/csrf/`` once to receive the ``csrftoken`` cookie.
2. It sends that value back in the ``X-CSRFToken`` header on unsafe requests.
3. ``login`` / ``logout`` create and destroy the session cookie.
"""
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import (
    DetailSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfView(APIView):
    """Set the CSRF cookie so the SPA can read it and echo it back in headers."""

    permission_classes = [AllowAny]

    @extend_schema(responses=DetailSerializer)
    def get(self, request: Request) -> Response:
        return Response({"detail": "CSRF cookie set."})


class RegisterView(APIView):
    """Create a new account and log the user in."""

    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses={201: UserSerializer})
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.register_user(**serializer.validated_data)
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate with username + password and start a session."""

    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: UserSerializer})
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # The email is stored as the username, so authenticate by it.
        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    """End the current session."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: DetailSerializer})
    def post(self, request: Request) -> Response:
        logout(request)
        return Response({"detail": "Logged out."})


class MeView(APIView):
    """Return the currently authenticated user."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request: Request) -> Response:
        return Response(UserSerializer(request.user).data)


class PasswordChangeView(APIView):
    """Change the authenticated user's password (keeps them logged in)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=PasswordChangeSerializer, responses={200: DetailSerializer})
    def post(self, request: Request) -> Response:
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        # Keep the current session valid after the password hash changes.
        update_session_auth_hash(request, request.user)
        return Response({"detail": "Password updated."})


class PasswordResetRequestView(APIView):
    """Email a password-reset link. Always succeeds so we don't leak which
    email addresses are registered."""

    permission_classes = [AllowAny]

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: DetailSerializer})
    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.send_password_reset_email(email=serializer.validated_data["email"])
        return Response(
            {"detail": "If that email exists, a reset link has been sent."}
        )


class PasswordResetConfirmView(APIView):
    """Set a new password from a valid reset token."""

    permission_classes = [AllowAny]

    @extend_schema(request=PasswordResetConfirmSerializer, responses={200: DetailSerializer})
    def post(self, request: Request) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            services.reset_password(**serializer.validated_data)
        except services.InvalidResetToken:
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"detail": "Password has been reset."})
