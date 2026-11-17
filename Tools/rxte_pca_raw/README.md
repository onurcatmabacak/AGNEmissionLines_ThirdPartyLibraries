# Raw RXTE PCA reduction (3C 120, 10339-02-01-01)

Status: **partial**.  `pcabackest` and `saextrct` run on the raw Standard-2
arrays, but the resulting fit does not yet reproduce the official `stdprod`
products.  This directory records the working commands so the remaining
filter/PCU/response work is reproducible; it is not a registered tool.

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

## Current results

- source PHA: **537,007 counts / 3,328 s**
- background PHA: **493,140 counts**, model exposure 3,696 s, BACKSCAL 1.111
- raw fit with `stdprod.rsp`: chi2/dof 9000/49 (C-stat 225/46)
- official `stdprod` pair: chi2/dof 89.85/49
- normalized 129-channel cross-correlation: minimum at **zero shift**, 2.4% shape difference
- XFL-derived GTI with the exact 3,328 s exposure gives the same 537,007 counts

The remaining mismatch is a few-percent filter/PCU/background-model shape
difference, not a channel-index error.  See `docs/UNRESOLVED_ITEMS.md`.
