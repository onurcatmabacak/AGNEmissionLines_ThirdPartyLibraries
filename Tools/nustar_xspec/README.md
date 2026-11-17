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

## Free cross-cal profile scan

`Tools/nustar_xspec/fit_crosscal_scan.py` reproduces the c = 1.07 result.  It
takes the two background-subtracted PHAs, their RMF/ARF pairs and scans the
FPMB/FPMA factor, refitting the shared absorbed cutoff power law at every step:

```bash
python Tools/nustar_xspec/fit_crosscal_scan.py \
  --joint-dir /work/test_out/joint \
  --a-rmf /work/test_out/test24.rmf  --a-arf /work/test_out/arf_corr_test.arf \
  --b-rmf /work/test_out/test24b.rmf --b-arf /work/test_out/arf_b_corr.arf \
  --c-min 1.04 --c-max 1.08 --c-step 0.005 \
  --output crosscal.json
```

The run inside `nustar_xspec` gives c = 1.07, C-stat/dof 3807.9/3794 = 1.004.

## PSF correction: where it stands (2026-11-17)

`numkarf` now runs to completion with the local CALDB mounted
(`psfflag=yes`, source-region ARF, `optaxis`/`det1` taken from the observation),
but the PSF correction is unusable:

```text
PSF fraction=-nan off-axis=8.5 duration=38913.975
energy band 20.0-79.0 keV: total PSF correction factor=-nan
'arfs/arf_psf.arf' file successfully written
```

and the SPECRESP column of that ARF is **NaN in all 4096 rows**, i.e. the ARF is
written but empty.  The NaN comes from the exposure map that `nuexpomap` builds
through the interactive `ximage`, not from `numkarf`.

What was verified about that step:

* `ximage` **cannot** be driven with `@file`: it treats the argument as a startup
  command and fails with "Failed to execute startup command: @...cmd.xco".  The
  existing wrapper in `~/nustar_work/bin/ximage` used exactly that form, which is
  why it never got past the prompt.
* `ximage` *can* be driven in batch through **stdin**, with an explicit `exit`:
  `printf 'read "in.fits"\nwrite "out.fits"\nexit\n' | ximage` reads, writes a
  valid FITS image and returns to the shell.
* With that form the map is still NaN, so the command sequence `nuexpomap`
  generates is doing something else wrong (the wrapper's `WRAP` log line was never
  written, i.e. the task did not go through the wrapper at all).

Next step: run `nuexpomap` standalone with `chatter=5`, keep its
`<pid>tmp_ximage.xco` (do not let it clean up), and compare that command file
with the interactive session that does work; or bypass it by rendering the
exposure map with `xproj`/`nuexpomap inmap=<precomputed>` and feeding
`inexpomapfile`.  Until then the product uses the ARF **without** PSF correction
(vignetting, aperture and detabs are applied), which affects the normalisation by
a few per cent and not the spectral shape.
