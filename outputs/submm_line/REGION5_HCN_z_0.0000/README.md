# `submm_line` — real-data test on observed HCN J=1-0

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

| component | v (km/s) | FWHM (km/s) | T_ex (K) | tau | S/N | detected |
|---|---:|---:|---:|---:|---:|---|
| c1 | +11.8 | 9.2 | 8.2 | 0.01 | 2.9 | no |

chi2/nu = 1.30

## Reading

McFine's optical-depth model on the same spectrum gives a consistent velocity (+11.8 vs +8.3 km/s) and is optically thin (tau = 0.01).  Also marginal at this S/N.  HCN 1-0 hyperfine structure is unresolved at 114 m/s channels, so a single component is used through the `custom_line` interface.

**No AGN claim is made from this dataset** — it is a Galactic molecular region,
used because it is real observed data at sub-mm wavelengths with a known line.
