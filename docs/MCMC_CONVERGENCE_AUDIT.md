# MCMC convergence audit

This page is the honest cross-tool audit requested after the PyQSOFit 13,000-step
and GalSpec 25,000-step runs were found to be below the 50-tau target.  The
lesson is general: **a step count chosen before measuring tau is not a
convergence budget**.  The correct gate is retained chain length / tau_max,
plus ESS and a dimension-appropriate acceptance check.

## Current chains

| tool | product | sampler | retained steps | tau_max | retained steps/tau | verdict |
|---|---|---|---:|---:|---:|---|
| PyQSOFit | `pyqsofit/mcmc` | emcee | 8 | not estimable | — | **initialization test only** |
| PyQSOFit | `pyqsofit/mcmc_long` | emcee | 1,900 | 255.2 (Hb) | 7.4 (Hb) | **not converged** |
| PyQSOFit | `pyqsofit/mcmc_converged` | emcee | 12,900 | 801.8 (Hb) | 16.1 (Hb) | **not converged**; Mg II and 1-D [N II] pass |
| PyQSOFit | `pyqsofit/mcmc_long_65k` | emcee | 50,000 | running | running | **in progress** (65,000 steps, 15,000 burn) |
| GalSpec | `galspec_line` | emcee | 2,800 | 342.6 | 8.2 | **not converged**; production caveat |
| GalSpec | `galspec_line_long` | emcee | 20,000 | 1156.1 | 17.3 | **not converged** |
| GalSpec | `work/galspec_long_70k` | emcee | 60,000 | running | running | **in progress** (80,000 steps, 20,000 burn) |
| GalSpec | `work/galspec_prod200_v2` | emcee (DEMove, gamma0=0.20) | 17,000 | 273.7 | **62.1** | **converged**; acceptance 0.262, 39/39 finite tau, min ESS 12,421 |
| QGfit | `qgfit` continuum | emcee | 800 | 99.5 | 8.0 | **not converged**; chain is not used for the continuum error |
| QGfit | `work/qgfit_long` | emcee | 5,000 | running | running | **in progress** (6,500 steps, 1,500 burn) |
| SHEAP | `sheap_line` | JAX Adam + bootstrap | n/a | n/a | n/a | **not an MCMC** |
| PAHFIT | `pahfit_mir` | least-squares + bootstrap | n/a | n/a | n/a | **not an MCMC**; convergence counts are MC refits |
| PyQSOFitSpec | `pyqsofitspec_line` | parametric bootstrap | n/a | n/a | n/a | **not an MCMC** |
| QSOFITMORE | `qsofitmore_line` | 200 lmfit MC refits | n/a | n/a | n/a | **not an MCMC** |
| S3Fit | `s3fit_line` | mock-spectrum MC | n/a | n/a | n/a | **not an MCMC** |
| CAFE | `cafe_line` | LMFIT covariance MC | n/a | n/a | n/a | **not an MCMC** |

## What was wrong

1. **Fixed budgets.**  PyQSOFit 13,000 and GalSpec 25,000 were selected before
   the final tau estimate.  The PyQSOFit Hβ tau grew from 255 at 1,900 steps to
   802 at 13,000 steps; the same chain is only 16 tau long.
2. **A step-accounting bug in GalSpec.**  `nsteps_over_tau_max` used total
   `nsteps`, while the gate and ESS use burn-in-subtracted retained steps.  The
   production 4,000-step run is 11.7 tau by total steps but only **8.2** by
   retained steps.  The code now reports both and uses retained steps for the
   primary diagnostic.
3. **A dimension-blind acceptance gate in PyQSOFit.**  A 1-D [N II] chain
   accepted 0.806 of proposals and had ESS 47,109 and tau 27.4; the 0.20-0.50
   band is a multi-dimensional guideline.  Treating it as a failure was a
   false alarm.  The gate now uses 0.05-0.95 for `nvarys == 1` and 0.20-0.50
   otherwise, and records `acceptance_band`/`acceptance_ok`.

## What is not an MCMC problem

SHEAP's uncertainty is a parametric bootstrap; QSOFITMORE, S3Fit, CAFE,
PyQSOFitSpec and PAHFIT use covariance or Monte-Carlo refits.  Those are not
chains and must not be described with tau/N_tau.  Their own convergence or
validity flags still matter, but they are out of scope for this gate.

