# `gandalf_line` — native GANDALF v1.5 under GNU Data Language (Docker)

Native **GANDALF v1.5** (`Gas AND Absorption Line Fitting`, Sarzi et al. 2006)
emission-line fit for optical AGN/QSO and galaxy spectra.  The public IDL
source runs with **GNU Data Language (GDL) 1.0.4**, not with licensed IDL.

GANDALF fits the stellar continuum and the gas emission **simultaneously**:
the stellar templates are convolved with a stellar LOSVD, each emission line
is a Gaussian template, and the relative weights are solved linearly (BVLS)
at every nonlinear step.  Line velocities/dispersions are fitted with MPFIT;
tied multiplets and the `l-kind d#` flux ratios are handled by GANDALF itself.
`FOR_ERRORS=1` enables the second, fully nonlinear MPFIT pass that returns
formal 1-sigma covariance errors (there is no MCMC in GANDALF).

## Production validation and regression

| run | object | z | coverage | pPXF | result |
|---|---|---:|---|---|---|
| production | `spSpec-51908-0277-120` | 0.0858772 | H-beta, [O III], H-alpha, [N II], [S II] | **accepted**, V=72.54 +/- 6.50, sigma=79.87 +/- 9.80 km/s, chi2/dof=0.720, 5 templates | H-alpha 1390.85 +/- 16.86, H-beta 244.00 +/- 4.43 (1e-17) |
| regression | `04592649654` | 0.587413 | H-beta and [O III] only | **rejected**, chi2/dof=26.919, 1 template | H-beta 2950.82 +/- 33.57 total, [O III] 5007 1422.74 +/- 13.74; H-alpha/[N II] `not_covered` |

The production object is the public GANDALF v1.5 `SDSS_example` spectrum
`spSpec-51908-0277-120.fit`, stored unmodified in
`inputs/spSpec-51908-0277-120_z_0.0859/`.  It is a real low-z SDSS galaxy with
H-alpha and H-beta in range, so it exercises the full line table rather than
only the blue side.  Its complete outputs are in
`outputs/gandalf_line/spSpec-51908-0277-120_z_0.0859/`; the QSO regression is
in `outputs/gandalf_line/04592649654_z_0.5874/`.

## Build / run

```bash
bash pipeline/runners/build_images.sh gandalf_line
.venv/bin/python pipeline/run_new_tools.py \
  --only spSpec-51908-0277-120_z_0.0859 --tools gandalf_line --force
```

The matrix runner prepares `work/prepared/<key>/pyqsofit/spectrum.fits` and
calls `pipeline/runners/run_gandalf_line_docker.sh`.  A direct run is:

```bash
bash pipeline/runners/run_gandalf_line_docker.sh work/prepared/<key>/pyqsofit \
  outputs/<key>/gandalf_line <key>
```

Typical runtime on the delivered image: **59-71 s GDL / 68-82 s pipeline
wall** for the 3805-pixel low-z galaxy (final run: 70.6 s GDL, 76.5 s container
total, 81.7 s wall), and **30-34 s GDL / 39-43 s wall** for the 2610-pixel QSO
(final run: 29.9 s GDL, 34.7 s container total, 38.6 s wall).  A cold image
build is dominated by apt (about 2-3 minutes); a cached rebuild is a few
seconds.

## Input

Prepared `spectrum.fits` with HDU0 flux (cgs), HDU1 wavelength (A), HDU2
1-sigma error and header `z`.  Raw SDSS COADD tables and classic SDSS
`spSpec` files are accepted too.  `pipeline/prepare_inputs.py` now reads the
classic `spSpec` primary 4 x npix image (row 0 flux, row 2 noise, log10
wavelength grid) and stages the PyQSOFit layout without changing the data;
zero-noise pixels remain explicit bad pixels.

The tool converts the spectrum to the rest frame and resamples it onto the
BC03/Tremonti04 log10 grid (`dlog=1e-4`, 3400-9200 A) in `1e-17` flux units.
If H-alpha is at or just beyond the red edge, the fit is truncated before
H-alpha so that its blue wing cannot bias the continuum.  Sky-line masks are
converted from observed to rest-frame wavelengths.

