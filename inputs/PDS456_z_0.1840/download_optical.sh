#!/usr/bin/env bash
# Real HST/STIS FUV+NUV spectrum of PDS 456 (HASP cspec product).
# MAST DOI: 10.17909/T9-STSC-8264 (HST proposal 8264, PI P. O'Brien)
set -euo pipefail
cd "$(dirname "$0")/raw"
base="https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:HST/product/hasp"
file="hst_8264_stis_pds456_sg140l-sg230l_o58s_cspec.fits"
curl -fL --retry 4 --max-time 300 -o "$file" "$base/$file"
echo "d6567d80cef6b515c006aec17ee20c6f18363fb88bde273f67cfde43f12c83c8  $file" | sha256sum -c -
