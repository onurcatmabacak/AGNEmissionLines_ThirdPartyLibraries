# `qsofitmore_line` — QSOFITMORE UV/optical AGN fitting (Docker)

QSOFITMORE is a standalone PyQSOFit-derived package for UV/optical quasar
spectra.  This image pins the public upstream at a specific commit and runs its
**lmfit** backend (no Kapteyn), with the Verner et al. (2009) Fe II template,
broken power law, Balmer continuum/high-order Balmer series, Galactic
extinction, and the package's native Monte Carlo uncertainty path.

## Provenance

| item | value |
|---|---|
| upstream | `https://github.com/rudolffu/qsofitmore` |
| pinned commit | `4c5f6e497b306aaf50b502a8e4b27ed9dfe89421` |
| package version | `1.2.2` |
| licence | GPL-3.0 |
| fitting backend | `lmfit==1.3.2` (`QSOFITMORE_USE_LMFIT=true`) |
| Python | 3.12 (image `python:3.12-slim`) |
| dust map | SFD98, DOI `10.7910/DVN/EWCNL5`, MD5-verified; `dustmaps==1.0.12` |
| image | `qsofitmore_line:latest`, 1,501,705,328 bytes (1.50 GB) at final build time |

The SFD98 `ngp`/`sgp` maps are downloaded at build time into
`/app/cache/dustmaps/sfd` and verified against the Dataverse MD5s
(`6f3a89528bba7d1b7bd55838da86b639` and
`60f7c43d51bccaff82961de3e9f9e789`).  `fetch_sfd.sh` is kept in the image so a
run can repair an incomplete cache.  `VERSION.json` records the DOI, file IDs,
MD5s, dustmaps version and fetch time.

## Build

```bash
bash Pipelines/build_images.sh qsofitmore_line
# or directly (build context is the repo root):
docker build -f Tools/qsofitmore_line/dockerfile -t qsofitmore_line .
```

## Run

```bash
# raw SDSS directory (recommended: preserves the IVAR mask)
bash Pipelines/run_qsofitmore_line_docker.sh \
  inputs/04592649654_z_0.5874/raw \
  outputs/qsofitmore_line/04592649654_z_0.5874 \
  --source-key 04592649654_z_0.5874 --mc-trails 200 --seed 20250101

# or through the orchestrator (it passes the raw directory for this tool)
.venv/bin/python pipeline/run_new_tools.py \
  --only 04592649654_z_0.5874 --tools qsofitmore_line --force
```

The runner accepts a directory (prepared `spectrum.fits`, raw `spec-*.fits`, or
any readable FITS) or a single FITS file.  Products go to
`outputs/<source>/qsofitmore_line/`.

## Model and switches

The effective configuration is
`configs/qsofitmore_line/default/config.json`; every switch is passed
explicitly to `QSOFitNew.Fit`:

* `deredden=True`, `dust_map=sfd`, Fitzpatrick (1999) `R_V=3.1`; the measured
  E(B-V) is recorded.
* `include_iron=True`, `iron_temp_name="V09"`, `Fe_verner09=True`: Verner et
  al. (2009) Fe II over 2000–10000 Å.  `Fe_verner09` is the package's
  compatibility flag needed so `Fe_line_prop` integrates the V09 template for
  the saved Fe II band fluxes; qsofitmore warns that it is redundant with
  `iron_temp_name`, but the flag is still stored.
* `broken_pl=True`: two-slope power law; the 4661 Å break is inside the
  coverage, so qsofitmore selects its optical profile (3000 Å pivot).
* `BC=True`: Dietrich et al. (2002) Balmer continuum plus the Storey & Hummer
  (1995) high-order Balmer series (n_upper=6–50, log10 n_e=9).
* `poly=False`: the broken power law already supplies the large-scale
  curvature; an extra polynomial is not identifiable over this lever arm.
* `decomposition_host=False`: qsofitmore's Yip+2004 host decomposition would
  restrict the rest-frame grid to ≳3450 Å and remove Mg II.  The host is
  measured independently by `ppxf_host`.
* `rej_abs=False`: the SDSS mask/calibrated errors already remove bad pixels.
* `tie_lambda/tie_width/tie_flux_1/tie_flux_2=True`: [O III] 4959/5007 and the
  outflow doublet share kinematics and a 0.33 flux ratio; Hβ narrow shares the
  [O III] core group.
