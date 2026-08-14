"""Tests for the environment loader (config/env.py).

Written in a "Django-style Gherkin": plain TestCase methods where each one reads
as a scenario — a docstring names it, and Given/When/Then comment blocks
structure the body. No BDD framework, no feature files.

These exercise the fail-closed path (missing variables abort startup), which the
normal suite never hits because it always runs with a complete ``.env``. To
reach it we run the loader in an isolated, empty environment (``os.environ``
cleared) pointed at an empty ``.env`` file, so every required variable resolves
as missing.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from .env import _SPECS, load_env


class LoadEnvTests(SimpleTestCase):
    def test_missing_variables_fail_closed(self) -> None:
        """Scenario: With no variables defined, startup aborts listing every one."""
        # GIVEN an empty environment and an empty .env file (nothing is defined)
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".env").write_text("")
            # WHEN the loader runs
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ImproperlyConfigured) as ctx:
                    load_env(Path(tmp))

        # THEN it fails closed, and the error names every required variable
        message = str(ctx.exception)
        self.assertIn(f"{len(_SPECS)} required environment variable(s) missing", message)
        for name, _cast, _secret in _SPECS:
            self.assertIn(name, message)

    def test_all_variables_present_returns_resolved_values(self) -> None:
        """Scenario: With every variable defined, the loader returns their values."""
        # GIVEN a complete environment (a valid value for each required variable)
        values = {name: self._sample_value(cast) for name, cast, _secret in _SPECS}
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".env").write_text("")
            # WHEN the loader runs against it
            with patch.dict(os.environ, values, clear=True):
                resolved = load_env(Path(tmp))

        # THEN it returns a resolved value for every required variable
        for name, _cast, _secret in _SPECS:
            self.assertIn(name, resolved)

    @staticmethod
    def _sample_value(cast: str) -> str:
        """A syntactically valid raw value for each cast type."""
        return {
            "str": "value",
            "bool": "True",
            "int": "42",
            "list": "a,b",
            "db": "sqlite:///db.sqlite3",
        }[cast]
