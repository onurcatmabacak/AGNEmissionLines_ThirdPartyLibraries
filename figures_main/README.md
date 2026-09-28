# Main figures

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

5 figures × 10 objects = 50 files. Regenerate with

```bash
python pipeline/collect_figures.py --select --out figures_main --clean
```

The full set of every plot is in `../figures/`.
