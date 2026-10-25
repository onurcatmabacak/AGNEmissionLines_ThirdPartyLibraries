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
| `04545014975_z_1.1289` | 1.1289 | SDSS DR18 eFEDS QSO | `spectrum` | ir, pyqsofit_uv, ppxf_host, cigale_sed, agnfitter_sed |
| `04570952937_z_0.9901` | 0.9901 | SDSS DR18 eFEDS QSO | `spectrum` | ir, pyqsofit_uv, ppxf_host, cigale_sed, agnfitter_sed |
| `04592566733_z_1.8297` | 1.8297 | SDSS DR18 eFEDS QSO | `spectrum` | ir, pyqsofit_uv, ppxf_host, cigale_sed, agnfitter_sed |
| `04592649654_z_0.5874` | 0.5874 | SDSS DR18 eFEDS QSO | `spectrum` | ir, pyqsofit_uv, qsofitmore_line, ppxf_host, cigale_sed, agnfitter_sed |
| `04592933676_z_0.6506` | 0.6506 | SDSS DR18 eFEDS QSO | `spectrum` | ir, pyqsofit_uv, ppxf_host, cigale_sed, agnfitter_sed |
| `spSpec-51908-0277-120_z_0.0859` | 0.0859 | SDSS legacy spSpec (GANDALF example) | `spectrum` | gandalf_line |
| `J0100p2802_z_6.3270` | 6.327 | JWST/NIRSpec G395H | `spectrum`, `centered` | nir_linefit (pipeline + QSO-centred), ir_linefit |
| `VV114_z_0.0200` | 0.020 | JWST/MIRI MRS (PAHFIT example) | `spectra` (12 s1d) | cafe_line, pahfit_mir, ir_linefit |
| `PDS456_z_0.1840` | 0.184 | JWST/MIRI MRS + HST/STIS UV | `spectra` (short/long), `optical_spectrum` (HST UV), `xshooter_spectrum` (X-SHOOTER VIS) | cafe_line, pahfit_mir, ir_linefit, xmm_xspec, pyqsofit_uv, optical_linefit, crossmission |
| `3C120_z_0.0330` | 0.033 | RXTE/PCA + HST/STIS optical | `optical_spectrum`, `xray_pca_*` | rxte_xspec, pyqsofit_uv, qsofitmore_line, crossmission |
| `NGC1068_z_0.0038` | 0.003793 | Herschel PACS + HIFI | `pacs`, `spectrum` | fir_linefit, ir_linefit |
| `NGC4151_z_0.0033` | 0.003319 | Spitzer IRS + Herschel PACS | `mir_table`, `pacs` | pahfit_mir, fir_linefit, ir_linefit, crossband |
| `Mrk231_z_0.0422` | 0.04217 | Spitzer IRS | `mir_table` | pahfit_mir, ir_linefit, crossband |
| `NGC253_z_0.0008` | 0.000811 | Spitzer IRS + Herschel PACS/HIFI | `mir_table`, `pacs`, `spectrum` | pahfit_mir, fir_linefit, ir_linefit, crossband |
| `synthetic_fir_z_0.5000` | 0.500 | synthetic PACS-like | `spectrum` | fir_linefit, ir_linefit |
| `NGC1194_z_0.0136` | 0.0136253 | real MaNGA DR17 AGN (Sy2) | `manga_cube`, `manga_rss`, `manga_maps_reference` | manga_dap |
| `synthetic_multiband_z_0.0000` | 0.000 | synthetic ratios | `ratios` | crossband |

`ir` = `ir_linefit` (the generic `pipeline_ir` fitter).

## Provenance

* SDSS five: SDSS DR18 eFEDS SAS (`spec-*.fits`); see `catalogs/sdss_zgt05.csv`.
  Photometry is derived by `pipeline/build_photometry.py` from `SPALL`
  (`MAG`, `WISE_MAG`) with nominal 0.05 mag (SDSS) / 0.125 mag (WISE) errors.
* `spSpec-51908-0277-120`: public GANDALF v1.5 `SDSS_example` low-z galaxy
  (plate 277, MJD 51908, fiber 120, z=0.0858772), copied unmodified.  See the
  directory README for the header-level provenance and MD5.
* J0100+2802: JWST/NIRSpec G395H pipeline `x1d` plus a QSO-centred 3×3 extraction from the public MAST `s3d` cube (`pipeline/extract_nir_aperture.py`).  The raw cube is not committed.
* VV114: PAHFIT's packaged MIRI MRS example (`*_s1d.fits`).
* PDS 456: JWST/MIRI MRS short/long `x1d`.
* NGC 1068, NGC 253: Herschel/PACS HPDP extracted spectra from the ESA HSA
  (`hpacs..._POC_*.fits.gz`); NGC 1068 also HIFI HPDP.
* Mrk 231, NGC 253, NGC 4151: Spitzer IRS Enhanced `*_merge.tbl` from IRSA.
* PDS 456 and 3C 120: real HST/STIS HASP `cspec` products from MAST; PDS 456
  additionally uses the public ESO VLT/X-SHOOTER VIS reduced spectrum for Hβ.
  See `inputs/<source>/README_OPTICAL.md` and `download_optical.sh`.
* NGC 1194 (plateifu 9193-12701): real MaNGA DR17 LOGCUBE/LOGRSS and the published DAP MAPS, downloaded by `NGC1194_z_0.0136/download.sh`; the two DRP cubes are Git-ignored (>100 MB) and SHA-256 verified.  See `source.json`.
* Synthetic files are labelled `synthetic_*`; they are not real sources.

The PACS files were extracted from the public HSA product
`PACS-S-POC.tar` (Herschel/PACS Pointing Offset Corrected spectra).
`crossband.csv` for Mrk 231/NGC 253 is derived from the PAHFIT and FIR outputs
by `pipeline/build_crossband_from_outputs.py`; it is small and kept for
reproducibility.

## Redshift and naming

The canonical key is `<slug(source_name)>_z_<z:0.4f>`; the exact redshift lives
in `source.json`.  `+` in a name is replaced by `p` (e.g. `J0100p2802`).
