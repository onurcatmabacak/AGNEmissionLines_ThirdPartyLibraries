# Repository layout (new IR/UV/SED tools)

```text
inputs/                  canonical source store (one raw copy per source)
  catalogs/              cross-source tables
  <source>_z_<z>/        source.json + raw/ [+ photometry/]
outputs/                 canonical results
  <source>_z_<z>/<tool>/ files for one source and one tool
pipeline/                orchestration, layout helpers, input preparation
pipeline_ir/             generic IR line router/fitter
pyqsofit_uv/ ppxf_host/  UV/host tool images
nir_linefit/ pahfit_mir/ NIR/MIR tool images
fir_linefit/ crossband/  FIR/ratio tool images
cigale_sed/              SED/torus image and configuration
```

`work/prepared/` and `work/logs/` are generated and ignored.  The legacy
optical v1 trees (`results/`, `runs/`, `figures/`, `figures_main/`,
`results_uncertainties/`, `runs_uncertainties/`, `statistical confirmation/`)
are retained for the original five-tool analysis and are not written by the new
runner.

The old path names `input_zgt05/`, `input_nir/`, `input_mir*/`, `input_fir/`,
`input_crossband/`, `input_sed/`, `results_ir/`, and `runs_ir_zgt05/` are
intentionally gone.  Use `inputs/` and `outputs/` for all new work.