## Diagnosis: why longer alone was not the answer

The old chains were not merely short.  They had **burn-in shorter than the
measured autocorrelation time**, and some weakly constrained line
parameters had a real initial transient.  Rhat (split-walker) and Geweke
(first 10% versus last 50%) on the old products:

| chain | burn | tau_max | burn/tau | Rhat max | worst drift |
|---|---:|---:|---:|---:|---|
| PyQSOFit H-beta | 100 | 801.8 | 0.12 | 1.073 | `HeII4687_br_1_sigma`; scale changes from ~0.98 to ~0.01 |
| PyQSOFit continuum | 100 | 521.2 | 0.19 | 1.077 | `conti_a_0`; PL slope drifts |
| PyQSOFit Mg II | 100 | 144.6 | 0.69 | 1.012 | weak, but not fully burned |
| PyQSOFit [N II] | 100 | 27.4 | 3.7 | 1.002 | none significant |
| GalSpec | 5,000 | 1156.1 | 4.3 | 1.271 | amplitudes 9/23, dv 5; acceptance 0.168 |
| QGfit | 200 | 99.5 | 2.0 | 1.973 | `f_old`, `host_shift`, `sigma`, `m_s`; strong drift |

The QGfit and PyQSOFit cases show that **adding steps while keeping a tiny
burn-in does not remove the transient**; it only mixes it into the retained
chain and inflates tau.  GalSpec's low acceptance and amplitude drift point to
the same combination of short burn and weak-line parameterisation.

The corrective runs therefore change the burn-in, not only the total:

| chain | total steps | burn | retained | burn/tau at old tau |
|---|---:|---:|---:|---:|
| PyQSOFit | 65,000 | 15,000 | 50,000 | 18.7 |
| GalSpec | 80,000 | 20,000 | 60,000 | 17.3 |
| QGfit | 6,500 | 1,500 | 5,000 | 15.1 |

These are still checks.  If Rhat remains >1.01 or the drift persists, the next
action is to diagnose the specific parameter (weak-line prior, initialization,
or multimodal likelihood), not another blind step increase.

## The GalSpec 7/39 tau report was a dead-walker artefact

The 200x20,000 `production_demove` chain (`work/galspec_prod200`) reported
`tau_status = ok (tol=0.0; best finite=7/39)` and only 7 finite tau values.
The chain length was not the problem.  On the same retained chain: with all
200 walkers emcee returns `0/39` finite tau; with the 196 live walkers it
returns `39/39`.  Four walkers had started where the continuum-positivity
prior is zero (`log_prob = -inf`) and never moved again, because DEMove steps
scale with the ensemble spread.  emcee's estimator averages one ACF per
walker and normalises by each walker's lag-zero power, so a constant series
contributes `0/0 = NaN` and poisons every parameter.

Two corrections are now in `galspec_full.run_full_mcmc`:

1. walkers with a non-finite initial `log_prob` are redrawn before sampling
   (28/200 in this model, of which 4 used to freeze permanently);
2. `_robust_autocorr` masks non-finite-log-prob walkers and falls back to a
   per-parameter ACF that skips zero-variance walkers.

The acceptance problem was separate and real: 2.38/sqrt(2*ndim) = 0.269
over-steps against the positivity prior (0.139 measured, 0.080 at 0.35,
0.034 at 0.45).  With `gamma0 = 0.20` acceptance is 0.262 while tau_max stays
at 274 steps, so the same 20,000-step budget now reaches 62 tau.

## Open corrections

- QGfit's committed continuum chain is still 8 tau; its README and `run.json`
  explicitly say it is not converged and it is not used as the continuum
  error.  A 6,500-step/1,500-burn run is now active; it is not a completed
  correction until its tau and Rhat are checked.
- GalSpec's production 4,000-step output remains a documented caveat until the
  70,000-step run is complete, but `work/galspec_prod200_v2` (62.1 tau,
  acceptance 0.262, 39/39 finite tau) is a converged 20,000-step product.
- PyQSOFit's 55,000-step run is in progress; its result must be checked, not
  assumed converged.
