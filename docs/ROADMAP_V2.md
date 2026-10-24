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
| 3 | **XMM-Newton** | SAS + XGA/XSPEC | real XMM/EPIC AGN observation | planned |
| 4 | **RXTE** | HEASoft + PyXspec | real RXTE/PCA AGN spectrum | planned |
| 5 | cross-mission | X-ray/optical/SED comparison | combined source products | planned |

## Wavelength coverage target

| band | existing tools | planned official/extra |
|---|---|---|
| UV | PyQSOFit, QSOFITMORE, GalSpec | HST/COS CALCOS for reduction |
| optical | PyQSOFit, BADASS, FANTASY, GELATO, GLEAM, S3Fit, GalSpec, QGfit, SHEAP, PyQSOFitSpec, **MaNGA DAP** | SDSS ZLINE; QSOFITMORE; MaNGA all-spaxel DAP |
| NIR | CAFE, S3Fit, nir_linefit, GANDALF | JWST/NIRSpec |
| MIR | CAFE, PAHFIT | JWST/MIRI, Spitzer IRS |
| FIR | fir_linefit, crossband | Herschel/PACS, ALMA/ADMIT |
| X-ray | none yet | XMM/SAS+XGA, RXTE/HEASoft+PyXspec |

No single code covers all bands.  The decision engine must route by observed
band, rest-frame line coverage, data type and science goal (SED vs lines).

## Stage 1 result — QSOFITMORE

Pinned upstream `rudolffu/qsofitmore` v1.2.2 at commit
`4c5f6e497b306aaf50b502a8e4b27ed9dfe89421` (GPL-3.0), lmfit backend, no
Kapteyn.  The image `qsofitmore_line` is 1,501,705,246 bytes (1.50 GB), bakes
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
**2.074**, with **0.060 dex** tool-to-tool scatter.  PyQSOFit (1.96), GANDALF
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
