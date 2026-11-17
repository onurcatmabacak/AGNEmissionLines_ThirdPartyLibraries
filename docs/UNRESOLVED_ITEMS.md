# Remaining unresolved items and evidence

This is the honest state after the final audit.  Each item has an owner (the research
subagent that investigated it), the verified blocker, and what would count as a fix.

> **Scope note (2026-11):** the repository no longer ships `inputs/` or `outputs/`
> — they were 2.4 GB of third-party observations — so every result now lives in
> [`docs/RESULTS.md`](RESULTS.md), the per-product `README.md` under `outputs/`,
> and the `source.json` manifests under `inputs/`.  A result is only reproducible
> if its manifest carries a retrievable pointer; `tests/test_manifests.py`
> enforces that.

## Solved since the previous audit

| item | outcome |
|---|---|
| **Radio / sub-mm band** | `radio_line` (ATCA H I 21-cm, v +123.07 km/s, tau 0.200, N(H I) 1.77e18 cm-2, S/N 11.7), `submm_line` + `casa_specfit` + `cube_lines` on ALMA HCN 3-2 (5.1 / 5.2 / 3.8 sigma, one line, three engines) |
| **Soft X-ray gratings** | `xmm_rgs`: OVII forbidden 22.10 A at 9.2 sigma and intercombination 21.80 A at 5.3 sigma — the pair that CCD resolution blends |
| **Hard X-ray above the PCA ceiling** | `rxte_hexte` (15-100 keV stdprod, official ARF/RMF): E_cut 43 keV, Delta C-stat +0.4, i.e. no cutoff required |
| **3ML joint fit** | `ml_joint` on PDS 456: alpha_ox = -1.37, single power law with 15% residuals (an earlier commit shipped +3.04 from a unit bug; corrected in 10ef1e9) |
| **Resolved spectroscopy** | `cube_lines`: per-spaxel moment maps and aperture fits, first product on the ALMA NGC 1275 cube |
| **Manifests** | all 22 sources now carry `urls` + a `retrieval` block (archive, identifier, service), enforced by a test |

