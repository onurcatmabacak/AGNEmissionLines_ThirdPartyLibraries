# `radio_line` — H I 21-cm absorption toward J012418-711202

Input: `inputs/J012418-711202_z_0.0000/raw/J012418-711202_spec.vot`, one of the 30
ASKAP spectra in the GASKAP-HI pilot release (CSIRO DAP collection 75305,
product 97358171).  Converted with `pipeline/votable_to_spectrum.py`
(`--flux-is opacity`, rest 1420.405751 MHz); the archive column named
`optical_depth` is really normalised absorption `exp(-tau)`.

```bash
bash pipeline/runners/run_radio_line_docker.sh \
    inputs/J012418-711202_z_0.0000/raw/J012418-711202_hi21cm.fits \
    outputs/radio_line/J012418-711202_z_0.0000 \
    --config configs/radio_line/hi21cm_gaskap --z 0 --ncomp 1
```

## Result

| quantity | value |
|---|---|
| velocity | **+168.9 km/s** |
| FWHM | 1.01 km/s (**unresolved**, ~1 channel) |
| peak optical depth | 1.447 |
| integral tau dv | 1.56 km/s |
| N(H I) = 1.823e18 * integral | **2.84e+18 cm^-2** |
| snr_integrated | **7.0** |
| snr_rms (per channel) | 6.4 |
| chi2/nu | 0.53 |
| detected | **True** |

## The degeneracy this exposes

The line is one channel wide at the 0.977 km/s channel spacing, so `tau` and the
width trade off: with a 3 km/s width the same data give tau ~ 0.74, and the fit
with the widest prior bounds settles on tau = 1.45 over
1.0 km/s.  Only the product is constrained, and it agrees with the
survey's own quoted `peak_tau = 0.488 +/- 0.209` over an effective width of a few
km/s (0.49 x 3 ~ 1.5 km/s versus 1.56 km/s here).  Quote the integral and
N(H I), not the peak optical depth.

## Why this object

The radio cm band had a single real dataset (PMN J0029-7228).  This is a second,
independent one from a different survey (ASKAP vs ATCA), which is what a "band
covered" claim needs: two instruments, two sightlines, same converter.
