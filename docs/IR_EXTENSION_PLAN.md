# Plan: IR AGN Emission-Line Analysis (NIR, MIR, FIR)

**Status:** v9 design baseline, after the two-expert final verification (both verdict "sound", zero critical/major) plus the host–AGN/SED/torus addition.  Implementation pilots now exist; see the v10 implementation note immediately below.  The design sections below are unchanged.
**Implementation status (v11, October 2026):** the new tools now use a canonical source registry (`inputs/<source>_z_<z>/`) and source-keyed outputs (`outputs/<source>_z_<z>/<tool>/`); the old `input_*`, `results_ir` and `runs_ir_*` paths are retired.  The v10 SED/torus pilot now has two CIGALE torus families, per-source outputs and WISE-band diagnostics; real PACS/HIFI/Spitzer-IRS adapters, real MIR/FIR validation, PyQSOFit real-error/host-free UV fits, pPXF reliability flags, FIR window-bias fixes and a real cross-band NGC 253 test are documented in `docs/CAVEAT_FIXES.md`.
**v10 implementation status:** `pipeline_ir`/`ir_linefit` (generic NIR/MIR/FIR line slice), `pyqsofit_uv`, `ppxf_host`, `nir_linefit`, `pahfit_mir`, `fir_linefit`, `crossband`, and the first P5a SED/torus pilot `cigale_sed` are in the repository as Docker tools with committed test results.  `cigale_sed` fits the five z>0.5 eFEDS QSOs with SDSS+WISE photometry and BC03+DL2014+SKIRTOR; two fits are excellent, two acceptable, one is a flagged optical outlier.  It is a pilot: AGNfitter-RX and PROSPECTOR-AGN are not yet implemented, the photometric errors are nominal, and no X-ray/radio constraints enter.  The P5a gate is therefore **not** claimed as passed by this pilot.
**Scope:** extend the optical five-tool factory to IR lines: z, coverage routing, per-object search, scoring, comparison, figures. SED/torus is P5.
**Thesis:** v7's primitives survive; v8 applies the final verification corrections. It keeps the z pad dimensional with catalogue-outlier rejection, recovers BADASS posterior errors from the production `par_table`, routes ALMA per band/SPW over 316-8570 um, convolves with real ILS kernels, states achievable scatter, serializes P3/P4, and records the per-family DOF and calibration contracts.

## 0. Executive summary

An **IR emission-line factory**, not an SED fitter. Per object: z from A-grade line z, then catalogue spec-z, then photo-z, always cross-checked by a line-comb likelihood in a km/s pad; discrepant catalogue redshifts are flagged, not converted into absurd pads. Per spectrum: lines in measured **setting segments** with R(lambda), scan_type, windows, a versioned flux prior and per-line rights. `covered_data`, `measurable` and `publishable` stay separate. Plans are per (object, spectrum, aperture); suites derive from rest-frame families; routing never uses band labels. Scoring is per segment, in resolution elements, at a common R using the measured ILS. Every band has an anchor; every gate counts only Tier B real spectra.

## 1. Goals, scope, non-goals, success criteria

### 1.1 Goals
- **G0 — Availability (gate).** Per (line x setting x z) matrix separating `program_target`, `covered_data`, `measurable`, `publishable`, with `snr_basis` and reference flux, generated from FITS WCS, AOR/ASDM windows and per-setting tables.
- **G1 — NIR.** Ground Pa-beta z 0.16-0.39 (OH-limited 0.22-0.28; blocked 0.05-0.11, 0.40-0.52), Pa-alpha 0.08-0.27, Br-gamma <=0.10. NIRSpec PRISM (R 30-330); G140/G235/G395 gratings (R 500-2700). Rest-optical H-alpha to z~2.63, [O III] to z~9.5. IFU cubes are first-class (P0b).
- **G2 — MIR.** [Ne II], [Ne III], [Ne V], [S IV], [S III], [O IV], [Ar II]/[Ar III], [Ne VI], H2, PAH in MIRI LRS 5-14, MRS 4.90-28.30 (12 sub-bands, R 1300-3700), IRS SL/LL/SH/LH; counts generated per line and sub-band. [O IV] 25.89 needs MRS z<0.093 (4/20) or IRS LH z<0.429 (17/20 with the 38.0 um setting; 18/20 with 37.2 um).
- **G3 — FIR.** [O I] 63/145, [O III] 51.8/88, [N II] 122/205, [N III] 57, [C II] 158 from PACS 51-220 (blue 51-105, red 102-220), SPIRE FTS 194-671, SOFIA, ALMA B1-B10. Windows generated from per-SPW edges (316-8570 um, gaps 381-416, 498-600, 779-804, 2400-2580, 4470-5990). B6-B10 (316-1420) give [C II] z 1.0-8.0 with gaps 1.42-1.64, 2.16-2.80, 3.94-4.10, [O III] 88 z 2.6-15.1, [O I] 63 z 4.0-21.5; B5-B1 extend [C II] to z 53.3 and [O III] 88 to z 96.
- **G4 — Optics.** Optical v1 modules, CLI, search and output tree frozen behaviorally; IR engines in a new package; the no-flag CLI stays optical-only.
- **G5 — Host–AGN separation.** For every spectrum, deliver a decomposition: NIR stellar+hot-dust+AGN continuum (pPXF/STARLIGHT + power law + hot dust), MIR PAH/dust vs AGN torus (PAHFIT/CAFE), FIR PDR/star-formation vs AGN; record `host_fraction`, `decomposition_class` and a systematic term.
- **G6 — SED/torus companion.** Add CIGALE/X-CIGALE, AGNfitter-RX and PROSPECTOR-AGN as a companion suite for AGN fraction, L_torus, L_AGN, M_star, SFR and dust luminosity; compare line-derived and SED-derived quantities. SED is not a substitute for line fitting.

### 1.2 Non-goals
SED/torus is a **companion suite**, not a substitute for line fitting. It starts after the P2 host/calibration contracts are in place (P5a) and never gates the line suites P1–P4. A bounded fixed-feature MIR nuisance is in scope; the NIR hot-dust continuum is a photometrically anchored nuisance (3.2). No new observations P0-P2; no survey orchestration.

### 1.3 Science requirements

| quantity | requirement (validation) |
|---|---|
| Flux repeatability | systematic (photon-subtracted) <=3 % NIR/MIR, <=5 % FIR at S/N>=10; total <=5 % NIR/MIR at S/N>=30. Repeats/injections report photon and systematic separately; 3 % at S/N=10 is not a total-scatter requirement. |
| Flux scale | <=5-10 % NIR/MIR, <=10-15 % FIR vs a primary standard in the same mode; anchor uncertainty in budget (CALSPEC/asteroid/PACS calibrator) |
| NIR FWHM | <=10 % only if FWHM >= 3c/R, 5c/R for a limit (LSF synthetics) |
| Limits | 95 % limit contains truth 95+/-3 % (low-S/N ensemble) |
| Redshift | \|dz\|/(1+z)<=0.001, >=2 lines/species/different blend_groups at R>=min_R_deblend; right in >=95 % of A/B (blind recovery, 300-700 km/s injections); discrepant Z_NOQSO flagged (4.2) |
| T1a / T1b | T1a independent code: bias <=5 %, scatter <=10 %, else `T1a=anchor`; T1b median + scatter + outlier fraction inside envelope (envelope or Tier C) |
| Cross-band | [O III] 88/5007 and Pa-alpha/H-alpha within 10-20 % under one aperture class (overlaps, pytest) |

