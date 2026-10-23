# `qgfit` — QGfit continuum + emission-line fit (Docker)

Dockerised **QGfit 1.0.0** (`https://github.com/qian-yang/QGfit`, commit
`3aed692`, 2025-01-03) applied to the repository's SDSS QSO spectra.  QGfit
fits a broken power-law AGN continuum, UV/optical Fe II templates, an optional
Balmer continuum, a BC03 host-galaxy SED, and skewed-Voigt emission lines
(with [O III] and Balmer-line kinematic ties).

QGfit is the preferred new optical line tool in this repository: it ships its
own Fe II and BC03 template data, needs no proprietary files, and runs on CPU.

## Build / run

```bash
bash Pipelines/build_images.sh qgfit

bash Pipelines/run_qgfit_docker.sh \
  inputs/04592649654_z_0.5874 \
  outputs/04592649654_z_0.5874/qgfit \
  --z 0.58741307
```

or through the source-keyed matrix:

```bash
.venv/bin/python pipeline/run_new_tools.py \
  --only 04592649654_z_0.5874 --tools qgfit --force
```

## Inputs

* `inputs/<source>_z_<z>/raw/spec-*.fits` — SDSS `COADD` table with `FLUX`
  (1e-17 erg s-1 cm-2 A-1), `LOGLAM` (vacuum), `IVAR`, `AND_MASK`.
* QGfit reads the SDSS file directly; no prepared copy is needed.
* `--z` overrides the manifest redshift.  RA/Dec come from `PLUG_RA`/`PLUG_DEC`.
* Pixels with `IVAR<=0`, non-finite values, or non-zero `AND_MASK` are removed
  before fitting.

## What is fitted

| component | QGfit model | enabled |
|---|---|---|
| AGN continuum | broken power law | yes |
| UV Fe II | bundled `fe_uv.txt` template, broadened/shifted | yes |
| optical Fe II | bundled `fe_op.txt` template | yes |
| Balmer continuum | non-LTE Balmer model | no (default) |
| host galaxy | bundled BC03 SSP grid (`bc03_ssp_fl_xarr.npz`), young+old | yes |
| emission lines | skewed Voigt, broad/narrow/mix, QGfit `lines.csv` | yes |

The host term is enabled because the source is at z=0.587 (< QGfit's
`host_zcut=1.2`).  The Balmer continuum is disabled by default; enable it with
`"conti_balmer": true` in `configs/qgfit/default/config.json`.

## External data requirements

* **Fe II and BC03 templates are bundled** in the QGfit package
  (`qgfit/template/`) and are copied into the image.  No external template
  download is required.
* **SFD dust maps are not bundled** (~160 MB, and QGfit's `sfdmap` dependency
  only reads them when `do_deredden=true`).  The committed run uses
  `"do_deredden": false`, matching the sibling PyQSOFit/GANDALF/S3Fit runs,
  which also use the observed SDSS spectrum with `EBV=0`.
* To enable Galactic dereddening, mount the four sfdmap FITS files at
  `/opt/sfd` (`--sfd-dir DIR`) and set `"do_deredden": true`.  The adapter
  refuses to run if the flag is true and the maps are absent.
