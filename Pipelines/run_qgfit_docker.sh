#!/usr/bin/env bash
# Run QGfit in the qgfit image.
#
#   bash Pipelines/run_qgfit_docker.sh <source-dir-or-fits> <output-dir> [options]
#
# Options:
#   --config DIR       config directory (default: configs/qgfit/default)
#   --z Z              override systemic redshift
#   --reference DIR    directory of sibling tool outputs (default: auto-detect
#                      pyqsofit_uv, gandalf_line, s3fit_line, galspec_line and
#                      pyqsofitspec_line next to OUT)
#   --name NAME        QGfit output stem (default: qgfit)
#   --sfd-dir DIR      mount a directory with sfdmap FITS files at /opt/sfd
#
# The input may be the canonical inputs/<source>_z_<z>/ directory (the runner
# searches recursively for spec-*.fits) or a single FITS file.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER="${DOCKER:-docker}"
IMAGE="${QGFIT_IMAGE:-qgfit}"

usage() {
  sed -n '2,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

IN=""
OUT=""
CONFIG="$ROOT/configs/qgfit/default"
Z=""
REF=""
NAME=""
SFD_DIR=""

while [ $# -gt 0 ]; do
  case "$1" in
    --config)     CONFIG="${2:?--config needs a path}"; shift 2 ;;
    --z)          Z="${2:?--z needs a value}"; shift 2 ;;
    --reference)  REF="${2:?--reference needs a path}"; shift 2 ;;
    --name)       NAME="${2:?--name needs a value}"; shift 2 ;;
    --sfd-dir)    SFD_DIR="${2:?--sfd-dir needs a path}"; shift 2 ;;
    -h|--help)    usage; exit 0 ;;
    --)           shift; break ;;
    -*)           echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    *)
      if [ -z "$IN" ]; then IN="$1"
      elif [ -z "$OUT" ]; then OUT="$1"
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
source "$(dirname "${BASH_SOURCE[0]}")/_output_layout.sh"
output_layout_resolve "$OUT"

MOUNTS=(
  -v "$IN":/app/input:ro
  -v "$OUT":/app/output
)
ARGS=(
  --input /app/input
  --output /app/output
  --config /app/config/config.json
)
[ -n "$Z" ] && ARGS+=(--z "$Z")
[ -n "$NAME" ] && ARGS+=(--name "$NAME")

if [ -d "$CONFIG" ]; then
  MOUNTS+=(-v "$CONFIG":/app/config:ro)
elif [ -f "$CONFIG" ]; then
  MOUNTS+=(-v "$(dirname "$CONFIG")":/app/config:ro)
  ARGS+=(--config "/app/config/$(basename "$CONFIG")")
else
  echo "config path not found: $CONFIG" >&2
  exit 2
fi

# Reference tables: sibling outputs by default.
if [ -z "$REF" ]; then
  mkdir -p "$OUT"

  ref_mounted=0
  for tool in pyqsofit_uv gandalf_line s3fit_line galspec_line pyqsofitspec_line; do
    cand="$(output_ref_dir "$tool")"
    if [ -d "$cand" ]; then
      MOUNTS+=(-v "$(realpath "$cand")":/app/reference/$tool:ro)
      ref_mounted=1
    fi
  done
  if [ "$ref_mounted" -eq 1 ]; then
    ARGS+=(--reference /app/reference)
  fi
else
  MOUNTS+=(-v "$(realpath "$REF")":/app/reference:ro)
  ARGS+=(--reference /app/reference)
fi

if [ -n "$SFD_DIR" ]; then
  MOUNTS+=(-v "$(realpath "$SFD_DIR")":/opt/sfd:ro)
fi

exec "$DOCKER" run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl \
  -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" \
  -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" \
  -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" \
  -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
  -e SFD_PATH=/opt/sfd \
  "${MOUNTS[@]}" \
  "$IMAGE" "${ARGS[@]}"
