# `sheap_line` — SHEAP JAX line fit (Docker, CPU)

Dockerised **SHEAP 0.0.11** (`https://github.com/felavila/sheap`, PyPI
`sheap`) applied to the rest-frame Hβ/[O III] 4959,5007 region of the
repository's SDSS QSO spectra.

SHEAP is a JAX spectral-fitting code.  Its headline feature is GPU
acceleration; this adapter deliberately runs it on **CPU JAX** so the result is
reproducible on the host.  `run.json` records the JAX devices actually used
(`TFRT_CPU_0`).  No GPU is required.

SHEAP is **AGPL-3.0**, not MIT.  It is installed from PyPI inside the Docker
image; no SHEAP source is vendored in this repository.  See
`THIRD_PARTY_LICENSES.md` and the licence note below before redistributing the
image.

## Status: repaired and retained in production

The original adapter (git `6ce42884`) fitted rest-frame **4600-5150 Å** with
one narrow component, no Fe II and SHEAP's default **600 km/s** narrow-FWHM
cap.  For `04592649654` that model could not describe the spectrum:

| quantity | original model | production model |
|---|---:|---:|
| fit window (rest Å) | 4600-5150 | **4450-5450** |
| narrow components | 1 | **2** (NLR core + blue [O III] wing) |
| Fe II | off | **template on** |
| continuum | broken power law | power law |
| narrow FWHM bound | 600 km/s (fit at 592) | 2000 km/s (fit at 900/1606) |
| broad Hβ FWHM | 8019 km/s | **3685 km/s** |
| broad Hβ velocity | +1877 km/s (near +2000 bound) | **+38 km/s** |
| χ²_ν | **46.0** | **2.87** |
| Hβ total (1e-17) | 3256 ± 41 | **3019.6** |
| [O III] 5007 (1e-17) | 814 ± 17 | **1491.4** |
| Hβ/[O III] 5007 | **4.00 ± 0.10** | **2.025** |

The full audit, variant tests and failure evidence are in
`docs/SHEAP_ASSESSMENT.md`.  The 4.00 ratio is **not** a property of the
object: it was the single narrow Gaussian saturating at SHEAP's 600 km/s cap
and the broad Hβ being pushed to its +2000 km/s bound to fill the [O III]
wings, while the missing Fe II template distorted the local continuum.

## Production model

* `inputs/<source>_z_<z>/raw/spec-*.fits` — SDSS `COADD` table.
* Fit region: rest-frame **4450-5450 Å**, covering He I 4471, He II 4686, Hβ,
  [O III] 4959/5007 and the Fe II blends on both sides.
