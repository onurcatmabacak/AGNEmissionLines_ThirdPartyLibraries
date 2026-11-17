# NGC 1365 — NuSTAR 3–79 keV (`nustar_xspec`)

First real NuSTAR product in the repository: real Level-2 event files, CALDB
RMFs, source-region `numkarf` ARFs, local background spectra, and independent
FPMA/FPMB PyXspec fits.  A proper joint cross-calibration fit is still open, so
the numbers are a reduction/response/background proof, not a publication flux
measurement.

## Observation

| item | value |
|---|---|
| source | NGC 1365 (RA 53.4016, Dec -36.1404) |
| ObsID | `60002046002` (full-frame; the configured `60002046001` is subframe) |
| date | 2012-07-25 |
| focal planes | FPMA **and** FPMB (independent fits) |
| source region | 60" circle |
| background region | annulus 100–200", same centre |
| spectra | FPMA `nu60002046002A01_sr.pha`, **12,603 counts** + `*_bk.pha`, 5,910; FPMB `nu60002046002B01_sr.pha`, **12,145 counts** + `*_bk.pha`, 6,447 |
| BACKSCAL | source 0.001868, background 0.015587 (both planes) |
| RMFs | `numkrmf` from CALDB (`nuAcutdet0..3`/`nuBcutdet0..3` + grouping), 66 MB each |
| ARFs | `numkarf` source-region ARFs (62 KB each), vignetting/aperture-stop/detector-absorption corrections enabled; PSF/ghost corrections still off |

The ARFs were generated from `nuskypos` optical-axis and DET1-reference files
(`nuCalign20200901v001`, `nuA/Bpixpos20100101v007`, `nuA/Bvign20100101v008`,
`nuA/B20100101v001.teldef`, the SOC mast-aspect and attitude files).  This is
the step the earlier "blocked" note was missing: the CALDB-index query works
once `CALDBCONFIG` is a mission/instrument table.

## Result (background-subtracted, independent fits)

PyXspec 13 / C-statistic, 3–79 keV, `tbabs*cutoffpl`:

| quantity | FPMA | FPMB |
|---|---:|---:|
| C-stat/dof | **1941.1 / 1895 = 1.024** | **1967.2 / 1895 = 1.038** |
| nH (cm^-2) | 1.2 x 10^23 | 2.1 x 10^23 |
| Gamma | 0.96 | 1.38 |
| E_cut | 79 keV | 500 keV (fit bound) |
| normalization | 3.4 x 10^-3 | 8.2 x 10^-3 |

Without the vignetting/aperture/detabs corrections the same model gave FPMA
C-stat/dof 0.992 (Gamma 0.97, E_cut 49 keV) and FPMB 0.978 (Gamma 1.35).  The
corrections change the effective area and the fitted normalization; the two
detectors still differ by ΔΓ ≈ 0.42, which is the cross-calibration/systematic
that a proper joint fit must address.

`tbabs*(cutoffpl+pexrav)` reaches C-stat/dof 1827.5/1891 = 0.966 on FPMA
without background, but the reflection parameters run to their bounds
(`foldE` ~ 1e6 keV, `rel_refl` 2.8), so that is not a physical reflection
detection.  The absorbed cutoff power law is the number to quote.

## Joint fit (fixed cross-cal)

A joint fit of the two background-subtracted spectra with the
cross-calibration constants fixed at 1 gives **C-stat/dof 3861.7/3794 =
1.018**, nH 1.58 x 10^23 cm^-2, Gamma 1.14, E_cut 162 keV and normalization
5.0 x 10^-3.  This is close to the independent fits but is more constrained
(perfect cross-cal).  A free FPMB/FPMA constant is not available in the
current PyXspec single-model setup: it needs two sources/models with linked
physical parameters, which is the remaining joint-fit work.

## What was actually blocking the tool

Five issues, none of them the archive:

1. **`CALDBCONFIG` format.**  The runner wrote `CALDB = /opt/caldb`.  HEASoft's
   CALDB library wants a mission/instrument table:
   `NUSTAR FPMA CALDB data/nustar/fpm caldb.indx CALDB data/nustar/fpm`.
   With the one-line form every query fails with
   `Problem reading CALDB config file` / `Operation not permitted`.
   `Tools/nustar_xspec/run_nustar_xspec.py` now writes the table.
2. **Subframe coordinates.**  The configured ObsID `60002046001` is a 32x32
   subframe exposure with `X/Y = -1`, so `numkrmf` cannot select detector
   pixels.  Use the full-frame `60002046002`.
3. **ARF generation.**  `numkarf` needs the optical-axis and DET1-reference
   files, which in turn need `nuskypos` with the CALDB alignment, pixel-position,
   vignetting and teldef products plus the SOC mast-aspect/attitude files.
   With those staged, the ARF is written; vignetting, aperture-stop and
   detector-absorption corrections are enabled, while the PSF correction
   remains disabled (its exposure-map stage is the blocker).
4. **FPMB temperature ARF.**  The FPMB `numkarf` query selects
   `nuB20100101v006.arf` (not the v001 file); it has to be staged as well.
5. **Background.**  `nuproducts` needs `bkgextract=yes` and a background region
   file; it writes the `*_bk.pha` and sets the BACKSCAL ratio.  The XSPEC
   background file is opened by basename relative to the source directory.

## Reproduce

```bash
# observation: event_cl + auxil from HEASARC (ObsID 60002046002)
# CALDB: caldb.indx; nuA/Bcutdet0..3* + grouping; nuA/B20100101v001.{arf,teldef};
#        nuB20100101v006.arf; nuCalign20200901v001; nuA/Bpixpos20100101v007;
#        nuA/Bvign20100101v008; nuA/Btemp0_20100101v001.arf
# spectra (source + background), then:
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
  ... psfflag=no vignflag=yes apstopflag=yes grflag=no detabsflag=yes \
  apstopcorrfile=nuAapstop20100101v001.fits detabscorrfile=nuAdetabs20100101v001.fits
# repeat with instrument=FPMB, B cut RMFs, B pixpos/vign/teldef and FPMB event
```

The working scripts are in `~/nustar_work/` on the `acer` host:
`test_numkrmf24*.sh`, `test_nuskypos*.sh`, `test_numkarf2*.sh`,
`test_nuprod_bkg*.sh`, `fit_nustar_bkg.py`.

## Remaining work

- Proper joint FPMA+FPMB fit with a free (or linked) cross-calibration constant.
- Re-run `numkarf` with the PSF correction enabled (vignetting, aperture and
  detabs are already on).  The PSF files and instrument map are staged, but `nuexpomap`
  invokes the interactive Tk `ximage`; Xvfb fixes the display error, but
  `ximage` still hangs at `[XIMAGE>`; its generated command file is only
  crop/write/quit with no `read` of the instrument map, so it reports
  `Image for inmap not loaded`.  A batch-mode `ximage` or a precomputed
  exposure map is needed; an Xvfb wrapper that prepends `read/file` of the
  det1 instrument map lets `numkarf` finish, but it reports
  `PSF fraction=-nan` and writes an all-NaN ARF.
- Register `nustar_xspec` in `pipeline/tool_registry.py` and add the product to
  `docs/RESULTS.md` once the joint fit is in.
