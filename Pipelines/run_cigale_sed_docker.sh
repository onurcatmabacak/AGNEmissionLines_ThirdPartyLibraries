#!/usr/bin/env bash
# Run the CIGALE SED/torus fit in the cigale_sed image.
#   bash Pipelines/run_cigale_sed_docker.sh <photometry-dir> <output-dir>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN="${1:?usage: run_cigale_sed_docker.sh <photometry-dir> <output-dir>}"
OUT="${2:?usage: run_cigale_sed_docker.sh <photometry-dir> <output-dir>}"
mkdir -p "$OUT"
exec docker run --rm --user "$(id -u):$(id -g)" -e MPLCONFIGDIR=/tmp/mpl -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
  -e CIGALE_AGN_MODEL="${CIGALE_AGN_MODEL:-skirtor2016}" \
  -v "$(realpath "$IN")":/app/input:ro -v "$(realpath "$OUT")":/app/output \
  cigale_sed
