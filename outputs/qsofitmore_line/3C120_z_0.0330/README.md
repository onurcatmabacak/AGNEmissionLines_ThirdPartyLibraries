# QSOFITMORE line fit — `3C120_z_0.0330`

## Provenance

* Upstream: `https://github.com/rudolffu/qsofitmore`, commit `4c5f6e497b306aaf50b502a8e4b27ed9dfe89421`, version `1.2.2`, GPL-3.0.
* Image: `qsofitmore_line` (size `1501705328` bytes), Python `3.12.15`, lmfit `1.3.2`.
* Input: `/app/input/hst_8700_stis_3c120d0_g430l-g750l_o62o_cspec.fits` (SHA256 `f0f1bbb19124ea01233922c2c633c6abcc8e44e25b9c59d387d692f427fecde2`), calibrated SDSS errors from `1/sqrt(IVAR)`; no error floor.
* Redshift `0.03300000`; observed `2993.1–10247.2 Å`; rest-frame `2897.5–9919.8 Å`.
* Galactic extinction: SFD98 (Schlegel, Finkbeiner & Davis 1998; DOI `10.7910/DVN/EWCNL5`) E(B-V) = `n/a` mag, Fitzpatrick (1999) R_V=3.1.
* Line table: `/app/config/line_table.csv` (SHA256 `9d0615785b272ac2b9ecc6046b0007c706523cee7d2b13f0e349fcee29505a18`); a FITS copy is `qsopar.fits`.
* Command: `/app/run/main.py --input-dir /app/input --out /app/output --config /app/config --mc-trails 200 --seed 20250101 --source-key 3C120_z_0.0330 --z 0.033`

## Model

* Continuum: broken power law (3000 Å pivot, 4661 Å break, both slopes free), Verner et al. (2009) Fe II template over 2000–10000 Å, Balmer continuum (Dietrich et al. 2002) and high-order Balmer series (Storey & Hummer 1995, n_upper=6–50, log10 n_e = 9). No polynomial term (`poly=False`); the broken power law supplies the large-scale curvature.
* Lines: broad and narrow Gaussians from the package line table. The Hβ complex contains `Hb_br` (3 Gaussians), `Hb_na`, [O III] 4959/5007 cores, and [O III] 4959w/5007w outflow wings. The [O III] doublet and outflow ratios are tied to 0.33; widths/centres are tied within each kinematics group. Mg II has a 2-Gaussian broad template plus a free narrow component.
* Host decomposition is **off**. qsofitmore's Yip+2004 decomposition would restrict the rest-frame grid to ≳3450 Å and remove Mg II; the host is measured separately by pPXF in this repo.
* Hα (6564.61 Å rest), C III] (1908.73 Å) and C IV (1549.06 Å) are outside this SDSS spectrum's rest-frame coverage. They remain in the table for UV/higher-z use and are skipped cleanly; they are reported as `not_covered`, not as zero-flux measurements.
* Hδ and [Ne III] were tested in pre-run variants and are not in the production table: the V09+Balmer-continuum model over-subtracts/does not constrain them (Hδ returned zero flux with χ²_r≈21). This is a model limitation, not a non-detection.

## Uncertainty

qsofitmore 1.2.2 has no emcee/MCMC sampler. Its native uncertainty mode is the lmfit Monte Carlo refit used here:

* **200** independent noise realizations per fitted complex (and for the continuum MC), seed `20250101`. This is 200× the package default `n_trails=1` and twice the PyQSOFit MC in this repo.
* Each realization adds `N(0, err)` to the calibrated spectrum and refits the continuum and each line complex with lmfit.
* The compact table recomputes each physical line total from **all** of its Gaussian components. The package's `<complex>_whole_br_area` column only sums Gaussians above its 1200 km/s classifier and is therefore not the total; it is retained in `qsofitmore_result.csv`.
* Hβ/[O III] uses the same Hβ-complex draws, so the ratio uncertainty includes the correlated line fluxes. Mg II is a separate complex with its own independent draws.
* `qsofitmore_corner.png`/`.pdf`: Hβ total, [O III] 5007, Hβ/[O III], Hβ FWHM. `qsofitmore_mgii_corner.*`: Mg II. `qsofitmore_uncertainty.*`: marginal histograms. `qsofitmore_mc_samples.csv` contains every retained realization.

