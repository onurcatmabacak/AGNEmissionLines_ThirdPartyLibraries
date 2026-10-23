# `configs/gandalf_line/default/`

* `emission_lines_setup` — GANDALF v1.5 rest-frame emission-line setup.  The
  columns are `i_line name lambda action l-kind A_i V_g/i sig_g/i fit-kind`.
  All lines start as `action=m` so the driver can test coverage; in-window
  lines are switched to `f`.  Multiplet satellites use `d#` and the published
  flux ratios.  Narrow H-beta is tied to [O III] 5007; broad H-beta is free.
* `config.json` — grid/template paths, `int_disp_kms=61.5` (SDSS), `mdegree=3`,
  PPXF attempt/acceptance controls, fixed 300 km/s stellar fallback, mask
  widths, detection threshold and timeout.

To adapt to a different instrument, change `int_disp_kms` and use matching
templates on a log10 grid with the same `dlog`; do not mix resolutions.
