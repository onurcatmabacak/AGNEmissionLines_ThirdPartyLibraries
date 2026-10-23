# Caveat fixes and residual limitations

## Solved or materially improved

| limitation | fix | current validation |
|---|---|---|
| PDS 456 PAHFIT long/both unstable | Fixed the `(1+z)` residual normalization; added `--init-from`; seeded long from a 15.4–18 µm fit and both from short; corrected the instrument metadata | short/long/both rms = 0.261/0.118/0.105; all stable; full 6.5–28.6 µm data still has missing sub-bands |
| FIR low-S/N bias | Use local pixel spacing near each line, not the global 30–300 µm spacing; two-pass S/N-weighted velocity-width tie for S/N<5 lines | synthetic OI63 498/500, OIII88 911/1000, NII122 347±67/300, CII158 1942±153/2000; median recovered/truth 0.983 (p=0.88) |
| C III] broad excess | Added satellites; C III] maxsig 0.015→0.008; Hβ 0.05→0.02; extra Fe II-free continuum windows; reject out-of-coverage and absorption outliers | C III] total/ZLINE = 1.33, 1.76, 1.29; narrow is separately reported and is not a reliable independent flux |
| NGC 4151 PAHFIT unstable | The IRS table is point-source calibrated; divide all orders by **one common aperture solid angle**, not different SL/LL slit areas | rms 0.65→0.065; stable; [Ne III]/[Ne II]=2.32 (replaces the spurious 0.059); [C II]/[N II]=12.17; S IV/Ne II=0.99 |
| NIR single/decentred extraction | Use cube WCS/PC matrix, auto centroid, PSF-weighted r=3 aperture, annulus background, propagated errors | PSF extraction: broad Hα S/N≈34, FWHM≈10,100 km/s; broad Hβ S/N≈4; 3×3 and pipeline retained for regression |
| Cross-band synthetic only | Real NGC 253 and real AGN NGC 4151 MIR+FIR; S IV/Ne II same-slit ratio | 15/15 ratios within broad priors in the current matrix |
| CIGALE nominal errors | Real SDSS `SPECTROFLUX_IVAR` and matched AllWISE errors | CIGALE rerun with real errors; no invented errors |
| No AGNfitter-RX | Public AGNfitter 2.0/AGNfitter-rx image, 8 bands, ultranest | 5/5 QSOs; compact medians/posteriors |
| Mrk 231 PACS no standard FIR line | Removed the non-informative PACS/FIR entry | Mrk 231 remains a real MIR-only AGN test |
| NGC 253 starburst cross-band | Added real Seyfert 1 NGC 4151 | NGC 4151 now the AGN cross-band validation |

## Residual limitations

* **PDS 456** x1d files contain only four MRS sub-bands; 56 % of 6.5–28.6 µm is
  absent.  The fit is stable but gap-limited; full short/medium data are needed
  for a complete MIR census.
* **NGC 253 PAHFIT** is still flagged (rms≈11.5 after the common-aperture fix);
  it is a starburst stress test, not the AGN pass gate.
* **C III] broad** remains blend-limited; the broad component is real, but the
  narrow/C III] comparison is not a clean one-number test.
* **PROSPECTOR-AGN** is not integrated.  The public `bd-j/prospector` main branch
  has the AGN BBB/torus components, but requires FSPS (~2.3 GB); with only eight
  bands the non-parametric host is unconstrained.  AGNfitter-RX + CIGALE supply
  the current model-family spread.
* **NIR** extraction is PSF-weighted r=3, not a full wavelength-dependent PSF
  fit or a joint background model.
* CIGALE/AGNfitter remain photometry-only; no X-ray/radio constraints.
