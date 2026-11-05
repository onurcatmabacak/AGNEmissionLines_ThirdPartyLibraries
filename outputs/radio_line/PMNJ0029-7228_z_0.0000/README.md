# `radio_line` — H I 21-cm absorption toward PMN J0029-7228

Input: `inputs/PMNJ0029-7228_z_0.0000/raw/pmn_j0029_hi21cm.vot`, the published
ATCA 21-cm absorption spectrum (CSIRO DAP collection 44763 / product 56857359),
570 channels at 1 km/s.  Converted with:

```bash
python pipeline/votable_to_spectrum.py \
    inputs/PMNJ0029-7228_z_0.0000/raw/pmn_j0029_hi21cm.vot \
    inputs/PMNJ0029-7228_z_0.0000/raw/pmn_j0029_hi21cm_spectrum.fits \
    --flux-is opacity --rest-ghz 1.420405751 --bunit "optical depth"
```

The archive stores **normalised absorption** (1.0 = no absorption), not optical
depth: the converter takes `tau = -ln(opacity)` and
`sigma_tau = sigma_opacity / opacity`.  Getting that wrong inverts the line.

## Result

| quantity | value |
|---|---|
| velocity | **+123.07 km/s** |
| FWHM | 4.57 km/s |
| peak optical depth | 0.200 |
| integral tau dv | 0.970 km/s |
| N(H I) = 1.823e18 * integral | **1.77e18 cm^-2** |
| snr_integrated | **11.7** |
| snr_rms (per channel) | 5.3 |
| chi2/nu | 0.52 |
| detected | **yes** |

The fitted centre reproduces the published absorption peak (+123 km/s) and the
fitted tau matches the published depth (0.206) to within the noise, so this is a
detection, not a marginal one: it is the repository's first **cm-band** line fit
and the only band that previously had no real data at all.

## Why this dataset

Ready-to-fit cm spectra are scarce: radio archives normally ship visibilities
that need calibration, and the survey cubes (HIPASS, HI4PI, LAB) are 0.6-8 GB.
This CSIRO product is a *calibrated, published* 140 kB VOTable, which makes the
radio band testable without either a calibration pipeline or a multi-GB
download.  `pipeline/votable_to_spectrum.py` is generic and also handles the
ASKAP GASKAP-HI pilot spectra, which use the same conventions.
