from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Item
from .permissions import IsOwnerOrStaff
from .serializers import ItemSerializer


@extend_schema(
    responses=inline_serializer(
        name="HealthResponse",
        fields={"status": serializers.CharField()},
    ),
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request: Request) -> Response:
    """Simple health-check endpoint used to verify the API is reachable."""
    return Response({"status": "ok"})


class ItemViewSet(viewsets.ModelViewSet):
    """Full CRUD for the example Item model, scoped to the owner.

    A user sees and mutates only their own items; staff users see and mutate
    all of them. Ownership is assigned server-side on create — never trust an
    ``owner`` from the request body (it is read-only on the serializer).
    """

    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        qs = Item.objects.all()
        return qs if user.is_staff else qs.filter(owner=user)

    def perform_create(self, serializer: ItemSerializer) -> None:
        serializer.save(owner=self.request.user)
