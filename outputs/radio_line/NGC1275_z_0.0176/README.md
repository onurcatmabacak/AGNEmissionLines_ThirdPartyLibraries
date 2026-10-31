# `radio_line` — real ALMA data: NGC 1275 HCN 3-2

Input: `inputs/NGC1275_z_0.0176/raw/ngc1275_hcn32_spectrum.fits`, extracted from the
real **primary-beam-corrected** ALMA cube `NGC1275_sci.spw25.cube.I.pbcor.fits`
(project 2018.1.01178.S, 260.35-262.18 GHz, 126 channels of ~17 km/s, 2646x2646
spaxels, 3.4 GB):

```bash
python pipeline/extract_cube_spectrum.py <cube> \
    inputs/NGC1275_z_0.0176/raw/ngc1275_hcn32_spectrum.fits --box 41 --unit Jy
```

## Result

| component | v (km/s) | FWHM (km/s) | amplitude (Jy) | S/N | detected |
|---|---:|---:|---:|---:|---|
| c1 | +312 | 68 | 6.4e-3 | 2.9 | no |

chi2/nu = 0.72

## Reading

pyspeckit Gaussian decomposition, one component plus a flat baseline.

The line is **not detected at 3 sigma** in this extraction: the peak channel is
~3.8 sigma but the profile is broad, so the integrated fit stays marginal.  What
the run does establish is that the two independent engines agree on the
velocity, and that the cube, the extractor and the adapters handle a real 3.4 GB
ALMA product end to end.

Velocity convention: `nu_obs = nu_rest / (1+z)`.  An earlier bug used
`nu_rest * (1+z)`, which shifted every velocity by ~2 z c = 10,500 km/s at this
redshift; the first fit returned +10,944 km/s and the fix brought it to +312.
