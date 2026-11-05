# Plan: IR AGN Emission-Line Analysis (NIR, MIR, FIR)

Status: v1 — revised scope (IR emission lines first; SED/torus secondary)
Repo: `/home/onur/Documents/AGNEmissionLines_ThirdPartyLibraries`
Scope: planning only. No code, no fits, no repository changes in this phase.

---

## 0. Executive summary

The user wants to extend the existing **optical emission-line factory** to
**near-, mid- and far-infrared AGN emission lines**, not primarily to SED
fitting. The target behaviour is the same as today:

1. read an object (spectrum + redshift),
2. detect/use the redshift to decide which rest-frame lines are observable,
3. select the tool(s) that can fit those lines in the available observed band,
4. run the per-object config search, score, compare and plot as for the optical
   five-tool suite.

The key correction to the external advice: **IR line analysis is a line-fitting
problem, not automatically an SED problem.** SED/torus fitting (CIGALE,
AGNfitter-RX, PROSPECTOR) is a *separate, later suite* used for AGN fraction,
torus luminosity and host properties — it does not replace line fitting.

The central technical object is a **line registry + coverage router**: for each
object it computes `λ_rest = λ_obs/(1+z)`, finds which NIR/MIR/FIR lines fall in
the observed coverage at sufficient predicted S/N and resolution, and selects the
line-fitting suite/tool. Redshift alone is not enough: two objects at the same z
with different observed bands (or with/without spectra) need different tools.

The hard parts are **not only AGN–host separation**:
telluric absorption/OH (NIR), PAH/dust and fringing (MIR), background/beam and
atmospheric transmission (FIR), flux calibration/slit losses/beam matching,
line blending, LSF/resolution, extinction, low S/N, AGN-vs-star-formation
diagnostics, and valid cross-band comparison.

---

## 1. Goals, scope, non-goals, success criteria

### 1.1 Goals
- **G1 — NIR lines:** fit rest-frame optical/NIR lines in observed NIR spectra
  (e.g. Hα, Hβ, [O III], Paα, Paβ, Brγ, He I/II, [S III], H2) for z ≳ 0.3–3.
- **G2 — MIR lines:** fit MIR fine-structure and molecular lines / PAH features
  ([Ne II] 12.8, [Ne III] 15.6, [Ne V], [O IV] 25.9, [S III] 18.7, [S IV] 10.5,
  [Ar II]/[Ar III], H2, PAH 6.2/7.7/8.6/11.3) in JWST/MIRI or Spitzer/IRS spectra.
- **G3 — FIR lines:** fit FIR fine-structure lines ([O I] 63/145, [O III] 88,
  [N II] 122, [N III] 57, [C II] 158, [Si II] 34.8) in Herschel/SOFIA/ALMA spectra.
- **G4 — Router and comparison:** redshift+coverage-driven tool selection,
  per-object search, shared scoring, cross-tool and cross-band comparison, with
  provenance and audit.
- **G5 — Preserve the optical pipeline:** the 20-object optical results remain
  reproducible; the new suites plug in without forking the repo.

### 1.2 Non-goals (this phase)
- No implementation, no new science claims, no fits.
- SED/torus fitting is **not** the first deliverable; it is a later suite.
- No survey-scale orchestration; single-object then sample-level.
- No replacement of instrument pipelines (telluric correction, flux calibration,
  fringe correction, cube reconstruction remain upstream, but their products and
  uncertainties are consumed and modelled).
- No sub-mm/ALMA *continuum* science in v1 beyond the FIR line windows; no
  radio/gamma-ray line analysis.
- No claim that a line is detectable from geometric coverage alone.

### 1.3 Success criteria
- **Line recovery:** injected NIR/MIR/FIR lines recovered with bias ≤5 % and
  scatter ≤10 % (bright, isolated), degrading gracefully with S/N and blending;
  FWHM bias ≤10 % after LSF convolution.
