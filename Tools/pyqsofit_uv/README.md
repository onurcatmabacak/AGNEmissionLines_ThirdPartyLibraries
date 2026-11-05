# `pyqsofit_uv` — PyQSOFit UV line fitting (Docker)

PyQSOFit configured for rest-frame UV lines (Mg II 2798, C III] 1908,
C IV 1549, Lyα/N V, Si IV), packaged as a Docker image.

## Build / run

```bash
bash pipeline/runners/build_images.sh pyqsofit_uv
.venv/bin/python pipeline/run_new_tools.py --only 04592649654_z_0.5874 --tools pyqsofit_uv --force
```

The orchestrator prepares `work/prepared/<source_key>/pyqsofit/spectrum.fits`
from the canonical raw spectrum and writes
`outputs/<source_key>/pyqsofit_uv/`.

## What changed in this pass

* **Real errors.** The old config replaced the calibrated error array with
  `0.02 * flux`, making every pixel S/N=50.  The fit now uses the real
  HDU2 error; `PYQSOFIT_ERR_FLOOR` is an opt-in floor.
* **UV is host-free by default.** The host decomposition shrank the rest-frame
  grid to ≳3450 Å and silently skipped Mg II/C III] at z≈0.59.  The UV fit is
  now host-free; pPXF handles the host independently.  `PYQSOFIT_HOST=1`
  restores the old decomposition.
* **Line table.** `pyqsofit_lines.csv` records broad and narrow areas,
  FWHM and S/N for Mg II, C III], C IV, Lyα, Hβ and [O III].  The narrow
  C III]/Mg II areas are the directly comparable quantities; the broad
  complexes are not narrow-line measurements.
* **Mg II at z≈0.59** is now fitted instead of skipped.

The default matrix run is maximum-likelihood.  The committed uncertainty for
`04592649654` is still the 100-realization MC under
`outputs/pyqsofit/04592649654_z_0.5874/mc/`; the MCMC product is kept separate
and explicitly labelled.

## MCMC: exact failure and fix

`PYQSOFIT_MCMC=1` used to run the continuum and Mg II/Hβ emcee chains and then
fail in the Hα complex with:

```text
File ".../pyqsofit/PyQSOFit.py", line 1564, in fit_lines
  line_samples = minimize(self._residual_line, params=line_fit.params, ...
File ".../lmfit/minimizer.py", line 1405, in emcee
  output = self.sampler.run_mcmc(p0, steps, progress=progress, ...)
File ".../emcee/ensemble.py", line 319, in sample
  raise ValueError(
ValueError: Initial state has a large condition number.
Make sure that your walkers are linearly independent for the best performance
```

At that call the free Hα parameters included
`SII6718_1_scale = 0.0` and `SII6732_1_scale = 0.0` (undetected [S II],
lower bound 0).  lmfit 1.3.2 builds its default start as
`p0 = (1 + 1e-4 * N(0,1)) * param.value`, so those two columns are exactly
zero.  `emcee.walkers_independent()` finds a zero column and rejects the
state.  This is an initialization defect, not a model or prior problem.

`configs/pyqsofit/uv/mcmc_support.py` supplies an explicit `pos` to every
emcee call.  It jitters each free parameter around its MLE with a
bounds-aware, strictly positive scale; a zero amplitude starts at 0.1% of the
largest fitted amplitude in the same complex.  It checks `ptp > 0` and
`cond <= 1e8` before sampling.  The likelihood, priors, number of parameters,
fixed/tied expressions, and sampler are unchanged.  The wrapper also records
the chain, acceptance fraction, integrated autocorrelation time and ESS, and
recomputes expression/tied parameters per draw (PyQSOFit otherwise freezes
e.g. [O III] 5007 at its MLE inside `gauss_result_all`).

## Production MCMC recipe

