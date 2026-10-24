# Caveat fixes and residual limitations

## Solved or materially improved

| limitation | fix | current validation |
|---|---|---|
| PDS 456 PAHFIT long/both unstable | Fixed the `(1+z)` residual normalization; added `--init-from`; seeded long from a 15.4–18 µm fit and both from short; corrected the instrument metadata | short/long/both rms = 0.0088/0.118/0.105; all stable; the short fit now uses the internal median normalization and its χ²_ν=557 is still dominated by model mismatch; full 6.5–28.6 µm data still has missing sub-bands |
| FIR low-S/N bias | Use local pixel spacing near each line, not the global 30–300 µm spacing; two-pass S/N-weighted velocity-width tie for S/N<5 lines | synthetic OI63 498/500, OIII88 911/1000, NII122 347±67/300, CII158 1942±153/2000; median recovered/truth 0.983 (p=0.88) |
| C III] broad excess | Added satellites; C III] maxsig 0.015→0.008; Hβ 0.05→0.02; extra Fe II-free continuum windows; reject out-of-coverage and absorption outliers | C III] total/ZLINE = 1.33, 1.76, 1.29; narrow is separately reported and is not a reliable independent flux |
| NGC 4151 PAHFIT unstable | The IRS table is point-source calibrated; divide all orders by **one common aperture solid angle**, not different SL/LL slit areas | rms 0.65→0.031; stable; [Ne III]/[Ne II]=2.32 (replaces the spurious 0.059); [C II]/[N II]=12.17; S IV/Ne II=0.99; the PAHFIT feature table gives a related 3.39 Ne III/Ne II ratio |
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
* **CAFE PDS 456** has only four contiguous MIRI sub-bands; the fit is stable
  (rms 0.038) but only [Ne V] 14.3 µm is formally detected, so CAFE is a
  continuum/PAH decomposition here, not a full MIR line census.
* **S3Fit 04592649654** fits the SDSS spectrum with χ²_ν=4.76 and a 3-mock MC;
  the Mg II/Balmer/AGN continuum is good, but the default MC is small and the
  Hα/[N II] region is outside the SDSS coverage.  A longer `--n-mocks` run is
  provided for production.
* **GANDALF 04592649654** uses native GANDALF v1.5 under GDL, but pPXF rejected
  the stellar kinematics (σ at its 1000 km/s bound) and the gas fit used a fixed
  300 km/s stellar LOSVD.  The gas lines are native GANDALF/MPFIT measurements;
  the stellar σ is not a measurement for this AGN-dominated spectrum.
* **PyQSOFit MCMC** is implemented upstream but the line-complex `emcee`
  initialization fails its condition-number check on this source.  The
  committed uncertainty figure is a 100-realization MC, explicitly not MCMC.
* **GalSpec** now uses the full 2280–6460 A rest-frame model (global
  polynomial continuum + Fe II + Balmer/[O II]/[Ne III]/[O III] lines), not
  the reduced 4720–5150 A window.  The full MCMC run gives Hβ total 3718 and
  [O III] 5007 total 1681 (ratio 2.21); the narrow/broad split remains
  model-dependent.  The chain is 80 walkers × 4000 steps with
  `tau_max=342.6`, `nsteps/tau_max=11.7`, saved posterior 37,334 samples; it
  is a real full-model posterior but not a 50-tau publication chain.
* **PyQSOFitSpec** uses a 10-realisation bootstrap; its Hβ total is 3439,
  about 18% above GANDALF/S3Fit.  The bootstrap errors are statistical only.
* **QGfit** uses a short continuum MCMC and least-squares line errors; its
  Hβ/[O III] = 2.50, at the upper edge of the optical-tool spread.
* **SHEAP** originally gave Hβ/[O III] = 4.00 because its 4600-5150 Å /
  single-narrow / 600 km/s-cap / no-Fe-II model could not describe this object
  (χ²_ν = 46).  The 2026-08 audit replaced that model; the production fit now
  gives 2.02 with χ²_ν = 2.9 (see `docs/SHEAP_ASSESSMENT.md`).  A hard quality
  gate prevents a failing SHEAP fit from entering the cross-tool comparison.
* **Official SDSS DAPs** (MaNGA/LVM) require IFU cubes and are excluded from
  this single-fiber sample; **AMARU**, **ELFO**, **AGNdecompose**, **pyspeckit**
  and **HEASOFT** are excluded for the reasons in
  `docs/OFFICIAL_PIPELINES_AND_XRAY.md`.
* **PAHFIT** formal covariance/χ² errors are much smaller than the residuals
  (χ²_ν 557 PDS short, 304 NGC 4151); they are statistical only and do not
  include the dominant model mismatch.

* **PROSPECTOR-AGN** is assessed but not integrated: public `main` needs FSPS
  (~2.3 GB) and the eight-band host is unconstrained.  See
  `docs/PROSPECTOR_ASSESSMENT.md`; CIGALE + AGNfitter-RX supply the model-family
  spread.
* **NIR** extraction is PSF-weighted r=3, not a full wavelength-dependent PSF
  fit or a joint background model.
* CIGALE/AGNfitter remain photometry-only; no X-ray/radio constraints.
