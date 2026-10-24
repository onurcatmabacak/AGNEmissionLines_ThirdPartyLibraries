# Line-fitting tools vs SED-fitting tools

CIGALE and AGNfitter are **broad-band SED/torus** codes.  They fit the overall
shape of a photometric SED with stellar, dust, AGN and torus templates; they do
not measure the flux or kinematics of an individual emission line.  PyQSOFit,
CAFE, S3Fit, GANDALF, PAHFIT and the generic Gaussian fitters operate on
**spectra** and return line fluxes, widths and component decomposition.

## Tool matrix

| tool | family | rest-frame coverage | decomposition | uncertainty |
|---|---|---|---|---|
| `pyqsofit_uv` | line | UV–optical | power-law/Fe II continuum + broad/narrow Gaussians | covariance, optional MC/`emcee` |
| `ir_linefit` | line | UV–FIR | local continuum + Gaussians, doublet/kinematic ties | covariance |
| `nir_linefit` | line | NIR | x1d/PSF spectrum + local continuum + Gaussians | covariance |
| `cafe_line` | line | NIR–MIR | stellar/dust/AGN continua + PAH + H/atomic/molecular lines | LMFIT covariance + MC |
| `s3fit_line` | line | UV–NIR | simultaneous spectrum + photometric SED, AGN/Fe II + multi-component lines | mock-spectrum MC |
| `gandalf_line` | line | optical–NIR | pPXF stellar continuum + simultaneous Gaussian gas | MPFIT covariance/bootstrap |
| `sdss_zline` | **official product** | optical | BOSS `speclinefit` narrow-line measurements from the `ZLINE` HDU | pipeline errors |
| `galspec_line` | line | optical–NIR | full-continuum polynomial + Fe II + Gaussian lines (2280–6460 A rest) | `emcee` MCMC (production) / dynesty / LSQ start |
| `pyqsofitspec_line` | line | UV–optical | PyQSOFitSpec skew-normal components + Fe II/Balmer | parametric bootstrap |
| `qgfit` | line | UV–optical | AGN power law + Fe II + host + multi-component lines | continuum MCMC; LSQ line errors |
| `sheap_line` | line | UV–optical | SHEAP SPAF/AGN decomposition, BH mass | JAX optimisation + parametric-bootstrap MC |
| `pahfit_mir` | line | MIR | PAH Drude profiles + dust continuum + gas Gaussians | least-squares + MC |
| `fir_linefit` | line | FIR | local continuum + Gaussian forbidden lines | covariance |
| `ppxf_host` | host | optical–NIR | stellar templates + AGN power law, emission masked | pPXF formal errors |
| `crossband` | ratio | NIR–FIR | line-ratio consistency | analytic propagation |
| `cigale_sed` | **SED** | UV–FIR | SFH + BC03 + dust + DL2014 + SKIRTOR/Fritz | `pdf_analysis` posterior |
| `agnfitter_sed` | **SED** | UV–MIR | BC03 + S17 + THB21 BBB + SKIRTOR torus | `ultranest` posterior |

## What each new line tool measures

### CAFE

Public `GOALS-survey/CAFE` (v1.0.1).  Fits a 1-D spectrum or CRETA cube with
dust-grain continua (CIR/CLD/COO/WRM/HOT), direct-light components (STR/STB/DSK),
PAH Drude features, and H-recombination/atomic/molecular lines.  Broad
components are enabled per line in the line tables.  The runner writes a
compact line table, native ECSV/ASDF products, fit figure, and a
covariance/MC uncertainty figure.

### S3Fit

PyPI `s3fit==2.2.6` (Chen 2025).  Simultaneously fits a spectrum and photometric
SED; supports AGN power law, Fe II, Balmer continuum, torus, and multiple line
components (`narrow`, `AGN BLR`, `outflow`).  `num_mocks=N` generates mock
spectra and refits them, which is the tool's native Monte Carlo uncertainty
estimate.  It also supports Paα/Paβ/Brγ, so it can be used in the NIR.

### GANDALF

Marc Sarzi's GANDALF v1.5 (IDL) is the original pPXF+Gandalf method: pPXF fits
the stellar continuum, then gas templates are solved simultaneously with tied
kinematics; `FOR_ERRORS` enables MPFIT uncertainties.  It requires IDL (or a
working GDL compatibility layer), the IDL Astronomy Library, MPFIT and stellar
templates.  The implementation documents whether native GDL or a pPXF-gas
fallback was used; the method is never mislabelled.

### Official SDSS / IFU and X-ray exclusions

