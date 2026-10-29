# `Tools/`

Dockerized fitting engines and their Dockerfiles.  See `Pipelines/build_images.sh`.

| directory | image |
|---|---|
| `badass/` | `badass` |
| `fantasy_agn/` | `fantasy_agn` |
| `Gelato/` | `gelato` |
| `Gleam/` | `gleam` |
| `pipeline_ir/` | `ir_linefit` |
| `pyqsofit_uv/` | `pyqsofit_uv` |
| `ppxf_host/` | `ppxf_host` |
| `gandalf_line/` | `gandalf_line` (native GANDALF v1.5 under GDL) |
| `nir_linefit/` | `nir_linefit` |
| `pahfit_mir/` | `pahfit_mir` (PAH/dust/gas + MC) |
| `cafe_line/` | `cafe_line` (CAFE NIRSpec/MIRI decomposition + covariance MC) |
| `s3fit_line/` | `s3fit_line` (S3Fit spectrum+SED + mock-spectrum MC) |
| `galspec_line/` | `galspec_line` (GalSpec Gaussian lines + emcee/dynesty) |
| `pyqsofitspec_line/` | `pyqsofitspec_line` (skew-normal lines + bootstrap) |
| `qgfit/` | `qgfit` (AGN/host/Fe II + continuum MCMC) |
| `sheap_line/` | `sheap_line` (SHEAP JAX AGN decomposition) |
| `optical_linefit/` | `optical_linefit` (local Hβ/[O III] joint fit) |
| `qsofitmore_line/` | `qsofitmore_line` (UV/optical QSOFITMORE) |
| `manga_dap/` | `manga_dap` (official MaNGA DAP) |
| `xmm_xspec/` | `xmm_xspec` (XMM EPIC PPS + PyXspec) |
| `rxte_xspec/` | `rxte_xspec` (RXTE PCA stdprod + PyXspec) |
| `fir_linefit/` | `fir_linefit` |
| `crossband/` | `crossband` |
| `cigale_sed/` | `cigale_sed` |
| `agnfitter_sed/` | `agnfitter_sed` |
| `pyqsofit/` | local PyQSOFit source, no image |
| `sculptor/` | legacy GUI-only source, no image |

## Post-processing (not a third-party fit)

`pipeline/compare_xray_optical.py` writes `outputs/crossmission/<source>/` and compares the
X-ray Fe K-alpha fit with the same object's H-beta or C IV line. It is not a Docker image
because it only reads committed tool outputs and performs arithmetic/plotting.
