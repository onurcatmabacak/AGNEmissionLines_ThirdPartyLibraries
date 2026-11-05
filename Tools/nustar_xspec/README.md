# nustar_xspec — NuSTAR 3-79 keV hard X-ray fitting

NuSTAR extends the X-ray coverage above the 20 keV ceiling of the XMM EPIC and
RXTE PCA tools, which is where the Compton-thick diagnostics live: the >10 keV
turnover, the Compton reflection hump and the Fe K-alpha equivalent width cannot
be constrained on a 2-10 keV band alone.

Image: HEASoft + NuSTARDAS + XSPEC from the **bioconda** `heasoft` package, because
conda-forge ships neither the 23 `nu*` tasks nor a NuSTAR CALDB.  CALDB is remote
(HTTPS) - the full tarball is 2.34 GB and unnecessary for a spectrum extraction.

Data: public NuSTAR **Level-2** cleaned event files, so `nupipeline` is skipped and
only `nuproducts` runs (ARF, RMF, spectrum).

Model: `tbabs*cutoffpl` plus a `zgauss` Fe K-alpha line, fitted with the
C-statistic; the absorbed and unabsorbed hypotheses are compared.
