#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:?usage: run_xmm_sas_fit_docker.sh <raw-output-dir> [--z Z]}"
shift || true
Z="${1:-0.184}"; [ "${1:-}" = "--z" ] && Z="${2:-0.184}"
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$(realpath "$OUT")":/out \
  xmm_sas_raw \
  /opt/conda/bin/python /app/run/fit_raw_pn.py --out /out --z "$Z"
