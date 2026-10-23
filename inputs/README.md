# `inputs/` — canonical source store

One directory per science source:

```text
inputs/
  catalogs/                  # cross-source tables only
  <source_name>_z_<redshift>/
    source.json              # name, z, kind, coordinates, roles, tools
    raw/                     # the canonical, unmodified data (only copy)
    photometry/photometry.txt# optional one-row CIGALE catalogue
```

The raw files are the **only** copies in the repository.  Tool-native layouts
(PyQSOFit `spectrum.fits`, pPXF input, FIR staging) are generated on demand
under `work/prepared/<source_key>/` and are not committed.  This is the compact
input policy: one source, one raw payload, one manifest.

## Sources

| source key | z | kind | raw roles | tools |
|---|---:|---|---|---|
| `04545014975_z_1.1289` | 1.1289 | SDSS DR18 eFEDS QSO | `spectrum` | ir, pyqsofit_uv, ppxf_host, cigale_sed |
| `04570952937_z_0.9901` | 0.9901 | SDSS DR18 eFEDS QSO | `spectrum` | ir, pyqsofit_uv, ppxf_host, cigale_sed |
| `04592566733_z_1.8297` | 1.8297 | SDSS DR18 eFEDS QSO | `spectrum` | ir, pyqsofit_uv, ppxf_host, cigale_sed |
| `04592649654_z_0.5874` | 0.5874 | SDSS DR18 eFEDS QSO | `spectrum` | ir, pyqsofit_uv, ppxf_host, cigale_sed |
| `04592933676_z_0.6506` | 0.6506 | SDSS DR18 eFEDS QSO | `spectrum` | ir, pyqsofit_uv, ppxf_host, cigale_sed |
| `J0100p2802_z_6.3270` | 6.327 | JWST/NIRSpec G395H | `spectrum` | nir_linefit, ir_linefit |
| `VV114_z_0.0200` | 0.020 | JWST/MIRI MRS (PAHFIT example) | `spectra` (12 s1d) | pahfit_mir, ir_linefit |
| `PDS456_z_0.1840` | 0.184 | JWST/MIRI MRS | `spectra` (short/long) | pahfit_mir (short/long/both), ir_linefit |
| `NGC1068_z_0.0038` | 0.003793 | Herschel PACS + HIFI | `pacs`, `spectrum` | fir_linefit, ir_linefit |
| `Mrk231_z_0.0422` | 0.04217 | Spitzer IRS + Herschel PACS | `mir_table`, `pacs` | pahfit_mir, fir_linefit, ir_linefit, crossband |
| `NGC253_z_0.0008` | 0.000811 | Spitzer IRS + Herschel PACS/HIFI | `mir_table`, `pacs`, `spectrum` | pahfit_mir, fir_linefit, ir_linefit, crossband |
| `synthetic_fir_z_0.5000` | 0.500 | synthetic PACS-like | `spectrum` | fir_linefit, ir_linefit |
| `synthetic_multiband_z_0.0000` | 0.000 | synthetic ratios | `ratios` | crossband |

`ir` = `ir_linefit` (the generic `pipeline_ir` fitter).

## Provenance

* SDSS five: SDSS DR18 eFEDS SAS (`spec-*.fits`); see `catalogs/sdss_zgt05.csv`.
  Photometry is derived by `pipeline/build_photometry.py` from `SPALL`
  (`MAG`, `WISE_MAG`) with nominal 0.05 mag (SDSS) / 0.125 mag (WISE) errors.
* J0100+2802: JWST/NIRSpec G395H `x1d` from the public archive.
* VV114: PAHFIT's packaged MIRI MRS example (`*_s1d.fits`).
* PDS 456: JWST/MIRI MRS short/long `x1d`.
* NGC 1068, NGC 253: Herschel/PACS HPDP extracted spectra from the ESA HSA
  (`hpacs..._POC_*.fits.gz`); NGC 1068 also HIFI HPDP.
* Mrk 231, NGC 253: Spitzer IRS Enhanced `*_merge.tbl` from IRSA.
* Synthetic files are labelled `synthetic_*`; they are not real sources.

The PACS files were extracted from the public HSA product
`PACS-S-POC.tar` (Herschel/PACS Pointing Offset Corrected spectra).
`crossband.csv` for Mrk 231/NGC 253 is derived from the PAHFIT and FIR outputs
by `pipeline/build_crossband_from_outputs.py`; it is small and kept for
reproducibility.

## Redshift and naming

The canonical key is `<slug(source_name)>_z_<z:0.4f>`; the exact redshift lives
in `source.json`.  `+` in a name is replaced by `p` (e.g. `J0100p2802`).
