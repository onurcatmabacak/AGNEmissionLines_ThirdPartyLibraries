# Official SDSS pipelines, community line fitters and HEASOFT

This note records what was adopted and what was deliberately excluded.  The
current sample is **1-D AGN spectroscopy** (SDSS single-fiber QSOs, JWST NIR/MIR,
Spitzer IRS, PACS/HIFI); it is not a MaNGA/LVM IFU sample and contains no X-ray
event files.

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
| **HEASOFT** | X-ray data reduction/analysis | **exclude from line matrix** | X-ray branch; no event/spectrum inputs here. See below. |

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

## HEASOFT / X-ray

HEASOFT is the right tool for the X-ray part of the paper (Swift/XRT and UVOT,
and Einstein Probe follow-up), but it is **not** an optical emission-line
fitter.  The paper's tasks are:

```text
xrtpipeline   # Swift/XRT event screening and exposure maps
xrtproducts   # XRT spectra/light curves and responses
uvotimsum     # UVOT exposure co-addition
uvotsource    # UVOT aperture photometry
FXTDAS/fxtchain  # Einstein Probe follow-up
```

A reproducible integration would be a separate image, not part of `Tools/` line
matrix:

```text
heasoft_xray/
  Dockerfile       # HEASOFT + CALDB + HEASoftPy
  run_xray.py      # xrtpipeline -> xrtproducts; UVOT branch
  configs/heasoft_xray/default/
```

with inputs such as:

```text
inputs/<source>/xray/swift_xrt/event.fits.gz
inputs/<source>/xray/swift_uvot/image.fits.gz
```

and outputs:

```text
outputs/<source>/heasoft_xray/{spectrum,response,lightcurve,uvot_photometry}/
```

The Python entry point is `heasoftpy`:

```python
from heasoftpy import heasoftpy
res = heasoftpy.xrtpipeline(indir="...", outdir="...", steminputs="...")
```

Requirements: HEASOFT (6.36+), CALDB, `HEADAS`/`CALDB` environment, and Swift/EP
data.  Since this repository has no X-ray event files, adding a 10+ GB HEASOFT
image now would not produce a tested science result.  The X-ray branch is
therefore documented, not faked.

## Implemented in this pass

| tool | branch / commit | output |
|---|---|---|
| GalSpec | `galspec-line` / `4503e140` | `outputs/04592649654_z_0.5874/galspec_line/` |
| PyQSOFitSpec | `pi-agent-0616...` / `228a497e` | `outputs/04592649654_z_0.5874/pyqsofitspec_line/` |
| QGfit | `feat/qgfit-sheap` / `08d5a814` | `outputs/04592649654_z_0.5874/qgfit/` |
| SHEAP | `feat/qgfit-sheap` / `08d5a814`; audited/repaired (see `docs/SHEAP_ASSESSMENT.md`) | `outputs/04592649654_z_0.5874/sheap_line/` |
| MaNGA DAP | `feat/manga-dap` (this work) | `outputs/NGC1194_z_0.0136/manga_dap/` |

The line-ratio comparison now includes all implemented tools; the spread is
`docs/line_ratio_scatter.csv`.
