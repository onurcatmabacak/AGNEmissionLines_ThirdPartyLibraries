# `nir_linefit` — NIR emission-line tool (Docker)

The `pipeline_ir` router/fitter with a JWST/NIRSpec x1d adapter, packaged as
`nir_linefit`.

## Run

```bash
bash Pipelines/build_images.sh nir_linefit
.venv/bin/python pipeline/run_new_tools.py --only J0100p2802_z_6.3270 --tools nir_linefit --force
```

The runner now produces both the public pipeline x1d fit
(`outputs/.../nir_linefit/`) and a **QSO-centred 3×3 IFU extraction**
(`outputs/.../nir_linefit/centered/`).

## QSO-centred cube extraction

`pipeline/extract_nir_aperture.py` fetches the public JWST/NIRSpec `s3d` cube
(MAST obsid 196672516), finds the target coordinates in the cube WCS, and
writes an `EXTRACT1D` table with a 3×3 spaxel aperture.  The raw 186 MB cube is
not committed; the 107 KB derived table is
`inputs/J0100p2802_z_6.3270/derived/centered_3x3_x1d.fits`.

The **PSF-weighted r=3** extraction (WCS/PC-correct centroid + annulus
background) detects:

* broad Hα at S/N≈34, FWHM≈10,100 km/s;
* narrow Hα and [N II] 6548/6585;
* broad Hβ at S/N≈4.

The 3×3 extraction gives broad Hα S/N≈25 and the pipeline x1d only S/N≈3.4;
all three are retained, with PSF r=3 as the primary result.

## Remaining limitations

* The cube extraction is 3×3; a full PSF/aperture optimisation is not performed.
* No telluric/PAH/AGN-continuum model; the generic local continuum is used.
* The 4.1 µm absorption/gap is a data-quality feature, not a line.
