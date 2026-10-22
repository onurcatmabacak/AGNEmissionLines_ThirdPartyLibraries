#!/usr/bin/env bash
# Run PAHFIT on JWST/MIRI x1d spectra in the pahfit_mir image.
#   bash run_pahfit_mir_docker.sh <input-dir> <output-dir> <z>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN="${1:?usage: run_pahfit_mir_docker.sh <input-dir> <output-dir> <z>}"
OUT="${2:?usage: run_pahfit_mir_docker.sh <input-dir> <output-dir> <z>}"
Z="${3:?usage: run_pahfit_mir_docker.sh <input-dir> <output-dir> <z> [extra args...]}"
shift 3
mkdir -p "$OUT"
exec docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl \
  -v "$(realpath "$IN")":/app/input:ro \
  -v "$(realpath "$OUT")":/app/output \
  pahfit_mir --input /app/input --output /app/output --z "$Z" "$@"
