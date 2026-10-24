# `configs/pyqsofitspec_line/default/`

Complete, executable configuration for `Tools/pyqsofitspec_line/`.  It is
passed to the container with `--config` and is the only place the line list
lives: the driver writes it to `qsopar2.fits`, which PyQSOFitSpec reads
(upstream `main.py` hard-codes the same table in Python).

The production defaults are **50 bootstrap realisations**, `kmpfit_maxiter =
1500`, and an NLR width anchored to a direct measurement of [O III] 5007 in
the same spectrum.  The full 55-draw run on `04592649654_z_0.5874` takes
about 10.5 min on one CPU (53 valid after the reduced-chi2 cut); see the tool
README for the measured runtime.  With the library-default kmpfit `xtol`, the
same run took 58 min because several realisations cycled to the iteration cap.

| key | meaning |
|---|---|
| `linemodel` | `skewnorm_model` (default) or `gauss_model`; selects the profile function in the vendored `fit_linemodel.py` |
| `nboot_fit` | bootstrap realisations. 50 = production; 5-10 = smoke test |
| `seed` | seed for `np.random.seed`; the bootstrap draws `N(f, err)` per pixel |
| `kmpfit_maxiter` | kmpfit iteration cap for the line fit. The kapteyn default is 200, which is **not enough** for the 8-component H-beta/[O III] complex (status 5 = "maximum number of iterations reached"). The driver retries a non-converged realisation once with 4x the cap |
| `kmpfit_ftol`, `kmpfit_xtol` | kmpfit convergence tolerances. Production uses `1e-8`/`1e-6`; the library default `xtol` is too strict for this 32-parameter complex and makes ~5 % of realisations cycle to status 5 with an otherwise good reduced chi2. `null` reverts to the library defaults |
| `nlr_width_anchor` | documentation block for the fixed NLR width (ln sigma = 0.0014, FWHM 989 km/s) measured from [O III] 5007; the driver records it in `run.json` |
| `max_line_red_chi2` | validity threshold on the per-complex reduced chi2 (default 15). Normal fits are 8.8-10.8; the cut rejects the rare converged-but-wrong local minimum (observed at rchi2 ~ 20 and ~ 227). Invalid realisations are excluded and counted |
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
| `ngauss` | number of Gaussians per component. The driver sums **all** blocks for `ngauss > 1`; the default is 1 everywhere |
| `sigval` | width prior/tie; see the three forms below |
| `voff` | half-width of the allowed velocity offset in `log(lambda)` |
| `iniskw` | initial skewness. `"0"` gives the package's default bounds (broad: +/-1000; narrow: +/-0.1); `"[lo, hi]"` sets explicit skew bounds |
| `fvalue` | initial amplitude / amplitude bounds, or `"OTHER*ratio"` for a fixed flux ratio |
| `kind` | **driver-only** declared component type (`broad` or `narrow`). It labels the output; it does not change the package fit. `QSOFit.line_prop` still uses its own `log10(sigma) > 0.0017` cut internally to select profile blocks |

### `sigval` forms (important)

* `"[min, max]"` — free width between the bounds; the initial value is the
  midpoint.  This is the normal form for a measured width.
* `"[value]"` — **fixed** width.  The package sets the bounds to
  `value*0.999 ... value*1.001`, i.e. the width is a configuration constant,
  not a fitted parameter.  Used here for the NLR anchor.
* `"OTHER*ratio"` — width **and velocity** are tied to `OTHER` (the centre is
  shifted by the rest-wavelength ratio).  Used for the [O III] 4959/5007
  doublet and for H-beta narrow.
* A bare number (no brackets) is **not** fixed: the package treats it as an
  initial value and applies its default bounds `[2.3e-4, 1.7e-3]`.  Use
  `"[value]"` if a genuinely fixed width is intended.

`fvalue` also sets the amplitude lower limit: for a positive value
`sc_down = 0.9 * fvalue`, so the small defaults (0.002-0.05) are lower
bounds, not scales.

