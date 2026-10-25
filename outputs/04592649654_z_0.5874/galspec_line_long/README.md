# GalSpec long chain — NOT CONVERGED

This is the 25,000-step, 80-walker, burn-in 5,000 GalSpec full-continuum
MCMC run.  It was run with four workers to avoid oversubscribing the host
while the MaNGA and PyQSOFit jobs were active.

## Convergence verdict

**NOT CONVERGED.**

- retained steps: 20,000
- `tau_max`: 1156.05
- steps per `tau_max`: **21.63** (gate: >= 50)
- required retained steps for 50 tau: **57,803**
- acceptance fraction: **0.168** (gate: 0.20–0.50)
- effective sample size: **1384**

The short autocorrelation-time status in `run.json` (`tau_status: ok`) only
means the emcee autocorrelation estimate is usable; it is not the convergence
gate used here.

## Measured line totals

H-beta total = 3652.25 (1e-17 erg/s/cm2), [O III] 5007 = 1710.69; the ratio
is about 2.13.  These are recorded for diagnostics only and are **provisional**.

## Files

`galspec_lines.csv`, `galspec_model.csv`, `galspec_mcmc.npz`, corner and
uncertainty figures, and the effective configuration are retained.  The
production GalSpec result remains in `outputs/.../galspec_line/`.