- **Uncertainty calibration:** 68 %/95 % interval coverage within 63–73 %/92–98 %
  on synthetic tests; no zero-error rows without an explicit status.
- **Cross-tool:** same line/component measured by ≥2 tools agrees within a
  documented tolerance (bias and scatter reported, not assumed).
- **Cross-band:** physically expected ratios (Paα/Hα, Brγ/Hα, [Ne III]/[Ne II],
  [O III]88/[O III]5007) are recovered within their model/calibration budget.
- **Router:** every object gets an auditable `execution_plan`; no silent
  "no tool" outcomes; refusals are explicit and tested.
- **Optical regression:** the current optical results are unchanged (or changes
  are explained by a documented extractor/frame fix).
- **Provenance:** every measurement carries tool/version/config/input hashes,
  band, resolution, masks, and uncertainty provenance.

---

## 2. Observed bands, rest-frame lines and redshift limits

### 2.1 The mapping
`λ_rest = λ_obs / (1 + z)`. The router must work in **rest-frame line space**,
not in a single "z threshold". The same observed NIR spectrum contains different
rest-frame lines at different z; the same rest-frame line moves from NIR to MIR
to FIR as z increases.

### 2.2 Bands and facilities (typical)
| band | observed λ | facilities | notes |
|---|---|---|---|
| NIR | 0.8–2.5 µm (ground); 0.6–5.3 µm (JWST/NIRSpec) | VLT/XShooter, Keck/MOSFIRE, Subaru/IRCS, IRTF/SpeX, JWST/NIRSpec | telluric/OH; nodding; slit losses |
| MIR | 5–30 µm | JWST/MIRI (5–28), Spitzer/IRS (5–38), ground 8–13/18–25 | PAH/dust, fringing, zodiacal light, beam |
| FIR | 30–300 µm | Herschel/PACS+SPIRE, SOFIA/GREAT+FIFI-LS, ALMA B6–B10 | beam/aperture, background, atmospheric T |

### 2.3 Rest-frame line families
- **Recombination (NIR/MIR):** Paα 1.875, Paβ 1.282, Paγ 1.094, Brγ 2.166,
  Brα 4.05, Brβ 2.63, Huα 3.74 µm; Hα 0.6563, Hβ 0.4861.
- **Optical/NIR forbidden:** [O III] 0.5007/0.4959, [N II] 0.6585/0.6549,
  [S II] 0.6718/0.6732, [S III] 0.907/0.953, [Fe II] 1.257/1.644,
  [Si VI] 1.963, [Ca VIII] 2.32, [Al IX] 2.04.
- **MIR fine structure:** [Ne II] 12.81, [Ne III] 15.56, [Ne V] 14.32/24.32,
  [O IV] 25.89, [S III] 18.71/33.48, [S IV] 10.51, [Ar II] 6.99, [Ar III] 8.99,
  [Fe II] 5.34/17.9/25.99, [Si II] 34.8, [Mg V] 5.6/7.6, [Na III] 7.3.
- **MIR molecular/PAH:** H2 rotational (5.5, 6.1, 6.9, 8.0, 9.7, 12.3, 17, 28 µm);
  PAH 3.3, 6.2, 7.7, 8.6, 11.3, 12.7, 17, 30 µm.
- **FIR fine structure:** [O I] 63.18/145.5, [O III] 88.36, [N II] 121.9,
  [N III] 57.3, [C II] 157.7, [Si II] 34.8, [S III] 33.48.

### 2.4 Redshift windows for key lines
Approximate z ranges for a line to fall inside an observed band
(`z = λ_band/λ_line − 1`):

