# `pyqsofit_uv` — PyQSOFit UV line fitting (Docker)

PyQSOFit configured for rest-frame UV lines (Mg II 2798, C III] 1908,
C IV 1549, Lyα/N V, Si IV), packaged as a Docker image.

## Build / run

```bash
bash Pipelines/build_images.sh pyqsofit_uv
.venv/bin/python pipeline/run_new_tools.py --only 04592649654_z_0.5874 --tools pyqsofit_uv --force
```

The orchestrator prepares `work/prepared/<source_key>/pyqsofit/spectrum.fits`
from the canonical raw spectrum and writes
`outputs/<source_key>/pyqsofit_uv/`.

## What changed in this pass

* **Real errors.** The old config replaced the calibrated error array with
  `0.02 * flux`, making every pixel S/N=50.  The fit now uses the real
  HDU2 error; `PYQSOFIT_ERR_FLOOR` is an opt-in floor.
* **UV is host-free by default.** The host decomposition shrank the rest-frame
  grid to ≳3450 Å and silently skipped Mg II/C III] at z≈0.59.  The UV fit is
  now host-free; pPXF handles the host independently.  `PYQSOFIT_HOST=1`
  restores the old decomposition.
* **Line table.** `pyqsofit_lines.csv` records broad and narrow areas,
  FWHM and S/N for Mg II, C III], C IV, Lyα, Hβ and [O III].  The narrow
  C III]/Mg II areas are the directly comparable quantities; the broad
  complexes are not narrow-line measurements.
* **Mg II at z≈0.59** is now fitted instead of skipped.

A five-sample MC demonstration is stored under
`outputs/04592649654_z_0.5874/pyqsofit_uv/mc/`; the default matrix run is
maximum-likelihood.

## Controls

```bash
PYQSOFIT_MC=1 PYQSOFIT_NSAMP=50 ...      # Monte-Carlo errors
PYQSOFIT_MCMC=1 PYQSOFIT_NSAMP=200 ...  # emcee posterior (slow)
PYQSOFIT_ERR_FLOOR=0.01 ...             # optional error floor
PYQSOFIT_HOST=1 ...                     # old host-decomposed run
```

## Remaining limitations

* C III] broad flux includes UV Fe II/outflow; after adding satellites and
tightening the broad-width prior, total/ZLINE is 1.29–1.76.  The narrow
component is severely blend/width limited and is reported only as a diagnostic.
* No MCMC in the default matrix run; it is available through the environment
  variables above.
* The UV fit and pPXF host fit are separate by design; their apertures are the
  same SDSS fibre.
