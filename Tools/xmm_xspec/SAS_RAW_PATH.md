# Optional SAS raw-ODF path (not run in the production test)

The production `xmm_xspec` result uses the **official PPS reduced products**.
This note records what a raw SAS reduction would require, so the provenance is
explicit and the path can be added later without pretending it was run.

## Why it was not run

* The SAS Docker image is ~16.5 GB (plus a ~2.9 GB CCF).
* The PPS archive already provides official SAS-reduced source spectra,
  background spectra and source ARFs for ObsID `0721010201`.
* The scientific acceptance test is the spectral fit; re-running `epproc` would
  reproduce the same calibration path at large image/time cost.

The PPS headers record `SASVERS = xmmsas_20241108_1150-21.0.0` (SAS 21.0.0).
The fit uses the current CCF extras RMFs (PN v22.0), which is a later
calibration product than the PPS reduction.  This is documented in `run.json`.

## Raw path (for a future run)

Inside a SAS + HEASoft container with the ODF and CCF mounted:

```bash
# PN and MOS event lists
epproc

# Source and background spectra; use the same regions as the PPS products or
# a documented custom region.  Example for PN:
especget eventset=PN_events.fits \
  srcregionfile=pn_source.reg backregfile=pn_background.reg \
  specset=pn_source.fits backset=pn_background.fits \
  withbackgroundset=yes witharfset=yes withrmfset=yes \
  rmfset=epn_e2_lw20_sdY9_v22.0.rmf \
  arfset=pn_source.arf \
  pattern=4 flag=0

# MOS spectra are 5 eV; rebin to 15 eV to use the canned 15 eV matrices:
specgroup spectrumset=mos1_source.fits groupedset=mos1_source_15eV.fits \
  backgndset=mos1_background.fits \
  mincounts=0 rebin=15 withrebin=yes

# Pile-up / pattern diagnostics
epatplot set=pn_source.fits
```

Then point `configs/xmm_xspec/default/config.json` at the new products (the
`products` override block), or create a variant config, and rerun the same
`Pipelines/run_xmm_xspec_docker.sh`.  The model and outputs are identical.

## What would change

* The ARF/RMF would be generated from the same event lists rather than taken
  from PPS/CCF; the fitted Γ, N_H and Fe Kα flux should be compared with the PPS
  result as a reduction systematic.
* A custom extraction region would change the background scaling and the soft
  excess; document the region files and the `BACKSCAL` values.
* `epatplot` and a pile-up check are mandatory for a bright source such as
  PDS 456 before claiming a production measurement from a custom extraction.
