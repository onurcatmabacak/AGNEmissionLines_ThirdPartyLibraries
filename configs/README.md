# Tool configurations

Central, reviewable configuration for every production tool.  Each tool has a
`configs/<tool>/<variant>/` directory.  New line-fit tools (`cafe_line`,
`s3fit_line`, `gandalf_line`, `galspec_line`, `pyqsofitspec_line`, `qgfit`,
`sheap_line`) consume these files directly through `--config`;
older tools use the same values as their documented defaults and their code
contains the executable implementation.

## SED vs spectrum decomposition

The two families are deliberately separate:

| family | tools | output |
|---|---|---|
| Broad-band SED / torus | `cigale_sed`, `agnfitter_sed` | stellar mass, AGN fraction, torus luminosity, model-family spread |
| Spectral line fitting | `pyqsofit_uv`, `optical_linefit`, `qsofitmore_line`, `pyqsofitspec_line`, `ir_linefit`, `nir_linefit`, `fir_linefit`, `pahfit_mir`, `cafe_line`, `s3fit_line`, `gandalf_line`, `galspec_line`, `qgfit`, `sheap_line`, `manga_dap`, `xmm_xspec`, `rxte_xspec`, `crossmission`, `crossband` | line flux, FWHM, velocity, equivalent width, ratios, X-ray Fe K-alpha |
| Host/continuum decomposition | `ppxf_host` | stellar velocity dispersion, host fraction |

`gandalf_line/default/` is a complete tool configuration rather than a tuning
variant: it contains the GANDALF emission-line setup and the fit controls
(`config.json`). See `configs/gandalf_line/README.md`.
`galspec_line/default/` is likewise a complete configuration: main/aux windows,
continuum and Fe II, Gaussian component bounds, fitter, error floor and
emcee/dynesty controls. See `configs/galspec_line/README.md`.
`manga_dap/default/` is a complete configuration: `config.json`, the full
`plan.toml`, the Stage-A `plan_moments.toml`, the full-method subset
`plan_subset.toml` and `line_database.csv`.  The accepted result is the
full-method SASUKE fit on the 9 central single-spaxel bins; the fast
fixed-continuum all-spaxel mode is flagged `FASTMODE_NOT_PRODUCTION`.  See
`configs/manga_dap/default/README.md`.

`rxte_xspec/default/` is a complete configuration for the official RXTE/PCA
fit: 3-20 keV production band, 3-10 keV line-band cross-check, `tbabs*(zpowerlw
+ zgauss)`, Fe K-alpha rest energy 6.4 keV, fixed 50 eV narrow core, free-width
and free-centroid diagnostics, a conservative `nH`-frozen variant and a
soft-blackbody continuum-systematic check.  `configs/rxte_xspec/mcg6-30-15/`
is the second independent AGN variant.  See `configs/rxte_xspec/README.md`.

`qsofitmore_line/default/` is a complete configuration: the effective line
table, the V09 Fe II / broken power law / Balmer-continuum switches, the
SFD98+F99 extinction choice, the 1200 km/s narrow-line cap, and the 200-draw
lmfit Monte Carlo mode. See `configs/qsofitmore_line/default/README.md`.

Legacy `pipeline/auto_tune.py` (wrapper `analyze.sh`) generated variants under
`configs/<tool>/auto_<tool>_<knob values>/`; those search artifacts were removed
during the layout cleanup.

CIGALE/AGNfitter must **not** be described as emission-line fitters; they fit
the broad-band SED with templates.

## Uncertainty / sampling modes

| tool | statistical method |
|---|---|
| `pyqsofit_uv` | covariance; optional MC resampling and `emcee` MCMC (`PYQSOFIT_MC`, `PYQSOFIT_MCMC`) |
| `optical_linefit` | least-squares covariance; local Hβ/[O III] joint fit; no MCMC |
| `qsofitmore_line` | lmfit parametric Monte Carlo (`MC=True`, `n_trails=200`); no MCMC sampler in qsofitmore 1.2.2 |
| `pyqsofitspec_line` | parametric bootstrap: `flux + N(0, err)` refit, mean/std over `nboot_fit` (no covariance/MC inside a fit) |
| `agnfitter_sed` | `ultranest` nested sampling (Bayesian posterior) |
| `cigale_sed` | `pdf_analysis` Bayesian likelihood/posterior; not MCMC |
| `pahfit_mir` | least-squares; MC uncertainty/refit option |
| `cafe_line` | LMFIT covariance + post-fit multivariate-normal MC |
| `s3fit_line` | least-squares + mock-spectrum Monte Carlo (`num_mocks`) |
| `galspec_line` | `emcee` posterior (GalSpec `MCMC_Fit`); optional `dynesty` nested sampling; LSQ covariance for auxiliary windows |
| `qgfit` | short continuum `emcee` MCMC; line LSQ covariance |
| `sheap_line` | JAX optimisation + parametric-bootstrap MC (not MCMC) |
| `gandalf_line` | native MPFIT covariance/`FOR_ERRORS`; fallback bootstrap if GDL unavailable |
| `ir_linefit`/`nir_linefit`/`fir_linefit` | covariance from `least_squares`/`curve_fit` |
| `manga_dap` | DAP formal covariance (`1/sqrt(IVAR)`); no MCMC; official full-method SASUKE on 9 central bins |
| `xmm_xspec` | XSPEC chi-square covariance; PN+MOS joint fit; Fe K-alpha Delta chi^2; no MCMC |
| `crossmission` | no sampler; same-object flux/EW consistency with explicit quality flags; N=2 is not a correlation fit |
| `rxte_xspec` | XSPEC chi-square covariance; `Delta chi^2` line significance; no MCMC; PCA background model systematics reported separately |
| `ppxf_host` | pPXF formal errors |
| `crossband` | analytic ratio error propagation |

## Layout

```
configs/
  pyqsofit/uv/main.py              # executable
  pyqsofit/uv/config.json          # effective settings snapshot
  optical_linefit/default/config.json
  qsofitmore_line/default/config.json    # fit switches + uncertainty mode
  qsofitmore_line/default/line_table.csv # effective editable line table
  qsofitmore_line/default/README.md      # switch-by-switch notes
  pyqsofitspec_line/default/config.json  # executable line table + bootstrap controls
  badass/{best,nbasin20}/main.py
  ...
  ir_linefit/default/config.json
  nir_linefit/{default,psf}/config.json
  fir_linefit/default/config.json
  pahfit_mir/{default,short,long,both}/config.json
  cafe_line/default/...
  s3fit_line/default/...
  gandalf_line/default/...
  galspec_line/default/config.json
  pyqsofitspec_line/default/config.json
  qgfit/default/config.json
  sheap_line/default/config.json
  crossband/default/config.json
  ppxf_host/default/config.json
  manga_dap/default/{config.json,plan.toml,plan_moments.toml,plan_subset.toml,line_database.csv}
  xmm_xspec/default/config.json
  crossmission/default/config.json
  rxte_xspec/{default,mcg6-30-15}/config.json
  cigale_sed/{skirtor2016,fritz2006}/config.json
  agnfitter_sed/default/config.json
```

Legacy optical variants and auto-tuning winners remain under the existing
`configs/<tool>/` directories.
