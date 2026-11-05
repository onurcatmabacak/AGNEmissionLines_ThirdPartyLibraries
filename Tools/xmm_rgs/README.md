# xmm_rgs — soft X-ray grating line fitting (XMM-Newton RGS)

Fits resolved soft-X-ray lines in an XMM RGS spectrum using the SOC pipeline
products only: the `SRSPEC` counts spectrum plus its `RSPMAT` response matrix.
No SAS/`rgsproc` run is needed (that path also requires ODF attitude and
housekeeping files, which XSA's AIO endpoint does not serve).

Model: `tbabs*zpowerlw` plus one `zgauss` per requested line, fitted with the
C-statistic in XSPEC.

Caveat: `RSPMAT` is a response matrix without a separate ARF, so line energies,
widths, significances and equivalent widths are calibrated while absolute fluxes
are not.
