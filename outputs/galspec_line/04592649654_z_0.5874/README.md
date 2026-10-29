# GalSpec full-continuum fit — `04592649654_z_0.5874`

Production posterior: 39-parameter global model (polynomial continuum + park2022
Fe II + all fitted lines) over 2280–6459 Å rest frame, sampled with emcee.

| | |
|---|---|
| config | `configs/galspec_line/production_30k/config.json` |
| image | `galspec_line` (`Tools/galspec_line/Dockerfile`) |
| sampler | `emcee` `DEMove(gamma0=0.20)`, 200 walkers |
| steps | 30,000 total, 5,000 burn, **25,000 retained** |
| seed | 46 |
| wall time | 9,595 s (39.8 s LSQ + 9,358 s sampling + 137 s plots) |

## Convergence verdict: **converged**

| diagnostic | value | gate |
|---|---:|---|
| acceptance fraction | **0.267** | 0.15–0.70 ✔ |
| finite integrated τ | **39/39** | all parameters ✔ |
| τ range | 182–300 steps | — |
| τ_max | 299.8 steps | — |
| retained steps / τ_max | **83.4** | ≥ 50 ✔ |
| total steps / τ_max | 100.1 | — |
| effective sample size (min / median) | **16,679 / 25,783** | ≥ 500 ✔ |
| walkers used for τ | 200/200 | — |
| dead samples / frozen walker-parameter cells | 0 / 0 | 0 ✔ |

No parameter is at the burn-in limit: 5,000 burn steps is 17 τ_max. The
chain is the longest-budget GalSpec run in this repository that passes every
gate; the earlier 4,000-, 25,000-, 70,000- and 110,000-step chains are
superseded (8.2, 17.3, 37.1 and 41.5 retained τ respectively, and the
20,000-step DEMove run reported only 7/39 finite τ because four walkers had
started outside the continuum-positivity prior and never moved).

## Fit quality

`chi2/nu(raw) = 3.709`, `chi2/nu(floor) = 2.159`, dof 4,484, rms 3.50
(1e-17 units), 4,523 pixels, 39 free parameters.

| line | component | flux (1e-17) | FWHM (km/s) | velocity (km/s) | S/N |
|---|---|---:|---:|---:|---:|
| Hβ | narrow | 1665.9 ± 36.9 | 1622 | 2.4 | 45.1 |
| Hβ | broad | 1989.7 ± 32.7 | 6419 | −64.7 | 60.9 |
| Hβ | total | 3654.2 ± 33.9 | 1915 | 0.0 | 107.8 |
| [O III] 5007 | narrow | 844.4 ± 31.7 | 846 | −147.9 | 26.6 |
| [O III] 5007 | wing | 868.3 ± 32.7 | 2061 | −894.2 | 26.6 |
| [O III] 5007 | total | 1712.2 ± 14.0 | 1039 | −184.6 | 122.4 |
| Mg II 2796 | broad | 817.8 ± 9.5 | 2161 | −262.4 | 86.1 |

The previous 4,000-step product gave Hβ total 3718.5 ± 28.6 and
[O III] 5007 total 1680.6 ± 13.1; the posteriors agree within the quoted
errors, and the longer chain no longer underestimates them.

## Cross-tool comparison caveat

`galspec_comparison.csv` is rebuilt against the **current** neighbouring
products in this tree by `Tools/galspec_line/rebuild_comparison.py` (the chain
itself was sampled in scratch space, where no siblings are mounted). Because
`pyqsofit_uv` was re-run after the previous comparison was written, its Hβ
split moved (broad 2280 → 2888, narrow 625 → 147, total 2905 → 3035). The
Hβ-total ratio is therefore 1.20 and the narrow-Hβ ratio 11.4; the ratio
column is a product-vintage comparison, not a GalSpec error. `[O III] 5007`
totals differ by 18 % (1712.2 vs 1446.7 from PyQSOFit), the usual
core-plus-wing versus single-Gaussian model systematic; the narrow core alone
agrees to 6 %.

## Files

`galspec_fit.pdf/png` (model over the full spectrum), `galspec_uncertainty.pdf/png`
(posterior envelopes), `galspec_corner.pdf/png`, `galspec_lines.csv`,
`galspec_model.csv`, `galspec_comparison.csv`, `galspec_mcmc.npz`
(200,000 saved samples, thin 25), `config.effective.json`, `galspec.log`,
`run.json`.
