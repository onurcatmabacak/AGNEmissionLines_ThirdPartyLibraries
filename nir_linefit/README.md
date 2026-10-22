# nir_linefit — NIR emission-line tool (Docker)

The next IR-suite tool: the `pipeline_ir` coverage router + local-Gaussian
fitter, extended with a **JWST/NIRSpec x1d adapter** and packaged as the
Docker image `nir_linefit`.

## Build / run

```bash
bash pipeline/build_images.sh nir_linefit
bash run_nir_linefit_docker.sh input_nir results_ir/nir_j0100 6.327
```

Input: a JWST `EXTRACT1D` x1d FITS (WAVELENGTH [µm], FLUX/FLUX_ERROR [Jy],
DQ), or an SDSS-style spectrum. `FLUX` is converted to 1e-17
erg s-1 cm-2 A-1; DQ≠0 pixels are masked. `z` can be passed explicitly when the
header has no redshift.

## Test: SDSS J0100+2802 at z=6.327 (JWST/NIRSpec G395H)

`input_nir/jw01218-o002_t002_nirspec_g395h-f290lp_x1d.fits`
(NIRSpec/IFU, 2.87–5.27 µm, 3610 pixels).

The router correctly places the rest-frame optical lines in the NIR band:

| line | observed (µm) | suite | measurable |
|---|---:|---|---|
| Hβ 4861 | 3.563 | nir | yes |
| [O III] 4959/5007 | 3.634/3.670 | nir | yes |
| Hα 6563 | 4.810 | nir | yes |
| [N II] 6548/6585 | 4.799/4.825 | nir | yes |
| [S II] 6718/6732 | 4.922/4.933 | nir | yes |

The fit detects **broad Hα at 4.81 µm** (flux 889 in 1e-17 units, FWHM
≈ 10,100 km/s, S/N 3.4, χ²_red 18). Hβ/[O III] are weak/absent in this
single IFU extraction, so only Hα clears the 3σ threshold. The spectrum also
has a deep absorption/gap near 4.1 µm; it is masked by the DQ cut.

**Inspect:** `results_ir/nir_j0100/SDSS_J0100+2802.png` / `.pdf`,
`SDSS_J0100+2802.measurements.csv`, `.route.json`.

## Caveats

- One IFU extraction only; a QSO-centred aperture or a different reduction may
  recover Hβ/[O III] and a narrower Hα core.
- The broad Hα is fitted with the generic local-Gaussian model; no
  telluric/PAH/AGN-continuum model yet.
- The 4.1 µm absorption/gap is a data-quality feature, not a line.
