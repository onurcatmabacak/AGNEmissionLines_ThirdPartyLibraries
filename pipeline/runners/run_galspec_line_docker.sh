#!/usr/bin/env bash
# Run the GalSpec full-continuum QSO emission-line fit in the galspec_line image.
#
#   bash pipeline/runners/run_galspec_line_docker.sh <source-dir> <output-dir> [options]
#
# Options:
#   --config DIR       config directory or JSON file (default: configs/galspec_line/default,
#                      which selects the full-continuum model)
#   --sampler MODE     mcmc (default), nested (dynesty) or lsq
#   --z Z              override systemic redshift
#   --object KEY       provenance label (source key)
#   --mcmc-steps N     override emcee steps (full production: 4000)
#   --nwalkers N       override emcee walkers (full production: 80, auto-raised to 2*ndim+2)
#   --nburn N          override emcee burn-in
#   --seed N           random seed
#
# The source directory is the canonical inputs/<source>_z_<z>/ directory or a
# directory containing spectrum.fits.  The output directory is mounted at
# /app/output; nothing is written into the input directory.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCKER="${DOCKER:-docker}"
IMAGE="${GALSPEC_IMAGE:-galspec_line}"

usage() {
  sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

IN=""
OUT=""
CONFIG="$ROOT/configs/galspec_line/default"
SAMPLER=""
Z=""
OBJECT=""
MCMC_STEPS=""
NWALKERS=""
NBURN=""
SEED=""

while [ $# -gt 0 ]; do
  case "$1" in
    --config)      CONFIG="${2:?--config needs a path}"; shift 2 ;;
    --sampler)     SAMPLER="${2:?--sampler needs mcmc|nested|lsq}"; shift 2 ;;
    --z)           Z="${2:?--z needs a value}"; shift 2 ;;
    --object)      OBJECT="${2:?--object needs a value}"; shift 2 ;;
    --mcmc-steps)  MCMC_STEPS="${2:?--mcmc-steps needs a number}"; shift 2 ;;
    --nwalkers)    NWALKERS="${2:?--nwalkers needs a number}"; shift 2 ;;
    --nburn)       NBURN="${2:?--nburn needs a number}"; shift 2 ;;
    --seed)        SEED="${2:?--seed needs a number}"; shift 2 ;;
    -h|--help)     usage; exit 0 ;;
    --)            shift; break ;;
    -*)            echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
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
CONFIG="$(realpath "$CONFIG")"
mkdir -p "$OUT"

ARGS=(--output /app/output)
if [ -d "$IN" ]; then
  MOUNTS=(-v "$IN":/app/input:ro)
  ARGS+=(--input /app/input)
else
  MOUNTS=(-v "$(dirname "$IN")":/app/input:ro)
  ARGS+=(--input "/app/input/$(basename "$IN")")
fi
MOUNTS+=(-v "$OUT":/app/output)

# Sibling tool outputs for the same source live under the same outputs/ root
# (outputs/<tool>/<source>/).  Mount that read-only so galspec_comparison.csv
# and the reference runtimes are built without writing outside OUT.
source "$(dirname "${BASH_SOURCE[0]}")/_output_layout.sh"
output_layout_resolve "$OUT"
REF="$OUT_REFS"
MOUNTS+=(-v "$REF":/app/references:ro)
ARGS+=(--reference-dir /app/references)

if [ -d "$CONFIG" ]; then
  MOUNTS+=(-v "$CONFIG":/app/config:ro)
  ARGS+=(--config /app/config)
elif [ -f "$CONFIG" ]; then
  MOUNTS+=(-v "$(dirname "$CONFIG")":/app/config:ro)
  ARGS+=(--config "/app/config/$(basename "$CONFIG")")
else
  echo "config path not found: $CONFIG" >&2
  exit 2
fi

[ -n "$SAMPLER" ] && ARGS+=(--sampler "$SAMPLER")
[ -n "$Z" ] && ARGS+=(--z "$Z")
[ -n "$OBJECT" ] && ARGS+=(--object "$OBJECT")
[ -n "$MCMC_STEPS" ] && ARGS+=(--mcmc-steps "$MCMC_STEPS")
[ -n "$NWALKERS" ] && ARGS+=(--nwalkers "$NWALKERS")
[ -n "$NBURN" ] && ARGS+=(--nburn "$NBURN")
[ -n "$SEED" ] && ARGS+=(--seed "$SEED")

exec "$DOCKER" run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl \
  -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" \
  -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" \
  -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" \
  -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
  -e GALSPEC_IMAGE="$IMAGE" \
  "${MOUNTS[@]}" \
  "$IMAGE" "${ARGS[@]}"
