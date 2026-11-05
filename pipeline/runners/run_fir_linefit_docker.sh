#!/usr/bin/env bash
# Run the FIR line fitter in the fir_linefit image.
#   bash pipeline/runners/run_fir_linefit_docker.sh <input.fits|input-dir> <output-dir> <z>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN="${1:?usage: run_fir_linefit_docker.sh <input.fits|dir> <output-dir> <z>}"
OUT="${2:?usage: run_fir_linefit_docker.sh <input.fits|dir> <output-dir> <z>}"
Z="${3:?usage: run_fir_linefit_docker.sh <input.fits|dir> <output-dir> <z> [extra args...]}"
shift 3
mkdir -p "$OUT"
if [ -d "$IN" ]; then
  exec docker run --rm --user "$(id -u):$(id -g)" -e MPLCONFIGDIR=/tmp/mpl -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
    -v "$(realpath "$IN")":/app/input:ro -v "$(realpath "$OUT")":/app/output \
    fir_linefit --input-dir /app/input --output /app/output --z "$Z" "$@"
else
  exec docker run --rm --user "$(id -u):$(id -g)" -e MPLCONFIGDIR=/tmp/mpl -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
    -v "$(realpath "$IN")":/app/input/spectrum.fits:ro \
    -v "$(realpath "$OUT")":/app/output \
    fir_linefit --input /app/input/spectrum.fits --output /app/output --z "$Z" "$@"
fi
