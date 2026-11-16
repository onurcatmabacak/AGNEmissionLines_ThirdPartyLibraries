# NGC 1365 — NuSTAR 3–79 keV (`nustar_xspec`)

First real NuSTAR product in the repository: a real Level-2 event file, a
CALDB RMF, a source-region `numkarf` ARF, and a PyXspec fit.  It is still
FPMA-only and background-free, so the numbers are a reduction/response proof,
not a publication flux measurement.

## Observation

| item | value |
|---|---|
| source | NGC 1365 (RA 53.4016, Dec -36.1404) |
| ObsID | `60002046002` (full-frame; the configured `60002046001` is subframe) |
| date | 2012-07-25 |
| focal plane | FPMA (FPMB not yet reduced) |
| extraction | 60" circle, no background |
| spectrum | `nu60002046002A01_sr.pha`, **12,603 counts** |
| RMF | `numkrmf` from CALDB (`nuAcutdet0..3` + `nuAcutgrprmf`), 66 MB |
| ARF | `numkarf` source-region ARF (`nu60002046002A01_sr.arf`, 62 KB), PSF/vignetting/aperture/ghost/detabs corrections disabled in this pass |

The ARF was generated from `nuskypos` optical-axis and DET1-reference files
(`nuCalign20200901v001`, `nuApixpos20100101v007`, `nuAvign20100101v008`,
`nuA20100101v001.teldef`, the SOC mast-aspect and attitude files).  This is the
step that the earlier "blocked" note was missing: the CALDB-index query works
once `CALDBCONFIG` is a mission/instrument table.

## Result

PyXspec 13 / C-statistic, 3–79 keV, `tbabs*cutoffpl`:

| quantity | value |
|---|---|
| C-stat/dof | **1867.1 / 1895 = 0.985** |
| nH | 1.9 x 10^23 cm^-2 |
| Gamma | 1.06 |
| E_cut | 88 keV |
| normalization | 6.9 x 10^-4 |

`tbabs*(cutoffpl+pexrav)` gives C-stat/dof 1827.5/1891 = 0.966, but the
reflection parameters run to their bounds (`foldE` ~ 1e6 keV, `rel_refl` 2.8),
so that improvement is not a physical reflection detection.  The absorbed
cutoff power law is the number to quote.

The earlier whole-FPM canned ARF gave nH 4.0 x 10^23 and Gamma 1.49 at
C-stat/dof 0.982; the source-region ARF changes the continuum parameters, which
is why the ARF mattered.  A proper background and FPMB joint fit are still
needed before comparing to published NGC 1365 spectra.

## What was actually blocking the tool

Three issues, none of them the archive:

1. **`CALDBCONFIG` format.**  The runner wrote `CALDB = /opt/caldb`.  HEASoft's
   CALDB library wants a mission/instrument table:
   `NUSTAR FPMA CALDB data/nustar/fpm caldb.indx CALDB data/nustar/fpm`.
   With the one-line form every query fails with
   `Problem reading CALDB config file` / `Operation not permitted`.
   `Tools/nustar_xspec/run_nustar_xspec.py` now writes the table.
2. **Subframe coordinates.**  The configured ObsID `60002046001` is a 32x32
   subframe exposure with `X/Y = -1` in the event file, so `numkrmf` cannot
   select detector pixels.  Use the full-frame `60002046002`.
3. **ARF generation.**  `numkarf` needs the optical-axis and DET1-reference
   files, which in turn need `nuskypos` with the CALDB alignment, pixel-position,
   vignetting and teldef products plus the SOC mast-aspect/attitude files.
   With those staged, the ARF is written; the flags were disabled to isolate the
   response from PSF/vignetting corrections.

## Reproduce

```bash
# observation: event_cl + auxil from HEASARC (ObsID 60002046002)
# CALDB: caldb.indx, nuAcutdet0..3*, nuAcutgrprmf*, nuA20100101v001.{arf,teldef},
#        nuCalign20200901v001, nuApixpos20100101v007, nuAvign20100101v008,
#        nuAtemp0_20100101v001.arf
# then, in the nustar_xspec image:
nuskypos pntra=53.4411 pntdec=-36.1092 \
  attfile=nu60002046002_att.fits alignfile=nuCalign20200901v001.fits \
  teldef=nuA20100101v001.teldef instrument=FPMA \
  optaxisfile=optaxis.fits det1reffile=det1ref.fits \
  mastaspectfile=nu60002046002_mast.fits clobber=yes
numkrmf infile=nu60002046002A01_cl.evt \
  srcregionfile=nu60002046002A01_src.reg \
  outfile=nu60002046002A01_sr.rmf clobber=yes
numkarf phafile=nu60002046002A01_sr.pha outfile=nu60002046002A01_sr.arf \
  optaxisfile=optaxis.fits det1reffile=det1ref.fits \
  infile=nu60002046002A01_cl.evt srcregionfile=nu60002046002A01_src.reg \
  ... psfflag=no vignflag=no apstopflag=no grflag=no detabsflag=no
# fit with PyXspec tbabs*cutoffpl
```

The working scripts are in `~/nustar_work/` on the `acer` host:
`test_numkrmf24.sh`, `test_nuskypos.sh`, `test_numkarf2.sh`, `fit_nustar_arf.py`.

## Remaining work

- Reduce FPMB and fit FPMA+FPMB jointly.
- Extract a background spectrum and set `BACKSCAL`.
- Re-run `numkarf` with the PSF/vignetting/aperture/ghost/detabs corrections
  enabled (the CALDB products are staged except the 2D-PSF grouping/files).
- Register `nustar_xspec` in `pipeline/tool_registry.py` and add the product to
  `docs/RESULTS.md` once the background/FPMB fit is in.
