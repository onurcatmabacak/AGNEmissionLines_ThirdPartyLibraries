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
``outputs/<tool>/<source>_z_<z>/``
    Every result file for one source and one tool.  The tree is keyed by tool
    first so a tool's products across all sources sit together; no flat
    ``results_ir`` directories, no per-tool duplicates of the raw input.

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
    """Canonical product path: ``outputs/<tool>/<source>_z_<z>/``."""
    return OUTPUT_ROOT / _slug(tool) / key


def output_key_tool(path: Path) -> tuple[str, str] | None:
    """Split an ``outputs/<tool>/<source>/`` path into ``(key, tool)``."""
    try:
        rel = Path(path).resolve().relative_to(OUTPUT_ROOT.resolve())
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) < 2:
        return None
    tool, key = parts[0], parts[1]
    if tool.startswith(".") or key.startswith(".") or "_z_" not in key:
        return None
    return key, tool


def iter_output_dirs() -> list[tuple[str, str, Path]]:
    """Return ``(tool, source_key, path)`` for every product tree.

    The canonical layout is ``outputs/<tool>/<source>_z_<z>/``.  Top-level
    files such as ``output_catalog.json``, comparison figures and
    dot-directories are skipped.
    """
    if not OUTPUT_ROOT.exists():
        return []
    out: list[tuple[str, str, Path]] = []
    for tool_dir in sorted(OUTPUT_ROOT.iterdir()):
        if not tool_dir.is_dir() or tool_dir.name.startswith("."):
            continue
        for src_dir in sorted(tool_dir.iterdir()):
            if not src_dir.is_dir() or src_dir.name.startswith("."):
                continue
            out.append((tool_dir.name, src_dir.name, src_dir))
    return out


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
