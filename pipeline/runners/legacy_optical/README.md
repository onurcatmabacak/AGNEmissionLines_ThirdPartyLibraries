# Legacy optical v1 drivers (archived)

`run_pipeline.sh`, `analyze.sh`, `run.sh` and `analysis/` are the original
optical five-tool implementation.  The old `input/`, `runs/`, `results/`,
`results_uncertainties/`, `figures/`, `figures_main/` and
`statistical confirmation/` trees were migrated/deleted in the v2 layout.

Production optical results now live at:

```text
outputs/<object_name>_z_<redshift>/<tool>/
```

Tools: `pyqsofit`, `badass`, `fantasy_agn`, `gelato`, `gleam`; uncertainty
products are under `<tool>/uncertainties/`.

These scripts are retained only so the original workflow is auditable; they
assume the retired directory layout and are not the supported entry point.
