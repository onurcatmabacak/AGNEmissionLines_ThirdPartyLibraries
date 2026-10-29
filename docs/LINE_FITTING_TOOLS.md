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
| `optical_linefit` | line | optical | local linear continuum + Hβ broad/narrow + [O III] 4959/5007 tied doublet | least-squares covariance; independent local cross-check |
| `qsofitmore_line` | line | UV–optical | broken PL + V09 Fe II + Balmer continuum/high-order Balmer + broad/narrow Gaussians | lmfit parametric MC (200 draws), no MCMC |
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
| `manga_dap` | line (IFU) | optical | **official DAP**: HYB10 binning + pPXF + SASUKE 35-line Gaussian fit on MaNGA cubes | DAP formal covariance; **9 central bins only**; fast mode rejected |
| `xmm_xspec` | line (X-ray) | 0.5-10 keV observed; Fe K-alpha at 6.4 keV rest | **official XMM-Newton EPIC PPS**: `tbabs*(zpowerlw+zgauss)`, PN+MOS | XSPEC covariance; `Delta chi^2` line significance; no MCMC |
| `crossmission` | comparison (X-ray + UV/optical) | same object; Fe K-alpha vs H-beta/C IV | reads `xmm_xspec`/`rxte_xspec` + `pyqsofit_uv` or `optical_linefit` | no fit; quality-flagged comparison; 2 objects, no correlation |
| `rxte_xspec` | line (X-ray) | 3-20 keV observed; Fe K-alpha at 6.4 keV rest | **official RXTE/PCA stdprod**: `tbabs*(zpowerlw+zgauss)` | XSPEC covariance; `Delta chi^2` line significance; no MCMC |
| `ppxf_host` | host | optical–NIR | stellar templates + AGN power law, emission masked | pPXF formal errors |
| `crossband` | ratio | NIR–FIR | line-ratio consistency | analytic propagation |
| `cigale_sed` | **SED** | UV–FIR | SFH + BC03 + dust + DL2014 + SKIRTOR/Fritz | `pdf_analysis` posterior |
| `agnfitter_sed` | **SED** | UV–MIR | BC03 + S17 + THB21 BBB + SKIRTOR torus | `ultranest` posterior |

## What each new line tool measures

### QSOFITMORE

Public `rudolffu/qsofitmore` v1.2.2 at commit
`4c5f6e497b306aaf50b502a8e4b27ed9dfe89421` (GPL-3.0), a standalone
PyQSOFit-derived UV/optical QSO fitter.  The `qsofitmore_line` image uses the
package's default lmfit backend (no Kapteyn), the Verner et al. (2009) Fe II
template, the broken power law, the Dietrich et al. (2002) Balmer continuum
and the Storey & Hummer (1995) high-order Balmer series, and the package's
Monte Carlo error path (`MC=True, n_trails=200`).  qsofitmore 1.2.2 has no
`emcee`/MCMC sampler; the MC is a parametric bootstrap of the calibrated
errors, not a posterior.

The effective line table is the upstream example table with the [O III]
4959/5007 and outflow doublet ratios tied to 0.33.  H-alpha, C III] and C IV
are outside the `04592649654` SDSS rest-frame coverage (2247–6510 Å) and are
reported as `not_covered`.  The compact table recomputes each physical line
total from all Gaussian components because the package's
`<complex>_whole_br_area` column applies a 1200 km/s classifier and can omit
Gaussians that belong to the broad template.  On `04592649654`: Hβ
3076.6±100.1, [O III] 5007 1505.3±57.3, Hβ/[O III] **2.044±0.102**, Mg II
2540.8±209.4; the Hβ complex χ²_r is 17.9 (model mismatch, not a flux
failure).  The cross-tool median Hβ/[O III] is 2.044 with 0.053 dex scatter.
See `docs/MCMC_AND_STATISTICS.md` and
`outputs/qsofitmore_line/04592649654_z_0.5874/README.md`.

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

### MaNGA DAP (implemented, subset production)

The official SDSS-IV MaNGA DAP (`sdss-mangadap` 4.5.0, BSD-3-Clause) is
implemented in `Tools/manga_dap/` on the real MaNGA AGN NGC 1194
(plateifu 9193-12701).  The accepted product is a Stage-A official DAP run
(rdxqa + HYB10/S/N=50 binning + pPXF + `EMOM` + `INDXEN`) followed by the
**official full-method SASUKE emission-line model** (65 MaStar-HC2 templates,
`ELPMPL11`, `mdegree=14`) on the **9 central single-spaxel bins**.  The subset
reproduces the published DAP MAPS at those spaxels to <0.1% with 9/9 BPT
agreement.  The all-spaxel 2397-bin fit exceeded the 58 min wall-clock budget
and was killed; the published official MAPS is the all-spaxel reference.  A
fast fixed-continuum all-spaxel mode is retained only in `aux_fastmode/` with
`QUALITY='FASTMODE_NOT_PRODUCTION'` and is rejected as production (Hα ratio
2.37, BPT agreement 41%).  The DAP is a narrow-line model, not a broad-line
QSO fitter.

