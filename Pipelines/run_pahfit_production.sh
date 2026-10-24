#!/usr/bin/env bash
# Reproduce the PAHFIT production matrix.
#
#   bash Pipelines/run_pahfit_production.sh
#
# Each block is independent; comment out blocks to shorten the campaign.
# Outputs are written under outputs/<source>/pahfit_mir/.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUN="bash Pipelines/run_pahfit_mir_docker.sh"
MIRI_ALL="jwst.miri.mrs.ch1.A,jwst.miri.mrs.ch1.B,jwst.miri.mrs.ch1.C,jwst.miri.mrs.ch2.A,jwst.miri.mrs.ch2.B,jwst.miri.mrs.ch2.C,jwst.miri.mrs.ch3.A,jwst.miri.mrs.ch3.B,jwst.miri.mrs.ch3.C,jwst.miri.mrs.ch4.A,jwst.miri.mrs.ch4.B,jwst.miri.mrs.ch4.C"
IRS="spitzer.irs.sl.2,spitzer.irs.sl.1,spitzer.irs.ll.2,spitzer.irs.ll.1"

PDS_IN="inputs/PDS456_z_0.1840/raw"
PDS_OUT="outputs/PDS456_z_0.1840/pahfit_mir"

echo "=== PDS 456 short (100 MC, auto)"
$RUN "$PDS_IN" "$PDS_OUT/short" 0.184 \
  --config /app/configs/pahfit_mir/short/config.json \
  --mc-samples 100 --mc-method auto

echo "=== PDS 456 short covariance comparison (100, rank-deficient)"
$RUN "$PDS_IN" "$PDS_OUT/short_covariance" 0.184 \
  --config /app/configs/pahfit_mir/short/config.json \
  --mc-samples 100 --mc-method covariance

echo "=== PDS 456 long seed (normalized, 5-18 um)"
$RUN "$PDS_IN" "$PDS_OUT/long/seed" 0.184 \
  --segment long --smooth-um 0.05 --max-wave 18.0 \
  --instrument "$MIRI_ALL" --normalize-fit --maxiter 5000 --fit-passes 2

echo "=== PDS 456 long (100 MC, auto, warm start)"
$RUN "$PDS_IN" "$PDS_OUT/long" 0.184 \
  --config /app/configs/pahfit_mir/long/config.json \
  --init-from /app/output/seed/pahfit_output.ecsv \
  --mc-samples 100 --mc-method auto

echo "=== PDS 456 both (100 MC, auto, short warm start)"
mkdir -p "$PDS_OUT/both/seed"
cp "$PDS_OUT/short/pahfit_output.ecsv" "$PDS_OUT/both/seed/pahfit_output.ecsv"
$RUN "$PDS_IN" "$PDS_OUT/both" 0.184 \
  --config /app/configs/pahfit_mir/both/config.json \
  --init-from /app/output/seed/pahfit_output.ecsv \
  --mc-samples 100 --mc-method auto

echo "=== VV114 full 12-channel MIRI s1d (200 MC, auto/covariance)"
$RUN inputs/VV114_z_0.0200/raw outputs/VV114_z_0.0200/pahfit_mir 0.02 \
  --config /app/configs/pahfit_mir/vv114/config.json \
  --mc-samples 200 --mc-method auto

echo "=== VV114 bootstrap validation (200 MC)"
$RUN inputs/VV114_z_0.0200/raw outputs/VV114_z_0.0200/pahfit_mir/bootstrap_200 0.02 \
  --config /app/configs/pahfit_mir/vv114/config.json \
  --mc-samples 200 --mc-method bootstrap

echo "=== NGC 4151 full IRS SL/LL (200 MC, auto)"
$RUN inputs/NGC4151_z_0.0033/raw outputs/NGC4151_z_0.0033/pahfit_mir 0.003319 \
  --config /app/configs/pahfit_mir/ngc4151/config.json \
  --mc-samples 200 --mc-method auto

echo "=== NGC 4151 bootstrap validation (200 MC)"
$RUN inputs/NGC4151_z_0.0033/raw outputs/NGC4151_z_0.0033/pahfit_mir/bootstrap_200 0.003319 \
  --config /app/configs/pahfit_mir/ngc4151/config.json \
  --mc-samples 200 --mc-method bootstrap

echo "=== NGC 253 starburst stress test (100 MC, auto; tail >30 um excluded)"
$RUN inputs/NGC253_z_0.0008/raw outputs/NGC253_z_0.0008/pahfit_mir 0.000811 \
  --config /app/configs/pahfit_mir/ngc253/config.json \
  --mc-samples 100 --mc-method auto

echo "=== NGC 253 full-tail failure control (no MC; 5-38 um, all unflagged rows)"
$RUN inputs/NGC253_z_0.0008/raw outputs/NGC253_z_0.0008/pahfit_mir/full_tail 0.000811 \
  --tbl --smooth-um 0.1 --min-wave 5 --max-wave 38 \
  --tbl-aperture-arcsec2 1.0 --instrument "$IRS" \
  --normalize-fit --fit-passes 2 --maxiter 1000

echo "=== comparison products"
python3 pipeline/compare_pahfit_mc.py || true
