#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/backend"

if [[ "${CONDA_DEFAULT_ENV:-}" == "ai_girl" ]]; then
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
  conda run -n ai_girl python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
