from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Item

User = get_user_model()


class HealthTests(APITestCase):
    def test_health_returns_ok(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})


class ItemTests(APITestCase):
    def setUp(self):
        # The Item API requires authentication (IsAuthenticated is the default).
        user = User.objects.create_user("tester", "tester@example.com", "s3cret-pass-99")
        self.client.force_authenticate(user=user)

    def test_items_require_authentication(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(
            self.client.get("/api/items/").status_code, status.HTTP_403_FORBIDDEN
        )

    def test_create_and_list_items(self):
        create = self.client.post(
            "/api/items/", {"name": "Example", "description": "hi"}, format="json"
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.count(), 1)

        listing = self.client.get("/api/items/")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(listing.data["results"][0]["name"], "Example")
