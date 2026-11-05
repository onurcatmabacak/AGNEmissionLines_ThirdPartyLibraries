# AUXILIARY ONLY — fast fixed-continuum mode

**Quality flag: `FASTMODE_NOT_PRODUCTION`. Do not use these files as the
production MaNGA DAP result.**

This directory contains the all-spaxel fast fixed-continuum SASUKE run on the
175 HYB10/S/N=50 bins.  It is useful as a diagnostic because it is fast and
shows the morphology, but it is **not** the official survey emission-line
model and it fails the acceptance comparison to the published MAPS:

| quantity | fast mode / published MAPS |
|---|---:|
| H-alpha median ratio | 2.37 |
| H-beta median ratio | 0.89 |
| [O III] 5007 median ratio | 1.01 |
| [N II] 6584 median ratio | 0.53 |
| BPT class agreement | 40.8% |
| H-alpha gas velocity offset | +175.5 km/s |

The fast mode fits the binned spectra with the pPXF continuum fixed and
reproduces the bin value on every spaxel; it does not perform the survey
per-spaxel deconstruction.  The large-bin H-alpha and [S II] fluxes are
therefore biased high and the [N II] flux is biased low.

The production/accepted result is in the parent directory: the official
full-method SASUKE fit on the 9 central single-spaxel bins, compared to the
published official MAPS as the all-spaxel reference.  See `../run.json`,
`../provenance.md` and `../comparison/`.

The FITS headers in `fits/` carry `QUALITY='FASTMODE_NOT_PRODUCTION'`,
`PRODSTAT='AUXILIARY'` and `ACCEPT=0`.