| line (µm) | NIR 0.9–2.5 | MIR 5–30 | FIR 30–300 |
|---|---|---|---|
| Hα 0.6563 | 0.37–2.81 | 6.6–44 | — |
| Hβ 0.4861 | 0.85–4.14 | 9.3–61 | — |
| [O III] 0.5007 | 0.80–3.99 | 9.0–59 | — |
| Paα 1.875 | ≤0.33 | 1.67–15.0 | — |
| Paβ 1.282 | ≤0.95 | 2.90–22.4 | — |
| Brγ 2.166 | ≤0.15 | 1.31–12.9 | — |
| Brα 4.05 | — | 0.23–6.41 | — |
| [Ne II] 12.81 | — | ≤1.34 | 1.34–22.4 |
| [Ne III] 15.56 | — | ≤0.93 | 0.93–18.3 |
| [Ne V] 14.32 | — | ≤1.10 | 1.10–20.0 |
| [O IV] 25.89 | — | ≤0.16 | 0.16–10.6 |
| [S III] 18.71 | — | ≤0.60 | 0.60–15.0 |
| [S IV] 10.51 | — | ≤1.85 | 1.85–27.5 |
| [O I] 63.18 | — | — | ≤3.75 |
| [O III] 88.36 | — | — | ≤2.40 |
| [N II] 121.9 | — | — | ≤1.46 |
| [C II] 157.7 | — | — | ≤0.90 |

Practical limits (not geometry):
- Ground NIR: Hα to **z ≈ 2.8** (K band), Hβ/[O III] to ~4 (faint), but telluric
  windows and sensitivity dominate; Paα only z ≲ 0.33, Brγ only z ≲ 0.15.
- JWST/NIRSpec (0.6–5.3 µm): Hα to **z ≈ 7.1**, [O III] to ~9.6, Paα to ~1.8,
  Brγ to ~1.45.
- JWST/MIRI (5–28 µm): [Ne II] to z ≈ 1.2, [Ne III] to ~0.8, [O IV] to ~0.1,
  PAH 11.3 to ~1.5; beyond that these lines move to FIR.
- FIR (30–300 µm): [C II] to z ≈ 0.9, [O III]88 to ~2.4, [O I]63 to ~3.75;
  beyond, they move to sub-mm (ALMA bands).
- Beyond the FIR: line diagnostics are no longer accessible with these bands;
  one moves to sub-mm/ALMA (dust/[C II] at very high z) or to rest-frame UV
  lines in the NIR/MIR. This is an explicit **refusal/other-suite** outcome.

### 2.5 What the router must decide
For each object:
1. redshift and its uncertainty (`z_used`, source, alternative `Z_NOQSO` etc.);
2. each observed spectrum's coverage, resolution, S/N, masks, flux calibration,
   telluric/PAH/background state, beam/aperture;
3. the rest-frame lines in coverage, with predicted S/N and blend status;
4. the line family (recombination/forbidden/coronal/molecular/PAH/fine-structure)
   and the diagnostics it supports;
5. the tool(s) that fit that family in that band;
6. refusals with a reason (no coverage, resolution too low, S/N too low,
   line blended beyond recovery, calibration missing, no tool).

---

## 3. Tool matrix (IR line fitting)

### 3.1 NIR lines (0.8–2.5 µm observed)
| tool | role | readiness / change |
|---|---|---|
| **BADASS3** | full AGN+host line fit, emcee | extend line list to Paα/Paβ/Brγ/He I/He II/[S III]/H2, `fit_reg`, NIR host templates; **walkers serial in this repo** |
| **PyQSOFit** | AGN continuum + broad lines + host | add NIR line priors (Paα/Paβ/Brγ, He I/II), NIR Fe II, telluric mask; no native walker pool |
| **FANTASY** | parametric AGN line model, MC errors | extend crop (currently 2900–8000 Å) and line CSVs; add NIR lines and hot-dust continuum |
| **GELATO** | line fit + bootstrap errors | add NIR line groups, continuum windows, telluric mask |
| **GLEAM** | one Gaussian per line + local continuum | extend `line_table.fits`, telluric mask, wider windows |
| **pPXF / STARLIGHT** | host stellar decomposition | NIR stellar libraries (eMILES, APOGEE/IRTF), kinematics |
| **molecfit / TelFit** | telluric correction (or standard-star ratio) | upstream/optional; record state and uncertainties |

