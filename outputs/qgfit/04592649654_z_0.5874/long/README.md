# QGfit continuum chain — host-fixed, 10,000 steps (converged)

The QGfit continuum MCMC for `04592649654_z_0.5874` with the BC03 host block
fixed at the least-squares solution (`mcmc_fix_host = true`,
`configs/qgfit/long/config.json`).

| | |
|---|---|
| sampler | lmfit/emcee, 100 walkers × 10,000 steps, 1,500 burn |
| retained | 8,500 steps (850,000 samples, thin 43) |
| acceptance | **0.374** (min 0.344) |
| τ_max | 151.6 steps |
| N_τ (retained / τ_max) | **56.1** |
| posterior-width check | MCMC/LSQ width 0.59 (target 0.5–2.0) ✔ |
| verdict | **converged** (`continuum.mcmc.converged = true`) |

Fixing the host block is what made this tractable: the free-host 6,500-step
attempt reached only 38 τ with τ_max 599, because the `f_old / m_s /
age_young / a_v / host_shift` ridge dominates the autocorrelation time.
Freeing it again would need roughly 30,000 retained steps.

## What this product does and does not change

* The committed production QGfit product (`../`) still uses **LSQ covariance**
  for its line errors; this chain does not replace them.
* The line MCMC stays disabled: the 50×300 pilot gave per-complex τ = 20–42,
  N_τ = 5–11 and red-χ² ≈ 6·10¹⁰ versus LSQ 11.5, i.e. a broken posterior,
  not a short chain.  `statistical_mode.line_converged = false` records that.

## Files

`qgfit_mcmc_chain.npz` (thinned chain), `qgfit_mcmc_summary.csv`,
`qgfit_uncertainty.png`, `qgfit_corner`/`qgfit_native_corner.jpg`, the fit and
residual figures, `qgfit_lines.csv`, `qgfit.pkl`, `run.json`.
