# PyQSOFit MCMC status — `04592649654_z_0.5874`

## Exact failure that was repaired

`PYQSOFIT_MCMC=1` previously failed in the H-alpha line complex with:

```text
File "/app/pyqsofit/PyQSOFit/src/pyqsofit/PyQSOFit.py", line 1564, in fit_lines
  line_samples = minimize(self._residual_line, params=line_fit.params, args=args,
File "/usr/local/lib/python3.12/site-packages/lmfit/minimizer.py", line 1405, in emcee
  output = self.sampler.run_mcmc(p0, steps, progress=progress, **run_mcmc_kwargs)
File "/usr/local/lib/python3.12/site-packages/emcee/ensemble.py", line 319, in sample
  raise ValueError(
ValueError: Initial state has a large condition number.
Make sure that your walkers are linearly independent for the best performance
```

The H-alpha MLE was:

```text
SII6718_1_scale:  0.00000000 (init = 0)   free, bounds [0, 1e10]
SII6732_1_scale:  0.00000000 (init = 0)   free, bounds [0, 1e10]
```

lmfit 1.3.2 constructs the default emcee state as
`p0 = (1 + 1e-4 * N(0, 1)) * param.value`.  The two undetected [S II]
amplitudes are exactly zero, so two columns of `p0` are identically zero.
`emcee.walkers_independent()` rejects that state.  The continuum, Mg II and
H-beta chains had already sampled; only H-alpha failed.

## Fix

`configs/pyqsofit/uv/mcmc_support.py` installs a wrapper around
`pyqsofit.PyQSOFit.minimize` and supplies an explicit `pos` to every emcee
call:

* every free parameter is jittered around its MLE with a positive,
  bounds-aware scale;
* a zero amplitude starts at 0.1% of the largest fitted amplitude in the same
  complex (for [S II] this is a small positive seed, not a fixed value);
* the state is clipped inside the uniform bounds and checked for
  `ptp > 0` and `cond <= 1e8`;
* model, priors, tied expressions, fixed parameters and `emcee` moves are
  unchanged;
* the wrapper records the chain, ln-probability, acceptance fraction,
  integrated autocorrelation time and ESS, and recomputes tied/expression
  parameters per draw for the line-flux posterior.

## What is committed

| product | status |
| --- | --- |
| `pyqsofit_mcmc_fit.pdf`, `pyqsofit_mcmc_fit.png` | fit figure from the 300-step capped run; fit wall time **1400.6 s** |
| `output.fits`, `qsopar.fits` | best-fit products preserved from that run |
| `pyqsofit_mcmc_samples.csv` | line-flux posterior from the validated **10-step** run |
| `pyqsofit_mcmc_samples.npz` | full chains/diagnostics from that 10-step run |
| `pyqsofit_mcmc_corner.pdf/.png`, `trace.pdf/.png`, `line_corner.png` | posterior figures from that 10-step run |
| `pyqsofit_mcmc_summary.csv` | median/p16/p84 for Hβ, [O III] and Mg II |
| `comparison_mc_tools.csv` | short-MCMC vs 100-realization MC and GANDALF/S3Fit/GalSpec/QGfit |
| `run.json`, `pyqsofit_mcmc_config.json` | exact versions, config and diagnostics |
| `../mc/*` | committed 100-realization MC; still the recommended uncertainty product |

The 300-step run used
`NSAMP=300, NBURN=80, NTHIN=1, NWALKERS=100, SEED=20240517`, retaining 220
steps per walker (22,000 draws).  Its outer shell timed out after
`Fitting finished in 1400.6s` and before the container copied the chains; the
preserved `result.pdf`, `output.fits` and `qsopar.fits` are that run.  This is
a runner timeout, not a sampler failure.

The 300-step log diagnostics were:

| stage | nvarys | acceptance mean ± std | tau mean | tau max | retained steps / tau_max |
| --- | --- | --- | --- | --- | --- |
| continuum | 11 | 0.367 ± 0.036 | 24.5 | 36.0 | 6.1 |
| Mg II | 9 | 0.406 ± 0.040 | 21.6 | 29.0 | 7.6 |
| Hβ | 17 | 0.317 ± 0.035 | 28.0 | 38.1 | 5.8 |
| Hα | 12 | 0.361 ± 0.040 | 25.4 | 35.2 | 6.3 |

Those chains are still short of the 20–50 tau convergence target (220 retained
steps vs tau_max 29–38); a longer run needs roughly 600–800 retained steps.

## Short-run convergence diagnostics

10-step validation run (`NSAMP=10, NBURN=2, NTHIN=1, NWALKERS=100`; 8 retained
steps = 800 draws; 10 line-posterior draws):

| stage | nvarys | acceptance mean ± std | tau | ESS | converged |
| --- | --- | --- | --- | --- | --- |
| continuum | 11 | 0.312 ± 0.158 | unavailable (chain too short) | — | no |
| Mg II | 9 | 0.315 ± 0.143 | unavailable | — | no |
| Hβ | 17 | 0.266 ± 0.134 | unavailable | — | no |
| Hα | 12 | 0.286 ± 0.156 | unavailable | — | no |

Acceptance is in the healthy 0.2–0.5 band, but 8 retained steps are far below
the ≥20–50 tau needed for a converged posterior.  The MCMC error bars in
`comparison_mc_tools.csv` are therefore **not** a converged uncertainty
estimate.  The 100-realization MC (`../mc/pyqsofit_mc_summary.csv`) remains
the committed uncertainty.

## Recommended next run

With the PyQSOFit internal per-draw `line_prop` loop, 1000 retained steps took
well over an hour and did not finish in the available shell budget.  The
practical recipe is the one in the README:

```bash
PYQSOFIT_MCMC=1 PYQSOFIT_NSAMP=300 PYQSOFIT_NBURN=80 PYQSOFIT_NTHIN=1 \
PYQSOFIT_NWALKERS=100 PYQSOFIT_MCMC_SEED=20240517 \
PYQSOFIT_MCMC_LINE_SAMPLES=500 \
bash pipeline/runners/run_pyqsofit_uv_docker.sh <input-dir> <output-dir>
```

Run it under a persistent shell (not a tool timeout) so the runner's final
`cp *.json *.npz` executes.  Vectorizing PyQSOFit's per-sample `line_prop`
loop is the prerequisite for a genuinely converged >500-step production
chain.
