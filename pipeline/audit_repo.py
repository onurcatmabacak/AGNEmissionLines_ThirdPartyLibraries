#!/usr/bin/env python3
"""Static consistency audit for the repository.

This is intentionally stricter than the scientific caveat matrix: it checks
that the registry, runnable tools, build list, source manifests, configs,
runners, caveat matrix and output catalogue agree.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.io_layout import iter_sources  # noqa: E402
from pipeline.run_new_tools import ALL_TOOLS, MULTICORE_TOOLS  # noqa: E402
from pipeline.tool_capabilities import THREADS, FULL_CAPABILITY  # noqa: E402
from pipeline.tool_registry import TOOLS  # noqa: E402

REFERENCE = {"sdss_zline"}
LEGACY_IMAGES = {"badass", "fantasy_agn", "gelato", "gleam"}
SHARED_IMAGES = {"manga_dap_full": "manga_dap"}
HOST_ONLY = {"crossmission"}


def main() -> int:
    errors = []
    registry = {t.name: t for t in TOOLS}
    for t in TOOLS:
        if not (ROOT / t.runner).exists():
            errors.append(f"{t.name}: runner missing {t.runner}")
        if t.config.endswith(".json") and not (ROOT / t.config).exists():
            errors.append(f"{t.name}: config missing {t.config}")
    runnable = set(ALL_TOOLS)
    expected_runnable = set(registry) - REFERENCE
    if runnable != expected_runnable:
        errors.append(f"ALL_TOOLS mismatch: missing={sorted(expected_runnable-runnable)} extra={sorted(runnable-expected_runnable)}")
    if set(THREADS) != set(registry):
        errors.append(f"capability keys mismatch: {sorted(set(registry)-set(THREADS))} / {sorted(set(THREADS)-set(registry))}")
    if set(FULL_CAPABILITY) != set(registry):
        errors.append(f"full-capability keys mismatch: {sorted(set(registry)-set(FULL_CAPABILITY))}")
    if not MULTICORE_TOOLS <= set(registry):
        errors.append(f"multicore tools not registered: {sorted(MULTICORE_TOOLS-set(registry))}")

    text = (ROOT / "Pipelines" / "build_images.sh").read_text()
    m = re.search(r"DOCKER_TOOLS=\(([^)]*)\)", text)
    images = set(m.group(1).split()) if m else set()
    required_images = {t.name for t in TOOLS if t.name not in HOST_ONLY | REFERENCE}
    required_images = {SHARED_IMAGES.get(x, x) for x in required_images}
    missing_images = required_images - images
    if missing_images:
        errors.append(f"image tools missing from build_images.sh: {sorted(missing_images)}")
    if images - set(registry) - LEGACY_IMAGES:
        errors.append(f"unregistered image tools: {sorted(images-set(registry)-LEGACY_IMAGES)}")

    for src in iter_sources():
        for tool in src.get("tools", []):
            if tool not in registry:
                errors.append(f"{src['key']}: unknown tool {tool}")

    caveat = {}
    cp = ROOT / "configs" / "caveats.yaml"
    if cp.exists():
        import yaml
        caveat = {x["tool"]: x for x in yaml.safe_load(cp.read_text()).get("tools", [])}
    if set(caveat) != set(registry):
        errors.append(f"caveat coverage mismatch: {sorted(set(registry)-set(caveat))} / {sorted(set(caveat)-set(registry))}")

    catalog_path = ROOT / "outputs" / "output_catalog.json"
    if catalog_path.exists():
        cat = json.loads(catalog_path.read_text())
        for e in cat.get("entries", []):
            if e["tool"] not in registry and e["tool"] not in {"pyqsofit"}:
                errors.append(f"catalog unknown tool: {e['source_key']}/{e['tool']}")
            for a in e.get("artifacts", []):
                if not (ROOT / a["path"]).exists():
                    errors.append(f"catalog missing artifact: {a['path']}")
    else:
        errors.append("outputs/output_catalog.json missing")

    # Local markdown links only; external URLs are intentionally ignored.
    for md in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]:
        for target in re.findall(r"\]\(([^)#]+)\)", md.read_text()):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            p = (md.parent / target).resolve()
            if not p.exists():
                errors.append(f"{md.relative_to(ROOT)}: broken link {target}")

    if errors:
        for e in errors:
            print("ERROR:", e)
        print(f"{len(errors)} consistency error(s)")
        return 1
    print(f"OK: {len(registry)} registered tools; {len(images)} image tools; "
          f"{len(list(iter_sources()))} sources; catalogue and links consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
