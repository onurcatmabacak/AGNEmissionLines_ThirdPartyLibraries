# `manga_dap` — NGC1194_z_0.0136

The production product is `full/`: the complete official Stage-A DAP run over all 5,476 spaxels (status 0, 48,731 s, 93,102 line measurements, BPT agreement 0.9885 against the published MAPS). `full_shard4/` is the bit-for-bit sharding validation and `aux_fastmode/` the auxiliary model attempt.

## Variants

- [`full/`](full/README.md)
- [`full_shard4/`](full_shard4/README.md)
- [`aux_fastmode/`](aux_fastmode/README.md)

The data and bulk artefacts are not shipped (see `outputs/README.md`); the
observation can be restored from `inputs/NGC1194_z_0.0136/source.json` and the tool
re-run with `pipeline/runners/run_manga_dap_docker.sh`.  Status, severity and
evidence for the tool are in `docs/CAVEAT_MATRIX.md`.
