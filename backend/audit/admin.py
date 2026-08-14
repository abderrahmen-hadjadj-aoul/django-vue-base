from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only view of the audit trail. Rows are written by middleware, never
    edited by hand, so everything is display-only."""

    list_display = ("timestamp", "method", "path", "pending", "status_code", "user", "duration_ms", "ip")
    list_filter = ("pending", "method", "status_code", "timestamp")
    search_fields = ("path", "ip", "user__username", "session_key")
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)

    _fields = (
        "timestamp", "user", "session_key", "method", "path", "query_params",
        "request_body", "pending", "status_code", "duration_ms", "ip", "user_agent",
    )
    readonly_fields = _fields

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
