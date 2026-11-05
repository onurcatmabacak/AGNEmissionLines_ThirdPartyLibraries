# Best configurations found by `auto_tune` (10-object eFEDS sample)

Search: `bash analyze.sh` per tool (`--limit 3 --rounds 1`), ranked by the mean
common reduced chi-square (`chi2_common`) over the three tuning objects.  The
final run then re-fit all 10 objects with these winners.

| tool | winning knobs | mean `chi2_common` (tuning set) |
|------|---------------|--------------------------------:|
| pyqsofit | base (error floor 0.02, Fe templates on) | 167.9 |
| badass | base (`fit_stat=OLS`, broad `disp_plim` lower 600) | **26.1** |
| fantasy_agn | `min_fwhm_br=400`, Fe II model off | 135.2 |
| gelato | `LineRegion=500`, `NBoot=0` | 41.5 |
| gleam | `resolution=2.5 Å`, `cont_width=40 Å` | 271.5 |

The same artifacts are checked in under `configs/<tool>/best/` and can be
re-applied with:

```bash
bash run_pipeline.sh \
  --variant pyqsofit=best --variant badass=best \
  --variant fantasy_agn=best --variant gelato=best --variant gleam=best
```

`chi2_common` is the fair, tool-agnostic reduced chi-square computed by
`pipeline/score_fits.py` (each tool's model rebuilt on the same prepared spectrum
with the same calibrated errors plus a fixed 2 % flux floor), so it is not
distorted by a tool's internal error floor.
