# GANDALF v1.5 production assessment

**Result: native GANDALF v1.5 under GNU Data Language (GDL) is working and is
now demonstrated on a real low-z SDSS galaxy with H-alpha and H-beta measured,
not only on the z=0.587 eFEDS QSO.**  The production validation object is the
public GANDALF v1.5 `SDSS_example` spectrum
`spSpec-51908-0277-120.fit` (z=0.0858772).  It is stored as the canonical input
`inputs/spSpec-51908-0277-120_z_0.0859/` and the run is in
`outputs/spSpec-51908-0277-120_z_0.0859/gandalf_line/`.

For that galaxy **pPXF is scientifically usable** as the stellar-kinematics
prior: V = 72.54 +/- 6.50 km/s, sigma = 79.87 +/- 9.80 km/s, chi2/dof = 0.720,
5 nonzero templates, 3439 good pixels.  The result is not at a bound.  The
absolute sigma still carries template/LSF systematics of order 20% (see
section 5), but the gas fit is not driven by a fake stellar width.

For the z=0.587 eFEDS QSO `04592649654` **pPXF remains unusable**: the
production fit is rejected with V = -190.25 km/s, sigma = 365.81 km/s,
only 1 nonzero template and chi2/dof = 26.919.  The fixed 300 km/s stellar
LOSVD fallback is retained and is recorded in `run.json`; no stellar sigma is
faked.

Primary/canonical run: `spSpec-51908-0277-120_z_0.0859` (SDSS legacy spSpec,
z=0.0858772).
Regression run: `04592649654_z_0.5874` (SDSS DR18 eFEDS QSO, z=0.587413).

---

## 1. Environment and audit of the previous state

Ubuntu 24.04 / Docker, no IDL licence:

| package | version |
|---|---|
| `gnudatalanguage` | 1.0.4-1build6 |
| `gdl-astrolib` | 2022.09.12+dfsg-1 |
| `gdl-mpfit` | 1.85+2017.01.03-4 |
| GDL | "GDL - GNU Data Language, Version 1.0.4" |
| pPXF IDL | 2018-03-02 (M. Cappellari) |
| BVLS | `bvls.pro` (M. Cappellari) |

The existing run of `04592649654` did complete natively.  H-beta and
[O III] 5007 were measured, H-alpha/[N II] were correctly marked `not_covered`,
`FOR_ERRORS=1` produced an MPFIT covariance error block, and the fit/PNG/PDF,
FITS, CSV, model table and `run.json` products were present.  The audit found
these real failures or quality problems:

1. **pPXF rejection was not diagnosable.**  The driver wrote a generic
   "sigma/velocity/template-count outside acceptance range" message.  It did
   not request pPXF formal errors and did not check chi2/dof or the
   significance of sigma.  The old pPXF configuration (8th-degree additive
   polynomial, 2000 km/s emission mask) drove the QSO fit to the hard
   sigma=1000 km/s bound; that bound was the only reason reported.
2. **The pPXF configuration was not the canonical GANDALF one.**  GANDALF's
   own `gandalf_SDSS.pro` uses `degree=0`, `mdegree=3` and a 200 km/s emission
   mask for pPXF.  The old 8/2000 setup over-masked the low-z galaxy
   (1713 good pixels instead of 3439) and returned sigma=62.85 km/s instead of
   the canonical 79.87 km/s.  This is a real config error for the low-z
   validation: the two settings differ by 27% in sigma.
3. **Tied-line kinematic errors were written as zero.**  H-beta, [O II],
   [Ne III], [O I], [N II] and [S II] are tied to a parent line by GANDALF,
   which sets the tied parameter errors to zero.  A zero is not a
   measurement; the parent's formal error must be inherited.
4. **Multiplet satellites were missing from the standard table.**  GANDALF
   fixes [O II] 3726, [O III] 4959, [N II] 6548 and [S II] 6730 through the
   `d#` ratios, but only the main `l` lines were written to
   `gandalf_lines.csv` and to the line-yield summary.
