# `inputs/` — source manifests (data deliberately not shipped)

This directory used to carry the raw observations themselves: SDSS, XMM-Newton,
RXTE, HST, JWST, Herschel, Spitzer, MaNGA and ALMA products — about **400 MB** of
third-party data that every clone paid for.

They are gone on purpose, and gone from the git history too.  What a source
directory keeps is its manifest:

```text
inputs/<SOURCE_KEY>/
  source.json      # kind, redshift, which tools it feeds, and the URLs
  raw/             # (not shipped) the actual spectra/cubes
```

`source.json` retains the provenance — instrument, obsID, product name and the
download URL — so every dataset can be re-fetched:

```bash
# read the URLs for a source
python -c "import json;print(json.load(open('inputs/<SOURCE_KEY>/source.json'))['urls'])"
```

The numerical results of every product that used these data are in
[`docs/RESULTS.md`](../docs/RESULTS.md), with the per-tool caveats in
[`docs/CAVEAT_MATRIX.md`](../docs/CAVEAT_MATRIX.md).
