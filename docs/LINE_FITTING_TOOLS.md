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
| `galspec_line` | line | optical | reduced H-beta/[O III] window + Fe II, GalSpec Astropy Gaussians | emcee posterior (dynesty optional) |
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
