#!/usr/bin/env bash
# Real HST/STIS G430L+G750L spectrum of 3C 120 (HASP cspec product).
# MAST DOI: 10.17909/T9-STSC-8700 (HST proposal 8700, PI A. Martel)
set -euo pipefail
cd "$(dirname "$0")/raw"
base="https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:HST/product/hasp"
file="hst_8700_stis_3c120d0_g430l-g750l_o62o_cspec.fits"
curl -fL --retry 4 --max-time 300 -o "$file" "$base/$file"
echo "f0f1bbb19124ea01233922c2c633c6abcc8e44e25b9c59d387d692f427fecde2  $file" | sha256sum -c -