| item | status | evidence / next action |
|---|---|---|
| **NuSTAR (3-79 keV)** | **partly solved (2026-11-17): RMFs + corrected ARFs + local background + free-cross-cal profile joint; PSF pending** | `Tools/nustar_xspec` builds (bioconda HEASoft 6.35.2), and the real response blocker was the CALDB **config format**, not the archive: `CALDBCONFIG` must be a mission/instrument table, not `CALDB = /path`. With that table and the `cut` detector RMFs, `numkrmf` builds 66 MB RMFs on a read-only mount; `nuskypos` + `numkarf` build source-region ARFs for both focal planes with vignetting/aperture/detabs corrections enabled (PSF/ghost still off). The configured ObsID `60002046001` is subframe (`X/Y=-1`) and cannot be used; full-frame `60002046002` yields 12,603 FPMA counts and 12,145 FPMB counts, with 5,910/6,447 background counts and a 100-200" annulus.  Background-subtracted `tbabs*cutoffpl`: FPMA C-stat/dof 1.024 (nH 1.2e23, Gamma 0.96, E_cut 79 keV), FPMB 1.038 (nH 2.1e23, Gamma 1.38, E_cut 500 keV); see `outputs/nustar_xspec/NGC1365_z_0.0035/`.  A profile joint fit with a free FPMB/FPMA factor gives c = 1.07 and C-stat/dof 3807.9/3794 = 1.004 (nH 1.40e23, Gamma 0.900, E_cut 35.5 keV).  Remaining: the PSF/ghost correction; vignetting/aperture/detabs and the free-cross-cal profile joint are done.  The PSF correction is blocked by `nuexpomap` invoking the interactive Tk `ximage`; Xvfb removes the `Tk startup failed` error, but `ximage` still hangs at its `[XIMAGE>` prompt; its command file has only crop/write/quit and no `read`, so it reports `Image for inmap not loaded`.  A batch-mode `ximage` or a precomputed exposure map is needed; an Xvfb wrapper that prepends `read/file` of the det1 instrument map lets `numkarf` finish, but it reports `PSF fraction=-nan` and writes an all-NaN ARF, so the PSF path still needs a correct exposure map/transform.  Registration is done (`pipeline/tool_registry.py`, `run_new_tools.py`, `build_images.sh`; audit = 34 tools). |
| **Raw XMM SAS** | **solved for PN** | Full `epproc instexpids=PNS003` exit 0; final `*_ImagingEvts.ds`; `especget` 20″/40–60″; PN-only Δχ² 14.03 (3.74σ), flux 2.15e-14. See `docs/XMM_RAW_SAS_RESULT.md`. |
| **Raw RXTE PCA** | **partly run 2026-11-17; raw fit mismatch** | The `pca/FS4a_*` Standard-2 arrays are public and HEASARC is serving them again: `https://heasarc.gsfc.nasa.gov/FTP/xte/data/archive/AO1/P10339/10339-02-01-01/pca/` returns HTTP 200 with `FS4a_*` and the `FH5a-e` housekeeping files. The `nustar_xspec` HEASoft 6.35.2 image now contains `pcabackest`, `saextrct` and `xtefilt` (the older `rxte_xspec` image did not). The XTE PCA CALDB index is available (`.../caldb/data/xte/pca/caldb.indx`, 2.0 MB) and the VLE background model is `data/xte/pca/cpf/bgnd/pca_bkgd_cmvle_eMv20111129.mdl.gz`; the response comes from the same CALDB. `xtefilt` is a Perl wrapper around `fcollect` that expects the old XTE FITS database layout (`FMI` plus a `stdprod/FIST...` index), so the archive files have to be staged in that layout or the filter file built another way. `pcabackest` now runs on the raw `FS4a_4205180-4205ff0` segment with the archive `x10339020101.xfl` filter and the VLE model, producing a 614 KB background file. The archive also carries the reference stdprod products (`xp10339020101_s2.pha`, `xp10339020101_b2.pha`, `xp10339020101.rsp`) for a direct comparison. `saextrct` then extracted a **537,007-count source PHA** over 3,328 s from the same segment, and the `pcabackest` output was summed to a 129-channel background PHA (493,140 counts; exposure 3,696 s; BACKSCAL 1.111).  A first XSPEC fit of the raw pair with `stdprod.rsp` is **not yet consistent** with the official product: raw chi2/dof 9000/49 (C-stat 225/46) versus stdprod 89.85/49.  The count rates agree (raw 161 cts/s, stdprod 173 cts/s; net 27.9 vs 30.0 cts/s, ratio 0.93) and the channel-by-channel net shapes agree at low energies, so the mismatch is in background scaling/grouping or response normalisation, not a gross extraction error.  Both raw and stdprod net spectra go negative above ~15 keV, so the background-model systematics dominate that band.  Using the stdprod `b2` background scaled to the raw exposure improves the raw chi2 from 9000 to 3519, but not to the stdprod 89.85; source and background rates are both 0.93x stdprod and their channel shapes agree, so the remaining mismatch is response/energy-scale or PHA grouping, not the background model alone.  A cross-correlation of the normalized 129-channel counts has its minimum at zero shift (normalized shape difference 2.4%), so there is no channel misalignment; the residual is a few-percent filter/GTI/PCU-selection shape difference, not an indexing bug.  An XFL-derived GTI with the exact 3,328 s exposure (`NUM_PCU_ON==5`, `TIME_SINCE_SAA>28`) gives the same 537,007 counts, so the 7% normalization difference is not the GTI selection.  Remaining: reproduce the exact stdprod filter/GTI/PCU selection and background model; the working commands are recorded in `Tools/rxte_pca_raw/README.md`. |
| **Full all-spaxel MaNGA** | **completed (serial production); sample throughput by parallel cubes** | The official Stage-A DAP ran serially over all 5,476 spaxels: `outputs/manga_dap/NGC1194_z_0.0136/full` finished with `dap_status_code = 0` in 48,731 s (13.51 h), 93,102 line measurements, BPT agreement 0.9885 against the published MAPS. Sharding is *settled*: the pPXF stage shard is validated bit-for-bit (`full_shard4`, worst relative line-flux difference 0.00e+00, identical BPT census) but only worth 2.5 % because pPXF is ~7 % of the runtime; the EMOM and SASUKE shards are implemented and unit-tested yet silently abort / are never reached, so they stay gated off (`MANGADAP_SHARD_STAGES=ppxf`). For a sample of galaxies the supported lever is `pipeline/run_manga_parallel.py` (independent cubes concurrently, unmodified pipeline, ~5 GB per run). The auxiliary 2,397-bin 65-template `EmissionLineModel` that was killed at the 58-minute budget is recorded as `config.dap.full_attempt.status = did_not_complete` and is not the production result. |
| **PAHFIT systematics** | **partly fixed, not eliminated** | Fixed the line-table λ² convention: `pahfit_lines.csv` now stores `integrated_line_power` (MJy/sr THz), so Ne III/Ne II changed from 3.39 to **2.30**. Remaining: PDS/NGC 4151 error-scale mismatch, NGC 253 edge pixels, VV114 single-τ attenuation/PAH degeneracy. Error floors, gap-edge trimming and a block bootstrap are now implemented in the tool (`--error-floor`, `--gap-trim-um`, `--mc-bootstrap-mode block`); a separate τ_9.7/τ_18 model and a rerun of the four products remain. |
| **MCMC convergence** | **closed: GalSpec, PyQSOFit and QGfit converged** | GalSpec `outputs/galspec_line/04592649654_z_0.5874` is the 200-walker DEMove γ0=0.20, 30,000-step chain (5,000 burn): acceptance 0.267, τ_max 299.8, **83.4 retained τ**, 39/39 finite τ, ESS 16,679 (median 25,783) — **converged**. QGfit `work/qgfit_hostfix_10k` (host parameters fixed) is 56.1 τ with acceptance 0.374 — **converged**; its line MCMC stays disabled after the unstable pilot. PyQSOFit `outputs/pyqsofit/04592649654_z_0.5874/mcmc_long_65k` (65,000 steps / 15,000 burn / 50,000 retained) is **converged on all four blocks** (Hβ 62.7 τ, continuum 63.7 τ, Mg II 308.6 τ, 1-D [N II] 1,834.6 τ; ESS 6,273 / 6,373 / 30,861 / 183,458) — the per-block diagnostics are in its `run.json` under `runs`. The older 4,000- and 25,000-step GalSpec chains and the 13,000-step PyQSOFit chain remain documented as not converged. See `docs/MCMC_CONVERGENCE_AUDIT.md`. |
| **Registry/image pinning** | **solved** | `publish-images.yml` is now a per-image matrix (one clean 14 GB runner per image, `max-parallel: 8`), `linux/amd64`, attestations off (`docker build` + `docker push`, not `buildx --push`), and the digest is taken from the `docker push` output and cross-checked against `docker buildx imagetools inspect`; mismatch fails the job. Images publish flat as `ghcr.io/<owner>/agn-<tool>:<tag>` and `xmm_sas_raw` is excluded (local-only, 8.7 GB). Locally verified: GHCR login, a real push with digest cross-check, and YAML/shell validation. Published end-to-end under tag `v1-new-bands`: `radio_line`, `submm_line`, `casa_specfit`, `cube_lines`, `ml_joint`, `xmm_xspec`, `xmm_rgs`, `rxte_hexte` (8 images, `ghcr.io/onurcatmabacak/agn-<tool>`). Two ordering bugs were found and fixed in the workflow: sibling images are `FROM xmm_xspec:latest`, which in Actions resolves to Docker Hub ("pull access denied"), so the build job now pulls `ghcr.io/<owner>/agn-<base>` and retags it locally — trying the run's tag before `:latest`, since the base is published under the run tag. `nustar_xspec` is registered but its image is not published (local/conditional; the response/ARF path is still manual). |
| **CIGALE clean rebuild** | **solved** | `Tools/cigale_sed/dockerfile` now pins `v2025.1` (`29cb909fe2636800b4acdb1dfc7129d8c8494a24`, the exact commit the committed products used) with a hard `rev-parse` check, and the build was re-run from scratch: image built, `pcigale 2025.1` imports, tag and commit verified inside the image. GitLab was reachable; the earlier timeout was transient. |
| **PAHFIT historical MC subdirectories** | **regenerated** | The whole production matrix was re-run with the current `pahfit_mir` image after the line-power fix: PDS 456 `short`/`short_covariance`/`long`/`both`, `VV114` and its `bootstrap_200`, `NGC 4151` and its `bootstrap_200`, `NGC 253` and `full_tail`. Every subdirectory now carries the `integrated_line_power` (MJy/sr THz) convention. |
| **BXA / torus / reflection / 3ML / QSFit** | **BXA implemented; table models and 3ML still open** | `bxa_xspec` (`Tools/bxa_xspec`, runner `pipeline/runners/run_bxa_xspec_docker.sh`, config `configs/bxa_xspec/default`) runs BXA 5.1.1 + UltraNest on the same PPS spectra and band as `xmm_xspec`, with C-stat and a six-model suite (absorbed power law, narrow/broad Fe K-alpha, warm absorber, partial covering, Compton-thick cut-off). Outputs `ln Z`, Bayes factors and 16/50/84 posteriors. Two solver findings are recorded: UltraNest's default `speed="safe"` never switches to slice sampling, which stalled the 5-parameter partial-covering model at ~2 % efficiency for ten hours (`speed="auto"` raises it to 25-42 %); and a broad Fe K-alpha with a boundary-pinned sigma (0.79 keV against a 0.8 keV prior cap, centroid 7.0 keV rest) is degenerate with continuum curvature, so its Bayes factor is not a line detection. A soft-excess continuum family was trialled and withdrawn (an 11-dex blackbody normalisation prior let the log-likelihood fall to -4e5). **The BXA evidence integral does not close for line models**: `pl` finishes in 13k evaluations at ~38 % efficiency, but any model with a Fe K-alpha term stalls at ~0.03 % efficiency around 75-95 % of the volume, because the C-stat peak is flat in the line normalisation. Two completed models give `ln Z(pl) = -342.12 ± 0.31` and `ln Z(pl_line_narrow) = -342.78 ± 0.35`, i.e. **d ln Z = -0.66 against the 50 eV line despite d chi2 = -27.3**: the Occam penalty cancels the fit improvement, so there is no Bayesian evidence for a narrow Fe K-alpha. Finishing the free-width/broad/pcfabs models needs a tighter line-normalisation prior or a different evidence estimator (profile likelihood / BIC) rather than more live points. **The X-ray band was moved to 2-10 keV**: with 0.5 keV included, chi2/dof stays at 2.70 no matter what is added (an unmodelled soft-excess/cross-calibration residual), so no Bayes factor is interpretable; 2-10 keV is the canonical Fe K-alpha band and gives chi2/dof 1.73. A 25-start chi-square scan there (with fixed parameters truly frozen) gives: narrow line (sigma 50 eV) -27, free-width line -162, pcfabs -158, warmabs ~0 -- so the free-width line and partial covering are degenerate competitors and both are sampled. **`cutoffpl_cabs` is unidentifiable with these data, not just slow**: a 25-start χ² scan gives best χ²/dof = 1391.2/515 = 2.701, against 1393.8/517 = 2.696 for a plain absorbed power law — Δχ² = 2.6 for two extra parameters. Nested sampling then integrates an essentially flat prior (live points start at log-likelihood −9e6 and never close their band), which is why the run burned 428k evaluations without converging. Dropping the model is the correct move; a Compton-thick comparison needs a broadband (NuSTAR) dataset. Every model also sits at χ²/dof ≈ 2.3-2.7, so an unmodelled component (soft excess / warm absorption / cross-calibration) must be fixed before any Bayes factor is quoted. MYTorus/UXCLUMPY/RELXILL remain open: they need external FITS tables and, for UXCLUMPY/XARS, licence review. 3ML is implemented (`ml_joint`); QSFit is IDL-only and stays excluded. |

