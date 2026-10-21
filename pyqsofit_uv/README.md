# pyqsofit_uv — PyQSOFit UV line fitting (Docker)

The second IR/UV-suite tool: **PyQSOFit** configured for rest-frame UV lines
(Mg II 2798, C III] 1908, C IV 1549, Lyα/N V, Si IV), packaged as a Docker image
like the optical five.

## Build / run

```bash
bash pipeline/build_images.sh pyqsofit_uv

# input dir must contain the prepared PyQSOFit spectrum.fits
.venv/bin/python pipeline/prepare_inputs.py --fits input_zgt05 --out runs_ir_zgt05
bash run_pyqsofit_uv_docker.sh runs_ir_zgt05/04570952937/inputs/pyqsofit \
     results_ir/zgt05_pyqsofit_uv/04570952937
```

The image contains the PyQSOFit source, the UV config
(`configs/pyqsofit/uv/main.py`), and the PCA templates. The run is fast
(`MC=0`, `MCMC=0`); set `PYQSOFIT_MC=1` / `PYQSOFIT_MCMC=1` for uncertainties.

## Results on the z>0.5 SDSS DR18 set

| z | UV complexes fitted | PyQSOFit / SDSS ZLINE | preview |
|---|---|---|---|
| 1.8297 | Si IV, C IV, C III], Mg II | C IV **0.95**; Mg II 1.43; C III] 2.60 | `result.png` |
| 1.1289 | Mg II, C III] | Mg II 1.25; C III] 1.81 | `result.png` |
| 0.9901 | C III], Mg II (+ Hβ/[O III]) | Mg II 1.65; C III] 2.92; Hβ 0.90; [O III] 0.68 | `result.png` |
| 0.6506 | Hβ, [O III] (Mg II complex skipped) | Hβ **1.05**; [O III] 0.41 | `result.png` |
| 0.5874 | Hβ, [O III] (Mg II complex skipped) | [O III] 0.75 | `result.png` |

Each directory also has `output.fits`, `qsopar.fits`, `pyqsofit_model.csv`,
`result.pdf` and `result.png`.

## Known limitations (first pass)

- The config keeps the upstream `error = 0.02 * flux` floor; pass real
  uncertainties before production.
- C III] areas are 1.8–2.9× the SDSS ZLINE value: the broad+narrow + UV Fe II
  decomposition is not yet constrained; this is the next refinement.
- At z=0.587/0.6506 PyQSOFit skipped the Mg II complex (its rest-frame window
  is in a masked/low-acceptance part of the prepared spectrum); Hβ/[O III]
  were fitted instead. The z>0.99 objects fit Mg II/C III] as intended.
- No MCMC in the committed runs; the `result.pdf` shows the maximum-likelihood
  fit and residual panels.
