# QSOFITMORE `default` configuration

This directory is the reviewable, executable configuration for the
`qsofitmore_line` Docker tool.  `config.json` records every fit switch;
`line_table.csv` is the editable emission-line table consumed by
`qsofitmore.QSOFitNew.Fit(line_list_path=...)`.  The container copies both
files to `/app/config` and writes the resolved copy to
`outputs/<source>/qsofitmore_line/config.effective.json`.

## Line table

The table is the upstream `qsofitmore/examples/output/qsopar_log.csv` at the
pinned commit (`4c5f6e497b306aaf50b502a8e4b27ed9dfe89421`), with two
scientifically necessary adaptations:

1. the [O III] 4959/5007 core and outflow doublets are tied to a 0.33 flux
   ratio (`findex=1`/`2`, `fvalue=0.33`/`1.00`), because an untied doublet
   collapses 4959 to an unphysical ratio;
2. narrow C III] and C IV rows are retained for UV spectra.

`inisig`/`minsig`/`maxsig` are ln(λ) widths (the package's default log axis);
`narrow_max_kms=1200` caps every non-`br` component.  `vindex`/`windex` group
centres/widths; `findex`/`fvalue` group amplitudes.  Hβ narrow and [O III]
share group 1; the [O III] outflow wings share group 2.

Hα, C III], C IV and He II 1640 are **outside** the rest-frame coverage of the
04592649654 SDSS spectrum (2247–6510 Å).  qsofitmore's complex selection skips
them automatically; the compact table reports them as `not_covered` rather
than as zero-flux measurements.  Keeping them in the table preserves the
tool's UV/higher-z capability without polluting this fit.

## Switch-by-switch

| switch | value | why |
|---|---|---|
| `deredden` | `true` | Apply Galactic foreground extinction. |
| `dust_map` | `sfd` | SFD98 (Schlegel, Finkbeiner & Davis 1998); image bakes and MD5-verifies the map. |
| `dust_law` | F99, `R_V=3.1` | qsofitmore's `f99law`; the measured E(B-V) is recorded. |
| `decomposition_host` | `false` | Yip+2004 host PCA would restrict the grid to ≳3450 Å and remove Mg II; pPXF handles the host separately. |
| `include_iron` | `true` | Enable the Fe II pseudo-continuum. |
| `iron_temp_name` | `V09` | Verner et al. (2009) Fe II over 2000–10000 Å. |
| `Fe_verner09` | `true` | Package compatibility flag so `Fe_line_prop` integrates V09 for the saved Fe II bands; qsofitmore warns it is redundant with `iron_temp_name`, but the flag remains part of the effective config. |
| `poly` | `false` | The broken power law already supplies large-scale curvature; an extra polynomial is not identifiable. |
| `broken_pl` | `true` | Two-slope power law; the 4661 Å break is inside coverage, so the optical profile (3000 Å pivot) is selected. |
| `BC` | `true` | Dietrich et al. (2002) Balmer continuum + Storey & Hummer (1995) high-order Balmer (n_upper=6–50). |
| `rej_abs` | `false` | SDSS masks/calibrated errors already remove bad pixels; enabling it did not change the Hβ/Mg II totals in pre-run checks. |
| `nsmooth` | `1` | No extra smoothing. |
| `wave_range` | `[2247, 6510.4]` Å rest | Clean COADD coverage after dropping zero-IVAR pixels; the red edge is just below Hα/N II 6549 so a prepared PyQSOFit copy cannot pull in the Hα complex. |
| `Fe_flux_range` | `[[2250,2700],[4434,4684],[5100,5600]]` | UV and optical Fe II pseudo-continuum bands. |
| `tie_lambda` | `true` | Tie centres within a kinematics group. |
| `tie_width` | `true` | Tie widths within a kinematics group. |
| `tie_flux_1` | `true` | [O III] 4959 core = 0.33 × 5007. |
| `tie_flux_2` | `true` | [O III] 4959 outflow = 0.33 × 5007 outflow. |
| `narrow_max_kms` | `1200` | Package hard cap on Gaussian sigma for non-broad components (not FWHM); none of this object's narrow components is at the cap. |
| `pl_pivot_A` | `3000` | Power-law pivot. |
| `log10_electron_density` | `9` | Storey & Hummer Balmer grid. |
| `MC` | `true` | Native lmfit Monte Carlo. |
| `n_trails` | `200` | 200 realizations per complex and for the continuum; 200× the package default. |
| `seed` | `20250101` | Reproducible random draws. |
| `mcmc` | `false` | qsofitmore 1.2.2 has no emcee/MCMC sampler; not claimed. |

## Notes and caveats

* The package's `<complex>_whole_br_area` column applies a 1200 km/s
  classifier and is **not** the total for a multi-Gaussian broad template.
  The compact table sums all components; the package columns remain in
  `qsofitmore_result.csv` and `qsofitmore_components.csv`.
* Hβ narrow is tied to the [O III] core width; it is not an independent
  narrow-line width.  The total Hβ is the robust quantity.
* The 1200 km/s cap is on Gaussian sigma, not FWHM.  The Mg II narrow
  component has sigma≈510 km/s (FWHM≈1200 km/s), so it is not at the cap; the
  `at_bound` column is retained for objects that do hit it.
* Hδ and [Ne III] were tested in pre-run variants and left out: the
  V09+Balmer-continuum model over-subtracts/does not constrain Hδ (zero flux,
  χ²_r≈21), and [Ne III] is not detected.  This is a model limitation, not a
  non-detection claim.
* The continuum is foreground-dereddened only; no intrinsic reddening is
  fitted.  The broken power law absorbs some intrinsic curvature.
* The host is not decomposed here; use `ppxf_host`.

See `Tools/qsofitmore_line/README.md` for build/run commands and the full
method, and `outputs/04592649654_z_0.5874/qsofitmore_line/README.md` for the
run-specific provenance note.
