from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwnerOrStaff(permissions.BasePermission):
    """Object-level permission: only the item's owner (or a staff user) may act
    on it.

    Paired with owner-scoped ``get_queryset`` on the viewset, non-owned objects
    already 404 for reads; this class is the explicit guard on the write path.
    """

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        return request.user.is_staff or obj.owner_id == request.user.id
