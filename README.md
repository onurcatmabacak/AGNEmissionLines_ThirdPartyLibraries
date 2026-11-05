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

- **A tool matrix:** 32 Docker images for line/SED/host/IFU/X-ray/cube analyses.
- **A canonical data layout:** one source directory in, one tool directory out.
- **A source-aware planner:** recommends tools from the data actually present.
- **A validation system:** output schema, SHA-256 artifact catalogue, pytest
  regression tests, per-tool caveats.
- **A results record:** every product's headline numbers in
  [`docs/RESULTS.md`](docs/RESULTS.md), with provenance and explicit limitations.
- **No shipped data.** `inputs/` keeps only the `source.json` manifests (URLs and
  product names) and `outputs/` only the per-product READMEs: cloning this
  repository no longer pulls ~2.4 GB of third-party observations.

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
| soft X-ray grating lines (OVII/OVIII) | `xmm_rgs` |
| H I 21-cm absorption / cm-band lines | `radio_line` |
| mm/sub-mm molecular or hyperfine lines | `submm_line`, `casa_specfit` |
| spatially resolved line maps from a cube | `cube_lines` |
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

## Results

This is a results-first repository: the code is the means, the numbers are the
product.  Clone size is kept small on purpose - the observations and the output
trees are **not** shipped - so the record lives in documents rather than in
gigabytes:

| category | what it contains |
|---|---|
| [`docs/RESULTS.md`](docs/RESULTS.md) | one row per committed product: source, tool, variant and the headline numbers (velocity, FWHM, S/N, chi2/nu, E_cut, alpha_ox, ...), generated by `pipeline/build_results_summary.py` |
| [`docs/SCIENCE_RESULTS.md`](docs/SCIENCE_RESULTS.md) | the statistical results, including where independent tools disagree |
| [`docs/CAVEAT_MATRIX.md`](docs/CAVEAT_MATRIX.md) | status, severity and evidence for every tool - what may and may not be claimed |
| `outputs/<tool>/<SOURCE>/README.md` | the per-product narrative that belongs next to the numbers (kept; only the bulk artefacts are gone) |
| `inputs/<SOURCE>/source.json` | provenance for every dataset: instrument, obsID, product name and download URL |

Representative results, one per band:

| band | result |
|---|---|
| radio cm | ATCA H I 21-cm absorption: v **+123.07 km/s**, tau **0.200**, N(H I) **1.77e18 cm-2**, S/N **11.7** |
| sub-mm/mm | NGC 1275 HCN 3-2: **5.1 sigma** (pyspeckit), **5.2 sigma** (McFine), **3.8 sigma** (CASA) - three engines, one line |
| resolved cube | ALMA moment maps: v **+232 km/s**, FWHM **156 km/s**, S/N **13.0** |
| MIR | PAHFIT / CAFE PAH and fine-structure decomposition on Spitzer IRS and JWST MIRI |
| NIR | JWST NIRSpec at z=6.33 (J0100+2802) |
| optical | nine SDSS line fitters, median H-beta/[O III] **2.04**, scatter **0.053 dex** |
| UV | HST STIS C IV fit (S/N 1.8 - reported as tentative, not a detection) |
| soft X-ray | XMM RGS: OVII forbidden **22.10 A** at **9.2 sigma**, intercombination at **5.3 sigma** |
| hard X-ray | HEXTE 15-100 keV: E_cut **43 keV**, Delta C-stat **+0.4** - no cutoff required |
| joint | 3ML fit of PDS 456 across UV/optical/MIR - and the finding that a single power law fails, because the UV is absorbed |

To reproduce any of them, restore the input with the URL in its `source.json` and
run the tool through its runner; the layout and the command are in
[`outputs/README.md`](outputs/README.md).

## Spectral bands actually covered

Every row below has a committed product produced from **real observations**, not
synthetic data.  Frequencies/wavelengths are the observed range of the data used.

| band | instrument / source | object(s) | tool(s) |
|---|---|---|---|
| X-ray 0.5-20 keV (CCD) | XMM-Newton EPIC, RXTE PCA | PDS 456; 3C 120, MCG-6-30-15 | `xmm_xspec`, `bxa_xspec`, `rxte_xspec`, `xmm_sas_raw` |
| X-ray 0.45-1.05 keV (grating) | XMM-Newton RGS | NGC 4051 | `xmm_rgs` |
| UV 1140-3140 A | HST STIS | PDS 456 | `pyqsofit_uv` |
| optical | SDSS, X-SHOOTER, MaNGA | 10 sources | 12 tools |
| NIR 2.9-5.2 um | JWST NIRSpec | J0100+2802 (z=6.33) | `nir_linefit`, `cafe_line`, `s3fit_line` |
| MIR 5-38 um | Spitzer IRS, JWST MIRI MRS | 6 sources | `pahfit_mir`, `cafe_line`, `ir_linefit` |
| FIR 55-210 um | Herschel PACS | NGC 4151, NGC 1068 | `fir_linefit`, `ir_linefit` |
| sub-mm / mm 88-266 GHz | Herschel HIFI, ALMA, HCN 1-0 | NGC 1068, NGC 1275, Galactic | `submm_line`, `radio_line`, `casa_specfit` |
| **radio cm 1.42 GHz** | **ATCA H I 21-cm** | **PMN J0029-7228** | **`radio_line`** |
| resolved cubes | ALMA, JWST MIRI MRS | NGC 1275 | `cube_lines` |

Deliberately **not** covered: gamma rays (no emission lines to fit) and radio
continuum photometry (this is an emission-line repository, not a radio SED
survey).  Hard X-rays above 20 keV (NuSTAR) and a joint multi-instrument
likelihood (3ML) are scoped but not implemented - see
[`docs/LITERATURE_COVERAGE.md`](docs/LITERATURE_COVERAGE.md).

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
- **Radio cm (ATCA H I 21-cm, PMN J0029-7228):** v **+123.07 km/s**, FWHM
  **4.57 km/s**, τ **0.200**, N(H I) **1.77e18 cm-2**, S/N **11.7** - reproduces
  the published peak and depth.
- **Soft X-ray gratings (XMM RGS, NGC 4051):** OVII forbidden **22.10 A** at
  **9.2σ** and intercombination **21.80 A** at **5.3σ**, resolved individually -
  the pair that CCD resolution blends into one hump.
- **Resolved mapping (ALMA, NGC 1275):** HCN 3-2 per-spaxel moment maps,
  aperture fit v **+232 km/s**, FWHM **156 km/s**, S/N **13.0**.
- **NGC 1275 HCN 3-2, three independent engines:** 5.1σ (pyspeckit), 5.2σ
  (McFine), 3.8σ (CASA specfit) on the same box - and the CASA cross-check
  originally caught the other two fitting a narrow spike 220 km/s off the line.

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
| [`docs/RESULTS.md`](docs/RESULTS.md) | every committed product's headline numbers (generated) |
| [`docs/XMM_RAW_SAS_RESULT.md`](docs/XMM_RAW_SAS_RESULT.md) | raw SAS PN cross-check of the PPS X-ray result |
| [`docs/UNRESOLVED_ITEMS.md`](docs/UNRESOLVED_ITEMS.md) | remaining blockers with evidence and owners |
| [`docs/RUN_MANIFEST.md`](docs/RUN_MANIFEST.md) | normalized run/catalog status |
| [`workflow/README.md`](workflow/README.md) | Snakemake graph |

## Environment and tests

- Host dependencies: `requirements-host.txt`
- QA tools: `requirements-dev.txt`
- Docker images: `pipeline/runners/build_images.sh` (32 images, 31 registered tools)
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
