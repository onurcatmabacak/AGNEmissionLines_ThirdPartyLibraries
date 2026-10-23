# `configs/pyqsofitspec_line/default/`

Complete, executable configuration for `Tools/pyqsofitspec_line/`.  It is
passed to the container with `--config` and is the only place the line list
lives: the driver writes it to `qsopar2.fits`, which PyQSOFitSpec reads
(upstream `main.py` hard-codes the same table in Python).

| key | meaning |
|---|---|
| `linemodel` | `skewnorm_model` (default) or `gauss_model`; selects the profile function in the vendored `fit_linemodel.py` |
| `nboot_fit` | bootstrap realisations. 10 = smoke size; use 50-100 for science |
| `seed` | seed for `np.random.seed`; the bootstrap draws `N(f, err)` per pixel |
| `error_floor_frac` | adds `sqrt(err^2 + (f*flux)^2)`; 0 keeps the calibrated SDSS `IVAR` errors |
| `obs_wave_range` | observed-frame cut before fitting [A]; default 3800-9200 (SDSS) |
| `flux_unit` | `auto` detects cgs vs `1e-17` from `BUNIT`/layout |
| `nsmooth`, `reject_badpix`, `Fe_uv_op`, `poly`, `BC`, `rej_abs`, `decomposition_host` | forwarded to `QSOFit.Fit` unchanged (host decomposition needs the PCA templates and is off) |
| `comparison.totals` | component groups summed per realisation for `pyqsofitspec_totals.csv` / the cross-tool table |
| `comparison.corner` | totals shown in the corner plot |
| `line_table` | rows of the PyQSOFitSpec `qsopar2.fits` table (see below) |

## `line_table` columns

| column | meaning |
|---|---|
| `lambda` | vacuum rest wavelength [A] |
| `compname` | fitting complex; rows sharing it are fitted simultaneously in `[minwav, maxwav]` |
| `minwav`, `maxwav` | rest-frame window of the complex [A] |
| `linename` | unique component name (also the key used in every output table) |
| `ngauss` | number of Gaussians per component |
| `sigval` | initial `log10(sigma)`, `"[min, max]"` bounds, or `"OTHER*ratio"` to tie the width and the velocity shift to another component |
| `voff` | half-width of the allowed velocity offset in `log(lambda)` |
| `iniskw` | initial skewness (`"0"` for the narrow components) |
| `fvalue` | initial amplitude / amplitude bounds, or `"OTHER*ratio"` for a fixed flux ratio |

Note that `fvalue` also sets the amplitude lower limit: for a positive value
`sc_down = 0.9 * fvalue`, so the small defaults (0.002-0.05) are lower
bounds, not scales.

Wavelengths are **vacuum** (PyQSOFitSpec divides the observed wavelength by
1+z and compares with these numbers).  They match the `pyqsofit_uv` line
list so the two tools can be compared directly.

## Ties used by the default table

* `OIII4959c` is tied to `OIII5007c` (`sigval` and `fvalue`), giving the
  physical 1:2.98 doublet ratio and identical kinematics.
* `OIII4959w` is tied to `OIII5007w` the same way.
* No tie between H-beta and [O III] kinematics: the NLR lines are resolved,
  the broad H-beta is not tied to them.

`Hb_na` and `OIII5007c` reach the `1.2e-3` upper bound (FWHM 848 km/s); the
driver flags that in `pyqsofitspec_lines.csv` (`note`).  Widen the bound only
if you also accept that the "narrow" component may become a broad-line
component (the 0.0017 classification threshold in `QSOFit.line_prop` is the
hard boundary).
