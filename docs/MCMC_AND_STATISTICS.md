# MCMC and statistical tests across the tools

See `docs/MCMC_CONVERGENCE_AUDIT.md` for the cross-tool step/tau audit and the
1-D acceptance-band correction.

This page separates **posterior sampling** from **uncertainty propagation**.  A
least-squares code with a covariance matrix is not an MCMC sampler, and a
broad-band SED code is not a line fitter.

| tool | native method | MCMC? | what is saved |
|---|---|---|---|
| `pyqsofit_uv` | least-squares; optional `emcee`; optional MC resampling | optional | `pyqsofit_mc_samples.csv`, `pyqsofit_mc.png` (100 MC realizations); MCMC corner only when stable |
| `optical_linefit` | least-squares covariance; local Hβ/[O III]; no MCMC | no | `optical_lines.csv`, `optical_lines_summary.json`, `optical_fit.png` |
| `qsofitmore_line` | least-squares; `MC=True` lmfit parametric bootstrap (200 realizations) | no | `qsofitmore_mc_samples.csv`, `qsofitmore_mc_summary.csv`, `qsofitmore_corner.png`, `qsofitmore_uncertainty.png` |
| `agnfitter_sed` | `ultranest` nested sampling | yes (nested) | posterior quantiles, realization PDFs |
| `cigale_sed` | `pdf_analysis` Bayesian likelihood/posterior | no | `sed_fit.png`, `sed_summary.csv`, model-family spread |
| `pahfit_mir` | least-squares + covariance/bootstrap MC (100-200 draws) | no | `pahfit_uncertainties.csv`, `pahfit_uncertainty.png` |
| `cafe_line` | LMFIT covariance + multivariate-normal MC (200 draws) | no | `cafe_uncertainties.csv`, `cafe_uncertainty.png` |
| `s3fit_line` | least-squares + mock-spectrum MC (`num_mocks`) | no | `s3fit_mc.png`, MC flux/FWHM distributions |
| `gandalf_line` | GANDALF/MPFIT covariance (`FOR_ERRORS`) | no | `gandalf_lines.csv`, error/covariance figure |
| `pyqsofitspec_line` | parametric bootstrap of line+continuum refits | no | bootstrap distributions/corner |
| `qgfit` | continuum `emcee`; line LSQ covariance | yes (continuum) | `qgfit_mcmc_summary.csv`, corner |
| `sheap_line` | JAX optimisation + 50-draw parametric-bootstrap MC | no | `sheap_mc_samples.csv`, uncertainty |
| `galspec_line` | emcee (`MCMC_Fit`, full-continuum global model); dynesty optional | yes (production) | `galspec_uncertainty.*`, `galspec_corner.*`, saved posterior in `galspec_mcmc.npz` |
| `ir_linefit` / `nir_linefit` / `fir_linefit` | `least_squares`/`curve_fit` covariance | no | per-line `flux_err`, `fwhm_err` |
| `manga_dap` | official DAP/SASUKE formal covariance (`1/sqrt(IVAR)`); no MCMC | no | `subset_comparison.json`, formal flux/kinematic errors; 9 central bins |
| `crossmission` | no sampler; same-object line-flux/EW comparison with quality flags | no | `xray_optical_comparison.json/csv/md/png`; **not** a correlation fit at N=2 |
| `xmm_xspec` | XSPEC chi-square (Levenberg-Marquardt); covariance; PN+MOS joint; `Delta chi^2` line significance | no | `xmm_fit.csv`, `xmm_lines.csv`, full `xspec.log`; no posterior |
| `rxte_xspec` | XSPEC chi-square (Levenberg-Marquardt); covariance; `Delta chi^2` line significance | no | `rxte_fit.csv`, `rxte_lines.csv`, full `xspec.log`; no posterior |
| `ppxf_host` | pPXF formal errors | no | `sigma_err_kms`, host error |
| `crossband` | analytic ratio propagation | no | `err` per ratio |

## QSOFITMORE: native Monte Carlo, no MCMC

`qsofitmore` 1.2.2 exposes `MC=True, n_trails=N`: it adds `N(0, err)` to the
calibrated spectrum and refits the continuum and each line complex with lmfit.
This is a frequentist parametric bootstrap, not an `emcee`/MCMC posterior; the
package has no MCMC sampler.  The production run uses **200 realizations**,
seed `20250101`, and records the H-beta/[O III] ratio from the same H-beta
complex draws (correlated errors) plus an independent Mg II complex.

