# `gandalf_line` — native GANDALF v1.5 under GNU Data Language (Docker)

Native **GANDALF v1.5** (`Gas AND Absorption Line Fitting`, Sarzi et al. 2006)
emission-line fit for optical AGN/QSO spectra.  The public IDL source is run
with **GNU Data Language (GDL) 1.0.4**, not with licensed IDL.

GANDALF fits the stellar continuum and the gas emission **simultaneously**:
the stellar templates are convolved with a stellar LOSVD, each emission line
is a Gaussian template, and the relative weights are solved linearly (BVLS)
at every nonlinear step.  Line velocities/dispersions are fitted with MPFIT;
tied multiplets and the `l-kind d#` flux ratios are handled by GANDALF itself.
`FOR_ERRORS=1` enables the second, fully nonlinear MPFIT pass that returns
formal 1-sigma covariance errors (there is no MCMC in GANDALF).

## Build / run

```bash
bash Pipelines/build_images.sh gandalf_line
.venv/bin/python pipeline/run_new_tools.py \
  --only 04592649654_z_0.5874 --tools gandalf_line --force
```

The matrix runner prepares `work/prepared/<key>/pyqsofit/spectrum.fits` and
calls `Pipelines/run_gandalf_line_docker.sh`.  A direct run is:

```bash
bash Pipelines/run_gandalf_line_docker.sh work/prepared/<key>/pyqsofit \
  outputs/<key>/gandalf_line <key>
```

## Input

Prepared `spectrum.fits` with HDU0 flux (cgs), HDU1 wavelength (A), HDU2
1-sigma error and header `z`.  Raw SDSS `spSpec` files and SDSS COADD tables
are accepted too.

The tool converts the spectrum to the rest frame and resamples it onto the
BC03/Tremonti04 log10 grid (`dlog=1e-4`, 3400-9200 A) in `1e-17` flux units.
If H-alpha is at or just beyond the red edge, the fit is truncated before
H-alpha so that its blue wing cannot bias the continuum.  Sky-line masks are
converted from observed to rest-frame wavelengths.

## Output

`outputs/<source>/gandalf_line/`:

| file | contents |
|---|---|
| `gandalf_lines.csv` | standardised line table (H-beta, [O III] 5007, H-alpha, [N II] 6584 first, plus other detected lines) |
| `gandalf_fit.png/pdf` | observed, GANDALF total, stellar continuum, gas emission, zoom and residual |
| `gandalf_uncertainty.png/pdf` | formal MPFIT flux/sigma errors and S/N |
| `gandalf_fit.fits` | galaxy, best fit, emission, residual, good pixels, weights, stellar kinematics, gas solution, errors, per-line templates |
| `gandalf_input.fits` | exact rest-frame grid, mask and templates passed to GDL |
| `gandalf_model.csv` | wave, flux, model, stellar, emission, residual, error |
| `gandalf_lines_raw.csv` | raw GANDALF solution (before the standardised table) |
| `gandalf_meta.txt`, `gandalf_run.log`, `gandalf_batch.gdl` | provenance |
| `run.json` | method, grid, PPXF stellar-kinematics block, measurements, runtime, limitations |

Columns in `gandalf_lines.csv` include `flux_1e17`, `flux_err_1e17`,
`flux_erg_s_cm2`, Gaussian `amplitude`, `velocity_kms`, `sigma_kms`
(intrinsic, instrumental 61.5 km/s subtracted), `sigma_obs_kms`, `snr`,
`detected`, `status` (`ok`, `weak`, `not_covered`, `not_detected`) and the
error `method` (`mpfit_covariance` or `amplitude_error_scaled` for lines
whose kinematics are tied).

## Config

`configs/gandalf_line/default/`:

* `emission_lines_setup` — rest-frame line list, multiplet ties and flux
  ratios.  All lines start with `action=m`; the driver tests coverage and
  switches in-window lines to `f` before the simultaneous fit.
* `config.json` — grid, templates, MPFIT/PPXF controls, mask widths,
  acceptance cuts and fixed stellar-LOSVD fallback.

The default setup ties narrow H-beta to [O III] 5007, ties [N II] 6584 and
[S II] to H-alpha, and adds independent broad H-beta and broad H-alpha
Gaussians (empirical BLR proxies).  H-alpha/[N II] rows are emitted as
`not_covered` when the spectrum does not reach them.

## Stellar kinematics

The canonical GANDALF workflow uses PPXF to obtain the stellar V and sigma
before the gas fit.  This tool attempts PPXF (IDL pPXF 2018 under GDL) with a
wide emission-line mask.  For an AGN-dominated QSO continuum PPXF often
cannot constrain the host absorption (the target here returns V=473 km/s,
sigma=1000 km/s, only 3 nonzero templates, so it is rejected).  In that case
the stellar templates are convolved with a fixed 300 km/s LOSVD and the
choice is recorded in `run.json` (`stellar_kinematics.source =
fixed_fallback`).  The gas fit itself is always native GANDALF.

## Caveats

* GDL is IDL-compatible but not identical; the exact compatibility fixes are
  documented in `docs/GANDALF_ASSESSMENT.md`.
* GANDALF errors are MPFIT covariance errors, not MCMC posterior errors.
* The broad H-beta component is an empirical Gaussian, not a physical BLR
  profile; the narrow component is tied to [O III].
* GANDALF v1.5 refuses `REDDENING` together with `MDEGREE>0`; no reddening
  correction is applied.
* This is integrated Gaussian line flux, not aperture photometry.

Third-party licences and attribution: `THIRD_PARTY_LICENSES.md`.
