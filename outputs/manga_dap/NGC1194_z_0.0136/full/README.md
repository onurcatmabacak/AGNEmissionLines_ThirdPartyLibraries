# MaNGA official DAP — full all-spaxel product (NGC 1194)

Complete official `sdss-mangadap` 4.5.0 Stage-A run of the NGC 1194 cube
(plate 9193, IFU 12701), all 5,476 spaxels, no binning shortcut.

| | |
|---|---|
| status | **ok** (`dap_status_code = 0`) |
| runtime | 48,731 s (13.51 h, serial; sdss-mangadap 4.5.0 is single-core) |
| spaxels | 5,476 |
| line measurements | 93,102 (`manga_lines_all.csv.gz`) |
| DAP products | `fits/manga_dap_maps.fits.gz` (HYB10-MILESHC-MASTARHC2), `fits/manga_dap_key_maps.fits.gz`, `fits/manga_dap_central_spectra.fits` |
| log | `logs/manga_dap.log` (EXECUTION SUMMARY, FINISH 2026-10-26 00:05:19) |

## Agreement with the published MAPS

`comparison/comparison_summary.json` compares the line fluxes, kinematics and
BPT classes spaxel by spaxel against the published official MAPS:

| metric | value |
|---|---:|
| BPT agreement fraction | **0.9885** (n = 2,269 spaxels with both classifications) |
| AGN-vs-star-forming agreement | 0.9965 |
| Seyfert / LINER / composite / star-forming (ours) | 1,940 / 218 / 82 / 9 |

`maps_stats.json` gives the full-spaxel BPT census: Seyfert 1,945 (85.0 % of
classified), LINER 231, composite 83, star-forming 9, unclassified 21.

## Provenance caveat (read this before quoting the numbers)

`effective_config.json` records a **rejected auxiliary attempt**: an all-spaxel
2,397-bin, 65-template `EmissionLineModel` that exceeded the 58-minute budget
and was killed, and a fast fixed-continuum all-spaxel mode that is auxiliary
only.  That attempt is *not* this product.  The product above is the official
Stage-A DAP (rdxqa → HYB10/S/N=50 binning → pPXF → EMOM → INDXEN) on the full
spaxel grid, which finished with exit status 0.

Sharding the pPXF calls across workers remains unimplemented; this run is the
honest serial baseline (`docs/UNRESOLVED_ITEMS.md`).

## Layout

This is a variant subtree of the MaNGA product; the 9-bin validation product
sits one level up in `outputs/manga_dap/NGC1194_z_0.0136/`.
