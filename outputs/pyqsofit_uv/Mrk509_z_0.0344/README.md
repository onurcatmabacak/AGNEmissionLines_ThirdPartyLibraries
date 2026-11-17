# `pyqsofit_uv` — Mrk 509, HST/STIS E140M+E230M

Input: `inputs/Mrk509_z_0.0344/raw/hst_8877_stis_mrk509_e140m-e230m_o6ap_cspec.fits`,
the HASP reduction of HST proposal 8877 (1142-3072 A, 46,616 pixels), which covers
Ly-alpha, N V, C IV, C III] and Mg II at z = 0.0344.

```bash
python pipeline/prepare_inputs.py --fits <cspec> --out /tmp/mrk509
bash pipeline/runners/run_pyqsofit_uv_docker.sh \
    /tmp/mrk509/<tag>/inputs/pyqsofit outputs/pyqsofit_uv/Mrk509_z_0.0344 \
    --config configs/pyqsofit/uv --z 0.0344 --source-key Mrk509_z_0.0344
```

## Result

| line | component | area (1e-17) | FWHM (km/s) | S/N |
|---|---|---:|---:|---:|
| MgII_br | broad | 4.2e+04 | 8216 | 1.07 |
| CIV_br | broad | 4.73e+05 | 30334 | 0.97 |
| Lya_br | broad | 3.96e+05 | 18803 | 2.04 |
| Lya_na | narrow | 3.88e+04 | 562 | 6.60 |

**Narrow Ly-alpha is detected at S/N 6.6**; the broad lines are not
well constrained by this fit route (C IV broad S/N 0.97, Mg II broad 1.07).

## What this object shows

The data are not the limitation: the S/N per pixel is **17.6 at Ly-alpha, 9.9 at
C IV and 15.6 at Mg II**.  The weak *fitted* significance of the broad lines is a
property of running PyQSOFit's SDSS-tuned model on STIS data - the same effect
appeared on PDS 456 (C IV S/N 1.77 in `outputs/pyqsofit_uv/PDS456_z_0.1840`).
So the UV band now has two real datasets, and the actionable conclusion is about
the fitter rather than the data: PyQSOFit's UV model needs per-instrument tuning
(resolution, Fe II template range and absorption rejection) before broad-line
fluxes from STIS can be quoted.

What is quotable from this product: the narrow Ly-alpha detection, and the
per-pixel S/N that any future UV fitter can be validated against.

## Rebinning was tried, and what it did not fix

`pipeline/rebin_spectrum.py` (added with this product) rebins inverse-variance
weighted, 46,065 -> 1,360 bins at 1 A, which makes the SDSS-era fitters practical
(`qsofitmore_line` had not finished after 45 minutes on the native grid).  On the
rebinned spectrum PyQSOFit gives C IV broad S/N 1.46 and Mg II 1.93 (versus 0.97
and 1.07 native) but loses the narrow Ly-alpha entirely (norm -> 0), so rebinning
changes which lines the fit finds without making the broad-line fluxes reliable.
The native-resolution run remains this product; the rebin tool is kept because it
is the difference between "does not finish" and "finishes" for these fitters, and
it is unit-tested (`tests/test_rebin_spectrum.py`).
