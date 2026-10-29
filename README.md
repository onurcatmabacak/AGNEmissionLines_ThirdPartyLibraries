# AGN emission-line + SED factory

A source-keyed, Dockerised framework for fitting **AGN emission lines and SEDs**
across UV, optical, NIR, MIR, FIR and X-ray data.  It is designed for
reproducible research, not for silently producing one "best" answer.

> **New here? Read [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) first.**
> It includes a 2-minute no-Docker tour and a 10-minute first fit.

## Start here

```bash
git clone https://github.com/onurcatmabacak/AGNEmissionLines_ThirdPartyLibraries.git
cd AGNEmissionLines_ThirdPartyLibraries

uv venv .venv
source .venv/bin/activate
uv pip install -r requirements-host.txt -r requirements-dev.txt

# No Docker needed: inspect the same-object 3C 120 result and ask the planner
python pipeline/plan_analysis.py --source 3C120_z_0.0330
python pipeline/compare_xray_optical.py --source 3C120_z_0.0330
```

For a first actual fit:

```bash
bash pipeline/runners/build_images.sh optical_linefit
python pipeline/run_new_tools.py --only PDS456_z_0.1840 --tools optical_linefit --force
```

For a complete first optical example:

```bash
bash pipeline/runners/build_images.sh pyqsofit_uv
python pipeline/run_new_tools.py --only 3C120_z_0.0330 --tools pyqsofit_uv --force
```

Do **not** start with `snakemake all`; some tools take tens of minutes.

## What this repository is

- **A tool matrix:** 26 Docker images for line/SED/host/IFU/X-ray analyses.
- **A canonical data layout:** one source directory in, one tool directory out.
- **A source-aware planner:** recommends tools from the data actually present.
- **A validation system:** output schema, SHA-256 artifact catalogue, pytest
  regression tests, per-tool caveats.
- **A scientific audit trail:** raw data, provenance, fit tables, figures and
  explicit limitations.

It is **not** a survey pipeline, an automatic AGN finder, or a claim that every
fit is publication-final.  Read `docs/CAVEAT_MATRIX.md` before using a number.

## Choose your path

| Goal / data | Recommended first tool |
|---|---|
| optical/UV AGN spectrum | `pyqsofit_uv`, `qsofitmore_line`, `optical_linefit` |
| broad Hβ + [O III] with a local model | `optical_linefit` |
| X-ray Fe Kα | `xmm_xspec` or `rxte_xspec` |
| NIR/MIR lines and PAHs | `cafe_line`, `pahfit_mir`, `nir_linefit` |
| FIR lines | `fir_linefit` |
| photometry / torus SED | `cigale_sed`, `agnfitter_sed` |
| MaNGA IFU | `manga_dap` |
| same-object X-ray + optical | `crossmission` (two-object case study) |

The planner encodes this logic:

```bash
python pipeline/plan_analysis.py --source <source_key> --goal auto
python pipeline/plan_analysis.py --source <source_key> --goal lines
python pipeline/run_new_tools.py --source <source_key> --auto
```

`--goal auto` excludes long tools unless `--include-expensive` is supplied.

## Repository contract

```text
inputs/<source_key>/source.json     # source metadata, file roles, chosen tools
inputs/<source_key>/raw/            # one canonical raw copy
outputs/<tool>/<source_key>/        # all products for that tool
pipeline/                           # Python orchestration + validators
pipeline/runners/                   # bash wrappers around each Docker image
work/prepared/                      # generated tool-native inputs (ignored)
work/logs/                          # run logs (ignored)
```

Every output is an artifact collection: `run.json`, CSV/FITS tables, figures and
a README.  The machine-readable catalogue is `outputs/output_catalog.json`; its
schema is `schemas/output_catalog.schema.json`.  See
[`docs/OUTPUT_SCHEMA.md`](docs/OUTPUT_SCHEMA.md).

## Reproducible execution

```bash
# validate the committed products
python -m pytest -q
python pipeline/validate_outputs.py

# dry-run a dependency graph
snakemake -s workflow/Snakefile -n \
  --config sources=3C120_z_0.0330 tools=pyqsofit_uv,crossmission

# execute it
snakemake -s workflow/Snakefile --cores 2 \
  --config sources=3C120_z_0.0330 tools=pyqsofit_uv,crossmission
```

The Snakemake graph calls the same Docker runners as `run_new_tools.py`; it is
a dependency layer, not a second implementation.

