from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter

from .views import ItemViewSet, health

router = DefaultRouter()
router.register(r"items", ItemViewSet, basename="item")

urlpatterns = [
    path("health/", health, name="health"),
    # OpenAPI schema + interactive docs (kept public in the template).
    path("schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny]),
        name="swagger-ui",
    ),
    path("", include(router.urls)),
]