### 1.4 Deliverables per band
- **Broad/narrow.** Every H/He line has `component_scope` in {total, broad, narrow} and `min_R_broad`; broad measurable at R>=100, narrow deblending at R>=1000-2000.
- **Diagnostics (P4)**, each with validity domain, component_scope and reference: [Ne V]/[Ne II], [O IV]/[Ne III], [Ne III]/[Ne II], [S III] 18.7/33.5, [O III] 88/[N II] 122, [O I] 63/145, PAH 6.2/11.3, Pa-alpha/H-alpha, **[O III] 88/5007**.
- **Host/AGN.** Every line suite reports `host_fraction` and a `decomposition_class`; NIR host from pPXF/STARLIGHT + hot dust, MIR from PAHFIT/CAFE, FIR from PDR/host. SED/torus (CIGALE/X-CIGALE, AGNfitter-RX, PROSPECTOR-AGN) supplies the companion prior and cross-check.
- **Multiplicity.** NIR 2-3 (rest-optical chain, pPXF+PL+BB, pyspeckit), MIR 2 (PAHFIT-like, local Gaussian), FIR 1 + anchor. Where no independent code exists, state `T1a=anchor`.
- **Flux priors.** `flux_prior.csv` per line (Pa-alpha/H-alpha, Br-gamma/H-alpha, [Ne II]/L_bol, [Ne III]/L_bol, PAH/L_IR, [C II]/L_IR), `snr_basis` in {literature, archive_pipeline_flux, unknown}; unknown ranks last, never silently dropped.

## 2. Instruments, lines and availability

### 2.1 Mapping
`lambda_obs = lambda_rest(1+z)` with both in one canonical frame (vacuum, 4.1). The router tests observed wavelength against setting segments, spectral windows and the measured grid; rest frame is for identification and suites.

### 2.2 Mode-resolved settings (router source of truth)
One row per (facility, instrument, mode, grating/filter/order/sub-band/SPW); `segments[]`; R per row; `site` in {space, airborne, ground}; `scan_type` in {line, range, ifu, fts}. **No gap inside a row's own interval** (self-test); rows generated from versioned tables. ILS per row: `gaussian`, `asymmetric`, `instrument_kernel`, `sinc`, `pacs`.

| setting | segments (um) | R | site |
|---|---|---|---|
| SDSS/eFEDS optical | 0.36-1.04 | 2000 | G |
| XShooter VIS; NIR arms | 0.30-1.02; 0.99-2.48 | 5000-9000 | G |
| SpeX prism; SXD; LXD; MOSFIRE JHK | 0.8-2.5; 0.8-2.4; 2.3-5.5; 0.97-2.45 | 100-3500 | G |
| NIRSpec PRISM | 0.60-5.30 | 30-330 (table) | S |
| NIRSpec G140M/H; G235M/H; G395M/H (F070/F100/F170/F290) | 0.70-1.89; 1.66-3.17; 2.87-5.27 | 500-2700 | S |
| MIRI LRS; MRS ch1-ch4 | 5.0-14.0; 4.90-28.30 (12 sub-bands) | 50-3700 | S |
| IRS SL/LL/SH/LH | 5.2-38.0 (4 modules) | 60-600 | S |
| PACS blue; red (5x5 IFU, 47x47 arcsec) | 51-105; 102-220 | 1000-4000 | S |
| SPIRE FTS SSW; SLW (beam 17-40) | 194-313; 303-671 | 370-1300 | S |
| SOFIA GREAT; FIFI-LS blue/red | receiver bands; 42-110/100-210 | 1e3-1e7 | A |
| ALMA B1 | 5990-8570 | up to 1e7 | G |
| ALMA B2 | 3330-4470 | up to 1e7 | G |
| ALMA B3 | 2580-3570 | up to 1e7 | G |
| ALMA B4 | 1840-2400 | up to 1e7 | G |
| ALMA B5 | 1420-1840 | up to 1e7 | G |
| ALMA B6 | 1090-1420 | up to 1e7 | G |
| ALMA B7 | 804-1090 | up to 1e7 | G |
| ALMA B8 | 600-779 | up to 1e7 | G |
| ALMA B9 | 416-498 | up to 1e7 | G |
| ALMA B10 | 316-381 | up to 1e7 | G |

Notes. MRS sub-bands overlap (4.90-28.30 gapless); `sub_band_id` mandatory, default highest R, extras share `covariance_id`, never independent in T0/T1a. Ground dead zones 1.33-1.49, 1.78-1.96, 2.38-2.90 um. Atmosphere gate for G and A: `usable_z` = geometry AND (space OR T>threshold over +/-1 FWHM AND PWV/airmass limits); rows carry `atm_model`, `PWV`, `airmass`, `tau_zenith`, `primary_beam`. ALMA rows are per band; ASDM SPW edges set intervals (gaps above), GREAT/FIFI-LS per tune; `coverage_source=header|aor|asdm`.

### 2.3 Line registry
Fields: id, species, transition, `line_type`, `lambda_vac` + optional `lambda_air` (null for MIR/FIR), `rest_band`, class, `component_scope`, `feature_components`, `blend_group`/`feature_group`, ratios, FWHM prior, `min_R_*`, priority, aliases, reference; generated from NIST ASD plus a versioned list; `feature_registry` covers PAH/H2/silicate. Registry v1 adds G1-G3 lines, PAH 3.3/30, H2, coronal [Si VII]/[Mg VIII]/[Si IX], stellar CO/Ca II/Na D; [C I] 0.985 is rest-optical.

**Completeness:** NIST ASD + pinned IRS AGN/feature atlases, exclusion table with a reason per line; CI asserts every line above a stated strength and every confuser.

**Confusers:** CO 1-0..13-12, OH 1.87/2.05, H2O, [C I] 370/609, HCN, silicate, PAH 3.3; [O III] 88.36 vs CO(30-29) 86.85 is **1.7 %** in (1+z), not 5 % (CO(9-8) is at 289.1 um and is not the confuser).

