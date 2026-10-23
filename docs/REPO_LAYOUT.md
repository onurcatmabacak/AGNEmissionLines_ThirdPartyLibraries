# Repository layout (new IR/UV/SED tools)

```text
inputs/                  canonical source store (one raw copy per source)
  catalogs/              cross-source tables
  <source>_z_<z>/        source.json + raw/ [+ photometry/]
outputs/                 canonical results
  <source>_z_<z>/<tool>/ files for one source and one tool
Pipelines/               shell entry points (new tools + archived optical)
pipeline/                Python orchestration, layout helpers, input preparation
Tools/                   Dockerized tool source and Dockerfiles
  pipeline_ir/           generic IR line router/fitter
  pyqsofit_uv/ ppxf_host/ UV/host tool images
  gandalf_line/          native GANDALF v1.5 under GDL
  cafe_line/ s3fit_line/ galspec_line/ NIR/MIR/optical spectrum+SED line tools
  nir_linefit/ pahfit_mir/ fir_linefit/ crossband/
  cigale_sed/ agnfitter_sed/
```

`work/prepared/` and `work/logs/` are generated and ignored.  The legacy
optical v1 trees (`results/`, `runs/`, `figures/`, `figures_main/`,
`results_uncertainties/`, `runs_uncertainties/`, `statistical confirmation/`)
were migrated to `outputs/` and removed from the root; aggregate legacy tables
are in `docs/legacy_optical/`.

The old path names `input_zgt05/`, `input_nir/`, `input_mir*/`, `input_fir/`,
`input_crossband/`, `input_sed/`, `results_ir/`, and `runs_ir_zgt05/` are
intentionally gone.  Use `inputs/` and `outputs/` for all new work.
