# PROSPECTOR-AGN assessment

Subagent review of the public PROSPECTOR ecosystem:

- `bd-j/prospector` `main` is the only maintained public code with the
  AGN BBB/torus components (`agn_bbb`, `AGNSSPBasis`, `AGNPolySpecModel`).
- PyPI `astro-prospector==1.4.1` only has the classic torus (`agn_tau`), not
  the BBB/accretion-disk components needed for the QSO `griz` bands.
- A minimal image needs FSPS + `SPS_HOME` (~2.3 GB), a pinned `main` SHA, and
  dynesty; image size ≈3 GB, runtime 5–15 min/source.
- With only eight photometric bands, the non-parametric `AGNSSPBasis` host is
  unconstrained; host `M*`/SFR cannot be defended.

Decision: **not integrated** as a production tool in this pass.  The current
SED-family spread is CIGALE SKIRTOR + Fritz + AGNfitter-rx.  A future
PROSPECTOR run should be a separate, deliberately bounded **torus/BBB-only**
fit with host parameters fixed, not a full host+SED claim.