5. **Classic SDSS `spSpec` could not pass through the repository pipeline.**
   `pipeline/prepare_inputs.py` only read FLUX/LOGLAM or FLUX/WL table HDUs.
   GANDALF itself already read the 4 x npix `spSpec` primary image, but
   `pipeline/run_new_tools.py` could not prepare the canonical input for it.
6. **GANDALF's formal flux errors were not reproducible.**  The upstream code
   calls `randomn(seed,100)` with `SEED` undefined, so GDL seeds from the
   system clock.  Repeated identical runs changed the H-alpha flux error by
   ~20% (14.7 to 17.5 in 1e-17 units) while the fluxes stayed fixed.
7. **The residual chi2 denominator was approximate and changed when derived
   rows were added.**  It counted output rows rather than GANDALF's free
   parameters, so adding satellites changed chi2_nu without changing the fit.
8. **The documentation contained stale, mutually inconsistent values**
   (for example the H-beta broad error and total error did not match the
   committed CSV).

The LSF is not a code failure but is a real limitation: `int_disp_kms=61.5`
is a single Gaussian value inherited from GANDALF's official SDSS example.
It is appropriate for the BC03/Tremonti04 templates distributed with GANDALF,
but the real SDSS LSF varies with wavelength and is not Gaussian.  This is now
recorded explicitly in `run.json` (`input_lsf`).

---

## 2. GDL compatibility fixes retained

The delivered driver already contains the port fixes found earlier; they were
re-verified in this audit:

| symptom | cause | fix |
|---|---|---|
| `% Programs can't be compiled from single statement mode.` | GDL batch mode does not expand IDL `@file` includes | compile each dependency with `.run /path/file.pro` |
| `% Parser syntax error: unexpected token: MASK_EMISSION_LINES` | GDL tokenises `1.0d+z` badly | spaces around `+` |
| `% CHECK2: Function not found: READFITS` | astrolib not on `!PATH` | prepend `/usr/share/gnudatalanguage/astrolib` |
| `ntemp 4323` then `% PPXF: STAR length cannot be smaller than GALAXY` | astrolib `MRDFITS` returns 2-D FITS images transposed | `templates = transpose(mrdfits(...))` |
| `% GANDALF: Subscript out of range [s:e].` at `kinstars = sol[0:5]` | GANDALF needs a 6-element stellar kinematics vector | pass `[V, sigma, h3..h6]` |
| `% GANDALF: Reddening & polynomial adjust. cannot be used together` | v1.5 forbids `REDDENING` with `MDEGREE>0` | no reddening; `MDEGREE=3` |
| orphan multiplet satellite causes a missing main-line index | e.g. [N II] 6548 inside the window while 6584 is outside | drop satellites whose parent is not fitted |
| nonphysical [O I] 6300 flux | wide mask overlapped the array edge | test the line centre against `min/max(goodpixels)` explicitly |

No GDL parser or runtime failure remains in the delivered image.

---

## 3. Changes made in this audit

| file | change |
|---|---|
| `pipeline/prepare_inputs.py` | added a classic SDSS `spSpec` reader (primary 4 x npix image; row 0 flux, row 2 noise, log10 wavelength grid); preserves zero-noise pixels as an explicit bad-pixel mask in the prepared PyQSOFit layout |
| `Tools/gandalf_line/gdl/run_gandalf.pro` | request pPXF `ERROR=`; record V/sigma errors and chi2/dof; acceptance now checks sigma bounds, |V|, template count, chi2/dof and sigma/sigma_err; exact rejection message; canonical pPXF defaults (`degree=0`, 200 km/s mask); seed for reproducible GANDALF MC flux errors |
| `Tools/gandalf_line/run_gandalf.py` | plumb pPXF acceptance controls; add `input_lsf`, pPXF errors and acceptance cuts to `run.json`; inherit kinematic errors for tied lines; add `d#` satellites as clearly labelled derived rows; add `line_yield_summary.txt`; count only GANDALF main lines in the chi2 dof; expand line yield; improve limitations text |
| `configs/gandalf_line/default/config.json` | production pPXF settings `degree=0`, `mask_sigma=200 km/s`; new `ppxf_chi2_max=3`, `ppxf_sigma_snr_min=3`, `ppxf_min_templates=2` |
| `Tools/gandalf_line/third_party/gandalf_v1.5/gandalf.pro` | fixed `seed=20250101L` before the 100-draw MC flux-error loop; model and fluxes unchanged, errors reproducible |
| `inputs/spSpec-51908-0277-120_z_0.0859/` | new canonical low-z input with provenance (`source.json`, `README.md`, unmodified raw file) |
| `inputs/README.md` | registry row and provenance note for the new source |
| `Tools/gandalf_line/README.md`, `configs/gandalf_line/README.md` | production recipe, runtime, pPXF status, line results, caveats |
| `Tools/gandalf_line/THIRD_PARTY_LICENSES.md` | documents the local GANDALF seed modification |