**Grouping.** `fit_window_group` = bookkeeping only. `blend_group` (line-line) = routing-time cross-talk >1 %; joint fit, per-component flux, `group_total` separate. `feature_group` (line-on-feature) = joint feature model, line marginalised, `delta_flux_from_feature`. Not blends: Pa-beta/[Fe II], H-alpha/[S II], [C II]/[O I] 63, [O III] 88/[N II] 122, Br-gamma/CO. Line-line: He II 1.6418+[Fe II] 1.6435 (no He II at R<3000), Pa-alpha+He I 1.869, Br-gamma+He I 2.162, [Si VI] 1.963+H2 1.957, H-alpha/[N II] (per-line only at R>=1500), [O IV]+[Fe II] 25.99. Line-on-feature: [Ne II]+PAH 12.7, [Ne VI]+PAH 7.7, [Ar III]+PAH 8.6, H2 17.03+PAH 17, **[S III] 18.71+silicate, [S IV] 10.51+silicate**; `[S IV]` has one classification.

### 2.4 Availability (deliverable)
The 20 optical spectra have no IR spectra; geometry is not data.
- `geometry.csv` (line x setting x z) generated per band with provenance URL and a golden file. `programs.csv` (program, object, instrument, setting, scan_type, windows, target lines) is intent only. `manifest_lines.csv` (long) carries object, spectrum, program, segment, line, the three predicates, rights, `snr_basis`, reference flux, coverage, aperture/beam; coverage from WCS and AOR/ASDM windows; **`scan_type=line` limits coverage to the scanned interval**.
- Tiers: A same 20; B public IR with optical cross-match; C synthetic/truth; P0 names a Tier B sample per band with program IDs and >=10 spectra at S/N>5; every row carries `tier`.
- Zero-new-data: [S III] 9071/9533 reaches z<0.091 in SDSS (3/20) and needs five tool line lists, four fit regions and scorer changes: a **smoke test, n=3**; the NIR anchor is a published Pa-beta flux re-measured from a named public spectrum.
- `anchors.csv` per band: object, spectrum, line, published flux/error, reference, instrument, aperture/beam, independence, `anchor_uncertainty`; >=3 per band spanning flux and z, >=1 primary standard.

### 2.5 Router decisions
Steps: z; segments/windows/scan_type/coverage/R(lambda)/LSF/atmosphere/S/N/mask/calibration/beam/rights; lines with `snr_est`, `flux_prior_source`, predicates; `suites[]` from rest-frame family in coverage/mode/R/aperture; tools/cost/caps.
- **Three predicates, never merged.** Select `covered_data AND measurable`; `publishable` only sets `can_publish` and a `data_rights` flag; proprietary spectra measure internally, never publish.
- `snr_est = expected_flux/local_noise` from `flux_prior.csv`; FIR continua are invisible, so a continuum-only S/N never fires.
- **Ladder:** per-line `min_R_flux`/`min_R_deblend`/`min_R_broad`; flux if R>=both; `group_total` if R>=min_R_flux; broad if R>=min_R_broad; limit below; at R(lambda), not a band label.
- **Decision tables** `nir_decision.csv`/`mir_decision.csv`: line -> preferred/fallback setting -> min R/S/N -> group/feature -> refusal; rank by `snr_est`, R, aperture match; record `selection_reason`.
- **Refusals:** `no_coverage`, `outside_spectral_window`, `resolution_insufficient`, `calibration_missing`, `no_tool`, `z_prior_too_wide`, `telluric_blocked`, `data_unreadable`, `no_ir_spectrum`. **Flags:** `data_rights`, `no_common_window`, `beam_mismatch`, `single_tool`, `epoch_mismatch`, `z_ambiguous`, `z_cat_outlier`, `not_agn`, `host_dominated`.
- Selection: all eligible under cap; prefer >=2 same-class; single tool -> `single_tool`; `--cross-tool off` is a report switch; optical first only if measurable at the required R.

## 3. Tools

### 3.1 Registry, capabilities, ToolPlugin
Entry: role, per-line evidence, licence, install, rights, version/digest, resources, parallelism, timeout, failures; capabilities (model, error, limit, posterior, line-flux-only, cube, wave_frame, model_includes_lsf/R_model, broad). `role=anchor` feeds validation, not the pool; `sculptor` is `role=gui, not_in_pool` or retired.
`ToolPlugin`: `write_input`, `run`, `parse_output`, `model_on_grid(segment_id, wave)`, `candidate_grid()`, **`neighbours(knobs)`**, **`render(knobs) -> (variant_id, config_path, sha256)`**, `line_id_map`, `param_map`, capabilities, **`n_free_params`**, `cost`. `model_on_grid` raises outside the segment, declares `model_includes_lsf`, and convolves once to R_common with the segment ILS kernel (`common_R_mode=kernel`); the Gaussian `sqrt(FWHM_common^2-FWHM_model^2)` shortcut is allowed only when `ils_kind=gaussian`; never up-interpolates. Drivers become generic engines **in `pipeline_ir/`** with `RunStore` (`legacy`/`ir`), `config_path(suite, tool, variant)` and versioned `best_configs`; optical modules/CLI stay byte-for-byte; a dummy-tool test covers stage 1 plus refinement.

### 3.2 NIR
`rest_optical_in_nir` splits. **(A)** H-alpha/[N II]/[S II] (+H-beta/[O III] where rest coverage <0.55 um): R>=2000 for deblending, `min_rest_coverage=0.55`; G235H/G395H, **not** PRISM (3.33:1 rest coverage exists only there, so "run optical tools unchanged" is withdrawn); hot dust included. **(B)** [S III] 9071/9533: registry+scorer lines, BADASS `fit_reg` to 9464, FANTASY crop/input to 9464/9500, flux-only for 9533.
New NIR: pPXF host (XSL/SpeX/MARCS) + power law + hot dust + Gaussians. `T_dust`/tau **anchored** by matched-aperture NIR photometry (UKIDSS/VISTA/HST) or a fixed grid (800/1200/1600 K); WISE W1/W2 are a prior, not matched aperture. Record `anchor_aperture`/`anchor_beam`; `delta_flux_from_continuum_model` and anchor uncertainty enter `chi2_sys`. Injection is continuum-mismatch; second fitter pyspeckit/lmfit; else `T1a=anchor`.

### 3.3 MIR
Primary: PAHFIT (or pinned fork) with fixed PAH wavelengths, **separate `tau_9.7`/`tau_18`**, emission/absorption mix, PAH widths free at R>1000, correlated-residual term in `chi2_sys`, named in-repo fallback. Parameter budget fixed per suite plus AIC/BIC. MRS PSF/EE wavelength-dependent: `ee_fraction` per sub-band, aperture correction, point-source calibrator test.
Order: MRS ch3/ch4 or IRS SH/LH for [Ne III]/[Ne V]/[O IV]; **[S III] 18.71 and [S IV] 10.51 are `feature_group` with silicate**. LRS only for [Ne II]/[S IV]/[Ar II]/[Ar III] as feature/blend group + `line_flux_only`. Secondary local continuum + multi-Gaussian; Level-2/2.5; FWHM only if >=3c/R; fringing in `chi2_sys`.

