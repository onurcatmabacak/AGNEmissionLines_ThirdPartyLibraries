# AGN emission-line + SED factory

A reproducible, Dockerised analysis of AGN spectra and photometry.  The repo is
organized around a source registry and a fixed output contract.

## Layout

```text
Tools/                  Dockerised tool source + Dockerfiles
Pipelines/              shell entry points (new tools; archived optical driver)
pipeline/               Python orchestration, layout, preparation and statistics
inputs/                 canonical source store
  catalogs/             cross-source tables
  <source>_z_<z>/       source.json + raw/ [+ photometry/]
outputs/                canonical results
  <source>_z_<z>/<tool>/files
docs/                   plan, caveat matrix, layout, statistics
work/                   ignored generated inputs/logs
```

`Tools/` contains: `badass`, `fantasy_agn`, `Gelato`, `Gleam`, `pyqsofit`,
`sculptor`, `pipeline_ir`, `pyqsofit_uv`, `pyqsofitspec_line`, `ppxf_host`,
`gandalf_line`, `cafe_line`, `s3fit_line`, `galspec_line`, `qgfit`,
`sheap_line`, `nir_linefit`, `pahfit_mir`, `fir_linefit`, `crossband`,
`cigale_sed`, `agnfitter_sed`.

CIGALE and AGNfitter are **SED/torus** codes; they do not measure individual
lines.  Use `pyqsofit_uv`, `pyqsofitspec_line`, `cafe_line`, `s3fit_line`,
`gandalf_line`, `galspec_line`, `qgfit`, `sheap_line`, `pahfit_mir`,
`nir_linefit` or `ir_linefit` for line fluxes and kinematics.

## Quick start

```bash
bash Pipelines/build_images.sh
bash Pipelines/run_new_tools.sh --list
bash Pipelines/run_new_tools.sh --cigale-models skirtor2016,fritz2006
```

All **20 Docker images** build successfully (`Pipelines/build_images.sh`).  The matrix runner writes only to:

```text
outputs/<source_name>_z_<redshift>/<tool_name>/...
```

Inputs are never copied into outputs; PyQSOFit/pPXF-native files are generated
under `work/prepared/`.

## Source-keyed matrix

| source group | tools |
|---|---|
| SDSS z>0.5 QSOs (5) | `ir_linefit`, `pyqsofit_uv`, `pyqsofitspec_line`, `ppxf_host`, `gandalf_line`, `s3fit_line`, `galspec_line`, `qgfit`, `sheap_line`, `cigale_sed`, `agnfitter_sed` |
| J0100+2802 | `nir_linefit` (pipeline, 3×3, PSF), `ir_linefit` |
| VV114 / PDS 456 | `pahfit_mir`, `cafe_line`, `ir_linefit` |
| Low-z SDSS GANDALF example | `gandalf_line` (Hα/Hβ coverage) |
| NGC 1068 / NGC 253 / NGC 4151 | `pahfit_mir`, `fir_linefit`, `ir_linefit`; cross-band for NGC 253/4151 |
| Mrk 231 | `pahfit_mir`, `ir_linefit`, `crossband` |
| synthetic FIR / multiband | `fir_linefit` + `ir_linefit` / `crossband` |

## Production-quality test run

The production matrix uses real data only:

| tool | suitable object | production mode | result |
|---|---|---|---|
| **CAFE** | VV114, full 12 MIRI `s1d` channels | AGN/SB continuum + selected MIR lines/PAHs, 200 covariance draws | rms **0.143**, χ²ν 2.68; Ar II, Ne II, Ne III, S IV, etc. detected |
| **S3Fit** | `04592649654` SDSS QSO | **spec+sed**, 8 bands, 10 mock spectra, 8 threads | χ²ν **1.035**; MC χ² 1.605±0.112; Hβ/[O III] **1.83**; 58 min |
| **GANDALF** | `spSpec-51908-0277-120` z=0.0859 | native GDL, pPXF + all Hα/Hβ/[O III]/[N II] lines | pPXF **accepted** (V=72.5, σ=79.9 km/s); Hα 1391, Hβ 244, [O III] 79.7 |
| **PAHFIT** | VV114, PDS 456, NGC 4151, NGC 253 | full MIRI/IRS, covariance/bootstrap, 100–200 draws | rms VV114 **0.195** (flagged hot-dust mismatch), PDS short/long/both **0.0088/0.017/0.038**, NGC 4151 **0.031**, NGC 253 **0.25**; all PAHFIT production runs are `flagged=true` / systematics-limited |
| **GalSpec** | `04592649654` | full-continuum global model + `emcee`, 39 parameters | 224,000 samples, 37,334 saved; Hβ 3718, [O III] 1681, ratio **2.21** |
| **PyQSOFitSpec** | `04592649654` | full Fe II/Balmer + skew-normal lines, 55 bootstrap draws | 53 valid; Hβ **3525**, [O III] **1639**, ratio **2.15** |
| **QGfit** | `04592649654` | long continuum MCMC + line complexes | 2334 s; Hβ/[O III] **2.50**; line errors LSQ |
| **SHEAP** | `04592649654` | Hβ/[O III] SPAF/JAX, 50 bootstrap draws | Hβ/[O III] **2.02**, χ²ν 2.9 |
| **PyQSOFit** | `04592649654` | 100-realization MC (`mc/`); short `emcee` MCMC (800 draws, not converged) + 300-step diagnostics | MCMC initialization fixed; acceptance ≈0.37; short-chain samples/corner/trace saved, but MC remains the quantitative product |
| **SDSS ZLINE** | five SDSS QSOs | official `ZLINE` HDU | 045926 ratio **1.57** |

