# Snakemake orchestration

`workflow/Snakefile` is a thin dependency layer over the existing Docker
runners.  It does not reimplement any science; each rule calls
`pipeline/run_new_tools.py --only <source> --tools <tool> --force`, which in
turn calls the tool's `pipeline/runners/run_*_docker.sh`.

## Quick checks

```bash
.venv/bin/snakemake -s workflow/Snakefile -n all
.venv/bin/snakemake -s workflow/Snakefile -n \
  --config sources=3C120_z_0.0330 tools=pyqsofit_uv,crossmission
```

Run:

```bash
# all registered source/tool pairs, four at a time
.venv/bin/snakemake -s workflow/Snakefile --cores 4 all

# one source
.venv/bin/snakemake -s workflow/Snakefile --cores 2 \
  --config sources=3C120_z_0.0330
```

Outputs are guarded by `outputs/<tool>/<source>/.snakemake_done`.  A missing
marker is a request to rerun, even when a previous product directory exists;
`--force` ensures the tool does not mix old and new files.  Science products
are never deleted by the `clean` rule — only markers are removed.

## Dependency edges

* `s3fit_line` waits for `pyqsofit_uv` because the S3Fit runner mounts the
  PyQSOFit output as its sibling SED/spectrum input.
* `crossmission` waits for `pyqsofit_uv` plus the source's X-ray tool
  (`xmm_xspec` or `rxte_xspec`).
* `crossband` waits for `pahfit_mir` and `fir_linefit` when both are registered.

Snakemake runs the science tools in Docker; it is not itself inside a
container.  The host needs Docker, the repository's `.venv`, and a completed
`bash pipeline/runners/build_images.sh`.
