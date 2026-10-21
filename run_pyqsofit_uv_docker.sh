#!/usr/bin/env bash
# Run PyQSOFit UV in the pyqsofit_uv image.
#   bash run_pyqsofit_uv_docker.sh <dir-containing-spectrum.fits> <output-dir>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN="${1:?usage: run_pyqsofit_uv_docker.sh <input-dir> <output-dir>}"
OUT="${2:?usage: run_pyqsofit_uv_docker.sh <input-dir> <output-dir>}"
mkdir -p "$OUT"
exec docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl \
  -v "$(realpath "$IN")":/app/input:ro \
  -v "$(realpath "$OUT")":/app/output \
  pyqsofit_uv
