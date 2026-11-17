# `configs/nustar_xspec/default/`

NuSTAR 3–79 keV configuration for NGC 1365.

| key | meaning |
|---|---|
| `band_keV` | observed-frame 3–79 keV fit band |
| `line_energy_keV` | Fe K-alpha rest energy, 6.4 keV |
| `nH_1e22` | starting cold absorption, 10^22 cm^-2 |
| `source_region` | RA, Dec and 60" radius for `nuproducts`/`numkarf` |

**Observation:** use full-frame ObsID `60002046002` (36.3 ks).  The older
`60002046001` is a 32x32 subframe exposure with `X/Y = -1`; `numkrmf` cannot
select detector pixels from it.  The product is FPMA+FPMB with local
background subtraction; see `outputs/nustar_xspec/NGC1365_z_0.0035/`.

**Response caveat:** the `numkarf` ARFs in the committed product have the
PSF/vignetting/aperture/ghost/detabs corrections disabled; a free
FPMB/FPMA cross-calibration joint fit is still open.  Do not quote the flux or
normalization as final.
