# Remaining unresolved items and evidence

This is the honest state after the final audit.  Each item has an owner (the research
subagent that investigated it), the verified blocker, and what would count as a fix.

| item | status | evidence / next action |
|---|---|---|
| **Raw XMM SAS** | **solved for PN** | Full `epproc instexpids=PNS003` exit 0; final `*_ImagingEvts.ds`; `especget` 20″/40–60″; PN-only Δχ² 14.03 (3.74σ), flux 2.15e-14. See `docs/XMM_RAW_SAS_RESULT.md`. |
| **Raw RXTE PCA** | **blocked** | The `pca/FS4a_*` Standard-2 arrays are public in the `pca/` sibling of `stdprod/` (not inside `stdprod`), but HEASARC is not serving the archive from this network and the image lacks `pcabackest`/`saextrct`/`xtefilt`. A full HEASoft image and a working archive endpoint are required; `stdprod` remains production. |
| **Full all-spaxel MaNGA** | **completed (serial); sharding not implemented** | sdss-mangadap 4.5.0 is single-core, so the official Stage-A DAP ran serially over all 5,476 spaxels: `outputs/manga_dap/NGC1194_z_0.0136/full` finished with `dap_status_code = 0` in 48,731 s (13.51 h), producing 93,102 line measurements with BPT agreement 0.9885 against the published MAPS. The auxiliary all-spaxel 2,397-bin 65-template `EmissionLineModel` was killed at the 58-minute budget and is recorded as `config.dap.full_attempt.status = did_not_complete` inside that product — it is not the production result. The verified parent-Voronoi-bin sharding design (~3 h on 6 workers) is **not implemented**; no sharded result is claimed. |
| **PAHFIT systematics** | **partly fixed, not eliminated** | Fixed the line-table λ² convention: `pahfit_lines.csv` now stores `integrated_line_power` (MJy/sr THz), so Ne III/Ne II changed from 3.39 to **2.30**. Remaining: PDS/NGC 4151 error-scale mismatch, NGC 253 edge pixels, VV114 single-τ attenuation/PAH degeneracy; error floors, gap trimming, block bootstrap and a separate τ_9.7/τ_18 model are required. |
| **MCMC convergence** | **closed: GalSpec, PyQSOFit and QGfit converged** | GalSpec `outputs/galspec_line/04592649654_z_0.5874` is the 200-walker DEMove γ0=0.20, 30,000-step chain (5,000 burn): acceptance 0.267, τ_max 299.8, **83.4 retained τ**, 39/39 finite τ, ESS 16,679 (median 25,783) — **converged**. QGfit `work/qgfit_hostfix_10k` (host parameters fixed) is 56.1 τ with acceptance 0.374 — **converged**; its line MCMC stays disabled after the unstable pilot. PyQSOFit `outputs/pyqsofit/04592649654_z_0.5874/mcmc_long_65k` (65,000 steps / 15,000 burn / 50,000 retained) is **converged on all four blocks** (Hβ 62.7 τ, continuum 63.7 τ, Mg II 308.6 τ, 1-D [N II] 1,834.6 τ; ESS 6,273 / 6,373 / 30,861 / 183,458) — the per-block diagnostics are in its `run.json` under `runs`. The older 4,000- and 25,000-step GalSpec chains and the 13,000-step PyQSOFit chain remain documented as not converged. See `docs/MCMC_CONVERGENCE_AUDIT.md`. |
| **Registry/image pinning** | **workflow drafted, not published** | The current GHCR workflow builds all 26 images in one job (~63 GB) on a 14 GB runner; `RepoDigests[0]` can be an unqualified local digest and default provenance makes the digest non-deterministic. Use a per-image matrix, `linux/amd64` only, `provenance: false`, and registry-verified `@sha256` digests; SAS is local-only/experimental. |
| **CIGALE clean rebuild** | **external network blocker** | `Tools/cigale_sed/dockerfile` clones `gitlab.lam.fr`; the final check timed out, though the 10.4 GB image is present and was used for the committed results. A pinned source tarball/mirror is required for a clean build. |
| **PAHFIT historical MC subdirectories** | **needs regeneration** | `bootstrap_200`, `short_covariance`, etc. were generated before the corrected line-power convention; they are not used by the current `line_ratio_comparison.csv`. Regenerate them with the current `pahfit_mir` image before using their per-feature errors. |
| **BXA / torus / reflection / 3ML / QSFit** | **not implemented** | BXA is the highest-value next X-ray tool (GPL-3.0, Python + XSPEC + UltraNest). MYTorus/UXCLUMPY need table-model licence decisions; RELXILL is diagnostic only at 4σ; 3ML needs a joint-fit science case; QSFit is IDL-only. See `docs/LITERATURE_COVERAGE.md`. |

## What is explicitly not a bug

- `crossmission` N=2: it is labelled a case study and fits no slope.
- PDS 456 Hβ = 5.99: provisional, not a validated measurement.
- 3C 120 PyQSOFit 1.55 vs QSOFITMORE 3.00: a real model-systematic spread; crossmission is provisional.
- PAHFIT `flagged=true`: a scientific quality flag, not a runner failure.
- `xmm_sas_raw` PN-only: a reduction cross-check, not a replacement for joint PPS.
