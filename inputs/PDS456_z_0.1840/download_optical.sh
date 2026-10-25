#!/usr/bin/env bash
# Real optical/UV spectra of PDS 456 used by pyqsofit_uv.
# 1) ESO VLT/X-SHOOTER VIS reduced spectrum (H-beta/[O III]/H-alpha)
# 2) HST/STIS G140L+G230L HASP cspec (Ly-alpha/C IV/C III])
set -euo pipefail
cd "$(dirname "$0")/raw"

xshoo="ADP.2023-04-20T08:25:01.842_XSHOOTER_VIS.fits"
curl -fL --retry 4 --max-time 300 \
  -o "$xshoo" \
  "https://dataportal.eso.org/dataPortal/file/ADP.2023-04-20T08:25:01.842"
echo "872a8aad22aaef495f69ee2ce347587da0bc1bb4c6d084a5d519b78922bea3e9  $xshoo" | sha256sum -c -

hst="hst_8264_stis_pds456_sg140l-sg230l_o58s_cspec.fits"
base="https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:HST/product/hasp"
curl -fL --retry 4 --max-time 300 -o "$hst" "$base/$hst"
echo "d6567d80cef6b515c006aec17ee20c6f18363fb88bde273f67cfde43f12c83c8  $hst" | sha256sum -c -
