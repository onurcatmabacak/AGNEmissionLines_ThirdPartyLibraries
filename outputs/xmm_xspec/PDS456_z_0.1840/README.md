# PDS 456 — XMM-Newton EPIC PPS fit (`xmm_xspec`)

Official XMM-Newton Pipeline Processing System (PPS) spectra of PDS 456
(ObsID `0721010201`, z = 0.184, PN Large Window Thin1, 100.4 ks), fitted with
HEASoft/PyXspec.  This is the X-ray continuum/Fe K-alpha branch of the matrix;
the raw-ODF cross-check is a separate product in `../xmm_sas_raw/`.

## Inputs

| item | value |
|---|---|
| PPS products | PN + MOS1 + MOS2 `SRSPEC`, `BGSPEC`, `SRCARF` |
| response | PN CCF v22.0 `epn_e2_lw20_sdY9_v22.0.rmf`; MOS 15 eV canned matrices |
| band | production config **0.7–10 keV** (observed frame) |
| model | `constant*tbabs*(zpowerlw + zgauss)`, Fe K-alpha at 6.4 keV rest, sigma fixed to 50 eV |
| statistic | chi-square on the grouped PPS spectra |

The PPS data and output files are not shipped.  Restore the small PPS products
with the download instructions in `Tools/xmm_xspec/README.md`, then run
`pipeline/runners/run_xmm_xspec_docker.sh`.

## Archived production result

The production run recorded in `Tools/xmm_xspec/README.md` used the 0.5–10 keV
band and the joint PN+MOS1+MOS2 fit:

| quantity | value |
|---|---|
| baseline `tbabs*zpowerlw` | chi2/dof = 879.03/516 = 1.704 |
| Gamma | 2.0221 +/- 0.0041 |
| N_H | (2.304 +/- 0.018) x 10^21 cm^-2 |
| narrow Fe K-alpha (50 eV) | chi2/dof = 862.64/515 = 1.675 |
| Delta chi2 (1 dof) | 16.39 -> **4.05 sigma** |
| line flux | (2.01 +/- 0.50) x 10^-14 erg cm^-2 s^-1 |
| EW_rest | 25.9 +/- 6.4 eV |

The current config has moved to 0.7–10 keV; the numbers above are the archived
0.5–10 keV run, not a current-config rerun.  The 0.5–0.7 keV band is PN
calibration (see `docs/UNRESOLVED_ITEMS.md`); the 2–10 keV band is the
production band for Fe K-alpha work.

## 2026-11-17 response cross-check

The open question was whether the remaining ~2.0 reduced chi-square at
0.7–10 keV is caused by the response matrix.  It is not:

| response | 0.5–10 keV | 0.7–10 keV | 2–10 keV |
|---|---:|---:|---:|
| CCF PN v22.0 | 2.35 | **2.05** | 1.98 |
| CCF PN v21.0 | 2.35 | **2.05** | 1.98 |

PN-only, `tbabs*zpowerlw`, PPS `SRSPEC0001` + `SRCARF0001` + `BGSPEC0001`,
XSPEC 13.0 in the `xmm_xspec` image.  v22.0 is already the matrix used by the
production path, and v21.0 (the SAS 21 era) gives the same result.  The repo's
raw 20" reduction reports 1.58 at 0.5–10 keV with the same v22.0 matrix, so the
remaining difference is aperture/background/pile-up, not the RMF.  Rebuilding
`epn_e2_lw20_sdY9.rmf` with `rmfgen` cannot close this residual.

## Limits

- PPS products, not a raw `epproc`/`especget` reduction (the raw product is
  `../xmm_sas_raw/`).
- PN/MOS Gamma differ by 2.9 sigma; quote the narrow-core line flux/EW, not a
  spin or relativistic profile.
- The broad Fe K-alpha width is degenerate with continuum curvature and is not
  a resolved velocity.
- Errors are XSPEC covariance 1-sigma; no MCMC.
