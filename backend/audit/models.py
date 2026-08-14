from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """One row per HTTP request, written by ``audit.services``.

    Captures request metadata (who/what/when/outcome) plus a request ``body`` the
    calling view built. Callers include only the fields that are safe to log for
    their endpoint, so the log itself never stores passwords, tokens, etc.

    Mutating endpoints use a write-ahead pattern (``begin_request`` →
    ``finalize_request``): a row is first written with ``pending=True`` and a null
    ``status_code`` *before* the action runs, then finalized (``pending=False``,
    real status) inside the same transaction as the action. A leftover
    ``pending=True`` row therefore marks a request whose action was rolled back or
    never completed — the trace survives even when the action does not.
    """

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    # SET_NULL (not CASCADE): deleting a user must not erase their audit trail.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    session_key = models.CharField(max_length=40, blank=True)
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=512, db_index=True)
    query_params = models.JSONField(default=dict, blank=True)
    request_body = models.JSONField(null=True, blank=True)
    # Null while a request is still pending (no outcome yet); set on completion.
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    # True between begin_request and finalize_request. A row that stays True means
    # the action was rolled back or the request never completed.
    pending = models.BooleanField(default=True, db_index=True)
    # Optional: callers may pass an elapsed time, but the explicit end-of-action
    # call site doesn't measure the full request, so it is left null by default.
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        who = self.user_id or "anon"
        outcome = "pending" if self.pending else self.status_code
        return f"{self.method} {self.path} -> {outcome} ({who})"
