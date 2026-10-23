# S3Fit configs

Two configurations are provided:

* `default/` — full production QSO mode: AGN powerlaw + Fe II + Balmer
  continuum + SKIRTOR torus + NLR/BLR lines, `mode: spec+sed`, 10 Monte-Carlo
  mocks, dual-annealing global search on.  This is the intended full fit but it
  is slow (the first pure-spectrum loop took 1161 s; the full spec+SED 10-mock
  run was not attempted for the committed demonstration).

* `smoke/` — documented fast fallback used for the committed
  `outputs/04592649654_z_0.5874/s3fit_line/` products: pure spectrum, torus
  disabled, no host/SSP term, dual annealing off, one nonlinear try,
  `accept_chi_sq=10`, 3 mocks on 3 threads.  H-alpha/[N II]/[S II] are removed
  because they are outside the SDSS coverage of the validation targets.

`model_config.json` references the component JSON files and the vendored
`Tools/s3fit_line/model_libraries/` FITS files.  `fit_config.json` holds the
mode, mock count, photometry calibration, spectrum mask, and fitting controls.
