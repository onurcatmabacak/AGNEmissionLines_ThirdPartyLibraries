# XMM-Newton EPIC provenance — PDS 456

ObsID **0721010201**.  Official PPS products + CCF responses; SAS epproc/especget NOT run.

## What was run

- Official XMM-Newton **PPS** source spectra, background spectra and source ARFs.
- Official CCF response matrices (PN v22.0; MOS 15 eV canned matrices).
- HEASoft/PyXspec XSPEC 13.0.0 with `tbabs*zpowerlw` and `zgauss`.

## What was not run

- **SAS `epproc`/`especget`/`specgroup`/`epatplot` were not run.**  The PPS
  spectra are the official SAS pipeline products; re-running the 16.5 GB SAS
  Docker image and ~2.9 GB CCF was outside this test's budget.  See
  `Tools/xmm_xspec/SAS_RAW_PATH.md` for the optional raw-ODF path.
- No event-file filtering, no custom extraction region, no pile-up or
  CTI correction beyond what PPS already applied.

## Response caveats

- The PPS MOS spectra have 2400 channels at 5 eV.  The 15 eV canned MOS
  matrices named in the PPS headers have 800 channels, so the MOS spectra
  and backgrounds were rebinned 3:1 to 15 eV (counts summed, QUALITY ORed,
  grouping preserved).  The PN spectrum and RMF both have 4096 channels.
- The RMF FILTER keyword is `Medium` while the observation used `Thin1`.
  The redistribution matrix is filter-independent; the ARF carries the
  filter throughput.  XSPEC emits a warning, which is expected.
- The PN RMF is the current CCF extras v22.0 matrix.  The PPS products
  were generated with SAS xmmsas_20241108_1150-21.0.0; the RMF is a
  later calibration product, not the exact matrix used by PPS in 2024.

## Statistical caveats

- The simple `tbabs*zpowerlw` continuum leaves a reduced chi-square of
  1.70; the soft excess and Compton reflection
  are not modeled.  A blackbody soft-excess baseline is fitted as a
  systematic check.
- The narrow Fe K-alpha core is measured with a 50 eV (rest-frame) Gaussian.
  A free-width Gaussian runs to the fit bound; the broad Fe K-alpha excess
  is degenerate with continuum curvature and is reported only as a
  systematic check, not as a resolved line width.
- Errors are XSPEC covariance 1-sigma errors; no MCMC was run.