## What is explicitly not a bug

- `crossmission` N=2: it is labelled a case study and fits no slope.
- PDS 456 Hβ = 5.99: provisional, not a validated measurement.
- 3C 120 PyQSOFit 1.55 vs QSOFITMORE 3.00: a real model-systematic spread; crossmission is provisional.
- PAHFIT `flagged=true`: a scientific quality flag, not a runner failure.
- `xmm_sas_raw` PN-only: a reduction cross-check, not a replacement for joint PPS.

## Still unsolved (2026-11)

| item | why it is still open | what would close it |
|---|---|---|
| **BXA evidence for line models** | **partly closed 2026-11-17: the prior-free check does not support “no line”.**  On the same 2-10 keV spectra and frozen constants (n = 387 bins), BIC/AIC rank `pcfabs` first (chi2/dof 504.0/381, Delta BIC -145.6), then the 300 eV broad line (-44.4), then the 50 eV narrow line (-15.4), then `pl` (0), then `warmabs` (+17.9).  The narrow-line nested-sampling result (`d ln Z = -0.66` in the older run, -0.86 in the product README) is therefore a prior-volume statement, not a prior-free detection or rejection.  The pcfabs nested run never converged, but that is a sampler/prior problem: its chi2 is 157.5 lower for two extra parameters. | a pcfabs nested run with a tighter prior (or a profile-likelihood scan) to put an evidence number on the BIC-preferred model; a 2026-11-17 attempt with pcfabs nH 15-40, CvrFract 0.35-0.65, shared continuum priors and 300 live points still had not found the BIC peak after 3.5k evaluations (Z ~ -456, likelihood max -329 against a BIC C-stat of 504), so it needs a better proposal/likelihood peak rather than just a narrower prior; the BIC/AIC scan is reproducible with `Tools/bxa_xspec/bic_scan.py` |
| **X-ray continuum residuals** | **partly solved: the sub-0.7 keV band was the dominant term.** Measured on the re-fetched PDS 456 PPS PN spectrum (obs 0721010201, 100 ks, Thin1 filter), `tbabs*zpowerlw`: chi2/dof **3.37** over 0.5-10 keV, **2.39** from 0.6 keV, **2.05** from 0.7 keV, 1.95 from 0.8 keV, 1.99 from 1.0 keV — i.e. essentially all of the excess above ~2 is 0.5-0.7 keV, which is PN calibration, not astrophysics. `configs/xmm_xspec/default` now uses **0.7-10 keV**. Background subtraction is worth 0.33 (2.835 -> 2.502 at 0.5-10) and the production adapter already attaches `BGSPEC`. Above 0.7 keV nothing tested fixes the remaining ~2.0: blackbody soft excess 1.91, `zbknpower` 1.95, partial covering (`zpcfabs`) 1.87-1.81, warm absorber (`zxipcf`) 2.09, C-statistic 1.97, and the three PPS pattern RMFs (SP0/SP4/SPD) give 2.05/2.01/2.10. | the residual at a fixed 0.7-10 keV band is unlikely to be missing physics alone (five model families tested); **tested 2026-11-17: the response is not the missing piece** - the CCF v21.0 and v22.0 PN matrices both give 2.05 at 0.7-10 keV, and v22.0 is already what production uses, so rebuilding the RMF cannot close it; the next test is pile-up/`epatplot` or a 20" extraction. For Fe K-alpha work the canonical 2-10 keV band (1.73 in the production config) stays the production answer. |
| **Table models** | MYTorus, UXCLUMPY/XARS and RELXILL need external FITS tables; UXCLUMPY/XARS also need a licence review | download the tables, vendor them under `Tools/*/third_party/`, register the model |
| **PAHFIT systematics** | PDS 456 / NGC 4151 error-scale mismatch, NGC 253 edge pixels, VV 114 tau/PAH degeneracy | **error floor, gap-edge trimming and block bootstrap implemented 2026-11-17** (`--error-floor F`, `--gap-trim-um U`, `--mc-bootstrap-mode block --mc-bootstrap-block L`; unit-tested; production products not rerun yet); a separate tau_9.7/tau_18 model remains |
| **Thin band coverage** | UV 1 object (C IV S/N 1.8, not a detection), NIR 1 object, FIR 2, radio cm 1 | more sources per band; the manifests already carry the archive pointers to fetch them |
| **MIRI cube for PDS 456** | the `mirifulong` product has zero-filled channels exactly where [Ne III]/[S III] sit, and [Ne V] is not detected at 2264 s | a deeper MRS observation or the MRS `s3d` cube of a brighter AGN |

