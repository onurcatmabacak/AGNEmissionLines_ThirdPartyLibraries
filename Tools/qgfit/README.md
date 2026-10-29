# `qgfit` — QGfit continuum + emission-line fit (Docker)

Dockerised **QGfit 1.0.0** (`https://github.com/qian-yang/QGfit`, commit
`3aed692`, 2025-01-03) applied to the repository's SDSS QSO spectra.  QGfit
fits a broken power-law AGN continuum, UV/optical Fe II templates, an optional
Balmer continuum, a BC03 host-galaxy SED, and skewed-Voigt emission lines
(with [O III] and Balmer-line kinematic ties).

The adapter also provides production diagnostics that upstream QGfit does not:
a longer continuum emcee chain with autocorrelation/width checks, per-complex
line-MCMC diagnostics, per-complex line zooms, residuals, an effective config,
and a five-tool component comparison.

## Build / run

```bash
bash pipeline/runners/build_images.sh qgfit

# Production run (100 x 1000 continuum MCMC, LSQ line covariance).
bash pipeline/runners/run_qgfit_docker.sh \
  inputs/04592649654_z_0.5874 \
  outputs/qgfit/04592649654_z_0.5874 \
  --config configs/qgfit/production \
  --z 0.58741307

# Fast smoke/demo run (40 x 100 continuum MCMC, LSQ lines).
bash pipeline/runners/run_qgfit_docker.sh \
  inputs/04592649654_z_0.5874 /tmp/qgfit_demo \
  --config configs/qgfit/default --z 0.58741307
```

or through the source-keyed matrix:

```bash
.venv/bin/python pipeline/run_new_tools.py \
  --only 04592649654_z_0.5874 --tools qgfit --force
```

The pipeline auto-detects `pyqsofit_uv/`, `gandalf_line/`, `s3fit_line/`,
`galspec_line/` and `pyqsofitspec_line/` next to the output directory; use
`--reference DIR` to point at a different parent directory.

## Inputs

* `inputs/<source>_z_<z>/raw/spec-*.fits` — SDSS `COADD` table with `FLUX`
  (1e-17 erg s-1 cm-2 A-1), `LOGLAM` (vacuum), `IVAR`, `AND_MASK`.
* QGfit reads the SDSS file directly; no prepared copy is needed.
* `--z` overrides the manifest redshift.  RA/Dec come from `PLUG_RA`/`PLUG_DEC`.
* Pixels with `IVAR<=0`, non-finite values, or non-zero `AND_MASK` are removed
  before fitting (4621/4648 pixels remain for this source).

## What is fitted

| component | QGfit model | production |
|---|---|---|
| AGN continuum | broken power law | yes |
| UV Fe II | bundled `fe_uv.txt`, broadened/shifted | yes |
| optical Fe II | bundled `fe_op.txt` | yes |
| Balmer continuum | non-LTE Balmer model | no |
| host galaxy | bundled BC03 SSP grid, young+old | yes (`z=0.587 < 1.2`) |
| emission lines | skewed Voigt, broad/narrow/mix | all covered complexes |

The fitted complexes are H-beta/[O III] 4959/5007, H-gamma/[O III] 4363,
H-delta/[S II] 4070, H-epsilon/He I 3889/[Ne III], He I 5877, [O I]
6300/6365, [N I] 5200, [O II] 3727/[Fe VII], Mg II, C III]/Al III,
C IV/He II/O III], and Ly-alpha/N V.  H-alpha/[N II]/[S II] are outside the
SDSS coverage at z=0.587 (rest-frame maximum 6510 A).

## Configurations

See `configs/qgfit/README.md` for the full table.  The production controls are:

* `conti_pl`, `conti_fe_uv`, `conti_fe_op`, `conti_host` all enabled;
  `conti_balmer` disabled.
* `check_kmpfit: true`, `conti_redchi_limit: 1.5`: QGfit attempts its KMPFIT
  fallback and keeps the better of LSQ/KMPFIT.  On this object LSQ
  (chi2_nu=16.81) beats KMPFIT (18.09), so the final continuum is LSQ.
* `conti_mcmc: true`, 100 walkers x 1000 steps, burn 200, seed 42.
* `line_mcmc: false`; line flux errors come from QGfit's least-squares
  covariance (`norm_stderr`).  A 50 x 300 line-MCMC pilot was unstable (see
  below) and was not used in production.
