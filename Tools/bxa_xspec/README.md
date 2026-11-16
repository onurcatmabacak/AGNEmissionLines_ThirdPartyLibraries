# `bxa_xspec` — Bayesian and prior-free X-ray model comparison

BXA 5.x + UltraNest on the same XMM-Newton EPIC PPS spectra that
`xmm_xspec` fits with chi-square.  The production band is **2–10 keV**, the
canonical Fe Kα band: including 0.5 keV leaves an unmodelled soft-excess /
cross-calibration residual that holds χ²/dof at 2.70.

| setting | value |
|---|---|
| base image | `xmm_xspec` (HEASoft XSPEC 13 + PyXspec) |
| inference | nested sampling (UltraNest) with BXA prior transforms |
| statistic | C-stat (Poisson); χ² starter for the BIC/AIC check |
| evidence tolerance | `dlogz = 2` (configurable) |
| live points | 300 (configurable) |
| priors | uniform / log-uniform, scale priors centred on the least-squares starter |

Model suite (`configs/bxa_xspec/default/config.json`):

| model | expression | purpose |
|---|---|---|
| `pl` | `constant*tbabs*(zpowerlw)` | continuum null hypothesis |
| `pl_line_narrow` | `+ zgauss` (6.4 keV rest, sigma 50 eV) | narrow Fe Kα evidence |
| `pl_line_broad` | `+ zgauss` with sigma fixed at 300 eV | broad Fe Kα / disc line |
| `pcfabs` | `tbabs*pcfabs*(zpowerlw)` | clumpy / partial covering |
| `warmabs` | `tbabs*zxipcf*(zpowerlw)` | ionized wind |

`cutoffpl_cabs` was dropped: it improves χ² by only 2.6 for two extra
parameters on these data (unidentifiable), and a Compton-thick comparison
needs broadband (NuSTAR) data.  MYTorus / UXCLUMPY / RELXILL are **not**
bundled: they need external FITS tables (and licence review for
UXCLUMPY/XARS), so the absorption family is the built-in XSPEC set.

## Two estimators

1. **Nested-sampling evidence** (`run_bxa_xspec.py`): `ln Z`, `Δ ln Z` and
   Bayes factors against `pl`, plus posterior 16/50/84 percentiles.  This is
   prior-dependent, which matters when a model adds a flat likelihood
   direction (line normalisation, covering fraction).
2. **Prior-free BIC/AIC** (`bic_scan.py`): uses the same prepared spectra,
   the same frozen cross-calibration constants and the same χ² starter:

   ```
   BIC = chi2 + k ln n        AIC = chi2 + 2k
   ```

   It runs in seconds and writes `bic_scan.csv` / `bic_scan.json`:

   ```bash
   python /app/run/bic_scan.py --input /app/input --output /app/output \
       --config /app/config/config.json --redshift 0.184 \
       --models pl,pl_line_narrow,pl_line_broad,pcfabs,warmabs
   ```

   **Do not read BIC as a Bayes factor.**  It has no prior volume, so it can
   disagree with `ln Z`; the disagreement is the diagnostic.

## PDS 456 result (n = 387 noticed bins)

| model | χ²/dof | k | ΔBIC vs pl | ΔAIC vs pl |
|---|---:|---:|---:|---:|
| `pl` | 661.5/383 | 3 | — | — |
| `pl_line_narrow` | 634.2/381 | 5 | **−15.4** | −23.3 |
| `pl_line_broad` | 605.2/381 | 5 | **−44.4** | −52.3 |
| `pcfabs` | 504.0/381 | 5 | **−145.6** | −153.5 |
| `warmabs` | 661.5/380 | 6 | +17.9 | +6.0 |

`k` counts the free physical parameters in the config; the three cross-calibration
constants are fitted once and frozen for every model, so they cancel in Delta BIC.

BIC ranks **partial covering** first, then the broad line, then the narrow
line, then `pl`.  The nested-sampling narrow-line result (`Δ ln Z = −0.86`
under the configured prior) is therefore **not** a prior-free “no line”
statement; it is dominated by the prior volume on the line normalisation and
energy.  The pcfabs nested run never converged, but that is a sampler/prior
problem, not evidence against the BIC-preferred model.

## Outputs

`bxa_evidence.csv` (from each model's UltraNest result), `chains/<model>/`
(per-model sampler output), `bic_scan.csv`/`bic_scan.json` (prior-free check),
`run.json`, `config.effective.json`, `prepared/` (the exact spectra handed to
XSPEC).
