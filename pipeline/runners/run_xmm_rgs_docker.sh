#!/usr/bin/env bash
# XMM-Newton RGS grating line fitting.
#   bash pipeline/runners/run_xmm_rgs_docker.sh <products-dir> <output-dir> [--source-key KEY] [--config DIR]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
[ "$#" -ge 2 ] || { echo "usage: $0 <products-dir> <output-dir> [options]" >&2; exit 2; }
IN="$1"; OUT="$2"; shift 2
CONFIG="${XMM_RGS_CONFIG:-$REPO_ROOT/configs/xmm_rgs/default}"
KEY=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --source-key) KEY="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$OUT"
MOUNTS=(-v "$(realpath "$IN")":/app/input:ro -v "$(realpath "$OUT")":/app/output)
if [ -d "$CONFIG" ]; then CFG=/app/config/config.json; MOUNTS+=(-v "$(realpath "$CONFIG")":/app/config:ro)
else CFG="/app/config/$(basename "$CONFIG")"; MOUNTS+=(-v "$(dirname "$(realpath "$CONFIG")")":/app/config:ro); fi
ARGS=(/opt/conda/bin/python /app/run/run_xmm_rgs.py --input /app/input --output /app/output --config "$CFG")
[ -n "$KEY" ] && ARGS+=(--source-key "$KEY")
# PyXspec only appears on PYTHONPATH after headas-init.sh, so source it first.
exec docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e PFILES=/tmp/pfiles -e MPLCONFIGDIR=/tmp/mpl \
  "${MOUNTS[@]}" xmm_rgs bash -lc 'source "$HEADAS/headas-init.sh" && exec "$@"' _ "${ARGS[@]}"
