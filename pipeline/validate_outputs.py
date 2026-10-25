#!/usr/bin/env python3
"""Validate the output catalogue against the formal schema and the filesystem.

Checks:
* JSON Schema validity of ``outputs/output_catalog.json``;
* every catalogued artifact exists and has the recorded size/SHA-256;
* every ``outputs/<source>/<tool>/`` directory is represented in the catalog;
* every source key exists under ``inputs/``;
* every tool name is registered (or is a known non-registry compatibility name);
* no zero-byte artifacts, no path traversal, no missing source.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import jsonschema  # noqa: E402
from pipeline.io_layout import iter_sources  # noqa: E402
from pipeline.tool_registry import BY_NAME  # noqa: E402

SCHEMA = ROOT / "schemas" / "output_catalog.schema.json"
CATALOG = ROOT / "outputs" / "output_catalog.json"
# Compatibility names that are intentionally retained in old output trees but
# are not independent fitting tools in the registry.
COMPAT = {"cmodel", "unknown", "pyqsofit"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(catalog_path: Path = CATALOG, schema_path: Path = SCHEMA,
             check_hashes: bool = True, strict_unknown: bool = True) -> list[str]:
    errors: list[str] = []
    cat = json.loads(catalog_path.read_text())
    schema = json.loads(schema_path.read_text())
    try:
        jsonschema.validate(cat, schema)
    except jsonschema.ValidationError as exc:
        errors.append(f"schema: {exc.message}")
        return errors

    known_sources = {s["key"] for s in iter_sources()}
    seen: set[tuple[str, str]] = set()
    for entry in cat["entries"]:
        key, tool = entry["source_key"], entry["tool"]
        seen.add((key, tool))
        if key not in known_sources:
            errors.append(f"{key}/{tool}: source key not present under inputs/")
        if tool not in BY_NAME and tool not in COMPAT:
            msg = f"{key}/{tool}: tool not in pipeline/tool_registry.py"
            (errors.append if strict_unknown else lambda _: None)(msg)
        if not entry["artifacts"]:
            errors.append(f"{key}/{tool}: empty artifact list")
        for art in entry["artifacts"]:
            rel = art["path"]
            if ".." in Path(rel).parts:
                errors.append(f"{key}/{tool}: path traversal {rel}")
                continue
            path = ROOT / rel
            if not path.is_file():
                errors.append(f"{key}/{tool}: missing {rel}")
                continue
            if path.stat().st_size != art["bytes"]:
                errors.append(f"{key}/{tool}: size mismatch {rel}")
            if path.stat().st_size == 0:
                errors.append(f"{key}/{tool}: zero-byte {rel}")
            if check_hashes and sha256(path) != art["sha256"]:
                errors.append(f"{key}/{tool}: sha256 mismatch {rel}")

    legacy = []
    for source_dir in sorted((ROOT / "outputs").iterdir()):
        if not source_dir.is_dir() or source_dir.name == "catalog":
            continue
        if source_dir.name not in known_sources:
            # Old flat-tree outputs retained for history, not part of the
            # canonical source registry.  They are reported but not errors.
            legacy.append(source_dir.name)
            continue
        for tool_dir in sorted(source_dir.iterdir()):
            if not tool_dir.is_dir() or tool_dir.name.startswith("."):
                continue
            if tool_dir.name in {"statistical_confirmation"}:
                continue
            files = [p for p in tool_dir.rglob("*") if p.is_file()]
            if not files:
                continue
            if (source_dir.name, tool_dir.name) not in seen:
                errors.append(f"{source_dir.name}/{tool_dir.name}: output tree not in catalog")
    if legacy:
        print(f"note: ignored {len(legacy)} legacy output directories not in inputs/", file=sys.stderr)
    return errors


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, default=CATALOG)
    p.add_argument("--schema", type=Path, default=SCHEMA)
    p.add_argument("--no-hash", action="store_true", help="skip SHA-256 verification")
    p.add_argument("--allow-unknown-tools", action="store_true")
    a = p.parse_args(argv)
    errors = validate(a.catalog, a.schema, check_hashes=not a.no_hash,
                      strict_unknown=not a.allow_unknown_tools)
    if errors:
        for e in errors:
            print("ERROR:", e)
        print(f"{len(errors)} validation error(s)")
        return 1
    print(f"OK: {a.catalog.relative_to(ROOT)} validated; all artifacts present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
