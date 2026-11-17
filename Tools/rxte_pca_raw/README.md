# Raw RXTE PCA reduction (3C 120, 10339-02-01-01)

Status: **solved — the raw reduction reproduces the official `stdprod` product
exactly.**  Two mistakes were responsible for the earlier mismatch, both in the
hand-rolled combination step rather than in the reduction:

1. only **one** of the three `FS4a` Standard-2 segments was processed
   (3,328 s instead of 9,808 s, so a third of the source counts), and
2. the summed PHA kept the **`STAT_ERR` of the first segment** instead of
   `sqrt(total counts)`.

With all three segments, `saextrct` on the summed `pcabackest` models, and
`STAT_ERR = sqrt(COUNTS)`:

| quantity | raw reduction | official `stdprod` |
|---|---|---|
| exposure | 9,808 s | 9,808 s |
| source counts | 1,703,352 | 1,703,352 |
| per-channel ratio | — | **1.00000** (max deviation 0.0000) |
| background counts | 1,408,899 | 1,408,935 |
| net counts | 294,453.4 | 294,416.5 (0.01 %) |
| `tbabs*zpowerlw`, 3-20 keV, C-stat | **91.07/49 = 1.859** | **91.07/49 = 1.859** |
| Gamma / nH | 1.866 / 2.780 | 1.866 / 2.780 |

The channel-by-channel identity means the raw chain is a genuine reproduction,
not a lookalike: same events, same good time, same background model.  It stays a
verification recipe rather than a registered tool, because `stdprod` is the
product; this exists to prove the recipe behind it.

## Data

| item | URL |
|---|---|
| Standard-2 arrays | `https://heasarc.gsfc.nasa.gov/FTP/xte/data/archive/AO1/P10339/10339-02-01-01/pca/FS4a_*.gz` |
| filter / GTI | `.../stdprod/x10339020101.xfl.gz`, `.../stdprod/x10339020101.gti.gz` |
| PCA background model | `https://heasarc.gsfc.nasa.gov/FTP/caldb/data/xte/pca/cpf/bgnd/pca_bkgd_cmvle_eMv20111129.mdl.gz` |
| PCA response | `.../caldb/data/xte/pca/cpf/responses/95apr03/5det_256ch_950403.rmf` (the official stdprod product uses `xp10339020101.rsp`) |

## Working commands

```bash
# 1. background model for one Standard-2 segment
pcabackest infile=FS4a_4205180-4205ff0 outfile=bkg_4205180.fits \
  modelfile=pca_bkgd_cmvle_eMv20111129.mdl \
  filterfile=x10339020101.xfl \
  modeltype=both modelfamily=VLE interval=16 propane=no layers=no \
  gaincorr=no fullspec=no saahfile=none interp=yes syserr=no \
  maxmodels=2000 timeslop=128 clobber=yes

# 2. source spectrum (GTI must be passed as GTIAND, not GTIOR)
saextrct infile=FS4a_4205180-4205ff0 outroot=src_4205180 \
  gtiorfile=APPLY gtiandfile=x10339020101.gti \
  accumulate=ONE timecol=TIME columns=GOOD binsz=INDEF \
  printmode=SPECTRUM spmode=SUM lcmode=RATE \
  chmin=0 chmax=255 chint=INDEF chbin=INDEF timemin=INDEF \
  timemax=INDEF timeint=INDEF obsdate=MJDREF obstime="TSTART TSTOP" \
  clobber=yes
```

`pcabackest` writes a 129-channel `XTE_SA` background model; the per-PCU
spectra must be summed and written to a PHA with `BACKSCAL` set to
`bkg_exposure/src_exposure`.

## Results

Per-segment (for the record): 3,328 s + 3,328 s + 3,152 s = 9,808 s, and the
three source spectra sum to the official 1,703,352 counts.  `pcabackest` writes
an `XTE_SA` file with per-PCU *rates* (five columns, one row per 16 s interval),
so the background also has to go through `saextrct` — summing the `XTE_SA` file
directly is what produced the earlier 493,140-count background.

Fit convention that matters: with a hand-built PHA, XSPEC uses the `STAT_ERR`
column when `POISSERR=False`.  Set it to `sqrt(COUNTS)` or the chi-square is
inflated by the missing exposure ratio; the C-statistic is immune and is the
cleaner cross-check here.  See `docs/UNRESOLVED_ITEMS.md`.