The canonical input policy is unchanged: the raw `spSpec` file is the only
committed copy; the PyQSOFit `spectrum.fits` staging is generated under
`work/prepared/<key>/` at run time.

---

## 4. Low-z production object

### Provenance

The file is the public GANDALF v1.5 SDSS example
`SDSS_example/spSpec-51908-0277-120.fit` (MD5
`db9336122ecaa4787f7b2d677d3f8376`, 167040 bytes).  The FITS header verifies:

* SDSS legacy `spSpec`: `VERSION=v3_23_2`, `VERS_1D=v5_9_4`.
* Plate 277, MJD 51908, fiber 120; `DATE-OBS=2000-12-30`; 12 exposures of
  2700 s; `QUALITY=excellent`; `OBJTYPE=GALAXY`.
* RA = 166.01292 deg, Dec = -0.15715033 deg; z = 0.0858772 +/- 0.0000415;
  `Z_CONF=0.947`; `NGOOD=3805`.
* H-alpha 6563 A, [N II] 6584 A and [S II] 6716/6730 A fall at observed
  7126/7149/7293/7309 A, inside the observed 3824-9185 A range.

The raw file is copied without modification.  `pipeline/prepare_inputs.py`
converts it to the PyQSOFit `spectrum.fits` layout for the pipeline; the
pixel values, wavelengths and 1-sigma errors are unchanged, and the 13
zero-noise pixels remain zero-error (the GANDALF reader drops them).

### Fit setup and runtime

Rest-frame coverage 3522.7-8458.2 A, 3805-good-pixel input, log10 grid with
`dlog=1e-4` (3805 pixels, 69.03 km/s/pixel), 38 BC03/Tremonti04 templates.
Native GANDALF v1.5 with `FOR_ERRORS=1`, `MDEGREE=3`, `DEGREE=0`.

| quantity | value |
|---|---:|
| GDL wall time | 70.6 s |
| container total (prepare + GDL + products) | 76.5 s |
| pipeline wall time (Docker included) | 81.7 s |
| residual chi2_nu | 0.847 |

Wall time varies with host load: repeated runs of the same production command
took 59-71 s GDL and 68-82 s pipeline wall.  The committed run above is the
final reproducibility check; the earlier 66-86 s figures included a cold
Docker cache and the old pPXF setup.

---

## 5. pPXF stellar-kinematics assessment

Production pPXF setup (IDL pPXF 2018 under GDL), following GANDALF's own SDSS
example:

```text
degree=0, mdegree=3, moments=2
emission mask sigma = 200 km/s
start = [systemic offset, 300 km/s]
accept: 30 < sigma < 800 km/s, |V| < 500 km/s, nz >= 2,
        chi2/dof <= 3, sigma/sigma_err >= 3
```

### Low-z galaxy: accepted and scientifically usable

| quantity | value |
|---|---:|
| good pPXF pixels | 3439 |
| V | 72.54 +/- 6.50 km/s |
| sigma | 79.87 +/- 9.80 km/s |
| sigma / sigma_err | 8.15 |
| chi2/dof | 0.720 |
| nonzero templates | 5 |

**Verdict: usable.**  The solution is not at a bound, five templates
contribute, the formal sigma error is 12%, and chi2/dof is 0.72.  The stellar
V=72.5 km/s lies between the H-beta/[O III] gas velocity (68.3 km/s) and the
H-alpha/[N II]/[S II] velocity (84.0 km/s); the stellar sigma=79.9 km/s is
comparable to the gas sigma (82-90 km/s).  These are physically sensible for a
low-z star-forming galaxy.

