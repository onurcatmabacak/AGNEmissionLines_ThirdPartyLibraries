#!/usr/bin/env bash
# Run the PyQSOFitSpec bootstrapped line fit in the pyqsofitspec_line image.
#
#   bash Pipelines/run_pyqsofitspec_line_docker.sh <input-dir-or-fits> <output-dir> [options]
#
# Options:
#   --config DIR       config directory (default: configs/pyqsofitspec_line/default)
#   --nboot N          bootstrap realisations (default from config.json: 5)
#   --seed N           random seed (default from config.json)
#   --z Z              override systemic redshift
#   --name NAME        object name used in the figures / run.json
#   --flux-unit UNIT   auto (default), cgs, or 1e-17
#
# <input-dir-or-fits> is normally the prepared PyQSOFit input directory
# (work/prepared/<source_key>/pyqsofit, containing spectrum.fits); the raw SDSS
# COADD file or a directory of spec-*.fits also works.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER="${DOCKER:-docker}"
IMAGE="${PYQSOFITSPEC_IMAGE:-pyqsofitspec_line}"

usage() {
  sed -n '2,17p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

IN=""
OUT=""
CONFIG="$ROOT/configs/pyqsofitspec_line/default"
NBOOT=""
SEED=""
Z=""
NAME=""
FLUX_UNIT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --config)    CONFIG="${2:?--config needs a path}"; shift 2 ;;
    --nboot)     NBOOT="${2:?--nboot needs a number}"; shift 2 ;;
    --seed)      SEED="${2:?--seed needs a number}"; shift 2 ;;
    --z)         Z="${2:?--z needs a value}"; shift 2 ;;
    --name)      NAME="${2:?--name needs a value}"; shift 2 ;;
    --flux-unit) FLUX_UNIT="${2:?--flux-unit needs auto|cgs|1e-17}"; shift 2 ;;
    -h|--help)   usage; exit 0 ;;
    --)          shift; break ;;
    -*)          echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    *)
      if [ -z "$IN" ]; then IN="$1"
      elif [ -z "$OUT" ]; then OUT="$1"
      else echo "unexpected argument: $1" >&2; usage >&2; exit 2
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
# Provenance label: repo-relative when the input lives in this checkout.
IN_LABEL="$IN"
case "$IN" in
  "$ROOT"/*) IN_LABEL="${IN#"$ROOT"/}" ;;
esac
CONFIG="$(realpath "$CONFIG")"
mkdir -p "$OUT"

MOUNTS=(-v "$IN":/app/input:ro -v "$OUT":/app/output)
ARGS=(--input-dir /app/input --out /app/output)

if [ -d "$CONFIG" ]; then
  MOUNTS+=(-v "$CONFIG":/app/config:ro)
elif [ -f "$CONFIG" ]; then
  MOUNTS+=(-v "$(dirname "$CONFIG")":/app/config:ro)
  ARGS+=(--config "/app/config/$(basename "$CONFIG")")
else
  echo "config path not found: $CONFIG" >&2
  exit 2
fi

[ -n "$NBOOT" ]     && ARGS+=(--nboot "$NBOOT")
[ -n "$SEED" ]      && ARGS+=(--seed "$SEED")
[ -n "$Z" ]         && ARGS+=(--z "$Z")
[ -n "$NAME" ]      && ARGS+=(--name "$NAME")
[ -n "$FLUX_UNIT" ] && ARGS+=(--flux-unit "$FLUX_UNIT")

exec "$DOCKER" run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl \
  -e PYQSOFITSPEC_ROOT=/app/pyqsofitspec \
  -e PYQSOFITSPEC_INPUT_HOST="$IN_LABEL" \
  "${MOUNTS[@]}" \
  "$IMAGE" "${ARGS[@]}"
