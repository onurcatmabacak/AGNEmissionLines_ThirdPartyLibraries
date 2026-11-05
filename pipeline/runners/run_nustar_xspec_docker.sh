#!/usr/bin/env bash
# NuSTAR hard X-ray fitting (nuproducts + PyXspec).
#   bash pipeline/runners/run_nustar_xspec_docker.sh <event-dir> <output-dir> [--config DIR] [--source-key KEY]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
[ "$#" -ge 2 ] || { echo "usage: $0 <event-dir> <output-dir> [options]" >&2; exit 2; }
IN="$1"; OUT="$2"; shift 2
CONFIG="${NUSTAR_CONFIG:-$REPO_ROOT/configs/nustar_xspec/default}"
KEY=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --source-key) KEY="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$OUT"
CALDB_DIR="${NUSTAR_CALDB:-/tmp/nustar_caldb}"
if [ ! -s "$CALDB_DIR/data/nustar/fpm/caldb.indx" ]; then
  echo "NuSTAR CALDB not found at $CALDB_DIR (set NUSTAR_CALDB)." >&2
  echo "Fetch it once with:" >&2
  echo "  curl -fsSL https://heasarc.gsfc.nasa.gov/FTP/caldb/data/nustar/fpm/goodfiles_nustar_fpm_20261102.tar.gz \\" >&2
  echo "    | tar xz -C \$NUSTAR_CALDB" >&2
  exit 2
fi
MOUNTS=(-v "$(realpath "$IN")":/app/input:ro -v "$(realpath "$OUT")":/app/output
        -v "$(realpath "$CALDB_DIR")":/opt/caldb:ro)
if [ -d "$CONFIG" ]; then CFG=/app/config/config.json; MOUNTS+=(-v "$(realpath "$CONFIG")":/app/config:ro)
else CFG="/app/config/$(basename "$CONFIG")"; MOUNTS+=(-v "$(dirname "$(realpath "$CONFIG")")":/app/config:ro); fi
ARGS=(/app/run/run_nustar_xspec.py --input /app/input --output /app/output --config "$CFG")
[ -n "$KEY" ] && ARGS+=(--source-key "$KEY")
exec docker run --rm -t --user "$(id -u):$(id -g)" -e HOME=/tmp -e PFILES=/tmp/pfiles \
  "${MOUNTS[@]}" nustar_xspec bash -lc 'source "$HEADAS/headas-init.sh" && exec /opt/conda/bin/python "$@"' _ "${ARGS[@]}"
