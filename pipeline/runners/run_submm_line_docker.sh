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
if [ -d "$IN" ]; then
  MOUNTS=(-v "$(realpath "$IN")":/app/input:ro)
  ARGS=(python /app/run/run_submm_line.py --input /app/input --output /app/output
        --config /app/config/config.json)
else
  MOUNTS=(-v "$(dirname "$(realpath "$IN")")":/app/input:ro)
  ARGS=(python /app/run/run_submm_line.py --input "/app/input/$(basename "$IN")"
        --output /app/output --config /app/config/config.json)
fi
MOUNTS+=(-v "$(realpath "$OUT")":/app/output)
if [ -d "$CONFIG" ]; then
  MOUNTS+=(-v "$(realpath "$CONFIG")":/app/config:ro)
elif [ -f "$CONFIG" ]; then
  MOUNTS+=(-v "$(dirname "$(realpath "$CONFIG")")":/app/config:ro)
  ARGS=(python /app/run/run_submm_line.py --input "${ARGS[3]}" --output /app/output
        --config "/app/config/$(basename "$CONFIG")")
else
  echo "config not found: $CONFIG" >&2; exit 2
fi
[ -n "$LINE" ] && ARGS+=(--line "$LINE")
[ -n "$NCOMP" ] && ARGS+=(--ncomp "$NCOMP")
[ -n "$Z" ] && ARGS+=(--z "$Z")
[ -n "$KEY" ] && ARGS+=(--source-key "$KEY")
exec docker run --rm --user "$(id -u):$(id -g)" -e MPLCONFIGDIR=/tmp/mpl \
  "${MOUNTS[@]}" submm_line "${ARGS[@]}"
