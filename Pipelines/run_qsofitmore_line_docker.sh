#!/usr/bin/env bash
# Run QSOFITMORE (pinned upstream, lmfit backend) in the qsofitmore_line image.
#
#   bash Pipelines/run_qsofitmore_line_docker.sh <input-dir-or-fits> <output-dir> \
#        [--config <config-dir>] [--mc-trails N] [--seed N] [--name NAME] [--no-systematics]
#
# The input may be a directory containing a prepared `spectrum.fits`, a raw
# SDSS `spec-*.fits`, or a single FITS file.  The default MC is 200
# realizations; the package's native uncertainty mode is the lmfit Monte Carlo
# refit (qsofitmore 1.2.2 has no emcee/MCMC sampler).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <input-dir-or-fits> <output-dir> [--config DIR] [--mc-trails N] [--seed N] [--name NAME] [--no-systematics]" >&2
  exit 2
fi

IN="$1"
OUT="$2"
shift 2

CONFIG="${QSOFITMORE_CONFIG:-$REPO_ROOT/configs/qsofitmore_line/default}"
MC_TRAILS="${QSOFITMORE_MC_TRAILS:-200}"
SEED="${QSOFITMORE_SEED:-20250101}"
NAME="${QSOFITMORE_NAME:-}"
SOURCE_KEY="${QSOFITMORE_SOURCE_KEY:-}"
REDSHIFT="${QSOFITMORE_Z:-}"
NO_SYSTEMATICS="${QSOFITMORE_NO_SYSTEMATICS:-0}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --mc-trails) MC_TRAILS="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    --source-key) SOURCE_KEY="$2"; shift 2 ;;
    --z) REDSHIFT="$2"; shift 2 ;;
    --no-systematics) NO_SYSTEMATICS=1; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if [ -d "$IN" ]; then
  INPUT_DIR="$(realpath "$IN")"
  INPUT_FILE=""
  INPUT_ARG=(--input-dir /app/input)
elif [ -f "$IN" ]; then
  INPUT_DIR="$(realpath "$(dirname "$IN")")"
  INPUT_FILE="$(basename "$IN")"
  INPUT_ARG=(--input-dir /app/input --input-file "$INPUT_FILE")
else
  echo "input not found: $IN" >&2
  exit 2
fi

if [ ! -f "$CONFIG/config.json" ] || [ ! -f "$CONFIG/line_table.csv" ]; then
  echo "config must contain config.json and line_table.csv: $CONFIG" >&2
  exit 2
fi

mkdir -p "$OUT"
OUT="$(realpath "$OUT")"
source "$(dirname "${BASH_SOURCE[0]}")/_output_layout.sh"
output_layout_resolve "$OUT"
CONFIG="$(realpath "$CONFIG")"

if ! docker image inspect qsofitmore_line >/dev/null 2>&1; then
  echo "ERROR: Docker image 'qsofitmore_line' not found." >&2
  echo "Build it with: bash Pipelines/build_images.sh qsofitmore_line" >&2
  exit 1
fi

IMAGE_SIZE="$(docker image inspect qsofitmore_line --format '{{.Size}}' 2>/dev/null || echo 0)"
REPO_COMMIT="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || true)"
UPSTREAM_COMMIT="${QSOFITMORE_COMMIT:-4c5f6e497b306aaf50b502a8e4b27ed9dfe89421}"

if [ -z "$SOURCE_KEY" ]; then
  SOURCE_KEY="$OUT_SOURCE"
fi

ARGS=(
  python /app/run/main.py
  "${INPUT_ARG[@]}"
  --out /app/output
  --config /app/config
  --mc-trails "$MC_TRAILS"
  --seed "$SEED"
  --source-key "$SOURCE_KEY"
)
if [ -n "$NAME" ]; then
  ARGS+=(--name "$NAME")
fi
if [ -n "$REDSHIFT" ]; then
  ARGS+=(--z "$REDSHIFT")
fi
if [ "$NO_SYSTEMATICS" = "1" ]; then
  ARGS+=(--no-systematics)
fi

exec docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl \
  -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" \
  -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" \
  -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" \
  -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
  -e HOME=/tmp \
  -e QSOFITMORE_IMAGE=qsofitmore_line \
  -e QSOFITMORE_IMAGE_SIZE="$IMAGE_SIZE" \
  -e QSOFITMORE_COMMIT="$UPSTREAM_COMMIT" \
  -e QSOFITMORE_REPO_COMMIT="$REPO_COMMIT" \
  -e QSOFITMORE_SOURCE_KEY="$SOURCE_KEY" \
  -v "$INPUT_DIR":/app/input:ro \
  -v "$OUT":/app/output \
  -v "$CONFIG":/app/config:ro \
  qsofitmore_line \
  "${ARGS[@]}"
