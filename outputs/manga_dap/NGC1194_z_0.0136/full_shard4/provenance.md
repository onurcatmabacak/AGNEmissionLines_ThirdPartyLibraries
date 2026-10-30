# MaNGA DAP provenance — NGC 1194 (9193-12701)

This note documents a **real run of the official SDSS MaNGA Data Analysis
Pipeline** (`sdss-mangadap` 4.5.0) on the public DR17 LOGCUBE of NGC 1194.
The published DAP MAPS (v3_1_1/3.1.0) is an independent reference
product; it was not used as an input to this run.

## Inputs

| role | file | size (bytes) | SHA-256 | source |
|---|---|---:|---|---|
| `manga_cube` | `manga-9193-12701-LOGCUBE.fits.gz` | 207992431 | `7810f4c94db2fbb677e1bc92bc91a866e88d421c24c8c52273aa5277b9b5f764` | https://data.sdss.org/sas/dr17/manga/spectro/redux/v3_1_1/9193/stack/manga-9193-12701-LOGCUBE.fits.gz |
| `manga_rss` | `manga-9193-12701-LOGRSS.fits.gz` | 169194046 | `812000fdc1946193f8aa0e2e96878555ec370fa30b3a41df20cd76b0bad497bd` | https://data.sdss.org/sas/dr17/manga/spectro/redux/v3_1_1/9193/stack/manga-9193-12701-LOGRSS.fits.gz |
| `reference_maps` | `manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz` | 10775592 | `f47f16b90c45fc668e0105e9b2a2241d6c28104924056bcfa493f84e1f200f49` | https://data.sdss.org/sas/dr17/manga/spectro/analysis/v3_1_1/3.1.0/HYB10-MILESHC-MASTARHC2/9193/12701/manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz |

The LOGCUBE is the datacube consumed by the DAP.  LOGRSS is loaded by
the official MaNGA datacube object to compute the spatial covariance
matrix used by the Voronoi binning; it is not fit as a spectrum.  Both
DRP files are downloaded unmodified by
`inputs/NGC1194_z_0.0136/download.sh` and are intentionally not committed
because they exceed GitHub's 100 MB per-file limit.  The 10.8 MB published
MAPS *is* committed because it is the comparison reference.

## Software

- `sdss-mangadap` **4.5.0** (upstream commit `g996b46cb9739126fe0fbe69c1a50d8490d924853`)
- numpy 2.4.1, scipy 1.18.1, astropy 8.0.2, ppxf 8.1.0
- cvxopt 1.3.3, vorbin 3.1.5, pydl 1.0.1
- Python 3.12.16 on Linux-7.0.0-38-generic-x86_64-with-glibc2.36

## Configuration

- DAPTYPE: `HYB10-MILESHC-MASTARHC2`
- analysis plan: `configs/manga_dap/default/plan_moments.toml`
- binning: `HYB10`, Voronoi target S/N = 50.0
- stellar continuum: `MILESHC` + pPXF, MILES-HC templates
- emission lines: `EFITHC2` + SASUKE, line database `ELPMPL11` (35 channels)
- templates: `MASTARHC2`; exact file hashes are in `effective_config.json`
- uncertainty: formal least-squares covariance from the DAP SASUKE fit; no MCMC

## Run

- started: 2026-10-29T07:35:53Z
- finished: 2026-10-29T20:47:33Z
- wall time: 47499.7 s
- status: **ok**
- DAP status code: 0
- warnings captured: 0

## Products

| file | contents |
|---|---|
| `manga_lines.csv` | compact per-spaxel table for the six key lines, ratios, BPT class and stellar kinematics |
| `manga_lines_all.csv.gz` | long table of every valid DAP channel measurement (35 channels) |
| `line_summary.csv` | per-line census: counts, medians, sums, EWs and kinematics |
| `fast_eline_bins.csv` | official SASUKE fit result for each of the 175 HYB10 bins |
| `fits/manga_dap_moments_maps.fits.gz` | Stage-A official DAP MAPS with stellar kinematics and emission-line moments (empty Gaussian extensions) |
| `logs/full_dap_attempt_summary.txt` | exact evidence for the full 65-template EmissionLineModel runtime blocker |
| `maps_stats.json` | global BPT fractions, kinematic summaries and bin/spaxel counts |
| `fits/manga_dap_maps.fits.gz` | full DAP MAPS produced by this run |
| `fits/manga_dap_key_maps.fits.gz` | compact subset of key line, BPT and kinematic maps |
| `fits/manga_dap_central_spectra.fits` | observed and DAP model spectra at the brightest H-alpha spaxel |
| `figures/manga_dap_maps.png` | pedagogical 3x3 maps of line flux, kinematics and S/N |
| `figures/manga_dap_bpt.png` | N2-BPT diagram and spatial ionization-class map |
| `figures/manga_dap_spectrum_fit.png` | H-beta/[O III] and H-alpha/[N II]/[S II] data-model fit |
| `run.json` | versions, input hashes, DAP status, warnings, runtime and product manifest |
| `effective_config.json` | exact plan, metadata, template/DB hashes and uncertainty settings |
| `provenance.md` | human-readable provenance, reproduction command and limitations |

## Measurement summary

- bins: 2397
- spaxels with a valid H-alpha Gaussian flux: 2681
- BPT classes: {'n_classified': 2289, 'n_total': 5476, 'star_forming': 9, 'star_forming_fraction': 0.003931847968545216, 'composite': 83, 'composite_fraction': 0.036260375709917, 'seyfert': 1945, 'seyfert_fraction': 0.8497160332022717, 'liner': 231, 'liner_fraction': 0.10091743119266056, 'agn_unclassified': 21, 'agn_unclassified_fraction': 0.009174311926605505}
- brightest H-alpha spaxel: row 37, col 37, BPT `liner`

## Comparison to the published MAPS

The independent comparison to the published MAPS is produced by `Tools/manga_dap/compare_maps.py`; its summary is in `comparison/comparison_summary.json` and `comparison/comparison_notes.md`.

## Limitations

- Only the 9 central single-spaxel HYB10 bins are measured with the official full-method SASUKE. This is not a spatially complete IFU map; the published official MAPS is the all-spaxel reference.
- The full all-spaxel 2397-bin 65-template EmissionLineModel did not complete within the 58 min wall-clock budget and was killed; no all-spaxel DAP MAPS was produced by this repository.
- The fast fixed-continuum all-spaxel mode is auxiliary only and is rejected as production (H-alpha ratio 2.37, [N II] 0.53, BPT agreement 41%, gas velocity offset +175 km/s).
- The DAP is a narrow-line single-Gaussian model. It does not fit broad Balmer lines, Fe II, Balmer continuum or AGN outflows.
- Gaussian line fluxes are integrated over the DAP fit window and tied multiplets; they are not aperture-corrected.
- No extinction correction is applied to the DAP line fluxes.
- The published MAPS was produced with DAP 3.1.0; this run uses 4.5.0, so the comparison is a code-version cross-check, not a bit-for-bit reproduction.
- BPT classes are discrete and boundary-sensitive; NGC 1194 sits near the Seyfert/LINER boundary.

## Reproduction

```bash
bash pipeline/runners/build_images.sh manga_dap
bash inputs/NGC1194_z_0.0136/download.sh
bash pipeline/runners/run_manga_dap_docker.sh \
  inputs/NGC1194_z_0.0136 \
  outputs/manga_dap/NGC1194_z_0.0136 \
  --reference inputs/NGC1194_z_0.0136/raw/manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz
```

The runner mounts the input directory read-only, mounts the config
directory read-only, and writes only under the requested output directory.
