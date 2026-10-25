# PDS 456 — real UV spectrum for the X-ray/UV line comparison

`raw/hst_8264_stis_pds456_sg140l-sg230l_o58s_cspec.fits` is the public
**HST/STIS G140L+G230L** HASP `cspec` product from MAST.  It is a single,
flux-calibrated spectrum covering **1140–3137 Å** (observed), with the two
STIS orders already merged by the Hubble Spectroscopic Legacy Archive.

- Proposal: HST 8264 (PI P. O'Brien), "PDS 456: A radio-quiet analogue of 3C 273"
- Observation: 2000-09-15, total 1921 s (FUV 1140 s + NUV 781 s)
- Aperture: 52×0.5 arcsec; gratings G140L + G230L
- Calibration: HASP HSLA Cal 1.2.4; `LICENSE = CC BY 4.0`
- MAST product: `mast:HST/product/hasp/hst_8264_stis_pds456_sg140l-sg230l_o58s_cspec.fits`
- SHA-256: `d6567d80cef6b515c006aec17ee20c6f18363fb88bde273f67cfde43f12c83c8`

The spectrum is used for the rest-frame **Lyα/N V, C IV 1549 and C III] 1909**
measurements in `pyqsofit_uv`.  It does **not** cover Hβ or Mg II: at z=0.184
Hβ is at 5758 Å and Mg II at 3315 Å, both redward of the STIS range.  The
X-ray/UV comparison therefore uses C IV, not Hβ, for PDS 456.  The JWST/MIRI
spectra remain the IR branch.

Reproduce with:

```bash
bash inputs/PDS456_z_0.1840/download_optical.sh
```
