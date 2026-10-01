# AGNEmissionLines_ThirdPartyLibraries

Fit AGN emission lines with **six independent codes** on the same spectra and
compare the results in one report. Five codes run automatically (PyQSOFit,
BADASS3, fantasy_agn, GELATO, GLEAM); SCULPTOR is prepared but GUI-only.

Input can be any FITS spectrum (classic SDSS or SDSS DR18 eFEDS); the pipeline
adapts it to each tool's native layout, fits, scores and reports.

Codes: [BADASS3](https://github.com/remingtonsexton/BADASS3) ·
[fantasy](https://github.com/yukawa1/fantasy/) ·
[PyQSOFit](https://github.com/legolason/PyQSOFit) ·
[SCULPTOR](https://github.com/jtschindler/sculptor) ·
[GELATO](https://github.com/TheSkyentist/GELATO) ·
[GLEAM](https://github.com/multiwavelength/gleam)

---

## How to use this repo

### One-time setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
sudo usermod -aG docker $USER          # then log out/in (no sudo needed after)
bash pipeline/build_images.sh          # build the badass/fantasy_agn/gelato/gleam images
```

`run_pipeline.sh` and `analyze.sh` re-exec themselves through `sg docker` if the
current shell lacks the docker group, so a fresh login is only needed for the
group to apply everywhere.

### Workflow A — automatic best fit per object (recommended)

Drop spectra into `input/` and run one command:

```bash
cp my_spectrum.fits input/
bash analyze.sh
```

`analyze.sh` tunes **each object on itself**: for every object it evaluates each
tool's whole candidate config grid, ranks the runs with a physical objective,
refines the winner by coordinate descent, applies the per-object winning config,
and writes the report. It also saves each object's winning config next to its
figure. This is what to use when you want the best result the tools can give and
do not mind it taking hours.

```bash
bash analyze.sh --dry-run                 # show the candidate grids, run nothing
bash analyze.sh --tools pyqsofit gelato   # restrict tools
bash analyze.sh --rounds 1 --pool 8       # fewer refinement rounds, more parallelism
bash analyze.sh --global                  # older whole-sample tuning (auto_tune.py)
```

### Workflow B — fast single fit pass

If you just want every tool run once with the current best-known configs:

```bash
bash run_pipeline.sh
```

It adapts each raw FITS, fits the 5 tools in parallel, collects, scores and writes
the report — typically well under an hour for ten objects.

### Getting sample data

```bash
bash run_pipeline.sh --fetch 10                       # stage 10 eFEDS spectra into input/
# or
.venv/bin/python pipeline/fetch_efeds.py --n 10 --class QSO --min-sn 8 --z-max 0.5
```

Hα (6563 Å) redshifts out of the 3600–10400 Å window above z ≈ 0.55, so select
low-z targets for optical line fitting.

### Where the results are

| path | contents |
|------|----------|
| `results/report.html` / `.md` | **cross-tool comparison report** (per object) |
| `results/scores.csv` | `chi2_red`, `chi2_common`, `line_penalty`, `has_broad/narrow` per (object, tool) |
| `results/lines.csv` | integrated line fluxes per kinematic component, per (object, tool) |
| `results/<tool>/<object>/` | every raw product collected from that tool |
| `figures_main/` | one best-fit figure per tool per object (50 for a 10-object run) |
| `figures_main/configs/` | the exact config behind each of those fits |
| `figures/` | every plot the tools produced (full component set) |
| `runs/<object>/inputs/<tool>/`, `runs/<object>/outputs/<tool>/` | adapted inputs and raw outputs |

Regenerate figures/configs after a run:

```bash
python pipeline/collect_figures.py --clean                      # figures/ (all plots)
python pipeline/collect_figures.py --select --out figures_main --clean
python pipeline/save_object_configs.py --best configs/BEST_PER_OBJECT.json
```

---

## Automatic tuning, in detail

Two drivers share the same candidate grids and objective:

| driver | scope | entry point |
|--------|-------|-------------|
| `pipeline/per_object_search.py` | **each object tuned on itself** (recommended) | `bash analyze.sh` |
| `pipeline/auto_tune.py` | one config per tool for the whole sample | `bash analyze.sh --global` |
| `pipeline/parallel_search.py` | same as `auto_tune` but one global CPU pool | `python pipeline/parallel_search.py` |

The search:
1. renders every candidate config per tool,
2. runs each on the tuning object(s) and ranks by `chi2_common + line_penalty`,
3. refines the winner by coordinate descent, and
4. re-runs the winning config and saves it.

Tuning knobs (declared in `pipeline/auto_tune.py`):

- **PyQSOFit** — error floor, Fe templates, bad-pixel rejection, broad-Gaussian multiplicity.
- **BADASS3** — `fit_stat`, broad dispersion floor, `n_basinhop`, width ties, Fe II, broad-decrement tie.
- **fantasy_agn** — broad-FWHM bounds, Fe II, `ntrial`.
- **GELATO** — `FThresh`, `LineRegion`, `TieDispersion`, `force_broad`.
- **GLEAM** — resolution, continuum window, grouping tolerance, probe width, `SN_limit`.

Fast modes are used during the search (GELATO `NBoot=0`, BADASS3
`BADASS_MAX_LIKE_NITER=0`, fantasy_agn `FANTASY_MC=0`) because errors are not
needed to rank models.

Manual variants are still available (see `configs/README.md`):

```bash
bash run_pipeline.sh --tools pyqsofit --variant pyqsofit=err05 --label pq_err05
.venv/bin/python pipeline/compare_variants.py --results results   # results/variants.html
```

---

## Flags and environment

`run_pipeline.sh` flags: `--fetch N`, `--tools "…"`, `--jobs N`,
`--variant tool=name` (repeatable), `--label NAME`, `--report-only`,
`--clean`, `--no-build`, `--no-report`.

| var | default | meaning |
|-----|---------|---------|
| `INPUT_DIR` / `RUNS_DIR` / `RESULTS_DIR` | `input` / `runs` / `results` | folders |
| `AGN_DATA_DIR` | `~/agn_data` | global dataset for `--fetch` |
| `PYTHON` | `.venv/bin/python` | interpreter for local tools + helpers |
| `DOCKER` | `docker` | set to `sudo docker` if needed |
| `JOBS` | `4` | max parallel jobs |
| `TOOLS` | `pyqsofit badass fantasy_agn gelato gleam` | tools to run |
| `TOOL_TIMEOUT` | unset | per-tool wall-clock limit (seconds) |
| `FANTASY_TIMEOUT` | `3600` | fantasy_agn safety timeout |
| `BADASS_MCMC` | `0` | `1` runs full emcee (hours/object) |
| `BADASS_NBASINHOP` | `50` | basinhopping iterations |
| `BADASS_MAX_LIKE_NITER` | `100` | MC-bootstrap iterations (`0` fastest) |
| `VARIANTS` / `RUN_LABEL` | unset | same as `--variant` / `--label` |

---

## Scoring

Two numbers are reported per (object, tool):

- **`chi2_common`** — the primary, fair metric. Every tool's total model is
  rebuilt on the *same* prepared spectrum with the *same* calibrated errors (raw
  ivar plus a fixed 2 % flux floor) and compared over the main optical line
  windows. It cannot be gamed by inflating a tool's internal error floor, and it
  is corrected for host subtraction (PyQSOFit/fantasy save `model_total` =
  AGN + host).
- **`chi2_red`** — each tool's own reported statistic (`chi2_kind` records what
  it is: per-complex, line-window, mean per-line, or global).

`line_penalty` is a physical-plausibility penalty (missing/negative [O III]5007,
missing broad Balmer, unphysical [O III] doublet ratio or broad Balmer
decrement). The search optimises `chi2_common + 150·line_penalty`.

`pipeline/score_fits.py` also extracts **integrated line fluxes** per kinematic
component (broad / narrow / outflow / total), normalised to
1e-17 erg s⁻¹ cm⁻², for Hβ, [O III] 4959/5007, Hα, [N II], [S II], [O II].
`.venv/bin/python pipeline/make_report.py` renders the per-object χ² table and
line-flux matrix.

```bash
.venv/bin/python pipeline/score_fits.py --runs runs --results results   # refresh scores/lines
bash run_pipeline.sh --report-only                                      # refresh the report
```

---

## Current status (10-object eFEDS sample)

Every tool now fits the full line set with broad+narrow components and physical
doublet ratios. `line_penalty = 0` counts (`line_penalty=0` = physically clean on
that object):

| tool | clean objects | notes |
|------|--:|-------|
| fantasy_agn | **10/10** | [O III], [N II], [S II] all modelled |
| gelato | **10/10** | broad Balmer fitted (per-object `force_broad` where the F-test rejects it) |
| badass | 9/10 | host + Fe II + [N II]/[S II] |
| pyqsofit | 8/10 | host decomposition; the 2 flags are residual line-core systematics |
| gleam | 7/10 | one Gaussian per line (+ broad duplicates); its "model" is lines + local continuum |

The remaining flags are individual-object cases (broad-Balmer decrement slightly
outside 2–6, a missing [O III]5007 in one GLEAM fit), not tool-wide failures.

---

## Input adapters and backends

`pipeline/prepare_inputs.py` reads a raw FITS (eFEDS `COADD`/`SPALL`, or the
classic SDSS layout) and writes each tool's native file:

| tool | prepared file | flux unit | wavelength | backend |
|------|---------------|-----------|------------|---------|
| PyQSOFit | `spectrum.fits` | cgs | HDU1 image; HDU2 error; header `z` | local `.venv` |
| BADASS3 | `my_sdss.fits` | cgs | `loglam` table + HDU2 `z` | Docker `badass` |
| fantasy_agn | `my_sdss.fits` | cgs | `loglam` table + HDU2 `z` | Docker `fantasy_agn` |
| GELATO | `my_sdss.fits` + `my_sdss.json` | 1e-17 | `loglam` table | Docker `gelato` |
| GLEAM | `spec1d.sdss.sdss.fiber1.1.fits` | 1e-17 | linear `wl` (TUNIT=Å); HDU2 `redshift` | Docker `gleam` |
| SCULPTOR | `spectrum.fits` | 1e-17 | `loglam` table | GUI only (not auto-run) |

Docker images bake in each tool plus a synthetic placeholder spectrum; the
per-object input is mounted over it at run time, so images are built once and
reused. Docker tools run detached (`docker run -d`), are awaited under a timeout,
then killed and removed if they hang.

---

## Limitations and notes

- **SCULPTOR** ships as a GUI; its input is prepared but it is not automated.
- **GELATO** had two long-standing bugs (a hardcoded redshift and a flux/error
  unit mismatch) that made it fit nothing; both are fixed. Where the data do not
  support GELATO's F-test for a broad Balmer component, the `force_broad` knob
  adds an explicit second Balmer species.
- **GLEAM** fits one Gaussian per line; `Gleam/line_table.fits` carries
  `Hb_broad`/`Ha_broad` duplicates so it can represent broad+narrow Hα/Hβ, and a
  runtime patch ties the [O III]/[N II] doublets, forbids negative amplitudes and
  draws the total model. Its reported χ² is a mean per-line value and its
  `chi2_common` is naturally higher (it models lines over a local continuum).
- **BADASS3** with full MCMC is hours per object; the default is a fast
  OLS/basinhopping fit (`BADASS_MCMC=0`). Set `BADASS_MCMC=1` for uncertainties.
- **fantasy_agn** can hang after writing its products; `FANTASY_TIMEOUT` bounds it
  and the run is kept once `my_sdss_model.csv` exists.
- The fits are CPU-only — none of the tools has a GPU/CUDA path.

---

## Repository layout

```
run_pipeline.sh                 # fit once with the current configs
analyze.sh                      # automatic per-object search (recommended)
input/                          # raw spectra you drop in
runs/                           # per-object adapted inputs + raw outputs
results/                        # collected products + CSVs + reports
figures/ , figures_main/        # all plots, and the 50 comparison figures + configs
configs/<tool>/<variant>/       # tuning variants (configs/README.md)
configs/BEST_PER_OBJECT.json    # per-object winning configs
pipeline/
├── prepare_inputs.py           # per-tool FITS adapters
├── run helpers: collect_results.py, score_fits.py, make_report.py
├── auto_tune.py                # whole-sample search (analyze.sh --global)
├── per_object_search.py        # per-object search (analyze.sh default)
├── parallel_search.py          # pooled whole-sample search
├── collect_figures.py          # figures/ + figures_main/
├── save_object_configs.py      # configs next to the figures
├── compare_variants.py         # results/variants.html
├── fetch_efeds.py              # download the eFEDS sample
└── build_images.sh             # build the Docker images
<tool>/                         # per-tool configs, dockerfiles, reference outputs
```

See **`pipeline/README.md`** for internals and **`configs/README.md`** for the
tuning workflow.
