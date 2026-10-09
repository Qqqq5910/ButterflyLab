#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
export BUTTERFLYLAB_REAL_LLM_ENABLED=0
if [ ! -x .venv/bin/python ]; then python3.14 -m venv .venv; fi
if ! .venv/bin/python -m backend.check_environment; then
  .venv/bin/python -m pip install -r backend/requirements.lock.txt
  .venv/bin/python -m backend.check_environment
fi
(cd frontend && (npm ls --depth=0 --silent >/dev/null 2>&1 || npm ci))
exec .venv/bin/python scripts/local_demo.py "$@"
