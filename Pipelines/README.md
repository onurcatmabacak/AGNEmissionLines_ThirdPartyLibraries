# `Pipelines/`

All shell entry points for the Docker tools and the source-keyed matrix.

```text
Pipelines/
  build_images.sh              # build all Docker images under Tools/
  run_new_tools.sh             # NIR/MIR/FIR/UV/SED matrix
  run_pahfit_mc.sh             # PAHFIT MC campaign + cross-object comparison
  run_ir.sh                    # generic IR fitter (host Python)
  run_*_docker.sh              # individual tool runners
  run_gandalf_line_docker.sh   # native GANDALF v1.5 (GDL) line fit
  run_cafe_line_docker.sh      # CAFE NIRSpec/MIRI decomposition
  run_s3fit_line_docker.sh     # S3Fit spectrum+SED line fit
  run_galspec_line_docker.sh   # GalSpec reduced H-beta/[O III] line fit
  legacy_optical/              # archived optical-v1 drivers
```

Examples:

```bash
bash Pipelines/build_images.sh
bash Pipelines/run_new_tools.sh --list
bash Pipelines/run_new_tools.sh --cigale-models skirtor2016,fritz2006
bash Pipelines/run_ir.sh --fits inputs/04592649654_z_0.5874/raw/spec-00000-59345-04592649654.fits \
  --z 0.58741307 --out outputs/04592649654_z_0.5874/ir_linefit

# CAFE spectral decomposition of the PDS 456 MIRI short+long x1d spectra
bash Pipelines/build_images.sh cafe_line
bash Pipelines/run_cafe_line_docker.sh \
  inputs/PDS456_z_0.1840/raw outputs/PDS456_z_0.1840/cafe_line 0.184 \
  --max-wave 27.8 --no-outlier-clip --mc-samples 200
```

The Python implementation remains in `pipeline/`; the scientific tool code/images
are under `Tools/`; inputs/outputs are under `inputs/` and `outputs/`.

`legacy_optical/` contains the original optical drivers (`run_pipeline.sh`,
`analyze.sh`, `run.sh`) and the old `analysis/` scripts.  They are archived for
provenance; their old `input/`, `runs/`, `results/` directories were migrated
into `inputs/` and `outputs/` and are no longer present.
