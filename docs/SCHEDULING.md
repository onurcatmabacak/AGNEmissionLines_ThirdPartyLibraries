# Parallel and long-run scheduling

The runner supports two scheduling modes.

## Sequential (default)

```bash
python pipeline/run_new_tools.py --only <source> --tools <tool1> <tool2>
```

One Docker job at a time.  Use this for debugging or when memory is tight.

## Phased (multicore first, then parallel single-core)

```bash
python pipeline/run_new_tools.py \
  --only 04592649654_z_0.5874 \
  --phased --threads 8 --jobs 4
```

Phase 1 runs tools in `MULTICORE_TOOLS` **one at a time**, with
`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS` and
`MANGA_DAP_NPROC` set to `--threads`.  Phase 2 runs all remaining tools
concurrently at one thread each, up to `--jobs`.

```text
multicore phase: s3fit_line, galspec_line, qgfit, pahfit_mir, cafe_line,
                 manga_dap, agnifitter_sed (serial, full thread budget)
parallel phase:  pyqsofit_uv, qsofitmore_line, optical_linefit, xray tools,
                 crossmission, ...
```

Override the classification when a tool has been benchmarked differently:

```bash
python pipeline/run_new_tools.py --phased \
  --multicore-tools s3fit_line,cafe_line --threads 8 --jobs 3
```

Each worker is a separate `run_new_tools.py` process, so Docker mounts and
logs are isolated.  `--force` is forwarded to every worker.

## Resource detection

`--threads auto` and `--jobs auto` use `pipeline/resources.py`, which reads
process affinity, cgroup v1/v2 CPU and memory limits, available memory and the
GPU inventory.  On the current 8-CPU/31-GB host the default budget is 6 CPUs
and 26 GB; an 8-GB tool is therefore capped at 3 threads, not blindly given 8.
Inspect it with:

```bash
python pipeline/run_new_tools.py --resource-report
```

The policy is conservative and memory-aware.  It does **not** claim that an
upstream code is multithreaded merely because a thread count was requested;
`pipeline/tool_capabilities.py` records the declared capability and the code is
run with the corresponding environment.

## Long runs

Long tools are never silently shortened:

- S3Fit: `--s3fit-threads 8`, full `spec+sed`, 10 mocks in the production config.
- GalSpec: `--galspec-mcmc-steps` / `--galspec-nwalkers` can be raised in the config;
  the existing 11.7 tau result remains a documented caveat until rerun.
- PyQSOFit: `PYQSOFIT_MCMC=1` plus `PYQSOFIT_NSAMP` controls.
- MaNGA: full DAP uses `plan.toml` (S/N=10, all bins); the subset production
  path remains the 9-bin validation.

The planner excludes long tools from `auto`; opt in explicitly:

```bash
python pipeline/run_new_tools.py --auto --source <key> --include-expensive
```

## Partial parallelism inside a tool

Some upstream codes do not expose a thread count.  The runner still sets the
standard BLAS/OpenMP environment variables; if the code ignores them, it runs
on one core.  S3Fit has an explicit `--threads` flag.  The phased scheduler
therefore gives a reliable ordering guarantee even when a tool cannot exploit
all cores.
