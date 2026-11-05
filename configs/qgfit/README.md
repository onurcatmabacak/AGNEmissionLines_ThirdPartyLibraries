# QGfit configurations

The adapter (`Tools/qgfit/run_qgfit.py`) is configured with a small JSON file.
Three configurations are kept in this directory:

| directory | purpose | continuum MCMC | line errors |
|---|---|---|---|
| `default/` | fast demonstration / smoke test | 40 walkers x 100 steps (burn 20) | least-squares covariance |
| `production/` | production science run | 100 walkers x 1000 steps (burn 200) | least-squares covariance (line MCMC tested, unstable) |
| `production_wing/` | [O III] wing diagnostic | LSQ continuum reused | least-squares covariance |

`production_wing/` ships a modified line template (`lines_oiii_wing.csv`).
It is not the native QGfit model; it exists to quantify how much of the
H-beta/[O III] 5007 ratio is set by the line-component definition.

## Production recipe

```bash
# Build the image once (the adapter and vendored QGfit are copied into it).
bash pipeline/runners/build_images.sh qgfit

# Full-capability production run.
bash pipeline/runners/run_qgfit_docker.sh \
  inputs/04592649654_z_0.5874 \
  outputs/qgfit/04592649654_z_0.5874 \
  --config configs/qgfit/production \
  --z 0.58741307

# Expanded-template [O III] wing diagnostic (same continuum, line MCMC on).
bash pipeline/runners/run_qgfit_docker.sh \
  inputs/04592649654_z_0.5874 \
  outputs/qgfit/04592649654_z_0.5874/expanded_template \
  --config configs/qgfit/production_wing \
  --z 0.58741307
```

The pipeline auto-detects `pyqsofit_uv/`, `gandalf_line/`, `s3fit_line/`,
`galspec_line/` and `pyqsofitspec_line/` next to the output directory and
mounts them as read-only references.  Use `--reference DIR` to point at a
different parent directory.

## What the production configuration enables

* `conti_pl`: broken power-law AGN continuum.
* `conti_fe_uv`, `conti_fe_op`: QGfit's bundled UV and optical Fe II templates,
  with free normalisation, FWHM and shift.
* `conti_host`: BC03 young+old host SED, enabled because z=0.587 < `host_zcut`.
* `conti_balmer: false`: QGfit's default; the Balmer continuum is not needed for
  this fit and is degenerate with the Fe II optical template.
* `line_fit: true` and QGfit's native `lines.csv` (or the expanded template in
  `production_wing/`).  All complexes with rest-frame coverage are fitted:
  H-beta/[O III], H-gamma/[O III] 4363, H-delta, H-epsilon/He I/[Ne III],
  He I 5877, [O I] 6300/6365, [N I] 5200, [O II] 3727/[Fe VII], Mg II,
  C III]/Al III, C IV/He II/O III], and Ly-alpha/N V.  H-alpha/[N II]/[S II]
  are outside the SDSS coverage at z=0.587 (rest frame ends at 6510 A).
* `mask_lowSN: false`: the adapter has already removed `IVAR<=0`, non-finite
  and non-zero `AND_MASK` pixels.  QGfit's extra `flux > -1 sigma` clip is not
  appropriate for this spectrum (it removes the H-beta/[O III] region).
* `check_kmpfit: true`, `conti_redchi_limit: 1.5`: QGfit attempts its KMPFIT
  fallback when the least-squares continuum chi2_nu exceeds 1.5 and keeps the
  better solution.  The chosen method is recorded in `run.json`.

## MCMC settings and convergence

### Continuum