* `kapteyn` (for QGfit's optional KMPFIT fallback) is built from source in the
  Docker image.  The image is Python 3.8 because that is QGfit's documented
  environment and the only combination in which Kapteyn 2.3.1 compiles here.

## Fit controls that matter

`configs/qgfit/default/config.json` sets:

* `mask_lowSN: false` — QGfit's default negative-S/N clipping removes the
  Hβ/[O III] region on this object and forces all four lines to zero.  All
  genuinely invalid pixels are already removed by `IVAR/AND_MASK`; the
  additional `flux > -1 sigma` clip is not appropriate for this spectrum.
* `test_add_broad: false` — QGfit's automatic BIC test for adding an extra
  broad component is disabled.  With it enabled, the Hβ complex is removed
  entirely by the BIC cleanup on this object.
* `check_kmpfit: true`, `conti_redchi_limit: 1.5` — QGfit's default KMPFIT
  fallback is attempted when the least-squares continuum χ²_ν exceeds 1.5.
  QGfit keeps the better of the two; for this source the least-squares solution
  (χ²_ν=16.81) beats KMPFIT (18.09), so the final fit is least-squares.
* `conti_mcmc: true`, `conti_nwalkers: 40`, `conti_steps: 100`,
  `conti_burn: 20` — a **short, real emcee MCMC of the continuum only**.
* `line_mcmc: false` — line MCMC would run one emcee chain per line complex and
  is much slower.  Line flux errors therefore come from QGfit's least-squares
  covariance (`norm_stderr`), not from the MCMC.

## Statistical mode (honest labels)

| product | method |
|---|---|
| continuum + lines | `lmfit` least-squares (KMPFIT fallback attempted and recorded) |
| `qgfit_uncertainty.png` | emcee MCMC, 40 walkers × 100 steps, burn 20, 16 free parameters, acceptance ≈0.34 |
| `qgfit_line_errors.png` | first-order covariance: `sigma(flux) ≈ sigma(norm) × lambda_rest`; width/shift terms neglected |
| line MCMC | not run |

The MCMC is intentionally short.  emcee warns that the chain is shorter than
50 integrated autocorrelation times; `run.json` records `converged: false` and
the figure title says "not converged".  Do not use the MCMC quantiles as a
converged posterior.

## Flux scale

QGfit works in the rest frame.  Its `line_info['flux']` is the integral over
rest-frame wavelength in units of 1e-17 erg s-1 cm-2.  The observed-frame line
flux is

```text
F_obs = integral(F_rest dlambda_rest) / (1+z)^2
```

because `dlambda_rest = dlambda_obs/(1+z)`.  The adapter stores both
`flux_rest_1e17` and the observed-frame `flux_1e17`; comparisons to the other
tools use `flux_1e17`.

## Committed demonstration run

`outputs/04592649654_z_0.5874/qgfit/` was produced with:

```bash
bash Pipelines/run_qgfit_docker.sh \
  inputs/04592649654_z_0.5874 outputs/04592649654_z_0.5874/qgfit \
  --z 0.58741307
```

| quantity | QGfit | PyQSOFit | GANDALF | S3Fit |
|---|---:|---:|---:|---:|
| Hβ total (1e-17) | 2915 ± 175 | 2905 | 2951 ± 33 | 2761 ± 4 |
| [O III] 5007 (1e-17) | 1167 ± 22 | 1480 | 1423 ± 12 | 1507 ± 9 |
| Hβ/[O III] 5007 | 2.50 ± 0.16 | 1.96 | 2.07 ± 0.03 | 1.83 ± 0.01 |
| QGfit/reference Hβ | — | 1.00 | 0.99 | 1.06 |
| QGfit/reference [O III] | — | 0.79 | 0.82 | 0.77 |

QGfit's Hβ total agrees with the three existing tools at the 1–6 % level.
[O III] 5007 is ~20 % lower, so the Hβ/[O III] ratio is ~25 % higher.  The
Hβ narrow component is removed by QGfit's BIC line cleanup; the total Hβ row
is therefore broad-only for this source.  The continuum χ²_ν is high (16.8),
driven by the simple power-law + Fe II + BC03 model against a luminous QSO
with strong Fe II and host light.

Runtime on the 8-core host: **231 s** inside the container (≈295 s wall with
image startup and file I/O), including the least-squares fit, KMPFIT fallback,
100-step continuum MCMC, line fit, and all figures.

## Outputs

```text
outputs/<source>_z_<z>/qgfit/
  qgfit_lines.csv                 line, component, flux, error, FWHM, velocity
  qgfit_model.csv                 rest-frame data / continuum / line / total model
  qgfit_fit.png/.pdf              full spectrum + Hβ/[O III] decomposition
  qgfit_uncertainty.png/.pdf      continuum MCMC corner plot (short run)
  qgfit_mcmc_summary.csv          per-parameter MCMC quantiles
  qgfit_line_errors.png           line-flux error bars (covariance)
  qgfit_native.pdf                QGfit's own multi-panel PDF
  qgfit_native_corner.jpg         QGfit's own corner plot
  qgfit.pkl                       native QGfit result (config, data, chains)
  qgfit_comparison.csv            QGfit vs sibling line fluxes
  qgfit_ratio_comparison.csv      Hβ/[O III] for QGfit and siblings
  run.json                        provenance, controls, method, timings, scope
```

## Caveats

* No Galactic dereddening (SFD maps not shipped; consistent with the siblings).
* No line MCMC; line errors are covariance, not posterior quantiles.
* The continuum MCMC is a short demonstration, not a converged chain.
* QGfit's BIC cleanup removes the Hβ narrow component on this object; the
  Hβ total is broad-only.  The Hβ/[O III] ratio is correspondingly high.
* The QGfit native plot can raise an axes-indexing error for single-component
  `comp_plot` lists; the adapter uses a multi-component list and falls back to
  its own figures if the native plot fails.

## Licensing

QGfit's `setup.py`/README declare MIT, but the pinned upstream commit has no
`LICENSE` file.  The vendored source retains the upstream headers and this
repository does not relicense it.  See `THIRD_PARTY_LICENSES.md`.
