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
tool only adds a config-driven line table, the optical H-beta / [O III]
complex, per-component flux extraction and the compact products.

## Build / run

```bash
bash Pipelines/build_images.sh pyqsofitspec_line      # build the image
bash Pipelines/run_pyqsofitspec_line_docker.sh \
  inputs/04592649654_z_0.5874/raw \
  outputs/04592649654_z_0.5874/pyqsofitspec_line \
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
fvalue`).

Default components (rest-frame vacuum wavelengths, matching the sibling
`pyqsofit_uv` line list):

| complex | window [A] | components |
|---|---|---|
| MgII | 2700-2900 | `MgII_br` (skew-normal, `sigval [0.004, 0.05]`), `MgII_na` (`[3.3e-4, 8e-4]`) |
| Hb | 4640-5100 | `Hb_br` (`[0.004, 0.05]`), `Hb_na` (`[3.3e-4, 1.2e-3]`), `OIII5007c` (narrow core), `OIII4959c` (tied to the 5007 core: width/velocity tie `OIII5007c*1.0`, flux ratio 0.33), `OIII5007w` (broad wing, `[0.003, 0.008]`), `OIII4959w` (tied to the wing) |

`linemodel` is `skewnorm_model` by default; `gauss_model` is available in
`fit_linemodel.py`.  A component is called *broad* when the fitted
`log10(sigma) > 0.0017` (`sigma > 512 km/s`), which is the package's own
`QSOFit.line_prop` classification.

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
each fit, otherwise the two error estimates would be mixed.
`nboot_fit=10` is a smoke-sized ensemble; production runs should use 50-100.

## Outputs

`outputs/<source_key>/pyqsofitspec_line/`:

| file | content |
|---|---|
| `pyqsofitspec_lines.csv` | compact table: line, component (broad/narrow), complex, rest wavelength, flux, flux error, p16/p84, flux in cgs, FWHM and error, sigma, skewness, EW, peak, S/N, `stable`, note, nboot |
| `pyqsofitspec_totals.csv` | broad+narrow totals used for the cross-tool comparison (MgII, Hbeta, OIII5007, OIII5007core) |
| `pyqsofitspec_out.csv` | native-style one-row-per-spectrum table (`<line>_<prop>_<br|na>` and `_err`, mean/std over the bootstrap), i.e. the upstream `pyqsofitspec_out.csv` schema extended with the line area |
| `pyqsofitspec_bootstrap.csv` | every realisation: scale, ln(center), ln(sigma), skew, FWHM, sigma, EW, peak, area |
| `spec-<name>_fit.pdf` / `.png` | the package's own fit figure (continuum decomposition + each complex, realisation 0) |
| `pyqsofitspec_bootstrap.png/.pdf` | bootstrap histograms of the total fluxes (the bimodal [O III] core is visible) |
| `pyqsofitspec_corner.png/.pdf` | corner plot of the H-beta / [O III] 5007 / Mg II totals (scatter mode for `nboot < 20`) |
| `run.json` | method, versions, input, per-iteration wall times and fluxes, fit status/reduced chi2, line table, caveats |
| `config.effective.json` | resolved configuration incl. input, z, coverage, seed, nboot |
| `run.log` | driver log |
| `cross_tool_comparison.csv/.json` | added by `compare_outputs.py` (see below) |

S/N is `flux / bootstrap_std`.  `stable=false` marks a component whose 16-84 %
interval is wider than 25 % of its mean (a multimodal or unconstrained
component).

Cross-tool table:

```bash
python3 Tools/pyqsofitspec_line/compare_outputs.py outputs/<source_key>
```

It reads the sibling `pyqsofit_uv`, `gandalf_line` and `s3fit_line` outputs
and writes `cross_tool_comparison.csv` next to the PyQSOFitSpec products.

## Committed demonstration run: `04592649654` (z = 0.5874)

```bash
bash Pipelines/run_pyqsofitspec_line_docker.sh \
  inputs/04592649654_z_0.5874/raw \
  outputs/04592649654_z_0.5874/pyqsofitspec_line --name 04592649654
```

`configs/pyqsofitspec_line/default` (`skewnorm_model`, `nboot_fit=10`,
`seed=20250101`, no error floor).  Rest-frame coverage 2394-5794 A,
3840 pixels used, 808 masked (observed frame 3800-9200 A).

| quantity | value |
|---|---:|
| image size | 1.2 GB |
| wall time, whole command | 3 m 47 s |
| driver wall time (10 bootstrap fits) | 221.8 s |
| per-realisation wall time | 18.5-23.9 s (mean 21.6 s) |
| Mg II 2798 total | 1932.6 +/- 30.2 (1e-17 erg s-1 cm-2) |
| H-beta total | 3439.5 +/- 33.6 |
| [O III] 5007 total (core+wing) | 1630.7 +/- 17.8 |
| [O III] 5007 core | 776 +/- 244 (bimodal, see caveats) |
| Mg II broad FWHM | 2847 +/- 50 km/s |
| H-beta broad FWHM | 3866 +/- 38 km/s |
| reduced chi2, Mg II complex | 6.01 (302 dof) |
| reduced chi2, H-beta complex | 10.26 (386 dof) |

