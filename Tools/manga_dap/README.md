# `manga_dap` — official SDSS MaNGA DAP, subset production result

Production implementation of the **official SDSS-IV MaNGA Data Analysis
Pipeline** (`sdss-mangadap` **4.5.0**) for a real MaNGA AGN datacube.

Source: **NGC 1194** (Sy2), MaNGA **plateifu 9193-12701**, `z = 0.0136253`
(NSA v1_0_1 via DRPall v3_1_1), from the **MaNGA AGN Catalog VAC**
(Comerford et al. 2020).

The accepted product is an **official full-method DAP/SASUKE fit on the 9
central single-spaxel HYB10 bins**, compared at the same spaxels to the
published official DAP MAPS.  This is a **subset**, not an all-spaxel DAP map:
the all-spaxel 2397-bin emission-line fit exceeded the time budget (see below).
The published MAPS is the all-spaxel reference.

## What was actually run

### Stage A — official DAP moments stage

The official `manga_dap()` workflow with the Gaussian `eline_fits` block set to
`None` completed:

1. reduction assessments and covariance;
2. HYB10 Voronoi binning at **target S/N = 50** (175 bins);
3. pPXF stellar kinematics with MILES-HC;
4. `EMOM` emission-line moments;
5. `INDXEN` spectral indices;
6. an official MAPS file (Gaussian-line extensions empty).

Stage-A runtime: **1741.7 s (29.0 min)**.  The moments-only MAPS, binned
spectra and pPXF continuum are committed under `outputs/.../manga_dap/fits/`.

### Stage B — official full-method SASUKE subset

The production emission-line measurement uses the **official default
`EmissionLineModel` method**, not the fast fixed-continuum mode:

* **65 MaStar-HC2** stellar templates;
* **`ELPMPL11`** 35-line database;
* `mdegree = 14`;
* `deconstruct_bins = 'ignore'` (official option; fit the 9 binned spectra);
* the upstream `Sasuke` Gaussian fitter.

