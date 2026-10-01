# Main figures + the configs behind them

One best-fit figure per tool, named `<tool>_<filename>_<object>.<ext>`:

| tool | file |
|------|------|
| pyqsofit | `pyqsofit_result_<obj>.pdf` |
| badass | `badass_max_likelihood_fit_<obj>.pdf` |
| fantasy_agn | `fantasy_agn_my_sdss_<obj>.pdf` (OIIIa/OIIIb, [NII], [SII]) |
| gelato | `gelato_my_sdss-comp_<obj>.pdf` (per-line components) |
| gleam | `gleam_linefits.sdss.sdss.fiber1.001_<obj>.png` (overview, wide Hα inset with the TOTAL model) |

`configs/` holds the exact configuration behind each fit
(`<tool>_<configfilename>_<object>.<ext>`, from the per-object search).

Regenerate with

```bash
python pipeline/collect_figures.py --select --out figures_main --clean
python pipeline/save_object_configs.py --best configs/BEST_PER_OBJECT.json
```
