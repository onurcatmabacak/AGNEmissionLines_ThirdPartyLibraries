# AGN emission-line pipeline

One command takes raw spectra, adapts each to the FITS layout every tool wants,
runs all the tools in parallel, and collects the results for comparison.

```bash
bash run_pipeline.sh                  # process everything in input/
bash run_pipeline.sh --fetch 10       # download 10 eFEDS spectra first
```

## Layout (tidy by construction)

```
input/                              raw .fits you drop in
runs/<object>/                      e.g. runs/04592939295
    inputs/<tool>/...               spectrum adapted to that tool
    outputs/<tool>/...              that tool's raw products
    manifest.json                   object id, redshift, RA/Dec, paths
results/<tool>/<object>/...         collected, ready to compare
results/index.csv                   one row per (object, tool)
results/summary.json
```

`runs/` and `results/` are gitignored; `input/` only tracks `.gitkeep`.

## Dataset

Test data is the **SDSS DR18 eFEDS** sample (eROSITA eFEDS AGN from SDSS-V/SPIDERS),
kept in a global folder so tools and containers can reach it directly:

```
$AGN_DATA_DIR (default ~/agn_data)
├── catalogs/efeds/spAll-v6_0_4-eFEDS.fits
└── efeds/spec-00000-<MJD>-<CATALOGID:011d>.fits
```

Fetch a reproducible subset (low-z by default so Hβ/[O iii] and Hα/[N ii]/[S ii]
stay inside the 3600–10400 Å window):

```bash
.venv/bin/python pipeline/fetch_efeds.py --n 10 --class QSO --min-sn 8 --z-max 0.5
```

## Input format matrix (`pipeline/prepare_inputs.py`)

Flux conventions were reverse-engineered from the FITS layout each tool expects
(matching its reference/example products), so each tool behaves as intended.

| tool | prepared file | flux unit | wavelength | notes |
|------|---------------|-----------|------------|-------|
| SCULPTOR | `spectrum.fits` | 1e-17 cgs | `loglam` table | header `Z`; GUI-only, not auto-run |
| PyQSOFit | `spectrum.fits` | cgs | HDU1 image | HDU0=flux, HDU1=λ, header `z` |
| BADASS3 | `my_sdss.fits` | cgs | `loglam` table | `flux/loglam/ivar/wdisp` + HDU2 `z` |
| fantasy_agn | `my_sdss.fits` | cgs | `loglam` table | same as BADASS3 |
| GELATO | `my_sdss.fits` + `my_sdss.json` | cgs | `loglam` table | object redshift injected into JSON |
| GLEAM | `spec1d.sdss.sdss.fiber1.1.fits` | 1e-17 cgs | linear `wl` (TUNIT=Å) | HDU2 `redshift`; constant `stdev`/`wdisp`; static `line_table.fits`, `Sky_bands.fits`, `gleamconfig.yaml`, `meta.dat` staged beside it |

Raw input may be the eFEDS `lite`/`full` layout (`COADD` HDU, redshift in `SPALL`)
or a classic SDSS `spPlate`-style FITS — the reader sniffs both.

## Execution backends

| tool | backend | notes |
|------|---------|-------|
| PyQSOFit | local `.venv` | needs `pyqsofit/PyQSOFit` (re-clone if missing); runs against `src/` |
| SCULPTOR | — | GUI only; skipped automatically |
| BADASS3 | Docker | `badass` image |
| fantasy_agn | Docker | `fantasy_agn` image |
| GELATO | Docker | `gelato` image |
| GLEAM | Docker | `gleam` image |

Images are built once (bake in code + deps); the prepared per-object input is
**mounted over a synthetic placeholder** at run time, so one image serves the
whole dataset and **no real/proprietary data is shipped in the images**:

```bash
bash pipeline/build_images.sh            # builds any missing images
```

If your shell lacks the `docker` group, `run_pipeline.sh` re-execs itself through
`sg docker` automatically — you never need `sudo`.

## Configuration (env vars)

| var | default | meaning |
|-----|---------|---------|
| `INPUT_DIR` | `input` | raw spectra |
| `RUNS_DIR` | `runs` | per-object inputs/outputs |
| `RESULTS_DIR` | `results` | collected outputs |
| `AGN_DATA_DIR` | `~/agn_data` | global dataset |
| `PYTHON` | `.venv/bin/python` | interpreter for local tools + helpers |
| `TOOLS` | `pyqsofit badass fantasy_agn gelato gleam` | which tools to run |
| `JOBS` | `4` | max parallel jobs |
| `TOOL_TIMEOUT` | (unset) | per-tool wall-clock limit, seconds |
| `BUILD` / `CLEAN` | `1` / `0` | build missing images / wipe `runs` |
| `BADASS_MCMC` | `0` | `1` restores the full emcee uncertainty run |
| `BADASS_NBASINHOP` | `5` | BADASS basinhopping threshold |
| `BADASS_MAX_LIKE_NITER` | `100` | BADASS MC-bootstrap iterations (`0` = fastest; also avoids an object-specific `scale<0` crash) |

