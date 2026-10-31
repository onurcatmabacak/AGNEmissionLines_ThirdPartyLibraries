# `radio_line` — radio / sub-mm spectral-line fitting (pyspeckit)

Fits N Gaussian components plus a polynomial baseline to a radio or sub-mm
spectrum and writes the repository-standard line table, so radio fluxes can be
compared with the optical ones in `docs/line_tool_comparison.csv`.

| | |
|---|---|
| engine | `pyspeckit` 1.0.4 (BSD-3) for the model + least squares |
| companions | `spectral-cube`, `radio-beam`, `astroquery` (Splatalogue line ID) |
| input | 1-D FITS spectrum (FREQ/VELO header honoured) or ASCII `x y [err]` |
| output | `radio_lines.csv`, `radio_model.csv`, `radio_fit.png/pdf`, `run.json` |

```bash
bash pipeline/runners/run_radio_line_docker.sh \
    inputs/<key>/radio/hi_spectrum.fits outputs/radio_line/<key> \
    --z 0.00379 --ncomp 2 --absorption
```

Config (`configs/radio_line/default/config.json`) sets the default component
count, baseline order, absorption flag and the line rest frequency.

## Limitations

* Single spectrum per invocation: a cube must be extracted to a spectrum first.
* Gaussian components only — hyperfine structure is not modelled (that is what
  `submm_line`/McFine is for).
* Velocities use the configured rest frequency and redshift.
