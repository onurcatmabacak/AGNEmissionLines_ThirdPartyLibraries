# `outputs/` — canonical result store

Every result lives under exactly one source and one tool:

```text
outputs/
  <source_name>_z_<redshift>/
    <tool_name>/
      ... files ...
```

There are no flat result directories for the new tools.  The old `results_ir/`,
`runs_ir_zgt05/`, `input_*`, `results/`, `runs/`, `figures*/`,
`results_uncertainties/`, and `statistical confirmation/` trees were migrated
into `outputs/` (20 optical production sources + the new-tool sources) and
deleted.  `docs/legacy_optical/` retains only aggregate legacy tables.

Tools and expected files:

| tool | files |
|---|---|
| `ir_linefit` | `*.route.json`, `*.measurements.csv`, `*.fit.png/pdf` |
| `pyqsofit_uv` | `result.png/pdf`, `output.fits`, `qsopar.fits`, `pyqsofit_model.csv`, `pyqsofit_lines.csv` |
| `ppxf_host` | `ppxf_fit.png/pdf`, `ppxf_model.csv`, `ppxf_result.fits`, `ppxf_summary.json` |
| `gandalf_line` | `gandalf_lines.csv`, `gandalf_fit.png/pdf`, `gandalf_uncertainty.png/pdf`, `gandalf_fit.fits`, `gandalf_input.fits`, `gandalf_model.csv`, `run.json` |
| `nir_linefit` | route/measurements/figure for the NIR spectrum |
| `pahfit_mir` | `pahfit_fit.png/pdf`, `pahfit_features.csv`, `pahfit_lines.csv`, `pahfit_output.ecsv`, `pahfit_summary.json`, MC products; PDS 456 has `short/`, `long/`, `both/`, `short_covariance/` |
| `cafe_line` | `cafe_fit.png/pdf`, `cafe_lines.csv`, `cafe_key_lines.csv`, `cafe_pah.csv`, `cafe_uncertainties.csv`, `cafe_uncertainty.png`, `run.json` |
| `s3fit_line` | `s3fit_fit.png`, `s3fit_mc.png`, `s3fit_lines.csv`, `s3fit_output.npz`, `pyqsofit_comparison.csv`, `run.json` |
| `galspec_line` | `galspec_lines.csv`, `galspec_fit.png/pdf`, `galspec_corner.png/pdf`, `galspec_uncertainty.png/pdf`, `galspec_mcmc.npz`, `run.json` |
| `pyqsofitspec_line` | `pyqsofitspec_lines.csv`, `pyqsofitspec_bootstrap.png/pdf`, `pyqsofitspec_corner.png/pdf`, `pyqsofitspec_out.csv`, `run.json` |
| `qgfit` | `qgfit_lines.csv`, `qgfit_fit.png/pdf`, `qgfit_uncertainty.png/pdf`, `qgfit_mcmc_summary.csv`, `run.json` |
| `sheap_line` | `sheap_lines.csv`, `sheap_model.csv`, `sheap_fit.png/pdf`, `sheap_zoom_hbeta.png/pdf`, `sheap_zoom_oiii.png/pdf`, `sheap_residual.png/pdf`, `sheap_uncertainty.png/pdf`, `sheap_mc_samples.csv`, `sheap_systematics.csv` (audit runs), `run.json` |
| `galspec_line` | `galspec_lines.csv`, `galspec_fit.png/pdf`, `galspec_uncertainty.png/pdf`, `galspec_corner.png/pdf`, `galspec_model.csv`, `galspec_mcmc.npz`, `galspec_comparison.csv`, `config.effective.json`, `run.json` |
| `fir_linefit` | `*.fir_lines.csv`, `*.fir_fit.png/pdf`, `*.fir_summary.json` |
| `crossband` | `crossband_ratios.csv`, `crossband_summary.json`, `crossband_ratios.png/pdf` |
| `cigale_sed` | `model_family.csv`, `model_family_spread.json`, and `skirtor2016/` + `fritz2006/` subdirectories with CIGALE outputs |
| `agnfitter_sed` | `agnfitter_summary.csv`, `sed_summary.json`, `parameter_outvalues`, `SED_manyrealizations` PDF |
| `pyqsofit_uv` (MC) | `mc/pyqsofit_mc_samples.csv`, `mc/pyqsofit_mc_summary.csv`, `mc/pyqsofit_mc.png` |

Run the matrix with:

```bash
.venv/bin/python pipeline/run_new_tools.py --list
.venv/bin/python pipeline/run_new_tools.py \
  --cigale-models skirtor2016,fritz2006
```

The runner writes logs to `work/logs/<source_key>/<tool>.log`; neither
`work/prepared/` nor `work/logs/` is committed.
