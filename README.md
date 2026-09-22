# AGNEmissionLines_ThirdPartyLibraries

Fit AGN emission lines with **six independent codes** on the same spectra, then
compare their results in one report.

Originally written to confirm the results of the `EmissionLineAnalysis` repo on
the AGN spectrum of **IeRASS J053448.4+212608**; it now runs a whole dataset end
to end.

Codes used:

- https://github.com/remingtonsexton/BADASS3
- https://github.com/yukawa1/fantasy/
- https://github.com/legolason/PyQSOFit
- https://github.com/jtschindler/sculptor
- https://github.com/TheSkyentist/GELATO
- https://github.com/multiwavelength/gleam

---

## Quick start

```bash
# 1. put raw spectra in input/  (or fetch a starter sample)
cp ~/agn_data/efeds/*.fits input/      # or:  bash run_pipeline.sh --fetch 10

# 2. one command fits, scores and reports
bash run_pipeline.sh
```

That single command:

1. adapts each raw FITS to every tool's native layout,
2. fits with **5 tools in parallel** (Docker + local venv),
3. collects the products, scores each fit, and
4. writes a cross-tool comparison report.

If your shell is not in the `docker` group, `run_pipeline.sh` re-execs itself via
`sg docker` — **no `sudo` needed**.

Outputs:

| path | contents |
|------|----------|
| `runs/<object>/inputs/<tool>/` | spectrum adapted for that tool |
| `runs/<object>/outputs/<tool>/` | that tool's raw products |
| `results/<tool>/<object>/` | collected, per-tool products |
| `results/index.csv` | one row per (object, tool) |
| `results/scores.csv` | reduced χ² per (object, tool) |
| `results/lines.csv` | integrated line fluxes per kinematic component |
| `results/report.html` / `.md` | **cross-tool comparison report** |
| `results/variants.html` / `.md` | tuning-variant ranking (after a sweep) |

One-time setup: install Docker, add yourself to the `docker` group, and build the
images (`bash pipeline/build_images.sh`); `run_pipeline.sh` handles the rest.

---

## Dataset — SDSS DR18 eFEDS

The test sample is the **SDSS DR18 eFEDS** AGN (eROSITA eFEDS selected,
observed by SDSS-V/SPIDERS): ~16 500 spectra, homogeneous 3600–10400 Å coverage,
with a catalog (`spAll-v6_0_4-eFEDS.fits`) giving redshift, class, S/N,
coordinates, MJD and fiber so subsets are reproducible.

It lives in a **global folder** every tool/container can reach:

```
$AGN_DATA_DIR (default ~/agn_data)
├── catalogs/efeds/spAll-v6_0_4-eFEDS.fits
└── efeds/spec-00000-<MJD>-<CATALOGID:011d>.fits
```

Fetch a reproducible subset (low-z by default, so Hβ/[O III] and Hα/[N II]/[S II]
stay inside the observed window):

```bash
.venv/bin/python pipeline/fetch_efeds.py --n 10 --class QSO --min-sn 8 --z-max 0.5
```

> Hα (6563 Å) redshifts out of coverage above z ≈ 0.55, so **select lower-z
> targets** for optical emission-line fitting. The raw eFEDS SAS directory does
> *not* ship PyQSOFit results; the baseline is your own PyQSOFit run.

---

## Input-format adapters

The tools disagree about how a spectrum is stored. `pipeline/prepare_inputs.py`
reads the raw eFEDS (`COADD` HDU, redshift in `SPALL`) or classic SDSS layout and
writes each tool's expected file. Flux conventions were reverse-engineered from
the reference FITS the original single-object analysis produced.

