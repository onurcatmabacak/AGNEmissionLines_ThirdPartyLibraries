# Third-party licences and provenance — `xmm_xspec`

## HEASoft / XSPEC / PyXspec

* Source: NASA/GSFC HEASARC, <https://heasoft.nasa.gov/> and
  <https://heasarc.gsfc.nasa.gov/xanadu/xspec/>.
* Distribution: freely available from HEASARC; the container installs the
  official conda package
  `xspec=13.0.0=hb0f4dca_2` from
  `https://heasarc.gsfc.nasa.gov/FTP/software/conda`.
* The package includes the HEASoft runtime (`HEADAS`), the XSPEC model data and
  PyXspec.
* This repository does not redistribute XSPEC source code; it calls the
  installed package through PyXspec.  Cite the XSPEC manual and the HEASoft
  release notes in any publication.

## XMM-Newton data and responses

* PPS products: ESA/XMM-Newton Science Operations Centre, served by HEASARC.
* CCF response matrices: ESA/XMM-Newton SOC,
  <https://xmm-tools.cosmos.esa.int/external/xmm_ccf/ccf/extras/responses/>.
* The data are public; see the XMM-Newton data-rights policy.  The repository
  commits only the small PPS spectra/ARFs/backgrounds (~15 MB) and the CCF
  matrices, not event files or ODFs.

## Python stack

* `astropy` — BSD-3-Clause, <https://www.astropy.org/>.
* `numpy` — BSD-3-Clause, <https://numpy.org/>.
* `scipy` — BSD-3-Clause, <https://scipy.org/>.
* `matplotlib` — PSF-based licence, <https://matplotlib.org/>.
* `mambaorg/micromamba` base image — BSD-3-Clause; see the image metadata.
* Conda-forge packages carry their own licences; `conda list` inside the image
  records the exact builds.

## Scientific references

* Wilms, J., Allen, A., & McCray, R. 2000, ApJ, 542, 914 (`tbabs`).
* Arnaud, K. A. 1996, ASP Conf. Ser. 101, 17 (XSPEC).
* Nandra, K., et al. 2007, MNRAS, 382, 194 (PDS 456 X-ray properties).
* Reeves, J. N., et al. 2009, Nature, 459, 953 (PDS 456 outflow / Fe K).
