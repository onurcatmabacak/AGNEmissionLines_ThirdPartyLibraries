# `pahfit_mir` — PDS 456, JWST/MIRI MRS, with the systematics flags on

Input: the two PI-reduced MIRI MRS `x1d` spectra of PDS 456 (programme 2547,
obs `jw02547001001`): `mirifushort` (4.9-11.7 um) and `mirifulong`
(15.4-28.7 um), at z = 0.184.

```bash
bash pipeline/runners/run_pahfit_mir_docker.sh <input-dir> outputs/pahfit_mir/PDS456_z_0.1840 \
    0.184 --segment short --error-floor 0.1 --gap-trim-um 0.3
```

## The systematics flags do what they were added for

Same spectrum, three runs (short segment, 1,360 -> 4,000 points after binning):

| run | chi2_red | rms_rel | quality flags |
|---|---:|---:|---|
| default | **35.9** | 0.0194 | `formal_chi2_mismatch`, `many_parameters_at_bound`, `coverage_gap` |
| `--error-floor 0.1` | **0.064** | 0.0196 | `many_parameters_at_bound`, `coverage_gap` |
| `--error-floor 0.1 --gap-trim-um 0.3` | **0.037** | 0.0166 | `coverage_gap` |

This is the PDS 456 "error-scale mismatch" item in one table: the formal MIRI
errors are ~0.2 % of the flux, so chi-square is meaningless until they are floored
at a realistic systematic level - the floor takes chi2_red from 35.9 to 0.064 and
removes the `formal_chi2_mismatch` flag.  Gap trimming then removes the
`many_parameters_at_bound` flag and lowers the residual by 15 %.

## Features in the fitted band (floor + trim run)

| feature | quantity | value |
|---|---|---:|
| starlight (5.92 um) | flux density | 2.12e5 MJy/sr |
| PAH 5.3 | integrated line power | 6.50e5 MJy/sr THz |
| PAH 7.7c | integrated line power | 1.66e6 MJy/sr THz |
| silicate | tau_sil | 0.0327 |

Only four features lie inside the short-segment coverage; everything else carries
`coverage_gap`, which is the correct outcome rather than a failure.

## What remains data-limited

The **long segment alone fails** with `PAHFITPackError` and produces no fit
(chi2_red, rms_rel both NaN).  That band has zero-filled channels exactly where
[Ne III] 15.6 um and [S III] 18.7 um would sit at this redshift, so there is no
masked-out gap that trimming can recover - it needs deeper or differently
processed MRS data, not a configuration change.  Fitting both segments together
fails the same way, which is why the production run above is the short segment.
