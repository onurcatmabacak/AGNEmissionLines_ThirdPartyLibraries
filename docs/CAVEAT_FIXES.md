# Caveat fixes and validation matrix

This pass addresses the remaining limitations with data/model changes, not just
notes.  All new tools use the source-keyed layout (`inputs/`, `outputs/`).

## Layout

* One raw payload per source in `inputs/<source>_z_<z>/raw/`, described by
  `source.json`.
* Tool-native copies are generated under `work/prepared/<source_key>/`; they
  are not committed.
* Every result is under `outputs/<source_key>/<tool>/`.
* Legacy optical-v1 `results/`, `runs/`, `figures*/` etc. are untouched.
* `pipeline/run_new_tools.py` is the single orchestrator; logs go to
  `work/logs/`.

## Caveat → fix → validation

| caveat | implementation | test |
|---|---|---|
| FIR validation was synthetic only | `read_pacs`/`read_hifi_hpdp` adapters; real PACS products from the ESA HSA | NGC 1068 [OI]63; NGC 253 [OI]63/[OIII]88/[OI]145/[CII]158; NGC 4151 [OIII]88/[NII]122/[OI]145/[CII]158 |
| FIR low-S/N bias | Widened the default window to 8 resolution elements; fixed the initial-width bound that rejected broad lines | Synthetic [OI]63 improved 445→498 (truth 500); low-S/N [NII]/[CII] still show a ~20 % Gaussian-width bias (documented) |
| PDS 456 PAHFIT unstable | Segment short/long/both, median binning, channel-specific MIRI instrument lists, `rms_rel`/`unstable` flags | Short is stable (rms 0.41); long/both are explicitly flagged (0.84/2.05) and are not used quantitatively |
| PAHFIT only validated on VV114 | Spitzer IRS `.tbl` adapter, Jy→MJy/sr slit conversion, real Mrk 231/NGC 253/NGC 4151 fits | VV114 rms 0.18; Mrk 231 0.35; NGC 4151 0.60 (flagged); NGC 253 2.4 (flagged) |
| PyQSOFit used 2 % flux floor and dropped UV lines | Calibrated errors by default; host-free UV fit; `PYQSOFIT_HOST=1` restores host decomposition | Mg II recovered at z=0.587; `pyqsofit_lines.csv` records broad and narrow components |
| PyQSOFit C III] high vs SDSS ZLINE | Added Si III]/Al III/Si II/Fe II/N III satellites; tightened C III] broad-width prior; report broad and narrow separately | Total C III]/ZLINE drops from 1.5–2.9 to ~1.45–2.0; narrow C III] remains 0.005–0.06 of ZLINE; broad component still includes Fe II/outflow |
| pPXF host unconstrained at high z | Template interpolation fix; host errors/upper limits; reliability reasons; 4000 Å-break and σ-bound flags | z=0.587 host 0.109 reliable; z=0.651 host 0.127 but σ at 1000 km/s flagged; z≥0.99 upper limits |
| NIR single extraction | Public JWST `s3d` cube + QSO-centred 3×3 extraction (`pipeline/extract_nir_aperture.py`); raw cube not committed, derived table committed | Centred: broad Hα S/N≈25 (pipeline x1d S/N≈3.4), narrow Hα/[N II], broad Hβ S/N≈3 |
| Generic IR had no real adapters | MIRI SURF_BRIGHT, PACS, HIFI, Spitzer IRS, PAHFIT s1d adapters; unit metadata | All real data ingest without unit guessing |
| Cross-band synthetic only | Real NGC 253 MIR+FIR and real AGN NGC 4151 MIR+FIR catalogues; [CII]/[OI] and [CII]/[NII] ratios | NGC 253 3/3; NGC 4151 [CII]/[NII]=12.2 (consistent); [NeIII]/[NeII]=0.059 is retained/flagged |
| CIGALE one torus family | Added `fritz2006`; `model_family.csv` and spread | 04592933676: SKIRTOR χ²_ν=19.2 (WISE-flagged) vs Fritz 0.72 |
| CIGALE photometric errors nominal | Real SDSS `SPECTROFLUX_IVAR` errors and matched AllWISE errors cached in `inputs/catalogs/photometry_errors.json`; nominal fallback only | CIGALE rerun with real errors; fit quality is lower but no longer artificially optimistic |
| No AGNfitter-RX | Added `agnfitter_sed` Docker image using public AGNfitter 2.0 (AGNfitter-rx release); 8-band fit, ultranest, compact summary | All five SDSS QSOs fitted; `agnfitter_summary.csv` and SED realization PDF |
| Mrk 231 PACS has no standard FIR line | Removed FIR from Mrk 231; moved real AGN FIR+MIR validation to NGC 4151 | NGC 4151 real 4-line FIR detection and MIR fit |
| NGC 253 is a starburst, not an AGN | Added real Seyfert 1 NGC 4151 (Spitzer IRS + PACS) as the AGN cross-band test | NGC 4151 [CII]/[NII]=12.17 consistent; [NeIII]/[NeII] flagged |

## Remaining limitations

* PDS 456 long/both PAHFIT remains data-limited (MRS calibration/short-long
  gap) and is flagged; only the short segment is quantitative.
* The FIR Gaussian flux still has a ~20 % low bias for the lowest-S/N synthetic
  lines; a model-independent aperture did not improve it, so it is not used.
* C III] broad remains blended with Fe II/outflow; narrow C III] is the
  comparable quantity, not the broad total.
* PROSPECTOR-AGN is still not integrated; **AGNfitter-RX** now is.
* NGC 4151 PAHFIT is flagged unstable (rms 0.60); its FIR and CII/NII ratio are
  the reliable parts of the cross-band test.
* The NIR extraction is 3×3, not a full PSF/aperture optimisation.
