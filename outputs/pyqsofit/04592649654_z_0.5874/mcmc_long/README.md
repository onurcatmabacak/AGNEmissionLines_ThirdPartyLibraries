# PyQSOFit 1900-step MCMC (not converged)

Full 1900 retained-step chain, 100 walkers, line workers=4/8 and capped
derived-quantity loop.  The chain is **not converged**:

- Hβ: 7.45 steps/tau (tau_max 255.2)
- Mg II: 21.3 steps/tau
- continuum: 11.0 steps/tau
- N II: 74.2 steps/tau

`run.json` records the full diagnostics.  This product is retained as evidence
that the workers/capped-loop path runs end-to-end; it is not a converged
posterior.  The `mcmc_converged` directory is a longer 13,000-step run.
