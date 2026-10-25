#!/usr/bin/env bash
# Official RXTE/PCA spectral fit runner (HEASoft/PyXspec 13.0.0).
#
#   bash Pipelines/run_rxte_xspec_docker.sh <input-dir> <output-dir> \
#        [--config <config-dir>] [--source-key KEY] [--redshift Z] \
#        [--source-name NAME]
#
# <input-dir> must contain the official HEASARC stdprod PCA products:
#   *_s2.pha.gz   source spectrum (Standard2)
#   *_b2.pha.gz   background model
#   *.rsp.gz      response matrix (5 PCUs summed)
# The input is mounted read-only.  The image is a thin layer on xmm_xspec and
# reuses its XSPEC 13.0.0 / HEASoft 6.37 installation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <input-dir> <output-dir> [--config DIR] [--source-key KEY] [--redshift Z] [--source-name NAME]" >&2
  exit 2
fi

IN="$1"
OUT="$2"
shift 2

CONFIG="${RXTE_XSPEC_CONFIG:-$REPO_ROOT/configs/rxte_xspec/default}"
SOURCE_KEY=""
REDSHIFT=""
SOURCE_NAME=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --source-key) SOURCE_KEY="$2"; shift 2 ;;
    --redshift) REDSHIFT="$2"; shift 2 ;;
    --source-name) SOURCE_NAME="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if [ ! -d "$IN" ]; then
  echo "input directory not found: $IN" >&2
  exit 2
fi
if [ ! -f "$CONFIG/config.json" ]; then
  echo "config must contain config.json: $CONFIG" >&2
  exit 2
fi

mkdir -p "$OUT"
IN="$(realpath "$IN")"
OUT="$(realpath "$OUT")"
CONFIG="$(realpath "$CONFIG")"

if ! docker image inspect rxte_xspec >/dev/null 2>&1; then
  echo "ERROR: Docker image 'rxte_xspec' not found." >&2
  echo "Build it with: bash Pipelines/build_images.sh rxte_xspec" >&2
  echo "The base image 'xmm_xspec' must exist (XSPEC 13.0.0 / HEASoft 6.37)." >&2
  exit 1
fi

IMAGE_SIZE="$(docker image inspect rxte_xspec --format '{{.Size}}' 2>/dev/null || echo 0)"
REPO_COMMIT="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || true)"
if [ -z "$SOURCE_KEY" ]; then
  SOURCE_KEY="$(basename "$(dirname "$OUT")")"
fi

ARGS=(
  python /app/run/run_rxte_xspec.py
  --input-dir /app/input
  --out /app/output
  --config /app/config
  --source-key "$SOURCE_KEY"
)
if [ -n "$REDSHIFT" ]; then ARGS+=(--redshift "$REDSHIFT"); fi
if [ -n "$SOURCE_NAME" ]; then ARGS+=(--source-name "$SOURCE_NAME"); fi

echo "==> RXTE/PCA fit: $IN -> $OUT"
echo "==> image rxte_xspec (${IMAGE_SIZE} bytes), base xmm_xspec"
set +e
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -e PFILES=/tmp/pfiles \
  -e MPLCONFIGDIR=/tmp/mpl \
  -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" \
  -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" \
  -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" \
  -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
  -e RXTE_XSPEC_HOME=/tmp/rxte_xspec_home \
  -e RXTE_XSPEC_IMAGE=rxte_xspec \
  -e RXTE_XSPEC_IMAGE_SIZE="$IMAGE_SIZE" \
  -e RXTE_XSPEC_REPO_COMMIT="$REPO_COMMIT" \
  -v "$IN":/app/input:ro \
  -v "$OUT":/app/output \
  -v "$CONFIG":/app/config:ro \
  rxte_xspec "${ARGS[@]}" 2>&1 | tee "$OUT/run.log"
RC=${PIPESTATUS[0]}
set -e
if [ "$RC" -ne 0 ]; then
  echo "ERROR: rxte_xspec container exited with $RC; see $OUT/run.log" >&2
  exit "$RC"
fi

for f in rxte_fit.csv rxte_lines.csv run.json config.effective.json xspec.log \
         rxte_spectrum_model_residual.png rxte_fe_ka_zoom.png; do
  if [ ! -s "$OUT/$f" ]; then
    echo "ERROR: expected output missing or empty: $OUT/$f" >&2
    exit 1
  fi
done
echo "done: $OUT"
