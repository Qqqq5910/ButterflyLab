#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
export BUTTERFLYLAB_REAL_LLM_ENABLED=0
python3.14 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
.venv/bin/python -m backend.check_environment
(cd frontend && (npm ls --depth=0 --silent >/dev/null 2>&1 || npm ci))
export VITE_API_URL=/api
export BUTTERFLYLAB_DEV_BACKEND=http://127.0.0.1:8001
.venv/bin/python -m uvicorn backend.api:app --host 127.0.0.1 --port 8001 &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' EXIT INT TERM
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
