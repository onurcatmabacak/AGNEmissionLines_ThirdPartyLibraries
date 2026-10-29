# `pipeline_ir` / `ir_linefit` — generic IR line router and fitter

The generic local-Gaussian line fitter used by the NIR/MIR/FIR suite.  It is
the fallback/cross-check tool; the specialised tools (`nir_linefit`,
`pahfit_mir`, `fir_linefit`) remain the primary models for their bands.

## Layout

Inputs are canonical source directories; results are source-keyed:

```bash
bash pipeline/runners/run_ir.sh --fits inputs/04592649654_z_0.5874/raw/spec-00000-59345-04592649654.fits \
  --z 0.58741307 --out outputs/ir_linefit/04592649654_z_0.5874
```

The orchestrator does this automatically:

```bash
.venv/bin/python pipeline/run_new_tools.py --tools ir_linefit
```

Per spectrum it writes `<object>.route.json`, `<object>.measurements.csv`,
`<object>.fit.png/pdf` and, for every undetected component, a finite 3σ
`flux_limit`.

## Adapters

`pipeline_ir/spectrum.py` now dispatches:

* SDSS DR18 eFEDS/BOSS `COADD`;
* JWST/NIRSpec `EXTRACT1D` `FLUX` [Jy] and JWST/MIRI `SURF_BRIGHT` [MJy/sr];
* PAHFIT/MIRI `*_s1d.fits` [MJy/sr];
* Spitzer IRS Enhanced IPAC `.tbl` [Jy -> cgs fλ];
* Herschel/PACS HPDP `hpacs...POC_*.fits(.gz)` [Jy];
* Herschel/HIFI HPDP [K, GHz], retained as antenna temperature.

The output JSON/CSV record `instrument`, `flux_unit` and
`native_flux_unit`; the fitter never guesses a unit.

## Validation

* Real SDSS z>0.5 sample: Hβ and [O III] agree with SDSS ZLINE at the
  10–30 % level (blends are flagged in the route JSON).
* Real JWST/NIRSpec J0100+2802: broad Hα detected at 4.81 µm.
* Real PACS NGC 1068 [OI] 63 µm and NGC 253 [OI]/[OIII]/[OI]/[CII] lines
  are recovered with the FIR tool.
* Synthetic NIR/MIR/FIR injections recover flux to a few percent and FWHM
  to a few percent at high S/N.

## Remaining limitations

* No telluric/PAH/fringe/background model; use the specialised tools.
* Broad/narrow decomposition is Hα/Hβ only.
* FIR line-flux biases at low S/N remain; the dedicated FIR tool is the
  quantitative path.
* The router is coverage/segment based; it does not magically create
  coverage for a line outside the spectrum.
