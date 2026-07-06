#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required but not found in PATH." >&2
  exit 2
fi

exec python3 -m metacleaner "$@"