### 3.2 MIR lines (5–30 µm observed)
| tool | role | notes |
|---|---|---|
| **PAHFIT** | PAH + dust continuum + line decomposition | standard for Spitzer/IRS and JWST/MIRI; not AGN-specific |
| **CAFE** | AGN MIR spectral fitting (torus + lines) | AGN-oriented; verify line list and priors |
| **SMART** | IRS spectral analysis | Spitzer-era; wrap or replace |
| **pPXF / STARLIGHT** | stellar/host contribution | MIR stellar continuum is hard; use with care |
| **pyspeckit / astropy / scipy** | Gaussian/line fitting | fallback and cross-check; full control of masks |
| **JWST/MIRI pipeline products** | fringe-corrected spectra, errors | consume, do not re-reduce |

### 3.3 FIR lines (30–300 µm observed)
| tool | role | notes |
|---|---|---|
| **pyspeckit / LineFit / astropy** | Gaussian line fitting | portable fallback; line windows and blends |
| **CLASS/GILDAS** | ALMA spectral-line fitting | ALMA B6–B10; beam/continuum |
| **CASA specfit/imfit** | ALMA cube/spectrum line fitting | if cubes; aperture/beam |
| **Herschel HIPE / SOFIA pipelines** | PACS/SPIRE/GREAT/FIFI-LS products | consume calibrated spectra/errors |
| **custom multi-Gaussian** | [C II]/[O I]/[O III]/[N II] complexes | blending and PDR decomposition |

### 3.4 Secondary / later suites
- **SED/torus:** CIGALE/X-CIGALE, AGNfitter-RX, PROSPECTOR-AGN, IRAGNSEP —
  for AGN fraction, L_torus, M*, SFR, dust; not a substitute for line fits.
- **UV:** PyQSOFit/BADASS UV lines, CIGALE UV continuum (later).
- **X-ray:** XSPEC/BXA/SPEX, AGNfitter-RX (later).

### 3.5 Parallelisation reality
- Existing tools: BADASS3 (serial walkers in this repo), PyQSOFit, FANTASY,
  GELATO serial per object; GLEAM has batch multiprocessing.
- New tools: PAHFIT/CAFE per spectrum serial (verify cube modes); CIGALE
  parallel over models/objects, not one SED; AGNfitter/emcee must be tested;
  CLASS/CASA may be multi-process.
- **Primary lever remains object-level parallelism.** Any intra-object claim is
  evidence-classed (`{verified, unverified, refuted}`) and smoke-tested.

---

## 4. What actually breaks (not just host–AGN)

1. **Telluric absorption and OH sky** (NIR): without correction/masking, line
   fluxes and continua are biased; the telluric state and standard-star model
   must be recorded.
2. **PAH/dust continuum and fringing** (MIR): PAH features can mimic or hide
   lines; detector fringes and zodiacal light need handling.
3. **Background/beam/atmospheric transmission** (FIR): beam size, aperture,
   nodding, and sky subtraction dominate the error budget.
4. **Flux calibration, slit losses, aperture/beam matching**: absolute fluxes
   across bands are not directly comparable without a calibration contract.
5. **Host starlight** (NIR) and **star formation/PDR** (MIR/FIR): dilution and
   contamination; host/AGN decomposition is required.
6. **Line blending**: Hα/[N II], [S II] doublet, Paα/He I, PAH/H2, [C II]/[O I],
   [O III]88/[N II]122; tied components and blend totals.
7. **Resolution/LSF**: FWHM and kinematics are biased if the LSF is not
   convolved/recorded.
8. **Extinction**: use Paα/Brγ and Hα/Hβ; record `SFD_EBV` and the dereddening
   state; the current optical configs use `ebv=0` and may have a 10–23 % flux
   deficit at Hα/Hβ.
9. **Low S/N / detector artifacts**: MIR/FIR lines are often faint; upper limits
   and non-detections must be modelled, not discarded.
