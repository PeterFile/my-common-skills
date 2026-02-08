#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_BIN="python"
    else
        echo "[sequential] ERROR: python not found (set PYTHON_BIN=python3 or install python)" >&2
        exit 127
    fi
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/scripts/sequential_loop.py" "$@"
