# `pyqsofitspec_line` — PyQSOFitSpec bootstrapped emission-line fitting (Docker)

Dockerised **PyQSOFitSpec** (<https://github.com/yongsukyee/PyQSOFitSpec>,
commit `aa326ed0b13003b22588a0ad9c8a369d9a2de6dd`, 2026-03-31) applied to the
repository's SDSS QSO spectra.  PyQSOFitSpec extends PyQSOFit v1.1 /
PyQSOFit_SBL with alternative line models (`fit_linemodel.py`: Gaussian and
skew-normal) and a **parametric bootstrap refit** of the whole
continuum+line model (`main.py`).

The fit itself is not reimplemented here: continuum fitting (UV/optical Fe II,
Balmer continuum, power law, polynomial), the `kmpfit` line fit and the
skew-normal profile evaluation all run inside the vendored package.  This
tool adds a config-driven line table, the optical H-beta / [O III] complex,
per-component flux extraction, convergence/validity auditing and the compact
products.

## Build / run

```bash
bash pipeline/runners/build_images.sh pyqsofitspec_line      # build the image
bash pipeline/runners/run_pyqsofitspec_line_docker.sh \
  inputs/04592649654_z_0.5874/raw \
  outputs/pyqsofitspec_line/04592649654_z_0.5874 \
  --name 04592649654
```

or through the matrix orchestrator (uses the prepared PyQSOFit spectrum
`work/prepared/<source_key>/pyqsofit/spectrum.fits`):

```bash
.venv/bin/python pipeline/run_new_tools.py --only 04592649654_z_0.5874 \
  --tools pyqsofitspec_line --force
# shorter/bootstrap-tunable:
.venv/bin/python pipeline/run_new_tools.py --only 04592649654_z_0.5874 \
  --tools pyqsofitspec_line --pyqsofitspec-nboot 5 --force
```

Runner options: `--config DIR|FILE` (default
`configs/pyqsofitspec_line/default`), `--nboot N`, `--seed N`, `--z Z`,
`--name NAME`, `--flux-unit auto|cgs|1e-17`.

The production default in `configs/pyqsofitspec_line/default/config.json` is
`nboot_fit = 50`; `--nboot 5` is a smoke test.  With the production
tolerances (`kmpfit_xtol=1e-6`), a 55-draw run on `04592649654` takes
**~10.5 min** on one CPU (measured: see the committed-run table below); the
earlier pass with the library-default `xtol` took 58 min because of failed
retries.  The driver prints a per-realisation wall time, and `run.json`
records every iteration, so a run can be stopped and audited if a documented
time cap is reached.

## Inputs

* `inputs/<source>_z_<z>/raw/spec-*.fits` — SDSS DR18 `COADD` table
  (`FLUX` in `1e-17 erg s-1 cm-2 A-1`, vacuum `LOGLAM`, `IVAR`, `WDISP`,
  redshift in `SPALL`/`ZALL`).  This is exactly the input upstream `main.py`
  expects.
* or the prepared PyQSOFit layout written by `pipeline/prepare_inputs.py`:
  flux in HDU0, wavelength in HDU1, 1-sigma error in HDU2, **absolute cgs**
  flux, redshift in the `Z` header keyword.

Both are converted to the unit PyQSOFit/PyQSOFitSpec works in,
`1e-17 erg s-1 cm-2 A-1` (the unit on the package's plot axes and in its
`qsopar2.fits` line table).  Pixels with non-finite values, `IVAR <= 0`, or
outside `obs_wave_range` are dropped; `error_floor_frac` optionally adds
`sqrt(err^2 + (f*flux)^2)`.

The two input routes were cross-checked on this object (two bootstrap
realisations each): line fluxes agree to < 0.3 %, the difference coming from
the pipeline's `IVAR <= 0` sanitising.

## Model and line table

`configs/pyqsofitspec_line/default/config.json` replaces the hard-coded
`newdata` array of upstream `main.py` with a JSON `line_table` that is written
to `qsopar2.fits` at run time (same 10 columns:
`lambda, compname, minwav, maxwav, linename, ngauss, sigval, voff, iniskw,
fvalue`; the driver-only `kind` field is not written to FITS).

