# `pahfit_mir` - PAHFIT 2.0 for MIR spectra (Docker)

PAHFIT 2.0 for JWST/MIRI MRS, PAHFIT `s1d`, and Spitzer IRS spectra.  The
driver performs a Levenberg-Marquardt least-squares fit, writes the standard
PAHFIT products, and adds a homogeneous line/PAH/continuum table, optional
covariance or full-refit bootstrap uncertainties, coverage diagnostics and
explicit quality flags.

## Quick run

```bash
bash Pipelines/build_images.sh pahfit_mir

# direct runner (config name resolves under configs/pahfit_mir/)
bash Pipelines/run_pahfit_mir_docker.sh inputs/NGC4151_z_0.0033/raw \
  outputs/pahfit_mir/NGC4151_z_0.0033 0.003319 \
  --config /app/configs/pahfit_mir/ngc4151/config.json \
  --mc-samples 200 --mc-method auto

# full production matrix (PDS short/long/both, VV114, NGC 4151, NGC 253)
bash Pipelines/run_pahfit_production.sh

# normal pipeline entry point
.venv/bin/python pipeline/run_new_tools.py --only VV114_z_0.0200 \
  --tools pahfit_mir --force
```

`Pipelines/run_pahfit_mc.sh` is retained as a backward-compatible wrapper
around the production script.  CLI flags override config values, and every run
writes the resolved settings to `<output>/effective_config.json`.

## Production matrix

The numbers below are from the committed production outputs.  `rms_rel` is
`RMS(data-model)/median(|data|)` on the fitted pixels; `chi2_red` uses the
formal uncertainties and `dof = n_data - n_free_all` (bound parameters are
counted).  Runtimes are wall-clock inside the container on the shared host and
are therefore indicative only.

| source | config | data / coverage | fit pixels | `rms_rel` | `chi2_red` (dof) | quality | MC | MC runtime |
|--------|--------|-----------------|------------|-----------|------------------|---------|----|------------|
| PDS 456 short | `short` | MIRI short `x1d`, 6.55-11.69 um; 2.37 um DQ gap | 58 | 0.0088 | 754.2 (34) | systematics-limited | bootstrap 100, rank 6/12 fallback | 128 s |
| PDS 456 long | `long` | MIRI long `x1d`, 15.43-27.98 um; 6.42 um gap | 125 | 0.0174 | 117.6 (104) | systematics-limited | bootstrap 100, rank 12/18 fallback | 273 s |
| PDS 456 both | `both` | short+long, 6.58-27.96 um; three gaps (2.37, 3.75, 6.45 um) | 94 | 0.0377 | 1164.4 (50) | systematics-limited | bootstrap 100, rank 12/24 fallback | 629 s |
| VV114 | `vv114` | all 12 MIRI `s1d` channels, 5.00-28.00 um, native sampling | 8727 (12 clipped) | 0.195 | 18422 (8679) | systematics-limited | covariance 200, rank 38/38; bootstrap 200 validation | 56 s / 879 s |
| NGC 4151 | `ngc4151` | full Spitzer IRS SL/LL, 5.26-37.86 um, 0.1 um bins | 254 | 0.0311 | 338.8 (201) | systematics-limited | covariance 200, rank 30/30; bootstrap 200 | 28 s / 845 s |
| NGC 253 | `ngc253` | Spitzer IRS 5.26-20.59 um; 1.36+1.52 um DQ gaps; 35.8-37.9 um tail excluded | 126 | 0.250 | 6110 (80) | systematics-limited, **flagged** | bootstrap 100, rank 28/30 fallback | 522 s |
| NGC 253 full tail | `full_tail` control | same table, 5.22-37.86 um including the 13-row tail | 139 | 0.715 | 7820 (86) | **unstable / flagged** | none | - |
| NGC 253 full tail, legacy | `full_tail_legacy` control | no normalization, one pass; reproduces the historical failure | 139 | 11.53 | 1.42e6 (86) | **unstable / flagged** | none | - |

