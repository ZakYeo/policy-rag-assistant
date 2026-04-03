#!/usr/bin/env bash
set -euo pipefail

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "Could not find a Python interpreter. Activate a virtual environment first." >&2
  exit 1
fi

"${PYTHON_BIN}" -m app.evals.cli