### 3.4 FIR
PACS double-differential scans: `LineScan` likelihood, line flux + **background from off-line channels in the same scan**; `dof = n_on+n_off-n_params` (2 fitted background, 1 fixed); `n_off>=3` per nod, `n_on>=2-3 resels`; no off-line channels -> a limit with `limit_method=on_line_noise+continuum_prior` and `limit_confidence`. SPIRE FTS: `FTS` class, sinc ILS, apodization/oversampling/fringe/baseline models, wavelength-dependent beam. `ils_kind`/`ils_ref` mandatory, validated on a calibration line. `line_shape_policy`: PACS/SPIRE flux-only+ILS; GREAT/ALMA flux+FWHM; MRS only if FWHM>=3c/R; LRS flux-only. PACS point-source calibrated; extended sources need surface brightness + aperture correction from `extent_source`. **Anchor:** published PACS flux for a bright AGN/calibrator within budget. SOFIA/ALMA per tune/SPW + atmospheric gate.

### 3.5 Dependencies, parallelism, licensing
Add specutils, astropy, Cloudy/MAPPINGS. Verified: BADASS emcee no pool; GELATO NProcess 1. Object/spectrum parallelism is the lever; wrappers **retain posteriors**; no proprietary data in git/images; CI `--public-only`. Spikes are pass/fail; registry evidence is a P0 gate; a failed tool downgrades to one tool + anchor or Tier C.

### 3.6 Host–AGN separation and SED/torus (companion)
Two complementary routes, both required:
- **Spectral decomposition (line suites).** NIR: pPXF/STARLIGHT with XSL/SpeX/MARCS libraries + power law + hot dust + Gaussians; MIR: PAHFIT PAH/dust + AGN torus, CAFE AGN templates; FIR: PDR/star-formation templates and host contribution. Output `host_fraction`, `host_subtracted_flux`, `decomposition_class` and a systematic term.
- **SED/torus fitting (companion suite).** **CIGALE/X-CIGALE** (stars, dust, AGN torus, X-ray; modular, parallel over models/objects), **AGNfitter-RX** (radio-to-X-ray Bayesian AGN+host; emcee; verify pool/MPI), **PROSPECTOR-AGN** (stellar+AGN SED). Inputs: matched-aperture photometry + spectra. Outputs: `agn_fraction`, `L_torus`, `L_AGN`, `M_star`, `SFR`, `dust_luminosity`, model-family spread.
- **Strategy:** (a) joint fit with a host component; (b) pre-subtract host (pPXF/STARLIGHT); (c) SED prior on `host_fraction`/`agn_fraction`; (d) compare line-derived and SED-derived L_AGN/AGN fraction. Record the chosen `decomposition_class` and model family; never compare a line FWHM to a stellar mass.
- **Degeneracies:** AGN vs starburst vs old stars vs torus; report model-family spread and `prior_dominated`; never report a single SED number without the family.

## 4. Data model, units and redshift

### 4.1 Data model, units, layout
`Object`: id, RA/Dec, catalogue z + quality, Z_NOQSO, z_err, z_systematic, `ebv_mw` (SFD), `ebv_agn`, `reddening_policy`, `reddening_law`, `R_V`, photometry, WISE/X-ray.
`Spectrum`: id, object, instrument/mode/grating/filter, `scan_type`, `spectral_windows[]`, epoch, `segments[]` (segment_id, `sub_band_id`, intervals, R(lambda), LSF, T/T_err, `atm_model`, `PWV`, `airmass`, `tau_zenith`, aperture), flux/error, mask+policy, FITS unit/frame keys (`BUNIT`/`BTYPE`/`BSCALE`/`BZERO`/`CUNIT`/`CTYPE`/`SPECSYS`), `flux_type`, frame, `wave_cal_err`, beam/aperture/`pixel_sr`/`beam_sr`/EE/`aperture_correction`, sky subtraction/nods/residual scale, `telluric_reference/model`, `OH_residual`, flags, `calibration_type`, CRDS, rights. Cube adds spaxel scale, beam map, `extract_aperture`, wavelength-dependent PSF/EE; `LineScan` adds scan_range/nods/transmission/background/ILS; `FTS` adds apodization/oversampling/fringe/baseline.
`LineMeasurement`: `measurement_id` (PK), spectrum/segment/line/component, `quantity_type` (line/feature/band; flux/ratio/EW/group_total), `measurement_class`, `decomposition_class`, flux/errors, FWHM, v_offset, EW, `detection_status`, `flux_limit`/`limit_method`/`limit_confidence`, `covariance_id`, `posterior_sha256`, `duplicate_of`, z, model status/class/tier, flags, `flux_unit`.
`Photometry`: band/filter, `lambda_eff`, flux, error, upper limit, beam/aperture, provenance. `SedMeasurement`: model family (CIGALE/AGNfitter-RX/PROSPECTOR), `agn_fraction`, `L_torus`, `L_AGN`, `M_star`, `SFR`, `dust_luminosity`, model-family spread, priors, `host_fraction`, `decomposition_class`, provenance.
Layout: legacy `runs/<tag>` untouched; `runs_ir/<object_id>/<spectrum_id>/<aperture_id>/<suite>/`; `best_configs` keyed (object, spectrum, suite, tool). `ratio_id`/`ratio_type`/`validity_domain` in the schema. `band_pairs[]` = (line_a, spectrum_a, line_b, spectrum_b, `cross_band_class`). OR_MASK gets a bit table and per-line policy.

