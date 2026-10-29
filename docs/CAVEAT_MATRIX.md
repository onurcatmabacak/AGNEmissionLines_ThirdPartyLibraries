# Caveat matrix

Generated from `configs/caveats.yaml` by `pipeline/build_caveat_matrix.py`.
`status` is what the repository actually validated; `severity` is the
scientific impact if the caveat is ignored.

| tool | kind | wave | status | severity | caveat | evidence / mitigation |
|---|---|---|---|---|---|---|
| `pyqsofit_uv` | line | UV/optical | **production** | medium | Global continuum+Fe II fit; broad-line totals are stable but component splits are degenerate. The PDS 456 HST/STIS C IV fit is tentative (S/N < 3). The short MCMC chain is not converged; the committed uncertainty for the SDSS QSO is the 100-realization MC. | outputs/pyqsofit_uv/PDS456_z_0.1840/, outputs/pyqsofit_uv/3C120_z_0.0330/, docs/MCMC_AND_STATISTICS.md<br>*Mitigation:* Use line totals; treat PDS 456 C IV as tentative; do not quote the short MCMC as an error bar. |
| `optical_linefit` | line | optical | **conditional** | medium | Local H-beta/[O III] fit, independent of global QSO models. PDS 456 uses the public X-SHOOTER VIS spectrum and detects H-beta, but the formal chi-square is high (absorption/continuum residuals) and the ratio is provisional. | outputs/optical_linefit/PDS456_z_0.1840/, docs/SCIENCE_RESULTS.md<br>*Mitigation:* Use it as a local cross-check; inspect optical_fit.png and the quality flag before quoting a ratio. |
| `qsofitmore_line` | line | UV/optical | **production** | low | No native MCMC; 200 lmfit MC draws. H-beta total includes broad+narrow; Mg II is bimodal and component-level H-beta is degenerate. | outputs/qsofitmore_line/04592649654_z_0.5874/, docs/MCMC_AND_STATISTICS.md<br>*Mitigation:* Quote total line fluxes and the MC interval; use the 16-84% range for Mg II. |
| `ir_linefit` | line | UV/optical/NIR/MIR/FIR | **production** | low | Local Gaussian fits with a generic continuum; not a full AGN/host decomposition and not a substitute for PyQSOFit/CAFE. | docs/LINE_FITTING_TOOLS.md<br>*Mitigation:* Use for individual line checks and ratios, not global continuum physics. |
| `nir_linefit` | line | NIR | **production** | medium | Depends on the x1d extraction and optional PSF aperture; line fluxes are aperture-sensitive. | outputs/nir_linefit/J0100p2802_z_6.3270/<br>*Mitigation:* Report the extraction/PSF variant used; compare pipeline and PSF apertures. |
| `pahfit_mir` | line | MIR | **conditional** | high | All production fits are flagged/systematics-limited: VV114 hot-dust mismatch, PDS 456 wavelength gaps, NGC 4151 residuals and NGC 253 gaps. Historical NGC 253 tails are unstable; PAHFIT does not prove a unique dust decomposition. | docs/CAVEAT_FIXES.md, outputs/*/pahfit_mir/run.json<br>*Mitigation:* Quote robust line fluxes with flags; do not interpret PAH/dust components as unique. |
| `fir_linefit` | line | FIR | **production** | medium | PACS/HIFI calibration and aperture mismatch; local Gaussian fit is not a full FIR SED. | outputs/fir_linefit/NGC1068_z_0.0038/, outputs/fir_linefit/NGC253_z_0.0008/<br>*Mitigation:* Use common apertures and report calibration systematics. |
| `cafe_line` | line | NIR/MIR | **conditional** | high | Full all-line VV114 fit exceeds the practical time budget; production is a documented line/PAH subset. PDS 456 has only sparse MIRI coverage and gaps. | outputs/cafe_line/VV114_z_0.0200/, outputs/cafe_line/PDS456_z_0.1840/<br>*Mitigation:* State the subset and masked windows; do not claim all-line simultaneity. |
| `s3fit_line` | line | UV/optical/NIR | **production** | medium | 58-minute production run; spec+sed mode; MC chi-square 1.605 +/- 0.112. Simultaneous SED/line models can absorb line flux into continuum components. | outputs/s3fit_line/04592649654_z_0.5874/<br>*Mitigation:* Compare to pure-spectrum fitters; report the mock-spectrum scatter. |
| `gandalf_line` | line | optical/NIR | **production** | medium | pPXF was accepted on the low-z galaxy, but rejected on the QSO; the QSO regression uses a fixed 300 km/s LOSVD. GANDALF is stellar+gas, not a broad-line AGN model. | outputs/gandalf_line/spSpec-51908-0277-120_z_0.0859/, docs/GANDALF_ASSESSMENT.md<br>*Mitigation:* Only quote pPXF-accepted kinematics; label fixed-LOSVD QSO lines. |
| `galspec_line` | line | optical/NIR | **production** | medium | Full-continuum emcee chain reached only ~8.2 retained tau (11.7 total), below the 50-tau convergence target. | outputs/galspec_line/04592649654_z_0.5874/<br>*Mitigation:* Report the tau/ESS diagnostic; do not claim full convergence. |
| `pyqsofitspec_line` | line | UV/optical | **production** | medium | H-beta is ~19% above GANDALF/S3Fit because of the continuum/model definition; 53/55 bootstrap draws valid. | outputs/pyqsofitspec_line/04592649654_z_0.5874/<br>*Mitigation:* Use the cross-tool median, not a single fitter, for line ratios. |
| `qgfit` | line | UV/optical | **production** | medium | Long continuum MCMC, but the line errors remain least-squares; line MCMC was not adopted. | outputs/qgfit/04592649654_z_0.5874/<br>*Mitigation:* Do not quote MCMC line errors; use LSQ covariance. |
| `sheap_line` | line | UV/optical | **conditional** | high | Restricted to the H-beta/[O III] window; repaired from the original 4.00 ratio but still a narrow-window decomposition. | outputs/sheap_line/04592649654_z_0.5874/, docs/SHEAP_ASSESSMENT.md<br>*Mitigation:* Quote only the validated H-beta/[O III] ratio and its bootstrap interval. |
| `manga_dap` | line | optical | **conditional** | high | Production validation is the official full-method SASUKE fit on 9 central single-spaxel bins, not all 2397 spaxels. The fast all-spaxel mode was rejected (H-alpha ratio 2.37, BPT agreement 41%). | outputs/manga_dap/NGC1194_z_0.0136/, inputs/NGC1194_z_0.0136/<br>*Mitigation:* Use the published MAPS for all-spaxel science; use this subset only as a same-spaxel DAP validation. |
| `manga_dap_full` | line | optical | **conditional** | high | Full all-spaxel official DAP is exposed as a long run (S/N=10, 2397 bins, full 65-template SASUKE). It is a single-core upstream workflow and may take many hours; the validated fast/9-bin result must not be substituted for it. | pipeline/runners/run_manga_dap_docker.sh, configs/manga_dap/default/plan.toml, docs/LONG_RUNS.md<br>*Mitigation:* Run with --full and wait for completion; compare the all-spaxel MAPS to the published reference before claiming the full DAP. |
| `xmm_sas_raw` | line | X-ray | **conditional** | medium | PN-only raw SAS 22.1 reduction. It used a custom 20 arcsec region, a CCF v22.0 RMF with SAS 22.1, and has no final pile-up/pattern optimization; it is not a joint PN+MOS or publication-grade replacement for xmm_xspec. | outputs/xmm_sas_raw/PDS456_z_0.1840/, Tools/xmm_sas_raw/README.md<br>*Mitigation:* Use as a reduction cross-check; run epatplot and a PPS-like region before quoting final numbers. |
| `xmm_xspec` | line | X-ray | **production** | medium | Uses official XMM PPS products, not a raw SAS epproc/especget reduction. Fe K-alpha is 4.05 sigma; PN/MOS Gamma differ by 2.9 sigma; the broad Fe width is degenerate with continuum curvature and is not a resolved velocity. | outputs/xmm_xspec/PDS456_z_0.1840/, Tools/xmm_xspec/SAS_RAW_PATH.md<br>*Mitigation:* Quote the narrow-core flux/EW; treat SAS raw reduction as future work; do not claim spin/relativistic profile. |
| `rxte_xspec` | line | X-ray | **production** | medium | Uses official HEASARC stdprod PCA products, not a raw pcabackest/saextrct reduction. PCA background systematics are severe; the Galactic-N_H diagnostic is not adopted. | outputs/rxte_xspec/3C120_z_0.0330/, outputs/rxte_xspec/MCG6-30-15_z_0.0077/<br>*Mitigation:* Quote the production and conservative fixed-N_H fits together; do not use the Galactic-N_H Delta chi2. |
| `crossmission` | ratio | X-ray/UV/optical | **postprocess** | medium | Two objects only; no correlation fit. 3C 120 uses PyQSOFit H-beta but is provisional because QSOFITMORE gives a different ratio; PDS 456 uses the local X-SHOOTER H-beta/[O III] fit, also provisional because of absorption/continuum residuals. The older PDS HST C IV result is retained only as UV context. | outputs/crossmission/3C120_z_0.0330/, outputs/crossmission/PDS456_z_0.1840/<br>*Mitigation:* Treat as same-object consistency checks; inspect the PDS quality flag and add more objects before fitting any slope. |
| `crossband` | ratio | NIR/MIR/FIR | **postprocess** | low | Analytic propagation of already-fitted line fluxes; inherits every parent fit's systematics. | outputs/crossband/Mrk231_z_0.0422/, outputs/crossband/NGC253_z_0.0008/<br>*Mitigation:* Propagate parent errors/systematics explicitly. |
| `cigale_sed` | sed | UV-FIR | **production** | low | SED/torus code; it does not measure individual emission lines. Model-family spread is real. | outputs/cigale_sed/04592649654_z_0.5874/<br>*Mitigation:* Never use CIGALE outputs as line fluxes. |
| `agnfitter_sed` | sed | UV-MIR | **production** | low | SED/torus nested sampling; it does not measure individual emission lines. | outputs/agnfitter_sed/04592649654_z_0.5874/<br>*Mitigation:* Use only for SED/torus parameters. |
| `ppxf_host` | host | optical/NIR | **production** | low | Stellar kinematics/host fraction; not an emission-line fit. | outputs/ppxf_host/04592649654_z_0.5874/<br>*Mitigation:* Use with GANDALF/S3Fit for host/AGN separation. |
| `sdss_zline` | reference | optical | **reference** | info | Official SDSS ZLINE narrow-line product; not a broad-line fit and not available for every source. | outputs/sdss_zline/04592649654_z_0.5874/, docs/OFFICIAL_PIPELINES_AND_XRAY.md<br>*Mitigation:* Use as a narrow-line anchor, not as a universal truth for broad lines. |

## Excluded or intentionally not run

| code/path | reason | evidence |
|---|---|---|
| `manga_all_spaxel` | Full 2397-spectrum DAP exceeded the practical time budget; fast SASUKE mode rejected (H-alpha ratio 2.37, BPT 41%). | outputs/manga_dap/NGC1194_z_0.0136/aux_fastmode/ |
| `lvm_dap` | Requires LVM IFU data products, not single-fiber AGN spectra. | docs/OFFICIAL_PIPELINES_AND_XRAY.md |
| `amaru` | Old public version; external EMILES/Fe II/Balmer templates; restrictive/contradictory licence. | docs/OFFICIAL_PIPELINES_AND_XRAY.md |
| `elfo_agndecompose` | IFS/2-D image decomposition, not 1-D single-fiber line fitting. | docs/OFFICIAL_PIPELINES_AND_XRAY.md |
| `pyspeckit` | Redundant with the existing Gaussian/line stack; no independent model. | docs/OFFICIAL_PIPELINES_AND_XRAY.md |
| `sas_raw_reduction` | The 16.5 GB SAS/CCF image and ODF reduction were not run; official PPS products were used instead. | Tools/xmm_xspec/SAS_RAW_PATH.md |
| `rxte_raw_reduction` | Raw pcabackest/saextrct were not rerun; official stdprod products were used. | outputs/rxte_xspec/3C120_z_0.0330/provenance.md |

## Decision-engine transparency

`pipeline/decide_tools.py` returns both a tool list and the reasons for
each selection.  Run:

```bash
.venv/bin/python pipeline/decide_tools.py --goal lines --z 0.59 --wave-min 3800 --wave-max 9200 --angstrom
.venv/bin/python pipeline/decide_tools.py --goal xray --z 0.033 --wave-min 3 --wave-max 20
```

The output is advisory: the source manifest's `tools` list is the final
routing decision.  SED codes (`cigale_sed`, `agnfitter_sed`) are never
returned as line fitters.
