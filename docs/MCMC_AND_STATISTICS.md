# MCMC and statistical tests across the tools

This page separates **posterior sampling** from **uncertainty propagation**.  A
least-squares code with a covariance matrix is not an MCMC sampler, and a
broad-band SED code is not a line fitter.

| tool | native method | MCMC? | what is saved |
|---|---|---|---|
| `pyqsofit_uv` | least-squares; optional `emcee`; optional MC resampling | optional | `pyqsofit_mc_samples.csv`, `pyqsofit_mc.png` (100 MC realizations); MCMC corner only when stable |
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
| `xmm_xspec` | XSPEC χ² minimisation + covariance (1σ); Δχ² line significance | no | `xmm_fit.csv`, `xmm_lines.csv`, `xmm_consistency.json`, `xspec.log` |
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
realizations were valid.  The cross-tool median Hβ/[O III] is 2.074 with
0.060 dex scatter.  **The MC distributions are not Gaussian.**  Mg II is
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
`outputs/04592649654_z_0.5874/pyqsofit/mcmc/STATUS.md`.

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
| PyQSOFit | `04592649654` | 100 | MC error-array resampling | `outputs/04592649654_z_0.5874/pyqsofit/mc/pyqsofit_mc.png` |
| QSOFITMORE | `04592649654` | **200** | lmfit parametric bootstrap (continuum + line complexes) | `outputs/04592649654_z_0.5874/qsofitmore_line/qsofitmore_corner.png` |
| PyQSOFit MCMC | `04592649654` | 800 (10-step validation) | `emcee`, **not converged**; 300-step diagnostics | `outputs/04592649654_z_0.5874/pyqsofit/mcmc/pyqsofit_mcmc_corner.png` |
| S3Fit | `04592649654` | **10** | mock spectra (spec+sed) | `outputs/04592649654_z_0.5874/s3fit_line/s3fit_mc.png` |
| GalSpec | `04592649654` | 37,334 saved samples (thin 6; 224,000 post-burn draws) | full-continuum `emcee`, 80 walkers x 4000 steps, tau_max 342.6 | `outputs/04592649654_z_0.5874/galspec_line/galspec_corner.png` |
| PyQSOFitSpec | `04592649654` | **53/55 valid** | parametric bootstrap | `outputs/04592649654_z_0.5874/pyqsofitspec_line/pyqsofitspec_bootstrap.png` |
| QGfit | `04592649654` | long continuum MCMC (2334 s) | `emcee` continuum; LSQ lines | `outputs/04592649654_z_0.5874/qgfit/qgfit_uncertainty.png` |
| SHEAP | `04592649654` | 50 | JAX + parametric-bootstrap MC (not MCMC) | `outputs/04592649654_z_0.5874/sheap_line/sheap_uncertainty.png` |
| CAFE | PDS 456 | 200 | LMFIT covariance multivariate normal | `outputs/PDS456_z_0.1840/cafe_line/cafe_uncertainty.png` |
| GANDALF | `04592649654` | formal errors | GDL/MPFIT `FOR_ERRORS=1` | `outputs/04592649654_z_0.5874/gandalf_line/gandalf_uncertainty.png` |
| PAHFIT | PDS 456 short/long/both, VV114, NGC 4151, NGC 253 | 100-200 each | full-rank covariance or full-refit bootstrap | `outputs/<source>/pahfit_mir/pahfit_uncertainty.png` |
| AGNfitter | 5 QSOs | nested sampling | `ultranest` | `outputs/<source>/agnfitter_sed/OUTPUT/.../SED_manyrealizations...pdf` |
| CIGALE | 5 QSOs × 2 tori | Bayesian `pdf_analysis` | posterior grid | `outputs/<source>/cigale_sed/*/sed_fit.png` |

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


## XMM-Newton XSPEC (`xmm_xspec`)

`xmm_xspec` is a frequentist XSPEC/PyXspec fit, not an MCMC sampler.  The
grouped PPS spectra are fitted by minimising χ² (Levenberg–Marquardt); the
1σ parameter errors are from the XSPEC covariance matrix.  No posterior or
chain is produced.

The line detection is a **nested-model Δχ² test**:

* baseline `tbabs*zpowerlw` versus baseline + `zgauss` at 6.4 keV rest;
* the narrow-core fit has one extra parameter (line normalization), so the
  Gaussian-equivalent significance is √Δχ²; the production fit gives
  Δχ² = 16.39, i.e. **4.05σ**;
* the free-centroid fit has two extra parameters (energy and normalization);
  the p-value is from the χ² distribution with 2 dof, and the reported
  significance is the equivalent one-sided Gaussian;
* the free-width fit is a diagnostic only: its width runs to the fit bound and
  is degenerate with the continuum, so it is not used for the production
  line flux/EW.

The flux and EW are derived from the fitted `zgauss` normalization:

```text
F_line = norm * E_obs * 1.602e-9 erg cm^-2 s^-1
EW_rest = norm * (1+z) / F_ph,cont(E_obs)
```

where `E_obs = 6.4/(1+z)` keV and `F_ph,cont` is the fitted power-law photon
flux density at `E_obs`.  XSPEC's `eqwidth` value is also recorded; it is
slightly lower because it evaluates the total model (including the line) at
the line peak.  The PN/MOS consistency is quantified with pulls on Γ, N_H and
the line normalization, plus the fitted cross-calibration constants.

The absolute χ²/dof (1.70 for the simple baseline, 1.68 with the line) is poor
because the soft excess and Compton reflection are not modeled; this is a
diagnostic, not an acceptance gate.  The line significance is relative to the
same baseline and is checked against a blackbody soft-excess baseline
(Δχ² = 17.83, 4.22σ).
