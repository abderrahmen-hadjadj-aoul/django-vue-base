from rest_framework import status
from rest_framework.test import APITestCase

from .models import Item


class HealthTests(APITestCase):
    def test_health_returns_ok(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})


class ItemTests(APITestCase):
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
