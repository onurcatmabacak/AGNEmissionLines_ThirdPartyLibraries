#!/usr/bin/env bash
# Run PyQSOFit UV in the pyqsofit_uv image.
#   bash pipeline/runners/run_pyqsofit_uv_docker.sh <dir-containing-spectrum.fits> <output-dir>
#
# Production MCMC recipe (see Tools/pyqsofit_uv/README.md):
#   PYQSOFIT_MCMC=1 PYQSOFIT_NSAMP=6000 PYQSOFIT_NBURN=1000 \
#   PYQSOFIT_NTHIN=5 PYQSOFIT_NWALKERS=100 \
#   bash pipeline/runners/run_pyqsofit_uv_docker.sh <input-dir> <output-dir>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
IN="${1:?usage: run_pyqsofit_uv_docker.sh <input-dir> <output-dir>}"
OUT="${2:?usage: run_pyqsofit_uv_docker.sh <input-dir> <output-dir>}"
GIT_COMMIT="${PYQSOFIT_GIT_COMMIT:-$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || true)}"
mkdir -p "$OUT"
exec docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl \
  -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" \
  -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" \
  -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" \
  -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
  -e PYQSOFIT_MC="${PYQSOFIT_MC:-0}" \
  -e PYQSOFIT_MCMC="${PYQSOFIT_MCMC:-0}" \
  -e PYQSOFIT_NSAMP="${PYQSOFIT_NSAMP:-50}" \
  -e PYQSOFIT_NBURN="${PYQSOFIT_NBURN:-20}" \
  -e PYQSOFIT_NTHIN="${PYQSOFIT_NTHIN:-10}" \
  -e PYQSOFIT_NWALKERS="${PYQSOFIT_NWALKERS:-100}" \
  -e PYQSOFIT_MCMC_SEED="${PYQSOFIT_MCMC_SEED:-20240517}" \
  -e PYQSOFIT_MCMC_WORKERS="${PYQSOFIT_MCMC_WORKERS:-1}" \
  -e PYQSOFIT_MCMC_DERIVED_SAMPLES="${PYQSOFIT_MCMC_DERIVED_SAMPLES:-1000}" \
  -e PYQSOFIT_ERR_FLOOR="${PYQSOFIT_ERR_FLOOR:-0}" \
  -e PYQSOFIT_HOST="${PYQSOFIT_HOST:-0}" \
  -e PYQSOFIT_SOURCE_KEY="${PYQSOFIT_SOURCE_KEY:-}" \
  -e PYQSOFIT_GIT_COMMIT="$GIT_COMMIT" \
  -e PYQSOFIT_IMAGE="pyqsofit_uv" \
  -e PYQSOFIT_INPUT="spectrum.fits" \
  -v "$(realpath "$IN")":/app/input:ro \
  -v "$(realpath "$OUT")":/app/output \
  pyqsofit_uv
