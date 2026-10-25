# Roadmap v2 — official mission pipelines

The goal is a **redshift-independent, multi-wavelength AGN factory**.  Each
stage is completed before the next starts, with the same acceptance gates:

1. Public code, pinned commit, licence and data provenance recorded.
2. Reproducible Docker image; no dependency installation in the shared venv.
3. A real downloaded dataset, not only a bundled example.
4. Full-capability fit, with the exact model/parameters documented.
5. Statistical evidence: uncertainties, residual/χ² diagnostics, and at least
   one independent cross-check.
6. Pedagogical README with commands, expected products, failure modes and a
   short “what this tool can and cannot measure”.
7. Repo contract: `Tools/<tool>/`, `Pipelines/run_<tool>_docker.sh`,
   `configs/<tool>/<variant>/`, `outputs/<source>/<tool>/`, registry/orchestrator
   entry, and a committed result figure.

## Planned sequence

| stage | mission/tool | official product | test data | status |
|---|---|---|---|---|
| 1 | **QSOFITMORE** | UV/optical AGN spectrum fit | real SDSS QSO `04592649654` | **complete** |
| 2 | **MaNGA DAP** | `sdss-mangadap` official IFU DAP | real MaNGA AGN cube | **complete (official subset; all-spaxel time-limited)** |
| 3 | **XMM-Newton** | PPS + HEASoft/PyXspec | real XMM/EPIC AGN observation | **complete (PPS+XSPEC; SAS raw reduction not run)** |
| 4 | **RXTE** | HEASoft + PyXspec | real RXTE/PCA AGN spectrum | **complete (3C 120 + MCG-6-30-15)** |
| 5 | cross-mission | X-ray/optical/SED comparison | 3C 120 + PDS 456 | **complete (same-object; 2 objects, no correlation fit)** |

## Wavelength coverage target

| band | existing tools | planned official/extra |
|---|---|---|
| UV | PyQSOFit, QSOFITMORE, GalSpec | HST/COS CALCOS for reduction |
| optical | PyQSOFit, BADASS, FANTASY, GELATO, GLEAM, S3Fit, GalSpec, QGfit, SHEAP, PyQSOFitSpec, **MaNGA DAP** | SDSS ZLINE; QSOFITMORE; MaNGA all-spaxel DAP |
| NIR | CAFE, S3Fit, nir_linefit, GANDALF | JWST/NIRSpec |
| MIR | CAFE, PAHFIT | JWST/MIRI, Spitzer IRS |
| FIR | fir_linefit, crossband | Herschel/PACS, ALMA/ADMIT |
| X-ray | **XMM/EPIC (`xmm_xspec`)**, **RXTE/PCA (`rxte_xspec`)** | Swift/XRT+UVOT, Einstein Probe; SAS raw reduction |

No single code covers all bands.  The decision engine must route by observed
band, rest-frame line coverage, data type and science goal (SED vs lines).

## Stage 1 result — QSOFITMORE

Pinned upstream `rudolffu/qsofitmore` v1.2.2 at commit
`4c5f6e497b306aaf50b502a8e4b27ed9dfe89421` (GPL-3.0), lmfit backend, no
Kapteyn.  The final image `qsofitmore_line` is 1,501,705,328 bytes (1.50 GB); the production run used the code-identical 1,501,705,246-byte image.  It bakes
and MD5-verifies the SFD98 map (DOI `10.7910/DVN/EWCNL5`), and records the map
version in `/app/cache/dustmaps/sfd/VERSION.json`.

The production fit used the V09 Fe II template, broken power law, Balmer
continuum/high-order Balmer series, SFD98+F99 foreground extinction, and
**200 lmfit Monte Carlo realizations** per complex (seed `20250101`).  Runtime
was 1,640.9 s (27m21s).  All 1,000 line-complex realizations were valid.

| quantity | QSOFITMORE | 1σ (MC) | note |
|---|---:|---:|---|
| Hβ total | 3076.6 | 100.1 | all Hb_br+Hb_na Gaussians |
| [O III] 5007 total | 1505.3 | 57.3 | core+outflow |
| Hβ/[O III] 5007 | 2.044 | 0.102 | MC p16–p84 1.960–2.103 |
| Mg II total | 2540.8 | 209.4 | broad+narrow |
| Hγ total | 1406.9 | 37.2 | |
| Fe II 4434–4684 Å | 736.4 | 13.9 | V09 pseudo-continuum |
| Balmer continuum norm | 8.28e-8 | 8.2e-10 | |

