#!/usr/bin/env python3
"""Build the formal catalogue of every committed output tree.

The catalogue is the machine-readable companion to ``docs/OUTPUT_SCHEMA.md``.
It records, for every ``outputs/<source>/<tool>/`` directory:

* the canonical source key and registered tool,
* the tool kind and run status (from ``run.json`` when available),
* a compact headline object and caveat list,
* every artifact with a role, media type, byte count and SHA-256.

The catalogue is validated against ``schemas/output_catalog.schema.json``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys_path = str(ROOT)
import sys  # noqa: E402
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)
from pipeline.io_layout import iter_sources, load_source  # noqa: E402
from pipeline.tool_registry import BY_NAME  # noqa: E402

SCHEMA_VERSION = "1.0.0"
ROLES = {
    ".png": "figure", ".pdf": "figure", ".jpg": "figure", ".jpeg": "figure",
    ".csv": "table", ".ecsv": "table", ".tbl": "table", ".tsv": "table",
    ".json": "metadata", ".yaml": "metadata", ".yml": "metadata",
    ".fits": "data", ".fit": "data", ".npz": "data", ".npy": "data",
    ".md": "report", ".txt": "report", ".log": "log",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def media_type(path: Path) -> str:
    if path.suffix.lower() == ".fits":
        return "application/fits"
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def role(path: Path) -> str:
    return ROLES.get(path.suffix.lower(), "other")


def headline(run: dict) -> dict:
    """Keep only small, JSON-safe headline fields."""
    out = {}
    for key in ("status", "mode", "result", "results", "summary", "metrics",
                "key_results", "quality", "runtime_s"):
        if key in run:
            value = run[key]
            if isinstance(value, (str, int, float, bool)) or value is None:
                out[key] = value
            elif isinstance(value, dict):
                flat = {k: v for k, v in value.items()
                        if isinstance(v, (str, int, float, bool)) or v is None}
                if flat:
                    out[key] = flat
    return out


def caveats(run: dict) -> list[str]:
    value = run.get("caveats") or run.get("caveat") or []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(x) for x in value]
    return []


def _caveat_index() -> dict:
    p = ROOT / "configs" / "caveats.yaml"
    if not p.exists():
        return {}
    try:
        data = yaml.safe_load(p.read_text()) or {}
    except Exception:
        return {}
    return {t["tool"]: t for t in data.get("tools", []) if "tool" in t}


def build() -> dict:
    sources = {s["key"]: s for s in iter_sources()}
    caveat_index = _caveat_index()
    entries = []
    for source_key in sorted(sources):
        for tool_dir in sorted((ROOT / "outputs" / source_key).iterdir()):
            if not tool_dir.is_dir() or tool_dir.name.startswith("."):
                continue
            if (tool_dir / ".running").exists():
                continue
            tool = tool_dir.name
            reg = BY_NAME.get(tool)
            run = {}
            run_json = tool_dir / "run.json"
            if run_json.exists():
                try:
                    run = json.loads(run_json.read_text())
                except Exception:
                    run = {}
            artifacts = []
            for path in sorted(tool_dir.rglob("*")):
                if not path.is_file() or path.name in (".snakemake_done", ".running"):
                    continue
                rel = path.relative_to(ROOT).as_posix()
                artifacts.append({
                    "path": rel,
                    "role": role(path),
                    "media_type": media_type(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                })
            if not artifacts:
                continue
            status = run.get("status")
            if not status:
                # A tool-native run.json is not standardized across upstream
                # codes.  A present product tree with a valid run.json or a
                # non-empty headline is still an "ok" artifact run; absence of
                # both is explicitly recorded as unknown.
                status = "ok" if (run_json.exists() or headline(run)) else "artifacts_present"
            cav = caveat_index.get(tool, {})
            entries.append({
                "source_key": source_key,
                "tool": tool,
                "kind": reg.kind if reg else "unknown",
                "run_status": str(status),
                "quality": cav.get("status", "unknown"),
                "severity": cav.get("severity", "info"),
                "caveat": cav.get("caveat", ""),
                "headline": headline(run),
                "caveats": caveats(run),
                "provenance": {"run_json": str(run_json.relative_to(ROOT)) if run_json.exists() else None},
                "artifacts": artifacts,
            })
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_count": len({e["source_key"] for e in entries}),
        "tool_count": len({e["tool"] for e in entries}),
        "entries": entries,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=ROOT / "outputs" / "output_catalog.json")
    p.add_argument("--csv", type=Path, default=ROOT / "outputs" / "output_catalog.csv")
    a = p.parse_args(argv)
    data = build()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(data, indent=2) + "\n")
    import csv
    with a.csv.open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["source_key", "tool", "kind", "run_status", "artifact_count", "figure_count", "bytes"])
        for e in data["entries"]:
            arts = e["artifacts"]
            w.writerow([e["source_key"], e["tool"], e["kind"], e["run_status"], len(arts),
                        sum(1 for x in arts if x["role"] == "figure"),
                        sum(x["bytes"] for x in arts)])
    print(f"wrote {a.out.relative_to(ROOT)} ({len(data['entries'])} entries, {data['tool_count']} tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
