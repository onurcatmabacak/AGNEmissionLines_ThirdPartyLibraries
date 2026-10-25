# Official SDSS pipelines, community line fitters and HEASOFT

This note records what was adopted and what was deliberately excluded.  The
current sample is **1-D AGN spectroscopy** (SDSS single-fiber QSOs, JWST NIR/MIR,
Spitzer IRS, PACS/HIFI); it is not a MaNGA/LVM IFU sample.  It contains no raw
X-ray event files, but it does now contain the official reduced RXTE/PCA
spectra used by the `rxte_xspec` branch.

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
| **HEASOFT** | X-ray spectral fitting (RXTE/PCA; Swift/XRT+UVOT future) | **implemented X-ray branch; exclude from the optical line matrix** | `rxte_xspec` fits official HEASARC PCA `stdprod` products with PyXspec 13.0.0.  Separate from the optical/IR line matrix.  See below. |

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

## HEASOFT / X-ray: official RXTE/PCA branch

HEASOFT is the right engine for the X-ray part of the paper, but it is **not**
an optical emission-line fitter and it is not part of the line-ratio matrix.
The repository now has one implemented X-ray branch in this worktree, `rxte_xspec`:

```text
inputs/<source>/xray/rxte_<obsid>/
  *_s2.pha.gz        # official HEASARC stdprod PCA Standard2 source
  *_b2.pha.gz        # official PCA background model
  *.rsp.gz           # official 5-PCU response matrix
  download.sh
  SHA256SUMS
    -> Tools/rxte_xspec/ (HEASoft 6.37 / PyXspec 13.0.0)
    -> outputs/<source>/rxte_xspec/
       rxte_spectrum_model_residual.png
       rxte_fe_ka_zoom.png
       rxte_fit.csv, rxte_lines.csv
       run.json, config.effective.json, xspec.log, provenance.md
```

The production example is **3C 120**, ObsID `10339-02-01-01`, PCA Standard2,
9808 s, 294,417 net counts; **MCG-6-30-15**, ObsID `20310-01-02-00`, 5888 s,
77,824 net counts, is the second independent AGN.  The model is
`tbabs*(zpowerlw+zgauss)` in 3-20 keV observed frame with the Fe K-alpha at
6.4 keV rest and a fixed 50 eV narrow core; the 3-10 keV fit is the line-band
cross-check.  See `docs/ROADMAP_V2.md` for the measured values.

### PPS-equivalent provenance and the raw-reduction caveat

The input files are the HEASARC **`stdprod`** products, the official reduced
PCA products.  They are the RXTE analogue of the XMM-Newton PPS products.
**`pcabackest` and `saextrct` are not run.**  A raw PCA reduction would need
the event files, housekeeping/particle-monitor screening, good-time intervals
and a newly generated background model; it would produce a different dataset.
The repository therefore fits the official archive products and records that
choice explicitly in `run.json` and `provenance.md`.  It does not claim to
reproduce the RXTE PCA reduction chain.

The `b2` file is a background **model**, not a measured background.  XSPEC
subtracts it and propagates its `STAT_ERR`, but the background-model
systematics (the dominant PCA uncertainty) are not in the chi-square errors.
The tool reports a conservative `nH`-frozen variant and a soft-blackbody
continuum-systematic check for this reason.

### Image reuse

`rxte_xspec` is a thin `FROM xmm_xspec` layer.  The existing `xmm_xspec` image
already contains XSPEC 13.0.0, HEASoft 6.37, CALDB and PyXspec; a second 4.3 GB
XSPEC environment would add no capability.  The `rxte_xspec` image is
4,346,170,410 bytes, only 217,048 bytes above the 4,345,953,362-byte base.

### What is still future work

