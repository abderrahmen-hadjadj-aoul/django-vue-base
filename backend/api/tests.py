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
        self.owner = User.objects.create_user("owner", "owner@example.com", "s3cret-pass-99")
        self.other = User.objects.create_user("other", "other@example.com", "s3cret-pass-99")
        self.client.force_authenticate(user=self.owner)

    def test_items_require_authentication(self):
        """Scenario: Items cannot be accessed anonymously."""
        # GIVEN no one is logged in
        self.client.force_authenticate(user=None)
        # WHEN the items are listed
        # THEN it is forbidden
        self.assertEqual(
            self.client.get("/api/items/").status_code, status.HTTP_403_FORBIDDEN
        )

    def test_create_assigns_owner(self):
        """Scenario: Creating an item assigns the requesting user as owner."""
        # GIVEN an authenticated user (see setUp)
        # WHEN they create an item
        create = self.client.post(
            "/api/items/", {"name": "Example", "description": "hi"}, format="json"
        )
        # THEN it is created and owned by them
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create.data["owner"], self.owner.pk)
        self.assertEqual(Item.objects.get().owner, self.owner)

    def test_owner_field_is_not_client_writable(self):
        """Scenario: A client cannot assign an item to someone else."""
        # GIVEN an authenticated user (see setUp)
        # WHEN they try to create an item owned by another user
        create = self.client.post(
            "/api/items/", {"name": "Example", "owner": self.other.pk}, format="json"
        )
        # THEN the spoofed owner is ignored and they own it themselves
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.get().owner, self.owner)

    def test_list_returns_only_own_items(self):
        """Scenario: A user sees only their own items."""
        # GIVEN one item owned by the user and one owned by someone else
        Item.objects.create(owner=self.owner, name="Mine")
        Item.objects.create(owner=self.other, name="Theirs")
        # WHEN the user lists items
        listing = self.client.get("/api/items/")
        # THEN only their own item is returned
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(listing.data["results"][0]["name"], "Mine")

    def test_cannot_retrieve_others_item(self):
        """Scenario: Another user's item is invisible (404, not 403)."""
        # GIVEN an item owned by someone else
        item = Item.objects.create(owner=self.other, name="Theirs")
        # WHEN the user requests it directly
        # THEN it is not found — its existence is not leaked
        self.assertEqual(
            self.client.get(f"/api/items/{item.pk}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_cannot_modify_others_item(self):
        """Scenario: A user cannot mutate another user's item."""
        # GIVEN an item owned by someone else
        item = Item.objects.create(owner=self.other, name="Theirs")
        # WHEN the user tries to update it
        resp = self.client.patch(
            f"/api/items/{item.pk}/", {"name": "Hijacked"}, format="json"
        )
        # THEN it is not found and stays unchanged
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        item.refresh_from_db()
        self.assertEqual(item.name, "Theirs")

    def test_staff_sees_and_edits_all_items(self):
        """Scenario: A staff user sees and can edit every user's items."""
        # GIVEN items owned by two different users
        Item.objects.create(owner=self.owner, name="Mine")
        theirs = Item.objects.create(owner=self.other, name="Theirs")
        # AND a logged-in staff user
        staff = User.objects.create_user(
            "admin", "admin@example.com", "s3cret-pass-99", is_staff=True
        )
        self.client.force_authenticate(user=staff)
        # WHEN the staff user lists items
        listing = self.client.get("/api/items/")
        # THEN every item is visible regardless of owner
        self.assertEqual(listing.data["count"], 2)
        # AND they can edit another user's item
        resp = self.client.patch(
            f"/api/items/{theirs.pk}/", {"name": "Edited"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
