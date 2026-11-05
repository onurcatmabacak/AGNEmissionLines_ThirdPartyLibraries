#!/usr/bin/env bash
# Spatially resolved line fitting on a spectral cube.
#
#   bash pipeline/runners/run_cube_lines_docker.sh <cube.fits> <output-dir> \
#        [--config DIR|FILE] [--z Z] [--source-key KEY] [--plot]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
[ "$#" -ge 2 ] || { echo "usage: $0 <cube.fits> <output-dir> [options]" >&2; exit 2; }
IN="$1"; OUT="$2"; shift 2
CONFIG="${CUBE_LINES_CONFIG:-$REPO_ROOT/configs/cube_lines/default}"
Z=""; KEY=""; PLOT=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --z) Z="$2"; shift 2 ;;
    --source-key) KEY="$2"; shift 2 ;;
    --plot) PLOT="--plot"; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$OUT"
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
ARGS=(python /app/run/run_cube_lines.py --input "$INPUT_ARG" --output /app/output --config "$CONFIG_ARG")
[ -n "$Z" ] && ARGS+=(--z "$Z")
[ -n "$KEY" ] && ARGS+=(--source-key "$KEY")
[ -n "$PLOT" ] && ARGS+=("$PLOT")
exec docker run --rm --user "$(id -u):$(id -g)" -e MPLCONFIGDIR=/tmp/mpl \
  "${MOUNTS[@]}" cube_lines "${ARGS[@]}"
