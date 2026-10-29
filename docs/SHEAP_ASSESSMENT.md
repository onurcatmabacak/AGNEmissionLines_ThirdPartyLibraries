# SHEAP Hβ/[O III] assessment and repair

**Result: the original SHEAP fit was a model failure, not a measurement of the
object.  It has been repaired and is retained in production.**  The corrected
fit gives χ²_ν = 2.87 and Hβ/[O III] 5007 = 2.025, inside the 1.8-2.5 optical
spread and within a few percent of PyQSOFit, GANDALF and S3Fit.  The old
χ²_ν = 46 / ratio = 4.00 configuration is no longer reachable as a production
result: it is rejected by hard quality gates and by the cross-tool comparison
reader.

Primary object: `04592649654_z_0.5874` (SDSS/eFEDS QSO, z = 0.58741307).
Tool: SHEAP 0.0.11 (PyPI), CPU JAX, Docker image `sheap_line`.
Code: `Tools/sheap_line/run_sheap.py`, `configs/sheap_line/default/config.json`.

---

## 1. Original failure evidence

The committed baseline (git `6ce42884`) fitted rest-frame 4600-5150 Å with one
narrow SPAF component, `n_broad=1`, `fe_mode="None"`, a broken-power-law
continuum and SHEAP's default limits.  Its `run.json` records:

| quantity | baseline | comment |
|---|---:|---|
| χ²_ν | **46.03** | 490 pixels, 13 parameters; the model does not describe the data |
| narrow FWHM | 592 km/s | SHEAP's default narrow upper bound is **600 km/s** |
| broad Hβ FWHM | 8019 km/s | implausibly wide |
| broad Hβ velocity | +1877 km/s | SHEAP's broad `vshift` bound is ±2000 km/s |
| Hβ total | 3256 (1e-17) | 10-18 % above the siblings |
| [O III] 5007 | 814 (1e-17) | 42-46 % below the siblings |
| Hβ/[O III] 5007 | **4.00 ± 0.10** | far outside 1.8-2.5 |

The blue/red residual pattern was diagnostic.  Reconstructing the model from
the native arrays gave, over the fitted region:

| window (rest Å) | median residual/σ | interpretation |
|---|---:|---|
| 4600-4700 | +4.8 | blue continuum/Fe II missing |
| 4850-4875 | +13.9 | Hβ core underpredicted |
| 4970-5000 | +10.8 | [O III] 5007 blue wing missing |
| 5000-5015 | +4.6 | [O III] core too narrow |
| 5015-5060 | +4.2 | red side overpredicted |

### The data are not the problem

A direct, model-independent look at the same spectrum (local linear continuum
from line-free sidebands) gives:

* [O III] 5007 half-maximum width **≈ 966 km/s** (FWHM), far above SHEAP's
  600 km/s narrow cap;
* the [O III] 5007 profile is strongly asymmetric: at −950 km/s (≈4990 Å) the
  line is **≈29 %** of its peak, while at +900 km/s (≈5022 Å) it is **≈8 %**;
* the Hβ profile has FWHM ≈ 1450 km/s including the broad component;
* a direct integration gives Hβ/[O III] 5007 ≈ 1.7-2.1, consistent with the
  sibling fitters (1.83, 1.96, 2.07).

So the object is an ordinary broad-line QSO with a broad [O III] blue wing and
strong Fe II.  The 4.00 ratio came entirely from the model.

## 2. Root causes

1. **Hard narrow-FWHM cap.** SHEAP's `DefaultLimits.yaml` caps narrow
   components at 600 km/s.  The baseline fit sat at 592 km/s.  The model could
   not reproduce the [O III] wings, so the broad Hβ was pushed to +1877 km/s
   (against its +2000 km/s bound) with FWHM 8019 km/s to fill them.  That
   simultaneously removed [O III] flux and added Hβ flux: the 4.00 ratio.
2. **No Fe II template.**  The 4450-5450 Å window contains strong Fe II
   multiplets.  With `fe_mode="None"` the corrected model still fails
   (χ²_ν = 16.8) and the ratio rises to 2.80.  The original adapter disabled
   Fe II because the window was thought to be too small.
3. **Window too narrow.**  4600-5150 Å leaves almost no line-free continuum
   and clips the Fe II blends.  Even with Fe II and a relaxed narrow prior, the
   same 4600-5150 Å model gives χ²_ν = 10.2.  The adopted 4450-5450 Å window
   fixes the continuum and Fe II.
