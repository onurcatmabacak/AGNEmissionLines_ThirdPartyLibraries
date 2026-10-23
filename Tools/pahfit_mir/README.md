# `pahfit_mir` — PAHFIT 2.0 for MIR spectra (Docker)

PAHFIT 2.0 for JWST/MIRI MRS, PAHFIT `s1d`, and Spitzer IRS spectra.

## Run

```bash
bash Pipelines/build_images.sh pahfit_mir
.venv/bin/python pipeline/run_new_tools.py --only VV114_z_0.0200 --tools pahfit_mir --force
.venv/bin/python pipeline/run_new_tools.py --only PDS456_z_0.1840 --tools pahfit_mir --force
```

The direct runner accepts a centralized JSON config:

```bash
bash Pipelines/run_pahfit_mir_docker.sh inputs/PDS456_z_0.1840/raw \
  outputs/PDS456_z_0.1840/pahfit_mir/short 0.184 \
  --config /app/configs/pahfit_mir/short/config.json
```

`--config short` also works (the runner resolves names under
`configs/pahfit_mir/`).  CLI flags override the config, so all flags used by
`pipeline/run_new_tools.py` keep working.  Every run writes the resolved
settings to `<output>/effective_config.json`.

## Outputs

| file | contents |
|------|----------|
| `pahfit_output.ecsv` | fitted PAHFIT feature table (native units) |
| `pahfit_features.csv` | same table as CSV |
| `pahfit_fit.png` / `.pdf` | PAHFIT layout plot |
| `pahfit_summary.json` | fit quality, convergence, config provenance, MC summary |
| `effective_config.json` | full resolved input/preprocess/fit/MC settings |
| `pahfit_lines.csv` | gas lines, PAH features, dust continuum, starlight, attenuation |
| `pahfit_uncertainties.csv` | feature flux + 1-sigma + method (when MC is enabled) |
| `pahfit_uncertainty.png` | relative errors, flux distributions, correlations/trace |
| `pahfit_mc_samples.csv` | per-realization feature fluxes (when MC is enabled) |

`pahfit_lines.csv` always has `flux_observed` (S07-attenuated model) and
`flux_intrinsic` (attenuation removed), plus `quantity` and `unit` per row.
Gas lines and PAH features are integrated intensities in `MJy/sr um`; dust
continuum and starlight rows are flux densities in `MJy/sr` at a reference
rest wavelength (20 um and 5 um, respectively), not integrated fluxes.
`pahfit_uncertainties.csv` uses the observed quantity as `flux`/`err` and
also carries intrinsic columns.

## Statistical uncertainty: what PAHFIT actually does

* PAHFIT classic is a **Levenberg-Marquardt least-squares** fit
  (`scipy.optimize.leastsq` inside astropy).  There is **no MCMC sampler** and
  the original driver had **no bootstrap**.
* PAHFIT constructs `LevMarLSQFitter(calc_uncertainties=True)`, so astropy
  attempts a parameter covariance from the final Jacobian.  In practice
  `fit_info["param_cov"]` is frequently `None`: the fit is rank-deficient
  and/or the number of free parameters is close to the number of spectral
  pixels (PDS 456 short: 58 pixels, 24 free parameters).  The original code
  never read the covariance, and `model.fit_info` is left as `None`.
* The new MC module therefore recomputes the Jacobian itself at the best fit
  and documents the rank, condition number and SVD cutoff.  When that
  covariance is ill-conditioned, `--mc-method auto` uses the full-refit
  bootstrap instead.

### Numerical scale caveat (important for PDS 456 short)

The MIRI `x1d` input is in Jy and the driver converts it to `MJy/sr` with the
nominal 0.04 arcsec^2 aperture.  For PDS 456 short this produces fluxes of
order `3e17 MJy/sr`.  At that scale PAHFIT's Levenberg-Marquardt fit stalls at
the initial guess: the historical `pahfit_output.ecsv` is the guess, with
`rms_rel ~ 0.261` and no parameter movement.  MC runs therefore use an
**internal fit normalization** (divide the spectrum by its median before
fitting, multiply every saved flux/parameter back afterwards).  This is a
numerical device only; output units are unchanged.  With normalization the
PDS 456 short fit converges to `rms_rel ~ 0.009` and `chi2_red ~ 557`, and the
saved ECSV is in the original `MJy/sr` convention.  MC-off runs keep the
historical behaviour exactly (`--no-normalize-fit` is the default when
`--mc-samples 0`).

