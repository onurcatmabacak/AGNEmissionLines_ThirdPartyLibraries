# `cube_lines` — resolved HCN 3-2 mapping of NGC 1275

Input: the real ALMA spw25 cube `NGC1275_sci.spw25.cube.I.pbcor.fits` (project
2018.1.01178.S, 2646x2646 spaxels, 126 channels), cropped to 160x160 spaxels
around the nucleus.  Fetch recipe: `inputs/NGC1275_z_0.0176/source.json`.

```bash
bash pipeline/runners/run_cube_lines_docker.sh <cube> \
    outputs/cube_lines/NGC1275_z_0.0176 \
    --config configs/cube_lines/ngc1275_alma --z 0.01756 \
    --source-key NGC1275_z_0.0176 --plot
```

## Result

| quantity | value |
|---|---|
| aperture spaxel (y, x), cropped frame | (103, 63) |
| velocity | +232 km/s |
| FWHM | 156 km/s |
| snr_integrated | 13.0 |
| snr (peak) | 7.1 |
| chi2/nu | 0.49 |
| spaxels above 3 sigma in the S/N map | 10451 |
| detected | **True** |

Outputs: `cube_maps.fits` (flux / velocity / dispersion / S/N planes),
`cube_maps.png|pdf`, `cube_lines.csv`.

## Caveats that matter

* The aperture is chosen by **signal-to-noise** (3x3-smoothed), not by peak flux:
  on a real cube the brightest integrated flux is usually a noise spike at the
  field edge, and on this object the S/N peak sits ~25 spaxels from the continuum
  nucleus.
* The linear per-spaxel continuum is fitted inside the same +/-1200 km/s band the
  line is extracted from.  The HCN 3-2 line is broad (FWHM ~300-500 km/s from the
  1-D tools), so it fills much of that window: the aperture-integrated moment-0
  flux and the fitted Gaussian amplitude can even disagree in sign.  Velocity and
  dispersion maps are meaningful where the line is detected; the absolute flux
  scale needs a wider band or a simultaneous continuum.
* This is the repository's first product that fits **many spectra from one cube**
  rather than one extracted box, which is what the ALMA and MIRI MRS data were
  bought for.
