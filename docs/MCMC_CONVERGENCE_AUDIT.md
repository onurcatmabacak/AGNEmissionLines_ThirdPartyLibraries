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
| PyQSOFit | `pyqsofit/mcmc_long_55k` | emcee | 54,900 | running | running | **in progress** |
| GalSpec | `galspec_line` | emcee | 2,800 | 342.6 | 8.2 | **not converged**; production caveat |
| GalSpec | `galspec_line_long` | emcee | 20,000 | 1156.1 | 17.3 | **not converged** |
| GalSpec | `galspec_long_70k` | emcee | 65,000 | running | running | **in progress** |
| QGfit | `qgfit` continuum | emcee | 800 | 99.5 | 8.0 | **not converged**; chain is not used for the continuum error |
| QGfit | `work/qgfit_long` | emcee | 5,300 | running | running | **in progress** (5,500 steps, 200 burn) |
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

## Open corrections

- QGfit's committed continuum chain is still 8 tau; its README and `run.json`
  explicitly say it is not converged and it is not used as the continuum
  error.  A 5,500-step run is now active; it is not a completed correction
  until its tau is checked.
- GalSpec's production 4,000-step output remains a documented caveat until the
  70,000-step run is complete.
- PyQSOFit's 55,000-step run is in progress; its result must be checked, not
  assumed converged.
