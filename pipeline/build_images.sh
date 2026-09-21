#!/usr/bin/env bash
# Build the Docker images for the tools that need them.
#
# Each image bakes in the tool's code and dependencies, and a *placeholder*
# spectrum.  run_pipeline.sh overrides the placeholder at run time by mounting
# the prepared per-object input over it, so images only have to be built once.
#
# Usage:  bash pipeline/build_images.sh [tool ...]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER="${DOCKER:-docker}"
# Tools with a Dockerfile; image name -> source directory (case-sensitive!)
DOCKER_TOOLS=(badass fantasy_agn gelato gleam)
declare -A TOOL_SRC=( [badass]=badass [fantasy_agn]=fantasy_agn [gelato]=Gelato [gleam]=Gleam )

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
  if ! $DOCKER build --network=host -t "$tool" -f "$df" "$ROOT/$srcdir"; then
    echo "!! build failed: $tool" >&2
    failed+=("$tool")
  fi
done
if [ ${#failed[@]} -gt 0 ]; then
  echo "Done with failures: ${failed[*]}" >&2
  exit 1
fi
echo "Done building: ${tools[*]}"
