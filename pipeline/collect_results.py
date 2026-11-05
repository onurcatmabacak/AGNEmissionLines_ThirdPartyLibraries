#!/usr/bin/env python3
"""Collect per-tool outputs into a single comparable results tree.

Given the tidy per-object run tree::

    runs/<tag>/outputs/<tool>/...

this copies everything to ``results/<tool>/<tag>/`` and writes:

    results/index.csv     one row per (tag, tool): status, file count, key outputs
    results/summary.json  the same information grouped by object

The parsers are deliberately forgiving: a tool that changed its output layout
only loses its parsed columns, it never aborts the run.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

# Files worth surfacing in the index for each tool (globs allowed).
KEY_PATTERNS = {
    "pyqsofit": ["qsopar*.fits", "output*.fits", "*result*.pdf"],
    "sculptor": ["*.csv", "*.hdf5", "*.pdf"],
    "badass": ["*.fits", "*.pdf", "*.json", "*.txt"],
    "fantasy_agn": ["*_model.csv", "*_pars.json", "*.pdf"],
    "gelato": ["*-results.fits", "*.fits", "*.pdf"],
    "gleam": ["*.png", "*.fits", "*.csv"],
}

TOOLS = ("sculptor", "pyqsofit", "badass", "fantasy_agn", "gelato", "gleam")


def _log_ok(log: Path) -> str:
    if not log.exists():
        return ""
    txt = log.read_text(errors="ignore")
    ok = ("Traceback" not in txt) and not any(
        w in txt for w in ("Error", "error:", "FAILED", "Exception")
    )
    return str(bool(ok))


def collect_outputs(runs: Path, results: Path) -> list[dict]:
    rows = []
    for objdir in sorted(p for p in runs.iterdir() if p.is_dir()):
        manifest = objdir / "manifest.json"
        meta = json.loads(manifest.read_text()) if manifest.exists() else {}
        tag = objdir.name
        outroot = objdir / "outputs"
        if not outroot.is_dir():
            continue
        for tool in TOOLS:
            out = outroot / tool
            if not out.is_dir():
                continue
            files = [f for f in out.rglob("*") if f.is_file()]
            if not files:
                continue
            dest = results / tool / tag
            for f in files:
                target = dest / f.relative_to(out)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)

            keys = []
            for pat in KEY_PATTERNS.get(tool, ["*"]):
                keys += [str(f.relative_to(out)) for f in sorted(out.glob(pat))]
            rows.append(
                {
                    "tag": tag,
                    "catalogid": meta.get("catalogid"),
                    "z": meta.get("z"),
                    "tool": tool,
                    "n_files": len(files),
                    "log_ok": _log_ok(out / "fit.log"),
                    "key_outputs": ";".join(dict.fromkeys(keys)),
                }
            )
    return rows


def summarise(runs: Path) -> dict:
    summary = {}
    for objdir in sorted(p for p in runs.iterdir() if p.is_dir()):
        if not (objdir / "manifest.json").exists():
            continue
        summary[objdir.name] = {}
        for tool in TOOLS:
            out = objdir / "outputs" / tool
            if out.is_dir():
                n = len([f for f in out.rglob("*") if f.is_file()])
                if n:
                    summary[objdir.name][tool] = n
    return summary


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    args = p.parse_args(argv)

    if not args.runs.is_dir():
        print(f"no runs dir: {args.runs}")
        return 1
    args.results.mkdir(parents=True, exist_ok=True)

    rows = collect_outputs(args.runs, args.results)
    index = args.results / "index.csv"
    with index.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["tag", "catalogid", "z", "tool", "n_files", "log_ok", "key_outputs"])
        w.writeheader()
        w.writerows(rows)

    (args.results / "summary.json").write_text(json.dumps(summarise(args.runs), indent=2))
    print(f"collected {len(rows)} tool run(s) across {len({r['tag'] for r in rows})} object(s)")
    print(f"  {index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