The instrumental LSF is a single 61.5 km/s Gaussian (`int_disp_kms`), taken
from GANDALF's official SDSS example and matched to the distributed
BC03/Tremonti04 templates.  It is not a per-pixel SDSS LSF; see Caveats.

## Output

`outputs/<source>/gandalf_line/`:

| file | contents |
|---|---|
| `gandalf_lines.csv` | standardised line table (required H-beta, [O III] 5007, H-alpha and [N II] 6584 rows first; other measured and derived lines follow) |
| `line_yield_summary.txt` | human-readable line yield (flux, error, sigma, S/N, status, method, notes) |
| `gandalf_fit.png/pdf` | observed, GANDALF total, stellar continuum, gas emission, zoom and residual |
| `gandalf_uncertainty.png/pdf` | formal MPFIT flux/sigma errors and S/N |
| `gandalf_fit.fits` | galaxy, best fit, emission, residual, good pixels, weights, stellar kinematics, gas solution, errors, per-line templates |
| `gandalf_input.fits` | exact rest-frame grid, mask and templates passed to GDL |
| `gandalf_model.csv` | wave, flux, model, stellar, emission, residual, error |
| `gandalf_lines_raw.csv` | raw GANDALF main-line solution (before standardisation) |
| `gandalf_meta.txt`, `gandalf_run.log`, `gandalf_batch.gdl` | provenance |
| `run.json` | method, grid, input LSF, PPXF block with errors and acceptance cuts, stellar kinematics, measurements, line yield, chi2, runtime, limitations |

Columns in `gandalf_lines.csv` include `flux_1e17`, `flux_err_1e17`,
`flux_erg_s_cm2`, Gaussian `amplitude`, `velocity_kms`, `sigma_kms`
(intrinsic, instrumental 61.5 km/s subtracted), `sigma_obs_kms`, `snr`,
`detected`, `status` (`ok`, `weak`, `not_covered`, `not_detected`) and the
error `method` (`mpfit_covariance` or `amplitude_error_scaled` for lines
whose kinematics are tied).

Kinematic errors of tied lines are inherited from their parent line, not
written as zero.  Multiplet satellites ([O II] 3726, [O III] 4959,
[N II] 6548, [S II] 6730) are added from the GANDALF `d#` ratio and carry
`method = gandalf_gdl_multiplet_ratio`; they are derived, not independent
measurements.

## Config

`configs/gandalf_line/default/`:

* `emission_lines_setup` — rest-frame line list, multiplet ties and flux
  ratios.  All lines start with `action=m`; the driver tests coverage and
  switches in-window lines to `f` before the simultaneous fit.
* `config.json` — grid, templates, MPFIT/PPXF controls, mask widths,
  acceptance cuts and the fixed stellar-LOSVD fallback.  The production pPXF
  settings follow GANDALF's `gandalf_SDSS.pro` (`degree=0`, `mdegree=3`,
  200 km/s emission mask).  pPXF is accepted only if
  `30 < sigma < 800 km/s`, `|V| < 500 km/s`, at least 2 nonzero templates,
  `chi2/dof <= 3` and `sigma/sigma_err >= 3`.

The default setup ties narrow H-beta to [O III] 5007, ties [N II] 6584 and
[S II] 6716 to H-alpha, and adds independent broad H-beta and broad H-alpha
Gaussians (empirical BLR proxies).  H-alpha/[N II]/[S II] rows are emitted as
`not_covered` when the spectrum does not reach them.

## Stellar kinematics and pPXF status

The canonical GANDALF workflow uses pPXF to obtain the stellar V and sigma
before the gas fit.  This tool attempts pPXF (IDL pPXF 2018 under GDL) with a
200 km/s emission mask, an additive polynomial of degree 0 and a
multiplicative polynomial of degree 3.

**Low-z galaxy: pPXF accepted and scientifically usable.**  V = 72.54 +/-
6.50 km/s, sigma = 79.87 +/- 9.80 km/s, chi2/dof = 0.720, 5 nonzero templates,
3439 good pixels.  The solution is not at a bound.  The earlier
`degree=8`/2000 km/s-mask configuration gave sigma = 62.85 km/s on the same
spectrum; that 27% spread is a template/mask/polynomial systematic.  A
conservative quote is sigma = 80 +/- 10 (formal) +/- 15 (systematic) km/s.

