# cube_lines — spatially resolved spectral-line fitting

`run_cube_lines.py` fits a 3-D spectral cube instead of a single extracted
spectrum: per-spaxel continuum removal in line-free windows, moment maps
(flux, velocity, dispersion), an aperture Gaussian fit with the shared
`pipeline/line_snr.py` statistics, and line-ratio maps.

Input: any FITS cube with celestial + spectral WCS, including JWST MIRI MRS
`s3d` products (whose spectral axis is a `-TAB` table — astropy needs
`WCS(header, fobj=hdul)` for those).  Intensity must be surface brightness
(`MJy/sr`); fluxes are converted to W/m^2 with the spaxel solid angle.

Outputs: `cube_lines.csv` (per line: aperture spaxel, flux, centre, FWHM, S/N),
`cube_ratios.csv`, `cube_maps.fits` (one ImageHDU per moment), optional PNG/PDF.

```bash
bash pipeline/runners/run_cube_lines_docker.sh cube_s3d.fits out/ \
    --config configs/cube_lines/pds456_miri --z 0.184 --source-key PDS456_z_0.1840
```
