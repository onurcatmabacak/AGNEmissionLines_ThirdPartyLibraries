#!/usr/bin/env bash
# Run the S3Fit line/SED fit in the s3fit_line image.
#
#   bash Pipelines/run_s3fit_line_docker.sh <source-dir> <output-dir> [options]
#
# Options:
#   --config DIR       config directory (default: configs/s3fit_line/default)
#   --n-mocks N        Monte-Carlo mock spectra (default from fit_config.json: 10)
#   --mode MODE        spec+sed or spec (default from fit_config.json)
#   --z Z              override systemic redshift
#   --threads N        S3Fit joblib threads (default 1)
#   --seed N           random seed (default 42)
#   --pyqsofit-dir DIR reference pyqsofit_uv output directory
#
# The source directory is the canonical inputs/<source>_z_<z>/ directory.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER="${DOCKER:-docker}"
IMAGE="${S3FIT_IMAGE:-s3fit_line}"

usage() {
  sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

IN=""
OUT=""
CONFIG="$ROOT/configs/s3fit_line/default"
N_MOCKS=""
MODE=""
Z=""
THREADS=""
SEED=""
PYQ=""

while [ $# -gt 0 ]; do
  case "$1" in
    --config)       CONFIG="${2:?--config needs a path}"; shift 2 ;;
    --n-mocks)      N_MOCKS="${2:?--n-mocks needs a number}"; shift 2 ;;
    --mode)         MODE="${2:?--mode needs spec+sed or spec}"; shift 2 ;;
    --z)            Z="${2:?--z needs a value}"; shift 2 ;;
    --threads)      THREADS="${2:?--threads needs a number}"; shift 2 ;;
    --seed)         SEED="${2:?--seed needs a number}"; shift 2 ;;
    --pyqsofit-dir) PYQ="${2:?--pyqsofit-dir needs a path}"; shift 2 ;;
    -h|--help)      usage; exit 0 ;;
    --)             shift; break ;;
    -*)             echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    *)
      if [ -z "$IN" ]; then IN="$1"
      elif [ -z "$OUT" ]; then OUT="$1"
      elif [ -z "$Z" ]; then Z="$1"
      else
        echo "unexpected argument: $1" >&2; usage >&2; exit 2
      fi
      shift ;;
  esac
done

if [ -z "$IN" ] || [ -z "$OUT" ]; then
  usage >&2
  exit 2
fi
IN="$(realpath "$IN")"
OUT="$(realpath -m "$OUT")"
CONFIG="$(realpath "$CONFIG")"
mkdir -p "$OUT"

# Reference PyQSOFit output: sibling pyqsofit_uv by default.
if [ -z "$PYQ" ]; then
  cand="$(dirname "$OUT")/pyqsofit_uv"
  if [ -d "$cand" ]; then PYQ="$cand"; fi
fi

ARGS=(
  --input-dir /app/input
  --out /app/output
)
[ -n "$Z" ] && ARGS+=(--z "$Z")
[ -n "$N_MOCKS" ] && ARGS+=(--n-mocks "$N_MOCKS")
[ -n "$MODE" ] && ARGS+=(--mode "$MODE")
[ -n "$THREADS" ] && ARGS+=(--threads "$THREADS")
[ -n "$SEED" ] && ARGS+=(--seed "$SEED")

MOUNTS=(
  -v "$IN":/app/input:ro
  -v "$OUT":/app/output
)

if [ -d "$CONFIG" ]; then
  MOUNTS+=(-v "$CONFIG":/app/config:ro)
  ARGS+=(--config /app/config)
elif [ -f "$CONFIG" ]; then
  MOUNTS+=(-v "$(dirname "$CONFIG")":/app/config:ro)
  ARGS+=(--config "/app/config/$(basename "$CONFIG")")
else
  echo "config path not found: $CONFIG" >&2
  exit 2
fi

if [ -n "$PYQ" ]; then
  if [ ! -d "$PYQ" ]; then
    echo "PyQSOFit reference directory not found: $PYQ" >&2
    exit 2
  fi
  MOUNTS+=(-v "$(realpath "$PYQ")":/app/reference:ro)
  ARGS+=(--pyqsofit-dir /app/reference)
fi

exec "$DOCKER" run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl \
  -e S3FIT_IMAGE="$IMAGE" \
  "${MOUNTS[@]}" \
  "$IMAGE" "${ARGS[@]}"
