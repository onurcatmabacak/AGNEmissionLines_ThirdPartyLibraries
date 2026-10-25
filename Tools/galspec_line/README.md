# `galspec_line` — GalSpec full-continuum QSO emission-line model (Docker)

Dockerised **GalSpec** (`https://github.com/jyshangguan/GalSpec`, pinned commit
`18e4effd796a1d51615ca2340bb927278eb18bbf`) applied to the repository's SDSS
QSO spectra.  The production path is a **full-continuum + emission-line**
model over the whole usable rest-frame spectrum, sampled with `emcee`.

The previous committed output was a reduced 4720-5150 A H-beta/[O III] fit.
That run is preserved as a legacy configuration in
`configs/galspec_line/reduced/`; it is not the production recipe.  The default
configuration (`configs/galspec_line/default/`) sets
`"model_mode": "full"`, and the committed `outputs/<source>/galspec_line/`
products below are from that full model.

## Audit of the previous reduced run

The committed pre-repair output was not a crash: it completed in 427 s with
`chi2_nu(raw)=1.926`, `chi2_nu(floored)=1.218` and a 17-parameter LSQ start.
Its capability gaps were:

* only the 4720-5150 A rest-frame window was modelled (379 pixels), with a
  local linear continuum, so there was no full UV/optical continuum;
* the `emcee` chain was 48 walkers x 4000 steps with 1500 burn-in;
  `tau_max=201.4` gave `nsteps/tau_max=19.9`, and the "2000 saved samples"
  were a `linspace` subsample of the 120,000 post-burn draws, not an
  independent posterior;
* H-beta narrow/broad/total were 1439.6/1798.5/3236.8 and [O III] 5007
  narrow/wing/total were 869.1/748.0/1618.7 (1e-17 units); the H-beta narrow
  FWHM was 1512 km/s, i.e. the "narrow" label was doing a lot of work;
* [O II], [Ne III] and [S II] were separate LSQ/covariance windows, not part
  of the MCMC likelihood, and Fe II was constrained only inside the small
  window;
* the comparison table covered PyQSOFit/GANDALF/S3Fit only;
* `galspec_model.csv` contained only the 379 main-window pixels, and the
  old top panel did not show a global model.

The full run below replaces that capability gap.  It does not reduce the
spectral model; it keeps 39 free parameters and samples the whole 2280-6459 A
rest-frame model.  The explicit compromise is chain length: 4000 steps at
80 walkers, `tau_max=342.6`, retained `nsteps/tau_max=8.2` (11.7 if total steps are used), ESS~654.

## Production model

```text
rest frame 2280-6460 A (all usable SDSS pixels; H-alpha is outside coverage)
normalised polynomial continuum, degree 4 (global)
+ park2022 Fe II template (GalSpec IronTemplate_new, 4000-5600 A)
+ H-beta narrow + broad
+ H-gamma broad, H-delta broad (kinematics tied to H-beta broad)
+ H-epsilon, H8-H12 narrow (H8-H12 tied to H-epsilon by Case-B ratios)
+ [O II] 3726/3729, [Ne III] 3869/3967, [Ne V] 3426
+ [S II] 4068/4076, [O III] 4363, He II 4686
+ [O III] 5007 core + wing; [O III] 4959 tied to 5007 by 2.98
+ Mg II 2796/2804 broad (doublet ratio 1.0, tied kinematics)
+ [O I] 6300/6363 (6363 tied by 3.05), [S III] 6312
```

The model has 39 free parameters.  The narrow lines share one NLR
sigma/dv; [O III] core, [O III] wing, broad Balmer and broad Mg II have their
own kinematic components.  The continuum is required to be positive over the
fitted range.  Fe II is an empirical template, not a physical model.

## Build / run

```bash
bash Pipelines/build_images.sh galspec_line

# production full-continuum run (the default config is full)
bash Pipelines/run_galspec_line_docker.sh \
  inputs/04592649654_z_0.5874 \
  outputs/04592649654_z_0.5874/galspec_line \
  --object 04592649654_z_0.5874

# through the matrix runner
.venv/bin/python pipeline/run_new_tools.py \
  --only 04592649654_z_0.5874 --tools galspec_line --force
```

Useful overrides:

