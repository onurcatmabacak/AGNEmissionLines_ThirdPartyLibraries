# pahfit_mir — PAHFIT 2.0 for MIR spectra (Docker)

The MIR-suite tool: **PAHFIT 2.0** (GitHub source) in Docker, fitting PAH,
dust-continuum and fine-structure/molecular features to JWST/MIRI MRS or
Spitzer/IRS spectra.

## Build / run

```bash
bash pipeline/build_images.sh pahfit_mir

# PAHFIT's packaged MIRI MRS validation spectrum (12 segments, z=0.020)
bash run_pahfit_mir_docker.sh input_mir_vv114 results_ir/mir_vv114_all 0.020 --s1d

# JWST MIRI x1d short/long (real data)
bash run_pahfit_mir_docker.sh input_mir results_ir/mir_pds456 0.184 --segment both
```

Inputs: `*_s1d.fits` (PAHFIT format: wavelength/flux/uncertainty, MJy/sr) or
JWST `*_x1d.fits` (`SURF_BRIGHT`/`SB_ERROR`, MJy/sr). Output: PAHFIT feature
table, ECSV model, fit figure, summary JSON.

## Validation: VV114 MIRI MRS (PAHFIT's included example)

`input_mir_vv114/` — 12 MIRI MRS segments, 5.0–28.0 µm, z=0.020, 9,096 pixels.
PAHFIT fits 53 features; the model tracks the data across the full MIRI range
with residuals mostly within ±2.5 %. **Inspect:**
`results_ir/mir_vv114_all/pahfit_fit.png` / `.pdf`,
`pahfit_features.csv`, `pahfit_summary.json`.

## Real MIRI AGN: PDS 456 (z=0.184) — caveat

`input_mir/` contains the real JWST/MIRI MRS x1d short+long spectrum of PDS 456.
The combined and single-segment PAHFIT fits are **unstable**: the fitter drives
very large PAH powers and the residuals reach hundreds of percent. The likely
causes are the high MRS spectral resolution, the short/long calibration
discontinuity, and the lack of a QSO-centred extraction. These fits are not
used as a pass gate; the VV114 example validates the tool. The PDS 456 route is
kept as the next data-reduction target (smooth to PAHFIT's R, use a QSO-centred
aperture, and verify the MIRI flux calibration).

## Caveats

- PAHFIT requires intensity units (MJy/sr); the x1d `FLUX` (Jy) must be
  converted or `SURF_BRIGHT` used.
- MIRI MRS is high-resolution; PAHFIT's feature model assumes the instrument
  pack; validate per segment before fitting a full spectrum.