The pPXF formal errors assume chi2/dof ~ 1; the low-z value of 0.720 is close
enough, while the QSO value of 26.919 makes its formal errors meaningless and
is one reason the fit is rejected.  The low-z caveat is systematic, not
formal: the older over-flexible pPXF setup (`degree=8`, 2000 km/s mask) gave
sigma=62.85 km/s on the same spectrum.  The difference, about 27%, is a
template/mask/polynomial systematic.  A
conservative reading is therefore sigma = 80 +/- 10 (formal) +/- 15
(systematic) km/s.  The gas fit uses the production value, 79.87 km/s; it
does not use a fixed fallback.

### `04592649654` QSO: rejected, fixed fallback retained

Under the production setup pPXF returns:

| quantity | value |
|---|---:|
| good pPXF pixels | 2360 |
| V | -190.25 +/- 11.05 km/s |
| sigma | 365.81 +/- 11.06 km/s |
| nonzero templates | 1 |
| chi2/dof | 26.919 |
| status | **rejected** |

The exact `run.json` message is:

```text
rejected: nz<min chi2/dof>max (V=-190.248 km/s, sigma=365.811 km/s,
sigma_err=11.059 km/s, nz=1, chi2/dof=26.919)
```

It fails the template-count and chi2 cuts.  Under the previous
`degree=8`/2000 km/s mask configuration, pPXF instead hit its hard sigma bound:
V=556.8 km/s, sigma=1000 km/s, 4 nonzero templates, chi2/dof=2.184.  Both
outcomes are consistent with an AGN-dominated continuum with no measurable
host absorption.  GANDALF therefore convolves the templates with a fixed
300 km/s LOSVD.  The choice is encoded in `run.json` as
`stellar_kinematics.source = fixed_fallback`; the gas fit remains native
GANDALF, and no stellar sigma is fabricated.

**Bottom line: pPXF is scientifically usable for the low-z galaxy and is not
usable for the QSO.  The fallback is scientifically honest but is not a
measurement of the QSO host sigma.**

---

## 6. Line results

Fluxes are integrated Gaussian fluxes in `1e-17 erg s^-1 cm^-2`.  `sigma` is
the intrinsic Gaussian width after subtracting the 61.5 km/s instrumental
LSF in quadrature; it is not an observed width.  Errors are GANDALF
`FOR_ERRORS=1` MPFIT covariance errors, with the fixed seed making the
free-line flux errors reproducible.

### `spSpec-51908-0277-120_z_0.0859` (z=0.0858772)

| line | component | flux | error | sigma (km/s) | sigma error | S/N | status |
|---|---|---:|---:|---:|---:|---:|---|
| H-beta | narrow (tied to [O III]) | 244.00 | 4.43 | 89.99 | 1.97 | 55.1 | ok |
| H-beta | broad | 0.00 | 0.00 | 1000.0 | - | 0.0 | not detected |
| H-beta | total = narrow + broad | 244.00 | 4.43 | - | - | 55.1 | ok |
| [O III] 4959 | narrow (derived, 0.35 x 5007) | 27.88 | 1.24 | 89.99 | 1.97 | 22.5 | ok |
| [O III] 5007 | narrow | 79.66 | 3.54 | 89.99 | 1.97 | 22.5 | ok |
| H-alpha | narrow | 1390.85 | 16.86 | 81.90 | 0.66 | 82.5 | ok |
| H-alpha | broad | 42.79 | 18.63 | 689.9 | 192.9 | 2.3 | weak |
| [N II] 6548 | narrow (derived, 0.34 x 6584) | 198.24 | 2.22 | 81.90 | 0.66 | 89.2 | ok |
| [N II] 6584 | narrow (tied to H-alpha) | 583.07 | 6.54 | 81.90 | 0.66 | 89.2 | ok |
| [S II] 6716 | narrow (tied to H-alpha) | 218.81 | 3.43 | 81.90 | 0.66 | 63.8 | ok |
| [S II] 6730 | narrow (derived, 0.75 x 6716) | 164.11 | 2.57 | 81.90 | 0.66 | 63.8 | ok |