## Verification sweep - 2026-11-17

Re-checked every row against the live tree at `f41c39f` (clean working tree) and
against the current archive endpoints.  The audit is otherwise confirmed; the
following items are new or need correcting.

### Confirmed, with a lifted blocker

- **NuSTAR (3-79 keV)** - the response blocker is resolved, but the product is
  not yet science-grade.  `https://heasarc.gsfc.nasa.gov/FTP/caldb/data/nustar/fpm/caldb.indx`
  returns HTTP 200 (2026-11-17), and the `nustar_xspec` image is present (5.96 GB).
  The undocumented failure was the **CALDB config format**, not the archive:
  `CALDBCONFIG` is a mission/instrument table
  (`NUSTAR FPMA CALDB data/nustar/fpm caldb.indx CALDB data/nustar/fpm`), not
  `CALDB = /path`.  With that table and the `cut` detector RMFs, `numkrmf`
  builds a 66 MB response from the CALDB on a read-only mount
  (`nuAcutdet0..3`, `nuAcutgrprmf`, `nuA20100101v001.arf`).  The full-frame
  observation `60002046002` (the configured `60002046001` is subframe with
  `X/Y = -1`, which `numkrmf` cannot use) yields 12,603 FPMA counts and 12,145
  FPMB counts.  `nuskypos` and `numkarf` then build **source-region ARFs for
  both focal planes** from the CALDB alignment/pixel-position/vignetting/teldef
  products and the SOC mast-aspect and attitude files.  A 100-200" annulus
  gives 5,910 FPMA and 6,447 FPMB background counts; `nuproducts` sets the
  BACKSCAL ratio (0.001868 / 0.015587).  Background-subtracted `tbabs*cutoffpl`
  fits: FPMA C-stat/dof 1.024 (nH 1.2e23, Gamma 0.96, E_cut 79 keV), FPMB 1.038
  (nH 2.1e23, Gamma 1.38, E_cut 500 keV).  FPMA `+pexrav` reaches 0.966 without
  background but its reflection parameters run to the bounds, so it is not a
  physical detection.  A profile joint fit with a free FPMB/FPMA factor
  gives c = 1.07 and C-stat/dof 3807.9/3794 = 1.004 (nH 1.40e23,
  Gamma 0.900, E_cut 35.5 keV).  **Remaining:** the PSF correction
  (vignetting, aperture and detabs are enabled; ghost is off); it is
  blocked by `nuexpomap` invoking the
  interactive Tk `ximage`.  Xvfb fixes the display but `ximage` still
  hangs at its `[XIMAGE>` prompt; the generated command file has only
  crop/write/quit and no `read`, so it reports `Image for inmap not
  loaded`.  A batch-mode `ximage` or a precomputed exposure map is
  needed.  Registration is done (registry + run_new_tools + build_images,
  audit 34 tools); the ARFs include vignetting/aperture/detabs but not
  PSF/ghost.
