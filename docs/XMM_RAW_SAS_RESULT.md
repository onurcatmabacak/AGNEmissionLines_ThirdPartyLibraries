# Raw XMM-Newton SAS reduction — PDS 456 PN

This is a real raw-ODF cross-check of the official PPS result.  It is not a
replacement for the joint PN+MOS PPS fit.

## Provenance

| item | value |
|---|---|
| ObsID | `0721010201` |
| ODF | XMM-Newton Science Archive, `level=ODF`, 297 MB (not committed) |
| SAS | 22.1.0, `xmmsas_22.1.0-a8f2c2afa-20250304` |
| HEASoft | existing XSPEC 13.0.0 base |
| CCF | `valid/` CCF, 2.8 GB, CIF built with `cifbuild` |
| Events | `epproc instexpids=PNS003`, full run, exit 0 |
| Extraction | `especget`, final `*_ImagingEvts.ds`, PN only |
| Source region | `circle(26851.0,27749.8,400)` = 20″ |
| Background | `annulus(26851.0,27749.8,800,1200)` = 40–60″ |
| RMF | `epn_e2_lw20_sdY9_v22.0.rmf` (CCF v22.0) |
| ARF | SAS `arfgen` |

## Known SAS trap

Do **not** use the intermediate `*_Evts.ds`.  It lacks the finalized
`STDGTI/EXPOSU` structure; `evselect` computes `EXPOSURE=inf` and CFITSIO
raises `bad float to string conversion`.  Use the final
`*_ImagingEvts.ds` from a completed `epproc`; then `especget` succeeds.

## Fit

`tbabs*zpowerlw` at 0.5–10 keV:

- χ²/dof = **3004.37/1901 = 1.58**
- Γ = **2.100**
- N_H = **2.48 × 10²¹ cm⁻²**

Adding a fixed 50 eV Fe Kα at 6.4 keV rest:

- χ²/dof = **2990.34/1900**
- **Δχ² = 14.03 (1 dof, 3.74σ)**
- flux = **(2.15 ± 0.57) × 10⁻¹⁴ erg cm⁻² s⁻¹**

The official joint PPS PN+MOS result is **16.39 (4.05σ)** and
**2.01 × 10⁻¹⁴ erg cm⁻² s⁻¹**.  The raw PN-only cross-check is consistent
within the different extraction/filter choices.

## Limits

- PN-only, not joint PN+MOS.
- 20″ custom region, not PPS 40″.
- CCF v22.0 RMF with a SAS 22.1 reduction.
- Pile-up/pattern optimization and `epatplot` are not final.
- The fit assumes the same absorbed power-law model as the PPS path; this is a
  reduction cross-check, not an independent physical model.

Products: `outputs/PDS456_z_0.1840/xmm_sas_raw/`.
