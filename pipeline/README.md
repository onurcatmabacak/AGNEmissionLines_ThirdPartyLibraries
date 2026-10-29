# `pipeline/` — orchestration library and Docker runners

One tree, two layers:

* top level — Python: layout helpers, input adapters, matrix runner, validators,
  comparisons and report generators;
* `runners/` — the bash entry points that wrap each Docker image (previously the
  separate top-level `Pipelines/` directory).

Python code here calls into `runners/` only through `pipeline/tool_registry.py`;
the runners never import Python.

```text
pipeline/
  io_layout.py, run_new_tools.py, validate_outputs.py, ...   # Python layer
  runners/
    run_galspec_line_docker.sh, run_qgfit_docker.sh, ...      # Docker wrappers
    build_images.sh, record_image_digests.sh
    _output_layout.sh                                         # shared path helper
    legacy_optical/                                           # archived optical v1
```

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
bash pipeline/runners/run_new_tools.sh --list
bash pipeline/runners/run_new_tools.sh --cigale-models skirtor2016,fritz2006
.venv/bin/python pipeline/statistical_tests_new_tools.py
```

The original optical pipeline is archived at
`pipeline/runners/legacy_optical/`; its old `input/`, `runs/`, `results/` layout is not
used by this library anymore.
