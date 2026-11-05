# Third-party code and data in `Tools/pyqsofitspec_line/`

The repository's top-level MIT licence applies to the Dockerfile, the driver
(`run_pyqsofitspec.py`), the comparison script and the `sfdmap` shim.  The
following components keep their own licences and are **not** relicensed by
the repository:

## PyQSOFitSpec (`third_party/PyQSOFitSpec/`)

Copyright (C) Suk Yee Yong and contributors.  Adapted from PyQSOFit v1.1
(Hengxiao Guo, Shu Wang, Yue Shen, Wenke Ren) and PyQSOFit_SBL (Jack Hon).

**Licence: GNU General Public License v3.0** — the upstream `LICENSE` file is
retained verbatim in `third_party/PyQSOFitSpec/LICENSE`.

Source: <https://github.com/yongsukyee/PyQSOFitSpec>, commit
`aa326ed0b13003b22588a0ad9c8a369d9a2de6dd`.

The vendored files are unmodified.  `example/` and `archive/` (upstream demo
notebooks, FITS spectra and PDFs) are not redistributed here.

## Fe II templates

`fe_uv.txt` (Vestergaard & Wilkes 2001 / Salviander et al. 2006 composite,
Boroson & Green 1992) and `fe_optical.txt` (Boroson & Green 1992) are the
templates distributed with PyQSOFit.  Cite the original papers when publishing
Fe II measurements.

## kapteyn 3.4

`kmpfit` is installed at image build time from
`https://www.astro.rug.nl/software/kapteyn/kapteyn-3.4.tar.gz`
(BSD-3-Clause, J. P. Terlouw, M. G. R. Vogelaar, M. A. Breddels), SHA256
pinned in the Dockerfile.  `patches/patch_kapteyn.py` only restricts the
build to the `kmpfit` extension; no kapteyn source is modified.

## SFD dust maps

The `sfddata/` directory (upstream: only a README) refers to the Schlegel,
Finkbeiner & Davis (1998) maps distributed by K. Barbary
(<https://github.com/kbarbary/sfddata>).  No map data are redistributed here
and dereddening is disabled, so none are downloaded during a run.