The official fit is restricted to the **9 central single-spaxel HYB10 bins**
by a documented `good_bins` / `select_binned_spectra_to_fit` selection in
`Tools/manga_dap/run_official_subset.py`.  BINIDs:
`[97, 57, 0, 107, 110, 1, 94, 101, 120]` (the central 3x3 spaxels at 0.5").
Runtime: **393.4 s (6.6 min)**, 9/9 fits succeeded.

The subset MAPS, central spectrum/model and line table are committed.  Every
other spaxel is masked in the subset MAPS; use the published MAPS for the full
field.

## Validation against the published official MAPS

For each selected bin, the published MAPS values were median-combined over the
spaxels in that bin and compared to the subset fit.  The same DRP cube, DAPTYPE,
line database and Gaussian model are used; the small residual is the DAP
code-version difference (3.1.0 reference vs 4.5.0 here).

| line | N bins | median ours/ref | 16-84% | Pearson r |
|---|---:|---:|---:|---:|
| H-alpha 6564 | 9 | 0.99985 | 0.99972-0.99990 | 0.999998 |
| H-beta 4862 | 9 | 0.99950 | 0.99902-0.99972 | 0.999980 |
| [O III] 5007 | 9 | 0.99999 | 0.99999-1.00000 | 0.99999999 |
| [N II] 6584 | 9 | 0.99986 | 0.99979-0.99987 | 0.9999997 |
| [S II] 6716 | 9 | 0.99997 | 0.99996-0.99999 | 0.9999994 |
| [S II] 6731 | 9 | 0.99999 | 0.99995-1.00003 | 0.9999988 |

BPT classification agrees for **9/9** bins (all LINER by the Kewley et al.
2006 [S II] division; NGC 1194 sits near the Seyfert/LINER boundary).
Formal-error ratios are 0.9999-1.0000.  Kinematics also match:
H-alpha velocity offset +0.001 km/s, H-alpha sigma offset -0.016 km/s,
stellar velocity offset +0.0001 km/s, stellar sigma offset -0.0004 km/s
(9 bins).  This validates the central 3x3 spaxels; it does not validate an
all-spaxel map.

## Time-budget limitation (important)

A separate full all-spaxel run at **HYB10 target S/N = 10** produced **2397
bins** and entered the official 65-template SASUKE fit (2397 original spectra,
2688 remapped spectra, 137 model degrees of freedom).  It reached
**“Fitting spectrum 157/2397”** and was killed by the **3500 s (58 min)**
wall-clock cap at ~100% of one CPU.  The DAP's Sasuke loop is serial and the
65-template problem is too large for this 8-core host within the budget.  No
all-spaxel MAPS was produced by this repository.  The published official MAPS
is the all-spaxel reference.

Exact evidence: `outputs/.../manga_dap/logs/full_dap_attempt_summary.txt` and
`full_dap_attempt_2397_tail.log`.

## Fast mode is rejected as production

`aux_fastmode/` contains a fast fixed-continuum SASUKE run on all 175
HYB10/S/N=50 bins.  It is **auxiliary only** and must not be cited as the
production DAP result.  Against the published MAPS it gives H-alpha median
ratio **2.37**, H-beta 0.89, [O III] 1.01, [N II] 0.53, BPT agreement
**40.8%**, and a **+175 km/s** H-alpha gas-velocity offset.  FITS headers carry
`QUALITY='FASTMODE_NOT_PRODUCTION'`, `PRODSTAT='AUXILIARY'`, `ACCEPT=0`.
Its comparison is in `aux_fastmode/comparison_fastmode/`.

## Build

```bash
bash pipeline/runners/build_images.sh manga_dap
```

Image: **1,853,913,965 bytes (1.85 GB)**.  Pins:

```
sdss-mangadap==4.5.0   (upstream commit 996b46cb9739126fe0fbe69c1a50d8490d924853)
numpy==2.4.1           scipy==1.18.1        astropy==8.0.2
matplotlib==3.11.2     ppxf==8.1.0          cvxopt==1.3.3
vorbin==3.1.5          pydl==1.0.1          shapely==2.2.0
```

The wheel ships MILES-HC and MaStar-HC2 templates, `elpmpl11.par`,
`elpscmsk.par`, `badsky.par` and `sdssMaskbits.par`; their MD5/SHA-256 are in
`effective_config.json`.

## Data

`inputs/NGC1194_z_0.0136/download.sh` downloads and SHA-256-verifies:

| product | size |
|---|---:|
| `manga-9193-12701-LOGCUBE.fits.gz` | 207,992,431 B |
| `manga-9193-12701-LOGRSS.fits.gz` | 169,194,046 B |
| `manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz` | 10,775,592 B |

The two DRP cubes exceed GitHub's 100 MB limit and are **not committed**;
`.gitignore` excludes them.  The published MAPS is committed as the
all-spaxel reference.  LOGRSS is loaded for the covariance matrix used by the
binning, not fit as a spectrum.

## Run

The committed subset products can be reproduced in two stages:

```bash
bash pipeline/runners/build_images.sh manga_dap
bash inputs/NGC1194_z_0.0136/download.sh

# Stage A: official moments-only DAP
docker run ... manga_dap python /app/run/run_manga_dap.py \
  --input-dir /app/input --out /app/output --config /app/config \
  --fast-eline --stage-a-only \
  --reference /app/reference/manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz

# Stage B: official full-method SASUKE on 9 central bins
docker run ... manga_dap python /app/run/run_official_subset.py \
  --input-dir /app/input --stage-a-dir /app/output \
  --out /app/output --config /app/config \
  --reference /app/reference/manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz \
  --n-bins 9
```

The committed `fits/dap_binned_spectra.fits.gz`,
`fits/dap_stellar_continuum.fits.gz` and
`fits/dap_stage_a_moments_maps.fits.gz` are the Stage-A inputs needed to rerun
Stage B without repeating the 29-minute Stage A.

## Config

`configs/manga_dap/default/`:

| file | role |
|---|---|
| `config.json` | DAPTYPE, metadata, binning, continuum, line database, subset and fast-mode quality gates |
| `plan.toml` | upstream default full plan (S/N=10, 2397 bins; the timed-out all-spaxel attempt) |
| `plan_moments.toml` | Stage-A plan (Gaussian block removed), S/N=50 |
| `plan_subset.toml` | official full-method subset plan (65 templates, ELPMPL11, mdegree=14, deconstruct_bins=ignore) |
| `line_database.csv` | 35 `ELPMPL11` channels, rest wavelengths and ties |

## Outputs

`outputs/manga_dap/NGC1194_z_0.0136/`:

| file | contents |
|---|---|
| `manga_lines.csv` / `subset_bins.csv` | the 9 central-bin official subset measurements, ratios, BPT, kinematics |
| `line_summary.csv` | subset per-line summary |
| `subset_comparison.json`, `subset_comparison_lines.csv`, `comparison/` | comparison to published MAPS at the same spaxels |
| `subset_stats.json` | BPT and line statistics for the subset |
| `subset_kinematics.csv/json` | H-alpha and stellar kinematics for the 9 bins vs published MAPS |
| `fits/dap_subset_maps.fits.gz` | official subset MAPS (9 valid bins, rest masked) |
| `fits/dap_subset_central_spectra.fits` | observed binned spectrum + full-method DAP/SASUKE model |
| `fits/dap_stage_a_moments_maps.fits.gz` | Stage-A official moments-only MAPS |
| `fits/dap_binned_spectra.fits.gz`, `fits/dap_stellar_continuum.fits.gz` | Stage-A inputs |
| `figures/manga_dap_spectrum_fit.png` | central full-method fit (H-beta/[O III], H-alpha/[N II]/[S II]) |
| `figures/manga_dap_subset_comparison.png` | 9-bin line comparison |
| `figures/manga_dap_subset_bpt.png` | 9-bin BPT |
| `aux_fastmode/` | fast all-spaxel diagnostics, `FASTMODE_NOT_PRODUCTION` |
| `run.json`, `effective_config.json`, `provenance.md` | versions, hashes, quality gate, reproduction |

Fluxes are **1e-17 erg/s/cm²/spaxel**, velocities/dispersions **km/s**, EWs
**Å**.  No extinction correction is applied to the line fluxes.

## Limitations

* Only 9 central single-spaxel bins are measured; this is not a full IFU map.
* The all-spaxel 2397-bin DAP exceeded the 58-minute budget and was killed.
* The fast fixed-continuum all-spaxel mode is rejected as production.
* The DAP is a narrow-line single-Gaussian model (no broad Balmer lines,
  Fe II, Balmer continuum or AGN outflows).
* Fluxes are not aperture-corrected or extinction-corrected.
* BPT classes are discrete; NGC 1194 is near the Seyfert/LINER boundary.
* Formal errors are from the DAP SASUKE covariance, not an independent error
  budget.
