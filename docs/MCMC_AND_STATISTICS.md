# MCMC and statistical tests across the tools

This page separates **posterior sampling** from **uncertainty propagation**.  A
least-squares code with a covariance matrix is not an MCMC sampler, and a
broad-band SED code is not a line fitter.

| tool | native method | MCMC? | what is saved |
|---|---|---|---|
| `pyqsofit_uv` | least-squares; optional `emcee`; optional MC resampling | optional | `pyqsofit_mc_samples.csv`, `pyqsofit_mc.png` (100 MC realizations); MCMC corner only when stable |
| `agnfitter_sed` | `ultranest` nested sampling | yes (nested) | posterior quantiles, realization PDFs |
| `cigale_sed` | `pdf_analysis` Bayesian likelihood/posterior | no | `sed_fit.png`, `sed_summary.csv`, model-family spread |
| `pahfit_mir` | least-squares + covariance/bootstrap MC (100-200 draws) | no | `pahfit_uncertainties.csv`, `pahfit_uncertainty.png` |
| `cafe_line` | LMFIT covariance + multivariate-normal MC (200 draws) | no | `cafe_uncertainties.csv`, `cafe_uncertainty.png` |
| `s3fit_line` | least-squares + mock-spectrum MC (`num_mocks`) | no | `s3fit_mc.png`, MC flux/FWHM distributions |
| `gandalf_line` | GANDALF/MPFIT covariance (`FOR_ERRORS`) | no | `gandalf_lines.csv`, error/covariance figure |
| `pyqsofitspec_line` | parametric bootstrap of line+continuum refits | no | bootstrap distributions/corner |
| `qgfit` | continuum `emcee`; line LSQ covariance | yes (continuum) | `qgfit_mcmc_summary.csv`, corner |
| `sheap_line` | JAX optimisation + 50-draw covariance MC | no | `sheap_mc_samples.csv`, uncertainty |
| `galspec_line` | emcee (`MCMC_Fit`); dynesty optional | yes (default) | `galspec_uncertainty.*`, `galspec_corner.*` |
| `ir_linefit` / `nir_linefit` / `fir_linefit` | `least_squares`/`curve_fit` covariance | no | per-line `flux_err`, `fwhm_err` |
| `ppxf_host` | pPXF formal errors | no | `sigma_err_kms`, host error |
| `crossband` | analytic ratio propagation | no | `err` per ratio |

## PyQSOFit: MCMC attempted, MC used

The optional `emcee` path is implemented upstream.  On
`04592649654_z_0.5874` the continuum MCMC ran, but the line-complex MCMC
raised `emcee`'s "Initial state has a large condition number" because the
initial walkers mix amplitudes (10^-17) with logarithmic wavelengths and
velocity widths.  This is a PyQSOFit initialization limitation, not a
scientific result.  The production uncertainty run therefore uses **100
independent MC resamplings of the calibrated error array** and saves the
per-realization line fluxes.  This is labelled MC, not MCMC.

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
| S3Fit | `04592649654` | 3 | mock spectra (fast demo) | `outputs/04592649654_z_0.5874/s3fit_line/s3fit_mc.png` |
| GalSpec | `04592649654` | 2000 saved MCMC samples | `emcee` on reduced Hβ/[O III] | `outputs/04592649654_z_0.5874/galspec_line/galspec_corner.png` |
| PyQSOFitSpec | `04592649654` | 10 | parametric bootstrap | `outputs/04592649654_z_0.5874/pyqsofitspec_line/pyqsofitspec_bootstrap.png` |
| QGfit | `04592649654` | short continuum MCMC | `emcee` continuum; LSQ lines | `outputs/04592649654_z_0.5874/qgfit/qgfit_uncertainty.png` |
| SHEAP | `04592649654` | 50 | JAX + covariance MC (not MCMC) | `outputs/04592649654_z_0.5874/sheap_line/sheap_uncertainty.png` |
| CAFE | PDS 456 | 200 | LMFIT covariance multivariate normal | `outputs/PDS456_z_0.1840/cafe_line/cafe_uncertainty.png` |
| GANDALF | `04592649654` | formal errors | GDL/MPFIT `FOR_ERRORS=1` | `outputs/04592649654_z_0.5874/gandalf_line/gandalf_uncertainty.png` |
| PAHFIT | PDS 456 short/long/both, VV114, NGC 4151, NGC 253 | 100-200 each | full-rank covariance or full-refit bootstrap | `outputs/<source>/pahfit_mir/pahfit_uncertainty.png` |
| AGNfitter | 5 QSOs | nested sampling | `ultranest` | `outputs/<source>/agnfitter_sed/OUTPUT/.../SED_manyrealizations...pdf` |
| CIGALE | 5 QSOs × 2 tori | Bayesian `pdf_analysis` | posterior grid | `outputs/<source>/cigale_sed/*/sed_fit.png` |

`docs/line_tool_comparison.png` combines the line ratios measured by PyQSOFit,
S3Fit, GANDALF and PAHFIT; `docs/line_ratio_scatter.csv` reports the
inter-tool log scatter.  For 04592649654, the three optical tools give
Hβ/[O III] 5007 now spans 1.83–4.00 across seven tools; the median is 2.11
and the full log-scatter is 0.33 dex.  The three best-tested optical tools
(PyQSOFit/S3Fit/GANDALF) remain within 0.05 dex.
