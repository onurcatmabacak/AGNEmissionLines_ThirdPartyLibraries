# `agnfitter_sed` — AGNfitter-rx SED engine (Docker)

The independent second SED engine: the public **AGNfitter 2.0
(AGNfitter-rx release)** from `GabrielaCR/AGNfitter`, fitted to the same
8-band SDSS+WISE photometry as CIGALE.

## Build / run

```bash
bash Pipelines/build_images.sh agnfitter_sed
.venv/bin/python pipeline/run_new_tools.py --only 04592649654_z_0.5874 \
  --tools agnfitter_sed --force
```

The runner builds a per-source AGNfitter catalogue and settings file, invokes
`RUN_AGNfitter_multi.py -i -n 0`, and writes:

```text
outputs/<source>_z_<z>/agnfitter_sed/
  agnfitter_summary.csv       # median / 16th / 84th percentiles
  sed_summary.json            # engine, bands, redshift, key parameters
  catalog.txt
  SETTINGS_AGNfitter.py
  OUTPUT/<id>/
    parameter_outvalues_<id>.txt
    posteriors_<id>.txt
    SED_manyrealizations_<id>.pdf
```

The 180 MB per-source model dictionary and the 15 MB realization dump are
removed after parsing; they are regenerable.

## Model

- BBB: THB21; torus: SKIRTOR_1P; galaxy: BC03_metal; starburst: S17.
- X-ray/radio disabled (no X-ray/radio photometry in this sample).
- Ultranest with 80 live points, 80 minimum ESS.
- Runtime ~5 minutes per source on one core.

## Caveats

- AGNfitter's model dictionary is built per source; this dominates the runtime
  and the peak disk usage.
- The public repo is an older codebase; the image applies compatibility fixes
  for Python 3.11 / NumPy / pandas / Matplotlib / Astropy.
- PROSPECTOR-AGN is not integrated.
- The fit is photometry-only; no X-ray/radio constraints.
