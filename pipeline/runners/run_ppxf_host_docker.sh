#!/usr/bin/env bash
# Run pPXF host decomposition in the ppxf_host image.
#   bash pipeline/runners/run_ppxf_host_docker.sh <dir-containing-spectrum.fits> <output-dir>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN="${1:?usage: run_ppxf_host_docker.sh <input-dir> <output-dir>}"
OUT="${2:?usage: run_ppxf_host_docker.sh <input-dir> <output-dir>}"
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
  ppxf_host --input /app/input/spectrum.fits --output /app/output
