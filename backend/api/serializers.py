from rest_framework import serializers

from .models import Item


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "description", "created_at", "owner"]
        # owner is assigned server-side from the request user (see the viewset);
        # exposing it read-only lets clients see ownership but never spoof it.
        read_only_fields = ["id", "created_at", "owner"]
