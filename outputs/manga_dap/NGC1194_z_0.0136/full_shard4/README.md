# Validation artifact — pPXF-sharded DAP vs the serial product

This tree is **not** the production MaNGA product.  It is the evidence that the
pPXF shard (`Tools/manga_dap/shard_ppxf.py`, enabled with
`MANGADAP_SHARD_WORKERS=4 MANGADAP_SHARD_STAGES=ppxf`) reproduces the serial
DAP exactly.  The production record remains `../full/`, produced by the
unmodified official pipeline.

| | serial `../full/` | sharded (this tree) |
|---|---|---|
| configuration | official Stage-A DAP, 2,397 HYB10 bins, 5,476 spaxels | identical inputs and plan |
| parallelism | 1 core | 4 forked workers on the pPXF stage only |
| wall clock | 13.51 h | **13.17 h** |
| status | ok, `dap_status_code 0` | ok |

## Equivalence

`shard_validation.txt` is the unedited output of

```bash
python pipeline/compare_manga_shard.py \
    outputs/manga_dap/NGC1194_z_0.0136/full \
    outputs/manga_dap/NGC1194_z_0.0136/full_shard4
```

```
worst relative difference in line fluxes: 0.00e+00 (rtol=1e-06)
BPT serial  : seyfert 1945, liner 231, composite 83, star-forming 9, n=5476
BPT sharded : seyfert 1945, liner 231, composite 83, star-forming 9, n=5476
OK: sharded product matches the serial reference
```

So the shard is **bit-identical** on the line-flux summary and the BPT census.

## Why it is only 2.5 % faster

The shard covers pPXF, which is ~7 % of the 13.5 h.  The emission-line moments
(~5 h) and SASUKE (~6 h) remain serial: the EMOM shard is implemented and
unit-tested but silently aborts the real run (no exception, no MAPS), and the
SASUKE shard is never reached.  Both are gated off (`MANGADAP_SHARD_STAGES`
defaults to `ppxf`).  See `docs/MANGA_SHARDING.md`.

For throughput on a *sample* of galaxies use `pipeline/run_manga_parallel.py`,
which runs independent cubes concurrently with the unmodified pipeline.