Cross-check: the Hβ/[O III] 5007 value is **2.044 ± 0.102**; the median of
PyQSOFit, GANDALF, S3Fit, GalSpec, PyQSOFitSpec, QGfit, SHEAP and SDSS ZLINE is
**2.044**, with **0.053 dex** tool-to-tool scatter.  PyQSOFit (1.96), GANDALF
(2.07) and SHEAP (2.02) are the closest.  An alternate BG92-VW01 Fe II fit
gives Hβ/O III = 2.34, i.e. the Fe II template is the dominant model
systematic.  Hα (6564.61 Å), C III] (1908.73 Å) and C IV (1549.06 Å) are outside
the SDSS rest-frame coverage (2247–6510 Å) and are reported as `not_covered`.

The Hβ complex χ²_r is 17.9 (the multi-Gaussian broad template plus V09/Balmer
continuum is not a complete physical description); Mg II is 1.38 and [O II]
3.98.  These are diagnostics, not acceptance gates.  qsofitmore 1.2.2 has no
MCMC sampler; the 200-draw lmfit parametric bootstrap is the native uncertainty
mode and is not described as a posterior.


## Stage 2 result — MaNGA DAP (official subset)

Pinned `sdss-mangadap` **4.5.0** at upstream commit
`996b46cb9739126fe0fbe69c1a50d8490d924853` (BSD-3-Clause).  The image
`manga_dap` is **1,853,913,965 bytes** (1.85 GB) and ships the official
MILES-HC and MaStar-HC2 templates plus `ELPMPL11`, `ELPSCMSK`, `BADSKY` and
`sdssMaskbits.par` inside the wheel.

Source: real MaNGA AGN **NGC 1194**, plateifu **9193-12701**, `z=0.0136253`
(NSA v1_0_1), MaNGA AGN Catalog VAC (Comerford et al. 2020).  The DR17
LOGCUBE (207,992,431 B) and LOGRSS (169,194,046 B) are downloaded unmodified
by `inputs/NGC1194_z_0.0136/download.sh` and are Git-ignored (over GitHub's
100 MB limit); the published DAP MAPS (10,775,592 B) is committed as the
all-spaxel reference.

**Accepted result.**  Official DAP Stage A (rdxqa, HYB10/S/N=50 binning,
pPXF stellar kinematics, `EMOM` moments, `INDXEN` indices; 1741.7 s) followed
by the **official full-method SASUKE** emission-line model (65 MaStar-HC2
templates, `ELPMPL11`, `mdegree=14`, `deconstruct_bins='ignore'`) on the
**9 central single-spaxel bins** (393.4 s, 9/9 fits).  Against the published
MAPS at the same spaxels, Hα/Hβ/[O III]/[N II]/[S II] median ratios are
**0.9995-0.99999** (Pearson r > 0.99998) and BPT agrees **9/9**.  The subset
MAPS, central spectrum/model, 9-bin line table, comparison and figures are
committed.

**Time-budget limitation.**  A full all-spaxel HYB10/S/N=10 run produced
**2397 bins**; the 65-template SASUKE fit reached 157/2397 spectra and was
killed at the **3500 s (58 min)** cap.  No all-spaxel MAPS was produced.  The
published official MAPS is the all-spaxel reference; the exact log is
`outputs/NGC1194_z_0.0136/manga_dap/logs/full_dap_attempt_summary.txt`.

**Fast mode rejected.**  A fixed-continuum all-spaxel diagnostic (175 bins)
gives Hα ratio 2.37, [N II] 0.53, BPT agreement 41% and a +175 km/s gas
velocity offset.  It is confined to `aux_fastmode/` with
`QUALITY='FASTMODE_NOT_PRODUCTION'`, `PRODSTAT='AUXILIARY'`, `ACCEPT=0` and is
not an acceptance product.

## Stage 4 result - official RXTE/PCA (HEASoft/PyXspec)

Pinned HEASARC conda **XSPEC 13.0.0** (`hb0f4dca_2`) on **HEASoft 6.37**
(PyXspec), reused from the existing `xmm_xspec` image.  The `rxte_xspec`
image is a thin `FROM xmm_xspec` layer: **4,346,170,410 bytes** (4.35 GB),
only 217,048 bytes above the 4,345,953,362-byte base.  A second 4.3 GB XSPEC
installation was deliberately avoided.

**Data.**  Official HEASARC RXTE/PCA **`stdprod`** products, i.e. the RXTE
equivalent of the XMM-Newton PPS products, for **3C 120**, ObsID
`10339-02-01-01` (AO1/P10339), PCA Standard2, **9808 s**, **294,417 net
counts** in 129 channels.  The committed input files are the official
`xp10339020101_s2.pha.gz` (source), `xp10339020101_b2.pha.gz` (background
model) and `xp10339020101.rsp.gz` (5-PCU response), with `download.sh` and
`SHA256SUMS`.  The response is the real 129-channel PCA matrix (300 energy
bins, `marfrmf 3.2.6`); no synthetic response is used.  **`pcabackest` and
`saextrct` are not run** - the archive `stdprod` products already contain the
official reduction.  The `b2` file is a background **model**, not a measured
background; this is the dominant PCA caveat.

