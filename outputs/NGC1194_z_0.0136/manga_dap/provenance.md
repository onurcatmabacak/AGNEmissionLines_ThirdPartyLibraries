# MaNGA DAP production provenance — NGC 1194 (9193-12701)

## Result in one sentence

The accepted product is an **official full-method SDSS MaNGA DAP/SASUKE fit
on the 9 central single-spaxel HYB10 bins**, validated against the published
official DAP MAPS at the same spaxels; the all-spaxel 2397-bin DAP emission
line model exceeded the time budget and is documented as a limitation, and the
fast fixed-continuum all-spaxel run is retained only in `aux_fastmode/` with a
`FASTMODE_NOT_PRODUCTION` quality flag.

## Source and inputs

| role | file | size (bytes) | SHA-256 | URL |
|---|---|---:|---|---|
| MaNGA LOGCUBE | `manga-9193-12701-LOGCUBE.fits.gz` | 207992431 | `7810f4c94db2fbb677e1bc92bc91a866e88d421c24c8c52273aa5277b9b5f764` | https://data.sdss.org/sas/dr17/manga/spectro/redux/v3_1_1/9193/stack/manga-9193-12701-LOGCUBE.fits.gz |
| MaNGA LOGRSS | `manga-9193-12701-LOGRSS.fits.gz` | 169194046 | `812000fdc1946193f8aa0e2e96878555ec370fa30b3a41df20cd76b0bad497bd` | https://data.sdss.org/sas/dr17/manga/spectro/redux/v3_1_1/9193/stack/manga-9193-12701-LOGRSS.fits.gz |
| published DAP MAPS | `manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz` | 10775592 | `f47f16b90c45fc668e0105e9b2a2241d6c28104924056bcfa493f84e1f200f49` | https://data.sdss.org/sas/dr17/manga/spectro/analysis/v3_1_1/3.1.0/HYB10-MILESHC-MASTARHC2/9193/12701/manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz |

The two DRP cubes are **not committed** (208 MB and 169 MB, above GitHub's
100 MB per-file limit).  `inputs/NGC1194_z_0.0136/download.sh` downloads and
SHA-256-verifies them.  The 10.8 MB published MAPS **is committed** in
`inputs/NGC1194_z_0.0136/raw/` and is the all-spaxel reference.

Source: NGC 1194, MaNGA plateifu **9193-12701**, `z = 0.0136253` (NSA v1_0_1
via DRPall v3_1_1), Seyfert 2, MaNGA AGN Catalog VAC (Comerford et al. 2020).

## Software and data

- `sdss-mangadap` **4.5.0**, upstream commit
  `996b46cb9739126fe0fbe69c1a50d8490d924853` (BSD-3-Clause).
- Docker image `manga_dap`, **1,853,913,965 bytes** (1.85 GB).
- numpy 2.4.1, scipy 1.18.1, astropy 8.0.2, matplotlib 3.11.2, ppxf 8.1.0,
  cvxopt 1.3.3, vorbin 3.1.5, pydl 1.0.1, shapely 2.2.0.
- DAP data used from the wheel: MILES-HC templates
  (`mangadap/data/spectral_templates/miles_cluster/*.fits`), MaStar-HC2
  templates (`.../mastarhc_v2/*.fits.gz`), `ELPMPL11` line database
  (`.../emission_lines/elpmpl11.par`), `BADSKY` artifact mask,
  `ELPSCMSK`, and `sdssMaskbits.par`.  Every file's MD5/SHA-256 is in
  `effective_config.json`.

## Stage A — official DAP moments stage

The official `manga_dap()` workflow was run with the Gaussian `eline_fits`
block set to `None` so that the expensive emission-line model could be
handled separately.  This completed:

- reduction assessments and covariance;
- HYB10 Voronoi binning at **target S/N = 50** (175 bins);
- pPXF stellar kinematics with MILES-HC;
- `EMOM` emission-line moments;
- `INDXEN` spectral indices;
- an official MAPS file with empty Gaussian-line extensions.

Stage-A runtime: **1741.7 s (29.0 min)**.  The moments-only MAPS is committed
as `fits/dap_stage_a_moments_maps.fits.gz`.  The binned spectra and pPXF
continuum are committed as `fits/dap_binned_spectra.fits.gz` and
`fits/dap_stellar_continuum.fits.gz`.

This stage is official DAP, but it is **not** a Gaussian emission-line fit.

## Stage B — official full-method SASUKE subset

The production emission-line measurement uses the **official default
`EmissionLineModel` method**, not the fast fixed-continuum mode:

- 65 MaStar-HC2 stellar templates;
- `ELPMPL11` 35-line database;
- `mdegree = 14`, `deconstruct_bins = 'ignore'`;
- `Sasuke` Gaussian fit, full official implementation.

The official `EmissionLineModel` was restricted to the **9 central
single-spaxel HYB10 bins** by documented `good_bins`/
`select_binned_spectra_to_fit` selections in
`Tools/manga_dap/run_official_subset.py`.  The 9 BINIDs are
`[97, 57, 0, 107, 110, 1, 94, 101, 120]` (central 3x3 spaxels, 0.5 arcsec
sampling).  Runtime: **393.4 s (6.6 min)**, no fit failures.  The same script was rerun inside the final image with the Stage-A tree mounted read-only and completed in **390.6 s** with identical ratios and 9/9 BPT agreement.

Outputs:

- `fits/dap_subset_maps.fits.gz` — official subset MAPS; only the 9 bins are
  valid, every other bin/spaxel is masked;
