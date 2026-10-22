#!/usr/bin/env bash
# Run the FIR line fitter in the fir_linefit image.
#   bash run_fir_linefit_docker.sh <input.fits> <output-dir> <z>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN="${1:?usage: run_fir_linefit_docker.sh <input.fits> <output-dir> <z>}"
OUT="${2:?usage: run_fir_linefit_docker.sh <input.fits> <output-dir> <z>}"
Z="${3:?usage: run_fir_linefit_docker.sh <input.fits> <output-dir> <z>}"
mkdir -p "$OUT"
exec docker run --rm \
  --user "$(id -u):$(id -g)" -e MPLCONFIGDIR=/tmp/mpl \
  -v "$(realpath "$IN")":/app/input/spectrum.fits:ro \
  -v "$(realpath "$OUT")":/app/output \
  fir_linefit --input /app/input/spectrum.fits --output /app/output --z "$Z"
