# PyQSOFit 13,000-step MCMC — NOT CONVERGED OVERALL

The chain was run with 100 walkers, 13,000 retained steps, line workers=4 and
a capped derived-quantity loop.  Full float64 samples are 134 MB and are kept
outside Git at:

```text
work/mcmc_converged_full/pyqsofit_mcmc_samples.float64.npz
```

The committed `pyqsofit_mcmc_samples_float32.npz` is a float32 downcast
(65 MB, not bit-identical) so that the posterior stays usable in a clone.

## Convergence verdict

**NOT CONVERGED.**

| complex | steps/tau | ESS_min | acceptance | verdict |
|---|---:|---:|---:|---|
| Mg II | 89.2 | 8921 | 0.407 | passes |
| continuum | 24.7 | 2475 | 0.301 | fails 50-tau |
| H-beta | 16.1 | 1609 | 0.246 | fails 50-tau |
| [N II] | 471.1 | 47109 | 0.806 | passes (1-D band 0.05–0.95) |

Mg II and the 1-D [N II] chain pass; H-beta and continuum fail the 50-tau gate.
Do not use the H-beta or continuum posterior as a publication-grade error budget.  The earlier 1,900-step diagnostic in
`../mcmc_long/` is also not converged.