## What has actually been validated

- **MaNGA DAP subset vs published MAPS:** BPT agreement **9/9**, Hα ratio
  **0.99985** (9 central bins; not all spaxels).
- **XMM PDS 456:** Fe Kα Δχ² **16.39 (4.05σ)**, rest EW **25.9 eV**.
- **RXTE 3C 120:** Fe Kα Δχ² **17.83 (4.22σ)**, rest EW **90.3 eV**; conservative fixed-N_H variant **3.46σ**.
- **Nine SDSS line fitters:** median Hβ/[O III] **2.04**, scatter **0.053 dex**.
- **Independent 3C 120 optical fits:** PyQSOFit **1.55**, QSOFITMORE **3.00** —
  a model-systematic spread, not a confirmed line ratio.
- **PDS 456 Hβ:** local X-SHOOTER fit gives **5.99**, but χ²_red is **430**
  and the continuum/absorption model is incomplete; quality is **provisional**.
  Do not quote 5.99 as a measurement.
- **Same-object X-ray/optical:** **N=2**, no correlation fitted; both objects are now **provisional** (X-ray detection/model consistency gate).  See
  [`docs/SCIENCE_RESULTS.md`](docs/SCIENCE_RESULTS.md).

These are honest results, including the disagreements.  The full statistical
report is regenerated by:

```bash
python pipeline/statistical_report.py
```

## Documentation map

| document | purpose |
|---|---|
| [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) | beginner tutorial |
| [`docs/SCHEDULING.md`](docs/SCHEDULING.md) | multicore / parallel scheduling |
| [`docs/LONG_RUNS.md`](docs/LONG_RUNS.md) | full-capability, long-run recipes |
| [`docs/SCIENCE_RESULTS.md`](docs/SCIENCE_RESULTS.md) | statistical results and caveats |
| [`docs/CAVEAT_MATRIX.md`](docs/CAVEAT_MATRIX.md) | status/severity/evidence for every tool |
| [`docs/OUTPUT_SCHEMA.md`](docs/OUTPUT_SCHEMA.md) | formal output contract |
| [`docs/LINE_FITTING_TOOLS.md`](docs/LINE_FITTING_TOOLS.md) | line fitters vs SED fitters |
| [`docs/MCMC_AND_STATISTICS.md`](docs/MCMC_AND_STATISTICS.md) | MC/MCMC/covariance modes |
| [`docs/OFFICIAL_PIPELINES_AND_XRAY.md`](docs/OFFICIAL_PIPELINES_AND_XRAY.md) | XMM/RXTE/SDSS provenance |
| [`docs/ROADMAP_V2.md`](docs/ROADMAP_V2.md) | implementation history and open items |
| [`docs/PINNING.md`](docs/PINNING.md) | image/upstream provenance |
| [`docs/LITERATURE_COVERAGE.md`](docs/LITERATURE_COVERAGE.md) | what is covered and what is genuinely missing |
| [`docs/XMM_RAW_SAS_RESULT.md`](docs/XMM_RAW_SAS_RESULT.md) | raw SAS PN cross-check of the PPS X-ray result |
| [`docs/UNRESOLVED_ITEMS.md`](docs/UNRESOLVED_ITEMS.md) | remaining blockers with evidence and owners |
| [`docs/RUN_MANIFEST.md`](docs/RUN_MANIFEST.md) | normalized run/catalog status |
| [`workflow/README.md`](workflow/README.md) | Snakemake graph |

## Environment and tests

- Host dependencies: `requirements-host.txt`
- QA tools: `requirements-dev.txt`
- Docker images: `pipeline/runners/build_images.sh` (26 tools)
- Tests: 27 pytest tests plus schema/hash validation

```bash
pytest -q
python pipeline/validate_outputs.py
python pipeline/build_output_manifest.py
```

## Contributing

Read `CONTRIBUTING.md` before adding a source or a tool.  Scientific claims must
carry their caveat and a reproducible output path.

## Citation and licence

See `CITATION.cff` and `LICENSE`.  Third-party codes retain their own licences;
HST/ESO archive data have their licences recorded in the source READMEs.

## Status

The framework is suitable for research use and method comparison.  It is not
yet a turnkey community product: several tools have conditional/systematic
caveats, the X-ray/optical comparison is a two-object case study, and raw SAS /
PCA reductions are not part of the production path.  Known limitations are
tracked in `docs/CAVEAT_MATRIX.md`, not hidden in this README.
