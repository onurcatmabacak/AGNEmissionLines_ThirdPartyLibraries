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

Flux conventions were reverse-engineered from the reference FITS files the
original single-object analysis produced, so each tool behaves exactly as before.

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
**mounted over** a placeholder at run time, so one image serves the whole dataset:

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
- **PyQSOFit redshift.** `main.py` had `z = 0.348` hardcoded for the original
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
  (`NoneType.to_string`); `wdisp`/`stdev` are constant as in the reference file.
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
- [x] adapters for all six tools (validated against reference FITS)
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

| tool | source | kind |
|------|--------|------|
| PyQSOFit | `output.fits` `1/2_line_red_chi2` | per-complex, reported |
| BADASS3 | `best_model_components.fits` (DATA vs MODEL) | line-window, computed |
| fantasy_agn | `my_sdss_model.csv` | line-window, computed |
| GLEAM | `linefits*.fits` (fluxes/EW) + per-line `reduced chi-square` in the log | mean, reported |
| GELATO | — | n/a (its saved model/chi² are numerically degenerate) |

Because the statistic differs per tool, cross-tool χ² is a guide; the line-flux
matrix is the like-for-like comparison. Fluxes are integrated per kinematic
component (broad / narrow / outflow) and normalised to 1e-17 erg s⁻¹ cm⁻².

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

- Docker tools run **detached** with a name, then `docker wait` under a timeout;
  a hung container is killed and removed (a foreground `docker run` would linger,
  and `docker wait` needs `timeout -k` because it ignores SIGTERM).
- `FANTASY_TIMEOUT` (default 900 s) bounds fantasy_agn, which can hang after
  writing its products; if its key product exists when the timeout fires, the run
  is kept.
- Container names include the run label and PID so variant sweeps can run in
  parallel.