Wavelengths are **vacuum** (PyQSOFitSpec divides the observed wavelength by
1+z and compares with these numbers).  They match the `pyqsofit_uv` line
list so the two tools can be compared directly.

## Production line model and ties

| complex | window [A] | components |
|---|---|---|
| MgII | 2700-2900 | `MgII_br` (free skew-normal, `[0.004, 0.05]`), `MgII_na` (width fixed at the NLR anchor) |
| Hb | 4640-5100 | `Hb_br` (free skew-normal, `[0.004, 0.012]`, skew `[-5, 5]`), `Hb_na` (tied to `OIII5007c`), `OIII4959c` (tied to `OIII5007c`: width/velocity, flux ratio 0.33), `OIII5007c` (width **fixed** at the NLR anchor), `OIII4959w` (tied to `OIII5007w`: width/velocity, flux ratio 0.33), `OIII5007w` (free wing, `[0.003, 0.008]`, skew `[-5, 5]`) |

The NLR width anchor is `ln sigma = 0.0014` (`FWHM = 989 km/s`), measured
independently from the [O III] 5007 line in this spectrum with a single
Gaussian plus a linear local continuum: `FWHM = 998 +/- 38 km/s`
(`sigma = 7.08 A`).  It is applied to `MgII_na`, `OIII5007c`, and through the
ties to `Hb_na` and `OIII4959c`.  This is the same physical choice as
GANDALF/S3Fit, which tie all NLR lines to a common kinematics; it removes the
old 848 km/s prior-bound artefact.

`OIII4959w` is tied to the **wing** (`OIII5007w`), not to the core; it
therefore inherits the wing width and velocity.

The free widths (`MgII_br`, `Hb_br`, `OIII5007w`) are checked after every
realisation and reported in `pyqsofitspec_lines.csv` (`width_mode`,
`pinned_at_bound`, `note`).  In the committed 53-valid run none of them is
pinned in the median; the fixed/tied components are marked
`width_mode = fixed` or `tied:...`, and `pinned_at_bound = false` because
their widths are not fitted parameters.  Two of the 53 realisations put the
[O III] wing at its lower 0.003 bound; the wing median is 0.00496.

## H-beta total definition (for the 18 % offset)

`pyqsofitspec_totals.csv` defines:

* `Hbeta = Hb_br + Hb_na`
* `Hbeta_broad = Hb_br`
* `Hbeta_narrow = Hb_na`
* `OIII5007 = OIII5007c + OIII5007w`
* `OIII5007core = OIII5007c`
* `MgII = MgII_br + MgII_na`

The H-beta total is **not** the same quantity as the GANDALF/S3Fit total:
PyQSOFitSpec fits one skew-normal broad component on its own Fe II continuum,
and the sibling tools use different continua, profile shapes and component
counts.  The data-minus-continuum integral in 4640-4940 A is ~4100
(1e-17 erg/s/cm2) with the PyQSOFitSpec continuum and ~2990 with the
PyQSOFit continuum; the model totals sit between those two continuum
definitions.  See the tool README for the measured ratios.

## Quick runs

```bash
# production (55 draws, ~11 min; 53 valid after the rchi2 cut)
bash Pipelines/run_pyqsofitspec_line_docker.sh \
  inputs/04592649654_z_0.5874/raw \
  outputs/04592649654_z_0.5874/pyqsofitspec_line --name 04592649654

# smoke test (5 realisations, a few minutes)
bash Pipelines/run_pyqsofitspec_line_docker.sh \
  inputs/04592649654_z_0.5874/raw /tmp/pyqsofitspec_smoke \
  --name 04592649654 --nboot 5

# matrix orchestrator (uses the prepared PyQSOFit spectrum)
.venv/bin/python pipeline/run_new_tools.py --only 04592649654_z_0.5874 \
  --tools pyqsofitspec_line --pyqsofitspec-nboot 50 --force
```
