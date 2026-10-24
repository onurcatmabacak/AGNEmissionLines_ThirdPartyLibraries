# QSOFITMORE cross-tool check

Hβ and [O III] 5007 are totals (all components); Mg II is the blended
2796/2804 doublet where a tool resolves it.  Fluxes are in
10^-17 erg s^-1 cm^-2.  `delta_sigma` uses
`(tool - QSOFITMORE)/sqrt(err_tool^2 + err_qm^2)`.

| tool | Hβ | [O III] 5007 | Hβ/[O III] | Mg II |
|---|---:|---:|---:|---:|
| qsofitmore_line | 3077 ± 100 | 1505 ± 57 | 2.04 | 2541 ± 209 |
| pyqsofit_uv | 2896 ± 31 | 1479 ± 37 | 1.96 | 2627 ± 70 |
| gandalf_line | 2951 ± 34 | 1423 ± 14 | 2.07 | n/a |
| s3fit_line | 1359 ± 28 | 743 ± 21 | 1.83 | 885 ± 26 |
| galspec_line | 3718 ± 29 | 1681 ± 13 | 2.21 | 1638 ± 15 |
| pyqsofitspec_line | 3525 ± 34 | 1639 ± 22 | 2.15 | 2030 ± 50 |
| qgfit | 2915 ± 170 | 1167 ± 22 | 2.50 | 2111 ± 28 |
| sheap_line | 3020 ± 27 | 1491 ± 15 | 2.02 | n/a |
| sdss_zline | 2374 | 1510 | 1.57 | 1273 |

## Summary

| quantity | QSOFITMORE | n tools | median ratio | mean log10 ratio | scatter dex |
|---|---:|---:|---:|---:|---:|
| Hβ | 3076.6 | 8 | 0.959 | -0.050 | 0.136 |
| [O III] 5007 | 1505.3 | 8 | 0.991 | -0.046 | 0.116 |
| Mg II | 2540.8 | 6 | 0.799 | -0.185 | 0.171 |
| Hβ/[O III] 5007 | 2.044 | 8 | 2.074 | -0.004 | 0.060 |

The scatter is the sample standard deviation of `log10(tool/QSOFITMORE)`; it is a
tool-to-tool model spread, not a measurement error.  Hβ/[O III] is the most
robust comparison because both lines are in the same QSOFITMORE complex, so their
Monte Carlo draws are correlated.
