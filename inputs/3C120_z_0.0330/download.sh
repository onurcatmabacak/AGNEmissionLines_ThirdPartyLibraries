#!/usr/bin/env bash
# Download the RXTE/PCA stdprod products for this source.
set -euo pipefail
exec "$(dirname "$0")/xray/rxte_10339-02-01-01/download.sh" "$@"
