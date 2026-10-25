#!/usr/bin/env bash
# Official SDSS MaNGA DAP production runner (sdss-mangadap 4.5.0).
#
# Default (accepted) mode: official DAP Stage A (rdxqa + HYB10/S/N=50 binning
# + pPXF + EMOM + INDXEN) followed by the official full-method SASUKE
# emission-line fit on the 9 central single-spaxel bins.  The published DAP
# MAPS is the all-spaxel reference.
#
#   bash Pipelines/run_manga_dap_docker.sh <input-dir> <output-dir> \
#        [--reference <published-MAPS.fits.gz>] [--config <config-dir>] \
#        [--n-bins 9] [--fast]
#
# --fast runs the auxiliary fixed-continuum all-spaxel mode (flag
# FASTMODE_NOT_PRODUCTION); it is NOT an accepted production result.
#
# <input-dir> must contain raw/manga-<plate>-<ifu>-LOGCUBE.fits.gz (and
# preferably the matching LOGRSS).  The input is mounted read-only.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <input-dir> <output-dir> [--reference MAPS] [--config DIR] [--n-bins N] [--fast]" >&2
  exit 2
fi

IN="$1"
OUT="$2"
shift 2

CONFIG="${MANGA_DAP_CONFIG:-$REPO_ROOT/configs/manga_dap/default}"
REFERENCE="${MANGA_DAP_REFERENCE:-}"
MODE=subset
NBINS=9
SOURCE_KEY="${MANGA_DAP_SOURCE_KEY:-}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --reference) REFERENCE="$2"; shift 2 ;;
    --config) CONFIG="$2"; shift 2 ;;
    --n-bins) NBINS="$2"; shift 2 ;;
    --fast) MODE=fast; shift ;;
    --full) MODE=full; shift ;;
    --subset) MODE=subset; shift ;;
    --source-key) SOURCE_KEY="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if [ ! -d "$IN" ]; then
  echo "input directory not found: $IN" >&2
  exit 2
fi
if [ ! -f "$CONFIG/config.json" ] || [ ! -f "$CONFIG/plan_moments.toml" ]; then
  echo "config must contain config.json and plan_moments.toml: $CONFIG" >&2
  exit 2
fi
if [ "$MODE" = "subset" ] && [ ! -f "$CONFIG/plan_subset.toml" ]; then
  echo "subset mode requires $CONFIG/plan_subset.toml" >&2
  exit 2
fi
if { [ "$MODE" = "fast" ] || [ "$MODE" = "full" ]; } && [ ! -f "$CONFIG/plan.toml" ]; then
  echo "$MODE mode requires $CONFIG/plan.toml" >&2
  exit 2
fi

mkdir -p "$OUT"
IN="$(realpath "$IN")"
OUT="$(realpath "$OUT")"
CONFIG="$(realpath "$CONFIG")"

if ! docker image inspect manga_dap >/dev/null 2>&1; then
  echo "ERROR: Docker image 'manga_dap' not found." >&2
  echo "Build it with: bash Pipelines/build_images.sh manga_dap" >&2
  exit 1
fi

IMAGE_SIZE="$(docker image inspect manga_dap --format '{{.Size}}' 2>/dev/null || echo 0)"
REPO_COMMIT="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || true)"
if [ -z "$SOURCE_KEY" ]; then
  SOURCE_KEY="$(basename "$(dirname "$OUT")")"
fi

REF_MOUNT=()
REF_ARG=()
if [ -n "$REFERENCE" ]; then
  REFERENCE="$(realpath "$REFERENCE")"
  if [ ! -f "$REFERENCE" ]; then
    echo "reference MAPS not found: $REFERENCE" >&2
    exit 2
  fi
  REF_MOUNT=(-v "$(dirname "$REFERENCE")":/app/reference:ro)
  REF_ARG=(--reference "/app/reference/$(basename "$REFERENCE")")
fi

COMMON_DOCKER=(
  docker run --rm
  --user "$(id -u):$(id -g)"
  -e HOME=/tmp
  -e MPLCONFIGDIR=/tmp/mpl
  -e OPENBLAS_NUM_THREADS=1
  -e OMP_NUM_THREADS=1
  -e MANGA_DAP_NPROC="${MANGA_DAP_NPROC:-8}"
  -e MANGA_DAP_IMAGE=manga_dap
  -e MANGA_DAP_IMAGE_SIZE="$IMAGE_SIZE"
  -e MANGA_DAP_REPO_COMMIT="$REPO_COMMIT"
  -v "$IN":/app/input:ro
  -v "$OUT":/app/output
  -v "$CONFIG":/app/config:ro
  "${REF_MOUNT[@]}"
  manga_dap
)

if [ "$MODE" = "full" ]; then
  echo "==> Official full DAP: S/N=10 binning, all spaxels, SASUKE all bins"
  RUN_ARGS=(
    python /app/run/run_manga_dap.py
    --input-dir /app/input
    --out /app/output
    --config /app/config
    --source-key "$SOURCE_KEY"
  )
  if [ ${#REF_ARG[@]} -gt 0 ]; then RUN_ARGS+=("${REF_ARG[@]}"); fi
  "${COMMON_DOCKER[@]}" "${RUN_ARGS[@]}"
  echo "done (full DAP): $OUT"
  exit 0
fi

if [ "$MODE" = "subset" ]; then
  echo "==> Stage A: official DAP moments-only workflow (HYB10/S/N=50)"
  STAGE_A=(
    python /app/run/run_manga_dap.py
    --input-dir /app/input
    --out /app/output
    --config /app/config
    --source-key "$SOURCE_KEY"
    --fast-eline --stage-a-only
  )
  if [ ${#REF_ARG[@]} -gt 0 ]; then STAGE_A+=("${REF_ARG[@]}"); fi
  "${COMMON_DOCKER[@]}" "${STAGE_A[@]}"

  echo "==> Stage B: official full-method SASUKE on ${NBINS} central bins"
  STAGE_B=(
    python /app/run/run_official_subset.py
    --input-dir /app/input
    --stage-a-dir /app/output/dap
    --out /app/output
    --config /app/config
    --n-bins "$NBINS"
    --source-key "$SOURCE_KEY"
  )
  if [ ${#REF_ARG[@]} -gt 0 ]; then STAGE_B+=("${REF_ARG[@]}"); else
    echo "ERROR: subset mode requires --reference <published MAPS>" >&2
    exit 2
  fi
  "${COMMON_DOCKER[@]}" "${STAGE_B[@]}"
  # Stage-A common/ref/model cube are no longer needed; the subset script
  # already copied the binned spectra, continuum and selected MAPS.
  rm -rf "$OUT/dap"
  echo "done (accepted subset): $OUT"
  exit 0
fi

echo "==> WARNING: running auxiliary FASTMODE_NOT_PRODUCTION path"
RUN_ARGS=(
  python /app/run/run_manga_dap.py
  --input-dir /app/input
  --out /app/output
  --config /app/config
  --source-key "$SOURCE_KEY"
  --fast-eline
)
if [ ${#REF_ARG[@]} -gt 0 ]; then RUN_ARGS+=("${REF_ARG[@]}"); fi
"${COMMON_DOCKER[@]}" "${RUN_ARGS[@]}"
mkdir -p "$OUT/aux_fastmode"
if [ -f "$OUT/fits/manga_dap_maps.fits.gz" ]; then
  mv "$OUT/fits/manga_dap_maps.fits.gz" "$OUT/aux_fastmode/manga_dap_maps_FASTMODE.fits.gz"
fi
echo "done (auxiliary fast mode; NOT production): $OUT"
