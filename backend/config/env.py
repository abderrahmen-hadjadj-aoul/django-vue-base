"""Environment configuration: load, validate, and report at startup.

Every setting this project needs is read from an environment variable with **no
default**. A missing variable is a hard, fail-closed error: rather than silently
falling back to an insecure placeholder (or blowing up with a stack trace on the
first access deep in Django), we collect *all* the missing variables up front,
print one readable report, and refuse to start.

Fill every variable in `backend/.env` (copy `backend/.env.example` to start).
When you add a new setting, add its spec to `_SPECS` below — that is the single
source of truth for "what this project requires from the environment".
"""

from __future__ import annotations

import sys
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

# (name, cast, secret) — `cast` names one of the readers in `_READERS`; `secret`
# values are never echoed in the startup report (only shown as "set").
_SPECS: list[tuple[str, str, bool]] = [
    ("SECRET_KEY", "str", True),
    ("DEBUG", "bool", False),
    ("ALLOWED_HOSTS", "list", False),
    ("CORS_ALLOWED_ORIGINS", "list", False),
    ("CSRF_TRUSTED_ORIGINS", "list", False),
    ("FRONTEND_URL", "str", False),
    ("EMAIL_BACKEND", "str", False),
    ("DEFAULT_FROM_EMAIL", "str", False),
    ("SESSION_COOKIE_SECURE", "bool", False),
    ("CSRF_COOKIE_SECURE", "bool", False),
    ("E2E_MODE", "bool", False),
    ("DATABASE_URL", "db", True),
    ("AUDIT_LOG_ENABLED", "bool", False),
    ("AUDIT_MAX_BODY_BYTES", "int", False),
]

_READERS = {
    "str": lambda env, name: env.str(name),
    "bool": lambda env, name: env.bool(name),
    "int": lambda env, name: env.int(name),
    "list": lambda env, name: env.list(name),
    "db": lambda env, name: env.db(name),
}


def _is_defined(env: environ.Env, name: str) -> bool:
    """A variable counts as defined only if it is present and non-blank.

    An explicitly empty value (``FOO=``) is treated as missing — for a mandatory
    setting that is almost always a mistake, so we surface it like any other.
    """
    try:
        raw = env.str(name)
    except ImproperlyConfigured:
        return False
    return raw.strip() != ""


def _render(cast: str, secret: bool, value) -> str:
    """Human-readable rendering of a resolved value for the report."""
    if secret:
        return "•••• (set)"
    if cast == "list":
        return ", ".join(value) if value else "(empty list)"
    return str(value)


def load_env(base_dir: Path) -> dict:
    """Read `.env`, validate every required variable, print a report, return values.

    Raises `ImproperlyConfigured` (after printing the report) if any variable is
    missing, so the process fails closed instead of running misconfigured.
    """
    env = environ.Env()
    environ.Env.read_env(base_dir / ".env")

    resolved: dict = {}
    rows: list[tuple[str, bool, str]] = []
    missing: list[str] = []

    for name, cast, secret in _SPECS:
        if _is_defined(env, name):
            value = _READERS[cast](env, name)
            resolved[name] = value
            rows.append((name, True, _render(cast, secret, value)))
        else:
            missing.append(name)
            rows.append((name, False, "MISSING — must be defined"))

    _print_report(rows, missing)

    if missing:
        raise ImproperlyConfigured(
            f"{len(missing)} required environment variable(s) missing: "
            f"{', '.join(missing)}. Copy backend/.env.example to backend/.env "
            "and fill in every value (see the report above)."
        )
    return resolved


def _print_report(rows: list[tuple[str, bool, str]], missing: list[str]) -> None:
    """Print the environment report to stderr (keeps stdout clean for commands)."""
    name_width = max(len(name) for name, _, _ in rows)
    bar = "═" * (name_width + 34)
    out = sys.stderr

    print(bar, file=out)
    print(" Environment configuration", file=out)
    print(bar, file=out)
    for name, ok, shown in rows:
        mark = "✓" if ok else "✗"
        print(f"  {mark} {name.ljust(name_width)}   {shown}", file=out)
    print(bar, file=out)
    if missing:
        print(f" ✗ {len(missing)} of {len(rows)} required variable(s) MISSING.", file=out)
        print("   Define them in backend/.env — the app will not start.", file=out)
    else:
        print(f" ✓ all {len(rows)} required variables are set.", file=out)
    print(bar, file=out)