* `narrow_max_kms=1200`: qsofitmore's hard cap on the Gaussian **sigma** of
  non-broad components (not on FWHM).  This object's narrow components have
  sigma ≈360–510 km/s, so none is at the cap.  The compact table's Mg II
  narrow FWHM of ≈1200 km/s is the Gaussian FWHM corresponding to sigma≈510
  km/s, not a bound hit.  A future object with sigma at 1200 km/s would be
  flagged `at_bound` and should not be read as a free narrow-line width.
* `wave_range=[2247, 6510.4]` Å rest: the clean SDSS COADD coverage after
  dropping zero-IVAR pixels.  The red edge is just below Hα/N II 6549 so the
  Hα complex cannot be pulled in by a prepared PyQSOFit copy that sanitises
  zero-IVAR pixels to the median variance.
* `Fe_flux_range=[[2250,2700],[4434,4684],[5100,5600]]`: UV/optical Fe II
  pseudo-continuum bands.

The line table is the upstream example `qsopar_log.csv` with the [O III]
doublet ratios tied and narrow C III]/C IV rows added for UV spectra.  Hα,
C III] and C IV are outside the observed rest-frame coverage and are reported
as `not_covered`, not as zero fluxes.

## Uncertainty: native MC, not MCMC

qsofitmore 1.2.2 has **no** `emcee`/MCMC sampler.  Its native uncertainty mode
is `MC=True, n_trails=N`: add `N(0, err)` to every fitted pixel and refit the
continuum and each line complex with lmfit.  The production run uses **200**
realizations (200× the package default of 1) with seed `20250101`.  This is a
frequentist parametric bootstrap; no posterior is claimed.

The runner records every line-complex refit by wrapping `lmfit.minimize` while
qsofitmore's `new_line_mc` is active.  It then sums each physical line from all
of its Gaussian components.  This is necessary because qsofitmore's
`<complex>_whole_br_area` column only sums Gaussians above its 1200 km/s
classifier; for `04592649654` that column is about half of the total Hβ flux.

Products: `qsofitmore_mc_samples.csv` (every retained realization),
`qsofitmore_mc_summary.csv`, `qsofitmore_hb_oiii_mc.csv`,
`qsofitmore_corner.png/pdf` (Hβ, [O III], ratio, Hβ FWHM),
`qsofitmore_mgii_corner.*`, and `qsofitmore_uncertainty.*`.

## Failure modes fixed here

* **NumPy 2 / qsofitmore plotting.**  qsofitmore's QA plot does
  `float(self.comp_result[np.where(...)])`; with NumPy 2 this raises
  “only 0-dimensional arrays can be converted to Python scalars”.  The image
  pins `numpy==1.26.4`.
* **Hα pulled into a prepared input.**  The PyQSOFit preparation replaces
  zero-IVAR SDSS pixels with the median variance, so the rest-frame grid can
  extend to 6551 Å and select the Hα complex through N II 6549.  The tool
  uses the raw COADD when driven by the orchestrator and trims to 6510.4 Å.
* **Package broad-area column is not the total.**  Multi-Gaussian broad
  templates contain Gaussians below the 1200 km/s classifier; the compact
  table sums all components and documents the difference.
* **Kapteyn.**  Not installed; the legacy kmpfit path is never used.
* **Dust-map fetch.**  `dustmaps.sfd.fetch()` uses the Dataverse API with the
  default requests user-agent and can receive HTTP 403; `fetch_sfd.sh` calls
  the direct datafile endpoints with a browser user-agent and verifies MD5s.

## Cross-check

```bash
.venv/bin/python pipeline/compare_qsofitmore.py --source-key 04592649654_z_0.5874
# figure products need matplotlib; run it in the qsofitmore_line image if the
# host venv is unavailable:
docker run --rm -v "$PWD":/work qsofitmore_line \
  python /work/pipeline/compare_qsofitmore.py --source-key 04592649654_z_0.5874
```

It compares Hβ total, [O III] 5007 total and Mg II total against PyQSOFit,
GANDALF, S3Fit, GalSpec, PyQSOFitSpec, QGfit, SHEAP and the SDSS ZLINE anchor,
and writes `cross_tool_comparison.csv/.json/.md` plus a figure.

## What this tool can and cannot measure

**Can:** UV/optical AGN continuum shape, Fe II pseudo-continuum, Balmer
continuum/high-order Balmer, broad/narrow Hβ/Hγ, Mg II, [O III] core/outflow,
[O II], [Ne V], and their Monte Carlo uncertainties.

**Cannot:** Hα/C III]/C IV on this SDSS spectrum (no coverage); a physical BLR
decomposition (the broad template is empirical and component-degenerate); a
posterior (no MCMC); an independent narrow Hβ width (tied to [O III]); a
stellar host (use `ppxf_host`).
