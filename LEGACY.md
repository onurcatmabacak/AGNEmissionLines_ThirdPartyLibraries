# Legacy optical v1 trees

These directories belong to the original five-tool optical analysis and are
intentionally not part of the new source-keyed layout:

```text
input/                 original optical drop directory
runs/                  old per-object optical runs
results/               old optical results
results_uncertainties/ old uncertainty campaign summaries
runs_uncertainties/    raw uncertainty runs (ignored)
figures/ figures_main/ old figure collections
statistical confirmation/
configs/*/auto_*       old auto-tuning artifacts (ignored)
```

They are retained for reproducibility of the original analysis.  All new
NIR/MIR/FIR/UV/SED work uses `inputs/` and
`outputs/<source>_z_<redshift>/<tool>/`; do not add new results to the legacy
trees.  See `docs/REPO_LAYOUT.md`.
