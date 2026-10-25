#!/usr/bin/env bash
# Run the NIR line tool in the nir_linefit image.
#   bash Pipelines/run_nir_linefit_docker.sh <input-dir> <output-dir> [z]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN="${1:?usage: run_nir_linefit_docker.sh <input-dir> <output-dir> [z]}"
OUT="${2:?usage: run_nir_linefit_docker.sh <input-dir> <output-dir> [z]}"
Z="${3:-}"
mkdir -p "$OUT"
exec docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl \
  -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" \
  -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" \
  -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" \
  -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
  -v "$(realpath "$IN")":/app/input:ro \
  -v "$(realpath "$OUT")":/app/output \
  nir_linefit --input-dir /app/input --out /app/output ${Z:+--z "$Z"}