Default components (rest-frame vacuum wavelengths):

| complex | window [A] | components |
|---|---|---|
| MgII | 2700-2900 | `MgII_br` (free skew-normal, `sigval [0.004, 0.05]`), `MgII_na` (width **fixed** at the NLR anchor) |
| Hb | 4640-5100 | `Hb_br` (free skew-normal, `[0.004, 0.012]`, skew `[-5, 5]`), `Hb_na` (tied to `OIII5007c`), `OIII4959c` (tied to `OIII5007c`: width/velocity, flux ratio 0.33), `OIII5007c` (width **fixed** at the NLR anchor), `OIII4959w` (tied to `OIII5007w`: width/velocity, flux ratio 0.33), `OIII5007w` (free wing, `[0.003, 0.008]`, skew `[-5, 5]`) |

`linemodel` is `skewnorm_model` by default; `gauss_model` is available in
`fit_linemodel.py`.  The `kind` field declares a component broad or narrow for
the output tables; `QSOFit.line_prop` still uses its own
`log10(sigma) > 0.0017` (sigma > 512 km/s) cut internally to select profile
blocks, so a narrow component whose fitted width crosses that cut is reported
with `width_class = broad` but keeps `component = narrow` (the declared
physical kind).

### Fixed NLR width (the old pinning fix)

The previous configuration used `sigval [3.3e-4, 1.2e-3]` for `Hb_na` and
`OIII5007c`; the fits sat on the 1.2e-3 upper bound (FWHM 848 km/s) in every
realisation.  That is not a measurement: it is the prior boundary.  The
production configuration removes the free NLR width altogether and anchors it
to an independent measurement of the clean [O III] 5007 line in the same
spectrum:

* single Gaussian + linear local continuum over 4973-5043 A (rest frame):
  `FWHM = 998 +/- 38 km/s`, `sigma = 7.08 A`;
* adopted anchor `ln sigma = 0.0014` (`FWHM = 989 km/s`);
* applied to `MgII_na` and `OIII5007c`, and through the ties to `Hb_na` and
  `OIII4959c`.

This is the same physical choice as GANDALF and S3Fit (a common NLR
kinematic component), and it leaves no free narrow width to pin.  The free
widths (`MgII_br`, `Hb_br`, `OIII5007w`) are interior in the median of the
53-valid production run; 2/53 realisations put the [O III] wing at its lower
0.003 bound, while `MgII_br` and `Hb_br` never touch a width bound.  The anchor uncertainty (+/-38 km/s) is a systematic, not a
bootstrap error: changing the anchor from 0.0013 to 0.0015 changes the narrow
H-beta flux by about +/-10 %, while the H-beta total changes by < 2 %.

## The bootstrap (this is not a single least-squares fit)

The uncertainty is generated exactly as in upstream `main.py`:

```python
np.random.seed(seed)
for nb in range(nboot_fit):
    flux_noise = [np.random.normal(f, fe) for f, fe in zip(flux, err)]
    q = QSOFit(lam, flux_noise, err, z, path=...)
    q.Fit(..., MC=False, n_trials=0, linemodel=linemodel, linefit=True)
    props = line_prop(...)          # every component, every realisation
value = mean(props); error = std(props)   # upstream value_meanstd()
```

Each realisation re-fits the continuum and all line complexes from scratch;
the reported value is the bootstrap mean, the error the bootstrap standard
deviation (upstream convention), plus 16/84 percentiles.  PyQSOFitSpec's own
internal Monte Carlo (`MC=True`, `n_trials`) is deliberately **off** inside
each fit, otherwise the two error estimates would be mixed.  Production uses
`nboot_fit=50`; the uncertainty of the uncertainty is
`1/sqrt(2*(nboot-1)) ~ 10 %`.

## Audit findings and fixes (2026-10 production pass)

