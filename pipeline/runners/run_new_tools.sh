#!/usr/bin/env bash
# Run the source-keyed NIR/MIR/FIR/SED matrix.
#   bash pipeline/runners/run_new_tools.sh [--tools ...] [--only ...] [--force]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec "$ROOT/.venv/bin/python" "$ROOT/pipeline/run_new_tools.py" "$@"
