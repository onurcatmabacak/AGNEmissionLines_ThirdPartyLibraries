#!/usr/bin/env bash
# =============================================================================
#  analyze.sh -- one command: drop spectra in input/ and get the best fit
# =============================================================================
#
#  By default this runs the PER-OBJECT optimiser (pipeline/per_object_search.py):
#  for every object it evaluates that tool's whole candidate config grid, ranks
#  the runs with the physical objective (chi2_common + line penalties), refines
#  the winner by coordinate descent, and applies each object's winning config
#  in a final pass.  So a config is tuned on the object it is used for, not once
#  for the whole sample.
#
#      cp my_spectrum.fits input/
#      bash analyze.sh                     # per-object search (default)
#      bash analyze.sh --tools pyqsofit gelato --rounds 1
#      bash analyze.sh --dry-run           # print the candidate grid
#      bash analyze.sh --global            # older whole-sample tuning (auto_tune.py)
#
#  Useful flags (forwarded to the chosen driver):
#      --tools A B        restrict tools
#      --limit N          objects used for a global search (auto_tune only)
#      --rounds N         coordinate-descent rounds
#      --pool N           max concurrent fits (per-object driver)
#      --jobs N           parallel jobs per pipeline run
#      --stage1-only      skip the final full-quality run
# =============================================================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

if [[ "${1:-}" == "--global" ]]; then
  shift
  exec "$PYTHON" "$ROOT/pipeline/auto_tune.py" "$@"
fi
exec "$PYTHON" "$ROOT/pipeline/per_object_search.py" "$@"