The cross-tool 04592649654 Hβ/[O III] 5007 values are:

```text
ZLINE 1.57 | S3Fit 1.83 | PyQSOFit 1.96 | GalSpec 2.21
GANDALF 2.07 | PyQSOFitSpec 2.15 | SHEAP 2.02 | QGfit 2.50
median 2.05, log-scatter 0.13 dex
```

## Failure audit and fixes

| failure | fix / outcome |
|---|---|
| CAFE PDS 456 had only four MRS L sub-bands and one detected line | added a 12-file MIRI `s1d` adapter; VV114 now has full 5–28 µm coverage and multiple MIR detections. The PDS gap remains documented. |
| S3Fit was pure-spectrum with only 3 mocks | full **spec+sed** run with **10 mocks**, 8 threads; χ²ν 1.035. |
| GANDALF had no Hα coverage and pPXF was rejected | added a real low-z SDSS spectrum; pPXF accepted; Hα/Hβ/[O III]/[N II] measured. |
| PAHFIT Jy/MJy conversion was wrong by **1e12**; MIRI s1d units were hard-coded; `pahfit_args` were dropped | corrected units, dynamic `TUNIT`/aperture handling, appended args; PDS long/both **0.017/0.038**, NGC 253 **0.25**. All production runs remain flagged/systematics-limited (VV114 hot dust, NGC 253 gaps, NGC 4151 residuals). |
| GalSpec only fit a reduced Hβ/[O III] window | full-continuum 39-parameter `emcee` model; 37,334 saved samples. |
| PyQSOFitSpec only 10 bootstraps and pinned widths | 55-draw bootstrap; width anchors and tied components documented. Hβ remains ~18% above GANDALF/S3Fit because of continuum/model definition. |
| QGfit used a very short continuum MCMC | 2334 s production run with long continuum MCMC and expanded [O III] template; line errors remain LSQ. |
| SHEAP failed at χ² 46 and Hβ/[O III]=4.00 | model/region/profile repair; now **2.02**, χ²ν 2.9, 50-draw MC. |
| PyQSOFit line-stage `emcee` condition-number failure | fixed by bounds-aware walker initialization; short MCMC samples/corner/trace saved (800 draws, not converged), plus 300-step diagnostics (acceptance ≈0.37). Full 300-step chains were lost at the container timeout; the 100-realization MC remains quantitative. |
| Official SDSS DAPs, AMARU, ELFO, AGNdecompose, pyspeckit | excluded with explicit data/model reasons; see `docs/OFFICIAL_PIPELINES_AND_XRAY.md`. |

## Statistics and caveats

* `docs/statistical_tests_new_tools.csv` — UV/ZLINE, SED-family, FIR recovery,
  cross-band and PAHFIT stability tests.
* `docs/statistical_analysis_new_tools.png` / `.pdf` — six-panel comparison.
* `docs/sed_family_comparison.csv` — CIGALE SKIRTOR/Fritz vs AGNfitter-rx.
* `docs/pyqsofit_zline_comparison.csv` — broad/narrow UV line table.
* `docs/CAVEAT_FIXES.md` — what was fixed and what remains.
* `docs/LINE_FITTING_TOOLS.md` — line-fitting tools vs SED fitting.
* `docs/MCMC_AND_STATISTICS.md` — MC, nested sampling and covariance modes.
* `docs/OFFICIAL_PIPELINES_AND_XRAY.md` — official SDSS DAP/HEASOFT exclusions and integration plan.
* `docs/line_tool_comparison.png` — official ZLINE + eight independent fitters.
* `docs/line_ratio_scatter.csv` — inter-tool scatter and bootstrap intervals.
* `docs/SHEAP_ASSESSMENT.md` — SHEAP repair and quality gates.
* `docs/GANDALF_ASSESSMENT.md` — low-z GDL/pPXF validation.

## Legacy optical v1

The original optical five-tool driver is archived in
`Pipelines/legacy_optical/`; its production results were migrated to
`outputs/<object>_z_<z>/{pyqsofit,badass,fantasy_agn,gelato,gleam}/`, with
uncertainty products under `<tool>/uncertainties/`.  The old `input/`, `runs/`,
`results/`, `figures*/`, `results_uncertainties/` and `statistical
confirmation/` directories are gone.

## Key docs

`docs/REPO_LAYOUT.md`, `docs/OUTPUTS.md`, `docs/STATISTICS.md`,
`docs/CAVEAT_FIXES.md`, `docs/IR_EXTENSION_PLAN.md`.
