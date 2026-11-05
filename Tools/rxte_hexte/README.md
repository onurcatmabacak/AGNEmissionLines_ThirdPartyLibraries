# rxte_hexte — RXTE/HEXTE 15-250 keV hard X-ray

HEXTE's official HEASARC `stdprod` products ship the source spectrum, the
background model, and the **official ARF and RMF** in the same directory as the
PCA files. That makes the 15-250 keV band reachable without CALDB, without a
reduction, and without NuSTARDAS.

Model: `tbabs*cutoffpl + zgauss` fitted to both clusters simultaneously with the
C-statistic; the exponential cutoff is left free and then frozen at 1e3 keV, so
the C-statistic difference measures whether the high-energy cutoff is required.
