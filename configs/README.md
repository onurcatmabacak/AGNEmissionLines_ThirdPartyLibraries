# Tool configurations

Central, reviewable configuration for every production tool.  Each tool has a
`configs/<tool>/<variant>/` directory.  New line-fit tools (`cafe_line`,
`s3fit_line`, `gandalf_line`) consume these files directly through `--config`;
older tools use the same values as their documented defaults and their code
contains the executable implementation.

## SED vs spectrum decomposition

The two families are deliberately separate:

| family | tools | output |
|---|---|---|
| Broad-band SED / torus | `cigale_sed`, `agnfitter_sed` | stellar mass, AGN fraction, torus luminosity, model-family spread |
| Spectral line fitting | `pyqsofit_uv`, `ir_linefit`, `nir_linefit`, `fir_linefit`, `pahfit_mir`, `cafe_line`, `s3fit_line`, `gandalf_line`, `crossband` | line flux, FWHM, velocity, equivalent width, ratios |
| Host/continuum decomposition | `ppxf_host` | stellar velocity dispersion, host fraction |

CIGALE/AGNfitter must **not** be described as emission-line fitters; they fit
the broad-band SED with templates.

## Uncertainty / sampling modes

| tool | statistical method |
|---|---|
| `pyqsofit_uv` | covariance; optional MC resampling and `emcee` MCMC (`PYQSOFIT_MC`, `PYQSOFIT_MCMC`) |
| `agnfitter_sed` | `ultranest` nested sampling (Bayesian posterior) |
| `cigale_sed` | `pdf_analysis` Bayesian likelihood/posterior; not MCMC |
| `pahfit_mir` | least-squares; MC uncertainty/refit option |
| `cafe_line` | LMFIT covariance + post-fit multivariate-normal MC |
| `s3fit_line` | least-squares + mock-spectrum Monte Carlo (`num_mocks`) |
| `gandalf_line` | native MPFIT covariance/`FOR_ERRORS`; fallback bootstrap if GDL unavailable |
| `ir_linefit`/`nir_linefit`/`fir_linefit` | covariance from `least_squares`/`curve_fit` |
| `ppxf_host` | pPXF formal errors |
| `crossband` | analytic ratio error propagation |

## Layout

```
configs/
  pyqsofit/uv/main.py              # executable
  pyqsofit/uv/config.json          # effective settings snapshot
  badass/{best,nbasin20}/main.py
  ...
  ir_linefit/default/config.json
  nir_linefit/{default,psf}/config.json
  fir_linefit/default/config.json
  pahfit_mir/{default,short,long,both}/config.json
  cafe_line/default/...
  s3fit_line/default/...
  gandalf_line/default/...
  crossband/default/config.json
  ppxf_host/default/config.json
  cigale_sed/{skirtor2016,fritz2006}/config.json
  agnfitter_sed/default/config.json
```

Legacy optical variants and auto-tuning winners remain under the existing
`configs/<tool>/` directories.
