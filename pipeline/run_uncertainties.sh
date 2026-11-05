#!/usr/bin/env bash
# =============================================================================
#  run_uncertainties.sh -- re-run the fits with uncertainty estimation ON
# =============================================================================
#
#  The parameter search runs every tool in its fastest mode (GELATO NBoot=0,
#  BADASS no bootstrap, PyQSOFit MC off, fantasy MC off) because errors are not
#  needed to rank models.  This wrapper re-runs the same pipeline with error
#  estimation enabled so results/lines.csv gets real flux_err_1e17 columns:
#
#      bash pipeline/run_uncertainties.sh                 # all tools
#      GELATO_NBOOT=50 bash pipeline/run_uncertainties.sh --tools gelato
#
#  Outputs go to runs_uncertainties/ and results_uncertainties/ by default so the
#  fast-search products are not overwritten.
# =============================================================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export GELATO_NBOOT="${GELATO_NBOOT:-20}"          # bootstrap samples
export BADASS_MAX_LIKE_NITER="${BADASS_MAX_LIKE_NITER:-100}"  # MC bootstrap iters
export FANTASY_MC="${FANTASY_MC:-1}"
export FANTASY_MC_N="${FANTASY_MC_N:-20}"
export PYQSOFIT_MC="${PYQSOFIT_MC:-1}"
export PYQSOFIT_NSAMP="${PYQSOFIT_NSAMP:-50}"      # MC resampling trials
export RUNS_DIR="${RUNS_DIR:-$ROOT/runs_uncertainties}"
export RESULTS_DIR="${RESULTS_DIR:-$ROOT/results_uncertainties}"

export INPUT_DIR="${INPUT_DIR:-$ROOT/input}"
echo "[uncertainties] GELATO_NBOOT=$GELATO_NBOOT BADASS_MAX_LIKE_NITER=$BADASS_MAX_LIKE_NITER"
echo "[uncertainties] FANTASY_MC=$FANTASY_MC/$FANTASY_MC_N PYQSOFIT_MC=$PYQSOFIT_MC/$PYQSOFIT_NSAMP"
echo "[uncertainties] -> $RUNS_DIR , $RESULTS_DIR"
exec bash "$ROOT/run_pipeline.sh" "$@"
