#!/usr/bin/env bash
# Run CAFE on JWST/MIRI x1d spectra in the cafe_line image.
#
#   bash Pipelines/run_cafe_line_docker.sh <input-dir> <output-dir> <z> [extra args...]
#
# Examples:
#   bash Pipelines/build_images.sh cafe_line
#   bash Pipelines/run_cafe_line_docker.sh \
#       inputs/PDS456_z_0.1840/raw outputs/PDS456_z_0.1840/cafe_line 0.184 \
#       --error-floor 0.01 --mc-samples 200
#
# Extra arguments are passed to run_cafe.py (e.g. --max-wave, --segment,
# --mc-samples, --config, --tables).  The prepared 3-column CAFE spectrum is
# written under work/prepared/<source>/cafe_line/, never into outputs/.
#
# Environment overrides:
#   CAFE_CONFIG_DIR  host directory mounted at /app/config (default configs/cafe_line)
#   CAFE_WORK_DIR    host work directory (default work/prepared/<key>/cafe_line)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IN="${1:?usage: run_cafe_line_docker.sh <input-dir> <output-dir> <z> [extra args...]}"
OUT="${2:?usage: run_cafe_line_docker.sh <input-dir> <output-dir> <z> [extra args...]}"
Z="${3:?usage: run_cafe_line_docker.sh <input-dir> <output-dir> <z> [extra args...]}"
shift 3

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found. Install Docker first." >&2
  exit 1
fi
if ! docker image inspect cafe_line >/dev/null 2>&1; then
  echo "ERROR: Docker image 'cafe_line' not found." >&2
  echo "Build it with:  bash Pipelines/build_images.sh cafe_line" >&2
  exit 1
fi

OUT_ABS="$(realpath -m "$OUT")"
IN_ABS="$(realpath -m "$IN")"
# outputs/<key>/cafe_line -> <key>; fall back to the output directory name.
KEY="$(basename "$(dirname "$OUT_ABS")")"
if [ "$KEY" = "." ] || [ -z "$KEY" ]; then KEY="$(basename "$OUT_ABS")"; fi
WORK="${CAFE_WORK_DIR:-$ROOT/work/prepared/$KEY/cafe_line}"
CONFIG_HOST="${CAFE_CONFIG_DIR:-$ROOT/configs/cafe_line}"

mkdir -p "$OUT_ABS" "$WORK"
if [ ! -d "$IN_ABS" ]; then
  echo "ERROR: input directory not found: $IN_ABS" >&2
  exit 1
fi
if [ ! -d "$CONFIG_HOST/tables" ]; then
  echo "ERROR: CAFE config tables not found under $CONFIG_HOST/tables" >&2
  echo "Set CAFE_CONFIG_DIR to a directory containing default/ and tables/." >&2
  exit 1
fi

exec docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl \
  -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" \
  -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" \
  -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" \
  -e NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}" \
  -e HOME=/tmp \
  -v "$IN_ABS":/app/input:ro \
  -v "$OUT_ABS":/app/output \
  -v "$(realpath -m "$WORK")":/app/work \
  -v "$(realpath -m "$CONFIG_HOST")":/app/config:ro \
  cafe_line \
    --input /app/input \
    --output /app/output \
    --work /app/work \
    --config /app/config/default \
    --tables /app/config/tables \
    --source-key "$KEY" \
    --z "$Z" \
    "$@"
