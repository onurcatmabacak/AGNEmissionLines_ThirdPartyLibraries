# `radio_line` — real-data test on observed HCN J=1-0

Input: `inputs/REGION5_HCN_z_0.0000/raw/region5_hcn10_spectrum.fits`, extracted with

```bash
python pipeline/extract_cube_spectrum.py \
    inputs/REGION5_HCN_z_0.0000/raw/region5_hcn_crop.fits \
    inputs/REGION5_HCN_z_0.0000/raw/region5_hcn10_spectrum.fits \
    --box 5 --unit K
```

A 1-D spectrum integrated over a 5x5-pixel box at the brightest position of the
**observed** HCN J=1-0 cube (88.6318473 GHz rest, Galactic, BUNIT K, distributed
with the pyspeckit test data): 352 channels of 114 m/s, peak 0.72 K, noise
0.105 K, peak S/N 6.9.

## Result

| component | v (km/s) | FWHM (km/s) | amplitude (K) | S/N | detected |
|---|---:|---:|---:|---:|---|
| c1 | +8.3 | 8.0 (prior cap) | 0.354 | 3.0 | no |

chi2/nu = 0.67

## Reading

Marginal: the profile reaches ~3 sigma while the peak channel pair is 6.9 sigma, and the Gaussian width runs to its prior cap.  The fit is statistically acceptable (chi2/nu < 1) but does not constitute a detection in this crop; the same tool recovers injected components exactly on synthetic data (see `Tools/radio_line/README.md`).

**No AGN claim is made from this dataset** — it is a Galactic molecular region,
used because it is real observed data at sub-mm wavelengths with a known line.