10. **AGN vs star formation**: MIR/FIR lines are not uniquely AGN; use
    [Ne V]/[O IV]/[Ne III]/[Ne II], PAH, [C II]/[O I], BPT-like IR diagrams.
11. **Redshift errors/systematics**: `Z` vs `Z_NOQSO` differences can be
    100–700 km/s; record `z_used` and the choice.
12. **Comparison validity**: a line ratio from NIR and a ratio from FIR are not
    the same measurement; comparisons need typed quantities and a documented
    bridge.

---

## 5. Architecture (extend the existing repo)

### 5.1 Data model
- `Spectrum`: wave, flux, error/ivar, mask, unit, frame, z, z_err, band,
  instrument, resolution/LSF, telluric/PAH/background state, aperture/beam,
  flux-calibration state, provenance.
- `LineRegistry`: line name, rest wavelength, family, band preferences,
  diagnostics, blend groups, expected ratios, prior constraints.
- `LineMeasurement`: object, spectrum, tool, line, component, kinematics
  (flux, FWHM, velocity offset, EW), uncertainties, status, provenance.
- `Photometry` (later SED): band, λ_eff, flux, error, upper limit, filter.

### 5.2 Router (z + coverage + line registry)
- Input: `z`, spectra (coverage, R, S/N, masks), available photometry.
- Steps: compute rest-frame coverage; find lines; predict S/N; classify family;
  select suite/tool; produce `execution_plan.json` with reasons and refusals.
- Rules are **line-and-coverage-based**; redshift is the key input but not the
  only one. Explicit `--dry-run` and `--goal` (line kinematics, ratios,
  diagnostics, host, SED) modes.
- Refusal statuses: `no_coverage`, `resolution_insufficient`, `insufficient_snr`,
  `blended_beyond_recovery`, `calibration_missing`, `no_tool`, `not_agn`,
  `host_dominated`, `z_unverified`.
- The router is auditable and tested; it never silently drops an object.

### 5.3 Tool registry and wrappers
- `tool.yaml` per tool: bands, lines, inputs, outputs, backend (venv/Docker/
  conda), resource needs, timeout, parallelisation (evidence class), version,
  known failure modes.
- Wrapper contract: `validate(input) -> run() -> normalize(output)`.
- Existing Docker/venv backends reused; new tools get pinned containers
  (PAHFIT/CAFE, CASA/CLASS, JWST/Spitzer readers).

### 5.4 Suites
- `nir_lines`, `mir_lines`, `fir_lines` (v1); `sed`, `uv_lines`, `xray` later.
- Each suite: configs/candidate grid, objective, scorer, figures, validation.
- Reuse `per_object_search.py`-style per-object search: candidate grid per tool
  (line components, ties, continuum, masks), score by line-fit quality and
  physical penalties (ratios, negative fluxes, blend consistency), then apply the
  winner per object.

### 5.5 Normalization and comparison
- Typed quantities: `line.flux`, `line.fwhm`, `line.ew`, `line.ratio`,
  `line.velocity`, `continuum`, `sed.*`, `xray.*`.
- Tier 1: same line/component, same method class (cross-tool).
- Tier 2: same physical quantity via a documented bridge (e.g., Paα/Hα
  case-B ratio; [O III]88/[O III]5007; [Ne III]/[Ne II]).
- Tier 3: model-agnostic diagnostics (IR BPT-like diagrams, PAH equivalent
  widths, [C II]/[O I]).
- No direct comparison of a line FWHM to a stellar mass; the schema enforces
  quantity types.
- Report bias/scatter/outliers with uncertainties; never a bare "average".

### 5.6 Provenance, caching, reproducibility
- Manifest per object/spectrum/suite/tool/run: input hash, config hash, code
  and container digests, seed status, masks, LSF, telluric/PAH/background state,
  calibration, `z_used`, runtime, quality flags.
- Cache key includes all of these; no reuse across incompatible versions.
- Baselines: optical v1, optical v2 (corrected extractor), IR pilot.
- Seed inventory: BADASS/PyQSOFit/FANTASY currently have no seed; GELATO has
  `RandomSeed`; GLEAM least-squares.