| tool | prepared file | flux unit | wavelength | notes |
|------|---------------|-----------|------------|-------|
| SCULPTOR | `spectrum.fits` | 1e-17 cgs | `loglam` table | header `Z`; GUI-only, not auto-run |
| PyQSOFit | `spectrum.fits` | cgs | HDU1 image | HDU0=flux, HDU1=λ, header `z` |
| BADASS3 | `my_sdss.fits` | cgs | `loglam` table | `flux/loglam/ivar/wdisp` + HDU2 `z` |
| fantasy_agn | `my_sdss.fits` | cgs | `loglam` table | same as BADASS3 |
| GELATO | `my_sdss.fits` + `my_sdss.json` | cgs | `loglam` table | object redshift injected into the JSON |
| GLEAM | `spec1d.sdss.sdss.fiber1.1.fits` | 1e-17 cgs | linear `wl` (TUNIT=Å) | HDU2 `redshift`; constant `stdev`/`wdisp`; static `line_table.fits`, `Sky_bands.fits`, `gleamconfig.yaml`, `meta.dat` staged beside it |

---

## Execution backends

| tool | backend |
|------|---------|
| PyQSOFit | local `.venv` (`pyqsofit/PyQSOFit/src`), per-object redshift from the header |
| SCULPTOR | GUI only — not automated (skipped) |
| BADASS3 | Docker image `badass` |
| fantasy_agn | Docker image `fantasy_agn` |
| GELATO | Docker image `gelato` |
| GLEAM | Docker image `gleam` |

Docker images bake in each tool's code + dependencies plus a placeholder spectrum;
the prepared per-object input is **mounted over** the placeholder at run time, so
an image is built once and reused across the whole dataset. Docker tools run
**detached** (`docker run -d --name …`) and are awaited under a timeout, then
killed and removed if they hang.

### Build fixes baked into the image definitions

- **BADASS3** — Debian bullseye is EOL, so apt is repointed to `archive.debian.org`.
- **fantasy_agn** — uses `python:3.9` + `fantasy_agn==0.7.3` (its pinned
  pandas 1.3.4 / matplotlib 3.4.3 only ship cp39 wheels) and patches the
  `SherpaFloat` import that sherpa ≥ 4.16 moved.
- **PyQSOFit** — its `main.py` had `z = 0.348` hardcoded for the original target;
  it now reads the per-object redshift from the FITS header (`PYQSOFIT_Z`
  overrides). The venv must keep `numpy==1.26.4` / `scipy==1.15.1` (PyQSOFit
  2.1.6 is not numpy-2 clean), and it is imported from `pyqsofit/PyQSOFit/src`
  because the repo's `pyqsofit/` folder shadows the installed package.
- **GLEAM** — the `wl`/`flux` columns must carry FITS `TUNIT` or GLEAM crashes
  (`NoneType.to_string`); `wdisp`/`stdev` are constant, as in the reference file.

Rebuild any missing image with `bash pipeline/build_images.sh [tool ...]`.

---

## Configuration

Flags for `run_pipeline.sh`:

| flag | meaning |
|------|---------|
| `--fetch N` | download N eFEDS spectra into the global folder and stage them |
| `--tools "…"` | subset of tools to run |
| `--jobs N` | max parallel jobs |
| `--variant tool=name` | use `configs/<tool>/<name>/` (repeatable) |
| `--label NAME` | namespace `runs/<NAME>` and `results/<NAME>` |
| `--report-only` | skip fitting; re-score + re-report from existing runs |
| `--clean` | wipe `runs/` first |
| `--no-build` | do not build missing images |

Environment variables:

| var | default | meaning |
|-----|---------|---------|
| `INPUT_DIR` / `RUNS_DIR` / `RESULTS_DIR` | `input` / `runs` / `results` | folders |
| `AGN_DATA_DIR` | `~/agn_data` | global dataset |
| `PYTHON` | `.venv/bin/python` | interpreter for local tools + helpers |
| `DOCKER` | `docker` | set to `sudo docker` if needed |
| `JOBS` | `4` | max parallel jobs |
| `TOOLS` | `pyqsofit badass fantasy_agn gelato gleam` | tools to run |
| `TOOL_TIMEOUT` | unset | per-tool wall-clock limit, seconds |
| `FANTASY_TIMEOUT` | `1800` | fantasy_agn safety timeout (it can hang at the end) |
| `BADASS_MCMC` / `BADASS_NBASINHOP` | `0` / `5` | BADASS speed vs thoroughness |
| `BADASS_MAX_LIKE_NITER` | `100` | BADASS MC-bootstrap iterations (`0` = fastest, avoids an object-specific `scale<0` bug) |
| `VARIANTS` / `RUN_LABEL` | unset | same as `--variant` / `--label` |

