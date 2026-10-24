# Official SDSS pipelines, community line fitters and HEASOFT

This note records what was adopted and what was deliberately excluded.  The
current sample is **1-D AGN spectroscopy** (SDSS single-fiber QSOs, JWST NIR/MIR,
Spitzer IRS, PACS/HIFI) plus a real **XMM-Newton EPIC** X-ray spectrum.  It is
not a MaNGA/LVM IFU sample and contains no X-ray event files: the X-ray branch
starts from the official PPS reduced spectra.

## Decision table

| code | type / input | verdict | reason / next step |
|---|---|---|---|
| **MaNGA DAP** (`sdss-mangadap` 4.5.0) | official SDSS IFU DAP; MaNGA `LOGCUBE`/`LOGRSS` cubes | **implemented (official subset)** | `manga_dap`; real NGC 1194 LOGCUBE, Stage-A official DAP (binning, pPXF, moments, indices) and official full-method SASUKE on 9 central single-spaxel bins.  The all-spaxel 2397-bin fit exceeded the 58 min budget; published MAPS is the all-spaxel reference.  Fast mode is auxiliary and rejected as production.  Narrow-line DAP, not a broad-line QSO fitter. |
| **LVM-DAP** (`sdss/lvmdap`, pyPipe3D/pyFIT3D) | official SDSS-V LVM IFU DAP | **exclude** | LVM IFU data products required; a row-stacked single spectrum is technically readable but all LVM binning/map products and the science case disappear. |
| **SDSS spectroscopic pipeline** (`idlspec2d`) | data reduction + `speclinefit` | **exclude code; use product** | The spectra are already RUN2D v6_0_4 products. Their `ZLINE` HDU is the official line-fit product and is now included as the `sdss_zline` anchor in the comparison. The reduction code itself is not needed. |
| **GalSpec** | community 1-D AGN/galaxy line fit | **implemented** | `galspec_line`; full-continuum 2280-6460 A model with Fe II, Balmer/[O II]/[Ne III]/[O III] lines; emcee MCMC; real SDSS fit. |
| **PyQSOFitSpec** | community 1-D QSO line fit | **implemented** | `pyqsofitspec_line`; skew-normal profiles + 10-fit parametric bootstrap. |
| **QGfit** | community 1-D AGN/host/Fe II line fit | **implemented** | `qgfit`; real SDSS fit; short continuum MCMC and LSQ line errors. |
| **SHEAP** | community JAX AGN spectral decomposition | **implemented** | `sheap_line`; real Hβ/[O III] fit; JAX + 50-draw parametric-bootstrap MC (not MCMC). |
| **AMARU** | automated pPXF model selection | **exclude** | Public `amaru_v01` is not the updated release; needs external EMILES/Fe II/Balmer templates and a developer request. |
| **ELFO** | CSST-IFS emission-line fitting | **exclude** | IFS-only; no 1-D path. |
| **AGNdecompose** | 2-D AGN/host image decomposition | **exclude** | Image decomposition, not spectral line fitting. |
| **pyspeckit** | general 1-D line fitting | **exclude** | Redundant with GLEAM/BADASS/local-Gaussian/PyQSOFit; no AGN-specific advantage. |
| **HEASOFT / XSPEC** | X-ray spectral fitting | **implemented as `xmm_xspec`** | Official XMM-Newton PPS spectra, source ARFs, backgrounds and CCF responses; HEASoft/PyXspec 13.0.0.  This is an X-ray branch, not an optical line tool.  SAS raw reduction and Swift/EP event pipelines remain future work. |

## Official SDSS pipelines: what is and is not usable

`sdss-mangadap` is the MaNGA Data Analysis Pipeline.  Its survey path requires
`SpatiallyBinnedSpectra`/MaNGA datacubes.  The upstream documentation also
provides a low-level *fit one spectrum* path (`Sasuke.fit`), which can consume
the DR18 `COADD` arrays if a BOSS LSF (`obj_sres`) is synthesized.  It is still
excluded: the DAP line database contains single-Gaussian, multiplet-tied
narrow lines, with no broad-line, Fe II or Balmer-continuum components — the
dominant physics in these QSOs.  A 1-D adapter would be a less capable duplicate
of `ir_linefit`/`pyqsofit_uv` at ~2 GB image cost.

`lvmdap` is the SDSS-V Local Volume Mapper DAP built on `pyPipe3D`/`pyFIT3D`.
It expects LVM IFU cubes; a row-stacked spectrum is technically readable but
the LVM binning, maps and calibration are meaningless.

`idlspec2d` is the SDSS BOSS data-reduction pipeline.  Its `pro/spec1d/speclinefit.pro`
produces the `ZLINE` HDU found in our `spec-*.fits` files.  We do **not** re-run
the IDL reduction; we use the already-produced **`ZLINE`** measurements as the
official SDSS anchor in `pipeline/compare_line_tools.py`.  For `04592649654`,
ZLINE gives Hβ/[O III] 5007 = **1.57 ± 0.014**, compared with 1.83–2.50 from
the independent fitters.

The implemented MaNGA branch is:

```text
inputs/NGC1194_z_0.0136/raw/manga-9193-12701-LOGCUBE.fits.gz
  -> official MaNGADataCube + LOGRSS covariance
  -> official manga_dap() Stage A (HYB10/S/N=50, pPXF, EMOM, INDXEN)
  -> official full-method SASUKE on 9 central bins (65 MaStar-HC2 templates)
  -> outputs/NGC1194_z_0.0136/manga_dap/
```