### 5.7 Execution
- Object-level parallelism; per-tool containers; resource-aware scheduling;
  partial-product retention; retries; explicit timeouts (no silent kill).
- Keep `run_pipeline.sh` as the compatibility entry point; add
  `run_suite.sh` / `analyze_all.sh` for routed multi-suite runs.

### 5.8 Proposed repo layout
```
pipeline/
  data_model/        # Spectrum, LineRegistry, LineMeasurement, Photometry
  adapters/          # SDSS/eFEDS, NIR (XShooter/IRTF/NIRSpec), MIR (IRS/MIRI),
                     # FIR (PACS/SPIRE/GREAT/ALMA), photometry, X-ray (later)
  router/            # coverage+line router, execution_plan, audit
  suites/
    nir_lines/       # extended optical tools + host/telluric
    mir_lines/       # PAHFIT, CAFE, SMART, custom
    fir_lines/       # pyspeckit, CLASS, CASA, HIPE/SOFIA
    sed/ uv_lines/ xray/   # later
  normalize/ compare/ validation/
configs/<suite>/<tool>/<variant>/
schemas/
docs/
```

---

## 6. Phases and gates

### P0 — Foundations (weeks 0–6)
- Line registry (NIR/MIR/FIR), data model, router v0 with `--dry-run`/audit.
- Synthetic IR line generator (per band, resolution, telluric/PAH/background,
  noise, blends).
- Optical regression: current 20-object results unchanged; extractor/frame
  fixes (frame, centroid, `par_table` CIs, zero-error provenance) documented.
- **Gate:** optical regression passes; router decisions auditable; synthetic
  line recovery in the optical works; IR line registry reviewed by the
  astronomer.

### P1 — NIR lines (weeks 6–18)
- Extend BADASS/PyQSOFit/FANTASY/GELATO/GLEAM line lists, `fit_reg`, continuum,
  host templates, telluric masks.
- Telluric state + correction/masking; OH residuals; LSF.
- NIR host decomposition (pPXF/STARLIGHT) and AGN/host joint fit.
- **Gate:** injected Paα/Paβ/Brγ/Hα recovery at z = 0.5/1/2/2.5; cross-tool
  agreement on Hα/Hβ/[O III] in NIR; telluric-window sensitivity; one real
  archival NIR spectrum end-to-end.

### P2 — MIR lines (weeks 12–26)
- Integrate PAHFIT (PAH/dust/lines) and CAFE (AGN MIR); Spitzer/IRS and
  JWST/MIRI adapters; fringe/zodiacal handling; beam/aperture.
- MIR line diagnostics ([Ne II]/[Ne III]/[Ne V]/[O IV], PAH, H2).
- **Gate:** synthetic MIR line recovery; PAH/line confusion tests; one real
  MIR spectrum end-to-end; cross-check PAHFIT vs custom Gaussian fits.

### P3 — FIR lines (weeks 20–32)
- FIR adapters (Herschel PACS/SPIRE, SOFIA GREAT/FIFI-LS, ALMA B6–B10).
- Line fitting for [O I] 63/145, [O III] 88, [N II] 122, [C II] 158; background,
  beam, atmospheric transmission; blended complexes.
- **Gate:** synthetic FIR recovery; beam/aperture and background tests; one real
  FIR spectrum/cube end-to-end; cross-check pyspeckit vs CLASS/CASA.

### P4 — Cross-band comparison and diagnostics (weeks 28–38)
- Cross-tool same-line comparison; cross-band ratios; IR diagnostic diagrams;
  host/AGN flags; comparison report.
- **Gate:** ratio recovery on synthetic multi-band objects; documented systematics;
  router runs end-to-end on a mixed sample.

### P5 — Optional SED/UV/X-ray (weeks 36+)
- CIGALE/X-CIGALE, AGNfitter-RX for AGN fraction/L_torus/M*/SFR; UV and X-ray
  suites. Not required for G1–G4.