---

## Scoring and comparison report

"Best = lowest reduced χ²" is the primary metric. Because each code reports a
different statistic over a different region, `chi2_kind` records what was measured:

| tool | source | kind |
|------|--------|------|
| PyQSOFit | `output.fits` `1/2_line_red_chi2` | per-complex, reported |
| BADASS3 | `best_model_components.fits` (DATA vs MODEL) | line-window, computed |
| fantasy_agn | `my_sdss_model.csv` | line-window, computed |
| GLEAM | `linefits*.fits` (line fluxes/EW) + `docker.log` (χ²) | mean per-line reported |
| GELATO | — | **n/a** (its saved model/`rChi2` are numerically degenerate) |

`pipeline/score_fits.py` also extracts **integrated line fluxes** per kinematic
component (broad / narrow / outflow / total) for the main optical lines, normalised
to 1e-17 erg s⁻¹ cm⁻². `pipeline/make_report.py` renders `results/report.html`
(and `.md`): per object a χ² table, a line-flux matrix across tools, and links to
every tool's products.

```bash
.venv/bin/python pipeline/score_fits.py --runs runs --results results   # refresh scores/lines
.venv/bin/python pipeline/make_report.py --runs runs --results results  # refresh report
# or simply:  bash run_pipeline.sh --report-only
```

> Cross-tool χ² is a guide (the statistics differ); the **line-flux matrix** is
> the like-for-like comparison.

### Example: 10-object eFEDS run

`bash run_pipeline.sh` on ten low-z eFEDS QSOs produced 50 tool runs
(all 10 objects × 5 tools) and 438 line measurements. Reduced χ² per object
(GELATO reports none):

| object | pyqsofit | badass | fantasy_agn | gleam | lowest |
|---|---:|---:|---:|---:|---|
| 04545183216 | 2.80 | **2.08** | 10.96 | 31.58 | badass |
| 04570362657 | 4.98 | 8.19 | 22.71 | **4.06** | gleam |
| 04570493016 | **4.59** | 23.53 | 203.60 | 19.20 | pyqsofit |
| 04592503068 | 17.92 | 39.69 | 64.30 | **14.85** | gleam |
| 04592517882 | 8.17 | 6.87 | 9.51 | **2.17** | gleam |
| 04592660180 | **4.35** | 11.28 | 29.90 | 4.60 | pyqsofit |
| 04592939295 | **5.07** | 10.16 | 48.59 | 8.97 | pyqsofit |
| 04592975881 | **4.41** | 24.72 | 51.72 | 10.50 | pyqsofit |
| 04592979214 | **9.67** | 98.04 | 196.31 | 21.08 | pyqsofit |
| 06872228427 | 13.25 | 17.58 | 87.14 | **2.96** | gleam |

Different tools win on different objects — exactly why the pipeline compares
them rather than trusting one code.

---

## Tuning the free parameters

Per-tool config variants live in `configs/<tool>/<variant>/` (see
`configs/README.md`). Copy a tool's config, change one block, and run it side by
side:

```bash
bash run_pipeline.sh --tools pyqsofit --variant pyqsofit=err05 --label pq_err05
bash run_pipeline.sh --tools pyqsofit --variant pyqsofit=err02 --label pq_err02
.venv/bin/python pipeline/compare_variants.py --results results
# -> results/variants.html / variants.md (lowest χ² per row highlighted)
```

