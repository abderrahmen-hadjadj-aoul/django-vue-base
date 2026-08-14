from django.db import transaction
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from audit import services as audit_services

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
    audit = audit_services.begin_request(request)
    with transaction.atomic():
        response = Response({"status": "ok"})
        audit_services.finalize_request(audit, response)
    return response


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

    # Audit every action with the write-ahead pattern: begin_request writes a
    # pending row first, then the action and finalize_request run in one
    # transaction — so an Item is never read/created/changed/deleted without a
    # finalized audit row, and a rolled-back action leaves a pending trace. Write
    # bodies come from _audit_body below, which names the fields worth keeping for
    # an Item (there is nothing sensitive to omit here).
    @staticmethod
    def _audit_body(request: Request) -> dict:
        """The audit body for an Item write: the client-supplied fields. `owner`
        is server-assigned and never in the body, so nothing needs excluding."""
        return {
            "name": request.data.get("name"),
            "description": request.data.get("description"),
        }

    def list(self, request: Request, *args, **kwargs) -> Response:
        audit = audit_services.begin_request(request)
        with transaction.atomic():
            response = super().list(request, *args, **kwargs)
            audit_services.finalize_request(audit, response)
        return response

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        audit = audit_services.begin_request(request)
        with transaction.atomic():
            response = super().retrieve(request, *args, **kwargs)
            audit_services.finalize_request(audit, response)
        return response

    def create(self, request: Request, *args, **kwargs) -> Response:
        audit = audit_services.begin_request(request, body=self._audit_body(request))
        with transaction.atomic():
            response = super().create(request, *args, **kwargs)
            audit_services.finalize_request(audit, response)
        return response

    def update(self, request: Request, *args, **kwargs) -> Response:
        audit = audit_services.begin_request(request, body=self._audit_body(request))
        with transaction.atomic():
            response = super().update(request, *args, **kwargs)
            audit_services.finalize_request(audit, response)
        return response

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        audit = audit_services.begin_request(request, body=self._audit_body(request))
        with transaction.atomic():
            response = super().partial_update(request, *args, **kwargs)
            audit_services.finalize_request(audit, response)
        return response

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        audit = audit_services.begin_request(request)
        with transaction.atomic():
            response = super().destroy(request, *args, **kwargs)
            audit_services.finalize_request(audit, response)
        return response