- **MaNGA DAP** and **LVM-DAP** are IFU-survey pipelines.  The MaNGA low-level
  `Sasuke.fit` path can consume one spectrum, but its line database has only
  narrow multiplet-tied Gaussians (no broad lines/Fe II/Balmer continuum), so
  it is a less capable duplicate of the existing fitters.  LVM's row-stacked
  degenerate case loses the LVM science products.  Both are excluded.
- The **SDSS spectroscopic pipeline** (`idlspec2d`) reduced these spectra; its
  official **`ZLINE`** product is used directly as the `sdss_zline` anchor.
  Re-running the IDL reduction is unnecessary.
- **AMARU** public v0.1 is not the updated version and needs external
  EMILES/Fe II/Balmer templates; it is excluded until those are public.
- **ELFO** and **AGNdecompose** are IFS/2-D image tools, not 1D AGN
  emission-line fitters; excluded.
- **pyspeckit** is a general line-fitting toolkit; it is redundant with the
  existing GLEAM/BADASS/local-Gaussian/PyQSOFit stack.
- **HEASOFT** is X-ray data reduction, not optical line fitting; see the
  HEASOFT section below.

### HEASOFT (X-ray)

The paper's HEASOFT use is Swift/XRT+UVOT reduction (`xrtpipeline`,
`xrtproducts`, `uvotimsum`, `uvotsource`) and Einstein Probe `FXTDAS/fxtchain`.
It is a separate X-ray branch, not an optical emission-line tool.  A proper
integration needs:

```bash
# inside a HEASOFT/HEASoftPy container with CALDB
xrtpipeline indir=... outdir=... steminputs=...
xrtproducts infile=... outdir=... regionfile=...
uvotimsum infile=... outfile=...
uvotsource image=... srcreg=... bkgreg=...
```

No X-ray event/spectrum data are in this repository, so HEASOFT is not added to
the line-tool matrix.  When X-ray data exist, add a separate `heasoft_xray`
Docker tool and a `route_analysis` branch; do not mix X-ray calibration with
optical line fitting.

### GalSpec / PyQSOFitSpec / QGfit / SHEAP

These four community 1-D codes were added and run on the real
`04592649654` SDSS spectrum:

| tool | fitted region/model | result |
|---|---|---|
| `galspec_line` | full-continuum global model, Fe II + Gaussian components | emcee MCMC, 37,334 saved samples; Hβ/[O III] = 2.21 (not 50-tau converged) |
| `pyqsofitspec_line` | UV/optical Fe II/Balmer + skew-normal lines | 53/55 valid parametric-bootstrap fits; Hβ/[O III] = 2.15 (Hβ 3525, [O III] 1639) |
| `qgfit` | AGN power law + Fe II + host + line complexes | long continuum MCMC, LSQ lines; Hβ/[O III] = 2.50 |
| `sheap_line` | Hβ/[O III] SPAF/JAX model, 4450-5450 Å, Fe II + 2 narrow components | 50-draw parametric bootstrap; Hβ/[O III] = 2.02, χ²_ν = 2.9; production |

GalSpec and PyQSOFitSpec are adopted as production alternatives.  QGfit is
kept with a caveat about its broader model.  SHEAP is retained in production
after the 2026-08 audit: the original 4.00 ratio was a model failure (600 km/s
narrow-FWHM cap, no Fe II, too narrow a window), not a property of the object.
See `docs/SHEAP_ASSESSMENT.md`.

### PAHFIT

Already used for MIR PAH/dust/gas decomposition.  The new statistics mode adds
per-feature uncertainty distributions and a line table; PAHFIT is not an MCMC
code.

## Routing examples

```bash
# SED only: no line measurements are implied
python pipeline/decide_tools.py --goal sed --z 0.59 --wave-min 3800 --wave-max 9200 --angstrom

# Optical lines at z=0.59
python pipeline/decide_tools.py --goal lines --z 0.59 --wave-min 3800 --wave-max 9200 --angstrom

# MIR lines/PAH at z=0.18
python pipeline/decide_tools.py --goal lines --z 0.18 --wave-min 5 --wave-max 28 --instrument JWST/MIRI

# NIR lines at z=6.327
python pipeline/decide_tools.py --goal lines --z 6.327 --wave-min 1.7 --wave-max 5.2
```

The decision engine is advisory; `inputs/<source>/source.json` still controls
which tools run.

## Configurations

Every tool has a reviewable configuration under `configs/<tool>/`; see
`configs/README.md`.  New tools consume their config through `--config` and the
run metadata records the exact file used.