### 4.2 Redshift (P0 gate)
- Priority: **A-grade IR line z -> catalogue spec-z (quality) -> photo-z -> none**; a catalogue spec-z never overrides a confirmed A line z.
- **Always** evaluate the line-comb likelihood at z_a +/- pad; record `z_line`, `z_lines[]`, `z_spectra[]`, `z_line_err`, `dz_line_kms`, `z_confirmation` {confirmed, tension, no_evidence}. Promote to the full scan on tension, grade B/C, photo-z, (predicted S/N>5 AND measured S/N<2), or <2 predicted primary lines.
- **Blind scan:** continuum-normalise, mask, convolve the registry comb with the LSF, scan z on a grid set by R and window; score = weighted line-window S/N; delta-chi2 vs continuum-only; false-alarm rate from phase-randomised spectra **with confusers**; enumerate hypotheses (single line x species, doublets, ratio pairs, confuser alternatives) with prior penalties; keep <=3, fit per hypothesis only when the line set differs.
- **z_quality:** A = >=2 lines, >=2 species, **different blend_groups**, R>=min_R_deblend for both, rest-frame lever arm >=2 (ratio of the two lines' rest wavelengths; not required for a known doublet with a tied ratio), and a narrow line or catalogue systemic; B = 1 line + prior or 2 same-species; C = single line or R<1000, pad set by the nearest confuser separation.
- **Pad, all km/s:** `z_pad_kms = max(3c*sigma_z/(1+z), c*wave_cal_err/lambda_line, 300, c*|Z-Z_NOQSO|/(1+z))`; the last term is admitted only when `|Z-Z_NOQSO|/(1+z)<=0.01`. Above that set `z_cat_outlier`, ignore Z_NOQSO for pad/windows, require the blind scan, and let only an A-grade line z set windows. `z_pad_z = z_pad_kms/c*(1+z)`. Test 04545183216 (Z=0.4675, Z_NOQSO=0.8513), the -704 km/s object and sigma_z=0.001.
- `z_used_for_windows` = narrow-line systemic z where available; half-width >= max(1.5 FWHM, z_pad).

## 5. Router, scoring and comparison

### 5.1 Router and plans
`execution_plan.json` per (object, spectrum): `spectrum_id`, z fields, `z_hypotheses[]`, `segments[]`, `lines[]` with spectrum/segment/line/aperture ids, `suites[]`/`suite`, the three predicates/rights, `snr_est`/`flux_prior_source`/`quantity_type`/`component_scope`/`sub_band_id`/`duplicate_of`/groups, tools, refusals, flags, `plan_hash`; `suites[]` per (spectrum, aperture). `object_plan.json` rolls up spectra, band_pairs, aperture/epoch match, booleans, `no_ir_spectrum`, drop reasons.

### 5.2 Registry and wrapper contract
`prepare` writes a canonical `spectrum.fits`: units, ivar, **`err_floor`**, mask, frame, LSF, atmosphere, segments, coverage, flux type. Wrappers write `model.csv` (`wave_obs`, `segment_id`, `model_total`, `continuum`), `model_components.csv`, `line_measurements.csv`, and `run.json` with `n_free_params`/`n_pix_used`, `run_status`, `model_status`, capabilities, `plan_hash`, attempted line ids. `score_fits` reads only canonical + wrapper outputs; `--scorer=legacy` keeps v1 as optical default; `model_status` in {ok, partial, failed, unsupported, not_attempted}, `lines_returned` from `line_measurements.csv`, mismatch -> partial. **Golden test:** re-score stored v1 outputs to `chi2_common` <1e-6. **Optical freeze:** run the optical search on 1-2 objects and compare `scores.csv`, `best_configs.json`, `runs/<tag>` list and `make_report` to stored hashes.

### 5.3 Scoring and search
- **Per segment.** `model_on_grid(segment_id, wave)`; `chi2(segments) -> (chi2, n_pix_used, dof)`; no interpolation across a boundary (it fabricates gaps and rewards gap-bridging models). `n_resel = sum(window_width/(lambda/R(lambda)))`, `n_pix = sum(window_width/pixel_width)`, `n_params` from `run.json`; `dof_resel = n_resel - n_params`, `dof_pix = n_pix - n_params`; report both; rank on `chi2_red_resel` only when `dof_resel>=3` and `scan_type` is not `{line,fts}`; for PACS/SOFIA line scans and SPIRE FTS rank on total chi2 + AIC/BIC (dof_resel is undefined there).
- **Common resolution.** `R_common = min(R_data, min tool R_model)` per line/suite. Models are convolved once (only if `model_includes_lsf=false`) with the segment ILS kernel resampled to the common grid (`common_R_mode=kernel`); the Gaussian `sqrt(FWHM_common^2-FWHM_model^2)` shortcut is allowed only for Gaussian ILS (`common_R_mode=gaussian`). For asymmetric/sinc/pacs/instrument_kernel ILS without a kernel, compare `group_total`/limits and flag `lsf_unavailable`; never apply a Gaussian kernel to a non-Gaussian ILS. High-R and low-R tools must agree; when `R_common < min_R_deblend`, compare `group_total`, not per-line flux.
- **Floors, objective, limits.** Floors 2 % optical, 10 % NIR, 15 % MIR, 20 % FIR. `chi2_sys` (telluric/OH residual with `T_err`, sky-residual scale and LSF correlation length, fringing, calibration, anchor uncertainty, continuum spread, feature marginalisation where not free) enters the likelihood. `objective = chi2_resel + chi2_sys + sum_k penalty_k`, penalties on log-ratios: PAH 6.2/7.7/8.6/11.3; [Ne III]/[Ne II], [S III] 18.7/33.5; Pa-alpha/Pa-beta, Br-gamma/Pa-beta (case B); [O III] 88/[N II] 122; broad > 2x narrow; [O III] 88/5007. Each has a cited mean, scatter, weight (`penalty_terms`); rank stable at +/-50 %. SNR>3 is detection, else a 95 % limit with `limit_method`/`limit_confidence`.
- **Search and cost.** Prepare hoisted and content-hash cached; per-suite `candidate_schema`; **two-stage coarse->refine with an adaptive CPU cap** (default 60 candidates); deterministic pruning (lower-prior z, then candidates) with `pruned`/`search_truncated`, never a silent fail; one posterior per (spectrum, config); <=3 top-k MCMC; `config_rank_pct`, top-decile outliers flagged. Cost in cpu_s per resel/parameter and mem_gb, measured per tool; planner fits a budget; 500 CPU-h per 10 objects.

### 5.4 Comparison and calibration
- `decomposition_class` = full_model / feature_model / local_gaussian / scan_ils / host. **T0** same segment/aperture/sub_band (cross-segment = T2). **T1a** independent implementation, **gate where two exist, else `T1a=anchor`**. **T1b** median + scatter + outlier fraction inside the envelope. **T2** after the aperture contract; **T3** model-agnostic.
- Grouping key `(measurement_id, spectrum_id, segment_id, suite, aperture_id, beam_id, sub_band_id, line_id, component, quantity_type, decomposition_class)`; `duplicate_of` suppresses double counting; tier per row.
- Contract: canonical units; per-line beam/aperture/EE; common beam or kpc-matched aperture; point sources >=90 % EE; extended surface-brightness matched; `aperture_kpc`/`enclosed_fraction`/`cross_band_class`; >=50 % overlap is necessary, not sufficient.
- **Cross-band is a publish gate.** Matched aperture + enclosed fraction + `mixed` systematic; refuse only when no aperture class encloses >=50 % of both beams or the AGN fraction is unconstrained. AGN hierarchy: X-ray, [Ne V], [O IV], [Si VI], radio; `host_fraction`/`host_subtracted_flux`; `host_dominated` blocks publication. P4 consumes optical **v2**; v1 (ebv=0) is refused.
- **Reddening:** `ebv_mw` (SFD) separate from `ebv_agn` (Balmer/Pa-alpha per family); H/He II use Balmer/Pa-alpha, forbidden lines a separate NLR tracer; MIR/FIR fine-structure lines carry a screen with `A_V` and a validity domain; record `reddening_law`, `R_V`, `ebv_source`, `ebv_used`.
- Bridges via Cloudy/MAPPINGS+PDR; `ratio_type` = atomic|validation|diagnostic|consistency; `component_scope` on every ratio; diagnostics report parameters. Truth on the same spectra/aperture; repeats; NIRSpec/MIRI overlaps.

### 5.5 Provenance, cache, reproducibility
Cache key: SHA256 of inputs, config, commit, image, CRDS, LSF, mask, telluric/PAH/background/calibration, z, seed, aperture/beam/extraction, versions, **plan_hash**, `sub_band_id` (no `posterior_id`); a hit requires matching `plan_hash`. **Posterior schema** with `posterior_sha256`; `covariance_id` on correlated lines; covariance propagated to ratios. **v1 byte-frozen**: `lines.csv` unchanged; `lines_v2.csv` hashes `lines.csv`, `qsopar.fits`, `output.fits`, SFD map and reddening law. Zero-error rows in `lines_v2.csv`: **BADASS (256) -> derive `flux_err` from `runs/<tag>/outputs/badass/**/log/par_table.fits` (the production tree; the `results/at_*` sibling has `sigma=0`), require `std_dev`/`ci_68_*`, and assert nonzero** (`std_dev`/`sigma`; else half the 68 % interval; else 95 %/1.96; for log-flux params `flux*ln10*sigma_log`), `uncertainty_method=posterior_marginal`, `covariance_id=null`, ratio errors by quadrature; `n_free_params`=emcee ndim (21-31), not par_table rows (194-209/236); PyQSOFit (60: OIII5007 narrow/outflow, NII6585 narrow) -> no propagated width in any stored product -> `unavailable`, or re-fit with the `runs_uncertainties` config (verified nonzero) and propagate `scale_err`/`sigma_err`; **FANTASY (2) -> inspect, `unavailable` or re-fit**. No zero error survives; a row with no posterior width is `unavailable` and excluded from T1a/T1b. **Artifacts:** commit rows/hashes/figures; ignore cubes and `runs_ir/`; `.dockerignore`; SHA256 manifest; `legacy_tag_alias`.

Execution: object/spectrum parallelism, containers, MCMC outside search; configs/run tags keyed by suite+spectrum; deterministic figures with optical/IR golden tests.

### 5.6 Host–AGN and SED comparison
- Router: run the host decomposition with every line suite; run the SED suite when matched-aperture photometry exists (or spectra cover the SED), independently of whether lines are detected.
- Comparison tiers: (1) same line/component across tools; (2) line-derived vs SED-derived L_AGN/AGN fraction through a documented bridge; (3) model-agnostic diagnostics (IR BPT, PAH, [C II]/[O I]); report the model-family spread and `host_fraction`.
- Never compare a FWHM to `M_star`; the schema enforces `quantity_type`.

## 6. Phases and gates
2 FTE x 56 weeks = 112 pw; 88 allocated + 18 contingency + 6 reserve. P3 and P4 are serial. Order from the P0 manifest; NIR->MIR->FIR provisional.

**P0a — Foundations (weeks 0-6, 8 pw).** `manifest_lines.csv`/`programs.csv`/`geometry.csv`; per-setting/SPW tables + Registry v1; schemas; 1D + NIRSpec IFU adapters; policies; router/plans; canonical writer + ToolPlugin + dummy tool + CI; optical freeze harness.
**P0b — Vertical slice (weeks 6-10, 6 pw).** One 1D product and one NIRSpec IFU cube end-to-end with the minimal fitter.
**Gate:** tests green (units, registry, router, v1 re-score <1e-6, optical hashes); registry signed; schema published; manifest approved with a named Tier B sample; one real IR line end-to-end; "no eligible redistributable tool" explicit.

**P1 — NIR (weeks 10-30, 26 pw incl. 6 pw blind z).** Blind z, telluric/OH split; rest-optical (A) then (B); Pa-beta/Pa-alpha/Br-gamma with anchored hot dust; NIRSpec 2.5-5.3; broad/narrow; Tier B >=10; **host decomposition (pPXF/STARLIGHT + hot dust) is a gate item and `host_fraction` is recorded**.
**Gate:** per-setting windows; injection into real spectra; telluric stress; **a NIR-native line recovers the anchor or primary standard within budget**; rest-optical >=2 tools or `T1a=anchor`; **>=10 Tier B real spectra with >=1 covered line at S/N>3 and a measured flux or 95 % limit**; BADASS-NIR go/no-go. **Descope:** <5 Tier B covered-line spectra -> methods + Tier C + smoke test, null recorded.

**P2 — MIR (weeks 30-42, 22 pw incl. 2 pw optical v2).** MRS ch3/ch4 and IRS SH/LH clean lines; [S III]/[S IV] feature_group; LRS group/limits; PAHFIT with **separate tau_9.7/tau_18**; wavelength-dependent EE; fringing; IFU after the 2D Gaussian test; **PAHFIT/CAFE host/AGN decomposition with `agn_fraction` and `host_fraction` recorded**. Optical v2 (`lines_v2.csv` from par_table) is derived here and frozen for P4.
**Gate:** [Ne III]/[Ne V]/[O IV] recovery; PAH confusion; **30 % feature error and tau 1-3 in both geometries inside budget, with [S III] 18.7 and [S IV] 10.5 recovered**; **T1b envelope plus a published flux**; **>=10 Tier B real spectra** with a line or limit. **Descope:** <5 clean-line spectra -> LRS group fluxes + methods.

**P3 — FIR (weeks 42-50, 14 pw).** Archival PACS/SPIRE/SOFIA/ALMA; `LineScan` with off-line background and limits; SPIRE `FTS`; ALMA per band/SPW; beam/background/`extent_source`; **P3a** methods + 3 detections, **P3b** >=10.
**Gate:** scan path + flux-only; ILS injection; beam/extended; **published PACS flux or primary standard within budget**; **>=10 Tier B real detections**; else descope/null.

**P4 — Cross-band (weeks 50-56, 12 pw).** T1b; cross-band after aperture and publish gates; three anchored diagnostics ([O III] 88/5007, [Ne III]/[Ne II], [S III] 18.7/33.5); Cloudy/PDR; figures/report.
**Gate:** ratios inside envelope; negative control; publish contract exercised (over-large beam or proprietary spectrum refused); zero silent no-tool; T1b envelope.

**P5 — SED/torus companion + optional UV/X-ray (P5a weeks 42-54, 6 pw from contingency; P5b weeks 56+).** P5a: CIGALE/X-CIGALE, AGNfitter-RX, PROSPECTOR-AGN on matched-aperture photometry + spectra; `agn_fraction`, `L_torus`, `L_AGN`, `M_star`, `SFR`, `dust_luminosity`, model-family spread; compare to line-derived L_AGN/AGN fraction. P5b: UV (PyQSOFit/BADASS + CIGALE) and X-ray (XSPEC/BXA) optional. SED never gates P1–P4. **Schedule note:** P5a consumes 6 of the 18 contingency pw; run concurrently with P3/P4 it needs ~2.5 FTE for weeks 42-54, otherwise it extends the programme by ~3 weeks (to ~59 weeks before the 6 pw reserve).
**Gate (P5a):** AGN fraction/L_torus recovery on synthetic + public templates; model-family spread reported; line-vs-SED comparison documented; no single-number claim without a family.

## 7. Validation
- Geometry/router: golden files; no gaps in a row; ALMA per-SPW edges/gaps including [C II] z=10, z=15.0 and z=30; PACS `scan_type=line` at z=0.1 excludes [O I] 145/[N II] 122; MRS sub-band; LRS group_total vs MRS per-line; PRISM red end; SOFIA/ALMA atmosphere; refusals vs flags; proprietary measure/no-publish.
- Scorer/units: no segment crossing; resel/pixel DOF; n_params; common-R; non-Gaussian ILS and Gaussian-shortcut bias; BADASS par_table flux_err/ndim; penalty stability; v1 re-score <1e-6; optical hashes; `plan_hash`; Jy/beam+beam_sr+nu; MJy/sr+pixel_sr; EE; frame; FANTASY; OR_MASK.
- Host/SED: synthetic AGN+host with known `host_fraction`/`agn_fraction`; pure host, pure AGN, no photometry; model-family spread; line-vs-SED L_AGN/AGN fraction; aperture/beam mismatch; PAH/dust; PDR.
- Nulls/injection: OH/fringe; silicate as a line; CO(30-29) vs [O III] 88; spurious z; Z_NOQSO outlier; single-line pad; cross-band negative; continuum mismatch; 30 % feature error; high-tau silicate; SPIRE baseline; PACS 1-on+3-off; photon-subtracted repeatability at S/N 10/30; broad+narrow <=2 %; router example; ivar=0; deterministic figures; Tier B-only gate.

## 8. Risks and mitigations
No IR spectra/thin pool/confusers: named Tier B, Tier B-only gates, numeric descope, `T1a=anchor`, >=3 anchors/band, generated geometry, always-on z confirmation, per-quality pad. Telluric/PAH/silicate/FIR units/beam: split states + sky-residual metadata, two silicate depths, scan_type/SPW, off-line background + limits, canonical units, EE, publish gate. Optical regression/schedule/calibration: byte-frozen modules/search/report hashes, `pipeline_ir/`, 112 pw (88+18+6), P3/P4 serial, primary standard 5-10/10-15 %.

Host–AGN degeneracy/SED priors: joint/pPXF decomposition, SED prior, model-family spread, `prior_dominated`, report `host_fraction`; never a single SED number.

## 9. Open decisions (defaults; week 2)
Best-covered Tier B first; band order from the manifest; FIR archival-only; host fit with hot dust anchored by matched-aperture NIR photometry; **host method (joint vs pre-subtract vs SED prior)**; **SED family (CIGALE modules, AGNfitter-RX, PROSPECTOR)**; **SED timing (P5a after P2)**; photometry availability; 64-128 cores/256 GB/10 TB; reproducibility = conclusions + hashes + re-score; rights = public + proprietary plugins; artifact/anchor policy per band; named MIR/FIR code or `T1a=anchor`.

## 10. Immediate next steps
1. Query archives; build `programs.csv`/`manifest_lines.csv` from WCS, AOR/ASDM windows and scan_type; generate `geometry.csv`; name Tier B samples and >=3 anchors/band; freeze optical v1 modules/search/report; Registry v1 sign-off; commit v7 (superseded file to `docs/archive/`).
2. Publish schemas, canonical writer, per-segment scorer, ToolPlugin + dummy tool; hoist prepare; z/mask/seed/rights/artifact policies; adapter fields; P0 spikes; 1D + cube pilot.
3. Build the matched-aperture photometry table and the SED/torus pilot (CIGALE/X-CIGALE, AGNfitter-RX, PROSPECTOR-AGN); define `agn_fraction`/`L_torus`/`host_fraction` in the schema.

## Appendix A — Key wavelengths and frames
`lambda_vac` canonical; `lambda_air` optional/null above 2.5 um; air-vacuum applied at the wrapper via per-tool `wave_frame`, tested to 5 km/s. Registry holds vac/air pairs; legacy `score_fits.REST` mixes frames (~73 km/s), frozen for v1.

## Appendix B — Output schema (v2)
v1 unchanged. v2 adds: z (`z_line`, `z_lines[]`, `z_spectra[]`, `z_confirmation`, `z_used_for_windows`, `z_pad_kms`, `z_pad_z`); instrument (`suite`, `setting_id`, `segment_id`, `sub_band_id`, `ils_kind`, `n_pix_used`, `n_free_params`, `plan_hash`); measurement (`measurement_id`, `line_id`, `component`, `component_scope`, `duplicate_of`, `blend_group`, `feature_group`, `quantity_type`, `group_total`, `posterior_sha256`, `covariance_id`, `config_rank_pct`); limits (`snr_basis`, `flux_prior_source`, `limit_method`, `limit_confidence`); feature/continuum (`delta_flux_from_feature`, `delta_flux_from_continuum_model`); calibration (`flux_type`, `flux_unit`, `beam_sr`, `pixel_sr`, `ee_fraction`, `calibration_error`, `ebv_mw`, `ebv_agn`, `ebv_used`); comparison (`extent_source`, `aperture_kpc`, `enclosed_fraction`, `cross_band_class`, `host_fraction`); status (`telluric_absorption_state`, `oh_contamination_state`, `uncertainty_method`, `tier`, `can_measure`/`can_compare`/`can_publish`).
Rules: canonical `flux_unit`; no zero/null error unless `uncertainty_method=unavailable`; `uncertainty_method` = posterior marginal or bootstrap (Fisher search-only); legacy rows carry derived `flux_err` + `uncertainty_provenance`; `quantity_type` separates line/feature/band; ids for T0/T2 and duplicate control.

SED/torus keys (v2): `agn_fraction`, `L_torus`, `L_AGN`, `M_star`, `SFR`, `dust_luminosity`, `sed_model`, `sed_prior`, `model_family_spread`, `host_fraction`, `decomposition_class`.

## Appendix C — Existing repo facts used
20 eFEDS/SDSS-like spectra z=0.0563-0.4675, observed 3601.6-10358.6 A; 46 candidates/object; 1204 `results/at_*` dirs (58-63/object); 318 zero-error rows (256 BADASS, 60 PyQSOFit, 2 FANTASY); BADASS chains not retained but production `par_table` keeps `*_FLUX` with `std_dev` (293/293 rows) and `ci_68` (272/293); ndim 21-31, `par_table` 194-214 (production) / 236-239 (uncertainty re-runs), serial walkers; GELATO NProcess 1; ebv=0 vs SFD_EBV 0.025-0.063; OR_MASK 51 %; 8/20 (9/20 on the alternative Z solution) Z-Z_NOQSO 140-704 km/s; `sculptor` in `collect_results`/`prepare_inputs`.
`score_fits.py`: mixed-frame REST lines (~73 km/s), COMMON_ERR_FLOOR 0.02, `line_penalty` on [O III]+broad Balmer, fixed 5-tool tuple, `np.interp` onto one grid; `auto_tune.objective = chi2_common + 150 x line_penalty`; `per_object_search` reruns per candidate; tool lists hardcoded. BADASS `fit_reg=(2900,8000)` (note 3460,9464), no dust emission; FANTASY crop 2900-8000; `key_produced` is file presence.

## Appendix D — execution_plan.json (illustrative, generated)
```
{"spectrum_id":"synthetic_g235h","z_used":0.312,"z_quality":"B","z_confirmation":"confirmed",
 "segments":[{"segment_id":"g235h","setting_id":"NIRSpec_G235H_F170LP","R_ref":2700,"coverage_intervals":[[1.66,3.17]]}],
 "lines":[{"line_id":"Pa_alpha_1.8756","covered_data":true,"measurable":true,"publishable":true,"quantity_type":"flux"},
  {"line_id":"Br_gamma_2.1661","covered_data":true,"measurable":true,"publishable":true,"quantity_type":"flux"},
  {"line_id":"Br_alpha_4.052","covered_data":false,"measurable":false,"publishable":false,"refusal":"no_coverage"}],
 "can_publish":true}
```

## Revision log (v7 final audit; v8 final verification; v9 host–AGN/SED/torus)
- Pad: `c|Z-Z_NOQSO|/(1+z)` with 1 % outlier rule; tests 04545183216, -704 km/s, sigma_z=0.001.
- BADASS errors from `par_table`; ndim DOF; no zero-error row; ALMA per-band/SPW; ILS-kernel convolution (Gaussian only for Gaussian); z=10/gap and router tests.
- Flux scatter split into photon-subtracted systematics (S/N>=10) and total at S/N>=30.
- Schedule serial P3/P4 to week 56; optical v2 in P2.
- Appendix D: Br-alpha at z=0.312 is `no_coverage`; Br-gamma covered.
- v9: added G5 (host–AGN separation) and G6 (SED/torus companion: CIGALE/X-CIGALE, AGNfitter-RX, PROSPECTOR-AGN), §3.6, §5.6, P5a, host/SED validation, risks, open decisions, schema keys. SED is a companion and never gates P1–P4.
- v12: tools moved to `Tools/`, runners to `Pipelines/`, optical production results migrated to `outputs/<object>_z_<z>/<tool>/`; CIGALE real errors, AGNfitter-rx, PDS/FIR/NGC 4151/NIR extraction fixes, and statistical comparison figure.
- v11: source-keyed layout and single runner; real PACS/HIFI/Spitzer IRS adapters; real NGC 253 MIR+FIR and NGC 1068 FIR tests; PyQSOFit real errors/host-free UV; pPXF reliability/upper limits; PDS 456 segment/quality handling; CIGALE two torus families and WISE diagnostics.  See `docs/CAVEAT_FIXES.md`.
- v10: implementation-status note; P5a CIGALE pilot (`cigale_sed`) on five z>0.5 eFEDS QSOs with SDSS+WISE; results and caveats in `cigale_sed/README.md` and `outputs/<source>_z_<z>/cigale_sed/`.  The design/gates are unchanged; AGNfitter-RX, PROSPECTOR-AGN and X-ray/radio SED constraints remain open.
## v8 final-verification corrections

Both the senior software engineer and the professor astronomer returned verdict **sound** with **zero critical/major** gaps. The following minor factual corrections and specification additions are incorporated here (factual fixes are also applied in the body).

- **Per-family parameter attribution.** `n_free_params` is per scored family (`param_map`), not the run-global ndim; a subset-scored family must not subtract the full 21-31. If unavailable, require suite = full run.
- **DOF guard.** Rank on `chi2_red_resel` only for `dof_resel >= 3`; for `scan_type in {line,fts}` use total chi2 + AIC/BIC; `dof <= 0` -> no reduced-chi2 rank, report `dof_insufficient`.
- **`z_cat_outlier` fallback.** If the blind line scan returns only B/C quality, use the catalogue z with `z_ambiguous` and a wide pad, or refuse; never leave the object with empty windows.
- **FIR repeatability asymmetry.** There is no total-repeatability row at S/N=10 in the FIR: 5 % systematic (+) 3.3 % photon = 6 % > 5 %. State this explicitly; the FIR gate is systematic-only at S/N>=10 and total only where S/N>=30.
- **`R_common` is model-side.** The data are never degraded. Chi2 is computed at the segment's measured R; `R_common` is used only for the per-line vs `group_total` decision. A genuine common-R comparison requires a data-side kernel and noise covariance; if absent, do not claim common-R.
- **Objective scale.** Normalize `chi2_resel` (reduced) and `chi2_sys` (total) before summing; penalty weights are per resolution element, not per window. Report both terms.
- **ALMA table is per band, not per ASDM.** Real ASDM windows cover a few GHz; coverage comes from the ASDM/SPW intersection, not the full band row. Add an ASDM-intersection test and caption.
- **Refusal semantics.** `outside_spectral_window` = line outside this setting's segment; `no_coverage` = no segment covers it. Keep them distinct in the schema and router tests.
- **IR figure/report deliverables.** Extend `collect_figures.py`/`make_report.py` with per-object IR line panels, ratio/diagnostic panels, and a determinism hash; a golden-figure test is required.
- **Ownership/FTE.** Name the 2 FTE split per phase; optical v2 (2 pw) is owned in P2 and frozen for P4. P3/P4 are serial.
- **Optical v2 MW extinction.** v2 applies the SFD screen to measured fluxes and records `ebv_used`/A_lambda; the 6-16 % effect at H-alpha is inside the 10-20 % cross-band budget. State post-hoc screen vs re-fit.
- **Tied doublets.** [O III] 4959/5007 and [S II] ratios are tied; do not use legacy quadrature ratios as anchored diagnostics; carry `covariance_id` for tied pairs.
- **PyQSOFit 60 rows.** Default: mark `unavailable` (documented reduced T1b population for O III 5007 / N II 6585). Re-fit with `runs_uncertainties` (verified nonzero) only in P2 if the T1b population is too small.
- **Appendix D.** The illustrative plan uses `synthetic_g235h` and `z_quality B` because Pa-alpha + Br-gamma are one species; add He I 2.0587 or [Fe II] 1.644 in G235H to make it A.
- **Corrected measured facts.** NIRSpec gratings R 500-2700 (prism 30-330); [O IV] IRS LH 17/20 (18/20 with 37.2 um); 8/20 (9/20 on the alternative Z solution) Z-Z_NOQSO; observed 3601.6-10358.6 A; production `par_table` 194-214 rows with 293/293 `std_dev`; 1204 `results/at_*` dirs.
- **Legacy ratios.** Do not use legacy quadrature ratios for kinematically tied doublets as anchored diagnostics; keep 4959/5007 out of the penalty when tied.
