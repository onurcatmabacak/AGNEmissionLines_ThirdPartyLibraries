# `s3fit_line` — S3Fit simultaneous spectrum + SED / line fit (Docker)

Dockerised **S3Fit 2.2.6** (`pip install s3fit==2.2.6`) applied to the
repository's canonical SDSS/WISE QSO inputs.  S3Fit uses `scipy.optimize`
(`least_squares` + `lsq_linear`), not MCMC; its uncertainty estimate is a set
of **Monte-Carlo mock spectra** generated and refitted `num_mocks` times.

The committed output in `outputs/s3fit_line/04592649654_z_0.5874/` is now a
**full production `spec+sed` fit**: 8 SDSS/WISE bands, AGN + Fe II + Balmer
continuum + SKIRTOR torus + NLR/BLR lines, **10 mock spectra**, all 10 mocks
successful.  The older 3-mock pure-spectrum output is superseded.

## Build / run

```bash
bash pipeline/runners/build_images.sh s3fit_line

# Production run (used for the committed output):
bash pipeline/runners/run_s3fit_line_docker.sh \
  inputs/04592649654_z_0.5874 outputs/s3fit_line/04592649654_z_0.5874 \
  --config configs/s3fit_line/production --n-mocks 10 --threads 8
```

The runner accepts `--config DIR` (default `configs/s3fit_line/default`),
`--n-mocks`, `--mode spec+sed|spec`, `--z`, `--threads`, `--seed`, and
`--pyqsofit-dir`.  If `outputs/<source>/pyqsofit_uv/` exists as a sibling of
the output directory, it is mounted read-only automatically and
`pyqsofit_comparison.csv` is produced.

`configs/s3fit_line/production/` is the recipe used for the committed run:
full model grid, `mode: spec+sed`, `n_mocks: 10`, `threads: 8`, with the
runtime compromise described below.  `configs/s3fit_line/default/` keeps the
same full model but with dual annealing on and `nlfit_ntry_max: 3`; it is the
higher-effort reference configuration.

## Production run measured on the 8-core host

| quantity | value |
|---|---:|
| image size | 730 MB |
| whole command wall time | 58 min 21 s (02:02:47–03:01:08) |
| `main_fit()` wall time | 3483.9 s (58 min 4 s) |
| original-data fit | 412.8 s, reduced chi2 = 1.035 |
| MC wall time (10 mocks, 8 threads) | 3071.1 s |
| MC loop-time sum over threads | 7414.3 s (effective parallelism ~2.4x) |
| successful loops | 11 / 11 (original + 10 mocks) |
| reduced chi2, mocks | 1.605 +/- 0.112 (10 mocks) |
| photometric bands used | 8 (SDSS g,r,i,z + WISE 1–4) |
| spectrum/photometry calibration ratio | 0.493796 |
| detected total lines (MC S/N >= 3) | 13 / 14 |

The joblib `threading` backend gives partial, not 8x, parallelism for this
Python-heavy fit; the measured MC wall time is 3071 s against 7414 s of summed
loop time.

### Exact runtime compromise (model grid unchanged)

`configs/s3fit_line/production/fit_config.json` uses:

* `if_run_init_annealing: false` — dual-annealing global search disabled
  (reference default: on);
* `nlfit_ntry_max: 1` — one nonlinear try per stage (reference default: 3);
* `accept_chi_sq: 10` — avoids repeated recycle fits (reference default: 3).

Nothing else is reduced: the AGN powerlaw + Fe II + Balmer continuum grid, the
SKIRTOR torus grid, the NLR/BLR line model, all 8 photometric bands, and the
10 mocks are retained.  A trial with the default annealing/ntry settings
reached the same original reduced chi2 = 1.035 but took 804.9 s for the
original loop (1.95x the production original loop) and projected to well over
two hours for 10 mocks; it was stopped and the production configuration above
was used.  The model grid was not shortened.

## What was fixed in the adapter

The previous committed run exposed three real problems:

1. **Mode**: it used the `smoke` config (`mode=spec`, 3 mocks).  The
   production config is `spec+sed`; the production run uses it.
