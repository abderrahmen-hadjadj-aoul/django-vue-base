from django.conf import settings
from django.db import models


class Item(models.Model):
    """A minimal example model to demonstrate CRUD through the API.

    Each item belongs to a user (``owner``); the API scopes visibility and
    mutation to the owner, with staff users bypassing that scope.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name
