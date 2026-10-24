# S3Fit configs

Three configurations are provided:

* `production/` — **the recipe used for the committed production run**.  Full
  QSO model grid (AGN powerlaw + Fe II + Balmer continuum + SKIRTOR torus +
  NLR/BLR lines), `mode: spec+sed`, 8 SDSS/WISE bands, 10 Monte-Carlo mocks,
  `threads: 8`.  Runtime compromise: dual-annealing initialisation is off,
  `nlfit_ntry_max=1`, `accept_chi_sq=10`.  The model grid and mock count are
  **not** reduced.  See the measured runtime in
  `Tools/s3fit_line/README.md`.

* `default/` — the same full model but with dual-annealing on and
  `nlfit_ntry_max=3`.  It is the higher-effort reference configuration; a
  trial reached the same original reduced chi2 = 1.035 but took ~1.95x longer
  for the original loop and projected to >2 h for 10 mocks on this host.

* `smoke/` — documented legacy fast fallback: pure spectrum, torus disabled,
  dual annealing off, one nonlinear try, `accept_chi_sq=10`, 3 mocks.  Its
  committed output has been superseded by the production run; do not quote it
  as a production result.

## Production command

```bash
bash Pipelines/run_s3fit_line_docker.sh \
  inputs/04592649654_z_0.5874 outputs/04592649654_z_0.5874/s3fit_line \
  --config configs/s3fit_line/production --n-mocks 10 --threads 8
```

Measured on the 8-core host: 58 min 21 s wall, `main_fit()` 3483.9 s,
original loop 412.8 s, MC block 3071.1 s (10/10 mocks successful),
reduced chi2 = 1.035 (original) and 1.605 +/- 0.112 (mocks).

## Line-list handling and fixes

`model_config.json` references the component JSON files and the vendored
`Tools/s3fit_line/model_libraries/` FITS files.  `fit_config.json` holds the
mode, mock count, photometry calibration, spectrum mask, and fitting controls.

The adapter applies two line-list fixes at runtime:

1. **Coverage filter.**  Lines whose rest-frame centres lie outside the
   fitted spectrum are removed before `FitFrame` is constructed.  This stops
   S3Fit from fitting extrapolated lines and, importantly, prevents an
   uncovered H-alpha line from becoming the BLR hydrogen reference and tying
   H-beta to an extrapolation.  For `04592649654` the fitted rest range is
   2299–6489 A; H-alpha, [N II] 6550/6585, [S II] 6718/6733 and C III] 1909
   are removed.  The list is recorded in `run.json -> scope.line_coverage`.

2. **Mg II doublet tie.**  `line_config.json` contains
   `["Mg II]:2796", "Mg II]:2804"]`.  The two broad components are blended and
   individually degenerate; without the tie all flux moved to 2796 and 2804
   was ~0.  The tie uses S3Fit's atomic ratio 1.0, so both components are
   reported with equal flux and the total is stable.

`fit_config.json` is the effective control file; the adapter writes the
resolved config to `fit_config.effective.json` in the output directory.
