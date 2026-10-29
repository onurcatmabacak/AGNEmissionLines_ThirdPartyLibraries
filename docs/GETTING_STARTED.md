# Getting started

This guide is for a new user who has never run the repository.  You do **not**
need to understand every fitting code or run the full matrix.  Start with one
object and one result.

## 1. What this repository does — and does not do

It runs **third-party AGN analysis codes** inside Docker and stores every
result under a canonical source/tool path:

```text
inputs/<source_key>/source.json          # what data exist
outputs/<tool>/<source_key>/             # what the tool produced
```

It does **not**:

- discover new AGN automatically;
- replace a full survey reduction;
- turn every fit into a publication result (see the caveat matrix);
- provide a single universal AGN model.  Different tools fit different physics.

There are two kinds of codes:

| kind | examples | what they measure |
|---|---|---|
| **line fitting** | PyQSOFit, QSOFITMORE, optical_linefit, GANDALF, S3Fit, CAFE, PAHFIT, XMM/RXTE/XSPEC | line flux, width, EW, kinematics |
| **SED fitting** | CIGALE, AGNfitter | stellar/dust/torus SED parameters — **not individual lines** |

## 2. Prerequisites

- Linux or macOS (Windows via WSL2 is possible but not tested)
- Docker Engine or Docker Desktop, with permission to run `docker`
- Python **3.12**
- [`uv`](https://docs.astral.sh/uv/) (or use `python -m venv` + `pip`)
- **Disk space:** at least ~15 GB free for the first few images; the full
  matrix is much larger (the XSPEC image alone is ~4.35 GB).
- Network access for the first image build and optional data downloads.

The repository already contains small real data for several examples.  Large
MaNGA cubes are intentionally not committed; see `inputs/README.md`.

## 3. A no-Docker first look (2 minutes)

From the repository root:

```bash
git clone https://github.com/onurcatmabacak/AGNEmissionLines_ThirdPartyLibraries.git
cd AGNEmissionLines_ThirdPartyLibraries

uv venv .venv
source .venv/bin/activate
uv pip install -r requirements-host.txt -r requirements-dev.txt

# What would the planner choose for 3C 120?
python pipeline/plan_analysis.py --source 3C120_z_0.0330

# Inspect an existing, committed cross-mission result (no Docker needed)
python pipeline/compare_xray_optical.py --source 3C120_z_0.0330
python -m json.tool outputs/crossmission/3C120_z_0.0330/xray_optical_comparison.json
```

You should see a plan containing an optical fit and an X-ray fit, and a JSON
result for the same object.  This is the safest way to learn the output
contract before building images.

## 4. Your first Docker fit (10–15 minutes)

Start with the small `optical_linefit` image and the public PDS 456
X-SHOOTER spectrum:

```bash
bash Pipelines/build_images.sh optical_linefit

python pipeline/run_new_tools.py \
  --only PDS456_z_0.1840 \
  --tools optical_linefit \
  --force
```

Read:

```text
outputs/optical_linefit/PDS456_z_0.1840/
  optical_lines.csv
  optical_lines_summary.json
  optical_fit.png
  README.md
```

The first line table contains the local Hβ and [O III] fit.  `quality` will be
`provisional` for PDS 456 because the X-SHOOTER spectrum has absorption and a
high formal χ²; that is a real scientific warning, not a pipeline failure.

For a more complete first example, build PyQSOFit:

```bash
bash Pipelines/build_images.sh pyqsofit_uv

python pipeline/run_new_tools.py \
  --only 3C120_z_0.0330 \
  --tools pyqsofit_uv \
  --force
```

This takes longer than `optical_linefit` but gives the Hβ/[O III] measurement
used by the 3C 120 cross-mission example.

## 5. Which path should I choose?

| I have / I want | Start with |
|---|---|
| optical/UV AGN spectrum | `pyqsofit_uv`, `qsofitmore_line`, `optical_linefit`, `s3fit_line` |
| X-ray spectrum | `xmm_xspec` or `rxte_xspec` |
| NIR/MIR spectrum | `cafe_line`, `pahfit_mir`, `nir_linefit` |
| FIR spectrum | `fir_linefit` |
| photometry / SED | `cigale_sed`, `agnfitter_sed` |
| MaNGA IFU cube | `manga_dap` |
| same-object X-ray + optical | `crossmission` (case study, not a correlation) |

The planner gives a source-specific recommendation:

```bash
python pipeline/plan_analysis.py --source <source_key> --goal auto
python pipeline/plan_analysis.py --source <source_key> --goal lines
python pipeline/plan_analysis.py --source <source_key> --goal xray
```

`--goal auto` excludes long runs by default.  Use `--include-expensive` or
`--goal all` only when you intend to spend the time.

## 6. Input contract

A source lives in one directory:

```text
inputs/<source>_z_<redshift>/
  source.json
  raw/
  photometry/            # optional
```

`source.json` is the authority.  Minimal example:

```json
{
  "key": "myAGN_z_0.0500",
  "name": "myAGN",
  "z": 0.05,
  "kind": "sdss",
  "files": {
    "spectrum": "raw/spec-00000-00000-00000000000.fits"
  },
  "tools": ["pyqsofit_uv", "optical_linefit"]
}
```

The `files` roles are described in `inputs/README.md`.  Do not copy raw data
into `outputs/`.  Tool-native prepared files go under `work/prepared/` and are
ignored by git.

## 7. Run one tool or a matrix

One source/tool:

```bash
python pipeline/run_new_tools.py \
  --only <source_key> --tools <tool> --force
```

A planned set:

```bash
python pipeline/run_new_tools.py --source <source_key> --auto
```

A Snakemake graph (dry-run first):

```bash
snakemake -s workflow/Snakefile -n \
  --config sources=3C120_z_0.0330 tools=pyqsofit_uv,crossmission

snakemake -s workflow/Snakefile --cores 2 \
  --config sources=3C120_z_0.0330 tools=pyqsofit_uv,crossmission
```

**Do not run `snakemake all` as a first command.**  It can launch S3Fit,
PAHFIT, CAFE and other long jobs.

## 8. Read the outputs

Typical files:

| file | meaning |
|---|---|
| `run.json` | tool status, configuration, software provenance |
| `*.csv` | machine-readable line/parameter measurements |
| `*.fits` | native tool products |
| `*.png` / `*.pdf` | fit, residual, corner or uncertainty figures |
| `README.md` | human-readable method and caveats |

Every output should be read with:

- the tool's `README.md`;
- `docs/CAVEAT_MATRIX.md`;
- `configs/caveats.yaml` for the machine-readable status.

`quality` values are not decoration: `tentative`, `provisional` and
`systematics-limited` mean the number should not be treated as a clean
publication measurement.

## 9. Validate the repository

```bash
python -m pytest -q
python pipeline/validate_outputs.py
python pipeline/build_output_manifest.py   # after you add/change products
```

The validation checks the output schema and SHA-256 hashes.  The tests are
regression/golden tests, not an independent astrophysical truth test.

## 10. Troubleshooting

**`docker: permission denied`**  
Add your user to the docker group, log out/in, or run Docker Desktop with the
appropriate permissions.

**`Docker image ... not found`**  
Build only that image: `bash Pipelines/build_images.sh <tool>`.

**A run is taking too long**  
Check the cost in `pipeline/plan_analysis.py`; stop the container and choose a
shorter tool.  `s3fit_line`, `cafe_line`, `galspec_line`, `qgfit` and
`agnfitter_sed` are long.

**`inputs/... raw cube missing`**  
Read `inputs/<source>/download.sh` or `inputs/README.md`; large files are not
committed.

**I changed an output and validation fails**  
Regenerate the catalogue with `pipeline/build_output_manifest.py`; never edit
`outputs/output_catalog.json` by hand.

**Docker uses too much disk**  
Remove unused images with `docker image prune`; the full XSPEC/MaNGA stack is
large.

## 11. Glossary

- **AGN** — active galactic nucleus.
- **Broad line** — line from the broad-line region, typically FWHM > 1000 km/s.
- **Narrow line** — forbidden/ionic line from the narrow-line region.
- **EW** — equivalent width (line strength relative to continuum).
- **Fe Kα** — X-ray fluorescence line at 6.4 keV rest frame.
- **χ²_ν** — chi-square per degree of freedom; not meaningful without the model.
- **MC** — Monte Carlo uncertainty propagation.
- **MCMC** — Markov-chain Monte Carlo posterior sampling.
- **BPT** — Baldwin–Phillips–Terlevich line-ratio diagnostic.
- **SED** — spectral energy distribution from photometry, not a spectrum.
- **IFU** — integral-field unit (spatially resolved spectroscopy).

## 12. Citation and licences

See `CITATION.cff` and `LICENSE`.  Third-party codes retain their own licences;
the repository does not relicense them.  HST and ESO data used in the examples
have their archive licences recorded in the source READMEs.