```bash
--config configs/galspec_line/default   # full production config
--config configs/galspec_line/reduced   # legacy reduced-window fit
--sampler mcmc|nested|lsq               # production is mcmc
--z 0.58741307                          # override redshift
--mcmc-steps 4000 --nwalkers 80 --nburn 1200 --seed 42
```

The image is built from the repository root because it copies
`Tools/galspec_line/` and `configs/galspec_line/`.  The upstream package is
installed with pip from the pinned public git commit; no GalSpec source or
example data is vendored into this repository.  `nested` is retained as a
`dynesty` smoke-test path; the committed production output is `emcee`.

## Input and units

The driver accepts either:

* raw SDSS DR18 `COADD` table FITS (`FLUX`, `LOGLAM`, `IVAR`, `WDISP`, `WRESL`,
  `AND_MASK`, `SPALL.Z`); or
* a prepared PyQSOFit-style FITS (`HDU0` flux, `HDU1` wavelength, `HDU2`
  1-sigma error, header `z`).

SDSS `LOGLAM` is vacuum.  The adapter applies `PyAstronomy.pyasl.vactoair2`,
de-redshifts to the rest frame, and multiplies flux and error by `(1+z)` so
that `F_lambda_rest = F_lambda_obs (1+z)`, the same convention as the
PyQSOFit and GANDALF outputs in this repository.  Internal modelling is in
`1e-17 erg s-1 cm-2 A-1`; output fluxes are given in both `1e-17` and cgs.

A 2 per cent error floor relative to the fitted global continuum is added in
quadrature (`errors.floor_frac_of_continuum`).  Both raw and floored
chi-square values are recorded.

## Output

`outputs/<source>/galspec_line/`:

| file | contents |
|---|---|
| `galspec_lines.csv` | all line components and totals: rest wavelength, flux/flux_err in cgs and 1e-17, FWHM, velocity, S/N, detected, status, method, integration window |
| `galspec_fit.png/pdf` | full rest spectrum, full model, continuum+Fe II, residuals, and zooms for Mg II, [O II]/[Ne III]/Balmer, H-gamma/[O III] 4363, H-beta/[O III], red [O I]/[S III], H-delta/[S II] |
| `galspec_corner.png/pdf` | posterior corner plot of 12 physically important parameters |
| `galspec_uncertainty.png/pdf` | emcee trace and posterior line-flux histograms |
| `galspec_mcmc.npz` | saved posterior samples, log probability, parameter names, MAP, autocorrelation time, thinning, and derived line-flux arrays |
| `galspec_model.csv` | full-spectrum model decomposition: data, total, continuum, Fe II, per-line models, residuals |
| `galspec_comparison.csv` | H-beta/[O III] 5007 comparison with PyQSOFit, PyQSOFitSpec, GANDALF, S3Fit, QGfit and SHEAP |
| `config.effective.json` | exact effective configuration, input path, sampler and redshift |
| `run.json` | provenance, full model, LSQ quality, MCMC diagnostics, all line measurements, comparison, runtime, limitations |
| `galspec.log` | adapter log |

`status=not_covered` rows (H-alpha, [N II], red [S II]) have NaN fluxes.
`method=emcee_mcmc_full` identifies the production posterior; `lsq_full` is a
debug-only path and is never labelled MCMC.

## Sampler settings and convergence

The committed full run uses:

| setting | value |
|---|---:|
| walkers | 80 (`2*ndim+2`, ndim=39) |
| steps | 4000 |
| burn-in | 1200 |
| saved posterior | up to 40000 post-burn samples, thinned to fit the cap |
| derived posterior | 4000 post-burn samples |
| autocorrelation | `emcee` integrated time, `tol=0` with fallbacks |

`run.json` records `tau_max`, `tau_status`, `nsteps/tau_max`,
`effective_sample_size`, `n_steps_kept`, `saved_samples` and `saved_thin`.
A finite `tau_max` and a saved posterior of thousands of samples are the
minimum acceptance criteria; the run is not described as asymptotically
converged unless the retained `n_steps_kept/tau_max` is comfortably above 50.  This is a
wide-line QSO with a 39-parameter global model, so the chain is best treated
as a production posterior with an explicit convergence diagnostic rather
than a publication-grade 50-tau chain.