- **Raw RXTE PCA** - the blockers are lifted: the HEASARC `pca/` archive for
  `10339-02-01-01` returns HTTP 200 with the `FS4a_*` Standard-2 arrays, and the
  `nustar_xspec` HEASoft 6.35.2 image contains `pcabackest`, `saextrct` and
  `xtefilt`.  The VLE `pcabackest` run on the raw `FS4a` segment succeeds and `saextrct` produced a 537,007-count source PHA; the first raw fit does not yet reproduce the stdprod chi2 (background scaling/grouping/response handling is the next check).
- **Table models**, **PAHFIT systematics**, **thin coverage**, **MIRI cube** -
  unchanged; no new data or tables are present in the tree.

### Corrected / closed

- **The X-ray response is not the missing piece (closes the `#2` next step).**
  We downloaded the exact CCF PN matrices named in the PPS header and refitted
  the official PPS PN spectrum (`SRSPEC0001` + `SRCARF0001` + `BGSPEC0001`,
  `tbabs*zpowerlw`, XSPEC 13.0 in the `xmm_xspec` image):
  v22.0 gives chi2/dof 2.35 (0.5-10), 2.05 (0.7-10), 1.98 (2-10);
  v21.0 gives 2.05 at 0.7-10.  The production path already uses v22.0, so
  "rebuild `epn_e2_lw20_sdY9.rmf`" cannot close the residual.  The repo's raw
  20" cross-check reports 1.58 at 0.5-10 with the same v22.0 matrix, so the
  remaining difference is aperture/background/pile-up, not response.  Keep
  2-10 keV as the production band; the next test is `epatplot`/pile-up or a
  20" PPS extraction, not `rmfgen`.