```bash
PYQSOFIT_MCMC=1 \
PYQSOFIT_NSAMP=300 PYQSOFIT_NBURN=80 PYQSOFIT_NTHIN=1 \
PYQSOFIT_NWALKERS=100 PYQSOFIT_MCMC_SEED=20240517 \
PYQSOFIT_MCMC_LINE_SAMPLES=500 \
bash pipeline/runners/run_pyqsofit_uv_docker.sh <input-dir> <output-dir>
```

`NSAMP=300, NBURN=80, NTHIN=1` retains 220 steps per walker (22,000 draws at
100 walkers).  Raise `NSAMP` for a longer posterior; the PyQSOFit internal
per-draw `line_prop` loop makes the runtime grow quickly.  The runner copies
`*.json` and `*.npz` in addition to fits/pdf/csv/png.

Products in the output directory:

```text
pyqsofit_mcmc_samples.csv       # readable thinned line-flux posterior
pyqsofit_mcmc_samples.npz       # full chains, lnprob, tau, ESS, per-line draws
pyqsofit_mcmc_summary.csv       # median/p16/p84 per line and component
pyqsofit_mcmc_corner.pdf/.png   # full corner, one page/stage + main-stage PNG
pyqsofit_mcmc_trace.pdf/.png    # parameter traces
pyqsofit_mcmc_line_corner.png   # corner of Hβ/[O III]/Mg II line fluxes
pyqsofit_mcmc_config.json       # effective config
run.json                        # status, versions, acceptance, tau, ESS, runtime
```

## Status for `04592649654_z_0.5874` (2026-10-24)

* A 300-step capped run completed the PyQSOFit fit in **1400.6 s** and its
  fit figure/output are preserved as
  `outputs/pyqsofit/04592649654_z_0.5874/mcmc/pyqsofit_mcmc_fit.pdf` and
  `output.fits`/`qsopar.fits`.  Its 220 retained steps gave acceptance
  0.37/0.41/0.32/0.36 (continuum/Mg II/Hβ/Hα) and tau_max 36/29/38/35,
  i.e. only 5.8–7.6 steps per tau; it is not converged either.
* The outer shell timed out after the fit and before the container copied the
  chains, so the 300-step samples were not persisted.  This is a runner
  timeout, not an MCMC failure.
* The committed `pyqsofit_mcmc_samples.csv`/`.npz`, corner and trace are from
  the validated **10-step** initialization-fix run (`NSAMP=10, NBURN=2,
  NTHIN=1, NWALKERS=100`; 8 retained steps = 800 draws; line posterior
  subsample 10).  Acceptance is 0.31 and the chain is **not converged**
  (`tau` is too short to estimate reliably).  Use this only as proof that the
  emcee path now runs end-to-end and as a template for a longer run.
* The 100-realization MC remains the committed uncertainty product.  The
  `comparison_mc_tools.csv` table puts the short MCMC medians beside that MC
  and GANDALF/S3Fit/GalSpec/QGfit; the MCMC scatter there is not a converged
  error bar.

## Controls

```bash
PYQSOFIT_MC=1 PYQSOFIT_NSAMP=100 ...                    # Monte-Carlo errors
PYQSOFIT_MCMC=1 PYQSOFIT_NSAMP=300 PYQSOFIT_NBURN=80 ... # emcee posterior
PYQSOFIT_MCMC_LINE_SAMPLES=500 ...                      # line-flux draws
PYQSOFIT_NWALKERS=100 PYQSOFIT_MCMC_SEED=20240517 ...   # sampler controls
PYQSOFIT_ERR_FLOOR=0.01 ...                             # optional error floor
PYQSOFIT_HOST=1 ...                                     # old host-decomposed run
```

## Remaining limitations

* C III] broad flux includes UV Fe II/outflow; after adding satellites and
tightening the broad-width prior, total/ZLINE is 1.29–1.76.  The narrow
component is severely blend/width limited and is reported only as a diagnostic.
* PyQSOFit's internal per-sample `line_prop` loop makes long MCMC chains
  expensive; the production recipe above is the practical cap.  A future
  cleanup should vectorize that loop before running >500 steps.
* The UV fit and pPXF host fit are separate by design; their apertures are the
  same SDSS fibre.
