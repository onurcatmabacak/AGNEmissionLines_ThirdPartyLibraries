# MaNGA DAP runtime: what is parallel, what is not

## Measured baseline

`outputs/manga_dap/NGC1194_z_0.0136/full` — official Stage-A DAP, all 5,476
spaxels, 2,397 HYB10 bins, 93,102 line measurements: **48,731 s (13.51 h)** on
one core, `dap_status_code = 0`, BPT agreement 0.9885 against the published
MAPS.

## What is implemented: parallel cubes

`pipeline/run_manga_parallel.py` runs N *different* cubes concurrently, one
container each:

```bash
python pipeline/run_manga_parallel.py --jobs 4 \
    inputs/NGC1194_z_0.0136 inputs/NGC4395_z_0.0010
```

Each job is the unmodified wrapper (`--full`), so every product is identical
to a serial run — only wall-clock changes.  With 6 cubes and 6 jobs the sample
costs one cube's 13.5 h instead of 81 h.

## What is *not* implemented: sharding one cube

There is no supported seam for it.  Verified against the installed
`sdss-mangadap` 4.5.0:

* no `ncpu`, `nproc`, `multiprocessing`, `concurrent.futures` or `joblib`
  anywhere in the package;
* the pPXF stage is a serial loop inside
  `mangadap.proc.ppxffit.PPXFFit._run_fit_iteration` (line ~929,
  `for i in range(nspec): ... ppxf.ppxf(...)`), with per-spectrum state
  written into shared arrays (`par`, `perror`, `chi2`, masks).

Two designs are possible, both need a validation campaign:

1. **Monkeypatched stage pool (no upstream change).**  Wrap
   `_run_fit_iteration` so the per-spectrum body runs in a process pool, then
   assemble the arrays in index order.  Each worker needs its own copy of
   `tpl_flux`/`tpl_rfft` (pickling ~1-2 GB for 65 templates) — use fork and a
   read-only global, as the GalSpec runner does.
   Risk: numerical identity is not guaranteed; must be checked bin-by-bin.
2. **Bin-shard the driver (upstream change).**  Add a `--bins` selector to the
   DAP driver, run K shards over disjoint bins, and merge the MAPS cubes.

Validation protocol (mandatory before any sharded claim): re-run NGC 1194 with
sharding enabled and compare against the serial product — identical
`EMLINE` fluxes to within the FITS precision, identical BPT classes, and
`maps_stats.json` reproduced exactly.  That is one 13.5 h reference run plus
one sharded run, so it is a deliberate campaign, not a quick switch.

Until then the sharded path is **not claimed**: `run.json` from the serial run
remains the production record, and `docs/UNRESOLVED_ITEMS.md` says so.