**QSO `04592649654`: pPXF rejected.**  V = -190.25 km/s, sigma = 365.81 km/s,
1 nonzero template, chi2/dof = 26.919.  Exact message:

```text
rejected: nz<min chi2/dof>max (V=-190.248 km/s, sigma=365.811 km/s,
sigma_err=11.059 km/s, nz=1, chi2/dof=26.919)
```

The previous 8/2000 setup instead hit the hard sigma=1000 km/s bound
(V=556.8 km/s, 4 templates, chi2/dof=2.184).  Both results show that the
AGN-dominated QSO continuum has no measurable host absorption.  The templates
are then convolved with a fixed 300 km/s LOSVD; `run.json` records
`stellar_kinematics.source = fixed_fallback`, and the gas fit is still native
GANDALF.  No stellar sigma is fabricated.

## Production line results (low-z)

`spSpec-51908-0277-120`, z=0.0858772, rest coverage 3522.7-8458.2 A,
residual chi2_nu=0.847.  Fluxes in `1e-17 erg s^-1 cm^-2`:

| line | component | flux | error | sigma (km/s) | S/N |
|---|---|---:|---:|---:|---:|
| H-beta | narrow (tied to [O III]) | 244.00 | 4.43 | 89.99 | 55.1 |
| H-beta | total (broad undetected) | 244.00 | 4.43 | - | 55.1 |
| [O III] 4959 | derived, 0.35 x 5007 | 27.88 | 1.24 | 89.99 | 22.5 |
| [O III] 5007 | narrow | 79.66 | 3.54 | 89.99 | 22.5 |
| H-alpha | narrow | 1390.85 | 16.86 | 81.90 | 82.5 |
| [N II] 6548 | derived, 0.34 x 6584 | 198.24 | 2.22 | 81.90 | 89.2 |
| [N II] 6584 | narrow (tied to H-alpha) | 583.07 | 6.54 | 81.90 | 89.2 |
| [S II] 6716 | narrow (tied to H-alpha) | 218.81 | 3.43 | 81.90 | 63.8 |
| [S II] 6730 | derived, 0.75 x 6716 | 164.11 | 2.57 | 81.90 | 63.8 |

The broad H-alpha component is weak (42.79 +/- 18.63, S/N=2.3) and broad
H-beta is undetected.  The galaxy is star-forming; the broad Gaussians should
not be read as BLR measurements.  H-alpha/H-beta = 5.70, [N II]/H-alpha =
0.419, [O III] 5007/H-beta = 0.327.

## Caveats

* GDL is IDL-compatible but not identical; the tested batch path and the
  exact compatibility fixes are documented in `docs/GANDALF_ASSESSMENT.md`.
* GANDALF errors are MPFIT covariance errors, not MCMC posterior errors.  The
  local GANDALF patch fixes the MC seed, so free-line flux errors are now
  reproducible; it does not make them Bayesian.
* The 61.5 km/s LSF is a single Gaussian.  Real SDSS resolution varies with
  wavelength; intrinsic sigma below ~80 km/s is LSF-dominated.  This is the
  main systematic for the low-z gas widths.
* pPXF sigma is configuration-sensitive at the ~20% level; the production
  value is 79.87 km/s.  It is usable as a stellar prior, not as a precise
  stellar-dispersion measurement.
* The broad H-beta and broad H-alpha components are empirical Gaussians, not
  a physical BLR profile.
* GANDALF v1.5 refuses `REDDENING` together with `MDEGREE>0`; no reddening
  correction is applied.
* Line fluxes are integrated Gaussian fluxes, not aperture photometry.
  Multiplet satellites are derived from the GANDALF `d#` ratios.
* For `04592649654`, H-alpha and [N II] are outside the observed/rest-frame
  coverage; they are `not_covered`, not non-detections.

Third-party licences and attribution: `THIRD_PARTY_LICENSES.md`.
