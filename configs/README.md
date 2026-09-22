# Config variants (tuning grid)

Each subdirectory holds one tunable artifact for a tool. `run_pipeline.sh` picks
it up when you pass `--variant <tool>=<name>` (or set `VARIANTS="tool=name,..."`):

| tool | file it replaces | what to change |
|------|------------------|----------------|
| `pyqsofit` | `main.py` | error floor, line priors, continuum windows |
| `badass` | `main.py` | fit options, component options, line bounds |
| `fantasy_agn` | `main.py` | fitting window, amplitude/FWHM/velocity bounds, model |
| `gelato` | `my_sdss.json` | FThresh, line regions, flags, ties |
| `gleam` | `gleamconfig.yaml` | resolution, SN_limit, tolerance, cont_width |

A variant only has to differ in the one block you are exploring; copy the current
file and edit it.

## Included examples

| variant | change | purpose |
|---------|--------|---------|
| `pyqsofit/err02` | error = 2 % of flux | baseline (matches the default) |
| `pyqsofit/err05` | error = 5 % of flux | documented fix for over-tight errors |
| `badass/nbasin20` | `BADASS_NBASINHOP` default 20 | more basinhopping, better minimum |
| `fantasy_agn/broadwin` | `min_fwhm_br = 400` | let broad lines go narrower |
| `gelato/fthresh80` | `FThresh = 0.80` | accept extra components more readily |
| `gleam/res6`, `gleam/res10` | SDSS resolution 6 / 10 Å | instrument-profile sensitivity |

## Running a sweep

```bash
# one labelled run per variant (results/<label>/, runs/<label>/)
for v in err02 err05; do
  bash run_pipeline.sh --tools pyqsofit --variant pyqsofit=$v --label pq_$v
done

# rank them by reduced chi-square
.venv/bin/python pipeline/compare_variants.py --results results
# -> results/variants.html  /  results/variants.md
```

`compare_variants.py` merges every `results/*/scores.csv` plus the default
`results/scores.csv` and highlights the lowest-chi-square variant per row.
