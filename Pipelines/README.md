# `Pipelines/`

All shell entry points for the Docker tools and the source-keyed matrix.

```text
Pipelines/
  build_images.sh              # build all Docker images under Tools/
  run_new_tools.sh             # NIR/MIR/FIR/UV/SED matrix
  run_ir.sh                    # generic IR fitter (host Python)
  run_*_docker.sh              # individual tool runners
  legacy_optical/              # archived optical-v1 drivers
```

Examples:

```bash
bash Pipelines/build_images.sh
bash Pipelines/run_new_tools.sh --list
bash Pipelines/run_new_tools.sh --cigale-models skirtor2016,fritz2006
bash Pipelines/run_ir.sh --fits inputs/04592649654_z_0.5874/raw/spec-00000-59345-04592649654.fits \
  --z 0.58741307 --out outputs/04592649654_z_0.5874/ir_linefit
```

The Python implementation remains in `pipeline/`; the scientific tool code/images
are under `Tools/`; inputs/outputs are under `inputs/` and `outputs/`.

`legacy_optical/` contains the original optical drivers (`run_pipeline.sh`,
`analyze.sh`, `run.sh`) and the old `analysis/` scripts.  They are archived for
provenance; their old `input/`, `runs/`, `results/` directories were migrated
into `inputs/` and `outputs/` and are no longer present.
