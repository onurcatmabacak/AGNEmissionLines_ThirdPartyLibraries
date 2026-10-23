# `s3fit_line` — S3Fit simultaneous spectrum + SED / line fit (Docker)

Dockerised **S3Fit 2.2.6** (`pip install s3fit==2.2.6`) applied to the
repository's canonical SDSS/WISE QSO inputs.  S3Fit uses `scipy.optimize`
(`least_squares` + `lsq_linear`), not MCMC; its uncertainty estimate is a set
of **Monte-Carlo mock spectra** generated and refitted `num_mocks` times.

## Build / run

```bash
bash Pipelines/build_images.sh s3fit_line
.venv/bin/python pipeline/run_new_tools.py --only 04592649654_z_0.5874 \
  --tools s3fit_line --s3fit-n-mocks 10 --force
```

or directly:

```bash
bash Pipelines/run_s3fit_line_docker.sh \
  inputs/04592649654_z_0.5874 outputs/04592649654_z_0.5874/s3fit_line \
  --n-mocks 10
```

The runner accepts `--config DIR` (default `configs/s3fit_line/default`),
`--n-mocks`, `--mode spec+sed|spec`, `--z`, `--threads`, `--seed`, and
`--pyqsofit-dir`.  If `outputs/<source>/pyqsofit_uv/` exists as a sibling of
the output directory, it is mounted read-only automatically and
`pyqsofit_comparison.csv` is produced.

## Inputs

* `inputs/<source>_z_<z>/raw/spec-*.fits` — SDSS DR18 `COADD` table
  (`FLUX` in `1e-17 erg s-1 cm-2 A-1`, `LOGLAM` vacuum, `IVAR`, `WDISP`).
* `inputs/<source>_z_<z>/photometry/photometry.txt` — one-row CIGALE
  catalogue in mJy (`sloan.sdss.g/r/i/z`, `wise.W1/W2/W3/W4`).
* Optional NIR spectrum: the current QSO mode only uses the optical SDSS
  spectrum.  A NIR spectrum can be added later as a second spectral segment;
  it is not needed for the five z>0.5 eFEDS QSOs.

The adapter masks non-finite pixels, `IVAR<=0`, and non-zero SDSS `AND_MASK`
bits.  It uses the SDSS `WDISP` array to derive the instrument resolution
`R(lambda)` and explicitly tells S3Fit that the wavelengths are **vacuum**
(SDSS `LOGLAM` is vacuum; S3Fit's default would apply an air-to-vacuum
correction).

## Model (QSO mode, no stellar SSP)

```text
AGN powerlaw  +  Fe II pseudo-continuum  +  Balmer continuum
+ SKIRTOR torus (dust)
+ NLR  (narrow Gaussian, H-beta/[O III]/[O II]/[Ne III]/...)
+ BLR  (broad Gaussian, H-beta/H-alpha/Mg II/C III])
```

* `Tools/s3fit_line/model_libraries/agn_iron_for_s3fit.fits` and
  `skirtor_for_s3fit.fits` are vendored from the public S3Fit 2.2.6 source
  distribution (`model_libraries/`).  The full S3Fit git repository is not
  vendored.
* `Tools/s3fit_line/filters/` contains the S3Fit SDSS g'/r'/i'/z' and WISE
  1–4 transmission curves.  They are needed because the PyPI wheel does not
  package `filters/`.
* **No stellar SSP library is used.**  S3Fit only initialises the `stellar`
  model frame when a `stellar`/`ssp` model is present; the QSO mode omits it.
  The effective `model_config.json` therefore has no `stellar` key, and the
  fit succeeds without an SSP FITS file.  This is the intended QSO mode, not a
  silent reduction: the disabled component is the host-galaxy stellar
  continuum, which is negligible in these luminous QSOs and not constrained by
  the SDSS fibre.
* PyNeb is disabled by default (`use_pyneb: false`); line ratios are S3Fit's
  fixed Case-B/forbidden-line ratios (ne=100 cm^-3, Te=1e4 K).  Enable it in
  `fit_config.json` and install `pyneb` if needed.

## Normalisation