* Continuum: SHEAP `powerlaw`.
* Fe II: `fe_mode="template"` (SHEAP's bundled Fe II UV/optical template).
  Required: without it χ²_ν rises to 16.8 and the ratio to 2.80.
* Broads: `n_broad=1` SPAF Gaussian for He I, He II and Hβ, with tied
  kinematics and free amplitudes.
* Narrow: `n_narrow=2` SPAF Gaussians.  SHEAP's component 1 is the blueshifted
  [O III] wing (FWHM ≈ 1606 km/s, v ≈ −827 km/s); component 2 is the NLR core
  (FWHM ≈ 900 km/s, v ≈ −19 km/s).  The wing has a free, effectively zero Hβ
  amplitude.  The [O III] 4959/5007 amplitude ratio is fixed at 0.3 by
  SHEAP's line repository.  The component numbering is visible in
  `sheap_lines.csv`; use the `velocity_kms` column to identify the wing.
* Host galaxy, Balmer continuum and Galactic extinction are not used.  The
  Balmer break is at 3646 Å, outside the window; the sibling tools also fit
  the observed SDSS spectrum with `EBV=0`.

`limits_overrides` widens SHEAP's hard priors so they are inactive: narrow
FWHM ≤ 2000 km/s and |v| ≤ 2000 km/s, broad |v| ≤ 3000 km/s.  The fit lands
away from every bound.

## What is run

| step | setting |
|---|---|
| optimiser | Adam, **4000 + 1000 steps**, learning rate 0.01 |
| best fit | SHEAP `estimate_posteriors("single")` |
| covariance | `covariance_error=True` (SHEAP's local JAX Jacobian/JTJ covariance) |
| uncertainty | `estimate_posteriors("montecarlo", num_samples=50, seed=42)` |
| MCMC | **not run** — SHEAP 0.0.11's `montecarlo` method is a parametric bootstrap, not an MCMC sampler |

The 50 draws are a real Monte-Carlo propagation: SHEAP resamples every pixel
from the observed flux and its 1-sigma error and re-runs the JAX optimiser.
It is **not** an MCMC posterior and **not** a draw from the fit covariance.
`run.json` records the method as `parametric bootstrap Monte Carlo (spectrum
resampling + re-optimisation)` with `mcmc: false`; the covariance matrix is a
separate local JTJ estimate.

## Build / run

```bash
bash Pipelines/build_images.sh sheap_line

bash Pipelines/run_sheap_line_docker.sh \
  inputs/04592649654_z_0.5874 \
  outputs/04592649654_z_0.5874/sheap_line \
  --z 0.58741307 --variants
```

or through the pipeline (quality gates only, no variant ensemble):

```bash
.venv/bin/python pipeline/run_new_tools.py \
  --only 04592649654_z_0.5874 --tools sheap_line --force
```

## Committed result

`outputs/04592649654_z_0.5874/sheap_line/` was produced with the command
above.  Rest-frame fluxes in units of 1e-17 erg s⁻¹ cm⁻² (same convention as
`gandalf_line`, which also multiplies by 1+z):

| quantity | SHEAP | PyQSOFit | GANDALF | S3Fit |
|---|---:|---:|---:|---:|
| Hβ total | 3019.6 ± 27.4 | 2905 | 2951 ± 33 | 2761 ± 4 |
| [O III] 5007 | 1491.4 ± 14.9 | 1480 | 1423 ± 12 | 1507 ± 9 |
| Hβ/[O III] 5007 | 2.025 ± 0.027 | 1.96 | 2.07 ± 0.03 | 1.83 ± 0.01 |
| broad Hβ FWHM (km/s) | 3685 | 3550 | 2079 | 2934 |
| reduced χ² | 2.87 | — | — | 4.76 (fast run) |

SHEAP now agrees with all three sibling fitters at the few-percent level.  The
broad/narrow split (2314 broad + 706 narrow Hβ) is close to PyQSOFit
(2280 + 625) and S3Fit (2091 + 670); GANDALF's 50/50 split reflects its
different narrow-line model.

Runtime on the shared 8-core host: fit 106 s, 50 bootstrap draws 459 s,
figures 14 s, five variants 340 s; total 926 s (15.4 min).  The bootstrap
re-optimises every draw, so it dominates the runtime.

The committed audit run also writes `sheap_systematics.csv`: the ratio is
2.025 with the production model, 2.030 with the red end at 5250 Å, 2.025 with
a broken-power-law continuum, 2.127 with a single narrow component, and 2.80
when Fe II is removed.  The 1000 km/s narrow-cap variant gives 2.074 but is
rejected because its wing saturates the cap.  The three passing variants span
2.025-2.127 (std 0.058, half-range 0.051), i.e. a model-systematic uncertainty
of about ±0.05, larger than the bootstrap error.

## Outputs

```text
outputs/<source>_z_<z>/sheap_line/
  sheap_lines.csv                 line, component, flux, error, FWHM, velocity
  sheap_model.csv                 fitted region: data/model/residual/components
  sheap_mc_samples.csv            50 bootstrap draws of the component fluxes
  sheap_fit.png/.pdf              full region: data/model/components/residual
  sheap_zoom_hbeta.png/.pdf       Hβ zoom
  sheap_zoom_oiii.png/.pdf        [O III] 4959/5007 zoom
  sheap_residual.png/.pdf         residual/sigma over the fitted region
  sheap_fit_native.png            SHEAP's own component plot
  sheap_uncertainty.png/.pdf      bootstrap histograms of Hβ, [O III], ratio
  sheap_comparison.csv            SHEAP vs sibling line fluxes
  sheap_ratio_comparison.csv      Hβ/[O III] for SHEAP and siblings
  sheap_systematics.csv           variant ensemble (only with --variants)
  run.json                        provenance, model, fit, quality gates, timings
```

`sheap_model.csv` is restricted to the fitted pixels; its `component_000`,
`component_001`, ... columns are in the order listed in
`run.json.model.components`.  In `sheap_lines.csv`, `lambda_rest` is the
fitted centroid and `lambda_lab` the laboratory wavelength.  The previous adapter
evaluated the *local* SHEAP model over the full 2247-6510 Å spectrum; a power
law extrapolated that far is meaningless and made the residual figure look
much worse than the actual fit.

## Quality gates

`run.json.quality` records every gate.  The run passes only if:

* χ²_ν ≤ 8;
* 1.8 ≤ Hβ/[O III] 5007 ≤ 2.5;
* the [O III] 4959/5007 ratio is 2.5-3.8;
* broad Hβ FWHM ≤ 7000 km/s;
* no line kinematic parameter sits on a hard SHEAP bound;
* when at least two sibling tables are present, Hβ and [O III] 5007 are
  within 30 % of their median.

A failing run still writes its diagnostic products, but exits with status 2,
sets `quality.production_ok = false`, and is skipped by
`pipeline/compare_line_tools.py`.  This is the guard that keeps a 4.0-style
model failure out of the production comparison.

## Caveats

* CPU only; GPU acceleration was not used.
* SHEAP 0.0.11's SPAF constraint builder only supports Gaussian/Lorentzian/
  top-hat sub-profiles; the skewed-Gaussian and EMG sub-profiles raise.  The
  blue [O III] wing is therefore modelled with a second Gaussian, not a
  physically asymmetric profile.
* Narrow-line kinematics are tied across Hβ, [O III] and He II within each
  component.  Individual pixels at the Hβ and [O III] cores still show
  ±10σ residuals; the integrated fluxes are stable across the model variants,
  the profile shapes are not perfect.
* The bootstrap errors are statistical only.  The best-fit ratio is 2.025;
  the 50-draw bootstrap median is 2.041 with a correlated 1σ of 0.022, while
  the table's quadrature propagation gives 0.027.  The model-systematic spread
  from `sheap_systematics.csv` (±0.05) dominates both.
* Fe II is a single bundled template; host galaxy and Balmer continuum are
  disabled.
* SHEAP's PyPI wheel does not include the SFD dust maps; extinction correction
  is disabled (`coords=None`, `extinction_correction="done"`).  If you enable
  it, provide the maps and set the correction flag in a custom runner.
* SHEAP's API differs between the PyPI wheel and the git head (the wheel
  expects the input array to carry an explicit object axis).  The adapter uses
  the PyPI 0.0.11 convention and pins that version.
* `group_method=False` (independent kinematics per line) runs the fit but
  crashes in SHEAP's `extract_basic_params_sampled` (upstream
  `TypeError: ... missing 1 required positional argument: 'distances'`), so it
  is not usable.

## Licensing

SHEAP is **AGPL-3.0-only**.  The Docker image installs it from PyPI.  The
repository's MIT licence does not cover SHEAP.  Redistributing the built image
or a service around it may trigger AGPL obligations; review the licence before
publishing the image.  Citation: Ávila-Vera et al., SHEAP paper (ADS
2026arXiv260603934A).