## Tool-specific notes (why it works)

- **Docker image builds.** `badass` (Debian bullseye, EOL) is pointed at
  `archive.debian.org`; `fantasy_agn` uses `python:3.9` + `fantasy_agn==0.7.3`
  (the pinned pandas 1.3.4 / matplotlib 3.4.3 only ship cp39 wheels) and patches
  the `SherpaFloat` import moved by sherpa ≥ 4.16.
- **PyQSOFit redshift.** `main.py` had a redshift hardcoded for its original
  target; it now takes the per-object redshift from the FITS header
  (`PYQSOFIT_Z` overrides). The venv must keep `numpy==1.26.4` / `scipy==1.15.1`
  (PyQSOFit 2.1.6 is not numpy-2 clean) — matching `requirements.txt`.
- **PyQSOFit import path.** The repo's `pyqsofit/` folder shadows the installed
  package; the runner sets `PYTHONPATH=pyqsofit/PyQSOFit/src` and runs from a
  clean cwd.
- **BADASS runtime.** Full MCMC (`nwalkers=1000`, `max_iter=2500`) takes hours per
  object. The pipeline defaults to OLS/basinhopping (`BADASS_MCMC=0`); the options
  are env-overridable in `badass/main.py` without changing its defaults.
- **GLEAM units.** The `wl`/`flux` columns must carry TUNIT or GLEAM crashes
  (`NoneType.to_string`); `wdisp`/`stdev` are constant, matching GLEAM's reference
  file layout.
- **GLEAM tabular output.** GLEAM already builds a per-line results table; the
  image's `gleam.sh` moves `linefits*.fits` (flux, FWHM, EWrest, detected, …) into
  the mounted `/app/output`, and `score_fits.py` reads it for the line-flux matrix
  (FWHM is converted from Angstrom to km/s).

## Results and limitations

`results/` holds every product copied per tool. Machine-readable products exist
for PyQSOFit (`qsopar.fits`, `output.fits`), fantasy_agn (`*_model.csv`,
`*_pars.json`), GELATO (`my_sdss-results.fits`), BADASS3
(`best_model_components.fits` + `fit.log`), and GLEAM (`linefits*.fits`), so the
scorer builds a unified line-flux table from all of them.

## Status

