#!/usr/bin/env bash
set -euo pipefail
source /opt/conda/heasoft/headas-init.sh
source /opt/sas/xmmsas_22.1.0-a8f2c2afa-20250304/setsas.sh
exec "$@"
