#!/usr/bin/env bash
# Download the official HEASARC RXTE/PCA stdprod products for MCG-6-30-15,
# ObsID 20310-01-02-00, and verify their SHA256 digests.
#
# This is the second independent AGN for the RXTE/PCA branch (fallback and
# cross-check).  See the 3C 120 download.sh for the archive-checksum caveat.
set -euo pipefail
cd "$(dirname "$0")"

BASE="https://heasarc.gsfc.nasa.gov/FTP/xte/data/archive/AO2/P20310/20310-01-02-00/stdprod"
FILES=(
  xp20310010200_s2.pha.gz
  xp20310010200_b2.pha.gz
  xp20310010200.rsp.gz
)

for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    echo "exists: $f"
    continue
  fi
  echo "downloading: $BASE/$f"
  curl -fSL --retry 3 --retry-delay 2 "$BASE/$f" -o "$f.tmp"
  mv "$f.tmp" "$f"
done

sha256sum -c SHA256SUMS
echo "OK: MCG-6-30-15 PCA stdprod products verified in $(pwd)"
