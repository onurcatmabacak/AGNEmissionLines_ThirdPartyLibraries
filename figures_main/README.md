# Main figures + the per-object configs behind them

One best-fit figure per tool, named `<tool>_<filename>_<object>.<ext>`:

| tool | file |
|------|------|
| pyqsofit | `pyqsofit_result_<obj>.pdf` |
| badass | `badass_max_likelihood_fit_<obj>.pdf` |
| fantasy_agn | `fantasy_agn_my_sdss_<obj>.pdf` (OIIIa 4959 and OIIIb 5007 plotted) |
| gelato | `gelato_my_sdss-comp_<obj>.pdf` (per-line component decomposition) |
| gleam | `gleam_linefits.sdss.sdss.fiber1.001_<obj>.png` |

`configs/` holds the exact winning configuration for each object/tool
(`<tool>_<configfilename>_<object>.<ext>`), from `pipeline/per_object_search.py`.

Regenerate with

```bash
python pipeline/collect_figures.py --select --out figures_main --clean
python pipeline/save_object_configs.py --best configs/BEST_PER_OBJECT.json
```
