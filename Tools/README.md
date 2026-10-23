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
| `pyqsofitspec_line/` | `pyqsofitspec_line` (PyQSOFitSpec skew-normal + parametric bootstrap) |
| `ppxf_host/` | `ppxf_host` |
| `gandalf_line/` | `gandalf_line` (native GANDALF v1.5 under GDL) |
| `nir_linefit/` | `nir_linefit` |
| `pahfit_mir/` | `pahfit_mir` (PAH/dust/gas + MC) |
| `cafe_line/` | `cafe_line` (CAFE NIRSpec/MIRI decomposition + covariance MC) |
| `s3fit_line/` | `s3fit_line` (S3Fit spectrum+SED + mock-spectrum MC) |
| `galspec_line/` | `galspec_line` (GalSpec reduced H-beta/[O III] + emcee/dynesty) |
| `fir_linefit/` | `fir_linefit` |
| `crossband/` | `crossband` |
| `cigale_sed/` | `cigale_sed` |
| `agnfitter_sed/` | `agnfitter_sed` |
| `pyqsofit/` | local PyQSOFit source, no image |
| `sculptor/` | legacy GUI-only source, no image |
