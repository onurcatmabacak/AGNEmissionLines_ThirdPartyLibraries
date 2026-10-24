# `configs/gandalf_line/default/`

* `emission_lines_setup` — GANDALF v1.5 rest-frame emission-line setup.  The
  columns are `i_line name lambda action l-kind A_i V_g/i sig_g/i fit-kind`.
  All lines start as `action=m` so the driver can test coverage; in-window
  lines are switched to `f`.  Multiplet satellites use `d#` and the published
  flux ratios.  Narrow H-beta is tied to [O III] 5007; narrow H-alpha is free;
  [N II] 6584 and [S II] 6716 are tied to H-alpha; broad H-beta and broad
  H-alpha are independent empirical BLR proxies.
* `config.json` — grid/template paths, `int_disp_kms=61.5`, `mdegree=3`,
  pPXF controls, fixed 300 km/s stellar fallback, mask widths, detection
  threshold and timeout.

## Production pPXF settings

The pPXF step follows GANDALF's own `gandalf_SDSS.pro` example:

| key | value | meaning |
|---|---:|---|
| `ppxf_degree` | 0 | additive polynomial degree |
| `ppxf_mdegree` | 3 | multiplicative polynomial degree |
| `ppxf_mask_sigma_kms` | 200 | emission-line mask half-width |
| `ppxf_sigma_min_kms` | 30 | lower sigma acceptance |
| `ppxf_sigma_max_kms` | 800 | upper sigma acceptance |
| `ppxf_v_max_kms` | 500 | \|V\| acceptance |
| `ppxf_chi2_max` | 3 | maximum chi2/dof |
| `ppxf_sigma_snr_min` | 3 | minimum sigma/sigma_err |
| `ppxf_min_templates` | 2 | minimum nonzero templates |

The earlier 8th-degree/2000 km/s-mask setup over-masked the low-z validation
galaxy and returned sigma=62.85 km/s instead of 79.87 km/s.  The production
values above give 3439 good pixels, 5 nonzero templates and chi2/dof=0.720 on
that galaxy.  For the z=0.587 eFEDS QSO the fit still fails (1 template,
chi2/dof=26.9), so the recorded 300 km/s fixed fallback is used.

## LSF and templates

`int_disp_kms=61.5` is the single Gaussian instrumental dispersion used by
GANDALF, taken from GANDALF's SDSS example and matched to the distributed
BC03/Tremonti04 templates.  It is appropriate for SDSS `spSpec`/COADD data at
R~2000 but is not a per-pixel LSF; real SDSS resolution varies with wavelength.
Intrinsic line sigmas below ~80 km/s are LSF-dominated.  `run.json` records
this assumption under `input_lsf`.

To adapt to a different instrument, change `int_disp_kms` and use matching
templates on a log10 grid with the same `dlog`; do not mix resolutions.  The
templates must already include the instrumental broadening (or be degraded to
it) because pPXF and GANDALF treat the adopted LSF as a Gaussian to subtract in
quadrature.

## Reproducibility

GANDALF's upstream MC flux-error loop leaves `SEED` undefined.  The local
`gandalf.pro` sets `seed=20250101L`, so repeated runs now give identical
formal flux errors; the fitted fluxes and model parameters are unchanged.
See `Tools/gandalf_line/THIRD_PARTY_LICENSES.md`.

## Production recipe and results

The shipped config is used by:

```bash
bash Pipelines/build_images.sh gandalf_line
.venv/bin/python pipeline/run_new_tools.py \
  --only spSpec-51908-0277-120_z_0.0859 --tools gandalf_line --force
```

On the 3805-pixel low-z galaxy this takes 59-71 s GDL / 68-82 s pipeline
wall, with residual chi2_nu=0.847.  The main line fluxes (1e-17 erg s^-1
cm^-2) are H-alpha 1390.85 +/- 16.86, H-beta 244.00 +/- 4.43, [O III] 5007
79.66 +/- 3.54, [N II] 6584 583.07 +/- 6.54, [S II] 6716 218.81 +/- 3.43
and [S II] 6730 164.11 +/- 2.57.  The QSO regression takes 30-34 s GDL and
keeps the recorded 300 km/s fixed fallback.

Caveats: the 61.5 km/s LSF is a single Gaussian; intrinsic sigmas below
~80 km/s are LSF-dominated.  pPXF sigma is configuration-sensitive at the
~20% level and its formal errors assume chi2/dof ~ 1.  GANDALF errors are
MPFIT covariance errors, not posteriors; broad lines are empirical Gaussians,
and multiplet satellites are derived from the `d#` ratios.
