# `bxa_xspec` — Bayesian X-ray evidence comparison

BXA 5.x + UltraNest on the same XMM-Newton EPIC PPS spectra and 0.5-10 keV
band that `xmm_xspec` fits with chi-square, so the two products are directly
comparable.

| setting | value |
|---|---|
| base image | `xmm_xspec` (HEASoft XSPEC 13 + PyXspec) |
| inference | nested sampling (UltraNest) with BXA prior transforms |
| statistic | C-stat (Poisson) |
| evidence tolerance | `dlogz = 0.5` |
| live points | 500 (configurable) |
| priors | uniform / log-uniform, centred on the least-squares starter |

Model suite (`configs/bxa_xspec/default/config.json`):

| model | expression | purpose |
|---|---|---|
| `pl` | `constant*tbabs*(zpowerlw)` | continuum null hypothesis |
| `pl_line` | `+ zgauss` (6.4 keV rest, sigma 50 eV) | narrow Fe Kα evidence |
| `pl_line_wide` | `+ zgauss` with free sigma (50-800 eV) | broad Fe Kα / disc line |
| `warmabs` | `tbabs*zxipcf*(zpowerlw)` | ionized wind |
| `pcfabs` | `tbabs*pcfabs*(zpowerlw)` | clumpy/partial covering |
| `cutoffpl_cabs` | `tbabs*cabs*(cutoffpl)` | Compton-thick absorption |

Reported: `ln Z` per model, `Δ ln Z` and Bayes factor against the absorbed
power law, and posterior 16/50/84 percentiles for every free parameter.

MYTorus / UXCLUMPY / RELXILL are **not** bundled: they need external FITS
table models (and licence review for UXCLUMPY/XARS), so the absorption family
is the built-in XSPEC set.  That keeps the comparison reproducible offline and
is stated in every `run.json`.
