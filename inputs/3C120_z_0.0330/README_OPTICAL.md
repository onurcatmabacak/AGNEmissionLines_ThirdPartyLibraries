# 3C 120 — real optical spectrum for the X-ray/optical line comparison

`raw/hst_8700_stis_3c120d0_g430l-g750l_o62o_cspec.fits` is the public
**HST/STIS G430L+G750L** HASP `cspec` product from MAST.  It covers
**2993–10247 Å** (observed), i.e. rest-frame 2897–9919 Å at z=0.03301:
Hγ, Hβ, [O III] 4959/5007, Hα, [N II] 6548/6584 and [S II] 6716/6731.

- Proposal: HST 8700 (PI A. Martel), HST/STIS spectroscopy of 3C 120
- Observation: 2000-09-09, 1440 s total (G430L 720 s + G750L 720 s)
- Aperture: 52×0.2 arcsec; CALSTIS 3.4.2/3.5.0; HASP HSLA Cal 1.2.4
- `LICENSE = CC BY 4.0`
- MAST product: `mast:HST/product/hasp/hst_8700_stis_3c120d0_g430l-g750l_o62o_cspec.fits`
- SHA-256: `f0f1bbb19124ea01233922c2c633c6abcc8e44e25b9c59d387d692f427fecde2`

The spectrum is fitted with `pyqsofit_uv` for the broad Hβ and narrow
[O III] 5007 measurements used in the RXTE Fe Kα comparison.  The G750L part
also covers Hα, which is reported as a consistency line but not used for the
Fe Kα correlation.

Reproduce with:

```bash
bash inputs/3C120_z_0.0330/download_optical.sh
```