### Other official SDSS / IFU and X-ray exclusions

- **LVM-DAP** is an IFU-survey pipeline.  LVM's row-stacked degenerate case
  loses the LVM science products; excluded until LVM cubes are added.
- The **SDSS spectroscopic pipeline** (`idlspec2d`) reduced these spectra; its
  official **`ZLINE`** product is used directly as the `sdss_zline` anchor.
  Re-running the IDL reduction is unnecessary.
- **AMARU** public v0.1 is not the updated version and needs external
  EMILES/Fe II/Balmer templates; it is excluded until those are public.
- **ELFO** and **AGNdecompose** are IFS/2-D image tools, not 1D AGN
  emission-line fitters; excluded.
- **pyspeckit** is a general line-fitting toolkit; it is redundant with the
  existing GLEAM/BADASS/local-Gaussian/PyQSOFit stack.
- **HEASOFT** is X-ray spectral fitting, not optical line fitting; the
  implemented X-ray branch is separate and does not enter the line-ratio
  matrix.  See the X-ray section below.

### HEASOFT / RXTE PCA (implemented X-ray branch)

HEASOFT is the right engine for the X-ray part of the paper (RXTE/PCA,
XMM-Newton/EPIC, Swift/XRT+UVOT and Einstein Probe follow-up), but it is **not**
an optical emission-line fitter.  The repository now has an implemented,
separate X-ray branch:

```text
inputs/<source>/xray/rxte_<obsid>/*_s2.pha.gz   # official PCA Standard2 source
                                  *_b2.pha.gz   # official PCA background model
                                  *.rsp.gz      # official 5-PCU response
  -> Tools/rxte_xspec/ (HEASoft/PyXspec 13.0.0)
  -> tbabs*(zpowerlw+zgauss), 3-20 keV
  -> outputs/rxte_xspec/<source>/
```

The production example is **3C 120** (ObsID `10339-02-01-01`, 9808 s,
294,417 net counts); **MCG-6-30-15** (ObsID `20310-01-02-00`, 5888 s,
77,824 net counts) is the second independent AGN.  The products are the
official HEASARC **`stdprod`** products, i.e. the RXTE equivalent of the XMM
PPS products.  `pcabackest`/`saextrct` are **not** run.  The `b2` file is a
background **model**; its systematics are not in the chi-square errors.  See
`Tools/rxte_xspec/README.md`, `docs/ROADMAP_V2.md` and
`docs/OFFICIAL_PIPELINES_AND_XRAY.md`.

The `rxte_xspec` image is a thin `FROM xmm_xspec` layer, reusing the existing
HEASoft/PyXspec 13.0.0 installation rather than adding a second 4.3 GB X-ray
environment.  Swift/XRT+UVOT reduction (`xrtpipeline`, `xrtproducts`,
`uvotimsum`, `uvotsource`) and Einstein Probe `FXTDAS/fxtchain` remain
documented future work; they would be another image, not part of the optical
line matrix.

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

## Same-object Hβ coverage

The public PDS 456 HST/STIS UV spectrum does not cover Hβ.  The ESO
VLT/X-SHOOTER VIS spectrum (`ADP.2023-04-20T08:25:01.842`) fills that gap, and
`optical_linefit` fits Hβ + [O III] jointly.  The fit detects Hβ but has a high
formal χ² from absorption residuals, so the quality is **provisional**.
3C 120 has HST G430L+G750L coverage and is fitted independently by PyQSOFit and
QSOFITMORE; the Hβ/[O III] values (1.55 and 3.00) show the model-systematic
spread.

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

# X-ray Fe K-alpha at z=0.033 (RXTE/PCA; observed keV)
python pipeline/decide_tools.py --goal xray --z 0.033 --wave-min 3 --wave-max 20
```

The decision engine is advisory; `inputs/<source>/source.json` still controls
which tools run.

## Configurations

Every tool has a reviewable configuration under `configs/<tool>/`; see
`configs/README.md`.  New tools consume their config through `--config` and the
run metadata records the exact file used.