---

## 7. Validation

- **Unit:** adapters, units, rest-frame transforms, masks, line registry,
  router, schema.
- **Synthetic injection–recovery:** per band, per line family, at the planned
  z/R/S/N; telluric/PAH/background stress; blends; upper limits.
- **Cross-tool:** same line/component, ≥2 tools; bias/scatter/outlier rate.
- **Cross-band:** Paα/Hα, Brγ/Hα, [Ne III]/[Ne II], [O III]88/[O III]5007,
  [C II]/[O I]; compare to case-B/PDR expectations; report systematics.
- **Null tests:** no lines, pure starlight, pure PAH/dust, pure PDR, wrong z,
  low S/N, edge coverage, bad calibration.
- **Real pilot:** one object per band, end-to-end, with a published/reference
  measurement where available.
- **Regression:** optical results and figures unchanged (or documented).
- **Performance:** runtime/RAM per tool per object; scale to N objects.

---

## 8. Risks and mitigations

| risk | impact | mitigation |
|---|---|---|
| Telluric/OH residuals | biased NIR lines | T(λ) state, masks, standard-star correction, stress tests |
| PAH/dust/fringing | false MIR lines | PAHFIT + custom fits, fringe masks, cross-checks |
| FIR background/beam | large systematics | beam matching, aperture corrections, PDR modelling |
| Flux cal/slit losses | wrong absolute fluxes | calibration contract; relative/ratio comparisons first |
| Host/AGN degeneracy | biased lines | joint/pPXF decomposition, priors, report multi-modality |
| Blending | wrong components | tied components, blend totals, high-R data |
| LSF mismatch | biased FWHM | LSF asset, convolution, resolution gate |
| Low S/N | upper limits | survival analysis/limits, not discarding |
| Tool claims/parallelisation | wrong cost/ETA | evidence classes + smoke tests |
| Cross-band comparison | false conclusions | typed quantities + documented bridges |
| Data access/rights | delay | archive preflight, fallbacks, pilot_only |

---

## 9. Open decisions (need the user)

1. **First IR dataset/instrument:** JWST/NIRSpec, ground NIR (XShooter/IRTF/
   Subaru), Spitzer/IRS, JWST/MIRI, Herschel/SOFIA, ALMA? Which sample?
2. **Line/diagnostic priority:** Paα/Paβ/Brγ BH mass and extinction first, or
   MIR ionization diagnostics, or FIR PDR/star-formation lines?
3. **Band order:** NIR → MIR → FIR (recommended) or NIR+FIR first?
4. **Host decomposition:** pre-subtract (pPXF) vs joint fit vs model-averaged.
5. **SED timing:** after line suites (recommended) or in parallel for AGN
   fraction?
6. **Compute/environment:** CASA/CLASS/JWST pipelines; cores/RAM/disk; cluster?
7. **Reproducibility target:** bit-for-bit or "same conclusions within errors"?
8. **Data rights:** public archives only, or proprietary/institutional data?

---

## 10. Immediate next steps (after this plan is reviewed)

1. Freeze the **line registry** and **output schema** (NIR/MIR/FIR).
2. Build the **router v0** with `--dry-run` and an audit log.
3. Extend **one NIR tool** end-to-end on a public NIR spectrum.
4. Add **PAHFIT** (MIR) and **pyspeckit/CLASS** (FIR) pilots.
5. Only then scale to the sample and add SED/UV/X-ray.

---

## Appendix A — Key line wavelengths (µm unless noted)

NIR: Hα 0.6563, Hβ 0.4861, [O III] 0.5007/0.4959, [N II] 0.6585/0.6549,
[S II] 0.6718/0.6732, [S III] 0.907/0.953, Paα 1.875, Paβ 1.282, Paγ 1.094,
Brγ 2.166, Brβ 2.63, Brα 4.05, He I 1.083/2.058, He II 1.64/4.05,
[Fe II] 1.257/1.644, [Si VI] 1.963, [Ca VIII] 2.32, H2 2.121.

