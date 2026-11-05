# `submm_line` — Galactic HCN 1-0

Input: `inputs/REGION5_HCN_z_0.0000/raw/region5_hcn10_spectrum.fits` (observed HCN 1-0,
Galactic, extracted from the cube shipped with pyspeckit).

```bash
bash pipeline/runners/run_submm_line_docker.sh \
    inputs/REGION5_HCN_z_0.0000/raw/region5_hcn10_spectrum.fits \
    outputs/submm_line/REGION5_HCN_z_0.0000 --config configs/submm_line/hcn10_region5 --z 0  \
    --source-key REGION5_HCN_z_0.0000 --ncomp 1
```

## This run

| v (km/s) | FWHM (km/s) | snr_integrated | snr (peak) | snr_rms | width at bound | detected |
|---:|---:|---:|---:|---:|---|---|
| 11.8 | 9.3 | 13.6 | n/a | 2.9 | False | True |

## Signal-to-noise (unified definitions)

`pipeline/line_snr.py` now defines these once for every tool:

* `snr_integrated` — **primary**: `|integral| / (rms * dv * sqrt(N_eff * k))`,
  where `k` is the noise correlation factor from the residual autocorrelation.
  `k` = 4.2 for this Galactic spectrum (channels are oversampled about 4x
  relative to the spectral resolution), so a naive `sqrt(N)` would overstate the detection by
  a factor of two.
* `snr` — peak significance from the fit covariance (`amp / amp_err`), or `n/a`
  where the tool has no such parameter-level error.
* `snr_rms` — the old per-channel `peak / rms`, kept for traceability. For a
  **resolved** line this is intrinsically small and must not be used to reject a
  detection.

`detected = snr_integrated >= snr_min` (falling back to `snr`), and always False
when the fitted width is pinned on a prior bound.

## Three-tool comparison on the same box-averaged spectrum

| tool | v (km/s) | FWHM (km/s) | snr_integrated | snr (peak) | snr_rms | width at bound | detected |
|---|---:|---:|---:|---:|---:|---|---|
| `radio_line` (pyspeckit) | +8.3 | 8.0 | 13.0 | 17.6 | 3.0 | **yes** | no |
| `submm_line` (McFine) | +11.8 | 9.3 | 13.6 | n/a | 2.9 | no | yes |
| `casa_specfit` (CASA) | -11.9 | 1.2 | 1.3 | 2.0 | n/a | no | no |

The tools still disagree here, and the disagreement is informative: this Galactic
crop is a weak, broad-ish line on a cuberegridded to 114 m/s channels, so the
Gaussian is not pinned down.  `radio_line` runs its width to the prior cap (hence
the `width_at_bound` veto despite a high integrated S/N), CASA prefers a narrow
component at a different centre, and McFine reaches the only solution that passes
all the gates.  No AGN claim is made from this Galactic dataset; it exists to
exercise the real-cube path end to end.
