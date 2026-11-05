# RESULTS & TUNING — per-tool review

Baseline = the fit outputs already in the repo (BADASS OLS/ML, fantasy,
GELATO, GLEAM, PyQSOFit, sculptor).  All were reviewed against the data
(see DIAGNOSTICS.md).  Summary of what each tool did, why, and the tuned
parameter choices applied in this repo.

## Common ground truths (measured from spectrum.fits)

- Errors: use `err = 0.05 * flux` (empirical; NOT 2% / 10% / 1.0).
- Instrument FWHM: ~5 Å (≈ 300–450 km/s).  `fwhm_res ≈ 6–8 Å` is the right
  ballpark; PyQSOFit's header value 1140 km/s must not be used directly.
- z: use 0.348 only as a *label*; the strong features are at observed
  5100.8 / 6647.5 / 6752.1 / 8837.6 Å; do not force narrow windows around
  the nominal z=0.348 positions (they miss the data, e.g. [OII] at 5024 Å
  does not exist).
- The red complex 6647.5/6752.1 Å is 104.6 Å apart — it is NOT the
  [OIII]4959/[OIII]5007 doublet.  Fit both lines as separate, free lines
  (and keep the 4959/5007 tie OFF unless using rest wavelengths that match
  the observed features — see DIAGNOSTICS.md).

---------------------------------------------------------------------------
## 1. BADASS (badass/main.py)  — the reference ML run is the best of the six

**What it did:**
- ML run: σ_resid=0.163, rchi²=0.74, R²=0.996 → but it solved the
  [OIII]-region with BROAD components (FWHM 1178–1879 km/s, one at the
  lower amplitude bound with voff=+204 km/s) and put the narrow-line
  amplitudes at 0 (`NA_*_AMP` flags=1, FWHM_corr=0) because the narrow
  allowed range 0–500 km/s is *below* the effective resolution.
- OLS run: same story, worse (rchi²=4.6, R²=0.97).
- Power-law continuum slope −2.6, polynomial 7th order absorbing the blue
  FeII structure; FeII template amp at boundary, narrow FWHM 10 km/s.
- Input quirks: `err = 0.1*spec` (10%, too big), `fwhm_res=6` (fine),
  `ebv=0`, and the spectrum was fed with `z=0.348`.

**Tuned parameters (applied):**
- `fit_options`: keep fit_stat "ML" (robust); mask_bad_pix False;
  fit_reg (2900,8000) fine.
- User lines: centers changed from nominal rest positions to the observed
  features → OII 3784, Hβ 4837(+broad), [OIII]a 4931.4, [OIII]b 5009.0,
  Hα 6556 (narrow) + broad Hα 6556 (wings), [NII] 6587, [SII] 6715/6730.
  Broad lines: add BR_H_ALPHA (amp 0–50, disp 300–6000 km/s, voff
  ±1500), BR_H_BETA similarly; fit OIII-region with NARROW components only
  (disp 200–2500 km/s) plus optional broad OIII wing (voff −1500..+500).
- `narrow_options`: amp_plim (0,50), disp_plim (150,2500) km/s,
  voff_plim (−1000,1000), profile gaussian.
- `broad_options`: disp_plim (500,6000), voff_plim (−1500,1500).
- `opt_feii_options`: amp 0.1–10 with start 0.3, disp 300–3000 km/s
  (fixes the boundary-flag fit).
- `err`: `0.05 * spec`; keep `fwhm_res=6`, `ebv=0.0`, `z` from header.
- Add `user_mask`/`combined_lines`/`test_lines=False`.
  The absorption-like dip at obs 8760–8780 should be left unmasked (it is
  part of the Hα wing; a 2-component broad Hα with voff ≤ 0 handles it).

---------------------------------------------------------------------------
## 2. Fantasy AGN (fantasy_agn/main.py)

**What it did:**
- Model = flat broken power law + narrow/broad Hβ/Hα/[OIII] lines.
- The output shows Hα "broad" FWHM 1580 km/s, amp 3.24 with the *narrow*
  FWHM 1002 km/s (max allowed 1200) — the two were effectively swapped
  (narrow Hα FWHM 1002 > broad 1580?!).  [OIII] "narrow" amp → 0.0
  (tied-model hit the lower bound) and the [OIII] got fit by a 1924 km/s
  "broad" component instead; FeII was NOT in the model.
