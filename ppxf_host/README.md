# ppxf_host — host–AGN decomposition with pPXF (Docker)

The third IR/UV-suite tool: **pPXF** fitted to the rest-frame optical part of
the z>0.5 QSO spectra, with the BADASS eMILES stellar templates. The AGN
continuum is absorbed by an additive Legendre polynomial; emission lines are
masked before the fit.

## Build / run

```bash
bash pipeline/build_images.sh ppxf_host
bash run_ppxf_host_docker.sh runs_ir_zgt05/04592649654/inputs/pyqsofit \
     results_ir/zgt05_ppxf_host/04592649654
```

Input: prepared PyQSOFit `spectrum.fits` (HDU0 flux, HDU1 Å, HDU2 error, header
`z`).  Output: `ppxf_model.csv`, `ppxf_result.fits`, `ppxf_fit.pdf/png`,
`ppxf_summary.json`.

## Results on the z>0.5 set

| z | χ²_red | σ (km/s) | host fraction | window (Å) |
|---|---:|---:|---:|---|
| 0.5874 | 26.6 | 702 | **0.114** | 4000–5000 |
| 0.6506 | 33.3 | 1000 | **0.122** | 4000–5000 |
| 0.9901 | 13.9 | 100 | 0.000 | 4000–5000 |
| 1.1289 | 16.5 | 100 | 0.000 | 3000–4000 |
| 1.8297 | 23.5 | 100 | 0.000 | 2000–3000 |

At z≈0.6 the host contributes ~11–12 % at 4–5 kÅ. At z≥0.99 the QSO continuum
dominates (host fraction 0; σ stays at the start value), and the host is not
constrained by these optical spectra. The z=1.83 object is rest-frame UV, where
eMILES has little leverage.

## Caveats

- The host fraction is model-dependent; χ²_red is high because the AGN Fe II /
  Balmer continuum is represented only by a polynomial.
- Emission lines (Hα/Hβ/[O III]/[N II]/[S II]/Mg II/C IV…) are masked with
  ±2000 km/s windows; the plotted residuals therefore show the lines.
- The σ values at z≈0.6 are broad (700–1000 km/s), likely absorbing residual
  broad-line wings; treat them as upper limits.
- No AGN torus, no MC/MCMC uncertainties, and no simultaneous line fit yet.