* `mask_lowSN: false`; invalid pixels are already removed by the adapter.
* `mcmc_init_scale: 0` (lmfit's small-ball start); covariance-based starts were
  tested and rejected (see audit findings).

## Statistical mode (honest labels)

| product | method |
|---|---|
| continuum + lines | `lmfit` least-squares (KMPFIT fallback attempted and recorded) |
| `qgfit_uncertainty.png/pdf` | emcee continuum chain, 100 x 1000, burn 200 |
| `qgfit_mcmc_summary.csv` | per-parameter continuum quantiles, tau, LSQ width ratio |
| `qgfit_line_errors.png` | LSQ covariance: `sigma(flux) = flux * sigma(norm)/norm` |
| line MCMC | disabled in production (pilot unstable) |

The continuum chain is checked three ways before `run.json` sets
`continuum_converged: true`:

1. `N_tau = steps_after_burn / tau_max >= 50`, from
   `emcee.autocorr.integrated_time`;
2. mean acceptance in 0.05-0.70;
3. median posterior width in 0.5-2.0 times `stderr_lsq/sqrt(redchi_nu)` for
   well-constrained, non-bound parameters.

The third check is essential: lmfit starts every walker in a 1e-4 relative ball
around the LSQ solution.  A 100-step chain is still expanding and its marginal
errors are 10-30 times too small.  The production run uses 1000 steps to give
the ensemble time to reach the posterior width; the width ratio and `N_tau` are
reported in `run.json` and in the corner title.

## Production results (04592649654, z=0.58741307)

The production run finished in **2334.5 s (38.9 min)** inside the container:
20.0 s continuum LSQ/KMPFIT, 2014.0 s continuum MCMC, 50.6 s line fit,
22.1 s figures/native PDF.  Native QGfit results:

| quantity | QGfit native | PyQSOFit | GANDALF | S3Fit | GalSpec | PyQSOFitSpec |
|---|---:|---:|---:|---:|---:|---:|
| H-beta total (1e-17) | 2915.2 +/- 170.4 | 2905 | 2951 +/- 33 | 2761 +/- 4 | 3237 +/- 38 | 3439 +/- 42 |
| [O III] 5007 (1e-17) | 1166.9 +/- 22.4 | 1480 | 1423 +/- 12 | 1507 +/- 9 | 1619 +/- 14 | 1631 +/- 250 |
| H-beta/[O III] 5007 | 2.498 +/- 0.154 | 1.96 | 2.07 +/- 0.03 | 1.83 +/- 0.01 | 2.00 +/- 0.03 | 2.11 +/- 0.45 |
| QGfit/reference H-beta | — | 1.00 | 0.99 | 1.06 | 0.90 | 0.85 |
| QGfit/reference [O III] | — | 0.79 | 0.82 | 0.77 | 0.72 | 0.72 |

The H-beta total agrees with PyQSOFit and GANDALF at the 0-1 % level and with
S3Fit at 6 %; GalSpec and PyQSOFitSpec recover 10-18 % more H-beta.  The
[O III] 5007 flux is 18-28 % lower than every sibling, so the H-beta/[O III]
ratio is high.

### Continuum MCMC

100 walkers x 1000 steps (burn 200), acceptance 0.297, `tau_max`=99.5 steps,
`N_tau`=8.0, median MCMC/LSQ width ratio **1.41** for 13 well-constrained
parameters.  The marginal widths now agree with the LSQ covariance (the old
40 x 100 chain was 10-30x too narrow), but the chain is only 8 integrated
autocorrelation times long.  Reaching `N_tau=50` would require ~4977 steps,
i.e. ~2.8 h at the measured ~2 s per step; the production budget stopped at
1000 steps.  `run.json` therefore reports `width_converged: true`,
`tau_converged: false`, `converged: false`, and the chain is not used to
replace the LSQ continuum best fit.

The MCMC median continuum is offset from the LSQ solution (`pl_norm` 204 vs
177, `pl_slope1` -1.35 vs -1.45) because the host/Fe II parameters are
degenerate; the line fit uses the LSQ continuum.  This does not change the
[O III] conclusion: the expanded-template run uses the same LSQ continuum and
still moves the ratio from 2.50 to 2.30.

### Why the native 2.50 ratio is a line-component effect

QGfit's native narrow-line profile has a hard-coded `ln_sigma` maximum of
0.0017 (FWHM <= 1200 km/s); `fwhm_narrow_max` in the config does not change
that internal limit.  The native fit puts both [O III] lines at FWHM 1131 km/s,
close to the cap, and recovers 1167 in [O III] 5007.

The sibling decompositions show what is missing:

| tool | H-beta broad | H-beta narrow | [O III] 5007 core | [O III] 5007 wing |
|---|---:|---:|---:|---:|
| QGfit native | 2915, FWHM 1935 | 0 (BIC removed) | 1167, FWHM 1131 | none |
| PyQSOFit | 2280, FWHM 3550 | 625, FWHM 847 | 814, FWHM 847 | 666, FWHM 1653 |
| GANDALF | 1464, FWHM 4896 | 1486, FWHM 1532 | 1423, FWHM 1532 | none |
| S3Fit | 2091, FWHM 2934 | 670, FWHM 1409 | 1507, FWHM 1409 | none |
| GalSpec | 1798, FWHM 5053 | 1440, FWHM 1512 | 869, FWHM 856 | 748, FWHM 1875 |
| PyQSOFitSpec | 2770, FWHM 3866 | 670, FWHM 848 | 776, FWHM 837 | 855, FWHM 1741 |

Every sibling either uses a single [O III] Gaussian broader than QGfit's
1200 km/s cap (GANDALF: 1532; S3Fit: 1409) or fits an explicit broad wing
(PyQSOFit, GalSpec, PyQSOFitSpec: FWHM 1650-1875).  QGfit's native model has
neither.  The H-beta total is robust; the [O III] denominator is not.

A controlled expanded-template run (`configs/qgfit/production_wing/`) removes
the H-beta narrow row (which QGfit's BIC already zeroes) and adds
`OIII4959w`/`OIII5007w` mix components.  With the same LSQ continuum it
recovers H-beta 2864.6 +/- 56.1 (FWHM 1980), [O III] 5007 narrow 630.3 + wing
615.6 = 1245.9 +/- 340.5, and H-beta/[O III] = 2.299 +/- 0.630 (the total
error is conservative because the narrow/wing covariance is not exposed).
The H-beta complex BIC improves from 1031.4 to 951.1 and chi2_nu from 10.95 to
8.58; the run took 177.5 s.  The ratio is therefore set by the line-component
definition, not by the AGN power law, Fe II or the host.

## Audit findings and fixes

* **QGfit cannot run an LSQ-only fit upstream.**  With `check_kmpfit=false`
  and `check_nelder=false`, `run_fit_conti` and `run_fit_line_one` left the
  local `out` unbound and raised `UnboundLocalError`.  The vendored copy now
  starts from `out = out_leastsq` (marked in the source).
* **`prop=True` with `conti_mcmc=False` and `save_conti_chains=True` raised
  `KeyError('mcmc')`.**  `cal_prop` now reads the chain only when the `mcmc`
  block exists.
* **The committed 40 x 100 continuum MCMC was not merely short.**  Its
  marginal widths were 10-30 times smaller than the LSQ covariance
  (e.g. `pl_norm` 0.37 vs 12.05) because the walkers never expanded out of
  lmfit's 1e-4 ball.  The production run uses 1000 steps and reports the
  width check.  A covariance-based start was tested and rejected: it put
  walkers in invalid host/Fe II corners (`redchi_mcmc` ~1e9-1e10).
* **Line MCMC is unstable at feasible chain lengths.**  A 50 x 300 pilot gave
  per-complex integrated autocorrelation times of 20-42 steps (`N_tau` ~5-11)
  and a pathological `redchi_mcmc` ~6e10 against LSQ chi2_nu=11.5.  The
  production run keeps LSQ covariance errors and labels every line
  `qgfit_leastsq`; it is not described as an MCMC line fit.  A converged line
  chain would need roughly 800-1500 steps per complex, i.e. an order of
  magnitude more runtime.
* **The H-beta narrow component is removed by QGfit's BIC cleanup** on this
  object; the H-beta total is broad-only.  The total flux is still consistent
  with PyQSOFit/GANDALF.
* **Two line complexes are poorly modelled by the native template.**  The
  [O II] 3727/[Fe VII] complex is left with chi2_nu=84.7 and zero fitted
  [O II] flux (the data show a clear 3727 spike), and He I 5877 has
  chi2_nu=5.28 with the broad component removed.  These failures do not enter
  the H-beta/[O III] ratio but are visible in `qgfit_zoom.png` and the
  per-complex table in `run.json`.
* **The continuum chi2_nu is high (16.81).**  The simple power law + Fe II +
  BC03 model cannot reproduce every broad Fe II bump in a luminous QSO at the
  SDSS error level.  Several host parameters hit bounds (`fe_uv_fwhm=10000`,
  `age_old=12.75/13`, `sigma=500/500`), but the host contributes only a few
  percent of the flux at 5000 A and does not explain the [O III] difference.
* **SFD/dust:** `do_deredden=false`; the SFD maps are not shipped.  The
  sibling tools also use the observed SDSS spectrum with no Galactic
  dereddening (PyQSOFit/GalSpec set `deredden=false`).  The adapter refuses to
  run with `do_deredden=true` if the maps are absent.
* **Units:** input is observed-frame 1e-17 f_lambda; QGfit stores rest-frame
  `f_rest = f_obs (1+z)^3`; line fluxes are reported in observed-frame
  equivalents `F_rest/(1+z)^2`.  `qgfit_model.csv` is rest-frame f_lambda, not
  observed-frame like some sibling model files.

## Runtime

The production run took **2334.5 s (38.9 min)** inside the container on the
shared 8-core host: 20.0 s continuum LSQ/KMPFIT, 2014.0 s continuum MCMC
(100 x 1000), 50.6 s line fit, 22.1 s figures/native PDF, and the remainder in
I/O/comparison.  The fast 40 x 100 demo takes ~305 s, of which ~87 s is the
continuum MCMC.  The complete breakdown is in `run.json`.

## Outputs

```text
outputs/<source>_z_<z>/qgfit/
  qgfit_lines.csv                 line, component, flux, error, FWHM, method
  qgfit_model.csv                 rest-frame data / continuum / line / total model
  qgfit_fit.png/.pdf              full spectrum + H-beta/[O III] zoom + residual
  qgfit_zoom.png/.pdf             one panel per fitted emission-line complex
  qgfit_residual.png/.pdf         full-spectrum and zoom residuals
  qgfit_uncertainty.png/.pdf      continuum MCMC corner
  qgfit_line_errors.png           line-flux error bars
  qgfit_mcmc_summary.csv          continuum quantiles, tau, LSQ width ratio
  qgfit_mcmc_chain.npz            continuum chain (thinned to 20000 samples)
  qgfit_line_mcmc_summary.csv     per-complex line-MCMC status (disabled/rejected)
  qgfit_native.pdf                QGfit's own multi-panel PDF
  qgfit_native_corner.jpg         QGfit's own corner plot
  qgfit.pkl                       trimmed native result
  qgfit_comparison.csv            QGfit vs sibling total line fluxes
  qgfit_component_comparison.csv  broad/narrow/wing component comparison
  qgfit_ratio_comparison.csv      H-beta/[O III] for QGfit and five siblings
  qgfit_config.effective.json     effective QGfit configuration
  run.json                        provenance, diagnostics, method, timings
  expanded_template/              expanded [O III] wing diagnostic run
```

## Caveats

* Line MCMC is not used in production; line errors are LSQ covariance, not
  posterior quantiles.  The `qgfit_line_mcmc_summary.csv` records why.
* The continuum MCMC does not include the line parameters; line and continuum
  uncertainties are not propagated into each other.
* The continuum chi2_nu is high and several host parameters are at bounds;
  the host is a minor contributor at 5000 A but the Fe II/host decomposition
  is not unique.
* QGfit's BIC cleanup removes the H-beta narrow component; the native
  [O III] width is capped at 1200 km/s.  Use the expanded template when the
  [O III] wing matters scientifically.
* H-alpha/[N II]/[S II] are outside the SDSS coverage at this redshift.

## Licensing and local patches

QGfit's `setup.py`/README declare MIT, but the pinned upstream commit has no
`LICENSE` file.  The vendored source retains the upstream headers and this
repository does not relicense it.  See `THIRD_PARTY_LICENSES.md`; the two small
source fixes (LSQ-only `out`, and `prop` without an MCMC block) are documented
there.  The adapter-side MCMC diagnostics are in `run_qgfit.py`.
