# `casa_specfit` — CASA 6 spectral-line fitting (cross-check)

CASA 6 ships as pip wheels (`casatools` ~82 MB + `casatasks` ~2 MB), so the
full NRAO tarball is not needed.  This image provides `casatasks.specfit` — the
task the ALMA/VLA community uses — as an independent cross-check of the
Gaussian decompositions from `radio_line` (pyspeckit) and `submm_line` (McFine),
and as the entry point for real ALMA/VLA data.

| | |
|---|---|
| image | `casatools`/`casatasks` 6.7.6.14 |
| input | spectral-line **image cube** (FITS), fitted in a box around the peak |
| output | `casa_specfit.csv`, `casa_spectrum.csv`, `run.json` |

```bash
bash pipeline/runners/run_casa_specfit_docker.sh <cube.fits> <outdir> --ncomp 2
```
