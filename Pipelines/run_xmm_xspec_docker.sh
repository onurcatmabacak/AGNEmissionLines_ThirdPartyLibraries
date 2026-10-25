#!/usr/bin/env bash
# Official XMM-Newton EPIC PPS spectral fit with HEASoft/PyXspec.
#
#   bash Pipelines/run_xmm_xspec_docker.sh <xmm-dir> <output-dir> \
#        [--config <config-dir>] [--redshift Z] [--source-key KEY] [--obsid ID]
#
# <xmm-dir> is the ObsID directory containing:
#   pps/PN/*PNS003SRSPEC0001.fits   pps/PN/*PNS003BGSPEC0001.fits
#   pps/PN/*PNS003SRCARF0001.fits   pps/MOS1/*M1S001...   pps/MOS2/*M2S002...
#   responses/epn_*.rmf  responses/m1_*.rmf  responses/m2_*.rmf
#
# The input is mounted read-only.  The output receives the figures, CSVs,
# run.json, config.effective.json, prepared spectra and the XSPEC log.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <xmm-dir> <output-dir> [--config DIR] [--redshift Z] [--source-key KEY] [--obsid ID]" >&2
  exit 2
fi

IN="$1"
OUT="$2"
shift 2

CONFIG="${XMM_XSPEC_CONFIG:-$REPO_ROOT/configs/xmm_xspec/default}"
REDSHIFT=""
SOURCE_KEY="${XMM_XSPEC_SOURCE_KEY:-}"
OBSID=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --redshift) REDSHIFT="$2"; shift 2 ;;
    --source-key) SOURCE_KEY="$2"; shift 2 ;;
    --obsid) OBSID="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if [ ! -d "$IN" ]; then
  echo "input directory not found: $IN" >&2
  exit 2
fi
if [ ! -d "$IN/pps/PN" ] || [ ! -d "$IN/responses" ]; then
  echo "input must contain pps/PN and responses/: $IN" >&2
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

if ! docker image inspect xmm_xspec >/dev/null 2>&1; then
  echo "ERROR: Docker image 'xmm_xspec' not found." >&2
  echo "Build it with: bash Pipelines/build_images.sh xmm_xspec" >&2
  exit 1
fi

IMAGE_SIZE="$(docker image inspect xmm_xspec --format '{{.Size}}' 2>/dev/null || echo 0)"
REPO_COMMIT="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || true)"
if [ -z "$SOURCE_KEY" ]; then
  SOURCE_KEY="$(basename "$(dirname "$OUT")")"
fi

RUN_ARGS=(
  python /app/run/run_xmm_xspec.py
  --input-dir /app/input
  --out /app/output
  --config /app/config
  --source-key "$SOURCE_KEY"
)
if [ -n "$REDSHIFT" ]; then RUN_ARGS+=(--redshift "$REDSHIFT"); fi
if [ -n "$OBSID" ]; then RUN_ARGS+=(--obsid "$OBSID"); fi

echo "==> XMM-Newton PPS + PyXspec"
echo "    input : $IN"
echo "    output: $OUT"
echo "    config: $CONFIG"
echo "    image : xmm_xspec (${IMAGE_SIZE} bytes)"

set +e
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp/xmm_xspec_home \
  -e MPLCONFIGDIR=/tmp/mpl \
  -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" \
  -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" \
  -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" \
  -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
  -e PFILES=/tmp/pfiles \
  -e HEADAS=/opt/conda/heasoft \
  -e LHEA_DATA=/opt/conda/heasoft/refdata \
  -e XMM_XSPEC_IMAGE_SIZE="$IMAGE_SIZE" \
  -e XMM_XSPEC_REPO_COMMIT="$REPO_COMMIT" \
  -e XMM_XSPEC_SOURCE_KEY="$SOURCE_KEY" \
  -v "$IN":/app/input:ro \
  -v "$OUT":/app/output \
  -v "$CONFIG":/app/config:ro \
  xmm_xspec \
  "${RUN_ARGS[@]}" 2>&1 | tee "$OUT/xspec.log"
rc=${PIPESTATUS[0]}
set -e

if [ "$rc" -ne 0 ]; then
  echo "xmm_xspec failed (rc=$rc); see $OUT/xspec.log" >&2
  exit "$rc"
fi
echo "done: $OUT"
