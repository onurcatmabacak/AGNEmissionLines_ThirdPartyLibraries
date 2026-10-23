#!/usr/bin/env bash
# Reproduce the PAHFIT Monte Carlo campaign used in the validation report.
#
#   bash Pipelines/run_pahfit_mc.sh
#
# This overwrites the PAHFIT products in outputs/<source>/pahfit_mir/...
# Monte Carlo is opt-in; the normal pipeline runs remain MC-free.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MIRI_ALL="jwst.miri.mrs.ch1.A,jwst.miri.mrs.ch1.B,jwst.miri.mrs.ch1.C,jwst.miri.mrs.ch2.A,jwst.miri.mrs.ch2.B,jwst.miri.mrs.ch2.C,jwst.miri.mrs.ch3.A,jwst.miri.mrs.ch3.B,jwst.miri.mrs.ch3.C,jwst.miri.mrs.ch4.A,jwst.miri.mrs.ch4.B,jwst.miri.mrs.ch4.C"
IRS="spitzer.irs.sl.2,spitzer.irs.sl.1,spitzer.irs.ll.2,spitzer.irs.ll.1"

echo "=== PDS 456 short: full-refit bootstrap (auto falls back from covariance)"
bash Pipelines/run_pahfit_mir_docker.sh \
  inputs/PDS456_z_0.1840/raw outputs/PDS456_z_0.1840/pahfit_mir/short 0.184 \
  --config /app/configs/pahfit_mir/short/config.json \
  --mc-samples 100 --mc-method auto

echo "=== PDS 456 short: fast covariance (rank-deficient comparison)"
bash Pipelines/run_pahfit_mir_docker.sh \
  inputs/PDS456_z_0.1840/raw outputs/PDS456_z_0.1840/pahfit_mir/short_covariance 0.184 \
  --config /app/configs/pahfit_mir/short/config.json \
  --mc-samples 100 --mc-method covariance

echo "=== NGC 4151: covariance (well-conditioned)"
bash Pipelines/run_pahfit_mir_docker.sh \
  inputs/NGC4151_z_0.0033/raw outputs/NGC4151_z_0.0033/pahfit_mir 0.003319 \
  --config /app/configs/pahfit_mir/default/config.json \
  --tbl --smooth-um 0.1 --instrument "$IRS" \
  --mc-samples 100 --mc-method auto

echo "=== NGC 4151: bootstrap validation"
bash Pipelines/run_pahfit_mir_docker.sh \
  inputs/NGC4151_z_0.0033/raw outputs/NGC4151_z_0.0033/pahfit_mir/bootstrap 0.003319 \
  --config /app/configs/pahfit_mir/default/config.json \
  --tbl --smooth-um 0.1 --instrument "$IRS" \
  --mc-samples 100 --mc-method bootstrap

echo "=== VV114: covariance (optional third object)"
bash Pipelines/run_pahfit_mir_docker.sh \
  inputs/VV114_z_0.0200/raw outputs/VV114_z_0.0200/pahfit_mir/mc_covariance 0.02 \
  --config /app/configs/pahfit_mir/default/config.json \
  --s1d --max-wave 28.0 --no-normalize-fit \
  --mc-samples 100 --mc-method covariance

echo "=== cross-object comparison"
python3 pipeline/compare_pahfit_mc.py