MIR: [Ar II] 6.99, [Ar III] 8.99, [S IV] 10.51, [S III] 18.71/33.48,
[Ne II] 12.81, [Ne III] 15.56, [Ne V] 14.32/24.32, [O IV] 25.89,
[Fe II] 5.34/17.9/25.99, [Si II] 34.8, [Mg V] 5.6/7.6, [Na III] 7.3,
H2 5.5/6.1/6.9/8.0/9.7/12.3/17/28, PAH 3.3/6.2/7.7/8.6/11.3/12.7/17/30.

FIR: [N III] 57.3, [O I] 63.18, [O III] 88.36, [N II] 121.9, [O I] 145.5,
[C II] 157.7, [Si II] 34.8, [S III] 33.48.

## Appendix B — Output schema (draft)

```
object_id, ra, dec, z, z_err, z_used, z_source, band, instrument,
spectrum_id, aperture, beam, resolution, frame, unit,
tool, tool_version, container_digest, config_hash, run_id,
line, line_family, component, blend_group,
flux, flux_err_low, flux_err_high, fwhm, fwhm_err, v_offset, ew,
ratio_name, ratio_value, ratio_err, ratio_bridge_id,
status, quality_flags, uncertainty_provenance, mask_state,
telluric_state, pah_state, background_state, flux_cal_state,
runtime_s, provenance_uri
```

## Appendix C — Existing repo facts used

- 20 eFEDS/SDSS-like optical spectra, z 0.0563–0.4675, observed 3567–10399 Å;
  46 candidates/object; 709 variant dirs; results/lines.csv 1058 rows with
  318 zero-error rows (256 BADASS, 60 PyQSOFit, 2 FANTASY); BADASS `ndim`
  21–31; `par_table` 194–209 rows; BADASS walkers serial; GELATO `RandomSeed`;
  current `ebv=0` vs `SFD_EBV` 0.025–0.063; `OR_MASK` ≠ 0 on 51 % of pixels;
  9/20 `Z` vs `Z_NOQSO` offsets 140–704 km/s.
- These facts motivate P0 (extractor/frame/uncertainty/calibration) before any
  IR extension; they do not change the IR line-analysis plan.

## Appendix D — Router decision table (illustrative)

| z | observed coverage | rest-frame lines | suite |
|---|---|---|---|
| 0.5–2.8 | NIR 0.9–2.5 µm | Hα/Hβ/[O III]/[N II]/[S II] | nir_lines |
| 0.0–0.33 | NIR | Paα/Paβ/Brγ | nir_lines |
| 1.3–12.9 | MIR 5–30 µm | Brγ, [Ne II], [Ne III], [S IV], PAH | mir_lines |
| 1.7–15 | MIR | Paα, Paβ | mir_lines |
| 1.3–22 | FIR 30–300 µm | [Ne II], [Ne III], [S III], [O IV] | fir_lines |
| 0.16–10.6 | FIR | [O IV] 25.9, [O III] 88, [C II] 158 | fir_lines |
| >7–10 | NIR/MIR | rest-frame UV lines (Lyα/C IV/Mg II) | uv_lines (later) |
| no line coverage | any | — | sed/continuum or refusal |

## Appendix E — Corrections to the external advice

- **IR line analysis is not SED fitting.** SED tools are complementary; they do
  not replace line fitting. The user's case is line analysis first.
- **BADASS3 does not parallelise walkers in this repo** (no `pool`/`threads`);
  treat its MCMC as serial per object.
- **FANTASY's repo config crops 2900–8000 Å**; NIR coverage requires code/config
  changes, not just a template claim.
- **CIGALE parallelises models/objects**, not a single SED.
- **"Beyond z≈3 use JWST/MIRI"** is too coarse: which lines are accessible
  depends on the line and the band; the router uses the line registry.
- **AGN–host separation is not the only problem**; see §4.