1. **kmpfit iteration cap (real solver failure).**  PyQSOFitSpec constructs
   its line `kmpfit.Fitter` without `maxiter`, so kapteyn's default 200
   applies.  The 8-component H-beta / [O III] complex reached status 5
   ("Maximum number of iterations reached") in every realisation; the
   returned parameters were a truncated iterate, not the minimum.
   The driver now wraps the Fitter constructor and sets
   `kmpfit_maxiter` (default 1500) plus `kmpfit_ftol=1e-8`,
   `kmpfit_xtol=1e-6`.  The default kmpfit `xtol` is too strict for this
   32-parameter complex: in the first 50-realisation pass, 3/50 fits cycled to
   status 5 at the 1500-iteration cap, and a retry with `maxiter=6000` still
   failed after 10-14 min.  The same noise draws converge in 7-11 s
   (status 2, rchi2 10-10.8) with `xtol=1e-6`, which is a parameter accuracy
   of ~0.3 km/s in the line centres, far below the measurement error.  The
   looser tolerances are now the production default; a realisation that still
   fails is retried once with a 4x cap, and a permanently failed realisation
   is excluded from the bootstrap statistics and reported in `run.json`.
2. **Pinned narrow widths (prior artefact).**  Fixed by the NLR anchor
   described above.  `width_mode`/`pinned_at_bound`/`note` in
   `pyqsofitspec_lines.csv` make the status auditable.
3. **Latent multi-Gaussian extraction bug.**  The old driver read only
   `<line>_1_*` from `gauss_result`; for `ngauss > 1` it would have reported
   only the first Gaussian's flux.  `component_parameters()` now concatenates
   all blocks and evaluates the summed profile with `line_prop`.  The
   production table uses `ngauss=1`, so this is a robustness fix, not a
   change to the committed numbers.
4. **Broken/truncated fits were trusted.**  A kmpfit status alone is not
   enough: during development a 2-Gaussian H-beta variant returned
   status 2 with a reduced chi2 of ~3000, and the 50-realisation production
   pass found converged local minima at rchi2 ~ 20 (Mg II collapsed) and
   ~ 227 (all lines collapsed).  `fit_validity()` now requires convergence of
   **every** fitted complex and a finite per-complex reduced chi2 below
   `max_line_red_chi2` (default 15, normal fits are 8.8-10.8).  Invalid
   realisations are excluded and counted (`nboot_valid`, `bootstrap.invalid`).
   The committed run requested 55 draws so that at least 50 remain after this
   cut.
5. **`run.json` was silent about convergence.**  It now records, for every
   realisation, the kmpfit status/message/niter/nfev/maxiter, the per-complex
   fit quality and the validity flag, plus a top-level `bootstrap` block and
   the `nlr_width_anchor`.
6. **H-beta total offset.**  See the dedicated section below.  It is a
   model/continuum-definition difference, not a units or summation bug.

## Outputs

`outputs/<source_key>/pyqsofitspec_line/`:

| file | content |
|---|---|
| `pyqsofitspec_lines.csv` | compact table: line, declared component (broad/narrow), fitted `width_class`, `width_mode` (free/fixed/tied), complex, rest wavelength, flux, flux error, p16/p84, flux in cgs, FWHM and error, sigma, skewness, EW, peak, S/N, `stable`, `note`, `pinned_at_bound`, fitted ln(sigma) min/max, nboot |
| `pyqsofitspec_totals.csv` | the totals used for the cross-tool comparison (`MgII`, `Hbeta`, `Hbeta_broad`, `Hbeta_narrow`, `OIII5007`, `OIII5007core`) |
| `pyqsofitspec_out.csv` | native-style one-row-per-spectrum table (`<line>_<prop>_<br|na>` and `_err`, mean/std over the valid bootstrap), i.e. the upstream `pyqsofitspec_out.csv` schema extended with the line area |
| `pyqsofitspec_bootstrap.csv` | every realisation (including invalid ones, flagged `valid=false`): scale, ln(center), ln(sigma), ln(sigma) min/max, width class/mode, skew, FWHM, sigma, EW, peak, area |
| `spec-<name>_fit.pdf` / `.png` | the package's own fit figure (continuum decomposition + each complex, realisation 0) |
| `pyqsofitspec_model.csv` | realisation-0 decomposition: rest wavelength, noisy flux, error, continuum, line model, total model (1e-17 cgs); used to audit the H-beta continuum offset |
| `pyqsofitspec_bootstrap.png/.pdf` | bootstrap histograms of the total fluxes |
| `pyqsofitspec_corner.png/.pdf` | corner plot of the H-beta / [O III] 5007 / Mg II totals (scatter mode for `nboot < 20`) |
| `run.json` | method, versions, input, per-iteration wall times, convergence diagnostics, fluxes, fit status/reduced chi2, line table, `nlr_width_anchor`, line definitions, caveats |
| `config.effective.json` | resolved configuration incl. input, z, coverage, seed, nboot, kmpfit_maxiter |
| `run.log` | driver log |
| `cross_tool_comparison.csv/.json` | added by `compare_outputs.py` (see below) |

