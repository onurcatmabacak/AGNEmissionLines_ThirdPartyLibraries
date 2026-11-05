# Third-party licences

`Tools/galspec_line/` contains only this repository's adapter code
(`run_galspec.py`, `Dockerfile`, `requirements.txt`, `README.md`).

The Docker image installs:

* **GalSpec** — MIT License, `https://github.com/jyshangguan/GalSpec`,
  pinned commit `18e4effd796a1d51615ca2340bb927278eb18bbf`.
* NumPy (BSD-3-Clause), SciPy (BSD-3-Clause), Astropy (BSD-3-Clause),
  Matplotlib (PSF-based), pandas (BSD-3-Clause), emcee (MIT),
  dynesty (MIT), corner (BSD-2-Clause), extinction (BSD-3-Clause),
  PyAstronomy (MIT), spectres (MIT), multiprocess (BSD-3-Clause).

No GalSpec source tree, example data or model grid is vendored in this
repository.  The image builds from the pinned public commit and keeps the
upstream licence files in the installed Python package.
