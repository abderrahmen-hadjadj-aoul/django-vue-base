from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ItemViewSet, health

router = DefaultRouter()
router.register(r"items", ItemViewSet, basename="item")

urlpatterns = [
    path("health/", health, name="health"),
    path("", include(router.urls)),
]
