"""Tests for the audit app.

Written in a "Django-style Gherkin": plain APITestCase methods where each one
reads as a scenario — a docstring names it, and Given/When/Then comment blocks
structure the body. No BDD framework, no feature files.
"""
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from . import services
from .models import AuditLog

User = get_user_model()


class AuditLoggingTests(APITestCase):
    def test_get_request_is_logged(self):
        """Scenario: Even an anonymous GET is recorded with metadata."""
        # GIVEN a fresh audit trail (empty test DB)
        # WHEN an unauthenticated GET hits the health endpoint
        response = self.client.get("/api/health/")
        # THEN the request succeeds
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # AND exactly one audit row captures its metadata
        entry = AuditLog.objects.get()
        self.assertEqual(entry.method, "GET")
        self.assertEqual(entry.path, "/api/health/")
        self.assertEqual(entry.status_code, status.HTTP_200_OK)
        self.assertFalse(entry.pending)
        self.assertIsNone(entry.user)

    def test_login_logs_email_but_not_password(self):
        """Scenario: The login view logs the email it received, never the password."""
        # GIVEN a registered user
        User.objects.create_user("dana@example.com", "dana@example.com", "sup3r-secret-pw")
        # WHEN they log in
        self.client.post(
            "/api/auth/login/",
            {"email": "dana@example.com", "password": "sup3r-secret-pw"},
            format="json",
        )
        # THEN the audit body keeps the email (useful) and omits the password entirely
        entry = AuditLog.objects.get(path="/api/auth/login/")
        self.assertEqual(entry.request_body, {"email": "dana@example.com"})
        self.assertNotIn("password", entry.request_body)
        self.assertNotIn("sup3r-secret-pw", str(entry.request_body))

    def test_item_create_finalizes_the_audit_row(self):
        """Scenario: A successful mutation leaves a finalized audit row."""
        # GIVEN an authenticated user
        user = User.objects.create_user("eve", "eve@example.com", "s3cret-pass-99")
        self.client.force_authenticate(user=user)
        # WHEN they create an item
        self.client.post(
            "/api/items/",
            {"name": "Widget", "description": "A thing"},
            format="json",
        )
        # THEN the row is finalized: not pending, real status, fields + user recorded
        entry = AuditLog.objects.get(path="/api/items/", method="POST")
        self.assertFalse(entry.pending)
        self.assertEqual(entry.status_code, status.HTTP_201_CREATED)
        self.assertEqual(entry.request_body, {"name": "Widget", "description": "A thing"})
        self.assertEqual(entry.user, user)

    def test_rolled_back_mutation_leaves_a_pending_trace(self):
        """Scenario: If the action fails after the pending write, the mutation is
        rolled back but the pending audit trace survives."""
        # GIVEN registration that writes a user and then blows up mid-action
        def boom(**kwargs):
            User.objects.create_user("ghost@example.com", "ghost@example.com", "x")
            raise RuntimeError("kaboom")

        # AND a client that surfaces the 500 instead of re-raising
        self.client.raise_request_exception = False
        # WHEN the registration is attempted
        with patch("accounts.views.services.register_user", side_effect=boom):
            self.client.post(
                "/api/auth/register/",
                {"email": "dana@example.com", "password": "sup3r-secret-pw"},
                format="json",
            )
        # THEN the half-done mutation was rolled back — no user was created
        self.assertFalse(User.objects.filter(username="ghost@example.com").exists())
        # AND a pending trace of the attempt remains, with no final status
        entry = AuditLog.objects.get(path="/api/auth/register/")
        self.assertTrue(entry.pending)
        self.assertIsNone(entry.status_code)
        self.assertEqual(entry.request_body, {"email": "dana@example.com"})

    @override_settings(AUDIT_LOG_ENABLED=False)
    def test_disabled_flag_skips_logging(self):
        """Scenario: With auditing disabled, no rows are written."""
        # GIVEN auditing is turned off (see override)
        # WHEN a request is made
        self.client.get("/api/health/")
        # THEN nothing is recorded
        self.assertEqual(AuditLog.objects.count(), 0)


class BeginFinalizeUnitTests(APITestCase):
    def _fake_request(self):
        request = Mock()
        request.user = None
        request.session = None
        request.method = "POST"
        request.path = "/api/example/"
        request.META = {"REMOTE_ADDR": "10.0.0.1", "HTTP_USER_AGENT": "pytest"}
        return request

    def test_begin_stores_the_body_verbatim(self):
        """Scenario: begin_request records exactly the body it is handed."""
        # GIVEN the caller has already decided what is safe to log
        body = {"email": "x@example.com"}
        # WHEN the pending row is written
        services.begin_request(self._fake_request(), body=body)
        # THEN it is stored as-is — the service performs no redaction of its own
        entry = AuditLog.objects.get()
        self.assertEqual(entry.request_body, body)
        self.assertEqual(entry.ip, "10.0.0.1")

    def test_begin_then_finalize(self):
        """Scenario: begin_request writes a pending row; finalize_request completes it."""
        # GIVEN a pending row written before the action
        audit = services.begin_request(self._fake_request(), body={"email": "x@example.com"})
        self.assertTrue(audit.pending)
        self.assertIsNone(audit.status_code)
        # WHEN the action finishes and the row is finalized
        services.finalize_request(audit, Mock(status_code=201))
        # THEN the stored row is no longer pending and carries the final status
        audit.refresh_from_db()
        self.assertFalse(audit.pending)
        self.assertEqual(audit.status_code, 201)

    @override_settings(AUDIT_MAX_BODY_BYTES=10)
    def test_oversized_body_is_replaced_with_a_note(self):
        """Scenario: A body larger than the cap is noted, not stored."""
        # GIVEN a body that exceeds the configured size cap
        body = {"name": "x" * 100}
        # WHEN the pending row is written
        services.begin_request(self._fake_request(), body=body)
        # THEN only a placeholder note is kept
        entry = AuditLog.objects.get()
        self.assertEqual(entry.request_body, {"_note": "body too large; not stored"})