`production/config.json` uses 100 walkers x 1000 steps with burn 200.  QGfit
initialises emcee walkers in a 1e-4 relative ball around the least-squares
solution; that ball is far too small for 16 correlated continuum parameters and
a 100-step chain produces errors 10-30 times smaller than the LSQ covariance.
The adapter can optionally draw walkers from the LSQ covariance
(`mcmc_init_scale`, `mcmc_use_correlations`), but tests on this object showed
that covariance-based starts put walkers in invalid host/Fe II corners
(`redchi_mcmc` ~1e9-1e10).  The production setting is therefore
`mcmc_init_scale=0` (lmfit's small ball, seed 42) with a 1000-step chain that
has time to expand.  The likelihood is unchanged.

`run.json` records:

* `continuum.mcmc.acceptance_fraction_mean` and `_min`;
* `continuum.mcmc.tau_max` and `n_tau` (integrated autocorrelation time from
  `emcee.autocorr.integrated_time`);
* `continuum.mcmc.width_ratio_median`: the median ratio of the emcee marginal
  width to `stderr_lsq/sqrt(redchi_nu)`, computed only for well-constrained,
  non-bound parameters;
* `continuum.mcmc.converged`: true only when `N_tau >= 50`, the acceptance is
  in 0.05-0.70, and the width ratio is 0.5-2.0.

The corner plot title and `qgfit_uncertainty.png/pdf` carry the same verdict.
`qgfit_mcmc_summary.csv` has per-parameter quantiles, autocorrelation times,
LSQ widths and the width ratio.

Measured on the 04592649654 production run: 100 x 1000 (burn 200), acceptance
0.297, `tau_max`=99.5 steps, `N_tau`=8.0, median width ratio 1.41 (pass),
`redchi_mcmc`=16.21 versus LSQ 16.81.  The chain is width-converged but not
50-tau converged; 50 tau would need ~4977 steps (~2.8 h at ~2 s/step).  The
production runtime was 2334.5 s (38.9 min), of which 2014.0 s was the
continuum MCMC.  `run.json` records `width_converged: true`,
`tau_converged: false`, `converged: false` and the step count needed for
50 tau.

### Lines

`production/config.json` sets `line_mcmc: false`.  A 50 walkers x 300 steps
pilot was run first: the per-complex integrated autocorrelation times were
20-42 steps, so the 220 post-burn samples gave `N_tau` ~5-11, and the chain
produced `redchi_mcmc` ~6e10 against an LSQ `redchi` of 11.5.  That is not a
usable posterior, so the production run keeps the least-squares covariance
errors and labels every line `qgfit_leastsq`.  The `qgfit_line_mcmc_summary.csv`
written by the production run records the disabled status for every complex.

If you enable `line_mcmc`, QGfit runs one independent chain per complex and only
for complexes in which more than one line norm varies.  The adapter accepts a
chain only when every chain that ran has `N_tau >= 20`, acceptance 0.02-0.80, a
dominant-norm width within 0.3-3.0 of `stderr_lsq/sqrt(redchi)`, and a sane
`redchi_mcmc`.  Otherwise it keeps the LSQ errors, labels them `qgfit_leastsq`,
and records the reason; the run is never described as an MCMC line fit in that
case.  Line MCMC does not propagate continuum uncertainty.

### Why not longer?

The production chain length is a compromise between convergence and runtime
(the continuum likelihood is expensive; see `Tools/qgfit/README.md`).  If a
future run reports `converged: false` with `N_tau < 50` or a width ratio outside
0.5-2.0, increase `conti_steps` first; the width check makes the failure
explicit instead of silently reporting a too-narrow posterior.

## Line template and the H-beta/[O III] ratio

QGfit's native narrow-line profile has a hard-coded `ln_sigma` maximum of
0.0017, i.e. FWHM <= 1200 km/s.  `fwhm_narrow_max` in the config does not
change that internal limit.  For this object the native fit puts the
[O III] 4959/5007 doublet at FWHM ~1131 km/s, close to the cap, and recovers
only 1167 (1e-17) in [O III] 5007.  PyQSOFit, GANDALF, S3Fit, GalSpec and
PyQSOFitSpec all recover 1420-1630 because they allow a broader [O III] profile
or an explicit broad wing (FWHM 1630-1875, 615-855 in flux).

`production_wing/lines_oiii_wing.csv` therefore:

* removes the H-beta narrow row (QGfit's BIC cleanup already sets its norm to
  zero on this object, and the row otherwise lets the optimiser collapse the
  broad H-beta into a 1200 km/s narrow component);
* adds `OIII4959w` and `OIII5007w` `mix` components with an independent width
  and shift and the standard 2.98 doublet ratio.

The continuum is identical to the production run, so the diagnostic uses
`conti_mcmc: false` and reuses the production LSQ continuum; this is recorded
in the README and in the diagnostic `run.json`.  The line MCMC is enabled.
The resulting [O III] 5007 flux and H-beta/[O III] ratio are compared with the
native template in `qgfit_component_comparison.csv` and
`qgfit_ratio_comparison.csv`.

## Units and SFD

* Input `FLUX` is 1e-17 erg s-1 cm-2 A-1 (observed frame).
* QGfit works with `f_rest = f_obs (1+z)^3` and rest-frame wavelength.
* `qgfit_model.csv` is rest-frame f_lambda; sibling model CSVs are usually
  observed-frame, so do not compare their raw continuum columns directly.
* Line fluxes in `qgfit_lines.csv` are observed-frame equivalents:
  `F_obs = integral(F_rest dlambda_rest)/(1+z)^2`.
* `do_deredden: false`; the SFD maps are not shipped, QGfit's `SFD_PATH` is
  empty, and the sibling tools also use the observed SDSS spectrum.  The
  adapter refuses to run if `do_deredden=true` without the maps.  To enable it,
  mount the four `SFD_dust_*.fits` files at `/opt/sfd` (`--sfd-dir DIR`).

## Effective configuration and provenance

Every run writes `qgfit_config.effective.json` (all scalar QGfit controls plus
the line-template path and SHA-256) and `run.json` (input, versions, continuum
and line diagnostics, comparison tables, runtime breakdown, product inventory).
`qgfit.pkl` is a trimmed native result: per-line chains are dropped and the
continuum chain is thinned to 20000 samples; the full continuum chain is in
`qgfit_mcmc_chain.npz`.
