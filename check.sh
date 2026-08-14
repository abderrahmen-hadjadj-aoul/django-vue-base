#!/usr/bin/env bash
#
# check.sh — the single "is this work DONE?" gate.
#
# Runs, sequentially and independently, the three checks that define DONE for
# this repo (see CLAUDE.md → "Coverage: 100% is the definition of DONE"):
#
#   1. Backend coverage tests  — cd backend && coverage run manage.py test
#                                 && coverage report --fail-under=100
#   2. Frontend type-check     — cd frontend && pnpm type-check
#   3. Frontend e2e tests      — cd frontend && pnpm test:e2e
#
# Every check runs even if an earlier one fails, so one invocation tells you the
# full picture. A per-item OK / NOT OK summary and a single global verdict are
# printed at the end. Exit code is 0 only when ALL three pass.
#
# Usage:  ./check.sh            (from anywhere — it locates its own directory)

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

# --- result tracking --------------------------------------------------------
BACKEND_RESULT="NOT OK"
TYPECHECK_RESULT="NOT OK"
E2E_RESULT="NOT OK"

hr() { printf '%s\n' "============================================================"; }
step() { hr; printf '>>> %s\n' "$1"; hr; }

# --- 1. Backend coverage tests ---------------------------------------------
step "1/3  Backend coverage tests (100% required)"
if [ ! -f "$BACKEND/.venv/bin/activate" ]; then
  echo "ERROR: backend venv missing ($BACKEND/.venv). Create it first:"
  echo "  cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
else
  (
    cd "$BACKEND" || exit 1
    # shellcheck disable=SC1091
    source .venv/bin/activate || exit 1
    coverage run manage.py test && coverage report --fail-under=100
  )
  if [ $? -eq 0 ]; then
    BACKEND_RESULT="OK"
  fi
fi

# --- 2. Frontend type-check -------------------------------------------------
step "2/3  Frontend type-check (pnpm type-check)"
(
  cd "$FRONTEND" || exit 1
  pnpm type-check
)
if [ $? -eq 0 ]; then
  TYPECHECK_RESULT="OK"
fi

# --- 3. Frontend e2e tests --------------------------------------------------
step "3/3  Frontend e2e tests (pnpm test:e2e)"
(
  cd "$FRONTEND" || exit 1
  pnpm test:e2e
)
if [ $? -eq 0 ]; then
  E2E_RESULT="OK"
fi

# --- Summary ----------------------------------------------------------------
GLOBAL_RESULT="OK"
if [ "$BACKEND_RESULT" != "OK" ] || [ "$TYPECHECK_RESULT" != "OK" ] || [ "$E2E_RESULT" != "OK" ]; then
  GLOBAL_RESULT="NOT OK"
fi

echo
hr
printf '  SUMMARY\n'
hr
printf '  %-32s %s\n' "Backend coverage tests" "$BACKEND_RESULT"
printf '  %-32s %s\n' "Frontend type-check"    "$TYPECHECK_RESULT"
printf '  %-32s %s\n' "Frontend e2e tests"     "$E2E_RESULT"
hr
printf '  %-32s %s\n' "GLOBAL" "$GLOBAL_RESULT"
hr

[ "$GLOBAL_RESULT" = "OK" ]
