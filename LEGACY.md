# Legacy optical v1

The original optical five-tool analysis has been migrated into the canonical
layout:

```text
outputs/<object_name>_z_<redshift>/
  pyqsofit/
  badass/
  fantasy_agn/
  gelato/
  gleam/
  .../<tool>/uncertainties/
  statistical_confirmation/
```

The archived optical drivers and analysis notes are in
`Pipelines/legacy_optical/` (`run_pipeline.sh`, `analyze.sh`, `run.sh`,
`analysis/`, `OPTICAL_README.md`).  They assume the retired `input/`, `runs/`,
`results/` trees and are not the supported entry point.

The old `input/`, `runs/`, `results/`, `results_uncertainties/`,
`runs_uncertainties/`, `figures/`, `figures_main/`, and
`statistical confirmation/` directories have been removed.
