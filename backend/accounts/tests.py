"""Tests for the session-cookie authentication flow.

Written in a "Django-style Gherkin": still plain APITestCase methods, but each
one reads as a single scenario — a docstring names it, and Given/When/Then
comment blocks structure the body. No BDD framework, no feature files.
"""
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class AuthFlowTests(APITestCase):
    def setUp(self) -> None:
        # enforce_csrf_checks mirrors the real browser flow (SessionAuthentication
        # enforces CSRF once a session exists).
        self.client = APIClient(enforce_csrf_checks=True)

    def _csrf_headers(self) -> dict:
        self.client.get(reverse("csrf"))
        token = self.client.cookies["csrftoken"].value
        return {"HTTP_X_CSRFTOKEN": token}

    def test_register_logs_user_in(self) -> None:
        """Scenario: Registering an account logs the user in."""
        # GIVEN no account exists for alice
        # (fresh test DB)

        # WHEN she registers with a valid email and password
        resp = self.client.post(
            reverse("register"),
            {"email": "alice@example.com", "password": "s3cret-pass-99"},
            format="json",
            **self._csrf_headers(),
        )

        # THEN the account is created and identified only by email
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["email"], "alice@example.com")
        self.assertNotIn("username", resp.data)
        # AND the email is copied into the username field internally
        self.assertEqual(User.objects.get().username, "alice@example.com")
        # AND she is authenticated -> /me/ works without logging in again
        me = self.client.get(reverse("me"))
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["email"], "alice@example.com")

    def test_register_normalizes_and_rejects_duplicate_email(self) -> None:
        """Scenario: Email is normalized, and a cased duplicate is rejected."""
        # GIVEN a mixed-case email is registered
        self.client.post(
            reverse("register"),
            {"email": "Bob@Example.com", "password": "s3cret-pass-99"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN it is stored lowercased
        self.assertTrue(User.objects.filter(email="bob@example.com").exists())

        # WHEN a different-cased duplicate registers
        dup = self.client.post(
            reverse("register"),
            {"email": "BOB@example.com", "password": "another-pass-77"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN it is rejected as invalid
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_rejects_weak_password(self) -> None:
        """Scenario: A weak password is rejected on registration."""
        # WHEN someone registers with a trivially weak password
        resp = self.client.post(
            reverse("register"),
            {"email": "bob@example.com", "password": "123"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN the request is rejected as invalid
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_logout(self) -> None:
        """Scenario: A registered user can log in and then out."""
        # GIVEN a registered user
        User.objects.create_user("carol@example.com", "carol@example.com", "s3cret-pass-99")

        # WHEN she logs in with the right credentials
        resp = self.client.post(
            reverse("login"),
            {"email": "carol@example.com", "password": "s3cret-pass-99"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN a session is established
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("me")).status_code, status.HTTP_200_OK)

        # WHEN she logs out
        logout = self.client.post(reverse("logout"), **self._csrf_headers())
        # THEN the session ends and /me/ is forbidden again
        self.assertEqual(logout.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.get(reverse("me")).status_code, status.HTTP_403_FORBIDDEN
        )

    def test_login_is_case_insensitive(self) -> None:
        """Scenario: Login is case-insensitive on the email."""
        # GIVEN a registered user with a lowercase email
        User.objects.create_user("carol@example.com", "carol@example.com", "s3cret-pass-99")

        # WHEN she logs in with a differently-cased email
        resp = self.client.post(
            reverse("login"),
            {"email": "Carol@Example.com", "password": "s3cret-pass-99"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN login still succeeds
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_login_bad_credentials(self) -> None:
        """Scenario: Login with the wrong password is rejected."""
        # GIVEN a registered user
        User.objects.create_user("dave@example.com", "dave@example.com", "s3cret-pass-99")

        # WHEN she logs in with the wrong password
        resp = self.client.post(
            reverse("login"),
            {"email": "dave@example.com", "password": "wrong"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN the request is rejected as invalid
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_authentication(self) -> None:
        """Scenario: The current-user endpoint requires authentication."""
        # GIVEN no one is logged in
        # WHEN the current user is requested
        # THEN it is forbidden
        self.assertEqual(
            self.client.get(reverse("me")).status_code, status.HTTP_403_FORBIDDEN
        )

    def test_password_change(self) -> None:
        """Scenario: A logged-in user can change their password."""
        # GIVEN a logged-in user
        User.objects.create_user("erin@example.com", "erin@example.com", "old-pass-1234")
        self.client.post(
            reverse("login"),
            {"email": "erin@example.com", "password": "old-pass-1234"},
            format="json",
            **self._csrf_headers(),
        )

        # WHEN she changes her password
        resp = self.client.post(
            reverse("password-change"),
            {"old_password": "old-pass-1234", "new_password": "new-pass-5678"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN the new password takes effect
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        erin = User.objects.get(email="erin@example.com")
        self.assertTrue(erin.check_password("new-pass-5678"))

    def test_password_reset_flow(self) -> None:
        """Scenario: A user can reset a forgotten password."""
        # GIVEN a registered user
        user = User.objects.create_user(
            "frank@example.com", "frank@example.com", "old-pass-1234"
        )

        # WHEN she requests a password reset
        resp = self.client.post(
            reverse("password-reset"),
            {"email": "frank@example.com"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN one reset email is sent
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

        # WHEN she confirms the reset with a valid uid+token and a new password
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        confirm = self.client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": token, "new_password": "reset-pass-9999"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN the new password takes effect
        self.assertEqual(confirm.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("reset-pass-9999"))

    def test_password_change_rejects_wrong_old_password(self) -> None:
        """Scenario: Changing a password with the wrong current password is rejected."""
        # GIVEN a logged-in user
        User.objects.create_user("gina@example.com", "gina@example.com", "old-pass-1234")
        self.client.post(
            reverse("login"),
            {"email": "gina@example.com", "password": "old-pass-1234"},
            format="json",
            **self._csrf_headers(),
        )

        # WHEN she submits the wrong current password
        resp = self.client.post(
            reverse("password-change"),
            {"old_password": "not-my-password", "new_password": "new-pass-5678"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN the request is rejected and the password is unchanged
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        gina = User.objects.get(email="gina@example.com")
        self.assertTrue(gina.check_password("old-pass-1234"))

    def test_password_reset_confirm_rejects_bad_token(self) -> None:
        """Scenario: Confirming a reset with a valid uid but wrong token is rejected."""
        # GIVEN a registered user
        user = User.objects.create_user(
            "hank@example.com", "hank@example.com", "old-pass-1234"
        )

        # WHEN she confirms with a correctly-encoded uid but a bogus token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        resp = self.client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": "not-a-real-token", "new_password": "reset-pass-9999"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN it is rejected and the old password still works
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        user.refresh_from_db()
        self.assertTrue(user.check_password("old-pass-1234"))

    def test_password_reset_confirm_rejects_unknown_uid(self) -> None:
        """Scenario: Confirming a reset for a uid that decodes to no user is rejected."""
        # GIVEN no user matching the encoded uid (fresh test DB, pk 999 absent)
        uid = urlsafe_base64_encode(force_bytes(999))
        token = default_token_generator.make_token(
            User.objects.create_user("iris@example.com", "iris@example.com", "pw-1234-abcd")
        )
        # WHEN a reset is confirmed against the missing user's uid
        resp = self.client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": token, "new_password": "reset-pass-9999"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN it is rejected (the uid decodes but matches no user)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_unknown_email_is_quiet(self) -> None:
        """Scenario: A reset for an unknown email is quietly ignored."""
        # WHEN a reset is requested for an email with no account
        resp = self.client.post(
            reverse("password-reset"),
            {"email": "nobody@example.com"},
            format="json",
            **self._csrf_headers(),
        )
        # THEN the response is still OK, but no email is sent (no user enumeration)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)
