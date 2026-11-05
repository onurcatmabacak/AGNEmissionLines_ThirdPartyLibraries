# PyQSOFit MCMC — 65,000-step production chain (converged)

Independent emcee re-sampling of the PyQSOFit UV/optical fit for
`04592649654_z_0.5874`: 100 walkers × 65,000 steps, 15,000 burn, 50,000
retained, seed 20240518.  Image `pyqsofit_uv`, git `ed97633`.

## Convergence verdict: **converged on all four blocks**

| block | nvarys | acceptance | τ_max | retained / τ | ESS (min) | verdict |
|---|---:|---:|---:|---:|---:|---|
| Hβ | 17 | 0.240 | 797.1 | **62.7** | 6,273 | converged |
| Mg II | 9 | 0.407 | 162.0 | **308.6** | 30,861 | converged |
| [N II] (1-D) | 1 | 0.807 | 27.3 | **1,834.6** | 183,458 | converged |
| continuum | 11 | 0.301 | 784.5 | **63.7** | 6,373 | converged |

Wall time 40,151 s (11.2 h).  Every block is above the 50-τ gate; the two
long-tau blocks (Hβ and continuum, τ ≈ 785-797) are the binding ones.

The 1-D [N II] chain accepts 0.807, outside the 0.20–0.50 multi-dimensional
band.  That is a proposal-geometry artefact of a one-variable target, not a
stuck chain: ESS 183,458 and 1,834 τ.  `docs/MCMC_CONVERGENCE_AUDIT.md`
records the same reading.

## Context

This supersedes the 12,900-step chain (`../mcmc_converged`) where Hβ was 16.1 τ
and the continuum 24.7 τ.  The Hβ τ grew from 255 at 1,900 steps to 802 at
13,000 steps and 797 here, so the earlier budgets were simply too short — the
fix was chain length, not a different sampler.

## Files

`pyqsofit_mcmc_summary.csv` (posterior medians and 16/84 percentiles per line
component), `pyqsofit_lines.csv` (MLE fluxes), `pyqsofit_mcmc_samples.csv`,
`pyqsofit_mcmc_corner.png/pdf`, `pyqsofit_mcmc_line_corner.png`,
`pyqsofit_mcmc_trace.png/pdf`, `pyqsofit_model.csv`, `output.fits`,
`pyqsofit_mcmc_config.json`, `run.json` (per-block diagnostics).

The full float64 sample array (512 MB) exceeds GitHub's per-file limit and is
git-ignored; `pyqsofit_mcmc_samples.csv` holds the same posterior in text form.
