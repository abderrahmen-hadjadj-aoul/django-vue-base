"""Serializers for the authentication endpoints.

These drive both request validation and the generated OpenAPI schema, so keep
the fields explicit and typed.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """The public shape of the authenticated user (never exposes the password).

    Credentials are email + password; the email is the account's identity, so
    ``username`` is not exposed (it holds a copy of the email internally — see
    RegisterSerializer).
    """

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Validates and creates a new user account, keyed by email."""

    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def validate_email(self, value: str) -> str:
        # Normalize case: email login must be case-insensitive, but the username
        # (where we store the email) is unique case-sensitively.
        value = value.strip().lower()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data: dict) -> "User":
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        # Store the email in the username field too, so Django's built-in
        # username-based auth (authenticate/login) works with email as the only
        # credential and email uniqueness is enforced by username's constraint.
        return User.objects.create_user(
            username=email, email=email, password=password, **validated_data
        )


class LoginSerializer(serializers.Serializer):
    """Credentials for session login (email + password)."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_email(self, value: str) -> str:
        return value.strip().lower()


class PasswordChangeSerializer(serializers.Serializer):
    """Change the password of the currently authenticated user."""

    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_old_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value: str) -> str:
        validate_password(value, user=self.context["request"].user)
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request a password-reset email for the given address."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Set a new password using the token emailed to the user."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_new_password(self, value: str) -> str:
        validate_password(value)
        return value


class DetailSerializer(serializers.Serializer):
    """A simple `{ "detail": "..." }` response body used across auth endpoints."""

    detail = serializers.CharField()
