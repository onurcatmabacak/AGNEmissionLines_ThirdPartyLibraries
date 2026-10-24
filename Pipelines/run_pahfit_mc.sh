#!/usr/bin/env bash
# Backward-compatible entry point for the PAHFIT Monte Carlo campaign.
#
# The campaign grew into a production matrix (PDS short/long/both, VV114,
# NGC 4151, NGC 253, covariance/bootstrap validation).  The actual recipe is
# maintained in Pipelines/run_pahfit_production.sh.
#
#   bash Pipelines/run_pahfit_mc.sh
#
# This overwrites the PAHFIT products in outputs/<source>/pahfit_mir/...
# Monte Carlo is opt-in; normal pipeline runs remain MC-free.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$ROOT/Pipelines/run_pahfit_production.sh" "$@"
