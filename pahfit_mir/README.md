# `pahfit_mir` — PAHFIT 2.0 for MIR spectra (Docker)

PAHFIT 2.0 for JWST/MIRI MRS, PAHFIT `s1d`, and Spitzer IRS spectra.

## Run

```bash
bash pipeline/build_images.sh pahfit_mir
.venv/bin/python pipeline/run_new_tools.py --only VV114_z_0.0200 --tools pahfit_mir --force
.venv/bin/python pipeline/run_new_tools.py --only PDS456_z_0.1840 --tools pahfit_mir --force
```

Inputs can be `*_x1d.fits` (`SURF_BRIGHT`/`SB_ERROR`), `*_s1d.fits`, or an
Spitzer IRS Enhanced `.tbl`.  Spitzer Jy is converted to MJy/sr using the
SL/LL slit solid angles before fitting.

## PDS 456 handling

The short/long MIRI spectra are fitted separately and jointly:

```text
outputs/PDS456_z_0.1840/pahfit_mir/short/
outputs/PDS456_z_0.1840/pahfit_mir/long/
outputs/PDS456_z_0.1840/pahfit_mir/both/
```

`--smooth-um` median-bins the high-resolution MRS data to a PAHFIT-friendly
grid.  Each summary records `rms_rel` and `unstable`.  The short segment is
stable; the long/both solutions are retained but flagged, not presented as
quantitative detections.

## Validation

* VV114 MIRI MRS: rms≈0.18, 53 features; pass gate.
* Mrk 231 Spitzer IRS (real AGN): rms≈0.35.
* NGC 253 Spitzer IRS: rms≈2.4 and `unstable=true`; retained as a real-data
  stress test, not an AGN pass.
* PDS 456 short: rms≈0.41; long/both higher and flagged.

## Remaining limitations

* PAHFIT assumes its standard feature pack; extreme MIRI resolution and
  short/long calibration discontinuities still require careful binning.
* Feature `power` uncertainties are not propagated into `pahfit_features.csv`;
  the crossband builder uses a 10 % working error.
* No simultaneous MIR line + PAH + AGN torus model.
