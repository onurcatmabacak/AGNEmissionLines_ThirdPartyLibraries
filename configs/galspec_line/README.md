# `configs/galspec_line/default/`

One JSON file, `config.json`, drives the GalSpec adapter.  It is a complete
tool configuration, not a tuning grid.

| block | contents |
|---|---|
| `input` | redshift/unit autodetection, vacuum-to-air conversion, rest-frame `(1+z)` flux correction, optional SDSS `AND_MASK` and Galactic dereddening |
| `instrument` | `WRESL`-based SDSS resolution, subtracted in quadrature for the `fwhm_intrinsic_kms` column |
| `continuum` | local linear continuum sidebands, and the park2022 Fe II template (GalSpec `IronTemplate_new`) |
| `main_window` | rest-frame H-beta + [O III] 4959,5007 window, component labels, Gaussian bounds, initial guesses, integration/profile windows, and the 4959/5007 amplitude ratio (2.98) |
| `aux_windows` | [O II] 3726/3728, [Ne III] 3869/3967 and [S II] 4068/4076, each with a linear continuum and tied narrow Gaussians |
| `coverage_lines` | H-alpha/[N II]/[S II] 6716/6731 rows emitted as `not_covered` when the spectrum does not reach them |
| `fitter` | `trf` (default), `levmar` or `dogbox`; maximum iterations |
| `errors` | per-pixel error floor: fraction of the sideband continuum + absolute term |
| `mcmc` | `emcee` walkers/steps/burn-in, seed, initial jitter, posterior sample count |
| `nested` | optional `dynesty` controls (`nlive`, `rwalk`, `multi`, `dlogz`); disabled by default |
| `detection` | S/N threshold for the `detected` flag |
| `output` | figure DPI/PDF and saved MCMC sample count |

## Main-window model

```text
linear local continuum
+ park2022 Fe II template (GalSpec IronTemplate_new)
+ H-beta narrow  Gaussian  (sigma 100-700 km/s)
+ H-beta broad   Gaussian  (sigma 700-5000 km/s)
+ [O III] 5007 narrow + wing
+ [O III] 4959 narrow + wing   (amplitude/kinematics tied to 5007, ratio 2.98)
```

The fit is performed on the 4720-5150 A rest-frame window.  `emcee` samples
the 17 free parameters; the line fluxes, FWHM and velocities in
`galspec_lines.csv` are posterior medians with 16th/84th-percentile errors.
The LSQ solution is reported in `run.json` and is used as the starting point.

## Auxiliary windows

The auxiliary lines are fitted independently with a linear continuum and one
Gaussian per line; multiplet members share `dv` and `sigma`.  Their errors are
linear covariance errors, not MCMC.  They are useful diagnostics, not part of
the H-beta/[O III] posterior.

## Error floor

`errors.floor_frac_of_continuum = 0.02` adds 2 per cent of the local sideband
continuum in quadrature to the calibrated SDSS error.  The raw and floored
chi-square values are both written to `run.json`
(`fit.main.chi2nu_raw`, `fit.main.chi2nu_floor`).  Set the fraction to `0` to
use the calibrated SDSS errors only.

## Adapting

For another instrument, update `instrument`, the main/aux windows, and the
line component bounds.  Do not use a different vacuum/air convention without
changing `input.vacuum_to_air`; GalSpec's optical line dictionary is in air
wavelengths.  For a spectrum that covers H-alpha, add a new main or auxiliary
window rather than moving the existing H-beta window.