The all-spaxel 2397-bin emission-line fit is a documented time-budget
limitation, not a hidden success.  Do not feed single-fiber spectra into the
MaNGA DAP, and do not call the fast fixed-continuum all-spaxel product the
production DAP.

## XMM-Newton EPIC (implemented) and Swift/EP (future)

HEASOFT is the right tool for the X-ray part of the paper, and the XMM-Newton
branch is now **implemented** with real data.  It is not an optical
emission-line fitter and is kept outside the line-tool matrix.

### Implemented: `xmm_xspec` (PPS + PyXspec)

The production test is **PDS 456**, XMM-Newton ObsID `0721010201`, PN Large
Window Thin1, 100.4 ks, 341,004 PN counts.  Inputs are the official PPS source
spectra, background spectra and source ARFs, plus the CCF responses (PN
`epn_e2_lw20_sdY9_v22.0.rmf`, MOS 15 eV canned matrices).  The MOS PPS spectra
are 2400 channels at 5 eV and are rebinned 3:1 to 800 channels at 15 eV to
match the matrices named in the PPS headers; PN is used directly at 4096
channels.

```text
inputs/PDS456_z_0.1840/xray/xmm_0721010201/
  -> PPS spectra + backgrounds + ARFs (official SAS products)
  -> PN direct; MOS 5 eV -> 15 eV channel rebin
  -> PyXspec 13.0.0: constant*tbabs*(zpowerlw + zgauss), 0.5-10 keV
  -> outputs/PDS456_z_0.1840/xmm_xspec/
```

The joint PN+MOS fit gives χ²/dof = 879.03/516 = 1.704, Γ = 2.0221 ± 0.0041,
N_H = (2.304 ± 0.018) × 10²¹ cm⁻², and a 50 eV Fe Kα line at 6.4 keV rest with
Δχ² = 16.39 (4.05σ), flux (2.01 ± 0.50) × 10⁻¹⁴ erg cm⁻² s⁻¹ and rest-frame
EW 30.7 ± 7.6 eV.  A blackbody soft-excess baseline still requires the line at
4.22σ.  The free-width fit prefers a broad component but the width is at the
fit bound and degenerate with the continuum; it is not a resolved line width.

**SAS was not run.**  The PPS spectra are official SAS pipeline products
(header `xmmsas_20241108_1150-21.0.0`); re-running the ~16.5 GB SAS image and
~2.9 GB CCF was outside this test's budget.  The optional raw-ODF path is
documented in `Tools/xmm_xspec/SAS_RAW_PATH.md`:

```bash
# inside a SAS + HEASoft container with ODF/CCF mounted (NOT run here)
epproc
especget eventset=PN_events.fits srcregionfile=... backregfile=... ...
specgroup spectrumset=mos1_source.fits groupedset=mos1_source_15eV.fits ...
epatplot set=pn_source.fits
```

The PN RMF is the current CCF v22.0 matrix, later than the 2024 PPS reduction;
this is a response-version systematic.  The PPS MOS 5 eV -> 15 eV rebin and the
`RMF FILTER=Medium` vs observation `Thin1` warning are documented in the tool
README and `run.json`.  There is no MCMC: errors are XSPEC covariance 1σ and
the line significance is Δχ².

### Future: Swift/XRT, UVOT and Einstein Probe

The paper's other HEASOFT tasks remain separate:

```text
xrtpipeline   # Swift/XRT event screening and exposure maps
xrtproducts   # XRT spectra/light curves and responses
uvotimsum     # UVOT exposure co-addition
uvotsource    # UVOT aperture photometry
FXTDAS/fxtchain  # Einstein Probe follow-up
```

They need event files and CALDB, not PPS spectra.  A future image can follow the
same pattern:

```text
Tools/swift_xrt/
  Dockerfile       # HEASOFT + CALDB + HEASoftPy
  run_xray.py      # xrtpipeline -> xrtproducts; UVOT branch
configs/swift_xrt/default/
inputs/<source>/xray/swift_xrt/event.fits.gz
outputs/<source>/swift_xrt/{spectrum,response,lightcurve,uvot_photometry}/
```

with `heasoftpy.xrtpipeline(...)`.  This is planned, not implemented.

## Implemented in this pass

| tool | branch / commit | output |
|---|---|---|
| GalSpec | `galspec-line` / `4503e140` | `outputs/04592649654_z_0.5874/galspec_line/` |
| PyQSOFitSpec | `pi-agent-0616...` / `228a497e` | `outputs/04592649654_z_0.5874/pyqsofitspec_line/` |
| QGfit | `feat/qgfit-sheap` / `08d5a814` | `outputs/04592649654_z_0.5874/qgfit/` |
| SHEAP | `feat/qgfit-sheap` / `08d5a814`; audited/repaired (see `docs/SHEAP_ASSESSMENT.md`) | `outputs/04592649654_z_0.5874/sheap_line/` |
| MaNGA DAP | `feat/manga-dap` (this work) | `outputs/NGC1194_z_0.0136/manga_dap/` |
| XMM-Newton EPIC | `xmm_xspec` (this work) | `outputs/PDS456_z_0.1840/xmm_xspec/` |

The line-ratio comparison now includes all implemented tools; the spread is
`docs/line_ratio_scatter.csv`.