- **MaNGA all-spaxel product is complete, but `docs/RESULTS.md` is stale.**  The
  committed `outputs/manga_dap/NGC1194_z_0.0136/full/README.md` records
  `dap_status_code = 0`, 48,731 s and 93,102 line measurements, while the
  results table still says `did_not_complete`.  The table was generated when
  the old `run.json` still existed; it can no longer be regenerated because no
  `outputs/**/run.json` is shipped (`find outputs -name run.json` = 0).
- **BXA evidence numbers disagree between the doc and the product README.**
  This row quotes `ln Z(pl) = -342.12 +/- 0.31` and
  `ln Z(pl_line_narrow) = -342.78 +/- 0.35` (Delta ln Z = -0.66).  The committed
  `outputs/bxa_xspec/PDS456_z_0.1840/README.md` quotes -342.06 +/- 0.27 and
  -342.92 +/- 0.46 (Delta ln Z = -0.86).  The two are consistent within errors
  and both disfavour the 50 eV line; quote one pair explicitly and say which run
  it is from.

- **BXA evidence (item #3) now has a prior-free answer.**  The nested-sampling
  evidence remains prior-limited, but BIC/AIC on the same 2-10 keV spectra rank
  `pcfabs` above both line models: Delta BIC -145.6 (pcfabs), -44.4 (300 eV
  broad line), -15.4 (50 eV narrow line).  The “no Bayesian evidence for a
  narrow line” statement is true only under the configured flat/log-uniform
  prior; it is not a prior-free rejection.  The pcfabs model is the new lead.

- **PAHFIT error floor, gap-edge trimming and block bootstrap are now available.**
  `--error-floor F` applies `sigma_new = sqrt(sigma^2 + (F*|flux|)^2)`;
  `--gap-trim-um U` drops samples within `U` microns of a coverage-gap edge;
  `--mc-bootstrap-mode block --mc-bootstrap-block L` resamples contiguous
  residual blocks.  All are covered by `tests/test_pahfit_spectrum_ops.py`;
  the four systematics-limited products still need a rerun with non-zero values.

- **The caveat-matrix builder was broken.**  `pipeline/build_caveat_matrix.py`
  raised `KeyError: mitigation` because `rxte_hexte`, `xmm_rgs`, `cube_lines`
  and `casa_specfit` had no `mitigation` field.  All four were added and
  `docs/CAVEAT_MATRIX.md`/`.json`/`.csv` regenerated (34 tools, 7 exclusions);
  `tests/test_caveat_coverage.py` now enforces registry/caveat coverage and
  the required fields.

### New gaps found

- **`outputs/xmm_xspec/PDS456_z_0.1840/` was missing and is now filled.**  It
  is cited by `docs/CAVEAT_MATRIX.md`, `docs/MCMC_AND_STATISTICS.md`,
  `configs/caveats.yaml` and the tool README as the evidence for the 4.05 sigma
  Fe K-alpha result.  The product README now records the archived production
  numbers, the 2026-11-17 response cross-check, and the fact that no data
  products are shipped.
- **The "one README per product" invariant is still not met.**  `outputs/` now
  has 31 tracked README files (`xmm_xspec` and `nustar_xspec` were added on
  2026-11-17), while `docs/RESULTS.md` lists 40 products.  Tools with result
  rows but no `outputs/<tool>/` README include `cafe_line`, `gandalf_line` and
  `pahfit_mir`; the PAHFIT MC subdirectories described as "regenerated" have
  no committed product tree.
- **`configs/xmm_xspec/default/README.md` was stale and is now fixed**: it
  said the default band was `[0.5, 10.0]`; `config.json` is `[0.7, 10.0]`.
- **`docs/RESULTS.md` is now a frozen artifact.**  `pipeline/build_results_summary.py`
  walks `outputs/**/run.json`, but the data-free tree contains none, so a
  regeneration would emit an empty table.  Either keep the table as a historical
  record with a note, or add a small committed results index.  Do not run the
  generator against the current tree without this.

### Verification method

- `git status --short` was clean at `f41c39f`; the fixes above are in
  `eb586f6`, `4b0a83c` and `6f12955`.
- `find outputs -name run.json` = 0; `git ls-files outputs` = 31.
- NuSTAR CALDB index HTTP 200; `caldb.config` HTTP 404 (the task writes its
  own table).
- NuSTAR response built with `numkrmf` on `60002046002A01_cl.evt` and the
  `nuAcutdet*`/`nuAcutgrprmf` CALDB files; fit in
  `~/nustar_work/fit_nustar.py`.
- XMM PN fits: `fit_pn.py` and `fit_pn_v21.py` in `~/xmm_response_work`, using
  `P0721010201PNS003SRSPEC0001`/`SRCARF0001`/`BGSPEC0001` and
  `epn_e2_lw20_sdY9_v21.0.rmf`/`_v22.0.rmf`.

## End-of-sweep status - 2026-11-17

This is the consolidated state after the 2026-11-17 verification and fix
sweep.  It supersedes the dated rows above where they disagree.

| item | state | evidence |
|---|---|---|
| X-ray continuum residual (#2) | **closed: response and pile-up both ruled out; it is the extraction** | CCF v21.0 and v22.0 PN matrices both give 2.05 at 0.7-10 keV (production already uses v22.0). Pile-up is ruled out by XSPEC's `pileup` model (`pileup*tbabs*zpowerlw`, alpha free, `Fit.nIterations=2000`): chi2/dof 2.04 and alpha stays at its starting value, i.e. the data need none. Model battery on the same PPS spectrum at 0.7-10 keV: absorbed power law 2.01, blackbody soft excess 1.93, `zpcfabs` partial covering **1.86** (Cf 0.15, NH 5e22, Gamma 2.13), `zxipcf` not fittable in this setup (parameters did not vary). Against that, the repo's raw 20" SAS extraction of the *same* observation gives **1.58** at 0.5-10 keV, so the residual is the PPS extraction (aperture/background), not the response or pile-up. Production keeps 2-10 keV for Fe K-alpha work. |
| NuSTAR | **partly solved** | RMFs, source-region `numkarf` ARFs with vignetting/aperture/detabs corrections, local backgrounds, independent FPMA/FPMB fits, a free-cross-cal profile joint fit (c = 1.07, C-stat/dof 1.004), and registration in `run_new_tools` are done.  The PSF/ghost correction remains, blocked by `nuexpomap`/`ximage`. |
| Raw RXTE PCA | **solved: exact reproduction of stdprod** | The mismatch was two bugs in the combination step, not the reduction: only one of the three `FS4a` segments was processed (3,328 s vs 9,808 s), and the summed PHA kept the first segment's `STAT_ERR`. With all three segments plus `saextrct` on the `XTE_SA` background models (per-PCU *rates*, not summable) and `STAT_ERR=sqrt(COUNTS)`, the raw product is channel-by-channel identical to the official one: 1,703,352 source counts, per-channel ratio 1.00000, background 1,408,899 vs 1,408,935, net 294,453 vs 294,417 (0.01%), and `tbabs*zpowerlw` at 3-20 keV gives **C-stat/dof 91.07/49 = 1.859, Gamma 1.866, nH 2.780** for *both*. Recipe: `Tools/rxte_pca_raw/README.md`. |
| BXA evidence | **prior-free answer obtained** | BIC/AIC on the same 2-10 keV spectra rank `pcfabs` first (Delta BIC -145.6), then the 300 eV broad line (-44.4) and the 50 eV narrow line (-15.4).  The narrow-line Bayes factor is prior-volume limited; a pcfabs nested run still needs a better proposal. |
| PAHFIT systematics | **partly implemented** | `--error-floor`, `--gap-trim-um` and `--mc-bootstrap-mode block` are implemented, unit-tested and in the image.  A separate tau_9.7/tau_18 model and a rerun of the four products remain. |
| Table models | **open** | MYTorus/UXCLUMPY/XARS/RELXILL tables and licence review still needed. |
| Thin band coverage | **open** | UV/NIR/FIR/radio-cm source counts unchanged; archive pointers are in the manifests. |
| MIRI cube for PDS 456 | **open** | The `mirifulong` zero-filled channels still need deeper/brighter MRS data. |
| Housekeeping | **solved** | `.git` 1.2 GB -> 102 MB after reflog expiry + `git gc`. |
| Repository integrity | **green** | 34 registered tools / 35 images / 22 sources; `pipeline/audit_repo.py` passes; 88 tests pass.  `pipeline/build_caveat_matrix.py` is fixed and guarded by `tests/test_caveat_coverage.py`. |

The remaining items are data- or specialist-analysis-gated, not blocked on
missing repository infrastructure.