The VV114 bootstrap validation is a 200-realization cross-check of the
production covariance run, not the production result.  All 200 refits
converged, but **all 48 features are frozen** at the best-fit minimum: the
model/data mismatch dominates the formal noise, so the bootstrap samples do
not move the parameters.  The full-rank covariance (rank 38/38, condition
`9.0e4`) is therefore the only usable VV114 uncertainty estimate, and it is
statistical only.  This is exactly the frozen-feature case the audit is
designed to expose.

Notes on the table:

* PDS 456 short/long/both have formal `chi2_red >> 1` because the MIRI fluxes
  have S/N of hundreds and PAHFIT's fixed instrument line profiles do not
  reproduce every high-resolution line core.  The short fit is numerically
  stable (`ierr=1`), not a failed fit.  Its bootstrap freezes 23/24 features
  at the best-fit minimum; the covariance probe is rank 6/12.  Therefore the
  formal line errors are not reliable.  Continuum/PAH rows receive the
  covariance delta error as a labeled fallback; H2/ionic lines remain
  `bootstrap_frozen_unconstrained`.
* PDS 456 both has 25 line/PAH features whose observed wavelengths fall in
  the three gaps; they are marked `coverage_gap` and are not usable.  In
  particular PAH 11.3a (observed 13.3 um) sits in the 11.67-15.42 um gap and
  its fitted flux is unconstrained.
* PDS 456 long and both fall back to bootstrap (rank 12/18 and 12/24
  respectively).  Both were rerun with `mc.maxiter=2000`; before that change
  only 42/100 both realizations converged.  With 2000, 100/100 converge, but
  11 (long) and 31 (both) features are frozen at the best-fit minimum.
* VV114 is a full 12-channel run.  Its `rms_rel=0.195` is dominated by the
  short-wavelength 5-8 um continuum: PAHFIT classic has 300 K and 35-200 K
  dust components and 5000 K starlight, but no 500-1000 K hot-dust component,
  so the 5-8 um rise is fitted mostly by PAH features.  The robust clip
  removes 12 unflagged cosmic-ray/hot-pixel outliers; it does not hide the
  global model mismatch.  `chi2_red` is formally enormous because the MIRI
  errors are very small.
* NGC 4151 is a good morphological fit (`rms_rel=0.031`) but is still
  systematics-limited: the IRS errors are ~0.2%, the residual is ~3%, and
  PAHFIT classic has no AGN torus or broad-line component.  23/53 parameters
  sit on physical bounds.  The 200-realization bootstrap agrees with the
  covariance for the detected lines/PAHs, but 21 mostly undetected features
  are frozen and remain flagged.
* NGC 253 is intentionally retained as the starburst stress test.  The
  unflagged 35.8-37.9 um edge island has 13 rows with ~300 Jy while the
  20 um continuum is ~40 Jy, and there is no unflagged coverage between 20.6
  and 35.8 um.  Fitting it drags the whole SED.  The normalized `full_tail` control gives
  `rms_rel=0.715`, `chi2_red=7820`, `ierr=5`; the historical
  `full_tail_legacy` control (no normalization, one pass) reproduces
  `rms_rel=11.53`.  Excluding that island (`max_wave=30`) reduces `rms_rel`
  to 0.250, but the 14.8-17.9 um DQ gaps and the starburst SED still leave
  `chi2_red=6110`; it is **not** called stable.

## What the audit fixed

1. **Jy/MJy unit factor.**  The old code converted `Jy` to `MJy/sr` with
   `flux * 1e6 / omega`, i.e. it used `1 Jy = 1e6 MJy`.  The correct factor is
   `1 Jy = 1e-6 MJy`.  The old absolute fluxes were therefore `1e12` too
   large (PDS 456 short `fit_flux_scale` was `3.4e17`; it is now `3.4e5`).
   The fit shape and relative line ratios were unaffected, but the physical
   scale, ECSV fluxes and the claimed "normalization stall at 3e17" were
   wrong.
2. **MIRI `s1d` units.**  `read_s1d` now reads `TUNIT2`/`BUNIT`.  The official
   VV114 example is `MJy` (flux density), not `MJy/sr`; it is divided by the
   requested aperture (9 arcsec^2 for `vv114`).  Files that really are
   `MJy/sr` are left alone.
