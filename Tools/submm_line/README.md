# `submm_line` — sub-mm spectral lines with McFine

Multi-component **hyperfine** fitting for (sub-)mm molecular lines, using
McFine's optical-depth radiative transfer (GPL-3.0, pure pip, no CASA).

| | |
|---|---|
| engine | `mcfine` 0.4 — `hyperfine_structure_lte` / `multiple_components` |
| lines | `n2hp10` (N2H+ 1-0, 93.17 GHz, 15 hyperfine components), `co21` (CO 2-1, 230.5 GHz), `hi21cm` |
| fit | lmfit over N components × (T_ex, log τ, v_centre, width) + one Jy-per-K scale |
| output | `submm_lines.csv`, `submm_model.csv`, `submm_fit.png/pdf`, `run.json` |

```bash
bash pipeline/runners/run_submm_line_docker.sh <spectrum> <outdir> \
     --line n2hp10 --ncomp 2 --z 0.0038
```

## Why hyperfine structure matters

A single Gaussian on N2H+ 1-0 is wrong: the transition is split into 15
hyperfine components spread over ~13 km/s, and the fitted width is then the
convolution of the intrinsic width with the hyperfine pattern.  McFine models
the pattern from the same optical depth, which is what makes the width physical.

## Limitations

* LTE only (McFine also offers RADEX, not wired here).
* One width shared by all hyperfine members of a component.
* The Jy-per-K scale is a nuisance parameter, not a beam filling factor.
