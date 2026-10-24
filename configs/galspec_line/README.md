# `configs/galspec_line/`

Two complete configurations are shipped:

| directory | model | status |
|---|---|---|
| `default/` | full-continuum global model, 2280-6460 A rest | production recipe |
| `reduced/` | legacy 4720-5150 A H-beta/[O III] window | reproducibility only; not the production run |

`default/config.json` selects the full model with `"model_mode": "full"`.
`reduced/config.json` has no `model_mode`, so the adapter uses the original
reduced-window path.

## Full-continuum model (`default/`)

```text
normalised polynomial continuum, degree 4, x0=4350 A, xscale=1200 A
+ park2022 Fe II template (GalSpec IronTemplate_new, rest 4000-5600 A)
+ H-beta narrow + broad
+ broad H-gamma and H-delta (broad Balmer sigma/dv tied to H-beta broad)
+ H-epsilon narrow, H8-H12 narrow (H8-H12 tied to H-epsilon by Case-B ratios)
+ [O II] 3726/3729 narrow
+ [Ne III] 3869/3967 narrow
+ [Ne V] 3426 narrow
+ [S II] 4068/4076 narrow
+ [O III] 4363 narrow
+ He II 4686 narrow
+ [O III] 5007 narrow/core + broad wing
+ [O III] 4959 narrow + wing (tied to 5007 by 2.98)
+ broad Mg II 2796 + 2804 (doublet ratio 1.0, kinematics tied)
+ [O I] 6300 + 6363 (6363 tied to 6300 by 3.05)
+ [S III] 6312 narrow
```

The model is fitted to the whole usable rest-frame spectrum, not to a local
window.  The polynomial continuum and Fe II are global; every line is part of
the same likelihood.  There are 39 free parameters.

### Kinematic groups

| group | reference component | free sigma/dv | typical bounds |
|---|---|---|---|
| `narrow` | `Hbeta_narrow` | yes | sigma 120-900 km/s, dv +/-700 km/s |
| `oiii` | `OIII_5007_narrow` | yes | sigma 120-900 km/s, dv -1000 to +500 km/s |
| `oiii_wing` | `OIII_5007_wing` | yes | sigma 400-4000 km/s, dv -2000 to +1000 km/s |
| `broad_balmer` | `Hbeta_broad` | yes | sigma 700-3500 km/s, dv +/-2000 km/s |
| `mgii` | `MgII_2796_broad` | yes | sigma 500-3000 km/s, dv +/-2000 km/s |

All other narrow lines share the `narrow` reference; [O III] 4363 and 4959
share the `oiii` reference; 4959 wing shares the `oiii_wing` reference; broad
H-gamma/H-delta share `Hbeta_broad`; Mg II 2804 shares `MgII_2796_broad`.
Amplitudes are free (with the documented Case-B or doublet ties).  This keeps
the global model identifiable at SDSS resolution.

### Continuum and Fe II

`continuum.polynomial_degree = 4`, evaluated in the normalised variable
`(wave - 4350)/1200`.  The continuum must be positive over the fitted range;
this is enforced as a prior in the emcee log-probability.  Fe II is GalSpec's
`park2022` empirical template; its redshift parameter is fixed at zero and
only amplitude, velocity width and velocity shift are sampled.

### Lines outside the coverage

H-alpha 6563, [N II] 6548/6583 and [S II] 6716/6731 are outside the SDSS
rest-frame coverage of the z=0.5874 target.  They are emitted in
`galspec_lines.csv` with `status=not_covered`, `method=none`, and NaN fluxes.
They are not silently omitted.

### Sampler

| setting | value |
|---|---:|
| sampler | `galspec.MCMC_Fit` / emcee `EnsembleSampler` |
| walkers | 80 (auto-raised to `2*ndim+2`; ndim=39) |
| steps | 4000 |
| burn-in | 1200 |
| seed | 42 |
| initial jitter | 2 per cent of each parameter's prior span |
| saved posterior | up to 40000 post-burn samples, thinned to fit the cap |
| derived posterior | 4000 evenly spaced post-burn samples |
| autocorrelation | `emcee` integrated time with `tol=0`, fallback `tol=1`/`5` |

The LSQ start is a trust-region fit in three stages: (1) polynomial + Fe II to
line-free pixels, (2) full model with continuum/Fe II fixed to solve the lines,
then (3) joint full-model refinement.  After the joint stage the continuum and
Fe II values are restored to the line-free solution, so a broad line cannot
absorb the global continuum; the joint stage is used to refine the line
parameters.  The LSQ solution is only a starting point; the reported line
fluxes are posterior medians.

### Errors

`errors.floor_frac_of_continuum = 0.02` adds 2 per cent of the fitted global
continuum in quadrature to the calibrated SDSS error, with a 1e-6 absolute
minimum.  Both raw and floored chi-square values are recorded.

### Adapting

For another instrument, update `instrument` and the line list/profile windows.
For a spectrum that covers H-alpha, add the line to `lines` and remove it from
`coverage_lines`.  Do not change `input.vacuum_to_air` without changing the
line wavelengths: GalSpec's optical dictionary and the line list are in air
wavelengths.  The full model is intended for rest coverage that includes at
least [O II] 3727, H-beta and [O III] 5007; below that, use a line-region
configuration and document the reduced coverage.
