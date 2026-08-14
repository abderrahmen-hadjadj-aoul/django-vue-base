"""Audit-log service — how views record requests to the AuditLog table.

Following the repo's "fat services, thin views" convention, persistence lives
here. **Choosing what is safe to log does not** — it is the caller's job. There
is deliberately no generic "redact by key name" helper: each view knows its own
payload and builds the audit ``body`` explicitly, including only the fields that
are safe for that endpoint and omitting the rest (passwords, tokens, …). The
service stores exactly what it is handed.

**There is one recording pattern, used by every view — reads included:**
write-ahead in two steps, so a request's effect can never happen without a
trace, and a trace can never be orphaned from its effect.

    1. :func:`begin_request` writes a ``pending=True`` row *before* the action.
       It runs in autocommit (outside any transaction) so the row is durable
       even if the action later rolls back.
    2. The action **and** :func:`finalize_request` run in one
       ``transaction.atomic()``, so they commit together. If the action raises,
       the block rolls back the action and the finalize update, leaving the
       ``pending=True`` row behind as the trace.

::

    audit = audit_services.begin_request(request, body={"email": request.data.get("email")})
    with transaction.atomic():
        user = services.register_user(**data)
        response = Response(..., status=201)
        audit_services.finalize_request(audit, response)
    return response

``begin_request``/``finalize_request`` do **not** swallow errors: auditing is a
precondition of the request, so a failure to write the trace aborts (or rolls
back) the action — fail closed, never a silent effect-without-a-log.
"""
from __future__ import annotations

import json
from typing import Any

from django.conf import settings
from django.db import connection

from .models import AuditLog


def begin_request(
    request,
    *,
    body: Any = None,
    query_params: Any = None,
) -> AuditLog | None:
    """Write a ``pending=True`` audit row *before* the action runs.

    Must be called **outside** a transaction so the row commits immediately and
    survives a later rollback of the action. Returns the row (pass it to
    :func:`finalize_request`), or ``None`` if auditing is disabled. Raises rather
    than swallowing: if we cannot record the intent to act, we do not act.
    """
    if not getattr(settings, "AUDIT_LOG_ENABLED", True):
        return None
    if connection.settings_dict.get("ATOMIC_REQUESTS"):
        # With ATOMIC_REQUESTS the whole view runs in one transaction, so the
        # pending row would be rolled back together with a failed action —
        # defeating the write-ahead guarantee. Fail loud rather than silently
        # lose the trace. (The caller must also not wrap begin_request in its own
        # transaction.atomic(); only the action + finalize_request go in there.)
        raise RuntimeError(
            "audit.begin_request needs autocommit so the pending row survives a "
            "rollback of the action, but ATOMIC_REQUESTS is enabled on this "
            "database. Disable it (the audited views manage their own transaction)."
        )
    return AuditLog.objects.create(
        pending=True,
        status_code=None,
        **_base_fields(request, body, query_params),
    )


def finalize_request(
    audit: AuditLog | None,
    response=None,
    *,
    status_code: int | None = None,
    duration_ms: int | None = None,
) -> None:
    """Finalize a pending row: clear ``pending`` and stamp the outcome.

    Call inside the same ``transaction.atomic()`` as the action, so the finalize
    commits with the mutation (or rolls back with it). No-ops if ``audit`` is
    ``None`` (auditing disabled). Does not swallow errors — a failure here rolls
    the action back with it.
    """
    if audit is None:
        return
    audit.pending = False
    audit.status_code = status_code if status_code is not None else getattr(response, "status_code", None)
    fields = ["pending", "status_code"]
    if duration_ms is not None:
        audit.duration_ms = duration_ms
        fields.append("duration_ms")
    audit.save(update_fields=fields)


# -- helpers -------------------------------------------------------------------


def _base_fields(request, body: Any, query_params: Any) -> dict:
    """The request metadata common to every audit row (all non-sensitive)."""
    user = getattr(request, "user", None)
    session = getattr(request, "session", None)
    return dict(
        user=user if getattr(user, "is_authenticated", False) else None,
        session_key=(session.session_key or "") if session is not None else "",
        method=request.method,
        path=request.path[:512],
        query_params=query_params if query_params is not None else {},
        request_body=_bounded(body),
        ip=_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
    )


def _bounded(body: Any) -> Any:
    """Guard row size: bodies that serialise larger than ``AUDIT_MAX_BODY_BYTES``
    are replaced with a note. This is a storage concern, not redaction — the body
    it receives already contains only the fields the caller chose to log."""
    if body is None:
        return None
    max_bytes = getattr(settings, "AUDIT_MAX_BODY_BYTES", 8192)
    if len(json.dumps(body, default=str)) > max_bytes:
        return {"_note": "body too large; not stored"}
    return body


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
