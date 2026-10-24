#!/usr/bin/env bash
# Download the RXTE/PCA stdprod products for this source.
set -euo pipefail
exec "$(dirname "$0")/xray/rxte_20310-01-02-00/download.sh" "$@"
