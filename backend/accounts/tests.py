"""Tests for the session-cookie authentication flow."""
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
        resp = self.client.post(
            reverse("register"),
            {"email": "alice@example.com", "password": "s3cret-pass-99"},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["email"], "alice@example.com")
        self.assertNotIn("username", resp.data)
        # The email is copied into the username field internally.
        self.assertEqual(User.objects.get().username, "alice@example.com")
        # Session established -> /me/ works without logging in again.
        me = self.client.get(reverse("me"))
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["email"], "alice@example.com")

    def test_register_normalizes_and_rejects_duplicate_email(self) -> None:
        self.client.post(
            reverse("register"),
            {"email": "Bob@Example.com", "password": "s3cret-pass-99"},
            format="json",
            **self._csrf_headers(),
        )
        # Stored lowercased.
        self.assertTrue(User.objects.filter(email="bob@example.com").exists())
        # A different-cased duplicate is rejected.
        dup = self.client.post(
            reverse("register"),
            {"email": "BOB@example.com", "password": "another-pass-77"},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_rejects_weak_password(self) -> None:
        resp = self.client.post(
            reverse("register"),
            {"email": "bob@example.com", "password": "123"},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_logout(self) -> None:
        User.objects.create_user("carol@example.com", "carol@example.com", "s3cret-pass-99")
        resp = self.client.post(
            reverse("login"),
            {"email": "carol@example.com", "password": "s3cret-pass-99"},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("me")).status_code, status.HTTP_200_OK)

        logout = self.client.post(reverse("logout"), **self._csrf_headers())
        self.assertEqual(logout.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.get(reverse("me")).status_code, status.HTTP_403_FORBIDDEN
        )

    def test_login_is_case_insensitive(self) -> None:
        User.objects.create_user("carol@example.com", "carol@example.com", "s3cret-pass-99")
        resp = self.client.post(
            reverse("login"),
            {"email": "Carol@Example.com", "password": "s3cret-pass-99"},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_login_bad_credentials(self) -> None:
        User.objects.create_user("dave@example.com", "dave@example.com", "s3cret-pass-99")
        resp = self.client.post(
            reverse("login"),
            {"email": "dave@example.com", "password": "wrong"},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_authentication(self) -> None:
        self.assertEqual(
            self.client.get(reverse("me")).status_code, status.HTTP_403_FORBIDDEN
        )

    def test_password_change(self) -> None:
        User.objects.create_user("erin@example.com", "erin@example.com", "old-pass-1234")
        self.client.post(
            reverse("login"),
            {"email": "erin@example.com", "password": "old-pass-1234"},
            format="json",
            **self._csrf_headers(),
        )
        resp = self.client.post(
            reverse("password-change"),
            {"old_password": "old-pass-1234", "new_password": "new-pass-5678"},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        erin = User.objects.get(email="erin@example.com")
        self.assertTrue(erin.check_password("new-pass-5678"))

    def test_password_reset_flow(self) -> None:
        user = User.objects.create_user(
            "frank@example.com", "frank@example.com", "old-pass-1234"
        )
        resp = self.client.post(
            reverse("password-reset"),
            {"email": "frank@example.com"},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        confirm = self.client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": token, "new_password": "reset-pass-9999"},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(confirm.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("reset-pass-9999"))

    def test_password_reset_unknown_email_is_quiet(self) -> None:
        resp = self.client.post(
            reverse("password-reset"),
            {"email": "nobody@example.com"},
            format="json",
            **self._csrf_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)
