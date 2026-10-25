#!/usr/bin/env bash
# Run the cross-band ratio tool in the crossband image.
#   bash Pipelines/run_crossband_docker.sh <input.csv> <output-dir>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN="${1:?usage: run_crossband_docker.sh <input.csv> <output-dir>}"
OUT="${2:?usage: run_crossband_docker.sh <input.csv> <output-dir>}"
mkdir -p "$OUT"
exec docker run --rm --user "$(id -u):$(id -g)" -e MPLCONFIGDIR=/tmp/mpl -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
  -v "$(realpath "$IN")":/app/input/ratios.csv:ro -v "$(realpath "$OUT")":/app/output \
  crossband --input /app/input/ratios.csv --output /app/output
