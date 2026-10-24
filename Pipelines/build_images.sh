#!/usr/bin/env bash
# Build the Docker images for the tools that need them.
#
# Each image bakes in the tool's code and dependencies, and a *placeholder*
# spectrum.  run_pipeline.sh overrides the placeholder at run time by mounting
# the prepared per-object input over it, so images only have to be built once.
#
# Usage:  bash Pipelines/build_images.sh [tool ...]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER="${DOCKER:-docker}"
# Tools with a Dockerfile; image name -> source directory (case-sensitive!)
# rxte_xspec is FROM xmm_xspec; build the xmm_xspec base image first if missing.
DOCKER_TOOLS=(badass fantasy_agn gelato gleam ir_linefit pyqsofit_uv qsofitmore_line pyqsofitspec_line ppxf_host gandalf_line nir_linefit pahfit_mir fir_linefit cafe_line crossband cigale_sed agnfitter_sed s3fit_line galspec_line qgfit sheap_line manga_dap rxte_xspec)
declare -A TOOL_SRC=( [badass]=Tools/badass [fantasy_agn]=Tools/fantasy_agn [gelato]=Tools/Gelato [gleam]=Tools/Gleam [ir_linefit]=Tools/pipeline_ir [pyqsofit_uv]=Tools/pyqsofit_uv [qsofitmore_line]=Tools/qsofitmore_line [pyqsofitspec_line]=Tools/pyqsofitspec_line [ppxf_host]=Tools/ppxf_host [gandalf_line]=Tools/gandalf_line [nir_linefit]=Tools/nir_linefit [pahfit_mir]=Tools/pahfit_mir [fir_linefit]=Tools/fir_linefit [cafe_line]=Tools/cafe_line [crossband]=Tools/crossband [cigale_sed]=Tools/cigale_sed [agnfitter_sed]=Tools/agnfitter_sed [s3fit_line]=Tools/s3fit_line [galspec_line]=Tools/galspec_line [qgfit]=Tools/qgfit [sheap_line]=Tools/sheap_line [manga_dap]=Tools/manga_dap [rxte_xspec]=Tools/rxte_xspec )
# These tools need the repo root as context (they copy repo-level code/configs).
declare -A TOOL_CTX=( [ir_linefit]="$ROOT" [pyqsofit_uv]="$ROOT" [qsofitmore_line]="$ROOT" [pyqsofitspec_line]="$ROOT" [ppxf_host]="$ROOT" [gandalf_line]="$ROOT" [nir_linefit]="$ROOT" [pahfit_mir]="$ROOT" [fir_linefit]="$ROOT" [cafe_line]="$ROOT" [crossband]="$ROOT" [cigale_sed]="$ROOT" [agnfitter_sed]="$ROOT" [s3fit_line]="$ROOT" [galspec_line]="$ROOT" [qgfit]="$ROOT" [sheap_line]="$ROOT" [manga_dap]="$ROOT" )

if ! command -v "${DOCKER%% *}" >/dev/null 2>&1; then
  echo "ERROR: '${DOCKER}' not found." >&2
  echo "Install Docker first, e.g.:  sudo apt-get install docker.io && sudo usermod -aG docker \$USER" >&2
  exit 1
fi

tools=("$@")
[ ${#tools[@]} -eq 0 ] && tools=("${DOCKER_TOOLS[@]}")

failed=()
for tool in "${tools[@]}"; do
  srcdir="${TOOL_SRC[$tool]:-$tool}"
  df="$ROOT/$srcdir/dockerfile"
  [ -f "$df" ] || { echo "skip $tool (no $srcdir/dockerfile)"; continue; }
  echo "==> building image '$tool' from $df"
  ctx="${TOOL_CTX[$tool]:-$ROOT/$srcdir}"
  if ! $DOCKER build --network=host -t "$tool" -f "$df" "$ctx"; then
    echo "!! build failed: $tool" >&2
    failed+=("$tool")
  fi
done
if [ ${#failed[@]} -gt 0 ]; then
  echo "Done with failures: ${failed[*]}" >&2
  exit 1
fi
echo "Done building: ${tools[*]}"