S/N is `flux / bootstrap_std`.  `stable=false` marks a component whose 16-84 %
interval is wider than 25 % of the mean (a multimodal or unconstrained
component).

Cross-tool table (now includes PyQSOFit, GANDALF, S3Fit, GalSpec and QGfit):

```bash
python3 Tools/pyqsofitspec_line/compare_outputs.py outputs/<source_key>
```

It reads the sibling outputs and writes `cross_tool_comparison.csv` /
`.json` next to the PyQSOFitSpec products.  Per tool the closest available
equivalent is used and recorded in the `definition` column; the tools do not
decompose the blends identically (for example QGfit has no [O III] wing, and
GalSpec does not fit Mg II).

## Committed production run: `04592649654` (z = 0.5874)

```bash
bash pipeline/runners/run_pyqsofitspec_line_docker.sh \
  inputs/04592649654_z_0.5874/raw \
  outputs/pyqsofitspec_line/04592649654_z_0.5874 --name 04592649654 --nboot 55
```

`configs/pyqsofitspec_line/default` (`skewnorm_model`, `seed=20250101`,
`kmpfit_maxiter=1500`, `kmpfit_ftol=1e-8`, `kmpfit_xtol=1e-6`,
`max_line_red_chi2=15`, fixed NLR anchor `ln sigma=0.0014`).  The committed
command requests **55** draws (`--nboot 55`) to guarantee >= 50 valid
realisations after the validity cut; the config default is 50.
Rest-frame coverage 2394-5794 A, 3840 pixels used, 808 masked (observed frame
3800-9200 A).

| quantity | value |
|---|---:|
| image size | 1.2 GB |
| bootstrap requested / valid | 55 / 53 (2 invalid: rchi2 19.9 and 226.7) |
| wall time, driver (55 fits) | 632.7 s (10.5 min) |
| per-realisation wall time | 7.4-17.9 s (median 11.4 s) |
| Mg II 2798 total | 2029.9 +/- 49.6 |
| H-beta total (Hb_br+Hb_na) | **3525.1 +/- 33.8** |
| H-beta broad (Hb_br) | 2720.4 +/- 25.3 |
| H-beta narrow (Hb_na) | 804.7 +/- 26.0 |
| [O III] 5007 total | 1638.9 +/- 22.2 |
| [O III] 5007 core | 761.6 +/- 196.4 (bimodal) |
| H-beta/[O III] 5007 | 2.151 |
| Mg II broad FWHM | 3622 km/s (free, interior) |
| H-beta broad FWHM | 4124 km/s (free, interior) |
| H-beta narrow FWHM | 968 km/s (tied to the fixed [O III] core) |
| [O III] core / wing FWHM | 986 / 1893 km/s (core fixed, wing free) |

Fluxes are in `1e-17 erg s-1 cm-2` (rest frame); errors are the bootstrap
standard deviation over the 53 valid realisations.  The full model integral
over 4640-4940 A is 3614 (`pyqsofitspec_model.csv`), 2.5 % above the
component-summed total (the `line_prop` +/-3 sigma truncation).

FWHM status (the audit criterion): the free widths (`MgII_br`, `Hb_br`,
`OIII5007w`) are interior in the median; 2/53 realisations put the [O III]
wing at its lower 0.003 bound, and the wing's median is 0.00496.  `MgII_na`
and `OIII5007c` are **fixed** at the NLR anchor (989 km/s), and `Hb_na` /
`OIII4959c` are **tied** to it; their `width_mode` is `fixed`/`tied` and
`pinned_at_bound=false`, because their widths are not fitted parameters.
No main-line FWHM is left at an arbitrary prior bound.

