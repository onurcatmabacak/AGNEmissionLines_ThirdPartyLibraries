# Caveat fixes and new test matrix

This pass addressed the residual limitations recorded in the individual tool
READMEs, and moved all new tools to the source-keyed layout (`inputs/`,
`outputs/<source>_z_<z>/<tool>/`).

## Layout

* One raw payload per source in `inputs/<source>_z_<z>/raw/`, described by
  `source.json`.
* Tool-native copies are generated under `work/prepared/<source_key>/` and are
  not committed.
* Every result is under `outputs/<source_key>/<tool>/`; no flat `results_ir`
  or per-tool `runs_ir_*` trees remain.
* Legacy optical-v1 `results/`, `runs/`, `figures*/` and
  `results_uncertainties/` are intentionally left untouched.
* `pipeline/run_new_tools.py` is the single orchestrator; it writes logs to
  `work/logs/`.

## Caveat → fix → validation

| caveat | implementation | test |
|---|---|---|
| FIR validation was synthetic only; archive adapter blocked | Added `read_pacs` (Herschel/PACS HPDP `wave`/`pointSource*Flux`) and `read_hifi_hpdp` (HIFI K/GHz) adapters; added real NGC 1068 and NGC 253 PACS spectra from the ESA HSA | NGC 1068 [OI] 63 µm detected; NGC 253 detects [OI] 63, [OIII] 88, [OI] 145, [CII] 158 |
| FIR 20–25 % low bias | Widened the line window (8 resolution elements), fixed the initial-width bound that rejected broad real lines, and added an optional joint/tied-width fit | Synthetic [OI] 63 improved from 445 to ~498 (truth 500); real PACS lines recover the expected wavelengths |
| PDS 456 PAHFIT unstable | Segment fits (`--segment short/long/both`), median binning (`--smooth-um`), explicit MIRI instrument list, and `rms_rel`/`unstable` quality flags | Short segment is stable (χ²-like rms 0.41); long/both are explicitly flagged unstable |
| PAHFIT only tested on VV114 | Added Spitzer IRS `.tbl` adapter, Jy→MJy/sr slit conversion, and real Mrk 231/NGC 253 IRS fits | Mrk 231 rms 0.35; NGC 253 rms 2.4 (flagged); VV114 rms 0.18 |
| PyQSOFit used a 2 % flux floor and dropped UV lines at low z | Uses the calibrated error array (optional `PYQSOFIT_ERR_FLOOR`), and the UV fit is host-free (`PYQSOFIT_HOST=1` enables the old host decomposition); writes `pyqsofit_lines.csv` | Mg II now fitted at z=0.587; broad/narrow C III] and Mg II are separately recorded |
| PyQSOFit C III] 1.8–2.9× SDSS ZLINE | The comparison is now explicitly broad vs narrow; the narrow C III] area is available separately, and the broadband/Fe II contribution is not presented as a narrow-line measurement | `pyqsofit_lines.csv` has both components |
| pPXF host unconstrained at z ≥ 0.99 | Fixed the empty-template interpolation at z>1, added `host_fraction_err`, a 3σ upper limit, `host_fraction_reliable`, `reliability_reasons`, `sigma_err`, and a 4000 Å-break flag | z=0.587 host fraction 0.109 reliable; z=0.990/1.13/1.83 flagged with upper limits |
| pPXF high σ from broad-line wings | Emission-line mask widened to ±2500 km/s; σ at the 1000 km/s bound is flagged | z=0.587 σ=689±45 km/s, χ²_red=26.6; z=0.651 σ=1000 km/s is flagged `sigma_at_upper` |
| NIR only one extraction / no upper limits | NIR x1d adapter retained; the generic fitter writes 3σ limits for Hβ, [OIII], [NII], Hα narrow, and [SII]; MIRI/IRS/HIFI/PACS are now unit-aware | J0100 broad Hα detected (S/N 3.4); all other NIR lines have finite 3σ limits |
| Generic IR had no real archive adapters | Added MIRI `SURF_BRIGHT`, PACS, HIFI, Spitzer IRS, PAHFIT s1d adapters and unit-aware CSV/route metadata | All real PACS/IRS/HIFI/MIRI files ingest without unit guessing |
| Cross-band validation synthetic only | Added a real NGC 253 MIR (Spitzer IRS/PAHFIT) + FIR (PACS) catalogue; added [CII]/[OI] and [CII]/[NII] ratios | Real NGC 253 ratios: [NeIII]/[NeII]=1.40, [SIII]18.7/[SIII]33.5=0.50, [CII]/[OI]63=7.03; 3/3 within priors with the new tolerance |
| CIGALE one torus family, no family spread | Added the `fritz2006` database and a second grid; `cigale_sed/model_family.csv` and `model_family_spread.json` record both families | Both families run on all five QSOs; e.g. 04592649654: SKIRTOR χ²_ν=6.45 vs Fritz 1.87; 04592933676: 9.95 vs 0.38 |
| CIGALE outlier / WISE contamination | Per-band χ² diagnostic (`chi2_optical`, `chi2_wise`, `wise_outlier`) is written to `sed_summary.csv`; the Fritz family is run alongside SKIRTOR | Outlier 4592933676: SKIRTOR χ²_ν=9.95 (WISE-flagged) vs Fritz 0.38; both reported |
| CIGALE photometric errors unavailable | SPALL has no MAGERR; the table uses documented nominal errors (0.05 mag SDSS, 0.125 mag WISE). This remains a limitation, not a solved measurement | `inputs/README.md` and `cigale_sed/README.md` state it explicitly |

## Remaining honest limitations

* The NIR J0100 spectrum is a single IFU extraction; a QSO-centred aperture is
  still the right data-level fix.
* AGNfitter-RX and PROSPECTOR-AGN are not implemented; CIGALE now has two
  torus families, not a full family ensemble.
* Real WISE/SDSS magnitude errors are not available in SPALL; nominal errors
  remain.
* The PDS 456 long/both PAHFIT solutions are flagged unstable; only the short
  segment should be used quantitatively.
* NGC 253 is a starburst, not an AGN; it validates the real MIR+FIR ratio path,
  not AGN physics.