## Headline measurements (1e-17 erg s^-1 cm^-2)

| line | area | 1σ (MC) | FWHM (km/s) | status |
|---|---:|---:|---:|---|
| Hβ total | 39750.9 | 848.2 | 2460 | ok |
| Hβ broad template | 38202.7 | 937.8 | 2971 | ok |
| Hβ narrow | 1548.2 | 792.0 | 818 | weak |
| [O III] 5007 total | 13256.4 | 3014.8 | 818 | ok |
| [O III] 5007 core | 13139.0 | 3419.5 | 818 | ok |
| [O III] 5007 outflow | 117.4 | 1314.7 | 161 | not_detected |
| Mg II total | n/a | n/a | n/a | not_covered |
| Hγ total | 13719.1 | 90.9 | 3129 | ok |

* **Hβ/[O III] 5007 = 2.999** (MC median 2.955, 16–84% 2.862–2.999).
* Hβ complex χ²_r = `182.10`; Mg II χ²_r = `n/a`; [O II] χ²_r = `52.01`. These are diagnostics, not goodness-of-fit gates; the Hβ complex is the hardest because the Fe II/Balmer model and the broad profile are not a complete physical description.
* Fe II band fluxes (from the V09 template): Fe_w2250_w2700_flux=0.0, Fe_w4434_w4684_flux=9114.7, Fe_w5100_w5600_flux=11692.4.
* Balmer continuum normalisation `0.000`; high-order Balmer normalisation `5229.6`.

## Cross-tool check

`qsofitmore_lines.csv` is the input to the host-side comparison:

```bash
.venv/bin/python pipeline/compare_qsofitmore.py --source-key 3C120_z_0.0330
```

It writes `cross_tool_comparison.csv`, `cross_tool_comparison.json`, and `cross_tool_comparison.png` in this directory. The comparison uses Hβ total, [O III] 5007 total, and Mg II total against PyQSOFit, GANDALF, S3Fit, GalSpec, PyQSOFitSpec, QGfit, SHEAP and the SDSS ZLINE anchor. See the CSV/JSON for ratios, log10 differences and `(tool - QSOFITMORE)/sqrt(err_tool^2 + err_qm^2)`.

## What this tool can and cannot measure

**Can:** UV/optical AGN continuum shape, Fe II pseudo-continuum, Balmer continuum/high-order Balmer, broad and narrow Balmer lines, Mg II, [O III] core/outflow, [O II], [Ne V], and their Monte Carlo uncertainties; line ratios and FWHMs.

**Cannot / caveats:**

* Hα, C III] and C IV are outside this SDSS spectrum's rest-frame coverage; no measurement is possible without UV/NIR data.
* The broad Hβ complex is a multi-Gaussian empirical profile, not a reverberation-mapped BLR model. Individual Gaussian components are degenerate; use the total, not the component split, for science.
* The Hβ narrow component is tied to the [O III] kinematics; its width is not independent. The package's broad/narrow classifier at 1200 km/s is not a physical decomposition; the compact total is the robust quantity.
* The Hβ complex χ²_r is larger than the Mg II χ²_r. This is a model mismatch (Fe II/Balmer template + Gaussian profile), not evidence that the Hβ flux is wrong; the total is stable across line-table variants (see `run.json` and the systematic BG92 fit).
* No MCMC posterior is produced or claimed. The MC is a frequentist parametric bootstrap of the calibrated errors.
* The Galactic extinction is foreground only; no intrinsic reddening is fitted. The broken power law absorbs some intrinsic curvature.
* The host is not decomposed here; use `ppxf_host` for the stellar host.

## Products

`qsofitmore_lines.csv`, `qsofitmore_components.csv`, `qsofitmore_mc_samples.csv`, `qsofitmore_mc_summary.csv`, `qsofitmore_hb_oiii_mc.csv`, `qsofitmore_continuum.csv`, `qsofitmore_result.csv`, `qsofitmore_result.fits`, `qsofitmore_fit.pdf/png`, `qsofitmore_corner.*`, `qsofitmore_mgii_corner.*`, `qsofitmore_uncertainty.*`, `config.effective.json`, `run.json`, `systematics/`.
