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
| **NuSTAR (3-79 keV)** | **partly solved (2026-11-17): RMF + source-region ARF build; FPMB/background pending** | `Tools/nustar_xspec` builds (bioconda HEASoft 6.35.2), and the real response blocker was the CALDB **config format**, not the archive: `CALDBCONFIG` must be a mission/instrument table, not `CALDB = /path`. With that table and the `cut` detector RMFs, `numkrmf` builds a 66 MB RMF on a read-only mount; `nuskypos` + `numkarf` then build a source-region ARF (PSF/vignetting/aperture/ghost/detabs corrections disabled in this pass). The configured ObsID `60002046001` is subframe (`X/Y=-1`) and cannot be used; full-frame `60002046002` yields a 12,603-count FPMA spectrum, and `tbabs*cutoffpl` fits at C-stat/dof 0.985 (nH 1.9e23, Gamma 1.06, E_cut 88 keV; see `outputs/nustar_xspec/NGC1365_z_0.0035/`).  Remaining: FPMB joint fit, background, full ARF corrections, registration. |
| **Raw XMM SAS** | **solved for PN** | Full `epproc instexpids=PNS003` exit 0; final `*_ImagingEvts.ds`; `especget` 20″/40–60″; PN-only Δχ² 14.03 (3.74σ), flux 2.15e-14. See `docs/XMM_RAW_SAS_RESULT.md`. |
| **Raw RXTE PCA** | **blocked** | The `pca/FS4a_*` Standard-2 arrays are public in the `pca/` sibling of `stdprod/` (not inside `stdprod`), but HEASARC is not serving the archive from this network and the image lacks `pcabackest`/`saextrct`/`xtefilt`. A full HEASoft image and a working archive endpoint are required; `stdprod` remains production. |
| **Full all-spaxel MaNGA** | **completed (serial production); sample throughput by parallel cubes** | The official Stage-A DAP ran serially over all 5,476 spaxels: `outputs/manga_dap/NGC1194_z_0.0136/full` finished with `dap_status_code = 0` in 48,731 s (13.51 h), 93,102 line measurements, BPT agreement 0.9885 against the published MAPS. Sharding is *settled*: the pPXF stage shard is validated bit-for-bit (`full_shard4`, worst relative line-flux difference 0.00e+00, identical BPT census) but only worth 2.5 % because pPXF is ~7 % of the runtime; the EMOM and SASUKE shards are implemented and unit-tested yet silently abort / are never reached, so they stay gated off (`MANGADAP_SHARD_STAGES=ppxf`). For a sample of galaxies the supported lever is `pipeline/run_manga_parallel.py` (independent cubes concurrently, unmodified pipeline, ~5 GB per run). The auxiliary 2,397-bin 65-template `EmissionLineModel` that was killed at the 58-minute budget is recorded as `config.dap.full_attempt.status = did_not_complete` and is not the production result. |
| **PAHFIT systematics** | **partly fixed, not eliminated** | Fixed the line-table λ² convention: `pahfit_lines.csv` now stores `integrated_line_power` (MJy/sr THz), so Ne III/Ne II changed from 3.39 to **2.30**. Remaining: PDS/NGC 4151 error-scale mismatch, NGC 253 edge pixels, VV114 single-τ attenuation/PAH degeneracy; error floors, gap trimming, block bootstrap and a separate τ_9.7/τ_18 model are required. |
| **MCMC convergence** | **closed: GalSpec, PyQSOFit and QGfit converged** | GalSpec `outputs/galspec_line/04592649654_z_0.5874` is the 200-walker DEMove γ0=0.20, 30,000-step chain (5,000 burn): acceptance 0.267, τ_max 299.8, **83.4 retained τ**, 39/39 finite τ, ESS 16,679 (median 25,783) — **converged**. QGfit `work/qgfit_hostfix_10k` (host parameters fixed) is 56.1 τ with acceptance 0.374 — **converged**; its line MCMC stays disabled after the unstable pilot. PyQSOFit `outputs/pyqsofit/04592649654_z_0.5874/mcmc_long_65k` (65,000 steps / 15,000 burn / 50,000 retained) is **converged on all four blocks** (Hβ 62.7 τ, continuum 63.7 τ, Mg II 308.6 τ, 1-D [N II] 1,834.6 τ; ESS 6,273 / 6,373 / 30,861 / 183,458) — the per-block diagnostics are in its `run.json` under `runs`. The older 4,000- and 25,000-step GalSpec chains and the 13,000-step PyQSOFit chain remain documented as not converged. See `docs/MCMC_CONVERGENCE_AUDIT.md`. |
| **Registry/image pinning** | **solved** | `publish-images.yml` is now a per-image matrix (one clean 14 GB runner per image, `max-parallel: 8`), `linux/amd64`, attestations off (`docker build` + `docker push`, not `buildx --push`), and the digest is taken from the `docker push` output and cross-checked against `docker buildx imagetools inspect`; mismatch fails the job. Images publish flat as `ghcr.io/<owner>/agn-<tool>:<tag>` and `xmm_sas_raw` is excluded (local-only, 8.7 GB). Locally verified: GHCR login, a real push with digest cross-check, and YAML/shell validation. Published end-to-end under tag `v1-new-bands`: `radio_line`, `submm_line`, `casa_specfit`, `cube_lines`, `ml_joint`, `xmm_xspec`, `xmm_rgs`, `rxte_hexte` (8 images, `ghcr.io/onurcatmabacak/agn-<tool>`). Two ordering bugs were found and fixed in the workflow: sibling images are `FROM xmm_xspec:latest`, which in Actions resolves to Docker Hub ("pull access denied"), so the build job now pulls `ghcr.io/<owner>/agn-<base>` and retags it locally — trying the run's tag before `:latest`, since the base is published under the run tag. `nustar_xspec` is deliberately not published: it is not a registered tool because its reduction does not complete (see the NuSTAR row). |
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
| **BXA evidence for line models** | **partly closed 2026-11-17: the prior-free check does not support “no line”.**  On the same 2-10 keV spectra and frozen constants (n = 387 bins), BIC/AIC rank `pcfabs` first (chi2/dof 504.0/381, Delta BIC -145.6), then the 300 eV broad line (-44.4), then the 50 eV narrow line (-15.4), then `pl` (0), then `warmabs` (+17.9).  The narrow-line nested-sampling result (`d ln Z = -0.66` in the older run, -0.86 in the product README) is therefore a prior-volume statement, not a prior-free detection or rejection.  The pcfabs nested run never converged, but that is a sampler/prior problem: its chi2 is 157.5 lower for two extra parameters. | a pcfabs nested run with a tighter prior (or a profile-likelihood scan) to put an evidence number on the BIC-preferred model; the BIC/AIC scan is reproducible with `Tools/bxa_xspec/bic_scan.py` |
| **X-ray continuum residuals** | **partly solved: the sub-0.7 keV band was the dominant term.** Measured on the re-fetched PDS 456 PPS PN spectrum (obs 0721010201, 100 ks, Thin1 filter), `tbabs*zpowerlw`: chi2/dof **3.37** over 0.5-10 keV, **2.39** from 0.6 keV, **2.05** from 0.7 keV, 1.95 from 0.8 keV, 1.99 from 1.0 keV — i.e. essentially all of the excess above ~2 is 0.5-0.7 keV, which is PN calibration, not astrophysics. `configs/xmm_xspec/default` now uses **0.7-10 keV**. Background subtraction is worth 0.33 (2.835 -> 2.502 at 0.5-10) and the production adapter already attaches `BGSPEC`. Above 0.7 keV nothing tested fixes the remaining ~2.0: blackbody soft excess 1.91, `zbknpower` 1.95, partial covering (`zpcfabs`) 1.87-1.81, warm absorber (`zxipcf`) 2.09, C-statistic 1.97, and the three PPS pattern RMFs (SP0/SP4/SPD) give 2.05/2.01/2.10. | the residual at a fixed 0.7-10 keV band is unlikely to be missing physics alone (five model families tested); **tested 2026-11-17: the response is not the missing piece** - the CCF v21.0 and v22.0 PN matrices both give 2.05 at 0.7-10 keV, and v22.0 is already what production uses, so rebuilding the RMF cannot close it; the next test is pile-up/`epatplot` or a 20" extraction. For Fe K-alpha work the canonical 2-10 keV band (1.73 in the production config) stays the production answer. |
| **Table models** | MYTorus, UXCLUMPY/XARS and RELXILL need external FITS tables; UXCLUMPY/XARS also need a licence review | download the tables, vendor them under `Tools/*/third_party/`, register the model |
| **PAHFIT systematics** | PDS 456 / NGC 4151 error-scale mismatch, NGC 253 edge pixels, VV 114 tau/PAH degeneracy | error floors, gap trimming, a block bootstrap and a separate tau_9.7/tau_18 model |
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
  `X/Y = -1`, which `numkrmf` cannot use) yields a 12,603-count FPMA spectrum.
  `nuskypos` and `numkarf` then build a **source-region ARF** from the CALDB
  alignment/pixel-position/vignetting/teldef products and the SOC mast-aspect
  and attitude files.  With that ARF, `tbabs*cutoffpl` fits at C-stat/dof 0.985
  (nH 1.9e23, Gamma 1.06, E_cut 88 keV); `+pexrav` reaches 0.966 but its
  reflection parameters run to the bounds, so it is not a physical detection.
  **Remaining:** FPMB joint fit, a background spectrum, the full
  PSF/vignetting/aperture/ghost corrections, and registration.  The ARF is
  source-region weighted but not yet the final corrected response.
- **Raw RXTE PCA** - unchanged; still needs a HEASoft image with
  `pcabackest`/`saextrct`/`xtefilt`.
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