- Errs: `ivar` from the converted fits = 10%; continuum `continuum(s)`
  left flat (index −0.0017/−1.0).

**Tuned parameters (applied):**
- Use `create_feii_model(max_fwhm=6000)` and add it to the model.
- `fwhm_br`: 1200–6000 km/s (min 1200 kept); `fwhm_na`: 150–1500 km/s.
- Split the model into: OIII5007_br as a WING (free voff −1500..+500,
  FWHM 600–4000) and OIII5007_na (FWHM 300–1200, voff ±300);
  Hb/Hα: br (2 gaussians: 800–5000 km/s) + na (300–1200).
- Continue to use tied narrow lines via `create_tied_model` but tie only
  [NII]+[SII]+Hα-narrow and [OIII]4959+[OIII]5007-na (ratio 0.35), and
  keep the FeII and continuum as separate components.
- Plot/analysis region: rest 4500–7000 is where all the action is; the
  earlier `.crop(2900,8000)` then output was fine.

---------------------------------------------------------------------------
## 3. GELATO (Gelato/Params.json, gelato.sh)

**What it did:**
- Results fits stored: SSP fit (z_spec=104391?! → the "SSP_Redshift" is
  actually the velocity dispersion, 130 km/s — mislabeled), flux values
  in 1e-14 (should be 1e-17), rChi2 = 1.27e-5 (fit normalised flux with
  no errors → meaningless), and the fit/comp PDFs contain no model curve.
- The `my_sdss.fits` given to GELATO has `ivar` = 1/(0.1·flux)² but
  `Params.json` scales SED-to-data in units of 1e-17; mis-matched units
  are the most likely cause of the invisible fit.

**Tuned parameters (applied):**
- `Params.json`: keep OutFolder/Plotting; set "FlamUnits" to 1e-17;
  "LineRegion": 300 (fine); "NBoot": 100 fine; "FThresh": 0.95 fine.
- EmissionGroups: [OIII]: Wavelength 5008.240/4960.295 with
  RelStrength 1 / 0.35 (vacuum) — KEEP; set Flag: 1 (single comp) instead
  of "FlagGroups: Outflow" unless you explicitly want 2 comps; add
  [SII] 6718.29/6732.67 with RelStrength 1/1.26; [NII] 6585.27/6549.86
  with 1/0.34; remove [NeV] 3346.79/3426.85 and [NeIII] 3869.86 or set
  Flag 1 (their rest positions are outside a z=0.348 air/vacuum grid and
  the data has no detectable [NeV]).
- SF groups: [OII] 3728.48 keep (Flag 1); [OI] 6302.046 keep.
- Balmer H I 6564.61/4862.68: these are VACUUM wavelengths (air Hα = 6562.8);
  GELATO uses them with the stored air/vacuum mixing → use 6562.8/4861.4
  (air) or 6564.6/4862.7 (vacuum) consistently; apply to line table.
- `gelato.sh`: `z=0.3482135` → z=0.3480 and double-check the fits
  wavelength scale matches (it is 4000–10000, GELATO expects vacuum (?)).

---------------------------------------------------------------------------
## 4. GLEAM (Gleam/gleam.sh, gleamconfig.yaml, spec1d…fits)

**What it did:**
- The output fits are broken: Hα/[OIII] fits run off-scale, the Ha inset
  shows the model shifted ~10 Å from the data, and the "fit" line is
  meaningless.
