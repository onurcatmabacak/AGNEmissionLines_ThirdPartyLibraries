#!/usr/bin/env python3
"""Collect every tool's plots into one folder with clear, flat names.

Copies the figure files from ``results/<tool>/<object>/`` into ``figures/`` named

    <tool>_<original filename>_<object>.<ext>

so all the emission-line fits for an object sit side by side and are easy to
open.  Nested products (e.g. BADASS' MCMC output) are flattened to their
basename.

Usage
-----
    python pipeline/collect_figures.py
    python pipeline/collect_figures.py --results results --out figures
"""

from __future__ import annotations

import argparse
import shutil
from collections import Counter
from pathlib import Path

TOOLS = ("pyqsofit", "badass", "fantasy_agn", "gelato", "gleam")
EXTS = (".pdf", ".png", ".jpg", ".jpeg", ".svg", ".gif", ".html")

# The single most informative best-fit figure per tool (used by --select).
SELECTED = {
    "pyqsofit": {"result"},
    "badass": {"max_likelihood_fit"},
    "fantasy_agn": {"my_sdss"},
    "gelato": {"my_sdss-comp"},
    "gleam": {"linefits.sdss.sdss.fiber1.001"},
}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--results", type=Path, default=Path("results"))
    p.add_argument("--out", type=Path, default=Path("figures"))
    p.add_argument("--clean", action="store_true", help="wipe the output folder first")
    p.add_argument("--select", action="store_true",
                   help="copy only the main best-fit figure per tool (badass max_likelihood_fit, "
                        "fantasy my_sdss, gelato my_sdss-spec, gleam linefits...001, pyqsofit result)")
    args = p.parse_args(argv)

    if args.clean and args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True, exist_ok=True)

    counts = Counter()
    used: set[str] = set()   # targets written this run (avoid duplicating on re-run)
    for tool_dir in sorted(d for d in args.results.iterdir() if d.is_dir() and d.name in TOOLS):
        tool = tool_dir.name
        for obj_dir in sorted(d for d in tool_dir.iterdir() if d.is_dir()):
            obj = obj_dir.name
            for f in sorted(obj_dir.rglob("*")):
                if not f.is_file() or f.suffix.lower() not in EXTS:
                    continue
                if args.select and f.stem not in SELECTED.get(tool, set()):
                    continue
                target = args.out / f"{tool}_{f.stem}_{obj}{f.suffix.lower()}"
                k = 1
                while target.name in used:   # same name from a different source file
                    target = args.out / f"{tool}_{f.stem}_{obj}_{k}{f.suffix.lower()}"
                    k += 1
                used.add(target.name)
                shutil.copy2(f, target)
                counts[tool] += 1

    total = sum(counts.values())
    print(f"copied {total} figure(s) to {args.out}/")
    for t in TOOLS:
        if counts[t]:
            print(f"  {t:12s} {counts[t]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