## The H-beta total and the 18 % offset

The reported total is exactly

```
Hbeta = Hb_br + Hb_na
```

where `Hb_br` is the single free skew-normal broad component and `Hb_na` is
the narrow Gaussian tied to the fixed [O III] 5007 width.  `OIII5007` is
`OIII5007c + OIII5007w`; `MgII` is `MgII_br + MgII_na`.

`line_prop` integrates each component over +/-3 sigma in ln(lambda), so a
strongly skewed profile loses a small fraction of its analytic tail.  The
component-summed H-beta total is therefore ~2.5 % below the full model
integral over 4640-4940 A (`pyqsofitspec_model.csv`): 3525 vs 3614 in the
production run.  This is the upstream PyQSOFitSpec definition; the sibling
tools use their own window/area conventions.

The earlier 3439 total (10 realisations, unconverged H-beta complex) was
~18 % above GANDALF (2951) and ~25 % above S3Fit (2761).  The production
total, 3525, is ~19.5 % above GANDALF, ~28 % above S3Fit, ~21 % above
PyQSOFit (2905), ~21 % above QGfit (2915) and only ~9 % above GalSpec
(3237).  The H-beta/[O III] ratio is 2.15, close to GANDALF (2.07) and
GalSpec (2.00), so the absolute offset affects both lines similarly and is
consistent with a continuum/absolute-scale difference rather than a
line-flux error.
This is **not** a summation or unit error.  It is driven by the continuum:

* with the PyQSOFitSpec continuum, the data-minus-continuum integral over
  4640-4940 A is ~4100 (1e-17 erg/s/cm2);
* with the PyQSOFit continuum (same data) it is ~2990;
* the PyQSOFitSpec continuum is lower by ~4-5 units (10-12 %) at 4700-4900 A,
  and the H-beta model absorbs that difference.

This can be recomputed from `pyqsofitspec_model.csv`:

```python
import numpy as np
d = np.genfromtxt("outputs/<source>/pyqsofitspec_line/pyqsofitspec_model.csv",
                  delimiter=",", names=True)
m = (d["wave"] > 4640) & (d["wave"] < 4940)
print(np.trapz(d["line"][m], d["wave"][m]))          # model line flux
print(np.trapz((d["flux"] - d["conti"])[m], d["wave"][m]))  # data - continuum
```

The two codes use different Fe II templates/continuum implementations
(PyQSOFitSpec's Vestergaard & Wilkes optical template vs PyQSOFit's own
templates) and different line profiles (one skew-normal vs two Gaussians).
PyQSOFitSpec's optical table also has **no separate He II 4687 component**, so
He II 4687 is absorbed by `Hb_br`; PyQSOFit fits `HeII4687_br`/`_na`
explicitly.  This is another model-definition difference, not a summation
bug.  The model totals therefore sit between the two continuum
definitions.  The offset is a **model/continuum-definition difference**, and
for line-ratio work the internal ratios (e.g. H-beta/[O III]) are more robust
than the absolute flux.

## Compatibility work (no change to the method)

Upstream pins `numpy==1.25.2, scipy==1.11.2, astropy==5.3.3,
matplotlib==3.7.3, PyAstronomy==0.19.0` and requires Python >= 3.11; those
exact versions are used (Python 3.11), so **`PyQSOFitSpec.py` and
`fit_linemodel.py` are vendored unmodified**.  Three build-environment issues
had to be solved:

1. **`kapteyn` (kmpfit)**.  Upstream says
   `pip install https://www.astro.rug.nl/software/kapteyn/kapteyn-3.4.tar.gz`.
   That tarball does not build as-is here: `setup.py` imports `numpy` at
   metadata time (needs `--no-build-isolation` with numpy pre-installed plus
   `Cython==3.0.11`), and its `wcs`/`ascarray`/`profiles` extensions use a
   private copy of the NumPy C API (`src/c_numpy.pxd`, `void
   import_array()`) that no longer compiles against numpy 1.25.
   `patches/patch_kapteyn.py` restricts the build to the `kmpfit` extension,
   the only submodule PyQSOFitSpec imports (`kapteyn/__init__.py` does not
   import the others).  The tarball is SHA256-pinned in the Dockerfile.
   kapteyn 2.3.1 from PyPI is older and does not build either.