4. **One narrow Gaussian cannot represent the line core and the blue wing.**
   With the wide window, Fe II and a relaxed prior, one narrow component gives
   χ²_ν = 6.43 and ratio 2.13; two components give χ²_ν = 2.87 and ratio 2.02.
   One of the two components (SHEAP's component 1) is a blueshifted
   [O III] wing at −827 km/s with FWHM 1606 km/s and a negligible Hβ
   amplitude; component 2 is the NLR core.
5. **Method mislabelling.**  The old README called SHEAP's `montecarlo`
   posterior "covariance Monte-Carlo draws".  It is a parametric bootstrap
   (resample the spectrum, re-optimise); `covariance_error=True` is the
   separate JTJ covariance.  This did not cause the bad fit, but it made the
   uncertainty provenance wrong.

## 3. Correction tests

All fits use the same input spectrum, `mask_and_mask=true`, and the same
adopted quality gates.  Fluxes are rest-frame 1e-17 erg s⁻¹ cm⁻².

| model | region (Å) | Fe II | narrow | χ²_ν | Hβ | [O III] 5007 | ratio | verdict |
|---|---|---|---:|---:|---:|---:|---:|---|
| baseline | 4600-5150 | no | 1 (cap 600) | 46.03 | 3256 | 814 | 4.00 | **rejected** |
| + Fe II, cap 1500 | 4600-5150 | yes | 1 | 10.17 | 3083 | 1479 | 2.09 | poor fit |
| wide, broken PL, cap 1500 | 4450-5450 | yes | 1 | 6.33 | 3037 | 1401 | 2.17 | acceptable, not preferred |
| wide, power law, cap 2000 | 4450-5450 | yes | 1 | 6.43 | 3055 | 1437 | 2.13 | acceptable, not preferred |
| wide, power law, cap 1000 | 4450-5450 | yes | 2 | 3.33 | 3017 | 1455 | 2.07 | ratio ok, but the wing saturates the 1000 km/s cap; rejected |
| **production, cap 2000** | **4450-5450** | **yes** | **2** | **2.87** | **3020** | **1491** | **2.03** | **adopted** |
| wide, no Fe II | 4450-5450 | no | 2 | 16.81 | 3932 | 1403 | 2.80 | **rejected** |
| wide, broken power law | 4450-5450 | yes | 2 | 2.90 | 3020 | 1491 | 2.03 | identical fluxes, 2 extra unconstrained parameters |
| 4250-5450 (includes Hγ) | 4250-5450 | yes | 2 | 4.61 | 3047 | 1367 | 2.23 | extra broad Hγ degeneracy; not adopted |
| 3 narrow components | 4450-5450 | yes | 3 | ~1.7 | 3240 | 1476 | 2.20 | overfits Hβ core with a +355 km/s Hβ-only component; rejected |
| ungrouped kinematics | 4450-5450 | yes | 2 | 3.05 | — | — | — | fit runs, but SHEAP `extract_basic_params_sampled` raises `TypeError ... missing 'distances'`; unusable |

Notes on the tested-but-rejected options:

* **Skewed/EMG profiles:** SHEAP 0.0.11's `ProfileConstraintMaker` supports
  only Gaussian, Lorentzian and top-hat SPAF sub-profiles; the skewed/EMG
  branches are not implemented (they raise `Unknown profile parameter`).  The
  asymmetric wing is therefore modelled with a second Gaussian.
* **`add_outflow=True`:** ties an outflow component to every narrow line and
  restricts its velocity; the wide-region variant gives χ²_ν = 7.1, worse than
  two free narrow components.
* **Broken power law:** the break is unconstrained in a 1000 Å window and sits
  at its initial 5500 Å; power law is the simpler model with identical fluxes.
* **Three narrow components:** the third component becomes a red-shifted
  Hβ-only Gaussian (+355 km/s) and raises the total Hβ by 7 %.  That is
  overfitting the Hβ core, not a physical component.

## 4. Adopted model and result

Rest-frame 4450-5450 Å (880 fitted pixels):

* one broad SPAF Gaussian: He I 4471, He II 4686, Hβ; tied kinematics, free
  amplitudes;
* two narrow SPAF Gaussians: [O III] 4959/5007 (ratio fixed at 0.3), He I,
  He II, Hβ per component; kinematics tied within each component;
* SHEAP Fe II UV/optical template (`logamp`, `logFWHM`, `vshift`);
* power-law continuum;
* Adam 4000 + 1000 steps at learning rate 0.01, `covariance_error=True`,
  50-draw parametric bootstrap, seed 42.

Best fit:

| quantity | value |
|---|---:|
| χ²_ν | **2.87** |
| fitted pixels / parameters | 880 / 22 |
| Hβ total | 3019.6 (1e-17) |
| Hβ broad / narrow | 2313.7 / 705.9 |
| [O III] 5007 | 1491.4 |
| [O III] 5007 / 4959 | 3.366 (tied) |
| Hβ/[O III] 5007 | **2.025** |
| broad Hβ FWHM / velocity | 3685 km/s / +38 km/s |
| narrow core FWHM / velocity | 900 km/s / −19 km/s |
| [O III] wing FWHM / velocity | 1606 km/s / −827 km/s |
| bound-saturated line parameters | none |

Comparison (rest-frame fluxes, 1e-17):

| quantity | SHEAP | PyQSOFit | GANDALF | S3Fit |
|---|---:|---:|---:|---:|
| Hβ total | 3019.6 | 2905 | 2951 ± 33 | 2761 ± 4 |
| [O III] 5007 | 1491.4 | 1480 | 1423 ± 12 | 1507 ± 9 |
| Hβ/[O III] 5007 | 2.025 | 1.96 | 2.07 ± 0.03 | 1.83 ± 0.01 |
| broad Hβ FWHM (km/s) | 3685 | 3550 | 2079 | 2934 |

SHEAP is within 4 % of the PyQSOFit/GANDALF/S3Fit median for Hβ and within
1 % for [O III] 5007.  The broad/narrow split matches PyQSOFit (2280 + 625)
and S3Fit (2091 + 670), not GANDALF's 50/50 split.

## 5. Robustness and systematics

The committed audit run (`--variants`) re-fits the same spectrum with five
alternative but defensible models.  Three variants pass every quality gate:
the single-narrow model (2.127), the 5250 Å red end (2.030) and the broken
power law (2.025).  Together with the production model, the passing range is
**2.025-2.127** (std 0.058, half-range 0.051), all inside the optical spread.  The 1000 km/s narrow-cap variant gives 2.074 but is rejected
because the wing sits on the cap; the no-Fe-II variant fails badly (2.80,
χ²_ν = 16.8), which is exactly the failure mode being guarded against.

The bootstrap errors on the integrated fluxes are ≈0.5-1 % (50 draws; Hβ
3019.6 ± 27.4, [O III] 5007 1491.4 ± 14.9, ratio 2.025 ± 0.027); the
model-systematic spread (±0.05 in the ratio) is about twice as large.  The line-core residuals (±10σ on a few
pixels) reflect the single-Gaussian-per-component limitation and the tied
narrow kinematics; they do not move the integrated fluxes outside the variant
range.

## 6. Remaining limitations

* SPAF is Gaussian-only in SHEAP 0.0.11; the [O III] blue wing is a second
  Gaussian, not a physically parametrised outflow profile.
* Narrow Hβ and [O III] share a FWHM and velocity within each component, so
  the Hβ and [O III] cores cannot be optimised independently.  This is the
  source of the remaining core residuals.
* Fe II is a single bundled template; host galaxy and Balmer continuum are
  disabled (the Balmer break is outside the window).
* The bootstrap is statistical only.  Use the variant spread for the model
  systematic.
* CPU JAX only; the runtime is dominated by the 50 bootstrap re-optimisations.

## 7. Production integration

* `run.json.quality` records every gate and `production_ok`.
* A failing fit still writes its diagnostic products but exits with status 2.
* `pipeline/compare_line_tools.py` skips any tool/source whose `run.json`
  has `quality.production_ok = false`, so a 4.0-style failure cannot enter
  `docs/line_tool_comparison.csv` or the ratio statistics.
* The old 4.00 value was removed from the tool documentation and replaced
  with the audited result.
* `configs/sheap_line/README.md` documents the model choices and the reason
  each rejected option was rejected.

## 8. Reproduction

```bash
bash Pipelines/build_images.sh sheap_line
bash Pipelines/run_sheap_line_docker.sh \
  inputs/04592649654_z_0.5874 \
  outputs/sheap_line/04592649654_z_0.5874 \
  --z 0.58741307 --variants
```

Runtime on the shared 8-core host: fit 106 s, 50 bootstrap draws 459 s,
five variants 340 s, total 926 s (15.4 min).  The committed run's exact
timing is in `run.json.runtime`.

## 9. Files changed by the audit

* `Tools/sheap_line/run_sheap.py` — corrected model, component-aware line
  table, region-restricted model CSV, new zoom/residual figures, quality
  gates, variant ensemble, corrected bootstrap labels.
* `Tools/sheap_line/README.md` — rewritten.
* `configs/sheap_line/default/config.json` — production model, limits,
  quality gates, variants.
* `configs/sheap_line/README.md` — new.
* `Pipelines/run_sheap_line_docker.sh` — `--variants` option.
* `pipeline/compare_line_tools.py` — honour `quality.production_ok`; keep
  wing/outflow components distinct from the total row (the old mapping made
  the reader use GalSpec's [O III] wing, 748, as the total, 1619).
* `docs/LINE_FITTING_TOOLS.md`, `docs/MCMC_AND_STATISTICS.md`,
  `docs/CAVEAT_FIXES.md`, `docs/OUTPUTS.md`, `configs/README.md` — updated.
* `outputs/sheap_line/04592649654_z_0.5874/` — regenerated.
