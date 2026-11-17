# `pyqsofit` — 04592649654_z_0.5874

The production product is `mcmc_long_65k/`: 65,000 steps / 15,000 burn / 50,000 retained, converged on all four parameter blocks (H-beta 62.7 tau, continuum 63.7, Mg II 308.6, 1-D [N II] 1834.6).  `mcmc_long/` and `mcmc_converged/` are the shorter chains retained for comparison.

## Variants

- [`mcmc_long_65k/`](mcmc_long_65k/README.md)
- [`mcmc_long/`](mcmc_long/README.md)
- [`mcmc_converged/`](mcmc_converged/README.md)

The data and bulk artefacts are not shipped (see `outputs/README.md`); the
observation can be restored from `inputs/04592649654_z_0.5874/source.json` and the tool
re-run with `pipeline/runners/run_pyqsofit_docker.sh`.  Status, severity and
evidence for the tool are in `docs/CAVEAT_MATRIX.md`.
