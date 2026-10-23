# `pipeline/` — Python library and orchestration

This is the implementation layer used by `Pipelines/run_new_tools.sh` and the
source-keyed matrix.  It is not a second set of shell entry points.

Key modules:

| module | purpose |
|---|---|
| `io_layout.py` | source keys, input/output paths, manifests |
| `run_new_tools.py` | matrix runner |
| `prepare_inputs.py` | tool-native input adapters |
| `build_photometry.py` | per-source CIGALE table from eFEDS photometry |
| `fetch_photometry_errors.py` | real SDSS/AllWISE errors |
| `extract_nir_aperture.py` | QSO-centred/PSF NIR cube extraction |
| `build_crossband_from_outputs.py` | real MIR+FIR cross-band catalogue |
| `compare_sed_families.py` | CIGALE vs AGNfitter comparison |
| `statistical_tests_new_tools.py` | tests and comparison figure |
| `validate_uv_zline.py` | PyQSOFit vs SDSS ZLINE table |

Run:

```bash
bash Pipelines/run_new_tools.sh --list
bash Pipelines/run_new_tools.sh --cigale-models skirtor2016,fritz2006
.venv/bin/python pipeline/statistical_tests_new_tools.py
```

The original optical pipeline is archived at
`Pipelines/legacy_optical/`; its old `input/`, `runs/`, `results/` layout is not
used by this library anymore.
