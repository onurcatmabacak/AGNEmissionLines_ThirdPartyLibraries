# Figures

Flat copies of every plot produced by the pipeline, named

```
<tool>_<original filename>_<object>.<ext>
```

- **tool** — `pyqsofit`, `badass`, `fantasy_agn`, `gelato`, `gleam`
- **original filename** — the tool's own figure name
- **object** — the 11-digit catalog id (e.g. `04592939295`)
- **ext** — `pdf`, `png`, or `html`

Regenerate with

```bash
python pipeline/collect_figures.py --clean
```

The single best-fit figure per tool and its config are in `../figures_main/`.
