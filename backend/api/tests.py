"""Tests for the api app.

Written in a "Django-style Gherkin": plain APITestCase methods where each one
reads as a scenario — a docstring names it, and Given/When/Then comment blocks
structure the body. No BDD framework, no feature files.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Item

User = get_user_model()


class HealthTests(APITestCase):
    def test_health_returns_ok(self):
        """Scenario: The health endpoint reports OK."""
        # WHEN the health endpoint is checked
        response = self.client.get("/api/health/")
        # THEN it reports status "ok"
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})


class ItemTests(APITestCase):
    def setUp(self):
        # The Item API requires authentication (IsAuthenticated is the default).
        user = User.objects.create_user("tester", "tester@example.com", "s3cret-pass-99")
        self.client.force_authenticate(user=user)

    def test_items_require_authentication(self):
        """Scenario: Items cannot be accessed anonymously."""
        # GIVEN no one is logged in
        self.client.force_authenticate(user=None)
        # WHEN the items are listed
        # THEN it is forbidden
        self.assertEqual(
            self.client.get("/api/items/").status_code, status.HTTP_403_FORBIDDEN
        )

    def test_create_and_list_items(self):
        """Scenario: An authenticated user can create and list items."""
        # GIVEN an authenticated user (see setUp)
        # WHEN they create an item
        create = self.client.post(
            "/api/items/", {"name": "Example", "description": "hi"}, format="json"
        )
        # THEN it is created and persisted
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.count(), 1)

        # WHEN they list the items
        listing = self.client.get("/api/items/")
        # THEN the created item is returned
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(listing.data["results"][0]["name"], "Example")
