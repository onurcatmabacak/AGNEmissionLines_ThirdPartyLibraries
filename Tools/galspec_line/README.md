# `galspec_line` — GalSpec reduced H-beta/[O III] line fit (Docker)

Dockerised **GalSpec** (`https://github.com/jyshangguan/GalSpec`, pinned commit
`18e4effd796a1d51615ca2340bb927278eb18bbf`) applied to the repository's SDSS
QSO spectra.  GalSpec is a pure-Python Astropy modelling package; this adapter
uses its `Line_Gaussian` and `IronTemplate_new` models, its Astropy
`TRFLSQFitter` start, and its native `MCMC_Fit` (`emcee`) posterior.  A
`Dynesty_Fit` nested-sampling path is available with `--sampler nested`.

This is a **reduced-window** fit, not a full-spectrum continuum/host
decomposition.  The main window is 4720-5150 A rest frame:

```text
linear local continuum
+ park2022 Fe II template
+ H-beta narrow + broad Gaussians
+ [O III] 5007 narrow + wing
+ [O III] 4959 narrow + wing (tied to 5007 by 2.98)
```

Auxiliary [O II] 3726/3728, [Ne III] 3869/3967 and [S II] 4068/4076 windows
are fitted with a linear continuum and tied narrow Gaussians.  H-alpha and the
red [N II]/[S II] lines are outside the SDSS rest-frame coverage of the
z=0.5874 target and are emitted as `not_covered`.

## Build / run

```bash
bash Pipelines/build_images.sh galspec_line

# direct run on the canonical source directory
bash Pipelines/run_galspec_line_docker.sh \
  inputs/04592649654_z_0.5874 \
  outputs/04592649654_z_0.5874/galspec_line \
  --object 04592649654_z_0.5874

# through the matrix runner
.venv/bin/python pipeline/run_new_tools.py \
  --only 04592649654_z_0.5874 --tools galspec_line --force
```

Useful overrides:

```bash
--config configs/galspec_line/default   # config directory or JSON file
--sampler mcmc|nested|lsq               # default mcmc (emcee)
--z 0.58741307                          # override redshift
--mcmc-steps 4000 --nwalkers 48 --nburn 1500 --seed 42
```

The image is built from the repository root because it copies
`Tools/galspec_line/` and `configs/galspec_line/`.  The upstream package is
installed with pip from the pinned public git commit; no GalSpec source or
example data is vendored into this repository.

## Input

The driver accepts either:

* raw SDSS DR18 `COADD` table FITS (`FLUX`, `LOGLAM`, `IVAR`, `WDISP`, `WRESL`,
  `AND_MASK`, `SPALL.Z`) — the canonical `inputs/<source>/raw/spec-*.fits`; or
* a prepared PyQSOFit-style FITS (`HDU0` flux, `HDU1` wavelength, `HDU2`
  1-sigma error, header `z`).

SDSS `LOGLAM` is vacuum.  The adapter applies `PyAstronomy.pyasl.vactoair2`,
de-redshifts to the rest frame, and multiplies the flux and error by `(1+z)`
so that `F_lambda_rest = F_lambda_obs (1+z)` (the same convention as the
PyQSOFit and GANDALF outputs in this repository).  Internal modelling is in
`1e-17 erg s-1 cm-2 A-1`; output fluxes are given in both `1e-17` and cgs.

The 2 per cent continuum error floor is configurable in
`configs/galspec_line/default/config.json` (`errors`).  Both the raw and
floored chi-square are recorded.

## Output

`outputs/<source>/galspec_line/`:

| file | contents |
|---|---|
| `galspec_lines.csv` | line, component, rest wavelength, flux/flux_err in cgs and 1e-17, FWHM, velocity, S/N, detected, status, method, integration window |
| `galspec_fit.png/pdf` | full rest spectrum, main-window data/model, residuals, H-beta and [O III] component zooms |
| `galspec_uncertainty.png/pdf` | emcee trace and posterior line-flux histograms |
| `galspec_corner.png/pdf` | posterior corner plot of the eight physically important line parameters |
| `galspec_model.csv` | wave, flux, error, total model, continuum, Fe II, per-line models, residual |
| `galspec_mcmc.npz` | thinned posterior samples, log probability, parameter names, derived line arrays |
| `galspec_comparison.csv` | H-beta/[O III] 5007 ratios vs PyQSOFit, GANDALF and S3Fit |
| `config.effective.json` | exact effective configuration, input path, sampler and redshift |
| `run.json` | provenance, model, fit quality, sampling diagnostics, all line measurements, comparison, runtime, limitations |
| `galspec.log` | adapter log |