2. **Uncovered lines**: S3Fit extends its evaluation range by a velocity
   tolerance, so H-alpha (rest 6564.6 A) was being fitted even though the
   fitted spectrum ends at rest 6488.5 A.  Worse, H-alpha became the BLR
   hydrogen reference and H-beta was tied to an extrapolated line.  The
   adapter now removes lines whose rest-frame centres are outside the fitted
   range before constructing `FitFrame`; the removed list is recorded in
   `run.json -> scope.line_coverage`.  For this source it removes H-alpha,
   [N II] 6550/6585, [S II] 6718/6733 and C III] 1909.
3. **Mg II doublet**: the 2796/2804 pair was un-tied.  Because the two broad
   components are blended, the fit put essentially all flux into 2796 and
   ~0 into 2804.  The production line config ties 2804 to 2796 at S3Fit's
   atomic ratio 1.0; both lines now have ~equal flux and the total is stable.

Detection flags now require all of: line centre covered by the fitted
spectrum, at least 3 successful MC loops, and MC S/N >= 3.  The MC uncertainty
is the standard deviation of the successful mock fluxes; a robust
`(p84-p16)/2` error is also written.  The fit and MC figures are written as
both PNG and PDF.

## Committed production results

Calibrated fluxes are in the fitted (photometry-calibrated) normalisation.
To compare with the sibling tools on the raw SDSS spectrum normalisation,
divide by `spec_calib_ratio = 0.493796`; `pyqsofit_comparison.csv` and
`cross_tool_comparison.csv` already do this.

| line | S3Fit calibrated (1e-17) | S3Fit raw-SDSS (1e-17) | component / note |
|---|---:|---:|---|
| H-beta total | 1359.45 +/- 27.80 | 2753.06 +/- 56.29 | BLR 1152.46 +/- 124.94; NLR 207.00 +/- 143.71 (not detected) |
| [O III] 5007 total | 742.81 +/- 20.95 | 1504.29 +/- 42.42 | NLR only; FWHM 1326.2 +/- 79.2 km/s |
| Mg II 2796+2804 total | 884.97 +/- 25.81 | 1792.18 +/- 52.27 | tied doublet; 2796 = 440.28, 2804 = 444.70 (1e-17) |
| H-beta / [O III] 5007 | 1.830 +/- 0.064 | 1.830 +/- 0.064 | calibration-independent ratio |

Kinematics: NLR FWHM 1326.2 +/- 79.2 km/s at voff -247.4 km/s; BLR FWHM
2623.8 +/- 310.6 km/s at voff +38.2 km/s.  The BLR H-beta and Mg II share the
tied BLR profile.  The only non-detected total line is [O III] 4364
(S/N = 2.20).

The production result is consistent with the superseded 3-mock smoke run after
removing the photometric calibration: smoke H-beta = 2761.05, [O III] 5007 =
1506.55, Mg II = 1822.52 (1e-17), i.e. within 2% of the production
raw-SDSS values above.  The joint SED fit did not change the line fluxes; it
did provide the photometric calibration and the torus constraint.

## Cross-tool comparison (H-beta, [O III] 5007, Mg II)

All values are in 1e-17 erg s-1 cm-2 on the raw SDSS normalisation.  S3Fit
values are divided by `spec_calib_ratio`.  Full tables:
`s3fit_line/cross_tool_comparison.csv` and
`s3fit_line/cross_tool_line_ratios.csv`.

| tool | H-beta | [O III] 5007 | Mg II | H-beta/[O III] |
|---|---:|---:|---:|---:|
| S3Fit (this run) | 2753.1 | 1504.3 | 1792.2 | 1.830 |
| PyQSOFit | 2905.1 | 1479.5 | 2613.1 | 1.964 |
| GANDALF | 2950.8 | 1422.7 | — | 2.074 |
| GalSpec | 3236.8 | 1618.7 | — | 2.000 |
| QGfit | 2915.2 | 1166.9 | 2111.5 | 2.498 |

Interpretation:

* **[O III] 5007** agrees well with PyQSOFit (+1.7%) and GANDALF (+5.7%);
  GalSpec is 7% higher and QGfit 29% lower.  The spread is dominated by the
  core/wing decomposition, not by the total line.
