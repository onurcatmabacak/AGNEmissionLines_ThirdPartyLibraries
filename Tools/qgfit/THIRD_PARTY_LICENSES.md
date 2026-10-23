# Third-party code and data in `Tools/qgfit/`

The repository's top-level MIT licence applies to the `qgfit` wrapper.
The following components keep their own licences and are **not** relicensed by
the repository.

## QGfit 1.0.0

`third_party/qgfit/`, `third_party/setup.py`, `third_party/requirements.txt`

Source: `https://github.com/qian-yang/QGfit`, commit
`3aed692919c0ff1b67fbc2a98a281cdb5e66f971` (2025-01-03, tag `v1`).

The upstream README and `setup.py` declare the MIT licence.  The pinned commit
does **not** contain a `LICENSE` file; the source is included verbatim with its
headers, and the repository does not relicense it.  If you redistribute this
image, confirm the licence with the QGfit authors.

Citation: Yang et al. (2024), arXiv:2408.16183.

## QGfit template data

`third_party/qgfit/template/fe_uv.txt`, `fe_op.txt`,
`bc03_ssp_fl_xarr.npz`, `lines.csv`, `conti_pars2.csv`

These are the Fe II, BC03 stellar-population and line-initialisation data
distributed with QGfit.  The BC03 grid is based on Bruzual & Charlot (2003);
the Fe II templates are the empirical templates referenced by the QGfit paper.
Cite QGfit and the original template papers when publishing results.

## Kapteyn 2.3.1 (built in the image)

`https://pypi.org/project/kapteyn/`

Kapteyn is BSD-licensed.  The Docker image builds it from the PyPI source
tarball; only the compiled `kmpfit` extension is used by QGfit's optional
KMPFIT fallback.

## Runtime libraries

NumPy, SciPy, pandas, Astropy, lmfit, emcee, corner, extinction, sfdmap,
Matplotlib and their transitive dependencies are installed from PyPI and keep
their own licences.
