# Remaining unresolved items and evidence

This is the honest state after the final audit.  Each item has an owner (the research
subagent that investigated it), the verified blocker, and what would count as a fix.

| item | status | evidence / next action |
|---|---|---|
| **Raw XMM SAS** | **solved for PN** | Full `epproc instexpids=PNS003` exit 0; final `*_ImagingEvts.ds`; `especget` 20″/40–60″; PN-only Δχ² 14.03 (3.74σ), flux 2.15e-14. See `docs/XMM_RAW_SAS_RESULT.md`. |
| **Raw RXTE PCA** | **blocked** | The `pca/FS4a_*` Standard-2 arrays are public in the `pca/` sibling of `stdprod/` (not inside `stdprod`), but HEASARC is not serving the archive from this network and the image lacks `pcabackest`/`saextrct`/`xtefilt`. A full HEASoft image and a working archive endpoint are required; `stdprod` remains production. |
| **Full all-spaxel MaNGA** | **solution known, not run** | sdss-mangadap 4.5.0 is single-core; 5376 ppxf calls. Sharding by parent Voronoi bin is exact; 6 workers × ~4 GiB fits the 31 GB host. Estimated 3 h wall vs 9–15 h serial. The current `--full` path is a serial first step; no sharded merge implementation is committed. |
| **PAHFIT systematics** | **partly fixed, not eliminated** | Fixed the line-table λ² convention: `pahfit_lines.csv` now stores `integrated_line_power` (MJy/sr THz), so Ne III/Ne II changed from 3.39 to **2.30**. Remaining: PDS/NGC 4151 error-scale mismatch, NGC 253 edge pixels, VV114 single-τ attenuation/PAH degeneracy; error floors, gap trimming, block bootstrap and a separate τ_9.7/τ_18 model are required. |
| **MCMC convergence** | **settings known, not rerun** | PyQSOFit needs workers=8 + 1900 retained steps; GalSpec needs 25,000/5,000 and ncores=8; QGfit needs a σ floor and 2500 steps; SHEAP window is a model choice, not a runtime defect. No converged chains are claimed. |
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