* **H-beta** is 5% below PyQSOFit/QGfit, 7% below GANDALF and 15% below
  GalSpec.  S3Fit's NLR H-beta is weak and not individually detected; the
  total is dominated by the broad component tied to the BLR profile.
* **Mg II** is 31% below PyQSOFit and 15% below QGfit.  GANDALF and GalSpec do
  not fit Mg II.  S3Fit uses a tied 2796+2804 doublet with a common BLR
  profile, while PyQSOFit and QGfit fit a single blended profile; the
  difference is a decomposition/model difference, not a flux-unit error
  (the H-beta and [O III] totals agree).
* **H-beta/[O III] 5007** is 1.830 for S3Fit, inside the 1.96–2.50 range of
  the other tools and 7% below PyQSOFit.  The ratio is insensitive to the
  absolute calibration, so it isolates the line decomposition difference.

## Inputs

* `inputs/<source>_z_<z>/raw/spec-*.fits` — SDSS DR18 `COADD` table
  (`FLUX` in `1e-17 erg s-1 cm-2 A-1`, `LOGLAM` vacuum, `IVAR`, `WDISP`).
* `inputs/<source>_z_<z>/photometry/photometry.txt` — one-row CIGALE
  catalogue in mJy (`sloan.sdss.g/r/i/z`, `wise.W1/W2/W3/W4`).
* Optional NIR spectrum: the current QSO mode only uses the optical SDSS
  spectrum.  A NIR spectrum can be added later as a second spectral segment;
  it is not needed for the five z>0.5 eFEDS QSOs.

The adapter masks non-finite pixels, `IVAR<=0`, and non-zero SDSS `AND_MASK`
bits.  It uses the SDSS `WDISP` array to derive the instrument resolution
`R(lambda)` and explicitly tells S3Fit that the wavelengths are **vacuum**
(SDSS `LOGLAM` is vacuum; S3Fit's default would apply an air-to-vacuum
correction).

## Model (QSO mode, no stellar SSP)

```text
AGN powerlaw  +  Fe II pseudo-continuum  +  Balmer continuum
+ SKIRTOR torus (dust)
+ NLR  (narrow Gaussian, H-beta/[O III]/[O II]/[Ne III]/...)
+ BLR  (broad Gaussian, H-beta/Mg II; Mg II 2796+2804 tied)
```

* `Tools/s3fit_line/model_libraries/agn_iron_for_s3fit.fits` and
  `skirtor_for_s3fit.fits` are vendored from the public S3Fit 2.2.6 source
  distribution (`model_libraries/`).  The full S3Fit git repository is not
  vendored.
* `Tools/s3fit_line/filters/` contains the S3Fit SDSS g'/r'/i'/z' and WISE
  1–4 transmission curves.  They are needed because the PyPI wheel does not
  package `filters/`.
* **No stellar SSP library is used.**  S3Fit only initialises the `stellar`
  model frame when a `stellar`/`ssp` model is present; the QSO mode omits it.
  The disabled component is the host-galaxy stellar continuum, which is
  negligible in these luminous QSOs and not constrained by the SDSS fibre.
* PyNeb is disabled by default (`use_pyneb: false`); line ratios are S3Fit's
  fixed Case-B/forbidden-line ratios (ne=100 cm^-3, Te=1e4 K).

## Normalisation

S3Fit is given the spectrum in **cgs** (`erg s-1 cm-2 A-1`) and the photometry
in **mJy**.  S3Fit internally divides the spectrum by `spec_flux_scale` (a
power of ten) for numerical conditioning and reports line fluxes in units of
`spec_flux_scale`; this adapter multiplies them back by `spec_flux_scale`, so
`s3fit_lines.csv` is in physical cgs.

For this SDSS sample the fibre spectrum and the `SPALL` imaging photometry
differ by ~0.7 mag (the synthetic SDSS g flux from the spectrum is ~1.8x the
catalogue g flux).  The joint spectrum+SED fit therefore uses S3Fit's
`phot_calib_b` option (`SDSS_gp,rp,ip,zp`) to scale the spectrum to the
photometry before fitting.  The scale factor is stored in `run.json` as
`fit.spec_calib_ratio` and in the NPZ as `spec_calib_ratio`; it is **not
silent**.  Line fluxes are reported in the fitted (photometry-calibrated)
normalisation, and the comparison tables also report the raw-SDSS equivalent
(`S3Fit flux / spec_calib_ratio`).

