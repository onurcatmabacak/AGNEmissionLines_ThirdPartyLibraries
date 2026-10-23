# `pahfit_mir` configuration

Each variant is a single JSON file:

```text
configs/pahfit_mir/<variant>/config.json
```

`Tools/pahfit_mir/run_pahfit.py` accepts `--config <file-or-name>`.  A bare
name is resolved under this directory, so `--config short` is equivalent to
`--config /app/configs/pahfit_mir/short/config.json` inside the Docker image.
Every run writes the resolved settings to `<output>/effective_config.json` and
records the config path in `pahfit_summary.json`.

## Variants

| variant | use | instrument | segment | smoothing | max wave | warm start |
|---------|-----|------------|---------|-----------|----------|------------|
| `default` | generic baseline | from CLI/input | `both` | none | 38 um | none |
| `short` | PDS 456 MIRI short | MIRI MRS ch1-ch4 | `short` | 0.05 um | 38 um | none |
| `long` | PDS 456 MIRI long | MIRI MRS ch1-ch4 | `long` | 0.05 um | 28 um | `<output>/seed/pahfit_output.ecsv` |
| `both` | PDS 456 short+long | MIRI MRS ch1-ch4 | `both` | 0.10 um | 28 um | `<output>/seed/pahfit_output.ecsv` (seeded from `short`) |

The PDS 456 pipeline recipe (which seed is created, and from which variant it
is copied) remains in `inputs/PDS456_z_0.1840/source.json`.  The `long` and
`both` configs only supply defaults; `pipeline/run_new_tools.py` still passes
the explicit `--init-from /app/output/seed/pahfit_output.ecsv` flag.

## Schema

```json
{
  "schema_version": 1,
  "name": "short",
  "input": {
    "instrument": ["jwst.miri.mrs.ch1.A", "..."],
    "segment": "short",
    "s1d": false,
    "tbl": false,
    "smooth_um": 0.05,
    "min_wave": 5.0,
    "max_wave": 38.0,
    "aperture_arcsec2": 0.04
  },
  "fit": {
    "maxiter": 1000,
    "passes": 1,
    "no_guess": false,
    "init_from": null,
    "normalize": null
  },
  "monte_carlo": {
    "enabled": false,
    "samples": 100,
    "method": "auto",
    "seed": 12346,
    "rcond": 1e-10,
    "maxiter": 500,
    "bootstrap_mode": "parametric",
    "scale": "none",
    "save_samples": true
  }
}
```

Command-line flags always override config values.  Existing flags used by
`pipeline/run_new_tools.py` (`--segment`, `--smooth-um`, `--max-wave`,
`--instrument`, `--init-from`, `--tbl`, `--s1d`) keep working unchanged.

## Monte Carlo

Monte Carlo is **opt-in** so normal pipeline runs keep their historical cost:

```bash
# 100 realizations, automatic mode (covariance when usable, otherwise bootstrap)
... run_pahfit.py ... --mc-samples 100

# force the fast linearized covariance mode
... run_pahfit.py ... --mc-samples 100 --mc-method covariance

# full refit bootstrap
... run_pahfit.py ... --mc-samples 100 --mc-method bootstrap \
    --mc-bootstrap-mode parametric --mc-maxiter 500
```

`--mc-samples 0` (the default) writes only the historical products plus the
new `pahfit_lines.csv` and `effective_config.json`; it does not fit extra
models.

`fit.normalize` is normally `null`: the runner normalizes the input by its
median only when MC is enabled (`--mc-samples > 0`), because PAHFIT's
Levenberg-Marquardt fit can stall at the native scale of the MIRI/IRS
`MJy/sr` conversion.  Saved fluxes are always multiplied back to the native
unit, and `fit_flux_scale` is recorded in `pahfit_summary.json` and
`effective_config.json`.  Pass `--no-normalize-fit` to disable it explicitly
or set `"normalize": false`.

MC runs also write:

| file | contents |
|------|----------|
| `pahfit_uncertainties.csv` | feature, quantity, unit, flux, 1-sigma, method, n_samples, status |
| `pahfit_uncertainty.png` | relative errors, distributions, correlations (covariance) or trace (bootstrap) |
| `pahfit_mc_samples.csv` | per-realization observed feature fluxes |
| `effective_config.json` | resolved config incl. `fit.normalize` and `fit.flux_scale` |

The config `monte_carlo.samples` value is used by `--mc` when no explicit
`--mc-samples` is given.  `monte_carlo.enabled` defaults to `false`; set it to
`true` only for a variant that should always run MC.

## Monte Carlo methods

* **covariance** (fast): numerical Jacobian of the PAHFIT model at the best
  fit, `C = (J^T W J)^-1` with `W = 1/sigma^2`, SVD truncation at
  `monte_carlo.rcond`, then either delta-method errors or draws from `C`.
  This is a *linearized* estimate, not MCMC.  The summary records the rank,
  condition number, and whether the covariance is rank-deficient.
* **bootstrap** (slow): perturb the observed flux by its real errors
  (`parametric`), or resample the fit residuals (`residual`), and refit the
  full PAHFIT model for every realization.  This measures refit scatter and
  does not assume a Gaussian posterior.

PAHFIT classic itself is a Levenberg-Marquardt least-squares fit.  It is not
an MCMC sampler.  PAHFIT requests an astropy covariance matrix
(`LevMarLSQFitter(calc_uncertainties=True)`), but that matrix is often
unavailable for these data because the number of free parameters is close to
or larger than the number of spectral pixels.  The covariance mode above
therefore recomputes the Jacobian and documents its rank and conditioning.
