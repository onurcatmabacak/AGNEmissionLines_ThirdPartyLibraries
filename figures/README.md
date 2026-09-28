# Figures

Flat copies of every plot produced by the pipeline, named

```
<tool>_<original filename>_<object>.<ext>
```

- **tool** — `pyqsofit`, `badass`, `fantasy_agn`, `gelato`, `gleam`
- **original filename** — the tool's own figure name (e.g. `result`, `spectrum`,
  `my_sdss`, `my_sdss-fit`, `linefits.sdss.sdss.fiber1.001.Hb`)
- **object** — the 11-digit catalog id (e.g. `04592939295`)
- **ext** — `pdf`, `png`, or `html`

So all five fits for one object can be compared by sorting on the object id.

| tool | figures |
|------|---------|
| pyqsofit | `pyqsofit_result_<obj>.pdf` |
| badass | `badass_spectrum_<obj>.pdf`, `badass_max_likelihood_fit_<obj>.pdf`, `badass_input_spectrum_<obj>.pdf`, `badass_2-onur_bestfit_<obj>.html` |
| fantasy_agn | `fantasy_agn_my_sdss_<obj>.pdf` |
| gelato | `gelato_my_sdss-fit_<obj>.pdf`, `gelato_my_sdss-comp_<obj>.pdf`, `gelato_my_sdss-spec_<obj>.pdf` |
| gleam | `gleam_linefits..._<obj>.png` (overview + one per line group) |

These are byte-identical copies of the files under `results/<tool>/<object>/`;
regenerate them with

```bash
python pipeline/collect_figures.py --clean
```
