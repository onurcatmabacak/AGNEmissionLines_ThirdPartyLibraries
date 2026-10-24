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
| 2 | **MaNGA DAP** | `sdss-mangadap` official IFU DAP | real MaNGA AGN cube | planned |
| 3 | **XMM-Newton** | SAS + XGA/XSPEC | real XMM/EPIC AGN observation | planned |
| 4 | **RXTE** | HEASoft + PyXspec | real RXTE/PCA AGN spectrum | planned |
| 5 | cross-mission | X-ray/optical/SED comparison | combined source products | planned |

## Wavelength coverage target

| band | existing tools | planned official/extra |
|---|---|---|
| UV | PyQSOFit, QSOFITMORE, GalSpec | HST/COS CALCOS for reduction |
| optical | PyQSOFit, BADASS, FANTASY, GELATO, GLEAM, S3Fit, GalSpec, QGfit, SHEAP, PyQSOFitSpec | SDSS ZLINE; QSOFITMORE |
| NIR | CAFE, S3Fit, nir_linefit, GANDALF | JWST/NIRSpec |
| MIR | CAFE, PAHFIT | JWST/MIRI, Spitzer IRS |
| FIR | fir_linefit, crossband | Herschel/PACS, ALMA/ADMIT |
| X-ray | none yet | XMM/SAS+XGA, RXTE/HEASoft+PyXspec |

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
