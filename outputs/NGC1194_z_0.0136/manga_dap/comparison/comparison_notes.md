# Official DAP subset vs published MaNGA DAP MAPS

**Product:** official full-method SASUKE fit on the 9 central single-spaxel
HYB10/S/N=50 bins of NGC 1194 (9193-12701).  **Reference:** published SDSS
DAP MAPS `HYB10-MILESHC-MASTARHC2`, v3_1_1/3.1.0, at the same spaxels.
This is not an all-spaxel comparison.

## Fluxes

For each selected bin, the reference value is the median of the published
per-spaxel values over the spaxels in that bin.  All bins are single-spaxel,
so this is a direct spaxel comparison.

| line | N | median ours/ref | 16-84% | Pearson r |
|---|---:|---:|---:|---:|
| H-alpha 6564 | 9 | 0.99985 | 0.99972-0.99990 | 0.999998 |
| H-beta 4862 | 9 | 0.99950 | 0.99902-0.99972 | 0.999980 |
| [O III] 5007 | 9 | 0.99999 | 0.99999-1.00000 | 0.99999999 |
| [N II] 6584 | 9 | 0.99986 | 0.99979-0.99987 | 0.9999997 |
| [S II] 6716 | 9 | 0.99997 | 0.99996-0.99999 | 0.9999994 |
| [S II] 6731 | 9 | 0.99999 | 0.99995-1.00003 | 0.9999988 |

Formal-error ratios are 0.9999-1.0000.  The tiny residual is the DAP
code-version difference (3.1.0 reference vs 4.5.0 here); the same DRP cube,
DAPTYPE, line database and Gaussian model are used.

## BPT

All 9 bins classify as **LINER** by the Kewley et al. (2006) [S II] division
in both products: **9/9 agreement**.  NGC 1194 is near the Seyfert/LINER
boundary; the Kewley et al. (2001) N2 division puts the central spaxels in the
AGN region.

## Kinematics

| quantity | N | median offset (ours-ref) | robust scatter |
|---|---:|---:|---:|
| H-alpha velocity | 9 | +0.001 km/s | 0.001 km/s |
| H-alpha sigma | 9 | -0.016 km/s | 0.004 km/s |
| stellar velocity | 9 | +0.0001 km/s | 0.0002 km/s |
| stellar sigma | 9 | -0.0004 km/s | 0.0006 km/s |

## Caveat

This validates the central 3x3 spaxels.  It is not a spatially complete DAP
map.  The all-spaxel 2397-bin DAP emission-line model exceeded the 58 min
budget and was killed; the published MAPS is the all-spaxel reference.  The
fast fixed-continuum all-spaxel mode in `../aux_fastmode/` is rejected as
production (`FASTMODE_NOT_PRODUCTION`): H-alpha ratio 2.37, [N II] 0.53,
BPT agreement 41%, gas-velocity offset +175 km/s.
