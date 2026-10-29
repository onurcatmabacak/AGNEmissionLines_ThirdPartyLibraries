#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/Tools:$ROOT"
exec "$ROOT/.venv/bin/python" -m pipeline_ir.run "$@"
