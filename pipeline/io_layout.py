"""Canonical source-keyed layout for the NIR/MIR/FIR/SED tools.

Inputs
------
``inputs/<source>_z_<z>/source.json``
    One manifest per science source.  ``raw/`` holds the canonical, unmodified
    data; ``photometry/`` holds a one-row CIGALE catalogue when applicable.
``inputs/catalogs/``
    Cross-source catalogues (the SDSS z>0.5 sample, the combined photometry).

Outputs
-------
``outputs/<source>_z_<z>/<tool>/``
    Every result file for one source and one tool.  No flat ``results_ir``
    directories, no per-tool duplicates of the raw input.

Prepared tool-native files (PyQSOFit/pPXF copies) live in
``work/prepared/<source>_z_<z>/<tool>/`` and are deliberately not committed.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = ROOT / "inputs"
OUTPUT_ROOT = ROOT / "outputs"
WORK_ROOT = ROOT / "work" / "prepared"
CATALOG_ROOT = INPUT_ROOT / "catalogs"


def _slug(text: str) -> str:
    text = str(text).strip().replace(" ", "_")
    text = text.replace("+", "p").replace("/", "_")
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    return text.strip("._") or "source"


def format_z(z: float) -> str:
    if z is None or not math.isfinite(float(z)):
        return "unknown"
    return f"{float(z):.4f}"


def source_key(name: str, z: float) -> str:
    """Return the canonical ``<source_name>_z_<redshift>`` key."""
    return f"{_slug(name)}_z_{format_z(z)}"


def source_dir(key: str) -> Path:
    return INPUT_ROOT / key


def output_dir(key: str, tool: str) -> Path:
    return OUTPUT_ROOT / key / _slug(tool)


def prepared_dir(key: str, tool: str) -> Path:
    return WORK_ROOT / key / _slug(tool)


def load_source(key: str) -> dict:
    p = source_dir(key) / "source.json"
    if not p.exists():
        raise FileNotFoundError(f"no source manifest: {p}")
    d = json.loads(p.read_text())
    d["_path"] = str(p.parent)
    return d


def iter_sources() -> list[dict]:
    if not INPUT_ROOT.exists():
        return []
    out = []
    for p in sorted(INPUT_ROOT.glob("*/source.json")):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        d.setdefault("key", p.parent.name)
        d["_path"] = str(p.parent)
        out.append(d)
    return out


def source_files(src: dict, kind: str | None = None) -> list[Path]:
    """Resolve ``files`` entries from a manifest; ``kind`` filters by role."""
    base = Path(src["_path"]) if "_path" in src else source_dir(src["key"])
    files = src.get("files", {})
    if isinstance(files, dict):
        items = []
        for role, value in files.items():
            if kind is not None and role != kind:
                continue
            for v in (value if isinstance(value, list) else [value]):
                items.append(base / v)
        return items
    return [base / v for v in files]


def ensure_output(key: str, tool: str, clean: bool = False) -> Path:
    out = output_dir(key, tool)
    if clean and out.exists():
        import shutil
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_manifest(key: str, data: dict) -> Path:
    p = source_dir(key) / "source.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return p