**Accepted model.**  `tbabs*(zpowerlw+zgauss)` in the observed 3-20 keV band,
`chi` statistic, Wilms abundances, Fe K-alpha at 6.4 keV rest with a fixed
50 eV narrow core.  The 3-10 keV line-band fit is the local-continuum
cross-check.  Runtime is 5.5 s inside the container.

| quantity | 3C 120, 3-20 keV (production) | 3C 120, 3-10 keV cross-check |
|---|---:|---:|
| baseline `tbabs*zpowerlw` chi2/dof | 89.85/49 = 1.834 | 42.11/22 = 1.914 |
| `tbabs*(zpowerlw+zgauss)` chi2/dof | **72.02/48 = 1.500** | **19.90/21 = 0.947** |
| photon index Gamma | **1.8163 +/- 0.0240** | 1.6880 +/- 0.0364 |
| N_H (10^22 cm^-2) | **3.06 +/- 0.51** | 1.36 +/- 0.61 |
| Fe K-alpha Delta chi2 (1 dof) | **17.83 -> 4.22 sigma** | **22.22 -> 4.71 sigma** |
| Fe K-alpha flux (erg cm^-2 s^-1) | **(5.03 +/- 1.17)e-13** | (5.54 +/- 1.15)e-13 |
| EW_rest (eV) | **90.3** | 102.7 |

**Systematic variants (3C 120).**  Freezing N_H to the continuum-only value
gives Delta chi2 = 11.94 (3.46 sigma), flux 3.43e-13 and EW_rest 59.6 eV.
Adding a soft blackbody continuum (`tbabs*(zpowerlw+zbbody+zgauss)`) gives
Delta chi2 = 53.91 (7.34 sigma), flux 5.21e-13 and EW_rest 95.4 eV; the
soft-excess fit has chi2/dof = 39.62/46 = 0.861.  The 3-10 keV free-width fit
gives sigma = 0.60 +/- 0.25 keV (Delta chi2 = 24.96 for 2 dof, 4.62 sigma) and
the free-centroid fit gives E_rest = 6.39 +/- 0.19 keV, sigma = 0.62 +/- 0.28
keV (4.32 sigma).  The width is not a resolved velocity measurement.

**Second independent AGN.**  MCG-6-30-15, ObsID `20310-01-02-00` (AO2/P20310,
5888 s, 77,824 net counts): `tbabs*(zpowerlw+zgauss)` in 3-20 keV gives
chi2/dof = **39.41/41 = 0.961**, Gamma = **1.867 +/- 0.048**, N_H =
**(2.40 +/- 1.03)e22 cm^-2**, Delta chi2 = **46.48 (6.82 sigma)**, flux
**(1.10 +/- 0.15)e-12 erg cm^-2 s^-1**, EW_rest = **263.5 eV**.  The 3-10 keV
cross-check gives Delta chi2 = 45.36 (6.74 sigma).  The Galactic-`nH`
diagnostic gives Delta chi2 = 91.38 (9.56 sigma) on a poor chi2/dof =
135.98/43 baseline, the same continuum-mismatch behaviour as 3C 120.  This is
the stronger of the two PCA detections and confirms the pipeline on a second
real AGN.

**The expected Delta chi2 ~ 82 caveat.**  The verified-data note quotes
Delta chi2 ~ 82 for the 3C 120 Fe K-alpha in 3-20 keV.  That larger value is
reproduced only if `nH` is **frozen at a low, Galactic-scale value**.  With
`nH = 0.024 x 10^22 cm^-2`, the diagnostic baseline is chi2/dof =
**198.45/50 = 3.97**, and adding the narrow line gives chi2/dof = 109.11/49 =
2.23, Delta chi2 = **89.33 (9.45 sigma)**, flux 8.77e-13 and EW_rest 171.6 eV.
That is the family of fits behind the ~82 quote (at `nH = 0.5e22` the same
baseline gives Delta chi2 = 76.8).  The baseline is a poor continuum
description, so the line is absorbing continuum residuals; this variant is
reported as a diagnostic, **not** as the production measurement.