3. **Line/PAH flux convention.**  `pahfit_lines.csv` reports the integrated
   PAHFIT's integrated line power (the frequency integral), in MJy/sr THz,
   evaluated on
   the same profile grid as the peak and EW.  PAHFIT's internal `power`
   parameter in the ECSV is a different quantity (integral over frequency);
   it is deliberately **not** copied into the line table.  The audit verified
   this convention against the component peak times width and corrected the
   peak-flux columns to include attenuation and the `1/(1+z)` dimming.
4. **Reference wavelengths.**  Dust-continuum and starlight rows now carry
   `reference_wavelength_um`; rows whose reference is outside the fitted
   range are marked `extrapolated=true`.  The uncertainty table uses the same
   reference as the line table (the old code used 5.245 um for the record and
   5.535 um for the uncertainty).
5. **Covariance fallback.**  `--mc-method auto` now requires a **full-rank**
   covariance.  The old 80%-rank rule accepted a rank-28/30 covariance for
   NGC 253.  Auto therefore falls back to bootstrap for all rank-deficient
   cases and records the covariance probe (rank, condition, `n_data`).
6. **Bootstrap fit status.**  Each realization now checks `ierr` and computes
   its chi-square in the rest frame.  Non-converged refits are counted in
   `n_failed`/`n_not_converged` instead of silently being called `ok`.
7. **Frozen bootstrap detection.**  If a feature's bootstrap samples have
   relative scatter `<1e-6` (or fewer than half the samples are distinct), the
   realization is not constraining that feature.  The row is marked
   `bootstrap_frozen_unconstrained` (or
   `bootstrap_frozen_covariance_fallback` when a finite delta-method error
   exists) and `reliable=false`.  This prevents fake S/N of `1e8` for
   undetected lines.
8. **Coverage and data quality.**  Every run now records `input_stats`
   (rows, good rows, DQ-flagged rows, input unit, conversion factor) and
   `coverage.gaps` with start/end/width.  PDS short/long/both and NGC 253 are
   no longer reported as gap-free.  Any line/PAH feature whose observed
   wavelength falls inside a gap wider than 0.5 um is marked
   `status=coverage_gap`, its S/N and formal errors are suppressed, and the
   feature names are listed in `features_in_coverage_gaps`.  This catches
   unconstrained fits such as PDS both PAH 11.3a (observed 13.3 um, inside the
   11.67-15.42 um gap).
9. **Quality reporting.**  `fit_quality`, `quality_flags`, `flagged`,
   `fit_converged`, `at_bound_fraction` and `n_clipped` are always written.
   The old `unstable` flag only looked at `rms_rel > 0.5`; it missed
   `chi2_red=304-754` and `chi2_red=6110`.
10. **ECSV metadata.**  PAHFIT 2.0 writes instrument and redshift into swapped
    metadata slots inside `Model.fit()`.  The driver now writes authoritative
    `instrument` and `redshift` metadata before saving the ECSV.
11. **IRS args.**  `pipeline/run_new_tools.py` used to replace, not append,
    `pahfit_args` for Spitzer IRS inputs; source-level `--max-wave` overrides
    were silently dropped.  It now appends them.
12. **Robust clipping.**  `--clip-nmad` adds an iterative relative-residual
    clip for unflagged cosmic rays (used for VV114 only).  It is relative,
    not formal-sigma, so a globally mismatched model is not deleted.

## Outputs

| file | contents |
|------|----------|
| `pahfit_output.ecsv` | fitted PAHFIT feature table (native units) |
| `pahfit_features.csv` | same table as CSV |
| `pahfit_fit.png` / `.pdf` | PAHFIT layout plot |
| `pahfit_summary.json` | fit quality, coverage, convergence, MC diagnostics, flags |
| `effective_config.json` | full resolved input/preprocess/fit/MC settings |
| `pahfit_lines.csv` | gas lines, PAH features, dust continuum, starlight, attenuation |
| `pahfit_uncertainties.csv` | feature flux, 1-sigma, method, reliability, status |
| `pahfit_uncertainty.png` | relative errors, distributions, correlations/trace |
| `pahfit_mc_samples.csv` | per-realization feature fluxes |

