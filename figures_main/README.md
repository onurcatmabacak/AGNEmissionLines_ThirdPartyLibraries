# Main figures + the per-object configs behind them

The single most informative best-fit figure for each tool, named

```
<tool>_<filename>_<object>.<ext>
```

| tool | file |
|------|------|
| pyqsofit | `pyqsofit_result_<obj>.pdf` |
| badass | `badass_max_likelihood_fit_<obj>.pdf` |
| fantasy_agn | `fantasy_agn_my_sdss_<obj>.pdf` |
| gelato | `gelato_my_sdss-spec_<obj>.pdf` |
| gleam | `gleam_linefits.sdss.sdss.fiber1.001_<obj>.png` |

5 figures × 10 objects = 50 files.

`configs/` holds the **exact winning configuration** for each object/tool
(`<tool>_<configfilename>_<object>.<ext>`, 50 files) produced by
`pipeline/per_object_search.py`, which tunes every object on itself.

Regenerate with

```bash
python pipeline/collect_figures.py --select --out figures_main --clean
python pipeline/save_object_configs.py
```

The full set of every plot is in `../figures/`; the machine-readable winner
list is `../configs/BEST_PER_OBJECT.json`.
