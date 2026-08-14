"""Tests for the api app.

Written in a "Django-style Gherkin": plain APITestCase methods where each one
reads as a scenario — a docstring names it, and Given/When/Then comment blocks
structure the body. No BDD framework, no feature files.
"""
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
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

    def test_item_str_is_its_name(self):
        """Scenario: An item renders as its name."""
        # GIVEN an item
        item = Item.objects.create(owner=self.owner, name="Widget")
        # WHEN it is rendered as a string
        # THEN it shows the name
        self.assertEqual(str(item), "Widget")

    def test_owner_can_retrieve_own_item(self):
        """Scenario: A user can retrieve their own item by id."""
        # GIVEN an item owned by the user
        item = Item.objects.create(owner=self.owner, name="Mine")
        # WHEN they request it directly
        resp = self.client.get(f"/api/items/{item.pk}/")
        # THEN it is returned
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Mine")

    def test_owner_can_delete_own_item(self):
        """Scenario: A user can delete their own item."""
        # GIVEN an item owned by the user
        item = Item.objects.create(owner=self.owner, name="Mine")
        # WHEN they delete it
        resp = self.client.delete(f"/api/items/{item.pk}/")
        # THEN it is gone
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Item.objects.filter(pk=item.pk).exists())

    def test_cannot_delete_others_item(self):
        """Scenario: A user cannot delete another user's item."""
        # GIVEN an item owned by someone else
        item = Item.objects.create(owner=self.other, name="Theirs")
        # WHEN the user tries to delete it
        resp = self.client.delete(f"/api/items/{item.pk}/")
        # THEN it is not found and stays intact
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Item.objects.filter(pk=item.pk).exists())

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


# The test-support endpoints are normally mounted under /api/test/ only when
# E2E_MODE is on (see config/urls.py) and are driven by the Playwright suite, not
# this one. We point ROOT_URLCONF straight at their urlconf so the same views run
# under the Django suite too — verifying the harness contract and covering the
# module without needing E2E_MODE toggled on the whole process.
@override_settings(ROOT_URLCONF="api.e2e_urls")
class E2ESupportTests(APITestCase):
    def test_reset_wipes_all_state(self):
        """Scenario: The reset endpoint clears users and items."""
        # GIVEN some existing data
        user = User.objects.create_user("x", "x@example.com", "s3cret-pass-99")
        Item.objects.create(owner=user, name="Leftover")
        # WHEN the harness resets state
        resp = self.client.post(reverse("e2e-reset"))
        # THEN everything is gone
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Item.objects.count(), 0)

    def test_seed_user_upserts_by_email(self):
        """Scenario: Seeding a user creates it, and re-seeding updates in place."""
        # WHEN a user is seeded with profile fields
        resp = self.client.post(
            reverse("e2e-seed-user"),
            {"email": "Seed@Example.com", "password": "pw-1234-abcd", "first_name": "Sea"},
            format="json",
        )
        # THEN it is created, email normalized, and identified only by email
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["email"], "seed@example.com")
        seeded = User.objects.get(email="seed@example.com")
        self.assertEqual(seeded.first_name, "Sea")
        self.assertTrue(seeded.check_password("pw-1234-abcd"))

        # WHEN the same email is seeded again (default password path)
        self.client.post(
            reverse("e2e-seed-user"), {"email": "seed@example.com"}, format="json"
        )
        # THEN no duplicate is created — it is upserted
        self.assertEqual(User.objects.filter(email="seed@example.com").count(), 1)

    def test_login_as_starts_a_session(self):
        """Scenario: login-as provisions a user and authenticates the client."""
        # WHEN the harness logs in as someone new
        resp = self.client.post(
            reverse("e2e-login-as"), {"email": "who@example.com"}, format="json"
        )
        # THEN the user exists and a session cookie is set
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.filter(email="who@example.com").exists())
        self.assertIn("sessionid", resp.cookies)

    def test_seed_item_for_new_and_existing_owner(self):
        """Scenario: Seeding an item provisions a new owner, or reuses an existing one."""
        # WHEN an item is seeded for a brand-new owner
        first = self.client.post(
            reverse("e2e-seed-item"),
            {"owner": "New@Example.com", "name": "Alpha", "description": "d"},
            format="json",
        )
        # THEN the owner is created and owns the item
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        owner = User.objects.get(email="new@example.com")
        self.assertEqual(Item.objects.get(pk=first.data["id"]).owner, owner)

        # WHEN a second item is seeded for that now-existing owner
        second = self.client.post(
            reverse("e2e-seed-item"),
            {"owner": "new@example.com", "name": "Beta"},
            format="json",
        )
        # THEN no duplicate owner is created and both items belong to them
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(email="new@example.com").count(), 1)
        self.assertEqual(owner.items.count(), 2)

    def test_password_reset_token_returns_valid_pair(self):
        """Scenario: The token endpoint mints a uid+token that actually validates."""
        # GIVEN a seeded user
        self.client.post(
            reverse("e2e-seed-user"), {"email": "reset@example.com"}, format="json"
        )
        # WHEN a reset token is requested
        resp = self.client.post(
            reverse("e2e-password-reset-token"),
            {"email": "reset@example.com"},
            format="json",
        )
        # THEN a uid and token come back
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("uid", resp.data)
        self.assertIn("token", resp.data)
