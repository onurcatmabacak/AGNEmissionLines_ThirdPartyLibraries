#!/usr/bin/env bash
# =============================================================================
#  analyze.sh -- one command: drop spectra in input/ and get the best fit
# =============================================================================
#
#      cp my_spectrum.fits input/
#      bash analyze.sh
#
#  This drives pipeline/auto_tune.py, which:
#    1. adapts every spectrum in input/ for the five tools,
#    2. searches each tool's parameter space on a few tuning objects,
#    3. scores every run with the common reduced chi-square,
#    4. refines the winner by coordinate descent,
#    5. re-runs the winning configuration on all objects and writes
#       results/report.html / report.md.
#
#  Useful flags (forwarded to auto_tune.py):
#      --tools pyqsofit badass ...   restrict the search
#      --limit N                     tune on the first N objects (default 3)
#      --rounds N                    coordinate-descent rounds (default 2)
#      --jobs N                      parallel jobs per run (default 4)
#      --dry-run                     print the candidate grid and exit
#      --stage1-only                 skip the final full-quality run
#
#  Python deps: auto_tune.py uses only the .venv interpreter; the fitting tools
#  run through run_pipeline.sh (Docker + local venv) exactly as before.
# =============================================================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
exec "$PYTHON" "$ROOT/pipeline/auto_tune.py" "$@"
