# `pahfit_mir` configuration

Each variant is a single JSON file:

```text
configs/pahfit_mir/<variant>/config.json
```

`Tools/pahfit_mir/run_pahfit.py` accepts `--config <file-or-name>`. A bare
name is resolved under this directory, so `--config short` is equivalent to
`--config /app/configs/pahfit_mir/short/config.json` inside the Docker image.
Every run writes the resolved settings to `<output>/effective_config.json` and
records the config path in `pahfit_summary.json`.

## Production variants

| variant | object | input | segment | bin | range | aperture | fit | MC |
|---------|--------|-------|---------|-----|-------|----------|-----|----|
| `short` | PDS 456 | MIRI `x1d` short | short | 0.05 um | 5-38 um | 0.04 arcsec^2 | 2 passes, maxiter 5000, normalized | 100 auto |
| `long` | PDS 456 | MIRI `x1d` long | long | 0.05 um | 5-28 um | 0.04 arcsec^2 | 2 passes, maxiter 5000, normalized, seed warm start | 100 auto |
| `both` | PDS 456 | MIRI `x1d` short+long | both | 0.10 um | 5-28 um | 0.04 arcsec^2 | 3 passes, maxiter 5000, normalized, short warm start | 100 auto |
| `vv114` | VV114 | 12 MIRI `s1d` channels | both | native | 5-28 um | 9 arcsec^2 | 2 passes + 2 robust clips, normalized | 200 auto |
| `ngc4151` | NGC 4151 | Spitzer IRS `.tbl` | both | 0.10 um | 5-38 um | 1 arcsec^2 common | 2 passes, maxiter 2000, normalized | 200 auto |
| `ngc253` | NGC 253 | Spitzer IRS `.tbl` | both | 0.10 um | 5-30 um | 1 arcsec^2 common | 3 passes, maxiter 5000, normalized | 100 auto |
| `default` | generic | from CLI | both | none | 5-38 um | 0.04 arcsec^2 | 1 pass, no normalization, no clipping | off |

`ngc253` deliberately excludes the 35.8-37.9 um unflagged edge island. The
full-tail failure control is produced by
`outputs/pahfit_mir/NGC253_z_0.0008/full_tail/` and is not a production
variant. `default` preserves the historical MC-off path.

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
    "aperture_arcsec2": 0.04,
    "tbl_aperture_arcsec2": 1.0
  },
  "fit": {
    "maxiter": 5000,
    "passes": 2,
    "no_guess": false,
    "init_from": null,
    "normalize": true,
    "clip_nmad": 0.0,
    "clip_iterations": 1
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

Command-line flags always override config values. Existing flags used by
`pipeline/run_new_tools.py` (`--segment`, `--smooth-um`, `--max-wave`,
`--instrument`, `--init-from`, `--tbl`, `--s1d`) keep working unchanged.
`pipeline/run_new_tools.py` resolves `source.json["pahfit_config"]` when no
variant list is present, and appends (rather than drops) `pahfit_args` for
Spitzer IRS inputs.

## Units and apertures

* MIRI `x1d` `FLUX`/`FLUX_ERROR` are in Jy. They are converted to MJy/sr with
  `1 Jy = 1e-6 MJy` divided by the requested aperture solid angle. The old
  driver used `1 Jy = 1e6 MJy`, a factor `1e12` error; the fix is why
  `fit_flux_scale` is now of order `1e5` rather than `1e17` for PDS 456.
* MIRI `s1d` files carry `TUNIT2`. The official VV114 example is `MJy` (flux
  density), not `MJy/sr`; it is divided by `aperture_arcsec2` (9 arcsec^2 in
  `vv114`, matching PAHFIT's packaged-spectrum convention). Files that really
  are `MJy/sr` are left unchanged.
* Spitzer IRS `.tbl` fluxes are point-source calibrated Jy. A single common
  aperture (`tbl_aperture_arcsec2`, default 1 arcsec^2) is used so the SL/LL
  orders remain on one SED; using per-slit areas inserts a factor 8.6 step.
* Every output is in MJy/sr (flux densities) or MJy/sr um (integrated line/PAH
  intensities). The input unit and conversion factor are recorded per file in
  `effective_config.json`.

## Monte Carlo

Monte Carlo is opt-in so normal pipeline runs keep their historical cost:

```bash
... run_pahfit.py ... --mc-samples 200 --mc-method auto
... run_pahfit.py ... --mc-samples 200 --mc-method covariance
... run_pahfit.py ... --mc-samples 200 --mc-method bootstrap \
    --mc-bootstrap-mode parametric --mc-maxiter 2000
```

`--mc-method auto` now requires a **full-rank** covariance (`rank == n_free`)
with condition number below `1e6`. Otherwise it falls back to the full-refit
bootstrap and keeps the covariance rank/condition as a probe. Explicit
`covariance` mode still writes the delta-method errors, but marks every
affected row `reliable=false` and `status=covariance_rank_deficient`.

`--mc-samples 0` (the default) writes only the historical products plus
`pahfit_lines.csv`, `effective_config.json`, coverage/gap diagnostics and
quality flags; it does not fit extra models.

`fit.normalize` is normally `true` for production and `null` for the generic
MC-off default. The runner normalizes the input by its median before fitting
because PAHFIT's Levenberg-Marquardt fit is sensitive to the native intensity
scale. Saved fluxes are multiplied back to the native unit and `fit_flux_scale`
is recorded.

## Robust clipping

`fit.clip_nmad` enables a robust relative-residual clip after the initial fit.
It is used for VV114 (`6.0`, two iterations) to remove unflagged cosmic rays /
hot pixels in the `s1d` tables. It is deliberately a **relative** MAD clip, not
a formal sigma clip: VV114 residuals are `chi2_red >> 1`, so a sigma clip would
delete most of the spectrum. The clip is iterated, refit, and recorded as
`n_clipped`, `clip_refits` and the `outliers_clipped` quality flag. It is off
for the PDS, NGC 4151 and NGC 253 production fits.

## Outputs and status

| file | contents |
|------|----------|
| `pahfit_output.ecsv` | fitted PAHFIT feature table (native units) |
| `pahfit_features.csv` | same table as CSV |
| `pahfit_fit.png` / `.pdf` | PAHFIT layout plot |
| `pahfit_lines.csv` | gas lines, PAH features, dust/stellar continuum, attenuation |
| `pahfit_uncertainties.csv` | feature flux, error, method, reliability, status |
| `pahfit_uncertainty.png` | errors, distributions, correlations/trace |
| `pahfit_mc_samples.csv` | per-realization observed feature fluxes |
| `pahfit_summary.json` | fit quality, coverage, MC diagnostics, quality flags |
| `effective_config.json` | fully resolved input/preprocess/fit/MC settings |

Quality is reported as `fit_quality` in
`good | systematics_limited | unstable | failed`, with a machine-readable
`quality_flags` list (`formal_chi2_mismatch`, `many_parameters_at_bound`,
`coverage_gap`, `features_in_coverage_gaps`, `covariance_rank_deficient`,
`bootstrap_frozen_features`,
`mc_fit_failures`, `outliers_clipped`, `fit_not_converged`, ...). The legacy
`unstable` boolean is still written; `flagged` is true whenever any quality
flag is present.
