# Third-party code and data in `Tools/manga_dap/`

The repository's top-level MIT licence applies to the wrapper code
(`run_manga_dap.py`, `compare_maps.py`, `manga_maps.py`, `fast_eline.py`).
The following components keep their own licences and are **not** relicensed by
the repository.

## `sdss-mangadap` 4.5.0

The official SDSS MaNGA Data Analysis Pipeline.

* Source: `https://github.com/sdss/mangadap`
* Upstream commit: `996b46cb9739126fe0fbe69c1a50d8490d924853` (tag `4.5.0`)
* Licence: **BSD 3-Clause** (Copyright (c) 2018, SDSS)
* Citation: Westfall et al. 2019, AJ, 158, 231; Belfiore et al. 2019, AJ,
  158, 160.

The complete BSD-3 licence text is included in the installed wheel; the
upstream copyright and licence are retained.  This repository does not modify
the upstream source.  `fast_eline.py` calls the public `Sasuke` API and does
not patch upstream code.

## DAP template and database data

The `sdss-mangadap` wheel ships the data used at runtime:

* **MILES-HC** stellar templates (`mangadap/data/spectral_templates/miles_cluster/`)
  — MILES simple stellar populations (Vazdekis et al. 2010, 2015; Falcón-Barroso
  et al. 2011).  Cite the MILES papers when publishing stellar kinematics.
* **MaStar-HC2** stellar templates (`mangadap/data/spectral_templates/mastarhc_v2/`)
  — MaStar library (Yan et al. 2019) convolved to the DAP resolution.
* **ELPMPL11** emission-line database (`mangadap/data/emission_lines/elpmpl11.par`)
  — NIST Ritz wavelengths and the DAP multiplet ties.
* DAP artifact/emission masks (`badsky.par`, `elpscmsk.par`) and
  `sdssMaskbits.par`.

These files are redistributed unmodified as part of the BSD-licensed
`sdss-mangadap` package.  Their MD5/SHA-256 values are recorded in
`effective_config.json`.

## Runtime libraries

`numpy`, `scipy`, `astropy`, `matplotlib`, `ppxf` (Cappellari 2017; Cappellari
& Emsellem 2004), `cvxopt`, `vorbin` (Cappellari & Copin 2003), `pydl` and
`shapely` are installed from PyPI and retain their own licences.  `ppxf` is
GPL-3.0; `vorbin` is MIT; the others use BSD/MIT-style licences.

## Survey data

The MaNGA DR17 LOGCUBE, LOGRSS and the published DAP MAPS are public SDSS
data products.  Cite SDSS DR17 (Abdurro'uf et al. 2022), MaNGA (Law et al.
2016), the DAP (Westfall et al. 2019; Belfiore et al. 2019) and the MaNGA AGN
Catalog (Comerford et al. 2020).