## Outputs

```text
outputs/<source>_z_<z>/s3fit_line/
  s3fit_lines.csv                  component, line, flux, error, robust error,
                                   FWHM, velocity, S/N, n_mc, covered, detected
  s3fit_fit.png / .pdf             data, model, components, residuals, SED
  s3fit_mc.png / .pdf              10-mock flux/FWHM distributions + chi2_nu
  s3fit_output.npz                 compact spectra, SED, MC line arrays
  model_config.json                effective S3Fit model configuration
  fit_config.effective.json        effective fitting controls
  run.json                         provenance, chi2, runtimes, detections,
                                   caveats, production flag, comparisons
  s3fit.log                        full S3Fit log
  run.log                          adapter log
  pyqsofit_comparison.csv          PyQSOFit total/component comparison
  cross_tool_comparison.csv        S3Fit vs PyQSOFit/GANDALF/GalSpec/QGfit
  cross_tool_line_ratios.csv       H-beta/[O III] 5007 ratios per tool
  s3fit_output.pkl.gz              only if compact and explicitly enabled
```

The native S3Fit pickle is disabled by default because it embeds all model
grids and loops; a compact NPZ with the spectra, SED, MC line arrays, and
parameters is written instead.  Set `"save_native_pickle": true` or pass
`--save-pickle` to attempt it; the file is removed if it exceeds
`native_pickle_max_mb` (default 25 MB).

## Config layout

```text
configs/s3fit_line/default/
  fit_config.json       full spec+sed, 10 mocks, annealing on, ntry=3
  model_config.json     agn/torus/line registry
  agn_config.json       powerlaw + Fe II + Balmer continuum components
  torus_config.json     SKIRTOR dust component
  line_config.json      NLR and BLR components + line lists + Mg II tie

configs/s3fit_line/production/
  same model/line/torus/AGN files, with the documented runtime compromise:
  annealing off, nlfit_ntry_max=1, accept_chi_sq=10, n_mocks=10, threads=8

configs/s3fit_line/smoke/
  legacy 3-mock pure-spectrum demonstration; not production
```

`model_config.json` may reference the component JSON files by name; the
adapter resolves those references and the model-library paths at startup and
writes the effective configuration to `model_config.json` in the output.
The adapter also filters `line_used` against the fitted rest-frame coverage
and freezes nested `line_ties` JSON arrays into tuples for S3Fit.

## Caveats

* The SDSS fibre spectrum does not cover H-alpha for this target
  (z=0.587: fitted rest range 2299–6489 A; H-alpha is at 6564.6 A).  The
  automatic coverage filter removes H-alpha, [N II] 6548/6585 and
  [S II] 6718/6733, so H-alpha-based ratios are not available from this run.
  C III] 1909 is also outside the blue end and is removed.
* The QSO mode has no host-galaxy/SSP term, no X-ray/radio constraints, and no
  NIR spectral segment.  The torus is constrained by the four WISE bands only.
  Its fitted optical depth is at the grid upper bound (11.0), so the torus
  parameters are not a unique solution.
* `phot_calib_b` is a single mean scale over the four SDSS bands; it corrects
  the fibre-vs-imaging offset but does not fit a wavelength-dependent
  calibration curve.
* S3Fit's MC is a parametric bootstrap (mock spectra generated from the
  best-fit model + low-pass residual and refitted), not an MCMC posterior.
  The 10-mock distributions are adequate for flux/FWHM scatters but do not
  capture model-systematic uncertainty.
* The BLR H-beta and Mg II share one Gaussian FWHM and velocity; the Mg II
  2796/2804 doublet is tied at ratio 1.0.  This is a deliberate
  decomposition choice, not an independent fit of each broad line.
* `accept_chi_sq` and S3Fit's recycle logic can refit loops; the production
  run needed one recycle for two high-chi2 mocks, and all 11 loops finished
  successful.  Runtimes are reported in `run.json` (`runtime.total_sec`,
  `runtime.original_fit_sec`, `runtime.mc_fit_sec`).
