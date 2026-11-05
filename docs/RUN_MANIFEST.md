# Normalized run status

Tool-native `run.json` files are not identical across upstream codes.  To keep
the repository queryable, `pipeline/build_output_manifest.py` writes a
**normalized catalogue entry** for every output tree:

```json
{
  "source_key": "PDS456_z_0.1840",
  "tool": "optical_linefit",
  "kind": "line",
  "run_status": "ok",
  "quality": "conditional",
  "severity": "medium",
  "caveat": "Local H-beta/[O III] fit ... provisional ...",
  "headline": {},
  "caveats": [],
  "provenance": {"run_json": "..."},
  "artifacts": [...]
}
```

`run_status` now resolves to one of:

- the native `run.json.status` when present;
- `ok` when a native `run.json` or a non-empty headline exists;
- `artifacts_present` when only product files exist;
- `unknown` only when no metadata can be inferred.

The scientific `quality` and `severity` come from `configs/caveats.yaml`.
This catalogue is the stable contract for downstream queries; the native
`run.json` remains the tool's own record.
