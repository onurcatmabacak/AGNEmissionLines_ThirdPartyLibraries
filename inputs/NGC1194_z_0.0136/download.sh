#!/usr/bin/env bash
# Download the real MaNGA DR17 products for NGC 1194 (plateifu 9193-12701).
#
# The LOGCUBE (208 MB) and LOGRSS (169 MB) exceed GitHub's 100 MB per-file
# limit and are intentionally not committed.  The published DAP MAPS
# (10.8 MB) is committed because it is the independent comparison reference.
#
# Usage:
#   bash inputs/NGC1194_z_0.0136/download.sh
#
# The script verifies the exact byte sizes and SHA-256 values recorded in
# source.json.  Existing files are re-used only if they match.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW="$DIR/raw"
mkdir -p "$RAW"

fetch() {
  local name="$1" url="$2" size="$3" sha="$4"
  local path="$RAW/$name"
  if [ -f "$path" ]; then
    local got_size got_sha
    got_size="$(stat -c %s "$path")"
    got_sha="$(sha256sum "$path" | awk '{print $1}')"
    if [ "$got_size" = "$size" ] && [ "$got_sha" = "$sha" ]; then
      echo "ok   $name (cached, $size bytes)"
      return 0
    fi
    echo "warn $name exists but does not match; re-downloading" >&2
  fi
  echo "get  $name"
  curl -L --fail --retry 5 --retry-delay 5 --continue-at - \
       -o "$path" "$url"
  local got_size got_sha
  got_size="$(stat -c %s "$path")"
  got_sha="$(sha256sum "$path" | awk '{print $1}')"
  if [ "$got_size" != "$size" ] || [ "$got_sha" != "$sha" ]; then
    echo "ERROR: $name failed verification" >&2
    echo "  expected size=$size sha256=$sha" >&2
    echo "  got      size=$got_size sha256=$got_sha" >&2
    return 1
  fi
  echo "ok   $name ($size bytes)"
}

fetch "manga-9193-12701-LOGCUBE.fits.gz" \
  "https://data.sdss.org/sas/dr17/manga/spectro/redux/v3_1_1/9193/stack/manga-9193-12701-LOGCUBE.fits.gz" \
  207992431 \
  7810f4c94db2fbb677e1bc92bc91a866e88d421c24c8c52273aa5277b9b5f764

fetch "manga-9193-12701-LOGRSS.fits.gz" \
  "https://data.sdss.org/sas/dr17/manga/spectro/redux/v3_1_1/9193/stack/manga-9193-12701-LOGRSS.fits.gz" \
  169194046 \
  812000fdc1946193f8aa0e2e96878555ec370fa30b3a41df20cd76b0bad497bd

fetch "manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz" \
  "https://data.sdss.org/sas/dr17/manga/spectro/analysis/v3_1_1/3.1.0/HYB10-MILESHC-MASTARHC2/9193/12701/manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz" \
  10775592 \
  f47f16b90c45fc668e0105e9b2a2241d6c28104924056bcfa493f84e1f200f49

echo "done: $RAW"
