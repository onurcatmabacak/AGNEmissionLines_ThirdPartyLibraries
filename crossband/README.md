# crossband — cross-band emission-line ratio comparer (Docker)

The P4 comparison tool: takes line measurements from different bands and
computes physically meaningful ratios with uncertainties, expected ranges and
a consistency flag.

## Ratios

| ratio | bands | expected range | diagnostics |
|---|---|---|---|
| Paα/Hα | NIR/optical | 0.04–0.25 | case-B extinction |
| Brγ/Hα | NIR/optical | 0.005–0.10 | case-B extinction |
| [OIII] 88/[OIII] 5007 | FIR/optical | 0.1–2.0 | PDR/AGN |
| [NeIII]/[NeII] | MIR | 0.1–5.0 | ionization |
| [SIII] 18.7/33.5 | MIR/FIR | 0.5–5.0 | density/PDR |

## Build / run

```bash
bash pipeline/build_images.sh crossband
bash run_crossband_docker.sh input_crossband/synthetic_multiband.csv \
     results_ir/crossband_synth
```

Input CSV: `object,line,band,flux,flux_err`. Output:
`crossband_ratios.csv`, `crossband_summary.json`, `crossband_ratios.png/pdf`.

## Validation (synthetic multi-band object)

`synthetic_multiband` with known lines gives:

| ratio | value | error | expected | consistent |
|---|---:|---:|---|---|
| Paα/Hα | 0.12 | 0.005 | 0.04–0.25 | yes |
| Brγ/Hα | 0.03 | 0.003 | 0.005–0.10 | yes |
| [OIII] 88/5007 | 0.50 | 0.052 | 0.1–2.0 | yes |
| [NeIII]/[NeII] | 2.00 | 0.256 | 0.1–5.0 | yes |
| [SIII] 18.7/33.5 | 2.00 | 0.361 | 0.5–5.0 | yes |

5/5 consistent. **Inspect:** `results_ir/crossband_synth/crossband_ratios.png`.

## Caveats

- Synthetic validation: the current sample has no single object with real
  NIR+MIR+FIR+optical spectra; real same-object ratios are the next data goal.
- Expected ranges are broad priors, not precise model predictions.
- Ratios are only meaningful when the lines come from comparable apertures and
  the same physical region.
