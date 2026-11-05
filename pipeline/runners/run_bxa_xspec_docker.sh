#!/usr/bin/env bash
# BXA (Bayesian X-ray Analysis) evidence comparison for XMM-Newton EPIC data.
#
#   bash pipeline/runners/run_bxa_xspec_docker.sh <xmm-dir> <output-dir> \
#        [--config DIR] [--redshift Z] [--source-key KEY] [--models a,b] \
#        [--n-live N] [--dlogz D]
#
# <xmm-dir> is the ObsID directory containing pps/PN, pps/MOS1, pps/MOS2 and
# the response files, exactly as for run_xmm_xspec_docker.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <xmm-dir> <output-dir> [--config DIR] [--redshift Z] [--source-key KEY] [--models LIST] [--n-live N] [--dlogz D]" >&2
  exit 2
fi

IN="$1"; OUT="$2"; shift 2
CONFIG="${BXA_CONFIG:-$REPO_ROOT/configs/bxa_xspec/default}"
REDSHIFT=""; SOURCE_KEY=""; MODELS=""; NLIVE=""; DLOGZ=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --redshift) REDSHIFT="$2"; shift 2 ;;
    --source-key) SOURCE_KEY="$2"; shift 2 ;;
    --models) MODELS="$2"; shift 2 ;;
    --n-live) NLIVE="$2"; shift 2 ;;
    --dlogz) DLOGZ="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$OUT"
MOUNTS=(-v "$(realpath "$IN")":/app/input:ro -v "$(realpath "$OUT")":/app/output)
ARGS=(python /app/run/run_bxa_xspec.py --input /app/input --output /app/output --config /app/config/config.json)

if [ -d "$CONFIG" ]; then
  MOUNTS+=(-v "$(realpath "$CONFIG")":/app/config:ro)
elif [ -f "$CONFIG" ]; then
  MOUNTS+=(-v "$(dirname "$(realpath "$CONFIG")")":/app/config:ro)
  ARGS=(python /app/run/run_bxa_xspec.py --input /app/input --output /app/output --config "/app/config/$(basename "$CONFIG")")
else
  echo "config not found: $CONFIG" >&2
  exit 2
fi

[ -n "$REDSHIFT" ] && ARGS+=(--z "$REDSHIFT")
[ -n "$SOURCE_KEY" ] && ARGS+=(--source-key "$SOURCE_KEY")
[ -n "$MODELS" ] && ARGS+=(--models "$MODELS")
[ -n "$NLIVE" ] && ARGS+=(--n-live "$NLIVE")
[ -n "$DLOGZ" ] && ARGS+=(--dlogz "$DLOGZ")

exec docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" \
  -e MPLCONFIGDIR=/tmp/mpl \
  "${MOUNTS[@]}" \
  bxa_xspec "${ARGS[@]}"
