# PDS 456 — real optical/UV spectra for the X-ray/optical line comparison

This source has **two** public spectra, because no single archive spectrum
covers both the UV and H-beta at z=0.184.

1. **ESO VLT/X-SHOOTER VIS**, `raw/ADP.2023-04-20T08:25:01.842_XSHOOTER_VIS.fits`
   - 5336.6–10200 Å observed, 2416 s, MJD 60049
   - public reduced `SFLX` product, programme `111.24T0.001`
   - covers Hβ 5758 Å, [O III] 4959/5007, Hα and [N II]/[S II]
   - SHA-256 `872a8aad...bea3e9`
2. **HST/STIS G140L+G230L**, `raw/hst_8264_stis_pds456_sg140l-sg230l_o58s_cspec.fits`
   - 1139–3137 Å observed, 1921 s
   - HASP `cspec`, HST proposal 8264 (PI P. O'Brien), CC BY 4.0
   - covers Lyα/N V, C IV 1549, C III] 1909
   - SHA-256 `d6567d80...2c83c8`

The original HST-only analysis could not measure Hβ (5758 Å) or Mg II
(3315 Å), so its C IV result was tentative.  The **X-SHOOTER VIS** spectrum
removes that limitation: `pyqsofit_uv` now measures Hβ and [O III] directly.
The HST UV spectrum is retained as `uv_spectrum` for C IV context and for
future multi-line work.

Reproduce both files with:

```bash
bash inputs/PDS456_z_0.1840/download_optical.sh
```

The JWST/MIRI spectra remain the IR branch.
