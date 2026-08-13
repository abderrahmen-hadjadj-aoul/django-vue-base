"""Business logic for the accounts app.

This is the **service layer**: plain functions that hold the domain logic and
side effects (creating users, minting reset tokens, sending email). Views call
into here and stay thin — they only translate HTTP <-> service calls and map
domain errors to responses. Serializers stay focused on validation and the
OpenAPI shape.

When business logic grows complex, put it here rather than in views (which then
become untestable without HTTP) or serializers (which would pollute the
generated API schema). Mirror this module in other apps (e.g. ``api/services.py``).
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

User = get_user_model()


class InvalidResetToken(Exception):
    """Raised when a password-reset uid/token pair is invalid or expired."""


def register_user(
    *,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
) -> "User":
    """Create a new account keyed by email.

    The email is stored in the ``username`` field too, so Django's built-in
    username-based auth (``authenticate``/``login``) works with email as the
    only credential and email uniqueness is enforced by username's constraint.
    """
    return User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )


def send_password_reset_email(*, email: str) -> None:
    """Email a reset link to every active user matching ``email``.

    Intentionally silent about whether the address exists, so callers can
    always report success and avoid leaking which emails are registered.
    """
    for user in User.objects.filter(email__iexact=email, is_active=True):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
        user.email_user(
            subject="Reset your password",
            message=(
                "Use the link below to choose a new password:\n\n"
                f"{reset_url}\n\n"
                "If you did not request this, you can ignore this email."
            ),
        )


def reset_password(*, uid: str, token: str, new_password: str) -> "User":
    """Set a new password from a valid reset token.

    Raises ``InvalidResetToken`` if the uid/token pair does not check out.
    """
    try:
        pk = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=pk)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        raise InvalidResetToken

    user.set_password(new_password)
    user.save(update_fields=["password"])
    return user