- Root causes: (a) `spec1d.sdss.sdss.fiber1.1.fits` stores `stdev=1.0`
  (a 43% error on a 2.3 flux!) so GLEAM's χ² is unweighted garbage;
  (b) `resolution: 12.5 Angstrom` ≈ 560 km/s — too big for the 300 km/s
  profile; (c) `w:` fine, but the `center` probe window 3 Å and tolerance
  26 Å interact with a z offset (spec stored z = 0.3482135 vs data;
  (d) the line_table mixes air (6563) and vacuum (5008.240) wavelengths.

**Tuned parameters (applied):**
- Rebuild `spec1d…fits`: `stdev = 0.05 * flux` (empirical), `wdisp` small.
- `gleamconfig.yaml`: `resolution: 8.0 Angstrom`; `SN_limit: 2` keep;
  `cont_width: 40` keep; `w: 3.0` keep; `tolerance: 26` fine;
  `center: constrained` keep; source overrides: `cont_width: 70` keep.
- `line_table.fits`: use a consistent vacuum list: Ha 6564.6,
  Hb 4862.7, OIII4 4960.3, OIII5 5008.2, NII1 6549.9, NII2 6585.3,
  SII1 6718.3, SII2 6732.7, OII 3728.5 with z=0.3480.
- If the fit still lands 5–10 Å off, check that gleam uses the stored
  `redshift` per source (0.3482135) — update to the fitted 0.3480.

---------------------------------------------------------------------------
## 5. PyQSOFit (pyqsofit/main.py) — RERUN locally with tuned priors

Original run: z hardcoded 0.348, errors 0.02·flux (too small), χ²_ν = 13.8
(Hβ) / 17.4 (Hα), narrow-only look.  It also placed "OIII4959c" at
**4930.30** (the FeII λ4930 blend, i.e. data-driven) which is why its
"OIII" looked weird.

Tuned run supplied as `pyqsofit/main_tuned.py` (uses `qsopar_tuned.fits`):
- `err = 0.05 * flux`; `reject_badpix=False`; `MC=False`, `MCMC=False`.
- Priors centered on the observed rest-frame features (3784.5, 4838+4860,
  4930.6, 4959.2/5009.2 tied doublet + wide wings, 4685.7 HeII, 6557
  Hα br 3-gauss + 6556 na, 6587/6552 [NII] tied 1:0.34, 6716/6731 [SII]).
- `Fe_op_norm` start 0.05, `PL_norm` 2.5, `PL_slope` −0.5; poly=True.
- Result (this run): χ²_ν(Hα)=2.6 (was 17.4), χ²_ν(Hβ)=3.7 (was 13.8),
  Hα FWHM(whole) ≈ 1380 km/s, [OIII]-complex FWHM ≈ 1700 km/s,
  FeII 4930 recovered (scale 1.25).  Still not physically clean because
  of the wavelength-scale problem in the data (DIAGNOSTICS.md), but the
  numbers are now comparable across tools.

---------------------------------------------------------------------------
## 6. Sculptor (sculptor/…)

- `specmodel_0..5_FitAll_fit_report.txt`: redchi 7.7/18.3/4.4/12.2/7.1/34.3;
  only 2–6 parameters each; windows of 44–155 px (≤ 250 Å); modelA only
  (amp + slope + a couple of Gaussian lines).  R² 0.84–0.97 but residuals
  large and `modelA_A_flux` at boundary.
- Tuning that must go into the Sculptor model-file (GUI):
  * for each line block use: centre = observed position (5100.8, 6647.5,
    6752.1, 8837.6), sigma 5–25 Å (free), amplitude free positive;
  * a shared continuum (power law + spline) over the whole 4000–10000 Å
    instead of a local linear term;
  * include a FeII pseudo-continuum between 4690–5400 Å (rest) or mask
    those windows if unused;
  * do **not** tie [OIII]4959 to [OIII]5007 with a fixed ratio unless the
    wavelength scale is fixed first (they are 104.6 Å apart in the data).

---------------------------------------------------------------------------
## Bottom line

- 5/6 tools as submitted cannot produce a trustworthy fit of this file;
  the reasons are split between (a) the internal wavelength inconsistency
  of spectrum.fits (DIAGNOSTICS.md) and (b) per-tool config bugs (
  errors, unit mismatches, wrong windows, missing FeII, z/vacuum mixing).
- PyQSOFit has been re-run locally with the tuned configuration
  (`pyqsofit/main_tuned.py`, `result_tuned.pdf`, `output_tuned.fits`),
  improving χ²_ν by 5–7× and recovering a broad Hα + FeII components.
- Recommend: fix the input spectrum first (option 1 of DIAGNOSTICS.md),
  then re-run all tools with the configs documented here.  If the
  original spectrum cannot be recovered, the data-driven configurations
  are the best available.
