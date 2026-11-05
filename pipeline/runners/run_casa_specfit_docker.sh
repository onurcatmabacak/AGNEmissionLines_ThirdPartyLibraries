#!/usr/bin/env bash
# CASA 6 specfit cross-check of the Gaussian decompositions.
#
#   bash pipeline/runners/run_casa_specfit_docker.sh <cube.fits> <output-dir> \
#        [--config DIR|FILE] [--z Z] [--source-key KEY] [--ncomp N]
#
# The cube is mounted read-only; the CASA image that importfits creates stays in
# the container's /tmp and never reaches the output directory.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"

[ "$#" -ge 2 ] || { echo "usage: $0 <cube.fits> <output-dir> [options]" >&2; exit 2; }
IN="$1"; OUT="$2"; shift 2
CONFIG="${CASA_SPECFIT_CONFIG:-$REPO_ROOT/configs/casa_specfit/default}"
Z=""; KEY=""; NCOMP=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --z) Z="$2"; shift 2 ;;
    --source-key) KEY="$2"; shift 2 ;;
    --ncomp) NCOMP="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$OUT"
# Resolve input and config independently.  An earlier version rebuilt the whole
# argument list inside the config branch, which silently dropped --input and made
# the adapter scan /app/input instead of the file it was given.
if [ -d "$IN" ]; then
  INPUT_ARG=/app/input
  MOUNTS=(-v "$(realpath "$IN")":/app/input:ro)
else
  INPUT_ARG="/app/input/$(basename "$IN")"
  MOUNTS=(-v "$(dirname "$(realpath "$IN")")":/app/input:ro)
fi
if [ -d "$CONFIG" ]; then
  CONFIG_ARG=/app/config/config.json
  MOUNTS+=(-v "$(realpath "$CONFIG")":/app/config:ro)
elif [ -f "$CONFIG" ]; then
  CONFIG_ARG="/app/config/$(basename "$CONFIG")"
  MOUNTS+=(-v "$(dirname "$(realpath "$CONFIG")")":/app/config:ro)
else
  echo "config not found: $CONFIG" >&2; exit 2
fi
MOUNTS+=(-v "$(realpath "$OUT")":/app/output)
ARGS=(python /app/run/run_casa_specfit.py --input "$INPUT_ARG" --output /app/output --config "$CONFIG_ARG")
[ -n "$Z" ] && ARGS+=(--z "$Z")
[ -n "$KEY" ] && ARGS+=(--source-key "$KEY")
[ -n "$NCOMP" ] && ARGS+=(--ncomp "$NCOMP")
exec docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e MPLCONFIGDIR=/tmp/mpl \
  "${MOUNTS[@]}" casa_specfit "${ARGS[@]}"
