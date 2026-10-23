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

The matrix runner writes only to:

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
| VV114 / PDS 456 | `pahfit_mir`, `cafe_line` (PDS), `ir_linefit` |
| NGC 1068 / NGC 253 / NGC 4151 | `pahfit_mir`, `fir_linefit`, `ir_linefit`; cross-band for NGC 253/4151 |
| Mrk 231 | `pahfit_mir`, `ir_linefit`, `crossband` |
| synthetic FIR / multiband | `fir_linefit` + `ir_linefit` / `crossband` |

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
* `docs/line_tool_comparison.png` — cross-tool line-ratio comparison.
* `docs/line_ratio_scatter.csv` — inter-tool scatter and bootstrap intervals.

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
