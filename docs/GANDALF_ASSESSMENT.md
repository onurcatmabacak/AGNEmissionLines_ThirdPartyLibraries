# GANDALF v1.5 feasibility and implementation assessment

**Result: native GANDALF v1.5 is feasible and was delivered.**  The public IDL
source runs under **GNU Data Language (GDL) 1.0.4** in Ubuntu 24.04 without an
IDL licence.  The repository now has a Dockerised `gandalf_line` tool, runner,
configs and a real-source output.  A Python fallback was **not** shipped
because it would be a different method and native GANDALF works.

Primary run: `04592649654_z_0.5874` (SDSS/eFEDS QSO, z=0.587413).
Validation run: GANDALF's public SDSS example `spSpec-51908-0277-120.fit`
(z=0.0859), which covers H-alpha and [N II].

---

## 1. Feasibility test

### Environment

Ubuntu 24.04 packages, no IDL:

| package | version |
|---|---|
| `gnudatalanguage` | 1.0.4-1build6 |
| `gdl-astrolib` | 2022.09.12+dfsg-1 |
| `gdl-mpfit` | 1.85+2017.01.03-4 |
| GDL | "GDL - GNU Data Language, Version 1.0.4" |
| pPXF IDL | 2018-03-02 (IDL source from M. Cappellari) |
| BVLS | `bvls.pro` from M. Cappellari |

`gdl-astrolib` supplies `READFITS`, `MRDFITS`, `READCOL`, `PSF_GAUSSIAN`,
`CONVOL`, `ROBUST_SIGMA` and the other Astronomy Library routines GANDALF
needs.  `gdl-mpfit` supplies MPFIT.  `gdl-coyote` is not needed in the final
image.

### Tests that passed

1. **SAURON example (GANDALF release).**  `gandalf_SAURON_std.pro` with
   `FOR_ERRORS=1` ran to completion under GDL.  It produced the expected
   `[O III]`, H-beta and `[N I]` fits with MPFIT errors (e.g.
   `[O III] 13.60 +/- 0.16` in the first pass), and wrote `out_gdl_test.fits`.
   This exercises PPXF + GANDALF + BVLS + MPFIT + `ROBUST_SIGMA`.
2. **SDSS example (GANDALF release).**  `spSpec-51908-0277-120.fit` with the
   BC03/Tremonti04 templates ran through the new tool with PPXF stellar
   kinematics accepted (V=75.9 km/s, sigma=62.9 km/s, 7 templates,
   chi2=0.605) and a GANDALF gas fit with residual chi2_nu=0.852.
3. **Repository target.**  `04592649654_z_0.5874` ran natively and produced
   H-beta and `[O III] 5007` measurements; H-alpha/[N II] are outside the
   observed coverage (see results).

No Docker build or runtime failure remains in the delivered image.

### GDL/Docker compatibility errors encountered and fixed

These are the exact failure modes found while porting; all are handled in the
delivered code.

| symptom | cause | fix |
|---|---|---|
| `% Programs can't be compiled from single statement mode.` / `% Parser syntax error: unexpected end of file` | GDL batch mode does not expand IDL `@file` includes the way IDL does | compile each dependency with `.run /path/file.pro`; do not use `@` |
| `% Parser syntax error: unexpected token: MASK_EMISSION_LINES` at a function call | GDL tokenises `1.0d+z` without spaces badly | write `1.0d + z` (spaces around `+`) |
| `% CHECK2: Function not found: READFITS` | astrolib not on `!PATH` | `!PATH = '/usr/share/gnudatalanguage/astrolib:' + !PATH` |
| `ntemp 4323` then `% PPXF: STAR length cannot be smaller than GALAXY` | astrolib `MRDFITS`/`READFITS` return FITS 2-D images transposed (`38 x 4323` instead of `4323 x 38`) | `templates = transpose(mrdfits(...))` |
| `% GANDALF: Subscript out of range [s:e].` at `kinstars = sol[0:5]` | GANDALF expects a 6-element stellar kinematics vector; a 2- or 4-element vector is too short | always pass `[V, sigma, h3, h4, h5, h6]` (zeros for h3-h6) |
| `% GANDALF: Reddening & polynomial adjust. cannot be used together` | GANDALF v1.5 forbids `REDDENING` with `MDEGREE>0`, contrary to parts of the SDSS example | no reddening; `MDEGREE=3` |
| `% GANDALF: Subscript out of range [s:e].` with an orphan multiplet satellite | e.g. [N II] 6548 is inside the window but its main line [N II] 6584 is outside; GANDALF looks up a missing main-line index | drop satellites whose main line is not being fitted |
| nonphysical `[O I] 6300` flux (`~2e14`) | a very wide PPXF mask overlapped the array edge, so a line whose centre was outside stayed `action=m` and was later fitted | test the line centre against `min/max(goodpixels)` explicitly before masking |
| `% PPXF: STAR length ...` / no convergence | PPXF cannot constrain a QSO host continuum; see below | record PPXF result, reject it with explicit cuts, use a fixed stellar LOSVD |

