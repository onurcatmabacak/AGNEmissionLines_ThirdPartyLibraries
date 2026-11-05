# `radio_line` — NGC 1275 HCN 3-2 (AGN)

Input: `inputs/NGC1275_z_0.0176/raw/ngc1275_hcn32_spectrum.fits` (real ALMA HCN 3-2,
project 2018.1.01178.S spw25, primary-beam corrected).

```bash
bash pipeline/runners/run_radio_line_docker.sh \
    inputs/NGC1275_z_0.0176/raw/ngc1275_hcn32_spectrum.fits \
    outputs/radio_line/NGC1275_z_0.0176 --config configs/radio_line/hcn32_ngc1275 --z 0.01756  \
    --source-key NGC1275_z_0.0176 --ncomp 1
```

## This run

| v (km/s) | FWHM (km/s) | snr_integrated | snr (peak) | snr_rms | width at bound | detected |
|---:|---:|---:|---:|---:|---|---|
| 194.0 | 331.1 | 5.1 | 3.9 | 1.6 | False | True |

## Signal-to-noise (unified definitions)

`pipeline/line_snr.py` now defines these once for every tool:

* `snr_integrated` — **primary**: `|integral| / (rms * dv * sqrt(N_eff * k))`,
  where `k` is the noise correlation factor from the residual autocorrelation.
  `k` = 2.1 for this ALMA cube (channels are oversampled about 2x
  relative to the spectral resolution), so a naive `sqrt(N)` would overstate the detection by
  a factor of two.
* `snr` — peak significance from the fit covariance (`amp / amp_err`), or `n/a`
  where the tool has no such parameter-level error.
* `snr_rms` — the old per-channel `peak / rms`, kept for traceability. For a
  **resolved** line this is intrinsically small and must not be used to reject a
  detection.

`detected = snr_integrated >= snr_min` (falling back to `snr`), and always False
when the fitted width is pinned on a prior bound.

## Three-tool comparison on the same 41x41 box

| tool | v (km/s, z-frame) | FWHM (km/s) | snr_integrated | snr (peak) | snr_rms | width at bound | detected |
|---|---:|---:|---:|---:|---:|---|---|
| `radio_line` (pyspeckit) | +194 | 331 | 5.1 | 3.9 | 1.6 | no | **yes** |
| `submm_line` (McFine) | +173 | 263 | 5.2 | n/a | 1.6 | no | **yes** |
| `casa_specfit` (CASA) | +93 | 360 | 3.8 | 6.0 | n/a | no | **yes** |

After the multi-start fixes all three tools detect the same broad line and agree
on its integrated significance (3.8-5.2 sigma) and width (263-360 km/s).  Before
those fixes the two least-squares adapters returned narrow components 220 km/s
away and called it a non-detection, while CASA found the systemic line - see the
cross-check note in `outputs/casa_specfit/NGC1275_z_0.0176/`.

The per-channel `snr_rms` of 1.6 is exactly why the per-channel statistic cannot
be used as a gate: a 360 km/s line carries its flux over ~22 channels, so no
single channel is significant even though the line is.
