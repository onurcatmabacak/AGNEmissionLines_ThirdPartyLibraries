# Official SDSS pipelines, community line fitters and HEASOFT

This note records what was adopted and what was deliberately excluded.  The
current sample is **1-D AGN spectroscopy** (SDSS single-fiber QSOs, JWST NIR/MIR,
Spitzer IRS, PACS/HIFI); it is not a MaNGA/LVM IFU sample and contains no X-ray
event files.

## Decision table

| code | type / input | verdict | reason / next step |
|---|---|---|---|
| **MaNGA DAP** (`sdss-mangadap` 4.5.0) | official SDSS IFU DAP; MaNGA `LOGRSS`/`LOGMAP` cubes | **exclude** | It cannot operate on single-fiber spectra. Add a `manga_dap` adapter only when a MaNGA cube + DRP products are ingested. |
| **LVM-DAP** (`sdss/lvmdap`, pyPipe3D/pyFIT3D) | official SDSS-V LVM IFU DAP | **exclude** | LVM IFU data products required; no LVM input here. |
| **SDSS spectroscopic pipeline** (`idlspec2d`) | data reduction (spectro1d/2d) | **exclude** | DR18 spectra are already reduced; this is not an emission-line fitter. |
| **GalSpec** | community 1-D AGN/galaxy line fit | **implemented** | `galspec_line`; emcee MCMC on reduced Hβ/[O III] window; real SDSS fit. |
| **PyQSOFitSpec** | community 1-D QSO line fit | **implemented** | `pyqsofitspec_line`; skew-normal profiles + 10-fit parametric bootstrap. |
| **QGfit** | community 1-D AGN/host/Fe II line fit | **implemented** | `qgfit`; real SDSS fit; short continuum MCMC and LSQ line errors. |
| **SHEAP** | community JAX AGN spectral decomposition | **implemented** | `sheap_line`; real Hβ/[O III] fit; JAX + 50-draw covariance MC (not MCMC). |
| **AMARU** | automated pPXF model selection | **exclude** | Public `amaru_v01` is not the updated release; needs external EMILES/Fe II/Balmer templates and a developer request. |
| **ELFO** | CSST-IFS emission-line fitting | **exclude** | IFS-only; no 1-D path. |
| **AGNdecompose** | 2-D AGN/host image decomposition | **exclude** | Image decomposition, not spectral line fitting. |
| **pyspeckit** | general 1-D line fitting | **exclude** | Redundant with GLEAM/BADASS/local-Gaussian/PyQSOFit; no AGN-specific advantage. |
| **HEASOFT** | X-ray data reduction/analysis | **exclude from line matrix** | X-ray branch; no event/spectrum inputs here. See below. |

## Official SDSS pipelines: why not used

`sdss-mangadap` is the MaNGA Data Analysis Pipeline.  Its `EmissionLineFit`
machinery expects MaNGA DRP `LOGRSS`/`LOGMAP` data with the MaNGA WCS and
instrument dispersion.  A single-fiber SDSS spectrum has no IFU dimensions and
no MaNGA DRP provenance, so running it would require inventing an IFU axis.

`lvmdap` is the SDSS-V Local Volume Mapper DAP built on `pyPipe3D`/`pyFIT3D`.
It likewise expects LVM IFU cubes and LVM-specific calibration.

`idlspec2d` is the SDSS spectroscopic **data-reduction** pipeline (spectro2d,
spectro1d, and their IDL/Python wrappers).  It produces calibrated spectra; it
does not replace a physical AGN emission-line decomposition.

If a MaNGA/LVM branch is added later, the correct design is:

```text
inputs/<source>/raw/manga_cube.fits
  -> manga_dap_adapter (DRP LOGRSS + redshift)
  -> sdss-mangadap EmissionLineFit
  -> outputs/<source>/manga_dap/
```

Do not feed single-fiber spectra into these DAPs.

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
| SHEAP | `feat/qgfit-sheap` / `08d5a814` | `outputs/04592649654_z_0.5874/sheap_line/` |

The line-ratio comparison now includes all four; the spread is
`docs/line_ratio_scatter.csv`.
