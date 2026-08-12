from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Item
from .serializers import ItemSerializer


@extend_schema(
    responses=inline_serializer(
        name="HealthResponse",
        fields={"status": serializers.CharField()},
    ),
)
@api_view(["GET"])
def health(request: Request) -> Response:
    """Simple health-check endpoint used to verify the API is reachable."""
    return Response({"status": "ok"})


class ItemViewSet(viewsets.ModelViewSet):
    """Full CRUD for the example Item model."""

    queryset = Item.objects.all()
    serializer_class = ItemSerializer
