#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IN="${1:?usage: run_optical_linefit_docker.sh <fits> <output> --z Z [--name NAME]}"
OUT="${2:?}"
shift 2
mkdir -p "$OUT"
exec docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
  -e MPLCONFIGDIR=/tmp/mpl -e HOME=/tmp \
  -v "$(realpath "$(dirname "$IN")")":/app/input:ro \
  -v "$(realpath "$OUT")":/app/output \
  optical_linefit \
  --fits "/app/input/$(basename "$IN")" --out /app/output "$@"
