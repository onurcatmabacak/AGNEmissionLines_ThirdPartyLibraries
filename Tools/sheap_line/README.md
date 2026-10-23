# `sheap_line` — SHEAP JAX line fit (Docker, CPU)

Dockerised **SHEAP 0.0.11** (`https://github.com/felavila/sheap`, PyPI
`sheap`) applied to the Hβ/[O III] 4959,5007 region of the repository's SDSS
QSO spectra.

SHEAP is a JAX spectral-fitting code.  Its headline feature is GPU
acceleration; this adapter deliberately runs it on **CPU JAX** so the result is
reproducible on the host.  `run.json` records the JAX devices actually used
(`TFRT_CPU_0`).  No GPU is required.

SHEAP is **AGPL-3.0**, not MIT.  It is installed from PyPI inside the Docker
image; no SHEAP source is vendored in this repository.  See
`THIRD_PARTY_LICENSES.md` and the licence note below before redistributing the
image.

## Build / run

```bash
bash Pipelines/build_images.sh sheap_line

bash Pipelines/run_sheap_line_docker.sh \
  inputs/04592649654_z_0.5874 \
  outputs/04592649654_z_0.5874/sheap_line \
  --z 0.58741307
```

or:

```bash
.venv/bin/python pipeline/run_new_tools.py \
  --only 04592649654_z_0.5874 --tools sheap_line --force
```

## Inputs and model

* `inputs/<source>_z_<z>/raw/spec-*.fits` — SDSS `COADD` table.
* Fit region: rest-frame **4600–5150 Å**, covering Hβ, [O III] 4959 and
  [O III] 5007 (and the weak He II 4686 blend that SHEAP's line repository adds
  automatically).
* Continuum: SHEAP `brokenpowerlaw` over the local region.
* Lines: `n_broad=1`, `n_narrow=1`, SPAF Gaussian profiles, with SHEAP's
  automatic [O III] 4959/5007 amplitude and kinematic ties.
* Fe II: `fe_mode="None"` (the Fe II templates are bundled with SHEAP but are
  not used in this small Hβ/[O III] window).
* Host galaxy: not used.
* Balmer continuum: not used.
* Galactic extinction: disabled (`coords=None`, `extinction_correction="done"`).
  SHEAP's SFD maps are excluded from the PyPI wheel upstream; they are not
  needed for this run.  The sibling tools also use the observed SDSS spectrum
  with `EBV=0`.

## What is run

| step | setting |
|---|---|
| optimiser | Adam, 1000 steps, learning rate 1e-2 |
| covariance | `covariance_error=True` (SHEAP finite-difference covariance) |
| best fit | SHEAP `estimate_posteriors("single")` |
| uncertainty | SHEAP `estimate_posteriors("montecarlo", num_samples=50, seed=42)` |
| MCMC | **not run** — SHEAP's `montecarlo` sampler draws from the covariance; it is not an MCMC posterior |

The 50 draws are a real covariance Monte-Carlo propagation, not a posterior
sampler.  `run.json` labels the method `sheap_jax_adam` / `covariance
Monte-Carlo draws`, with `mcmc: false`.

## Committed demonstration run

`outputs/04592649654_z_0.5874/sheap_line/` was produced with:

```bash
bash Pipelines/run_sheap_line_docker.sh \
  inputs/04592649654_z_0.5874 outputs/04592649654_z_0.5874/sheap_line \
  --z 0.58741307
```

| quantity | SHEAP | PyQSOFit | GANDALF | S3Fit |
|---|---:|---:|---:|---:|
| Hβ total (1e-17) | 3256 ± 41 | 2905 | 2951 ± 33 | 2761 ± 4 |
| [O III] 5007 (1e-17) | 814 ± 17 | 1480 | 1423 ± 12 | 1507 ± 9 |
| Hβ/[O III] 5007 | 4.00 ± 0.10 | 1.96 | 2.07 ± 0.03 | 1.83 ± 0.01 |
| broad Hβ FWHM (km/s) | 8019 | 3550 (PyQSOFit) | 2079 (GANDALF) | 2934 (S3Fit) |
| reduced χ² | 46.0 | — | — | 4.76 (S3Fit fast run) |

**SHEAP is reproducible but not competitive for this object.**  It produces a
real JAX fit, but the broad Hβ component is extremely wide (FWHM ≈ 8000 km/s,
centroid +1877 km/s), the Hβ total is ~12 % above the other tools, and
[O III] 5007 is ~45 % low.  The Hβ/[O III] ratio is therefore ~2× the
PyQSOFit/GANDALF/S3Fit values.  `run.json` records this in
`scope.fit_quality_note`; the adapter does not present SHEAP as a preferred
measurement.

Runtime on the 8-core host: **58.5 s** inside the container (≈64 s wall),
including the JAX fit, covariance, 50 MC draws, and figures.

## Outputs

```text
outputs/<source>_z_<z>/sheap_line/
  sheap_lines.csv                 line, component, flux, error, FWHM, velocity
  sheap_mc_samples.csv            50 MC draws of Hβ/[O III] quantities
  sheap_model.csv                 rest-frame data / model / residual
  sheap_fit.png/.pdf              compact data/model/residual figure
  sheap_fit_native.png            SHEAP's own component plot
  sheap_uncertainty.png/.pdf      MC histograms of Hβ, [O III], ratio
  sheap_comparison.csv            SHEAP vs sibling line fluxes
  sheap_ratio_comparison.csv      Hβ/[O III] for SHEAP and siblings
  run.json                        provenance, JAX devices, controls, timings
```

## Caveats

* CPU only; GPU acceleration was not used.
* The Hβ/[O III] fit is poor for this luminous QSO (χ²_ν=46; residuals up to
  ±20σ at the line cores).  Treat the SHEAP numbers as a reproducibility
  demonstration, not a preferred line measurement.
* The covariance Monte-Carlo is a local propagation; it is not an MCMC
  posterior and it does not capture the model mismatch that dominates the
  residual.
* Fe II, host, and Balmer continuum are disabled; the fit is a local
  Hβ/[O III] decomposition, not a full QGfit-style AGN+host model.
* SHEAP's PyPI wheel does not include the SFD dust maps; extinction correction
  is disabled.  If you enable it, provide the maps and set the correction flag
  in a custom runner.
* SHEAP's API differs between the PyPI wheel and the git head (the wheel
  expects the input array to carry an explicit object axis).  The adapter uses
  the PyPI 0.0.11 convention and pins that version.

## Licensing

SHEAP is **AGPL-3.0-only**.  The Docker image installs it from PyPI.  The
repository's MIT licence does not cover SHEAP.  Redistributing the built image
or a service around it may trigger AGPL obligations; review the licence before
publishing the image.  Citation: Ávila-Vera et al., SHEAP paper (ADS
2026arXiv260603934A).
