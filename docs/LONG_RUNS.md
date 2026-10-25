# Long and full-capability runs

The repository does not silently shorten a production fit.  Use the controls
below when you need the full model and can afford the wall time.

## Scheduling

```bash
# One heavy multicore tool first, then single-core tools in parallel
python pipeline/run_new_tools.py \
  --source 04592649654_z_0.5874 \
  --phased --threads 8 --jobs 4

# Explicit selection
python pipeline/run_new_tools.py --source 04592649654_z_0.5874 \
  --tools s3fit_line galspec_line pyqsofit_uv qsofitmore_line \
  --phased --threads 8 --jobs 4
```

Phase 1 is serial for `MULTICORE_TOOLS`; phase 2 uses one thread per remaining
tool.  S3Fit receives `--threads` explicitly; other tools receive standard
`OMP_NUM_THREADS` / `OPENBLAS_NUM_THREADS` / `MKL_NUM_THREADS`.

## S3Fit

```bash
python pipeline/run_new_tools.py --source 04592649654_z_0.5874 \
  --tools s3fit_line --s3fit-mode spec+sed --s3fit-threads 8 \
  --s3fit-n-mocks 10 --phased --threads 8
```

## GalSpec

The default `mcmc.nsteps=4000` reaches only ~8.2 retained τ.  A longer run:

```bash
python pipeline/run_new_tools.py --source 04592649654_z_0.5874 \
  --tools galspec_line --galspec-config configs/galspec_line/long \
  --phased --threads 8
```

The acceptance gate is `nsteps / tau_max >= 50` and an ESS large enough to
report the posterior; do not call it converged from step count alone.

## PyQSOFit MCMC

```bash
PYQSOFIT_MCMC=1 PYQSOFIT_NSAMP=2000 PYQSOFIT_NBURN=500 \
PYQSOFIT_NTHIN=1 PYQSOFIT_NWALKERS=100 \
bash Pipelines/run_pyqsofit_uv_docker.sh \
  work/prepared/04592649654_z_0.5874/pyqsofit \
  outputs/04592649654_z_0.5874/pyqsofit/mcmc_long
```

This is a multi-hour run.  The committed short chain is only an
initialization-fix proof; the 100-realization MC remains the quantitative
product until a long chain passes the τ/ESS gate.

## QGfit line MCMC

`configs/qgfit/production/config.json` keeps `line_mcmc=false` because the
pilot per-complex chain was unstable (`tau` 20–42, red-χ² ~6e10 versus LSQ
~11.5).  Enabling it without fixing that posterior would not "solve" the
uncertainty; the LSQ covariance remains the honest product.

## SHEAP

The production result is restricted to a validated Hβ/[O III] window.  A
broader-window run requires a model change, not just a longer runtime; see
`docs/SHEAP_ASSESSMENT.md`.

## Full MaNGA DAP

The all-spaxel official DAP is exposed as `manga_dap_full`:

```bash
bash Pipelines/run_manga_dap_docker.sh \
  inputs/NGC1194_z_0.0136 outputs/NGC1194_z_0.0136/manga_dap_full \
  --reference inputs/NGC1194_z_0.0136/raw/manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz \
  --full
```

This uses `plan.toml` (S/N=10, all bins) and the full 65-template SASUKE fit.
It is a multi-hour single-core upstream workflow.  Do not substitute the
fixed-continuum fast mode and call it full DAP.

## Raw XMM SAS and RXTE PCA

The production X-ray products use official PPS / `stdprod` products.  Raw SAS
and raw PCA reductions remain external, instrument-team-style reductions:

- `Tools/xmm_xspec/SAS_RAW_PATH.md` documents the exact `epproc`/`especget`
  commands and the SAS/CCF size.
- RXTE raw Standard-2 arrays are in the `pca/` sibling of `stdprod/`, not
  inside `stdprod`; raw `pcabackest`/`saextrct` also needs the mission
  housekeeping/obc files, a HEASoft build with those tools, and a working
  HEASARC endpoint.  `stdprod` is the current production path.

The raw XMM PN path has now been run end-to-end for PDS 456; see
`docs/XMM_RAW_SAS_RESULT.md` and `outputs/PDS456_z_0.1840/xmm_sas_raw/`.
It is a PN-only cross-check, not a replacement for joint PPS.  Raw RXTE PCA
remains unavailable from the current network and would require a separate
full-HEASoft image.

## Registry digests

`docs/image_digests.json` records local IDs.  For immutable registry references,
run the manual `Publish images to GHCR` workflow (`.github/workflows/publish-images.yml`);
it pushes `ghcr.io/<owner>/agnemissionlines-thirdpartylibraries/<tool>:<tag>`
and uploads the returned `@sha256` digests.
