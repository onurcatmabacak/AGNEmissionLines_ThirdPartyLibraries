# GalSpec production v2 (DEMove, gamma0 = 0.20)

200 walkers, 20,000 steps, 3,000 burn (17,000 retained), `DEMove` with
`gamma0 = 0.20`, 7 workers.  Same sampling budget as `production_demove`, so
the change in every diagnostic comes from the fixes below, not from more
steps.

## Why this config exists

`production_demove` (gamma0 = 2.38/sqrt(2*ndim) = 0.269) produced a
scientifically correct posterior but two unusable diagnostics:

| diagnostic | `production_demove` | `production_v2` |
|---|---:|---:|
| acceptance fraction | 0.139 (below the 0.15 floor) | **0.262** (inside 0.15-0.70) |
| finite tau | **7/39** | **39/39** |
| tau_max (steps) | 317.3 | 273.7 |
| retained steps / tau_max | 53.6 | **62.1** |
| min ESS | 10,717 | **12,421** |

### Fix 1: walkers that start outside the prior support are redrawn

28 of 200 walkers were initialised where the continuum-positivity prior is
zero.  `DEMove` steps scale with the ensemble spread, so those walkers could
never jump back into the allowed region: 4 of them stayed frozen for the whole
20,000-step chain.  emcee normalises each walker's autocorrelation function by
that walker's own lag-zero power, so a constant series gives `0/0 = NaN`, and
**one** frozen walker turns every parameter's tau into NaN.  That is the
mechanism behind the reported `7/39` finite tau, not a short chain.

`run_full_mcmc` now evaluates `log_prob` on the initial ensemble and redraws
every non-finite walker (shrinking jitter, then jitter around a live walker)
before sampling.  The run log records
`initial ensemble: redrew 28/200 walkers ...`.

### Fix 2: tau is estimated on live walkers only

`_robust_autocorr` masks any walker with a non-finite log-probability before
calling `emcee.autocorr.integrated_time`, and falls back to a per-parameter
ACF average that skips zero-variance walkers.  `run.json` records
`n_walkers_used_for_tau` and, in `tau_status`, the walker count and the move.

### Fix 3: gamma0 = 0.20

The Gaussian optimum 2.38/sqrt(2*ndim) over-steps against the hard
continuum-positivity prior: measured acceptance from a warm converged ensemble
was 0.139 at 0.269, 0.124 at 0.30, 0.080 at 0.35 and 0.034 at 0.45.  At 0.20
the acceptance is 0.262 while tau_max stays at 274 steps, i.e. the extra
acceptance is free.

## Result (`work/galspec_prod200_v2`, 7,009.6 s)

| quantity | value |
|---|---:|
| acceptance | 0.262 |
| tau_max | 273.7 steps |
| retained steps / tau_max | 62.1 |
| total steps / tau_max | 73.1 |
| effective sample size (min / median) | 12,421 / 18,044 |
| finite tau | 39/39 |
| walkers used for tau | 200/200 |
| dead samples (non-finite log-prob) | 0 |
| frozen walker-parameter cells | 0 |

The posterior itself is unchanged: H-beta total 3654.9 vs 3654.0,
[O III] 5007 total 1712.3 vs 1712.9, Mg II broad 818.1 vs 818.1 (all
within 0.04 sigma of `work/galspec_prod200`).  The fixes correct the
diagnostics and stop wasting four chains; they do not move the science.