The package's `<complex>_whole_br_area` column sums only Gaussians above its
1200 km/s classifier.  A multi-Gaussian broad template can contain narrower
Gaussians, so the compact table recomputes each physical line total from all
components.  This matters: for `04592649654` the package's H-beta broad column
is about half of the total H-beta flux, while the all-component total is
consistent with PyQSOFit/GANDALF.  The component-level split is degenerate;
the total is the stable quantity.  The production result is Hβ
3076.6±100.1, [O III] 5007 1505.3±57.3, Hβ/[O III] **2.044±0.102** (MC
p16–p84 1.960–2.103), and Mg II 2540.8±209.4; all 1,000 line-complex
realizations were valid.  The cross-tool nine-fitter median Hβ/[O III] is 2.04 with
0.053 dex scatter.  **The MC distributions are not Gaussian.**  Mg II is
bimodal: a high-quality mode near 2560 (best fit, χ²_r=1.38) and a lower
local-minimum mode near 2130 where both broad Gaussians hit the 0.004 ln-width
bound (χ²_r≈2.4).  The 16–84% interval 2133–2603 is the appropriate
uncertainty; the std 209 spans both modes.  Hβ total is mildly bimodal (modes
near 2900 and 3070; 16–84% 2895–3089).  These are template degeneracies, not
Gaussian errors.

## PyQSOFit: MCMC initialization fixed, short chain retained

The optional `emcee` path initially failed on `04592649654_z_0.5874` with
`Initial state has a large condition number`: two undetected [S II] amplitudes
were exactly zero and lmfit's default walker state had zero columns.  The
repair supplies a bounds-aware positive `pos` and records chains/tau/ESS.

A **10-step validation chain** (800 draws; 8 retained steps) is committed with
corner/trace/sample products.  A **300-step capped run** completed the fit
(1400.6 s) with acceptance ≈0.37 and τ_max 36–38, i.e. only ~6 τ steps; its
full chains were lost when the container timed out during the copy step.  The
short chain is **not converged**, so the committed quantitative uncertainty
remains the **100-realization MC**.  Both statuses are explicit in
`outputs/pyqsofit/04592649654_z_0.5874/mcmc/STATUS.md`.

## RXTE/PCA: chi-square and Delta chi-square, not MCMC

`rxte_xspec` fits the official PCA Standard2 spectrum with XSPEC's `chi`
statistic (grouped PHA, `STAT_ERR` from the official products).  Parameter
uncertainties are the XSPEC covariance (1-sigma).  The Fe K-alpha significance
is the Gaussian-equivalent one-sided p-value of
`chi2_sf(Delta chi^2, Delta dof)`: one degree of freedom for the fixed
6.4 keV / 50 eV narrow line, two for a free width, three for a free width and
centroid.  It is **not** a posterior and **not** a look-elsewhere-corrected
discovery significance.

The PCA `b2` file is a background **model**, not a measured background.  XSPEC
propagates its `STAT_ERR`, but the background-model systematics are not in the
errors.  The tool therefore reports a conservative variant with `nH` frozen to
the continuum-only value and a soft-blackbody continuum-systematic check.
For 3C 120 the narrow-line `Delta chi^2` is 17.8 (4.2 sigma) on the production
`tbabs*zpowerlw` baseline, 11.9 (3.5 sigma) with `nH` frozen to the continuum
value, 22.2 (4.7 sigma) in the 3-10 keV line band, and 53.9 (7.3 sigma) when a
soft blackbody is added.  The verified-data note's `Delta chi^2 ~ 82` is
reproduced only when `nH` is frozen near the Galactic value: at
`nH = 0.024e22 cm^-2` the diagnostic gives `Delta chi^2 = 89.3` (9.45 sigma),
but the corresponding continuum baseline is chi2/dof = 3.97, so the line is
absorbing continuum residuals.  That variant is reported but not adopted.
The production free-`nH` baseline (chi2/dof = 1.83 before the line, 1.50
after) gives 17.8.  The spread is the honest continuum/background systematic,
not a statistical error bar.

## Interpretation

- `ultranest` (AGNfitter) and CIGALE `pdf_analysis` give **posterior**
  distributions over SED parameters.
- S3Fit's `num_mocks` is a **mock-spectrum Monte Carlo**, not MCMC.
- CAFE, PAHFIT, pPXF, GANDALF and the Gaussian line fitters use
  **covariance or bootstrap/MC** uncertainties.  PAHFIT's `auto` mode now
  requires a full-rank covariance; rank-deficient cases fall back to the
  bootstrap and are flagged, including frozen-feature detection.
- Cross-tool comparisons use line **ratios** and FWHM, which are less sensitive
  to absolute flux calibration than raw fluxes.

## Current uncertainty runs

