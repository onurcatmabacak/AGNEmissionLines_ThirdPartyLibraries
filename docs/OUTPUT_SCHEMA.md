# Formal output contract and schema

Every science product is written under:

```text
outputs/<source_key>/<tool_name>/
```

`source_key` is the canonical `inputs/<source_key>/source.json` directory name.
`tool_name` is a registered name in `pipeline/tool_registry.py` (plus the
legacy-compatible `pyqsofit` alias).  Raw inputs are never copied into
`outputs/`; tool-native prepared copies live under `work/prepared/` and are
ignored.

## Two schemas

| file | purpose |
|---|---|
| `schemas/output_catalog.schema.json` | JSON Schema (draft 2020-12) for the complete output catalogue |
| `outputs/output_catalog.json` | generated catalogue with one entry per `(source_key, tool)` |
| `outputs/output_catalog.csv` | flat summary: source, tool, kind, status, artifact counts, bytes |
| `docs/caveat_matrix.json` | machine-readable scientific status/caveat table |
| `docs/CAVEAT_MATRIX.md` | rendered caveat matrix |

The catalogue is deliberately **descriptive**, not a claim that every file is
scientifically validated.  Validation lives in `docs/CAVEAT_MATRIX.md` and the
per-tool `README.md`/`run.json`.

## Catalogue entry

```json
{
  "source_key": "PDS456_z_0.1840",
  "tool": "crossmission",
  "kind": "ratio",
  "run_status": "unknown",
  "headline": {},
  "caveats": [],
  "provenance": {"run_json": "outputs/PDS456_z_0.1840/crossmission/run.json"},
  "artifacts": [
    {
      "path": "outputs/PDS456_z_0.1840/crossmission/xray_optical_comparison.csv",
      "role": "table",
      "media_type": "text/csv",
      "bytes": 481,
      "sha256": "..."
    }
  ]
}
```

Artifact roles:

| role | examples |
|---|---|
| `figure` | `.png`, `.pdf`, `.jpg` |
| `table` | `.csv`, `.ecsv`, `.tbl`, `.tsv` |
| `metadata` | `.json`, `.yaml` |
| `data` | `.fits`, `.npz`, `.npy` |
| `report` | `.md`, `.txt` |
| `log` | `.log` |

The schema requires at least one artifact per entry; a zero-byte file is a
validation error.  `sha256` binds the catalogue to the exact committed bytes.

## Generate and validate

```bash
.venv/bin/python pipeline/build_output_manifest.py
.venv/bin/python pipeline/validate_outputs.py
```

`validate_outputs.py` checks:

* JSON Schema validity;
* every artifact exists, has the recorded byte count and SHA-256;
* every current `outputs/<source>/<tool>/` tree appears in the catalogue;
* every source key exists under `inputs/`;
* every tool is registered;
* no path traversal and no zero-byte artifacts.

Legacy flat-tree outputs without an `inputs/<source_key>/source.json` are
reported as ignored, not silently accepted as current science products.

## Per-tool contract

A production tool should normally write:

```text
run.json / config.effective.json   provenance, software, inputs, status, caveats
*.csv                              line/parameter tables
*.fits                             machine-readable fit products
*.png / *.pdf                      fit, residual, corner, uncertainty figures
README.md                          human-readable method + caveats
xspec.log / *.log                  if the code provides a native log
```

`run.json` is intentionally not schema-locked because the third-party tools
use different native result structures; the catalogue records the common
metadata and the per-tool README documents the native fields.

## Reproducibility checklist

1. `bash Pipelines/build_images.sh <tool>` (or no argument for all 24).
2. `bash Pipelines/run_<tool>_docker.sh ...` or
   `.venv/bin/python pipeline/run_new_tools.py --tools <tool> --only <source> --force`.
3. `snakemake -s workflow/Snakefile --cores N all` for the graph-managed path.
4. Regenerate `outputs/output_catalog.json`.
5. Run `.venv/bin/pytest` and `pipeline/validate_outputs.py`.

The `crossmission` product is a post-processing comparison, not a new
third-party fit: it reads the committed `xmm_xspec`/`rxte_xspec` and
`pyqsofit_uv` tables and writes only a derived comparison.
