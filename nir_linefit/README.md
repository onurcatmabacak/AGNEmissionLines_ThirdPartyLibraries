# `nir_linefit` — NIR emission-line tool (Docker)

The `pipeline_ir` router/fitter with a JWST/NIRSpec x1d adapter, packaged as
`nir_linefit`.

## Run

```bash
bash pipeline/build_images.sh nir_linefit
.venv/bin/python pipeline/run_new_tools.py --only J0100p2802_z_6.3270 --tools nir_linefit --force
```

Input: `inputs/J0100p2802_z_6.3270/raw/*_x1d.fits` (or another x1d/SDSS-style
spectrum).  Output: `outputs/<source>/nir_linefit/`.

The adapter handles NIRSpec `FLUX` [Jy] and MIRI `SURF_BRIGHT` [MJy/sr]; DQ≠0
pixels are masked.  Undetected Hβ, [O III], [N II], narrow Hα and [S II]
components are written as finite 3σ upper limits; the broad Hα is detected in
J0100+2802 (S/N≈3.4, FWHM≈10,100 km/s).

## Remaining limitations

* One IFU extraction only; a QSO-centred aperture may recover Hβ/[O III].
* No telluric/PAH/AGN-continuum model; the generic local continuum is used.
* The 4.1 µm absorption/gap is a data-quality feature, not a line.
