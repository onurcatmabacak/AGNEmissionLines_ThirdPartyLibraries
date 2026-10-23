#!/usr/bin/env bash
# Run the native GANDALF v1.5 (GDL) line fit in the gandalf_line image.
#   bash Pipelines/run_gandalf_line_docker.sh <dir-containing-spectrum.fits> <output-dir>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IN="${1:?usage: run_gandalf_line_docker.sh <input-dir> <output-dir>}"
OUT="${2:?usage: run_gandalf_line_docker.sh <input-dir> <output-dir> [object]}"
OBJ="${3:-}"
EXTRA=()
if [ -n "$OBJ" ]; then EXTRA=(-e "GANDALF_OBJECT=$OBJ"); fi
mkdir -p "$OUT"
exec docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl "${EXTRA[@]}" \
  -v "$(realpath "$IN")":/app/input:ro \
  -v "$(realpath "$OUT")":/app/output \
  gandalf_line --input /app/input/spectrum.fits --output /app/output
