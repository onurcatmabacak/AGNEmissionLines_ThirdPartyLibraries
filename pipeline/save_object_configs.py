#!/usr/bin/env python3
"""Copy each object's winning tool configs next to the figures.

Reads ``work/per_object/best_configs.json`` (keys ``"<tag>|<tool>"``) and copies
the winning variant config files into ``figures_main/configs/`` named

    <tool>_<configfilename>_<object>.<ext>

so the exact configuration behind each fit travels with its plot.

Usage
-----
    python pipeline/save_object_configs.py
    python pipeline/save_object_configs.py --best work/per_object/best_configs.json --out figures_main/configs
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import auto_tune as at


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--best", type=Path, default=Path("work/per_object/best_configs.json"))
    p.add_argument("--out", type=Path, default=Path("figures_main/configs"))
    args = p.parse_args(argv)

    if not args.best.exists():
        print(f"no {args.best}; run pipeline/per_object_search.py first")
        return 1
    raw = json.loads(args.best.read_text())
    args.out.mkdir(parents=True, exist_ok=True)

    n = 0
    for key, info in sorted(raw.items()):
        tag, tool = key.split("|", 1)
        spec = at.TOOLS.get(tool, (None,))[0]
        if spec is None:
            continue
        src = at.CONFIGS / tool / info["variant"] / spec["file"]
        if not src.exists():
            print(f"[save] missing {src}")
            continue
        dst = args.out / f"{tool}_{src.stem}_{tag}{src.suffix}"
        shutil.copy2(src, dst)
        n += 1
    print(f"copied {n} object config(s) to {args.out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