The LSQ start is a trust-region fit in three stages: polynomial + Fe II on
line-free pixels, full model with the continuum fixed, then joint refinement.
After the joint stage the continuum and Fe II values are restored to the
line-free solution, preventing broad lines from absorbing the global
continuum.  LSQ is only the starting point and a cross-check.

## Results (committed run)

| quantity | value |
|---|---:|
| input / model | `04592649654_z_0.5874`, full continuum |
| rest coverage | 2280-6459 A |
| pixels / line-free pixels | 4523 / 3236 |
| free parameters | 39 |
| chi2/nu raw / floored | 3.709 / 2.159 |
| LSQ start | 39.3 s |
| emcee | 80 walkers x 4000 steps, burn 1200 |
| acceptance fraction | 0.188 |
| tau_max | 342.6 steps |
| retained nsteps / tau_max | 8.2 |
| total nsteps / tau_max | 11.7 |
| effective sample size | 654 |
| saved posterior | 37334 samples, thin 6 |
| MCMC wall time | 3596.6 s |
| total wall time | 3703.0 s |

Line measurements (posterior median +/- 16th/84th percentile half-width):

| line | component | flux (1e-17) | FWHM (km/s) | velocity (km/s) | S/N |
|---|---|---:|---:|---:|---:|
| Hbeta | narrow | 1778.6 +/- 24.4 | 1698 +/- 17 | -3 | 73.0 |
| Hbeta | broad | 1937.5 +/- 34.4 | 7110 +/- 92 | -29 | 56.4 |
| Hbeta | total | 3718.5 +/- 28.6 | 1959 +/- 23 | 0 | 129.9 |
| OIII_5007 | narrow | 834.6 +/- 21.4 | 835 +/- 14 | -141 | 39.0 |
| OIII_5007 | wing | 844.8 +/- 26.2 | 1977 +/- 43 | -890 | 32.2 |
| OIII_5007 | total | 1680.6 +/- 13.1 | 1026 +/- 15 | -178 | 128.8 |
| MgII_2796 | broad | 818.1 +/- 10.6 | 2114 +/- 45 | -261 | 77.5 |
| Hgamma | total | 769.6 +/- 15.1 | 1665 +/- 20 | 0 | 51.1 |
| Hdelta | total | 257.8 +/- 11.3 | 1665 +/- 20 | 0 | 22.8 |
| OII_3726 | narrow | 197.1 +/- 29.8 | 1698 +/- 17 | -3 | 6.6 |
| NeIII_3869 | narrow | 232.3 +/- 11.4 | 1698 +/- 17 | -3 | 20.3 |

The run is a real full-continuum posterior, but it is not a 50-tau
publication chain: `tau_max=342.6` steps and retained `nsteps/tau_max=8.2`.  The
limited chain length is the explicit compromise for a 39-parameter global
model on a shared CPU host; the spectral model was not reduced.  The saved
37,334 samples (thin 6, 224,000 post-burn draws) are a posterior, not an
interpolation of a handful of points, and `effective_sample_size=654` is
reported so the correlation is visible.

## Comparison (committed run)