## Monte Carlo modes

```bash
# fast linearized covariance (100 draws from the parameter covariance)
... --mc-samples 100 --mc-method covariance

# full-refit bootstrap (100 refits; parametric noise or residual resampling)
... --mc-samples 100 --mc-method bootstrap --mc-bootstrap-mode parametric
... --mc-samples 100 --mc-method bootstrap --mc-bootstrap-mode residual

# automatic: covariance when well conditioned, otherwise bootstrap
... --mc-samples 100 --mc-method auto
```

* `covariance`: numerical Jacobian of the model at the best fit,
  `C = (J^T W J)^-1` with `W = 1/sigma^2`, SVD truncation at `--mc-rcond`
  (default `1e-10`), then delta-method errors and correlated draws.  Fast
  (seconds) but only trustworthy when the rank is full and the condition
  number is modest.  Rank-deficient directions are reported and their zero
  errors are marked `covariance_rank_deficient`.
* `bootstrap`: perturb the observed flux by its real errors
  (`parametric`) or resample the fit residuals (`residual`) and refit the
  full PAHFIT model.  Slow (minutes) but does not assume a Gaussian
  posterior.  For each realization a new `Model` is warm-started from the
  best fit.

`--mc-samples 0` (the default) does not fit extra models and preserves the
historical products; it still writes the always-on line table and effective
config.

## Validation and MC results

| source | configuration | fit `rms_rel` | MC method | MC runtime | typical 1-sigma |
|--------|---------------|---------------|-----------|------------|-----------------|
| PDS 456 short | `short`, normalized | 0.0088 | bootstrap, N=100 | 81.6 s | lines `1e-8`–`2e-7` relative; PAH 6.2 `8e-8` |
| PDS 456 short | `short`, normalized | 0.0088 | covariance, N=100 (rank 6/12) | 1.4 s | continuum/PAH `0.2`–`0.8 %`; line errors rank-deficient |
| NGC 4151 | `default` + IRS flags | 0.031 | covariance, N=100 (rank 30/30) | 6.2 s | lines `0.5`–`0.7 %`; PAH 6.2 `17 %` |
| NGC 4151 | `default` + IRS flags | 0.031 | bootstrap, N=100 | 267 s | lines `0.5`–`0.7 %`; PAH 6.2 `20 %` |
| VV114 | `default`, `--s1d` | 0.218 | covariance, N=100 (rank 38/38) | 16.5 s | lines `0.02`–`0.9 %`; PAH `0.01 %` |

For NGC 4151 the covariance and bootstrap agree on the 1:1 line (see
`outputs/pahfit_mc_comparison.png`), which validates the fast mode for a
well-conditioned fit.  For PDS 456 short the covariance is rank-deficient and
only the bootstrap line errors are meaningful.  For all sources the formal
statistical errors are much smaller than the fit residual (`rms_rel` and
`chi2_red` are recorded in `pahfit_summary.json`), so systematics dominate.

Comparison products:

```bash
.venv/bin/python pipeline/compare_pahfit_mc.py
# -> outputs/pahfit_mc_comparison.png, outputs/pahfit_mc_comparison.csv
```

## PDS 456 handling

The short/long MIRI spectra are fitted separately and jointly:

```text
outputs/PDS456_z_0.1840/pahfit_mir/short/
outputs/PDS456_z_0.1840/pahfit_mir/long/
outputs/PDS456_z_0.1840/pahfit_mir/both/
```

`--smooth-um` median-bins the high-resolution MRS data to a PAHFIT-friendly
grid.  Each summary records `rms_rel` and `unstable`.  Long/both use seeded
`Model.from_saved` warm starts; the PDS recipe is encoded in
`inputs/PDS456_z_0.1840/source.json` and in `configs/pahfit_mir/`.

## Remaining limitations

* PAHFIT assumes its standard feature pack; extreme MIRI resolution and
  short/long calibration discontinuities still require careful binning.
* Feature flux errors are statistical only.  The formal errors are far below
  the fit residual for these data; a residual/systematic term is not included
  in the default error budget.
* The `Jy -> MJy/sr` conversion uses the nominal aperture; the absolute
  surface-brightness scale is therefore aperture-dependent.  Relative
  quantities and line ratios are unaffected.
* No simultaneous MIR line + PAH + AGN torus model.
