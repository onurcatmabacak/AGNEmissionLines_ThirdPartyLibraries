# Third-party code and data in `Tools/sheap_line/`

The repository's top-level MIT licence applies to the `sheap_line` wrapper.
**SHEAP itself is AGPL-3.0-only** and is not relicensed by this repository.

## SHEAP 0.0.11

Source: `https://github.com/felavila/sheap`, PyPI `sheap==0.0.11`.
Installed from PyPI inside the Docker image; no SHEAP source is vendored here.

Licence: **GNU Affero General Public License v3.0 only** (AGPL-3.0-only).
The image is a combined work that contains SHEAP.  Review AGPL obligations
before redistributing the image or exposing it as a network service.

Citation: Ávila-Vera, F., et al., *Spectral Handling and Estimation of AGN
Parameters (SHEAP): The first GPU-based AGN spectral-fitting code*, A&A
(submitted), ADS 2026arXiv260603934A.

## SHEAP template data (inside the PyPI wheel)

The wheel includes the Fe II templates, Balmer high-order template, and
E-MILES/XSL SSP cubes under `sheap/SuportData/templates/`.  The repository does
not redistribute them separately.  See SHEAP's
`SuportData/templates/README.md` for the original citations (Park et al. 2022;
Mejía-Restrepo et al. 2016; E-MILES).  The Hβ/[O III] run here does not use
Fe II, host, or Balmer-continuum templates.

## JAX / jaxlib

`jax==0.4.38`, `jaxlib==0.4.38` (Apache-2.0) are installed from PyPI.  The
CPU wheel is used; no CUDA libraries are included.

## Runtime libraries

NumPy, SciPy, pandas, Astropy, Matplotlib, optax, chex, sfdmap2 and their
transitive dependencies are installed from PyPI and keep their own licences.