Rows with `status=not_covered` have NaN fluxes.  `method` is `emcee_mcmc`,
`dynesty_nested` or `lsq_covariance`; auxiliary lines are always
`lsq_covariance`.

## Statistical mode

The committed demonstration uses a real `emcee` chain.  The chain length is a
short production demonstration, not a converged publication posterior:
`nsteps/nburn/nwalkers` and `tau_max` are reported in `run.json`.  The LSQ
solution is used only as the starting point and as a cross-check; it is not
labelled MCMC.  `--sampler lsq` is available for debugging and is explicitly
marked in the output.

## Committed demonstration run

`outputs/04592649654_z_0.5874/galspec_line/` was produced by the default
`emcee` configuration:

```bash
bash Pipelines/run_galspec_line_docker.sh \
  inputs/04592649654_z_0.5874 outputs/04592649654_z_0.5874/galspec_line \
  --object 04592649654_z_0.5874
```

Measured on the 8-core host:

| quantity | value |
|---|---:|
| image size | 1.36 GB (~1.356e9 bytes) |
| wall time, whole command | 7 min 13.3 s |
| driver total | 427.1 s |
| LSQ start | 0.66 s |
| emcee (4000 steps, 1500 burn, 48 walkers, 17 parameters) | 404.4 s |
| `chi2_nu` raw / floored | 1.926 / 1.218 |
| acceptance fraction | 0.324 |
| `tau_max` | 201.4 steps |
| `nsteps/tau_max` | 19.9 |
| H-beta narrow / broad / total | 1439.6 / 1798.5 / 3236.8 (1e-17) |
| [O III] 5007 narrow / wing / total | 869.1 / 748.0 / 1618.7 (1e-17) |
| H-beta total / PyQSOFit | 1.114 |
| H-beta total / GANDALF | 1.097 |
| H-beta total / S3Fit | 1.172 |
| [O III] 5007 total / PyQSOFit | 1.094 |
| [O III] 5007 total / GANDALF | 1.138 |
| [O III] 5007 total / S3Fit | 1.074 |

Reference runtimes: GANDALF 43.9 s, S3Fit 937.0 s (from their `run.json`);
PyQSOFit did not write a runtime.  The GANDALF and S3Fit comparisons use their
reported total [O III] 5007 flux even though neither splits a broad wing; the
narrow-component ratios are in `galspec_comparison.csv` and are not directly
comparable because our core/wing split differs.

`--sampler nested` was also exercised with `dynesty` at `nlive=50` and
`dlogz=1.0` (336.8 s, log evidence `-767.48 +/- 2.30`); the committed output is
the `emcee` run, not the nested smoke test.

## Caveats

* Reduced 4720-5150 A rest-frame model; no full QSO principal-component
  continuum, Balmer pseudo-continuum or host-galaxy stellar decomposition.
* H-alpha, [N II] 6548/6583 and [S II] 6716/6731 are outside the SDSS coverage
  of this z=0.5874 target (rest ~2246-6509 A); they are `not_covered`, not
  fitted.
* The narrow/broad and core/wing splits are empirical Gaussian
  decompositions.  Their flux ratios are not directly interchangeable with
  other tools' component definitions; compare the totals and the measured
  widths.
* Fe II is the empirical park2022 template; it is not a physical Fe II
  model and is degenerate with the local continuum at some level.
* Auxiliary [O II], [Ne III] and [S II] fluxes use single Gaussians and
  covariance errors; the [O II] and [S II] doublets are blended at SDSS
  resolution, so individual doublet components can have large errors.
* FWHM is measured from the summed line profile; `fwhm_intrinsic_kms`
  subtracts the SDSS `WRESL` resolution in quadrature.
* The full image build needs network access to install the pinned GalSpec
  commit.  Third-party licences remain with their upstream projects.

Upstream: GalSpec, MIT licence, `https://github.com/jyshangguan/GalSpec`.