S3Fit is given the spectrum in **cgs** (`erg s-1 cm-2 A-1`) and the photometry
in **mJy**; no arbitrary scaling is applied by this adapter.  S3Fit internally
divides the spectrum by `spec_flux_scale` (a power of ten) for numerical
conditioning and reports line fluxes in units of `spec_flux_scale`; this
adapter multiplies them back by `spec_flux_scale`, so `s3fit_lines.csv` is in
physical cgs.

For this SDSS sample the fibre spectrum and the `SPALL` imaging photometry
differ by ~0.7 mag (the synthetic SDSS g flux from the spectrum is ~1.8x the
catalogue g flux).  The joint spectrum+SED fit therefore uses S3Fit's
`phot_calib_b` option (`SDSS_gp,rp,ip,zp`) to scale the spectrum to the
photometry before fitting.  The scale factor is stored in `run.json` as
`fit.spec_calib_ratio` and in the NPZ as `spec_calib_ratio`; it is **not
silent**.  Line fluxes are reported in the fitted (photometry-calibrated)
normalisation, and `pyqsofit_comparison.csv` also reports
`ratio_rawspec = (S3Fit flux / spec_calib_ratio) / PyQSOFit`, i.e. the
comparison on the original SDSS-spectrum normalisation used by PyQSOFit.

If you do not want the calibration, set `"phot_calib_b": null` in
`configs/s3fit_line/default/fit_config.json` (or run `--mode spec`); then
`spec_calib_ratio` is 1.

## Outputs

```text
outputs/<source>_z_<z>/s3fit_line/
  s3fit_lines.csv                  component, line, flux, error, FWHM, velocity
  s3fit_fit.png                    data/model/residuals + line components (+ SED)
  s3fit_mc.png                     MC flux/FWHM distributions + chi2_nu
  s3fit_output.npz                 compact spectra, SED, MC line arrays
  model_config.json                effective S3Fit model configuration
  fit_config.effective.json        effective fitting controls
  run.json                         provenance, chi2, runtimes, detections
  s3fit.log                        full S3Fit log
  run.log                          adapter log
  pyqsofit_comparison.csv          optional validation against pyqsofit_uv
  s3fit_output.pkl.gz              only if compact and explicitly enabled
```

The native S3Fit pickle is disabled by default because it embeds all model
grids and loops; a compact NPZ with the spectra, SED, MC line arrays, and
parameters is written instead.  Set `"save_native_pickle": true` or pass
`--save-pickle` to attempt it; the file is removed if it exceeds
`native_pickle_max_mb` (default 25 MB).

## Config layout

```text
configs/s3fit_line/default/
  fit_config.json       mode, n_mocks, fitting controls, photometry calibration
  model_config.json     mods (agn/torus/line) + root_info
  agn_config.json       powerlaw + Fe II + Balmer continuum components
  torus_config.json     SKIRTOR dust component
  line_config.json      NLR and BLR components + line lists
```

`model_config.json` may reference the component JSON files by name; the
adapter resolves those references and the model-library paths at startup and
writes the effective configuration to `model_config.json` in the output.

## Caveats

* The SDSS fibre spectrum does not cover H-alpha for either validation target
  (`04592649654`, z=0.587: rest ~2250–6550 Å; `04570952937`, z=0.990: rest
  ~1790–5230 Å).  H-beta, [O III] 5007, Mg II and (for the z=0.990 target)
  C III] are covered and used for the MC/validation plots.  H-alpha is kept in
  the line list and is automatically masked when out of range; the MC plot
  falls back to the first available lines.
* The QSO mode has no host-galaxy/SSP term, no X-ray/radio constraints, and no
  NIR spectral segment.  The torus is constrained by the four WISE bands only.
* `phot_calib_b` is a single mean scale over the four SDSS bands; it corrects
  the fibre-vs-imaging offset but does not fit a wavelength-dependent
  calibration curve.
* S3Fit's `accept_chi_sq` and recycle logic can refit loops; the runtime is
  reported in `run.json` (`runtime.total_sec`, `runtime.original_fit_sec`,
  `runtime.mc_fit_sec`).
