# `sheap_line` configuration

`configs/sheap_line/default/config.json` is mounted at `/app/config/config.json`
by `Pipelines/run_sheap_line_docker.sh`.  It controls the SHEAP 0.0.11 JAX fit
of the rest-frame Hβ/[O III] 4959,5007 region.

The 2026-08 audit replaced the original 4600-5150 Å / single-narrow / no-Fe II
configuration.  That model could not describe the `04592649654` spectrum
(χ²_ν = 46, Hβ/[O III] 5007 = 4.00); see `docs/SHEAP_ASSESSMENT.md`.  Do not
revert to it as a production setting.

## Fields

| key | meaning |
|---|---|
| `region_rest` | rest-frame fit window in Å. Production: **4450-5450**, wide enough to anchor the power-law continuum and the Fe II template. |
| `n_broad` | number of broad SPAF components. One broad component covers Hβ + He II 4686 (and He I 4471 when in range). |
| `n_narrow` | number of narrow SPAF components. **2**: an NLR core and a blueshifted [O III] wing. One component is not enough for this object (χ²_ν 6.4); three components overfit the Hβ core with a non-physical +355 km/s Hβ-only component. |
| `fe_mode` | `"template"` adds SHEAP's Fe II UV/optical template. **Required**: `"None"` raises χ²_ν from 2.9 to 16.8 and pushes the ratio to 2.80. |
| `continuum_profile` | `"powerlaw"`. The 4450-5450 Å window does not justify a broken power law; `brokenpowerlaw` gives the same fluxes (χ²_ν 2.87) with two extra, unconstrained parameters. |
| `add_balmer_continuum` | false. The Balmer continuum/break is at 3646 Å, outside this window. |
| `add_balmerhighorder_continuum` | false; 3646-3910 Å, outside. |
| `add_outflow` | false. Tested: SHEAP's outflow branch ties the wing to every narrow line and restricts its velocity; the two-narrow-component model fits better (χ²_ν 7.1 vs 2.9). |
| `num_steps` | Adam step list. `[4000, 1000]` at a constant learning rate of 0.01 is converged: 6000 steps changes the fluxes by <0.1%. |
| `learning_rate` | `[0.01, 0.01]`. Lowering the final rate to 0.005 stops at a worse local solution. |
| `method` | `"adam"`. |
| `profile` | `"gaussian"`, the SPAF sub-profile. SHEAP 0.0.11's `ProfileConstraintMaker` does not build constraints for the skewed/EMG SPAF sub-profiles, so asymmetric wings are modelled with the second Gaussian. |
| `covariance_error` | true. Computes SHEAP's local JAX Jacobian/JTJ covariance. |
| `montecarlo_samples` | number of parametric-bootstrap draws. The committed run uses 50. |
| `seed` | bootstrap seed. |
| `limits_overrides` | widen SHEAP's hard priors so they are not active. The defaults cap narrow FWHM at 600 km/s, while the observed [O III] lines are ~950 km/s wide; the uncorrected fit sat at 592 km/s. Production uses narrow FWHM ≤ 2000 km/s and |v| ≤ 2000 km/s, broad |v| ≤ 3000 km/s. The adopted fit lands at 900/1606 km/s and -827 km/s, away from every bound. |
| `variants` | model-systematics ensemble used only with `--variants`: a 1000 km/s narrow cap, one narrow component, no Fe II, a 5250 Å red end, and a broken power law. |

`quality_gates` (top level, not inside `sheap`) controls the production gate:

| gate | threshold | why |
|---|---|---|
| `max_chi2_red` | 8 | catches the original χ²_ν = 46 model failure; the adopted fit is 2.9 |
| `ratio_min/max` | 1.8 / 2.5 | the optical Hβ/[O III] 5007 spread of the sibling fitters |
| `max_broad_hbeta_fwhm_kms` | 7000 | the failing baseline reached 8019 km/s |
| `max_reference_deviation` | 0.30 | Hβ and [O III] 5007 must agree with the sibling median to 30 % |
| `min_reference_tools` | 2 | only apply the reference gate when at least two sibling tables exist |
| `oiii_doublet_min/max` | 2.5 / 3.8 | sanity check on the tied [O III] 4959/5007 ratio |

If any gate fails, `run.json` records `quality.production_ok = false`, the tool
exits with status 2, and `pipeline/compare_line_tools.py` skips the result.
The diagnostic tables/figures are still written.

## Running

```bash
# pipeline path (quality gates only, no variants)
.venv/bin/python pipeline/run_new_tools.py \
  --only 04592649654_z_0.5874 --tools sheap_line --force

# full audit run with the model-systematics ensemble
bash Pipelines/run_sheap_line_docker.sh \
  inputs/04592649654_z_0.5874 outputs/sheap_line/04592649654_z_0.5874 \
  --z 0.58741307 --variants
```

A copy of this config is baked into the image at `/app/config/config.json`.
The runner mounts the repository directory over it, so edits take effect
without rebuilding the image.  Only `Tools/sheap_line/run_sheap.py` is copied
into the image; rebuild after editing it:

```bash
bash Pipelines/build_images.sh sheap_line
```
