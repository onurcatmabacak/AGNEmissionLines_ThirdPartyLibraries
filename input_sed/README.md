# `input_sed` — SDSS + WISE photometry for CIGALE

The five **z > 0.5** eFEDS QSOs already used for the PyQSOFit-UV and pPXF-host
pilots (`input_zgt05/`) supply the photometry.  No new data are introduced.

## Source columns

`input_zgt05/*.fits`, extension `SPALL`:

| catalogue column | use |
|---|---|
| `CATALOGID` | object id |
| `MAG` | SDSS `u,g,r,i,z` AB magnitudes (the `u` entry is the `-9.99999` sentinel in every object, so `u` is omitted) |
| `WISE_MAG` | WISE `W1,W2,W3,W4` Vega magnitudes |

`ZALL["Z"]` supplies the spectroscopic redshift.

`SPALL` has **no magnitude-error columns**.  The table therefore uses nominal
errors: **0.05 mag** for SDSS and **0.125 mag** for WISE (a conservative choice
for the WISE points).  CIGALE additionally applies its own 10 % flux-error
floor, so the errors written into `out/observations.fits` are slightly larger
than the values in `photometry.txt`.

## Conversion

* SDSS AB magnitudes: `F[mJy] = 3631 Jy * 10^(-0.4 m) * 1000`.
* WISE Vega magnitudes: zero points `309.54, 171.79, 31.67, 8.363 Jy`
  for W1–W4, same conversion to mJy.
* Flux error: `sigma_F = F * sigma_m * ln(10) / 2.5`.

## Files

* `photometry.txt` — the table consumed by CIGALE.  Columns are
  `id redshift` + `sloan.sdss.{g,r,i,z}` + `wise.{W1,W2,W3,W4}` +
  the corresponding `_err` columns.  The `_err` block follows the flux block
  (CIGALE matches columns by name, not position).
* `build_photometry.py` — reproducible generator (`.venv/bin/python
  input_sed/build_photometry.py`); the `astropy` dependency is available in
  the repo `.venv`.

## Caveats

* The `u` band is missing for all five objects.
* WISE photometry can be blended/contaminated at 12 and 22 µm; the CIGALE
  pilot treats it as the QSO counterpart without a deblending prior.
* The adopted errors are not the true catalogue errors; they are a documented
  working assumption for this pilot.