`pahfit_lines.csv` always has `flux_observed` (S07-attenuated) and
`flux_intrinsic` (attenuation removed), `quantity`, `unit`, `status`,
`at_bound`, `extrapolated`, `reference_wavelength_um`, and `snr`.
Gas lines and PAH features are integrated line powers in `MJy/sr THz`; dust
continuum and starlight are flux densities in `MJy/sr` at a reference rest
wavelength (20 um and 5 um or the red edge, respectively), not integrated
fluxes.  `flux_observed` for continuum/starlight includes the `1/(1+z)`
dimming; `flux_intrinsic` is rest-frame.

`pahfit_uncertainties.csv` uses the observed quantity as `flux`/`err`,
carries `err_delta`, `err_low`, `err_high`, `flux_intrinsic`,
`err_intrinsic`, `reliable` and `status`.  `err_delta` is the linearized
covariance probe error when available; it is not a replacement for a reliable
bootstrap error.

## Monte Carlo methods

```bash
# fast linearized covariance (fast; only trustworthy at full rank)
... --mc-samples 200 --mc-method covariance

# full-refit bootstrap (parametric noise or residual resampling)
... --mc-samples 200 --mc-method bootstrap --mc-bootstrap-mode parametric
... --mc-samples 200 --mc-method bootstrap --mc-bootstrap-mode residual

# automatic: full-rank covariance, otherwise bootstrap
... --mc-samples 200 --mc-method auto
```

* `covariance`: numerical Jacobian of the model at the best fit,
  `C = (J^T W J)^-1`, `W = 1/sigma^2`, SVD truncation at `--mc-rcond`
  (default `1e-10`), delta-method errors and correlated draws.  Fast but only
  trustworthy at full rank and modest condition number.
* `bootstrap`: perturb the observed flux by its real errors (`parametric`) or
  resample fit residuals (`residual`) and refit the full PAHFIT model for each
  realization.  Slow, but does not assume a Gaussian posterior.  Each
  realization starts from the best fit.  Frozen features are detected and
  marked as described above.

PAHFIT classic is a Levenberg-Marquardt least-squares fit, not an MCMC
sampler.  PAHFIT requests an astropy covariance matrix
(`LevMarLSQFitter(calc_uncertainties=True)`), but `param_cov` is `None` for
these data; the driver reconstructs the Jacobian itself.

## Quality flags

`fit_quality` is one of `good`, `systematics_limited`, `unstable`, `failed`.
`quality_flags` may contain:

* `formal_chi2_mismatch` (`chi2_red > 10`)
* `many_parameters_at_bound` (more than half of all free parameters)
* `coverage_gap` (a gap wider than 0.5 um)
* `features_in_coverage_gaps` (line/PAH wavelengths inside such a gap)
* `covariance_rank_deficient`
* `bootstrap_frozen_features`
* `mc_fit_failures`
* `outliers_clipped`
* `fit_not_converged`
* `few_degrees_of_freedom`
* `mc_unavailable`

All four science objects have `systematics_limited` fits.  NGC 253 is the only
one that remains explicitly **flagged** for a data/model failure after the
tail cut.  VV114 is flagged for its unresolved 5-8 um hot-dust mismatch even
though its 200-realization covariance is full rank.

## Reproduce

```bash
bash Pipelines/run_pahfit_production.sh
```

This writes the production directories and, for the validation runs,
`VV114_z_0.0200/pahfit_mir/bootstrap_200` and
`NGC4151_z_0.0033/pahfit_mir/bootstrap_200`.  The NGC 253 failure control is
`NGC253_z_0.0008/pahfit_mir/full_tail`.

## Remaining limitations

* PAHFIT's classic feature pack has no 500-1000 K hot-dust continuum.  This is
  the dominant VV114 short-wavelength mismatch and cannot be fixed by binning.
* No simultaneous MIR line + PAH + AGN torus or broad-line model.  NGC 4151
  and the PDS 456 formal chi-square therefore remain far above unity even
  when the morphology looks good.
* Formal MIRI/IRS errors are much smaller than the model systematics.  The
  production errors are statistical only; use `rms_rel`, `chi2_red` and
  `quality_flags` when quoting systematics.
* The absolute surface-brightness scale depends on the chosen aperture.  Line
  ratios and relative quantities are unaffected; the aperture and conversion
  factor are recorded per input file.
* MIRI MRS DQ gaps are real.  They are reported, not interpolated or hidden.