With `nH` free and the official background model, the production fit gives
Delta chi2 = **17.83 (4.22 sigma)**.  The value depends strongly on the
continuum/background treatment: a soft-blackbody continuum reaches 53.91
(7.34 sigma), while a fixed-`nH` (continuum-value) conservative fit gives 11.94
(3.46 sigma).  The detection is significant in every variant (3.5-9.6 sigma),
but the exact Delta chi2 is not a robust headline number.  The production
choice is the free-`nH` baseline because it is the statistically adequate
continuum description (`chi2/dof = 1.83` before the line, 1.50 after), whereas
the Galactic-`nH` baseline is not (`chi2/dof = 3.97`).

**Cross-mission note.**  The `xmm_xspec` branch is the XMM-Newton EPIC PPS
fit of **PDS 456** (ObsID `0721010201`, z = 0.184, 100.4 ks): narrow Fe K-alpha
Delta chi2 = 16.39 (4.05 sigma) with the same absorbed power-law model.  The
`rxte_xspec` branch reuses `xmm_xspec` as its HEASoft/PyXspec base and fits
3C 120.  PDS 456 and 3C 120 are **independent AGN**, not a same-object
cross-calibration.  **NGC 4151** is the natural same-object XMM/RXTE anchor,
but its PCA background systematics are severe; it is not used here for a
same-object claim.  The X-ray pair is therefore a methodological cross-check
(independent objects, independent missions), not a cross-calibration.

Stage 5 extends each object with a real **same-object** UV/optical spectrum
(HST/STIS and X-SHOOTER) and compares Fe K-alpha with H-beta (both objects);
see the Stage 5 result below.

**Raw-vs-PPS provenance.**  The `stdprod` products are the official reduced
PCA products.  Re-running `pcabackest`/`saextrct` from raw PCA event files
would change the good-time intervals, background model and response; it would
not be the same dataset.  The tool therefore fits the official products and
records the choice in `run.json` and `provenance.md`.  It does not claim to
reproduce the RXTE PCA reduction chain.  This is the RXTE analogue of using
XMM PPS spectra instead of re-running SAS.

## Stage 5 result - same-object X-ray / UV-optical line comparison

Two real archival spectra were added without touching the X-ray products:

| source | optical/UV data | X-ray branch | line used | result |
|---|---|---|---|---|
| **3C 120** | HST/STIS G430L+G750L HASP `cspec`, 2993-10247 A | RXTE/PCA `stdprod` | broad H-beta + [O III] 5007 | H-beta 28436, [O III] 18363, ratio **1.55**; H-beta FWHM 2676 km/s (S/N 17.9) |
| **PDS 456** | HST/STIS UV + ESO X-SHOOTER VIS | XMM-Newton PPS | local Hβ/[O III] | Hβ **33448**, [O III] 5007 **5580**, ratio **5.99**; χ²_red 430; **provisional** |

The public HST/STIS spectrum of PDS 456 does **not** cover H-beta (5758 A
observed) or Mg II (3315 A); only Ly-alpha, N V, C IV and C III] are available.
A public ESO VLT/X-SHOOTER VIS reduced spectrum fills that gap and is now used
for a **local** Hβ/[O III] fit.  The local fit has high formal χ² because the
X-SHOOTER spectrum contains absorption residuals; the ratio is therefore
labelled provisional.  The HST/STIS spectrum of 3C 120 covers H-beta,
[O III], H-alpha and [N II]/[S II].

`pipeline/compare_xray_optical.py` writes
`outputs/<source>/crossmission/xray_optical_comparison.{json,csv,md,png,pdf}`.
The 3C 120 comparison is **provisional** because independent optical models disagree (Hβ/[O III] 1.55 vs 3.00).  The PDS 456 comparison
now uses the X-SHOOTER **Hβ** local fit but is **provisional** because the local
fit has high formal χ²; it is not the earlier C IV-only tentative result.  With
two objects the tool does **not** fit a slope or claim a correlation; adding
more objects is the next scientific step.

The HST files are 57 KB and 45 KB; the X-SHOOTER VIS file is 1.3 MB.  All are
committed with SHA-256 and reproduced by `inputs/<source>/download_optical.sh`.
A unit-conversion bug in
the HST `ivar` path (cgs vs the repository's 1e-17 convention) was found by the
pytest golden suite and fixed before the production results were accepted.

## Engineering additions

* `workflow/Snakefile` runs the Docker graph through Snakemake, with explicit
  `s3fit_line -> pyqsofit_uv` and `crossmission -> pyqsofit_uv + X-ray` edges.
* `tests/` contains unit tests plus golden scientific reference values for
  QSOFITMORE, XMM, RXTE, MaNGA and the cross-mission comparison.
* `schemas/output_catalog.schema.json` plus `pipeline/validate_outputs.py`
  formalise and verify the `outputs/<source>/<tool>/` contract.
* `configs/caveats.yaml` is the source of truth for the rendered
  `docs/CAVEAT_MATRIX.md`; every registered tool must have an entry.
