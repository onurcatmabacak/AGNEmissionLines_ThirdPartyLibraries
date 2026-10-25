# Contributing

## Adding a new source

1. Create `inputs/<source>_z_<z>/source.json` and `raw/`.
2. Add the file roles under `files` (see `inputs/README.md`).
3. Add only the tools that are scientifically appropriate.
4. Run `python pipeline/plan_analysis.py --source <key>` and check the plan.
5. Run one tool at a time; never start with the full matrix.
6. Add the output catalogue entry by running
   `python pipeline/build_output_manifest.py`.
7. Run `pytest -q` and `python pipeline/validate_outputs.py`.

## Adding a tool

1. Put the Dockerfile and runner under `Tools/<tool>/`.
2. Add a `Pipelines/run_<tool>_docker.sh` entry point.
3. Register the tool in `pipeline/tool_registry.py`.
4. Add it to `Pipelines/build_images.sh`, `pipeline/run_new_tools.py` and
   `pipeline/plan_analysis.py`.
5. Add a config under `configs/<tool>/`.
6. Document the scientific model and a **caveat** in
   `configs/caveats.yaml`; regenerate `docs/CAVEAT_MATRIX.md`.
7. Add a golden/regression test only after validating on real data.

## Scientific claims

Do not describe a conditional result as production-grade.  If a fit is
tentative, provisional or systematics-limited, say so in the output
`README.md`, in `run.json`, and in the caveat matrix.
