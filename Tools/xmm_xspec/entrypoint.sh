#!/usr/bin/env bash
# Container entry point: initialise HEASoft/PyXspec and run the requested command.
set -euo pipefail

export HEADAS="${HEADAS:-/opt/conda/heasoft}"
export LHEA_DATA="${LHEA_DATA:-${HEADAS}/refdata}"
export HOME="${XMM_XSPEC_HOME:-/tmp/xmm_xspec_home}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl}"
export PFILES="${PFILES:-/tmp/pfiles}"

mkdir -p "$HOME/.xspec" "$MPLCONFIGDIR" "$PFILES"

# headas-init.sh needs HEADAS and writes a temporary setup script.  Source it
# before running Python so that PyXspec and its model data are on the path.
if [ -f "$HEADAS/headas-init.sh" ]; then
  # shellcheck disable=SC1091
  . "$HEADAS/headas-init.sh"
fi

# headas-init may prepend its own bin directory; keep the conda Python first.
export PATH="/opt/conda/bin:${HEADAS}/bin:${PATH}"
export PFILES="${PFILES:-/tmp/pfiles}"
export LHEA_DATA="${LHEA_DATA:-${HEADAS}/refdata}"

exec "$@"