| tool | run | realizations | method | figure |
|---|---|---:|---|---|
| PyQSOFit | `04592649654` | 100 | MC error-array resampling | `outputs/pyqsofit/04592649654_z_0.5874/mc/pyqsofit_mc.png` |
| QSOFITMORE | `04592649654` | **200** | lmfit parametric bootstrap (continuum + line complexes) | `outputs/qsofitmore_line/04592649654_z_0.5874/qsofitmore_corner.png` |
| PyQSOFit MCMC | `04592649654` | 800 (10-step validation) | `emcee`, **not converged**; 300-step diagnostics | `outputs/pyqsofit/04592649654_z_0.5874/mcmc/pyqsofit_mcmc_corner.png` |
| S3Fit | `04592649654` | **10** | mock spectra (spec+sed) | `outputs/s3fit_line/04592649654_z_0.5874/s3fit_mc.png` |
| GalSpec | `04592649654` | 37,334 saved samples (thin 6; 224,000 post-burn draws) | full-continuum `emcee`, 80 walkers x 4000 steps; tau_max 342.6; retained nsteps/tau=8.2 (not converged) | `outputs/galspec_line/04592649654_z_0.5874/galspec_corner.png` |
| PyQSOFitSpec | `04592649654` | **53/55 valid** | parametric bootstrap | `outputs/pyqsofitspec_line/04592649654_z_0.5874/pyqsofitspec_bootstrap.png` |
| QGfit | `04592649654` | long continuum MCMC (2334 s) | `emcee` continuum; LSQ lines | `outputs/qgfit/04592649654_z_0.5874/qgfit_uncertainty.png` |
| SHEAP | `04592649654` | 50 | JAX + parametric-bootstrap MC (not MCMC) | `outputs/sheap_line/04592649654_z_0.5874/sheap_uncertainty.png` |
| CAFE | PDS 456 | 200 | LMFIT covariance multivariate normal | `outputs/cafe_line/PDS456_z_0.1840/cafe_uncertainty.png` |
| GANDALF | `04592649654` | formal errors | GDL/MPFIT `FOR_ERRORS=1` | `outputs/gandalf_line/04592649654_z_0.5874/gandalf_uncertainty.png` |
| PAHFIT | PDS 456 short/long/both, VV114, NGC 4151, NGC 253 | 100-200 each | full-rank covariance or full-refit bootstrap | `outputs/<source>/pahfit_mir/pahfit_uncertainty.png` |
| AGNfitter | 5 QSOs | nested sampling | `ultranest` | `outputs/<source>/agnfitter_sed/OUTPUT/.../SED_manyrealizations...pdf` |
| CIGALE | 5 QSOs × 2 tori | Bayesian `pdf_analysis` | posterior grid | `outputs/<source>/cigale_sed/*/sed_fit.png` |
| XMM-Newton | PDS 456 | none (XSPEC chi-square) | covariance + `Delta chi^2` line significance; PN+MOS | `outputs/xmm_xspec/PDS456_z_0.1840/xmm_fe_ka_zoom.png` |
| RXTE/PCA | 3C 120 + MCG-6-30-15 | none (XSPEC chi-square) | covariance + `Delta chi^2` line significance | `outputs/rxte_xspec/<source>/rxte_fe_ka_zoom.png` |
| crossmission | 3C 120 + PDS 456 | none (post-processing) | same-object flux/EW with quality flags; no correlation fit | `docs/xray_optical_comparison.png` |

`docs/line_tool_comparison.png` combines the line ratios measured by PyQSOFit,
S3Fit, GANDALF and PAHFIT; `docs/line_ratio_scatter.csv` reports the
inter-tool log scatter.  After the production reruns, the 04592649654
Hβ/[O III] 5007 values are: ZLINE 1.57, S3Fit 1.83, PyQSOFit 1.96,
GalSpec 2.21, GANDALF 2.07, PyQSOFitSpec 2.15, QGfit 2.50 and SHEAP 2.02.
The full lens is regenerated in `docs/line_ratio_scatter.csv`; the
well-tested trio (PyQSOFit/S3Fit/GANDALF) still agrees at 0.05 dex.


## MaNGA DAP (subset)

`manga_dap` is not an MCMC sampler.  The MaNGA DAP emission-line model
(`Sasuke`) returns formal Gaussian covariance errors; the MAPS stores
`1/sqrt(IVAR)`.  The production validation is the official full-method
`EmissionLineModel` on the 9 central single-spaxel bins of NGC 1194
(plateifu 9193-12701).  Against the published DAP MAPS at the same spaxels,
Hα/Hβ/[O III]/[N II]/[S II] median ratios are 0.9995-0.99999 and BPT agrees
9/9.  The all-spaxel 2397-bin fit exceeded the 58 min budget and was killed;
the published MAPS is the all-spaxel reference.  A fast fixed-continuum
all-spaxel run is kept only as an auxiliary diagnostic with
`FASTMODE_NOT_PRODUCTION`; it fails the validation (Hα ratio 2.37, BPT 41%)
and is not an error or posterior model.