| line | component | GalSpec | reference tool | reference | ratio |
|---|---|---|---:|---:|---:|
| Hbeta | total | 3718.5 | pyqsofit_uv | 2905.1 | 1.280 |
| Hbeta | total | 3718.5 | pyqsofitspec_line | 3439.5 | 1.081 |
| Hbeta | total | 3718.5 | gandalf_line | 2950.8 | 1.260 |
| Hbeta | total | 3718.5 | s3fit_line | 2761.0 | 1.347 |
| Hbeta | total | 3718.5 | qgfit | 2915.2 | 1.276 |
| Hbeta | total | 3718.5 | sheap_line | 3256.3 | 1.142 |
| Hbeta | narrow | 1778.6 | pyqsofit_uv | 624.7 | 2.847 |
| Hbeta | narrow | 1778.6 | pyqsofitspec_line | 669.5 | 2.657 |
| Hbeta | narrow | 1778.6 | gandalf_line | 1486.4 | 1.197 |
| Hbeta | narrow | 1778.6 | s3fit_line | 669.7 | 2.656 |
| Hbeta | narrow | 1778.6 | sheap_line | 774.8 | 2.296 |
| Hbeta | broad | 1937.5 | pyqsofit_uv | 2280.4 | 0.850 |
| Hbeta | broad | 1937.5 | pyqsofitspec_line | 2769.9 | 0.699 |
| Hbeta | broad | 1937.5 | gandalf_line | 1464.4 | 1.323 |
| Hbeta | broad | 1937.5 | s3fit_line | 2091.4 | 0.926 |
| Hbeta | broad | 1937.5 | qgfit | 2915.2 | 0.665 |
| Hbeta | broad | 1937.5 | sheap_line | 2481.5 | 0.781 |
| OIII_5007 | total | 1680.6 | pyqsofit_uv | 1479.5 | 1.136 |
| OIII_5007 | total | 1680.6 | gandalf_line | 1422.7 | 1.181 |
| OIII_5007 | total | 1680.6 | s3fit_line | 1506.5 | 1.116 |
| OIII_5007 | total | 1680.6 | sheap_line | 814.4 | 2.064 |
| OIII_5007 | narrow | 834.6 | pyqsofit_uv | 813.8 | 1.026 |
| OIII_5007 | narrow | 834.6 | pyqsofitspec_line | 776.0 | 1.076 |
| OIII_5007 | narrow | 834.6 | gandalf_line | 1422.7 | 0.587 |
| OIII_5007 | narrow | 834.6 | s3fit_line | 1506.5 | 0.554 |
| OIII_5007 | total | 1680.6 | qgfit | 1166.9 | 1.440 |
| OIII_5007 | narrow | 834.6 | qgfit | 1166.9 | 0.715 |
| OIII_5007 | narrow | 834.6 | sheap_line | 814.4 | 1.025 |

QGfit has no separate total [O III] 5007 row; its single narrow component is
used as the total in the table (and is also listed as `OIII5007/narrow`); SHEAP has only one [O III] component, so its
"total" is effectively a core-only flux.  PyQSOFitSpec's total H-beta is the
sum of its broad+narrow rows.  Component ratios are not directly
interchangeable because each tool defines narrow/broad and core/wing
differently; the total-flux ratios are the robust comparison.

## Caveats

* The continuum is a global polynomial plus Fe II, not a QSO principal
  component or host/stellar decomposition.  Absolute continuum systematics
  (flux calibration, slit losses, intrinsic variability) are not propagated
  into the line-flux errors.
* Fe II is the empirical park2022 template (4000-5600 A).  UV Fe II blends
  below 4000 A are absorbed by the polynomial continuum, not modelled
  explicitly.  A separate Balmer pseudo-continuum is not included: explicit
  Balmer lines H-beta through H12 are fitted, while broad high-order Balmer
  lines are blended with Fe II and are not separately resolved.
* The narrow/broad and [O III] core/wing splits are empirical Gaussian
  decompositions.  Their ratios are not directly interchangeable with other
  tools' component definitions; compare totals and widths.
* H-alpha, [N II] 6548/6583 and red [S II] 6716/6731 are outside this
  z=0.5874 SDSS coverage.  They are `not_covered`, not fitted.
* The narrow lines share one sigma/dv.  This is a deliberate identifiability
  choice at SDSS resolution; it can bias individual weak-line widths.
* Mg II is modelled as a broad doublet with tied kinematics and a fixed 1:1
  doublet ratio.  The UV iron blends and the Balmer pseudo-continuum are not
  part of that fit, so the Mg II flux is less robust than H-beta/[O III]; the
  combined Mg II 2796+2804 broad flux (1638 in 1e-17 units) is lower than
  PyQSOFit's 2517 because PyQSOFit includes UV Fe II and a different UV
  continuum.
* Broad H-gamma and H-delta are not detected in this spectrum (S/N < 1 in the
  committed posterior); the broad Balmer signal is carried by H-beta.  The
  red [O I] 6300/[S III] 6312 lines sit in a region with SDSS sky residuals
  and are correspondingly less reliable than the blue/optical lines.
* Intrinsic FWHM subtracts the SDSS `WRESL` resolution in quadrature; the
  observed FWHM is also stored.
* The full image build needs network access to install the pinned GalSpec
  commit.  Third-party licences remain with their upstream projects.

Upstream: GalSpec, MIT licence, `https://github.com/jyshangguan/GalSpec`.
