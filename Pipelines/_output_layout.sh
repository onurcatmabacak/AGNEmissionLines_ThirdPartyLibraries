#!/usr/bin/env bash
# Shared output-layout helper for the Docker wrappers.
#
# Canonical product layout:  outputs/<tool>/<source>_z_<z>/
# Legacy scratch layout:     work/<run>/  (anything not under outputs/)
#
# Source this file, then call:
#
#   output_layout_resolve "$OUT"
#
# which sets:
#   OUT_SOURCE       directory name of the product tree (the source key in the
#                    canonical layout, the run tag in the legacy one)
#   OUT_TOOL         parent directory name (the tool in the canonical layout)
#   OUT_REFS         directory holding the sibling tool trees for this source:
#                    the repository outputs/ root in the canonical layout,
#                    dirname(OUT) in the legacy one
#   OUT_IS_CANONICAL 1 for outputs/<tool>/<source>, 0 otherwise
#
# Then ``output_ref_dir <tool>`` echoes the sibling tool tree for this source:
# outputs/<tool>/<source> in the canonical layout, dirname(OUT)/<tool> otherwise.

output_layout_resolve() {
  local out="$1"
  OUT_SOURCE="$(basename "$out")"
  OUT_TOOL="$(basename "$(dirname "$out")")"
  OUT_REFS="$(dirname "$out")"
  OUT_IS_CANONICAL=0
  if [ "$(basename "$OUT_REFS")" != "outputs" ] \
     && [ "$(basename "$(dirname "$OUT_REFS")")" = "outputs" ]; then
    OUT_IS_CANONICAL=1
    OUT_REFS="$(dirname "$OUT_REFS")"
  fi
}

output_ref_dir() {
  local tool="$1"
  if [ "$OUT_IS_CANONICAL" -eq 1 ]; then
    echo "$OUT_REFS/$tool/$OUT_SOURCE"
  else
    echo "$OUT_REFS/$tool"
  fi
}
