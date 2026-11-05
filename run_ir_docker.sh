#!/usr/bin/env bash
# Run the IR line fitter inside the ir_linefit Docker image.
#   bash run_ir_docker.sh <input-dir> <output-dir> [extra run_ir args]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN="${1:?usage: run_ir_docker.sh <input-dir> <output-dir> [args...]}"
OUT="${2:?usage: run_ir_docker.sh <input-dir> <output-dir> [args...]}"
shift 2
mkdir -p "$OUT"
exec docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MPLCONFIGDIR=/tmp/mpl \
  -v "$(realpath "$IN")":/app/input:ro \
  -v "$(realpath "$OUT")":/app/output \
  ir_linefit --input-dir /app/input --out /app/output "$@"
