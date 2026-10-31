# Literature coverage

This is an evidence-based coverage map, not a claim that the registry contains
"every tool".  It was produced by a read-only survey of the current registry
and public source/paper/licence pages.

## Current coverage

| category | implemented |
|---|---|
| UV/optical 1-D AGN lines | PyQSOFit, QSOFITMORE, PyQSOFitSpec, optical_linefit, S3Fit, GANDALF, GalSpec, QGfit, SHEAP, generic local Gaussian |
| host | pPXF, GANDALF |
| IFU | official MaNGA DAP (9-bin subset; full path implemented as `manga_dap_full`) |
| NIR/MIR/FIR | CAFE, PAHFIT, S3Fit, NIR line fitter, FIR line fitter |
| X-ray | XMM PPS + XSPEC/PyXspec; RXTE stdprod + XSPEC/PyXspec |
| SED/torus | CIGALE (SKIRTOR/Fritz), AGNfitter-rx |
| reference | SDSS ZLINE |

## High-priority gaps

These are absent and are the scientifically defensible next additions.  They are
not silently claimed as implemented.

| candidate | why it matters | licence/runtime | status |
|---|---|---|---|
| **Radio / sub-mm** | jets, H I absorption and molecular gas — the repository has no radio data and no radio tool | RadioSED (GPL-3.0, buildable); XCLASS/McFine need CASA; Qubespec has no licence; MoD_AbS and the SED 'Lightning' have no public distribution | **none implemented** — feasibility verified in `docs/RADIO_SUBMM_INTEGRATION.md` |
| **BXA** | Bayesian X-ray parameter estimation and evidence/model comparison; the chi-square covariance remains the reference fit | GPL-3.0, Python + XSPEC/Sherpa + UltraNest | **implemented** as `bxa_xspec` (absorbed PL, Fe K-alpha, warm/partial/Compton-thick absorbers) |
| **MYTorus** | Smooth torus absorption/scattering and Compton-thick Fe Kα; current model has no torus | public FITS table model, XSPEC | **not implemented** |
| **UXCLUMPY/XARS** | Clumpy/eclipsing torus geometry | AGPL-3.0, XSPEC table model | **not implemented** |
| **RELXILL** | Relativistic reflection/spin diagnostic; current 4σ narrow line cannot constrain spin | LGPL-3.0, C/C++ local XSPEC model | **not implemented; diagnostic only** |
| **3ML** | Joint multi-instrument likelihood, not post-hoc flux ratios | BSD-3-Clause, Python | **not implemented; needs a defined joint-fit case** |
| **QSFit** | Published AGN continuum/Fe II/line fitter; strong overlap with PyQSOFit/QSOFITMORE | GPL-3.0 but IDL >=8.1 + Gnuplot | **conditional; GDL spike only** |

## Low-priority or excluded

- **STARLIGHT / STECKMAP / FADO**: host stellar-population synthesis; redundant
  with pPXF/GANDALF for line-ratio work, or public code/licence not verified.
- **CLUMPY / BAGPIPES / Prospector**: SED/torus or stellar-population
  alternatives; no new line-ratio gain, and Prospector already assessed.
- **LVM-DAP / GIST / LZIFU / pyPipe3D / FIT3D**: IFU-only; MaNGA DAP covers the
  current IFU case.
- **AMARU / ELFO / AGNdecompose / pyspeckit / Sherpa / ISIS / SPEX**: excluded
  or redundant for the reasons in `docs/OFFICIAL_PIPELINES_AND_XRAY.md`.

## Acceptance rules for adding a tool

A new tool is added only if it has:

1. a public, verifiable source and licence;
2. a Dockerised, pinned runtime;
3. a real AGN spectrum/cube test, not a synthetic-only demo;
4. an output contract and a caveat entry;
5. a statistical cross-check against an existing tool or official product.

The X-ray branch (BXA + torus/reflection) is the highest-value extension.  The
optical stack already has nine fitters; adding another optical fitter would not
improve the limiting evidence.
