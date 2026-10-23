#!/usr/bin/env bash
# Run AGNfitter-rx on a source photometry directory.
#   bash run_agnfitter_sed_docker.sh <photometry-dir> <output-dir>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN="${1:?usage: run_agnfitter_sed_docker.sh <photometry-dir> <output-dir>}"
OUT="${2:?usage: run_agnfitter_sed_docker.sh <photometry-dir> <output-dir>}"
mkdir -p "$OUT"
exec docker run --rm --user "$(id -u):$(id -g)" -e MPLCONFIGDIR=/tmp/mpl \
  -v "$(realpath "$IN")":/app/input:ro -v "$(realpath "$OUT")":/app/output \
  agnfitter_sed