- [x] global dataset + reproducible eFEDS fetcher
- [x] adapters for all six tools (validated against each tool's expected FITS layout)
- [x] single root `run_pipeline.sh` with docker auto-group + bounded parallelism
- [x] four Docker images built; all five auto-run tools verified end-to-end
- [x] unified cross-tool line-flux comparison table (`score_fits.py`)
- [x] GLEAM tabular output (`linefits*.fits`) used by the scorer
- [x] 10-object eFEDS run + report (50 tool runs)
- [ ] SCULPTOR automation (GUI)

## Supertool: one command, five tools, one report

`bash run_pipeline.sh` now runs the whole chain automatically:

```
input/*.fits
   └─ adapt (prepare_inputs.py)
        └─ fit with 5 tools (parallel, Docker + local)
             └─ collect_results.py   → results/<tool>/<object>/ + index.csv
                  └─ score_fits.py    → results/scores.csv + results/lines.csv
                       └─ make_report.py → results/report.html + results/report.md
```

The report has, per input object: a reduced-χ² table for every tool (with the
kind of statistic), a line-by-line flux matrix across tools, and links to every
tool's products. `bash run_pipeline.sh --report-only` regenerates the report from
existing runs without refitting.

### Reduced χ² (the ranking metric)

Two numbers are reported per tool. `chi2_red` is the tool's own statistic;
`chi2_common` is a **fair, tool-agnostic** reduced χ² computed by
`score_fits.py`: it rebuilds each tool's total model on the *same* prepared
spectrum and the *same* calibrated errors (the raw ivar combined in quadrature
with a fixed 2 % flux floor), so it cannot be gamed by a tool inflating its
internal error floor. `chi2_common` is the primary tuning objective; `chi2_red`
is kept for reference.

| tool | own `chi2_red` source | kind |
|------|--------|------|
| PyQSOFit | `output.fits` `1/2_line_red_chi2` | per-complex, reported |
| BADASS3 | `best_model_components.fits` (DATA vs MODEL) | line-window, computed |
| fantasy_agn | `my_sdss_model.csv` | line-window, computed |
| GLEAM | `linefits*.fits` (fluxes/EW) + per-line `reduced chi-square` in the log | mean, reported |
| GELATO | `PARAMS` `rChi2` | global, reported |

The common model reconstruction needs a total-model grid: PyQSOFit now writes
`pyqsofit_model.csv`, BADASS3/fantasy_agn/GELATO save theirs, and GLEAM's total
model is rebuilt from its per-line Gaussians. Fluxes are integrated per kinematic
component (broad / narrow / outflow) and normalised to 1e-17 erg s⁻¹ cm⁻².

### Automatic tuning (iterative search)

`pipeline/auto_tune.py` (wrapper: `bash analyze.sh`) turns the pipeline into a
self-optimising fitter:

```
input/*.fits
   └─ prepare
        └─ stage 1: run every candidate config on a few tuning objects
             └─ rank by mean chi2_common
                  └─ stage 2: coordinate descent around the winner
                       └─ final run with the winner on all objects + report
```

```bash
cp new_spectrum.fits input/
bash analyze.sh                     # full automatic run
bash analyze.sh --dry-run           # print the candidate grid
bash analyze.sh --tools gelato --limit 1 --rounds 1   # a focused search
```

Per-tool knobs currently searched: PyQSOFit error floor / Fe templates /
bad-pixel rejection; BADASS3 `fit_stat` / broad dispersion floor / `n_basinhop` /
width ties; fantasy_agn broad-FWHM bounds / Fe II / `ntrial`; GELATO `FThresh` /
`LineRegion` / `TieDispersion`; GLEAM resolution / continuum width / tolerance /
probe width / `SN_limit`. Generated variants are written under
`configs/<tool>/auto_<tool>_<key>/` and the winner is recorded in
`work/auto_tune/best_configs.json`.

> **Runtime.** The search runs each tool many times, so it uses fast modes:
> GELATO `NBoot=0`, BADASS3 `BADASS_MAX_LIKE_NITER=0`, and fantasy_agn
> `FANTASY_MC=0` (the model CSV is written before its Monte-Carlo block).

### Parallel search (CPU)

`auto_tune.py` evaluates one tool at a time, so the slowest tool's *serial*
candidate chain sets the wall-clock while cores freed by faster tools sit idle.
`pipeline/parallel_search.py` flattens every tool's candidate grid into one
global pool sized to the machine, refines all tools' winners in parallel rounds,
then does the final combined run:

```bash
python pipeline/parallel_search.py                       # all tools, pool = nproc
python pipeline/parallel_search.py --pool 8 --limit 3 --rounds 1
python pipeline/parallel_search.py --tools gelato gleam --limit 1 --rounds 0 --stage1-only
```

Each pool task calls `run_pipeline.sh ... --jobs 1`, so the pool (not the nested
run) owns total concurrency.  On the 8-core test host, GELATO+GLEAM on one object
went from ~28 min (serial candidates) to ~10 min with `--pool 8`.

> **GPU note.** There is no GPU execution path.  The hardware has an NVIDIA
> GTX 960M, but none of the five fitters (PyQSOFit, BADASS3, fantasy_agn,
> GELATO, GLEAM) use CUDA/cupy/torch/jax — they are NumPy/SciPy/lmfit/emcee/
> sherpa CPU codes fitting ~4600-pixel 1-D spectra, where GPU transfer overhead
> would dominate.  Docker also has no NVIDIA runtime here.  The speedup comes
> from CPU scheduling, not the GPU.

### Known fixes that made the tools comparable

- **GELATO** used to fit *every* object at a hardcoded `z=0.3482135`
  (`Gelato/gelato.sh`), and its prepared FITS had a cgs flux with an ivar
  calibrated for 1e-17 units, so its errors were ~1e16× too large and it fit
  nothing. `gelato.sh` now reads the per-object redshift from HDU2, and
  `prepare_inputs.py` writes GELATO's flux in 1e-17 units.
- **PyQSOFit** now dumps `pyqsofit_model.csv` (total/continuum/line model) for the
  common score.
- **fantasy_agn** `FANTASY_MC=0` skips the Monte-Carlo block for fast sweeps.
- **GLEAM** fits one Gaussian per line in a group, so the shipped
  `Gleam/line_table.fits` now carries `Hb_broad`/`Ha_broad` duplicates next to
  `Hb`/`Ha`. GLEAM then fits two Gaussians at H-alpha/H-beta and can represent a
  broad+narrow profile; `score_fits.py` labels these as the broad/narrow
  components and includes GLEAM's per-line continuum when rebuilding its model.

## Tuning grid

Per-tool config variants live in `configs/<tool>/<variant>/` (see
`configs/README.md`). Run them side by side and rank by χ²:

```bash
bash run_pipeline.sh --tools pyqsofit --variant pyqsofit=err05 --label pq_err05
bash run_pipeline.sh --tools pyqsofit --variant pyqsofit=err02 --label pq_err02
.venv/bin/python pipeline/compare_variants.py --results results
# -> results/variants.html / variants.md
```

Demonstrated on object `04592939295`: raising PyQSOFit's error floor from 2 % to
5 % cut the reduced χ² from **5.07 to 0.85**.

### Robustness notes

- `run_pipeline.sh --no-report` skips the HTML/MD step during sweeps.
- Docker tools run **detached** with a name, then `docker wait` under a timeout;
  a hung container is killed and removed (a foreground `docker run` would linger,
  and `docker wait` needs `timeout -k` because it ignores SIGTERM).
- `FANTASY_TIMEOUT` (default 900 s) bounds fantasy_agn, which can hang after
  writing its products; if its key product exists when the timeout fires, the run
  is kept.
- Container names include the run label and PID so variant sweeps can run in
  parallel.