2. **`sfdmap`**.  Upstream lists the unmaintained `sfdmap==0.1.1`, which does
   not install on modern Python.  `sfdmap2` (the maintained fork, already used
   by `pyqsofit_uv`) provides the API; `sfdmap_shim/sfdmap.py` re-exports it
   under the legacy module name.  Galactic dereddening is off, so no SFD data
   are downloaded.
3. **`import sfdmap` / `import fit_linemodel`** are plain module imports: the
   package directory is on `PYTHONPATH` (`/app/pyqsofitspec`) as in upstream
   `main.py`.

No numpy/scipy/astropy API patch was needed inside the package itself; the
pinned versions are recent enough for the code as published.  The only
runtime intervention is the kmpfit `maxiter` wrapper described above, which
does not change the model or the minimiser, only its iteration cap.

## Caveats

* **The [O III] core/wing split is still bimodal.**  The total 5007 flux is
  stable, but individual realisations split it differently between the narrow
  core and the broad wing (the two components overlap in velocity and width).
  `OIII5007c` is therefore flagged `stable=false` in some runs; use
  `OIII5007 = OIII5007c + OIII5007w` for line-ratio work, not the core alone.
* **The NLR width is fixed, not fitted.**  It is anchored to the [O III] 5007
  measurement (`FWHM 998 +/- 38 km/s` -> adopted 989 km/s).  The narrow-line
  fluxes are conditional on that anchor; a +/-40 km/s change moves the narrow
  H-beta flux by ~10 % and the total by < 2 %.
* **Reduced chi2 is 8-11**, not ~1.  The SDSS `IVAR` is a formal per-pixel
  error and does not include flux-calibration/template systematics; the Fe II
  pseudo-continuum is also imperfect under H-beta.  The bootstrap inherits
  those formal errors, which is why the statistical error bars are small
  compared with the inter-tool spread.
* **Skew-normal degeneracy.**  The skewness parameter is free over
  `[-5, 5]` for the broad components (`[-1000, 1000]` is the upstream
  default).  The fit often sits near the -5 bound (a mildly one-sided
  profile); a skewed profile trades peak against wing flux, so broad FWHM and
  broad flux are correlated.  The corner plot shows this.  The bound is a
  shape prior, not a width prior.
* **Mg II is a blended doublet** (2796/2804) plus UV Fe II; the model fits one
  skewed profile plus a weak narrow component whose width is fixed to the NLR
  anchor.  The Mg II broad/narrow split is therefore model-dependent (the
  fixed 989 km/s narrow component carries 367 of the 2030 total); use the
  Mg II **total**, not the split, for line-ratio work.  Mg II fluxes are
  comparable in definition only to tools that also treat the blend as one
  line (S3Fit sums 2796+2804).
* **H-beta/[O III] only** for this object: at z = 0.587 the rest-frame
  coverage is 2394-5794 A, so H-alpha/[N II]/[S II] are not observable and
  C III]/C IV are not in the list (they were dropped from upstream `main.py`'s
  UV set to keep the run short); add them to `line_table` for higher-z
  targets.
* The fit figure is realisation 0 of the bootstrap (upstream behaviour); the
  numbers in the tables are means over all valid realisations.

## Provenance / licence

`third_party/PyQSOFitSpec/` is a verbatim copy of the upstream files needed
for a run (`PyQSOFitSpec.py`, `fit_linemodel.py`, `main.py`, `fe_uv.txt`,
`fe_optical.txt`, `qsopar2.fits`, `sfddata/`, `LICENSE`, `README.md`,
`CHANGELOG.md`, `requirement*.txt`) from commit
`aa326ed0b13003b22588a0ad9c8a369d9a2de6dd`; `example/` and `archive/`
(demo notebooks/PDFs) are omitted.  PyQSOFitSpec is GPL-3.0 (see
`LICENSE` and `THIRD_PARTY_LICENSES.md`); the repository's MIT licence applies
to the wrapper files in this directory only.

Part of the toolkit group in `configs/README.md`; built by
`pipeline/runners/build_images.sh pyqsofitspec_line`.