Swift/XRT+UVOT reduction (`xrtpipeline`, `xrtproducts`, `uvotimsum`,
`uvotsource`) and Einstein Probe `FXTDAS/fxtchain` remain documented future
work.  They would be another image, not part of the optical line matrix.  A
same-object XMM/RXTE comparison (e.g. NGC 4151) is Stage 5 work; the current
XMM PDS 456 and RXTE 3C 120 results are independent AGN, not a
cross-calibration.

## Implemented in this pass

| tool | branch / commit | output |
|---|---|---|
| GalSpec | `galspec-line` / `4503e140` | `outputs/04592649654_z_0.5874/galspec_line/` |
| PyQSOFitSpec | `pi-agent-0616...` / `228a497e` | `outputs/04592649654_z_0.5874/pyqsofitspec_line/` |
| QGfit | `feat/qgfit-sheap` / `08d5a814` | `outputs/04592649654_z_0.5874/qgfit/` |
| SHEAP | `feat/qgfit-sheap` / `08d5a814`; audited/repaired (see `docs/SHEAP_ASSESSMENT.md`) | `outputs/04592649654_z_0.5874/sheap_line/` |
| MaNGA DAP | `feat/manga-dap` (this work) | `outputs/NGC1194_z_0.0136/manga_dap/` |
| RXTE/PCA | `rxte_xspec` (this work) | `outputs/3C120_z_0.0330/rxte_xspec/`, `outputs/MCG6-30-15_z_0.0077/rxte_xspec/` |

The line-ratio comparison now includes all implemented tools; the spread is
`docs/line_ratio_scatter.csv`.

## Same-object UV/optical data for the X-ray branches (Stage 5)

The X-ray fits are complemented by real **public HST/STIS** spectra from the
Hubble Spectroscopic Legacy Archive (HASP `cspec` products), downloaded from
MAST.  These are official reduced, flux-calibrated products, not synthetic
spectra and not re-reductions of raw STIS files.

| source | HST product | observed coverage | lines used | X-ray branch |
|---|---|---|---|---|
| **3C 120** | `hst_8700_stis_3c120d0_g430l-g750l_o62o_cspec.fits` | 2993-10247 A | H-beta, [O III] 4959/5007, H-alpha, [N II]/[S II] | RXTE/PCA |
| **PDS 456** | HST/STIS G140L+G230L + ESO X-SHOOTER VIS | 1139-3137 A (UV) + 5337-10200 A (optical) | C IV (UV); Hβ/[O III]/Hα (optical) | XMM-Newton |

Provenance:

* 3C 120: HST proposal 8700 (PI A. Martel), STIS G430L+G750L, 1440 s,
  2000-09-09, `LICENSE = CC BY 4.0`.
* PDS 456: HST proposal 8264 (PI P. O'Brien), STIS G140L+G230L, 1921 s,
  2000-09-15, `LICENSE = CC BY 4.0`; plus the public ESO VLT/X-SHOOTER VIS
  reduced spectrum `ADP.2023-04-20T08:25:01.842` (programme 111.24T0.001,
  2416 s) covering Hβ and [O III].
* Both files are committed with SHA-256; reproduce with
  `inputs/<source>/download_optical.sh`.

The HST spectra are fitted by `pyqsofit_uv` after a small, tested adapter in
`pipeline/prepare_inputs.py` converts `WAVELENGTH/FLUX/ERROR` tables to the
PyQSOFit cgs layout.  The HST `ivar` is stored in the repository's 1e-17
convention; a cgs/1e-17 mismatch was caught by the regression suite and fixed.

`pipeline/compare_xray_optical.py` then writes
`outputs/<source>/crossmission/`.  3C 120 is a **provisional** H-beta vs Fe K-alpha comparison because independent optical models give 1.55 and 3.00.  PDS 456 now uses a **local X-SHOOTER Hβ/[O III]** fit; the line is
detected but the formal local χ² is high, so the result is **provisional**, not
publication-grade.  The earlier HST C IV result is retained as UV context and
is not used as the primary comparison.  With two objects the
comparison is not a correlation fit.  The next step is to add more objects,
not to over-interpret these two points.
