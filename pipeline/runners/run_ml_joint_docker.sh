#!/usr/bin/env bash
# Joint multi-instrument 3ML fit.
#   bash pipeline/runners/run_ml_joint_docker.sh <repo-root-mount> <output> [--config ...] [--source-key ...]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
[ "$#" -ge 2 ] || { echo "usage: $0 <repo-root> <output-dir> [options]" >&2; exit 2; }
IN="$1"; OUT="$2"; shift 2
CONFIG="${ML_JOINT_CONFIG:-$REPO_ROOT/configs/ml_joint/pds456}"
KEY=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --source-key) KEY="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$OUT"
MOUNTS=(-v "$(realpath "$IN")":/repo:ro -v "$(realpath "$OUT")":/app/output)
if [ -d "$CONFIG" ]; then CFG=/app/config/config.json; MOUNTS+=(-v "$(realpath "$CONFIG")":/app/config:ro)
else CFG="/app/config/$(basename "$CONFIG")"; MOUNTS+=(-v "$(dirname "$(realpath "$CONFIG")")":/app/config:ro); fi
ARGS=(python /app/run/run_ml_joint.py --input /repo --output /app/output --config "$CFG" --prepare)
[ -n "$KEY" ] && ARGS+=(--source-key "$KEY")
exec docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e MPLCONFIGDIR=/tmp/mpl -e XDG_CONFIG_HOME=/tmp/.config -w /repo \
  "${MOUNTS[@]}" ml_joint "${ARGS[@]}"
