#!/usr/bin/env bash
# Run PyQSOFit UV in the pyqsofit_uv image.
#   bash Pipelines/run_pyqsofit_uv_docker.sh <dir-containing-spectrum.fits> <output-dir>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN="${1:?usage: run_pyqsofit_uv_docker.sh <input-dir> <output-dir>}"
OUT="${2:?usage: run_pyqsofit_uv_docker.sh <input-dir> <output-dir>}"
mkdir -p "$OUT"
exec docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl \
  -e PYQSOFIT_MC="${PYQSOFIT_MC:-0}" \
  -e PYQSOFIT_MCMC="${PYQSOFIT_MCMC:-0}" \
  -e PYQSOFIT_NSAMP="${PYQSOFIT_NSAMP:-50}" \
  -e PYQSOFIT_ERR_FLOOR="${PYQSOFIT_ERR_FLOOR:-0}" \
  -e PYQSOFIT_HOST="${PYQSOFIT_HOST:-0}" \
  -v "$(realpath "$IN")":/app/input:ro \
  -v "$(realpath "$OUT")":/app/output \
  pyqsofit_uv