- `fits/dap_subset_central_spectra.fits` and
  `figures/manga_dap_spectrum_fit.png` — observed binned spectrum and
  full-method DAP/SASUKE model at the central bin;
- `manga_lines.csv` / `subset_bins.csv` — the 9 bin measurements;
- `subset_comparison.json`, `subset_comparison_lines.csv`,
  `comparison/` — comparison to the published MAPS at the same spaxels.

## Subset validation against the published official MAPS

For each of the 9 selected bins, the published MAPS values were median-combined
over the spaxels belonging to that bin and compared to the subset fit.  The
agreement is essentially exact because the same DRP cube, DAPTYPE, line
database and Gaussian model are used; the small residual is the DAP
code-version difference (3.1.0 reference vs 4.5.0 here).

| line | N bins | median ours/ref | 16-84% | median fractional diff | Pearson r |
|---|---:|---:|---:|---:|---:|
| H-alpha 6564 | 9 | 0.99985 | 0.99972-0.99990 | -1.5e-4 | 0.999998 |
| H-beta 4862 | 9 | 0.99950 | 0.99902-0.99972 | -5.0e-4 | 0.999980 |
| [O III] 5007 | 9 | 0.99999 | 0.99999-1.00000 | -8e-6 | 0.99999999 |
| [N II] 6584 | 9 | 0.99986 | 0.99979-0.99987 | -1.4e-4 | 0.9999997 |
| [S II] 6716 | 9 | 0.99997 | 0.99996-0.99999 | -2.6e-5 | 0.9999994 |
| [S II] 6731 | 9 | 0.99999 | 0.99995-1.00003 | -1e-5 | 0.9999988 |

BPT classification agrees for **9/9** bins (all LINER by the Kewley et al.
2006 [S II] division; NGC 1194 sits near the Seyfert/LINER boundary).
Formal-error ratios are 0.9999-1.0000.  Kinematics: H-alpha velocity offset
+0.001 km/s, H-alpha sigma -0.016 km/s, stellar velocity +0.0001 km/s,
stellar sigma -0.0004 km/s (9 bins).

This is a defensible measurement of the central 3x3 spaxels, not a
spatially complete DAP map.  The all-spaxel reference is the published MAPS.

## Full all-spaxel DAP limitation

A separate full all-spaxel run at HYB10 target S/N=10 produced **2397 bins**
and entered the official 65-template SASUKE fit (2397 original spectra,
2688 remapped spectra, 137 model degrees of freedom).  It reached
"Fitting spectrum 157/2397" and was killed by the **3500 s (58 min)**
wall-clock cap at ~100% of one CPU.  The DAP's Sasuke loop is serial and the
65-template least-squares problem is too large for this 8-core host within
the budget.  No all-spaxel MAPS was produced by that attempt.

Exact evidence: `logs/full_dap_attempt_summary.txt` and
`logs/full_dap_attempt_2397_tail.log`.

This is a **time-budget limitation**, not a claim that the DAP is broken.
The published official MAPS remains the all-spaxel reference.

## Fast mode is rejected as production

`aux_fastmode/` contains a fast fixed-continuum SASUKE run on all 175
HYB10/S/N=50 bins.  It is **not** the production result and must not be cited
as one.  Against the published MAPS it gives H-alpha median ratio 2.37,
H-beta 0.89, [O III] 1.01, [N II] 0.53, BPT agreement 40.8%, and a
+175 km/s H-alpha gas-velocity offset.  The FITS headers carry
`QUALITY='FASTMODE_NOT_PRODUCTION'`, `PRODSTAT='AUXILIARY'`, `ACCEPT=0`.
Its comparison is in `aux_fastmode/comparison_fastmode/`.

## Outputs and quality gate

`run.json` has `status: ok_subset`, `all_spaxel_dap_completed: false`, and a
`quality_gate` block with `subset_acceptance: true`,
`all_spaxel_acceptance: false`, `fast_mode_acceptance: false`.

Main figures: `figures/manga_dap_spectrum_fit.png` (central official
DAP/SASUKE fit), `figures/manga_dap_subset_comparison.png` (9-bin line
comparison), `figures/manga_dap_subset_bpt.png` (9-bin BPT).

## Reproduction

```bash
bash Pipelines/build_images.sh manga_dap
bash inputs/NGC1194_z_0.0136/download.sh
# Stage A (official moments-only DAP)
docker run ... manga_dap python /app/run/run_manga_dap.py \
  --input-dir /app/input --out /app/output --config /app/config \
  --fast-eline --stage-a-only --reference /app/reference/<published-MAPS>
# Stage B (official full-method subset)
docker run ... manga_dap python /app/run/run_official_subset.py \
  --input-dir /app/input --stage-a-dir /app/output \
  --out /app/output --config /app/config \
  --reference /app/reference/<published-MAPS> --n-bins 9
```

The committed `fits/dap_binned_spectra.fits.gz`,
`fits/dap_stellar_continuum.fits.gz` and
`fits/dap_stage_a_moments_maps.fits.gz` are the Stage-A inputs needed to
rerun Stage B without rebuilding the expensive Stage A products.

## Limitations

- Only 9 central single-spaxel bins are measured; this is not a full IFU map.
- The DAP is a narrow-line single-Gaussian model: no broad Balmer lines,
  Fe II, Balmer continuum or AGN outflows.
- The published MAPS uses DAP 3.1.0; this run uses 4.5.0, so the comparison
  is a code-version cross-check.
- Fluxes are not aperture-corrected or extinction-corrected.
- BPT classes are discrete and boundary-sensitive; NGC 1194 is near the
  Seyfert/LINER boundary.
