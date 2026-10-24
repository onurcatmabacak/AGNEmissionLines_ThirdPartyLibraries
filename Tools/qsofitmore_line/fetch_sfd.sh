#!/usr/bin/env bash
# Download the SFD98 E(B-V) dust map used by qsofitmore's dustmaps backend.
#
# The Harvard Dataverse API is called with a browser user-agent: the default
# requests user-agent used by dustmaps.sfd.fetch() is blocked from some hosts
# (HTTP 403), while the direct datafile endpoints work.  Files are verified
# against the MD5 checksums published with DOI 10.7910/DVN/EWCNL5.
set -euo pipefail

DEST="${1:-/app/cache/dustmaps/sfd}"
mkdir -p "$DEST"

DATAVERSE_DOI="10.7910/DVN/EWCNL5"
BASE="https://dataverse.harvard.edu/api/access/datafile"

fetch_one() {
  local file_id="$1" md5="$2" name="$3"
  local target="$DEST/$name"
  if [ -f "$target" ] && echo "$md5  $target" | md5sum -c --status -; then
    echo "[sfd] cached $name ($md5)"
    return 0
  fi
  echo "[sfd] downloading $name from Dataverse datafile $file_id"
  curl --fail --location --retry 5 --retry-delay 2 \
       --user-agent "Mozilla/5.0 (qsofitmore-line provenance fetch)" \
       --output "$target.tmp" "$BASE/$file_id"
  echo "$md5  $target.tmp" | md5sum -c -
  mv "$target.tmp" "$target"
}

fetch_one 2902687 6f3a89528bba7d1b7bd55838da86b639 SFD_dust_4096_ngp.fits
fetch_one 2902695 60f7c43d51bccaff82961de3e9f9e789 SFD_dust_4096_sgp.fits

python - "$DEST" "$DATAVERSE_DOI" <<'PY'
import datetime, importlib.metadata as md, json, pathlib, sys
dest = pathlib.Path(sys.argv[1])
doi = sys.argv[2]
try:
    dustmaps_version = md.version("dustmaps")
except Exception:
    dustmaps_version = "unknown"
meta = {
    "map": "SFD98",
    "citation": "Schlegel, Finkbeiner & Davis (1998), ApJ 500, 525",
    "doi": doi,
    "dataverse_url": f"https://doi.org/{doi}",
    "files": {
        "SFD_dust_4096_ngp.fits": {"dataverse_file_id": 2902687,
                                    "md5": "6f3a89528bba7d1b7bd55838da86b639"},
        "SFD_dust_4096_sgp.fits": {"dataverse_file_id": 2902695,
                                    "md5": "60f7c43d51bccaff82961de3e9f9e789"},
    },
    "dustmaps_version": dustmaps_version,
    "queried_by": "dustmaps.sfd.SFDQuery(map_dir=...)",
    "downloaded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "note": "SFD98 E(B-V); qsofitmore applies Fitzpatrick (1999) R_V=3.1 extinction.",
}
(dest / "VERSION.json").write_text(json.dumps(meta, indent=2) + "\n")
print("[sfd] wrote", dest / "VERSION.json")
PY
