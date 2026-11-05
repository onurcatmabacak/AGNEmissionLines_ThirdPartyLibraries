# `manga_dap/default`

Official SDSS-IV MaNGA Data Analysis Pipeline configuration for the real MaNGA
AGN **NGC 1194** (plateifu **9193-12701**, `z=0.0136253`).

## Files

| file | role |
|---|---|
| `config.json` | DAPTYPE, source metadata, binning, continuum, line database, subset/fast quality gates, uncertainty and limitations |
| `plan.toml` | upstream `sdss-mangadap` 4.5.0 default plan (`HYB10`, target S/N=10, full 65-template Gaussian model).  This is the all-spaxel attempt that exceeded the time budget. |
| `plan_moments.toml` | Stage-A plan: the same official DAP with the Gaussian `eline_fits` block removed, target S/N=50 (175 bins). |
| `plan_subset.toml` | Stage-B plan: official full-method `EmissionLineModel` (65 MaStar-HC2 templates, `ELPMPL11`, `mdegree=14`, `deconstruct_bins='ignore'`), restricted to 9 central bins by the runner. |
| `line_database.csv` | 35 `ELPMPL11` channels with NIST rest wavelengths (vacuum) and DAP multiplet ties. |

## DAP settings

* DAPTYPE: `HYB10-MILESHC-MASTARHC2`
* Binning: `HYB10`, Voronoi, target S/N = 50 for the completed Stage A
* Stellar continuum: `MILESHC` + pPXF, `velscale_ratio=4`, `BADSKY` artifact
  mask, `ELPSCMSK` emission mask
* Emission-line moments: `EMOM`
* Emission-line model: `EFITHC2` + `Sasuke`, `ELPMPL11`, `MASTARHC2`
  (65 templates), `mdegree=14`, `etpl_line_sigma_mode='offset'`,
  `etpl_line_sigma_min=10`
* Spectral indices: `INDXEN`

## Quality gates

The accepted product is the official full-method SASUKE fit on the **9 central
single-spaxel bins** (BINIDs 97, 57, 0, 107, 110, 1, 94, 101, 120).  It
reproduces the published DAP MAPS at those spaxels to <0.1% with 9/9 BPT
agreement.

The all-spaxel 2397-bin fit (target S/N=10) reached 157/2397 spectra and was
killed at the 3500 s (58 min) wall-clock cap.  No all-spaxel DAP MAPS was
produced; the published MAPS is the all-spaxel reference.

The fast fixed-continuum all-spaxel mode is **rejected as production**:
H-alpha median ratio 2.37, [N II] 0.53, BPT agreement 40.8%, H-alpha gas
velocity offset +175 km/s.  It is retained only in
`outputs/.../manga_dap/aux_fastmode/` with
`QUALITY='FASTMODE_NOT_PRODUCTION'`, `PRODSTAT='AUXILIARY'`, `ACCEPT=0`.

## Uncertainty

The DAP reports formal least-squares covariance errors; the MAPS stores
`1/sqrt(IVAR)` for flux, velocity and dispersion.  There is no MCMC.  Ratio
errors in the compact table use analytic propagation and ignore covariance
between lines from the same fit.

## Reproduction

```bash
bash pipeline/runners/build_images.sh manga_dap
bash inputs/NGC1194_z_0.0136/download.sh
bash pipeline/runners/run_manga_dap_docker.sh \
  inputs/NGC1194_z_0.0136 \
  outputs/manga_dap/NGC1194_z_0.0136 \
  --reference inputs/NGC1194_z_0.0136/raw/manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz \
  --n-bins 9
```
