#!/usr/bin/env bash
# Sub-mm spectral-line fitting with McFine.
#   bash pipeline/runners/run_submm_line_docker.sh <input> <output-dir> \
#        [--config DIR|FILE] [--line NAME] [--ncomp N] [--z Z] [--source-key KEY]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
[ "$#" -ge 2 ] || { echo "usage: $0 <input> <output-dir> [options]" >&2; exit 2; }
IN="$1"; OUT="$2"; shift 2
CONFIG="${SUBMM_LINE_CONFIG:-$REPO_ROOT/configs/submm_line/default}"
LINE=""; NCOMP=""; Z=""; KEY=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --line) LINE="$2"; shift 2 ;;
    --ncomp) NCOMP="$2"; shift 2 ;;
    --z) Z="$2"; shift 2 ;;
    --source-key) KEY="$2"; shift 2 ;;
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
ARGS=(python /app/run/run_submm_line.py --input "$INPUT_ARG" --output /app/output --config "$CONFIG_ARG")
[ -n "$LINE" ] && ARGS+=(--line "$LINE")
[ -n "$NCOMP" ] && ARGS+=(--ncomp "$NCOMP")
[ -n "$Z" ] && ARGS+=(--z "$Z")
[ -n "$KEY" ] && ARGS+=(--source-key "$KEY")
exec docker run --rm --user "$(id -u):$(id -g)" -e MPLCONFIGDIR=/tmp/mpl \
  "${MOUNTS[@]}" submm_line "${ARGS[@]}"