**Demonstrated** on object `04592939295`: raising PyQSOFit's error floor from 2 %
to 5 % cut the reduced χ² from **5.07 to 0.85**.

Included example variants:

| variant | change | purpose |
|---------|--------|---------|
| `pyqsofit/err02` | error = 2 % of flux | baseline |
| `pyqsofit/err05` | error = 5 % of flux | documented fix for over-tight errors |
| `badass/nbasin20` | `n_basinhop` default 20 | more basinhopping |
| `fantasy_agn/broadwin` | `min_fwhm_br = 400` | let broad lines go narrower |
| `gelato/fthresh80` | `FThresh = 0.80` | accept extra components more readily |
| `gleam/res6`, `gleam/res10` | SDSS resolution 6 / 10 Å | instrument-profile sensitivity |

### Which knobs matter most (highest → lowest leverage)

- **PyQSOFit** (`pyqsofit/main.py`): error floor; `line_priors` ties — same
  `vindex` (velocity), `windex` (width), `findex`/`fvalue` (ratio) for the
  [O III] 4959/5007 and [N II] 6549/6585 doublets; `conti_windows`.
- **BADASS3** (`badass/main.py`): `fit_stat`, `reweighting`, `mask_bad_pix`,
  `mask_emline`, `max_like_niter` (MC-bootstrap iterations; `0` is fastest and
  avoids an object-specific `scale<0` crash), `comp_options` (Fe II, host, Balmer,
  ties), and the `narrow_options`/`broad_options` `disp_plim`/`voff_plim`/`line_profile`.
- **fantasy_agn** (`fantasy_agn/main.py`): `s.crop(...)` window, amplitude/FWHM/
  offset bounds, and the model composition (tied/narrow/broad/Fe II components).
- **GELATO** (`Gelato/my_sdss.json`): `FThresh`, `LineRegion`, per-species
  `Flag`/`FlagGroups` and `RelStrength`, `TieDispersion`.
- **GLEAM** (`Gleam/gleamconfig.yaml`): `resolution`, `SN_limit`, `tolerance`,
  `cont_width`, and the line subset.

---

## Limitations and notes

- **SCULPTOR** ships as a GUI; it is prepared (`inputs/sculptor/spectrum.fits`)
  but not automated.
- **GELATO** exposes no usable χ² in this setup (its `SUMMARY` model and `rChi2`
  are numerically degenerate); only its line fluxes enter the comparison.
- **GLEAM** writes a per-line results table (`linefits*.fits` with flux, FWHM, EWrest,
  χ²-adjacent diagnostics) that the scorer reads, plus plot PNGs; its reduced χ² is
  parsed from the per-line LMFIT blocks in the log.
- **BADASS3** with full MCMC is hours per object; the pipeline defaults to a fast
  OLS/basinhopping fit (`BADASS_MCMC=0`). Set `BADASS_MCMC=1` for uncertainties.
- **fantasy_agn** can hang after writing its products; `FANTASY_TIMEOUT` bounds it
  and the run is kept only if its key product (`my_sdss_model.csv`) exists.

---

## Repository layout

```
run_pipeline.sh                 # the ONE entry point
input/                          # raw spectra you drop in (git-tracked except .fits)
runs/                           # per-object adapted inputs + raw outputs (gitignored)
results/                        # collected products + CSVs + reports (gitignored)
configs/<tool>/<variant>/       # tuning variants (+ configs/README.md)
pipeline/
├── fetch_efeds.py              # download the dataset
├── prepare_inputs.py           # per-tool FITS adapters
├── collect_results.py          # gather products + index.csv/summary.json
├── score_fits.py               # reduced χ² + line fluxes per tool
├── make_report.py              # results/report.html / .md
├── compare_variants.py         # results/variants.html / .md
├── build_images.sh             # build the Docker images
└── README.md                   # full pipeline documentation
<tool>/                         # per-tool configs, dockerfiles, reference outputs
```

See **`pipeline/README.md`** for the full detail, and **`configs/README.md`**
for the tuning workflow.