Cross-tool comparison (1e-17 erg s-1 cm-2; ratio is relative to
PyQSOFitSpec):

| line | PyQSOFitSpec | PyQSOFit (`pyqsofit_uv`) | GANDALF | S3Fit |
|---|---:|---:|---:|---:|
| Mg II 2798 | 1932.6 +/- 30.2 | 2613.1 (1.35) | — | 1822.5 (0.94) |
| H-beta | 3439.5 +/- 33.6 | 2905.1 (0.84) | 2950.8 (0.86) | 2761.0 (0.80) |
| [O III] 5007 | 1630.7 +/- 17.8 | 1479.5 (0.91) | 1422.7 (0.87) | 1506.5 (0.92) |

Reading the differences:

* **[O III] 5007** agrees with all three tools to 8-13 %.  This is the most
  robust line: the narrow core is resolved and the total is prior-bounded.
* **H-beta** is 16-25 % higher than PyQSOFit/GANDALF/S3Fit.  The skew-normal
  broad profile (fitted `a` = -0.65 for H-beta, -2.6 for Mg II, -11 for the
  [O III] wing, i.e. a red wing) puts more flux in the broad base than a
  Gaussian; the narrow component adds another ~670.  The spread of the three
  reference tools (2761-2951) is itself 7 %.
* **Mg II** is 6 % below S3Fit and 35 % above PyQSOFit.  PyQSOFit's UV fit
  includes UV Fe II under the Mg II blend and reports a much larger
  broad component (2517 vs 1835); S3Fit fits the 2796/2804 doublet with a
  Gaussian BLR profile and lands close to the skew-normal result.  The
  Mg II "line" is a blend with Fe II emission, so a 30 % inter-tool spread is
  expected.
* The bootstrap errors (1-2 %) are far smaller than the inter-tool spread,
  i.e. they are statistical-only and conditioned on this model; they must not
  be used to claim a line-flux measurement better than ~10-20 %.

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
pinned versions are recent enough for the code as published.

## Caveats

* **`nboot_fit=10` is a smoke ensemble.**  The uncertainty of the uncertainty
  is ~1/sqrt(2*(nboot-1)) ~ 24 %; use 50-100 for science.
* **The [O III] core/wing split is bimodal.**  In 5 of 10 realisations the
  fit puts ~1030 in the narrow core and ~600 in the wing, in the other 5
  ~520/~1110.  The *total* 5007 flux is stable (1631 +/- 18), the split is
  not (`OIII5007c` is flagged `stable=false`).  Use `OIII5007` total, not the
  core, for line-ratio work.
* **Narrow-line widths are prior-bounded.**  `Hb_na` and `OIII5007c` sit at
  the `sigval` upper bound `1.2e-3` (FWHM 848 km/s), i.e. the data want a
  broader "narrow" component; the same happens in `pyqsofit_uv` (846.8 km/s).
  Only their fluxes are measurements; `pyqsofitspec_lines.csv` flags this in
  the `note` column.
* **Reduced chi2 is 6-10**, not ~1.  The SDSS `IVAR` is a formal per-pixel
  error and does not include flux-calibration/template systematics; the
  Fe II pseudo-continuum is also imperfect under H-beta.  The bootstrap
  inherits those formal errors, which is why the statistical error bars are
  small compared with the inter-tool spread.
* **Skew-normal degeneracy.**  The skewness parameter is free over
  [-1000, 1000] for broad components (upstream default) and the fit uses
  `a ~ -0.7 ... -2.6`; a skewed profile trades peak against wing flux, so the
  broad FWHM and the broad flux are correlated.  The corner plot shows this.
* **Mg II is a blended doublet** (2796/2804) plus UV Fe II; the model fits one
  skewed profile per component, so Mg II fluxes are comparable in definition
  only to tools that also treat the blend as one line (S3Fit sums 2796+2804).
* **H-beta/[O III] only** for this object: at z = 0.587 the rest-frame
  coverage is 2394-5794 A, so H-alpha/[N II]/[S II] are not observable and
  C III]/C IV are not in the list (they were dropped from `main.py`'s UV set
  to keep the run short); add them to `line_table` for higher-z targets.
* The fit figure is realisation 0 of the bootstrap (upstream behaviour); the
  numbers in the tables are means over all realisations.

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
`Pipelines/build_images.sh pyqsofitspec_line`.
