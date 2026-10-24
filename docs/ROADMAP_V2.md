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
| 1 | **QSOFITMORE** | UV/optical AGN spectrum fit | real SDSS QSO `04592649654` | in progress |
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
