# `outputs/` — canonical result store

Every result lives under exactly one source and one tool:

```text
outputs/
  <source_name>_z_<redshift>/
    <tool_name>/
      ... files ...
```

There are no flat result directories for the new tools.  `results_ir/`,
`runs_ir_zgt05/`, and the old `input_*` directories have been retired; the
legacy optical v1 `results/`, `runs/`, `figures*/` and `results_uncertainties/`
trees are deliberately left in place and are not part of the new layout.

Tools and expected files:

| tool | files |
|---|---|
| `ir_linefit` | `*.route.json`, `*.measurements.csv`, `*.fit.png/pdf` |
| `pyqsofit_uv` | `result.png/pdf`, `output.fits`, `qsopar.fits`, `pyqsofit_model.csv`, `pyqsofit_lines.csv` |
| `ppxf_host` | `ppxf_fit.png/pdf`, `ppxf_model.csv`, `ppxf_result.fits`, `ppxf_summary.json` |
| `nir_linefit` | route/measurements/figure for the NIR spectrum |
| `pahfit_mir` | `pahfit_fit.png/pdf`, `pahfit_features.csv`, `pahfit_output.ecsv`, `pahfit_summary.json`; PDS 456 has `short/`, `long/`, `both/` |
| `fir_linefit` | `*.fir_lines.csv`, `*.fir_fit.png/pdf`, `*.fir_summary.json` |
| `crossband` | `crossband_ratios.csv`, `crossband_summary.json`, `crossband_ratios.png/pdf` |
| `cigale_sed` | `model_family.csv`, `model_family_spread.json`, and `skirtor2016/` + `fritz2006/` subdirectories with CIGALE outputs |
| `agnfitter_sed` | `agnfitter_summary.csv`, `sed_summary.json`, `parameter_outvalues`, `SED_manyrealizations` PDF |

Run the matrix with:

```bash
.venv/bin/python pipeline/run_new_tools.py --list
.venv/bin/python pipeline/run_new_tools.py \
  --cigale-models skirtor2016,fritz2006
```

The runner writes logs to `work/logs/<source_key>/<tool>.log`; neither
`work/prepared/` nor `work/logs/` is committed.
