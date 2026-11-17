# nustar_xspec — NuSTAR 3-79 keV hard X-ray fitting

NuSTAR extends the X-ray coverage above the 20 keV ceiling of the XMM EPIC and
RXTE PCA tools, which is where the Compton-thick diagnostics live: the >10 keV
turnover, the Compton reflection hump and the Fe K-alpha equivalent width cannot
be constrained on a 2-10 keV band alone.

Image: HEASoft + NuSTARDAS + XSPEC from the **bioconda** `heasoft` package.
Data: public NuSTAR **Level-2** cleaned event files, so `nupipeline` is skipped.
The working product uses the full-frame ObsID `60002046002` (NGC 1365); the
configured `60002046001` is a 32x32 subframe with `X/Y = -1`, which `numkrmf`
cannot use.

## Response path (fixed 2026-11-17)

`CALDBCONFIG` is a **mission/instrument table**, not `CALDB = /path`:

```
NUSTAR FPMA CALDB data/nustar/fpm caldb.indx CALDB data/nustar/fpm
NUSTAR FPMB CALDB data/nustar/fpm caldb.indx CALDB data/nustar/fpm
```

With that table and a local CALDB tree, the response builds on a read-only
mount:

1. `numkrmf` on the Level-2 event file + detector region -> RMF
   (`nuAcutdet0..3`, `nuAcutgrprmf`).
2. `nuskypos` with the CALDB alignment/pixel-position/teldef products and the
   SOC mast-aspect/attitude files -> optical-axis and DET1-reference files.
3. `numkarf` on the `nuproducts` PHA + those files -> source-region ARF with
   vignetting, aperture-stop and detector-absorption corrections enabled.
   The PSF/ghost corrections remain off: `nuexpomap` invokes an interactive
   `ximage`, and the wrapper that bypasses it produces an all-NaN ARF.
4. PyXspec `tbabs*cutoffpl` (C-stat), 3-79 keV.

The full CALDB tarball is not required; the targeted `caldb.indx` + `cut`
detector RMFs + ARF/teldef/align/pixpos/vign/aperture/detabs products are
enough.

## Product

`outputs/nustar_xspec/NGC1365_z_0.0035/README.md`: 12,603 FPMA + 12,145 FPMB
counts with local backgrounds.  Background-subtracted `tbabs*cutoffpl`:
FPMA C-stat/dof 1.024, FPMB 1.038; free-cross-cal profile joint c = 1.07,
C-stat/dof 1.004 (nH 1.40e23, Gamma 0.900, E_cut 35.5 keV).  Only the PSF/ghost
correction remains.

Model: `tbabs*cutoffpl` plus an optional `zgauss` Fe K-alpha line; the
`+pexrav` reflection variant is tried but is unconstrained on this
single-epoch spectrum.
