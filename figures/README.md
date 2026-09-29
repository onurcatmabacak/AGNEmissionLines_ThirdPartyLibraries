# Figures

Flat copies of every plot produced by the pipeline, named

```
<tool>_<original filename>_<object>.<ext>
```

- **tool** — `pyqsofit`, `badass`, `fantasy_agn`, `gelato`, `gleam`
- **original filename** — the tool's own figure name (e.g. `result`, `spectrum`,
  `my_sdss`, `my_sdss-fit`, `linefits.sdss.sdss.fiber1.001.OIII4.OIII5`)
- **object** — the 11-digit catalog id (e.g. `04592939295`)
- **ext** — `pdf`, `png`, or `html`

Regenerate with

```bash
python pipeline/collect_figures.py --clean
```

The single best-fit figure per tool is in `../figures_main/`.
