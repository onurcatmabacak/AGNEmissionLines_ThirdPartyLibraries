#!/usr/bin/env bash
# Download the official XMM-Newton PPS products for PDS 456 (ObsID 0721010201).
#
# This is the *official reduced-product* path: the HEASARC PPS archive serves
# source and background spectra extracted by the XMM-Newton Science Analysis
# System (SAS) pipeline, together with source-specific ARFs.  We do NOT run
# SAS epproc/especget here (see README.md for the optional raw path).
#
# Files are small (< 20 MB total).  The archive serves gzip-compressed FITS
# (``.FTZ``); the script decompresses them to plain ``.fits`` and removes the
# ``.FTZ`` copy.
#
# Usage:  bash inputs/PDS456_z_0.1840/xray/xmm_0721010201/download.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PPS="https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0721010201/PPS"
CCF="https://xmm-tools.cosmos.esa.int/external/xmm_ccf/ccf/extras/responses"

OBSID="0721010201"
PN="P${OBSID}PNS003"
M1="P${OBSID}M1S001"
M2="P${OBSID}M2S002"

fetch_ftz() {  # fetch_ftz <url-basename> <subdir>
  local name="$1" sub="$2"
  local url="$PPS/$name.FTZ"
  local raw="$HERE/$sub/$name.FTZ"
  local out="$HERE/$sub/$name.fits"
  mkdir -p "$HERE/$sub"
  if [ -s "$out" ]; then
    echo "exists  $sub/$name.fits"
    return
  fi
  echo "fetch   $url"
  curl -fL --retry 3 --retry-delay 5 -o "$raw" "$url"
  # .FTZ from HEASARC is gzip-compressed FITS.
  gzip -dc "$raw" > "$out"
  rm -f "$raw"
  echo "wrote   $sub/$name.fits ($(stat -c%s "$out") bytes)"
}

# --- EPIC source spectra, source ARFs and background spectra -----------------
# Source number 0001 is the target (PDS 456); higher numbers are other sources
# in the field and are deliberately not downloaded.
for inst in PN MOS1 MOS2; do
  case "$inst" in
    PN)   tag="$PN";  sub="pps/PN" ;;
    MOS1) tag="$M1";  sub="pps/MOS1" ;;
    MOS2) tag="$M2";  sub="pps/MOS2" ;;
  esac
  fetch_ftz "${tag}SRSPEC0001" "$sub"
  fetch_ftz "${tag}SRCARF0001" "$sub"
  fetch_ftz "${tag}BGSPEC0001" "$sub"
done

# --- Response matrices -------------------------------------------------------
# The PPS ARFs are source-specific, but PPS does not ship the RMF.  These are
# the official CCF "extras" response matrices (same calibration epoch v22.0
# for PN; 15 eV MOS matrices).  The PN matrix is the large-window / thin-filter
# matrix that matches the PN Large Window Thin1 exposure.
mkdir -p "$HERE/responses"
fetch_rmf() {  # fetch_rmf <url> <filename>
  local url="$1" name="$2"
  if [ -s "$HERE/responses/$name" ]; then
    echo "exists  responses/$name"
    return
  fi
  echo "fetch   $url"
  curl -fL --retry 3 --retry-delay 5 -o "$HERE/responses/$name" "$url"
  echo "wrote   responses/$name ($(stat -c%s "$HERE/responses/$name") bytes)"
}
fetch_rmf "$CCF/PN/epn_e2_lw20_sdY9_v22.0.rmf" "epn_e2_lw20_sdY9_v22.0.rmf"
fetch_rmf "$CCF/MOS/15eV/m1_e15_im_pall_c.rmf" "m1_e15_im_pall_c.rmf"
fetch_rmf "$CCF/MOS/15eV/m2_e15_im_pall_c.rmf" "m2_e15_im_pall_c.rmf"

# --- Provenance --------------------------------------------------------------
cd "$HERE"
sha256sum pps/PN/* pps/MOS1/* pps/MOS2/* responses/* > MANIFEST.sha256
echo
echo "Wrote $HERE/MANIFEST.sha256"
du -sh "$HERE"