Other detected lines in the table: [O II] 3729 133.67 +/- 3.96 (the 3726
satellite is 102.93 +/- 3.05), [Ne III] 3869 13.43 +/- 3.69,
[Ne III] 3967 0.12 +/- 2.85 (weak), [O I] 6300 25.09 +/- 2.58.

The strong-line ratios are H-alpha/H-beta = 5.70, [N II] 6584/H-alpha =
0.419, [O III] 5007/H-beta = 0.327.  The galaxy is star-forming; the broad
H-alpha component is only 2.3 sigma and the broad H-beta is undetected.  The
broad components are retained as empirical BLR proxies, but they are not
physically required by this galaxy.

The exact uncertainty jitter in earlier runs is gone: two independent runs
with the fixed seed produced identical flux errors.

### `04592649654_z_0.5874` regression (z=0.587413)

| line | component | flux | error | sigma (km/s) | sigma error | S/N | status |
|---|---|---:|---:|---:|---:|---:|---|
| H-beta | narrow (tied to [O III]) | 1486.44 | 11.26 | 650.68 | 3.25 | 132.0 | ok |
| H-beta | broad | 1464.38 | 31.63 | 2079.04 | 27.14 | 46.3 | ok |
| H-beta | total | 2950.82 | 33.57 | - | - | 87.9 | ok |
| [O III] 4959 | narrow (derived, 0.35 x 5007) | 497.96 | 4.81 | 650.68 | 3.25 | 103.6 | ok |
| [O III] 5007 | narrow | 1422.74 | 13.74 | 650.68 | 3.25 | 103.6 | ok |
| H-alpha | narrow | - | - | - | - | - | **not covered** |
| [N II] 6584 | narrow | - | - | - | - | - | **not covered** |

The gas fluxes are unchanged from the pre-audit run (H-beta total
2950.82227, [O III] 5007 1422.7398) because the fixed 300 km/s fallback is
unchanged.  The formal errors now differ only through the fixed GANDALF seed.
The cross-tool snapshots in `docs/line_tool_comparison.csv` and
`docs/line_ratio_comparison.csv` predate that seed fix: their QSO GANDALF
fluxes and ratios are unchanged, but the GANDALF formal errors and S/N in
those files are the old stochastic draw.  They were not regenerated here
because that comparison suite also covers unrelated tools.
Other measured lines: [O II] 3729 264.47 +/- 4.53 (3726 satellite 203.64
+/- 3.49), [Ne III] 3869 204.95 +/- 6.85, [Ne III] 3967 26.10 +/- 13.15
(weak), [O III] 4959 as above.  H-alpha (6563 A) and [N II] (6584 A) are
redward of the observed SDSS limit: at z=0.587 H-alpha would be at 10418 A,
just outside 10400 A.  The fit is truncated at 6200 A rest to avoid the blue
wing of the out-of-range H-alpha line.  These rows are `not_covered`, not
non-detections.

The residual chi2_nu is 14.13.  The high value is dominated by AGN Fe II and
the non-Gaussian broad H-beta/[O III] profiles, not by the line cores; it is
not evidence of a GDL failure.  Runtime for this regression is 29.9 s GDL /
34.7 s container total / 38.6 s pipeline wall.

### Line-yield summary

Every run writes `line_yield_summary.txt` next to `gandalf_lines.csv`, with
one row per line/component, flux, error, intrinsic sigma, S/N, status, method
and notes.  `run.json["line_yield"]` carries the same values for H-beta,
[O III] 4959/5007, H-alpha, [N II] 6548/6584 and [S II] 6716/6730.
Multiplet satellites are marked `gandalf_gdl_multiplet_ratio`; they are
derived from the GANDALF `d#` ratio and are not independent measurements.

---

## 7. Outputs and provenance files

`outputs/<key>/gandalf_line/` now contains:

| file | contents |
|---|---|
| `gandalf_lines.csv` | standardised table with all measured and derived lines |
| `line_yield_summary.txt` | human-readable line-yield table |
| `gandalf_fit.png/pdf` | observed, total, stellar continuum, gas emission, zoom, residual |
| `gandalf_uncertainty.png/pdf` | formal flux/sigma errors and S/N |
| `gandalf_fit.fits` | galaxy, best fit, emission, residual, good pixels, weights, stellar kinematics, gas solution, errors, templates |
| `gandalf_input.fits` | exact rest-frame grid, mask and templates passed to GDL |
| `gandalf_model.csv` | wave, flux, model, stellar, emission, residual, error |
| `gandalf_lines_raw.csv` | raw GANDALF main-line solution |
| `gandalf_meta.txt`, `gandalf_run.log`, `gandalf_batch.gdl` | provenance |
| `run.json` | method, grid, input LSF, pPXF block with errors and acceptance cuts, stellar kinematics, measurements, line yield, chi2, runtime, limitations |

`run.json` now records the LSF assumption, pPXF failure reason verbatim, pPXF
formal errors, and all acceptance thresholds.  It is the authoritative
machine-readable summary.

---

## 8. Reproduce

```bash
bash Pipelines/build_images.sh gandalf_line

# Low-z production object (H-alpha and H-beta covered)
.venv/bin/python pipeline/run_new_tools.py \
  --only spSpec-51908-0277-120_z_0.0859 --tools gandalf_line --force

# QSO regression
.venv/bin/python pipeline/run_new_tools.py \
  --only 04592649654_z_0.5874 --tools gandalf_line --force
```

Direct run (the prepared input is generated by the pipeline, not committed):

```bash
bash Pipelines/run_gandalf_line_docker.sh \
  work/prepared/spSpec-51908-0277-120_z_0.0859/pyqsofit \
  outputs/spSpec-51908-0277-120_z_0.0859/gandalf_line \
  spSpec-51908-0277-120_z_0.0859
```

---

## 9. Caveats and remaining limitations

1. **GDL is not IDL.**  The tested numerical path (pPXF, GANDALF, BVLS,
   MPFIT, astrolib) works.  Widgets, `@` includes and some graphics are not
   supported; the batch driver avoids them.
2. **GANDALF v1.5 is non-commercial software.**  The repository MIT licence
   does not relicense it; see `Tools/gandalf_line/THIRD_PARTY_LICENSES.md`.
3. **Errors are formal MPFIT covariance errors, not MCMC posteriors.**  They
   assume the model and noise are correct.  The fixed seed makes the
   stochastic flux-error propagation reproducible but does not make the
   errors Bayesian.
4. **The LSF is a single 61.5 km/s Gaussian.**  Real SDSS resolution varies
   with wavelength and is not Gaussian.  Intrinsic sigma values below
   ~80 km/s are LSF-dominated; the H-alpha width of 81.9 km/s is at that
   boundary.  This is the dominant systematic for the low-z gas widths.
5. **pPXF sigma is configuration-sensitive.**  The production value is
   79.87 km/s; the old 8/2000 configuration gave 62.85 km/s.  The gas fit is
   stable at the few-per-cent level against that change, but the absolute
   stellar sigma should be quoted with a ~20% systematic.
6. **Broad H-beta and broad H-alpha are empirical Gaussians**, not a physical
   BLR profile.  On the low-z galaxy broad H-beta is undetected and broad
   H-alpha is only 2.3 sigma; they should not be interpreted as BLR
   measurements.
7. **No reddening correction.**  GANDALF v1.5 refuses `REDDENING` together
   with `MDEGREE>0`; no E(B-V) is fitted or applied.
8. **Line fluxes are integrated Gaussian fluxes.**  There is no aperture
   correction.  Satellite fluxes are derived from the GANDALF `d#` ratio.
9. **The QSO's stellar kinematics are fixed at 300 km/s.**  This is recorded
   in `run.json` and must be quoted with any use of the QSO gas fit.  It
   affects the stellar continuum shape, not the native GANDALF gas machinery.
10. **H-alpha/[N II] are not covered for `04592649654`.**  They are reported
    as `not_covered`, not as non-detections.  The low-z object is the
    production demonstration of those lines.
