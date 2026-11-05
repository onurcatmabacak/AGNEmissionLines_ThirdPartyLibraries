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

## Intra-cube sharding: implemented

`sdss-mangadap` 4.5.0 has no parallel switch (no `ncpu`/`nproc`/
`multiprocessing`/`concurrent.futures`/`joblib` anywhere), but
`PPXFFit._run_fit_iteration` is **data-parallel**: it walks
`for i in range(nspec)` and writes `result[i]`, and every shared input
(`tpl_flux`, `tpl_rfft`, `self`) is read-only.

`Tools/manga_dap/shard_ppxf.py` exploits exactly that.  It replaces the method
with one that

1. splits `0..nspec` into contiguous, balanced ranges,
2. calls the **original** method in a forked worker per range with the sliced
   arrays (`obj_flux[lo:hi]`, `obj_ferr[lo:hi]`, `start[lo:hi]`, ...
   plus per-spectrum `obj_to_fit`/`tpl_to_use`),
3. concatenates the returned `PPXFFitResult` lists in index order.

Because the fit itself is never reimplemented, the numerics are the upstream
numerics; fork + copy-on-write shares the template arrays instead of pickling
them.  `plot=True` and workloads below 2 spectra per worker stay serial.

Enable it with one environment variable (the wrapper forwards it, the image
ships a `sitecustomize` that installs the patch before the DAP CLI starts):

```bash
MANGADAP_SHARD_WORKERS=4 bash pipeline/runners/run_manga_dap_docker.sh \
    inputs/NGC1194_z_0.0136 outputs/manga_dap/NGC1194_z_0.0136/full_shard4 --full
```

Measured on the NGC 1194 cube: the stellar-continuum stage reports
`Running pPXF fit on spectrum: 2397/2397 (sharded over 4 processes)` and the
container runs at ~400 % CPU (4 cores) instead of 100 %.

Stages are selected with `MANGADAP_SHARD_STAGES` (default `ppxf`):

| stage | status |
|---|---|
| `ppxf` | **validated** — sharded product matches the serial one bit-for-bit (worst relative line-flux difference `0.00e+00`, identical BPT census) |
| `emom` | implemented + unit-tested, **known broken in the real pipeline**: enabling it makes the DAP stop right after the moments stage with "DAP completed without producing a MAPS file" and no exception |
| `sasuke` | implemented + unit-tested; never reached while `emom` breaks the run, and its installer had to be fixed (`sasuke.py` binds the symbol with `from … import`, so patching `xjmc` alone is not enough) |

Because of that, only `ppxf` is on by default.  **Enable `emom`/`sasuke` only
while debugging**, and treat any product produced with them as unvalidated.

### Validation

* `tests/test_manga_shard.py` (8 tests) pins the contract with a deterministic
  stand-in for the fit: range splitting is contiguous and complete, the
  assembled result equals the serial result for 2-4 workers, per-spectrum
  flags follow the slice, and `plot=True` stays serial.
* Full-data check (pPXF only): `outputs/manga_dap/NGC1194_z_0.0136/full_shard4`
  was compared against the serial `full/` product with
  `pipeline/compare_manga_shard.py` — **OK, worst relative line-flux difference
  0.00e+00, identical BPT census (1945/231/83/9, 5476 spaxels)**.  Wall clock
  13.17 h vs 13.51 h serial, i.e. only ~2.5 %: pPXF is ~7 % of the runtime, so
  the win has to come from EMOM (~5 h) and SASUKE (~6 h), which are not usable
  yet.
* The serial product remains the production record; nothing sharded is
  promoted while `emom`/`sasuke` are broken.

## Decision (settled)

Intra-cube sharding stops at pPXF.  The measured payoff is 2.5 % (13.51 h →
13.17 h) because pPXF is only ~7 % of the runtime, while the two stages that
hold ~80 % of it (EMOM ~5 h, SASUKE ~6 h) either corrupt the run silently
(EMOM) or were never exercised (SASUKE).  A silently wrong DAP product is far
worse than a slow one, and every debugging iteration costs a 13.5 h run.

Therefore:

* `MANGADAP_SHARD_STAGES` defaults to `ppxf`; the production product is the
  serial `full/` tree and nothing sharded is promoted.
* `full_shard4` is kept **only** as validation evidence, with its own README and
  `shard_validation.txt`.
* Throughput for a sample comes from `pipeline/run_manga_parallel.py`
  (independent cubes, unmodified pipeline).  Validate memory with a 4-job pilot
  first: each cube peaked at ~5 GB of 31 GB.

Revisit intra-cube sharding only if a single cube ever has a hard deadline, or
if the sample grows past what parallel cubes can absorb on this host.