The last item is scientific, not a GDL bug: PPXF often cannot measure stellar
absorption in an AGN-dominated QSO.  For the target, PPXF returned V=556.8
km/s, sigma=1000 km/s (its upper bound), 4 nonzero templates, chi2=2.184 on
871 good pixels.  The built-in acceptance cuts (`30 < sigma < 800` km/s,
`|V| < 500` km/s, at least 2 templates) reject it.  The stellar templates are
then convolved with a fixed 300 km/s LOSVD, and `run.json` records
`stellar_kinematics.source = fixed_fallback`.  The gas fit is still native
GANDALF; only the stellar broadening is fixed.  On the SDSS validation galaxy
PPXF is accepted (V=75.9, sigma=62.9 km/s).

### Licensing and runtime

* **GANDALF v1.5** (Sarzi et al. 2006): non-commercial use, copyright headers
  retained.  **pPXF IDL / BVLS** (Cappellari): non-commercial use, headers
  retained.  **BC03/Tremonti04 templates**: cite Bruzual & Charlot (2003) and
  Tremonti et al. (2004).  These are separate from the repository MIT licence;
  see `Tools/gandalf_line/THIRD_PARTY_LICENSES.md`.
* **No IDL licence is required.**  GDL is GPL software; the GANDALF/pPXF
  source keeps its own non-commercial terms.
* Image: Ubuntu 24.04 + GDL/astrolib/MPFIT + Python 3 (NumPy/Astropy/
  Matplotlib).  Cold build is dominated by apt (about 2-3 minutes); a cached
  rebuild is seconds.
* Runtime: primary target **33-39 s** in GDL / **36-49 s** wall (the spread
  includes Docker startup); SDSS validation **67 s** in GDL / **70 s** wall.
  The larger validation grid (3805 pixels, H-alpha included) is slower.

---

## 2. Native GANDALF/GDL vs pPXF-gas fallback

| | Native GANDALF v1.5 / GDL (delivered) | pPXF-gas fallback (not shipped) |
|---|---|---|
| engine | actual `gandalf.pro` under GDL 1.0.4 | Python `ppxf` gas fit |
| model | stellar templates convolved with a LOSVD **plus** Gaussian gas templates, solved simultaneously; BVLS linear amplitudes at each nonlinear step; MPFIT velocities/dispersions | pPXF's own gas-template implementation and penalty; no GANDALF `l-kind d#` multiplet/ratio machinery |
| kinematics ties | GANDALF `fit-kind` (`f/h/t#/v#/s#`) and multiplet `d#` ratios | manual pPXF gas components/ties, not identical |
| errors | `FOR_ERRORS=1` second nonlinear MPFIT pass; formal covariance | pPXF covariance / optional MC, different model |
| IDL licence | not required (GDL) | not required |
| output label | `gandalf_gdl` | would be `ppxf_gas_fallback` |
| fidelity | published GANDALF method | defensible full-spectrum gas fit, but not GANDALF |
| status | **delivered and run** | not shipped; unnecessary because native works |

A fallback would only be justified if GDL could not execute GANDALF.  It can,
so shipping a renamed Gaussian/pPXF fitter would be less faithful and would
misrepresent the method.  The native path is used and labelled
`method = gandalf_gdl`.

---

## 3. What is actually measured

`gandalf_lines.csv` reports, for each fitted Gaussian component:

* rest-frame integrated line flux in `1e-17 erg s^-1 cm^-2` (and cgs),
* Gaussian peak amplitude,
* velocity relative to systemic (km/s),
* intrinsic Gaussian sigma (km/s; the 61.5 km/s SDSS instrumental dispersion
  is subtracted by GANDALF), observed sigma, and S/N,
* formal 1-sigma errors from the MPFIT covariance.

For lines whose kinematics are tied, GANDALF does not propagate a formal flux
error through the velocity/sigma covariances.  The tool then scales the MPFIT
amplitude error to a flux error (`method = amplitude_error_scaled`) and says so
in the `notes` column.  Free lines use `mpfit_covariance`.

The narrow H-beta is tied to `[O III] 5007`; the broad H-beta is an independent
Gaussian and an **empirical BLR proxy**, not a physical broad-line profile.
`Hbeta total` is narrow + broad with errors added in quadrature.  No aperture
correction, no reddening correction and no Fe II/Balmer-continuum model are
included.  GANDALF has no MCMC; the uncertainty figure is the MPFIT covariance,
not a posterior.

---

## 4. Results

### Primary target `04592649654_z_0.5874`

Rest-frame coverage 3400-6200 A, log10 grid with `dlog=1e-4`, 2610 pixels,
velocity scale 69.03 km/s/pixel, 38 BC03/Tremonti04 templates.  PPXF rejected;
stellar LOSVD fixed at 300 km/s.  Residual chi2_nu = 14.17 (the high value is
dominated by AGN Fe II and the non-Gaussian broad H-beta/[O III] profiles, not
by the line cores).

