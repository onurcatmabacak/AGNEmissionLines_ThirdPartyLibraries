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
| `xmm_xspec` | line (X-ray) | 0.5–10 keV observed (0.59–11.8 keV rest at z=0.184) | `tbabs*zpowerlw` + Fe Kα `zgauss`; per-instrument constants | XSPEC χ² + covariance; Δχ² line significance |
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
failure).  The cross-tool median Hβ/[O III] is 2.074 with 0.060 dex scatter.
See `docs/MCMC_AND_STATISTICS.md` and
`outputs/04592649654_z_0.5874/qsofitmore_line/README.md`.

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
- **HEASOFT/XSPEC** is implemented for the XMM-Newton X-ray branch
  (`xmm_xspec`), not as an optical line fitter; see the XMM-Newton section
  below.

### XMM-Newton EPIC (X-ray branch, implemented)

`xmm_xspec` is the repository's official X-ray spectral fit.  It is **not** an
optical emission-line fitter and is kept out of the line-ratio matrix; it fits
the broad-band EPIC continuum and the Fe Kα line.

The production test is **PDS 456**, ObsID `0721010201`, PN Large Window Thin1,
100.4 ks, 341,004 PN counts.  Inputs are the **official PPS** source spectra,
background spectra and source ARFs plus the official CCF responses (PN
`epn_e2_lw20_sdY9_v22.0.rmf`; MOS 15 eV canned matrices).  The PPS MOS spectra
are 2400 channels at 5 eV; they are rebinned 3:1 to 800 channels at 15 eV to
match the RMFs named in the PPS headers.  PN is used directly at 4096 channels.

```text
constant * tbabs * (zpowerlw + zgauss)          # 0.5-10 keV, joint PN+MOS
constant_PN = 1 (fixed); constant_MOS1/MOS2 free
zgauss: E_rest = 6.4 keV, sigma = 50 eV (narrow core)
```

Results (HEASoft/PyXspec 13.0.0, wilm abundances): joint baseline
χ²/dof = 879.03/516 = 1.704, Γ = 2.0221 ± 0.0041,
N_H = (2.304 ± 0.018) × 10²¹ cm⁻²; adding the narrow Fe Kα gives
χ²/dof = 862.64/515 = 1.675, **Δχ² = 16.39 (4.05σ)**, line flux
(2.01 ± 0.50) × 10⁻¹⁴ erg cm⁻² s⁻¹ and rest-frame EW 30.7 ± 7.6 eV.  The
MOS/PN constants are 1.0514 (MOS1) and 1.0422 (MOS2).  Independent fits:
PN 3.13σ, MOS2 2.45σ, MOS1 1.10σ; the line normalizations agree within 0.7σ,
while PN and MOS Γ differ by 2.9σ (a cross-calibration systematic).  A
blackbody soft-excess baseline still requires the line at 4.22σ.  The
free-width Gaussian runs to the fit bound (σ ≈ 1.16 keV) and is degenerate
with the continuum; it is not a resolved line width.

**SAS `epproc`/`especget`/`specgroup`/`epatplot` were not run.**  PPS spectra
are official SAS products (header `xmmsas_20241108_1150-21.0.0`); the raw-ODF
path is documented in `Tools/xmm_xspec/SAS_RAW_PATH.md`.  The PN RMF is CCF
v22.0, later than the 2024 PPS reduction.  There is no MCMC: errors are XSPEC
covariance 1σ and the line significance is Δχ².  Products:
`outputs/PDS456_z_0.1840/xmm_xspec/`.

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
