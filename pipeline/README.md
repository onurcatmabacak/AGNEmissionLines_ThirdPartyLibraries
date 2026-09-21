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

## Results and limitations

`results/` holds every product copied per tool. Machine-readable products exist
for PyQSOFit (`qsopar.fits`, `output.fits`), fantasy_agn (`*_model.csv`,
`*_pars.json`), GELATO (`my_sdss-results.fits`), and BADASS3 (`fit.log` parameter
table + `spectrum.pdf`). **GLEAM currently emits only PNG plots**, so a unified
line-flux table requires either enabling GLEAM's tabular output or parsing its
plots — a pending step (see TODO).

## Status

- [x] global dataset + reproducible eFEDS fetcher
- [x] adapters for all six tools (validated against reference FITS)
- [x] single root `run_pipeline.sh` with docker auto-group + bounded parallelism
- [x] four Docker images built; all five auto-run tools verified end-to-end on one
      eFEDS object (z = 0.175)
- [ ] unified cross-tool line-flux comparison table
- [ ] SCULPTOR automation (GUI) and GLEAM tabular output