| line | component | flux (1e-17) | error | sigma (km/s) | sigma error | V (km/s) | S/N | status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| H-beta | narrow (tied to [O III]) | 1486.44 | 11.26 | 650.68 | tied | -70.92 | 132.0 | ok |
| H-beta | broad | 1464.38 | 29.26 | 2079.04 | 27.14 | 932.53 | 50.0 | ok |
| H-beta | total | 2950.82 | 31.36 | - | - | - | 94.1 | ok |
| [O III] 5007 | narrow | 1422.74 | 13.14 | 650.68 | 3.25 | -70.83 | 108.3 | ok |
| H-alpha | narrow | - | - | - | - | - | - | **not covered** |
| [N II] 6584 | narrow | - | - | - | - | - | - | **not covered** |

Other detected lines in the output: `[O II] 3729` 264.47 +/- 4.53,
`[Ne III] 3869` 204.95 +/- 6.85, `[Ne III] 3967` 26.10 +/- 13.15 (weak,
S/N=2.0).  GANDALF propagates free-line flux errors with 100 random draws, so
the formal flux errors jitter slightly (a few per cent) between identical
reruns; the line centres and Gaussian parameters are deterministic.  H-alpha (6563 A) and [N II] (6584 A) are redward of the observed
SDSS limit (10400 A at z=0.587): H-alpha would be at 10418 A, just outside.
They are reported as `not_covered`, not as non-detections.  The fit truncates
at 6200 A rest to avoid the blue wing of the out-of-range H-alpha line.

**Caveat on the target:** the broad H-beta and the [O III] doublet are not
single Gaussians; the residual chi2 and the fit figure show profile mismatch.
The integrated Gaussian fluxes are the GANDALF model measurements, with formal
errors, but they are not aperture fluxes and the broad component is not a
physical BLR profile.

### Validation `spSpec-51908-0277-120.fit` (z=0.0859)

This run uses PPXF stellar kinematics (V=75.9, sigma=62.9 km/s, 7 templates,
chi2=0.605), rest coverage 3523-8458 A, 3805 pixels, residual chi2_nu=0.852,
runtime 66.8 s GDL / 70.1 s wall.

| line | component | flux (1e-17) | error | sigma (km/s) | sigma error | S/N | status |
|---|---|---:|---:|---:|---:|---:|---|
| H-beta | total | 244.37 | 4.43 | 89.82 | tied | 55.1 | ok |
| [O III] 5007 | narrow | 79.68 | 3.48 | 89.82 | 1.96 | 22.9 | ok |
| H-alpha | narrow | 1396.20 | 17.02 | 81.26 | 0.65 | 82.0 | ok |
| [N II] 6584 | narrow (tied to H-alpha) | 582.80 | 6.45 | 81.26 | tied | 90.4 | ok |

The validation demonstrates that the same native tool measures H-alpha and
[N II] when they are in range.  Its fit figure and table are in
`docs/gandalf_sdss_example/`.

---

## 5. Reproduce

```bash
bash Pipelines/build_images.sh gandalf_line
.venv/bin/python pipeline/run_new_tools.py \
  --only 04592649654_z_0.5874 --tools gandalf_line --force
```

Direct:

```bash
bash Pipelines/run_gandalf_line_docker.sh \
  work/prepared/04592649654_z_0.5874/pyqsofit \
  outputs/04592649654_z_0.5874/gandalf_line \
  04592649654_z_0.5874
```

Outputs: `outputs/04592649654_z_0.5874/gandalf_line/` and the validation
artifacts in `docs/gandalf_sdss_example/`.

---

## 6. Remaining limitations

1. GDL is not IDL.  The tested numerical path (PPXF, GANDALF, BVLS, MPFIT,
   astrolib) works, but arbitrary IDL features (widgets, `@` includes, some
   graphics) do not; the batch driver avoids them.
2. GANDALF v1.5 is non-commercial software; the repository MIT licence does
   not relicense it.  `THIRD_PARTY_LICENSES.md` records the terms.
3. No MCMC.  Errors are formal MPFIT covariance errors and assume the model
   and noise are correct.  The broad H-beta and non-Gaussian [O III] profile
   make the target's formal errors optimistic.
4. H-alpha/[N II] are not covered for the z=0.587 target; only the validation
   spectrum demonstrates them.
5. The stellar kinematics of the target are fixed (300 km/s) because PPXF
   cannot constrain the QSO host.  This is recorded in `run.json`; it affects
   the stellar continuum shape, not the GANDALF gas-template machinery.
6. GANDALF v1.5 cannot combine `REDDENING` with `MDEGREE>0`; no reddening
   correction is applied.  A future variant could set `MDEGREE=0` and fit
   reddening, at the cost of continuum flexibility.
