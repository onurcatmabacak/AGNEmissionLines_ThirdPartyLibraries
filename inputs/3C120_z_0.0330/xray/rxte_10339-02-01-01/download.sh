#!/usr/bin/env bash
# Download the official HEASARC RXTE/PCA stdprod products for 3C 120,
# ObsID 10339-02-01-01, and verify their SHA256 digests.
#
# HEASARC does not publish a per-file checksum next to these stdprod files.
# The digests in SHA256SUMS pin the exact archive bytes used by the production
# fit; they are checked after download.
set -euo pipefail
cd "$(dirname "$0")"

BASE="https://heasarc.gsfc.nasa.gov/FTP/xte/data/archive/AO1/P10339/10339-02-01-01/stdprod"
FILES=(
  xp10339020101_s2.pha.gz
  xp10339020101_b2.pha.gz
  xp10339020101.rsp.gz
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
echo "OK: 3C 120 PCA stdprod products verified in $(pwd)"
