#!/usr/bin/env python3
"""Compare tuning variants across the labelled result sets.

Each ``run_pipeline.sh --label <name>`` writes ``results/<name>/scores.csv`` (and
the default run writes ``results/scores.csv``).  This script merges them into a
single table so a parameter sweep can be ranked:

    results/variants.html / variants.md

Rows are (object, tool); columns are the variant labels; cells are the reduced
chi-square, with the best (lowest) variant per row highlighted.
"""

from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path


def read_scores(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open() as fh:
        return list(csv.DictReader(fh))


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def gather(results: Path):
    """Return {label: {(tag, tool): (chi2, kind)}}."""
    data = {}
    if (results / "scores.csv").exists():
        data["default"] = {(r["tag"], r["tool"]): (r["chi2_red"], r["chi2_kind"])
                           for r in read_scores(results / "scores.csv")}
    for sub in sorted(p for p in results.iterdir() if p.is_dir()):
        if (sub / "scores.csv").exists():
            data[sub.name] = {(r["tag"], r["tool"]): (r["chi2_red"], r["chi2_kind"])
                              for r in read_scores(sub / "scores.csv")}
    return data


def build(results: Path):
    data = gather(results)
    labels = list(data)
    keys = sorted({k for d in data.values() for k in d})
    md = ["# Tuning-variant comparison (reduced chi^2)", "",
          "| object | tool | " + " | ".join(labels) + " |",
          "|---|---|" + "---:|" * len(labels)]
    h = ["<!doctype html><html><head><meta charset='utf-8'><title>Variant comparison</title>",
         "<style>body{font-family:system-ui,sans-serif;margin:2rem}table{border-collapse:collapse}",
         "th,td{border:1px solid #ccc;padding:4px 8px;font-size:13px}th{background:#f0f0f0}",
         ".best{background:#d7f5d7;font-weight:600}.num{text-align:right}</style></head><body>",
         "<h1>Tuning-variant comparison</h1><table><tr><th>object</th><th>tool</th>" +
         "".join(f"<th>{html.escape(l)}</th>" for l in labels) + "</tr>"]
    for tag, tool in keys:
        vals = {}
        for lab in labels:
            v = data.get(lab, {}).get((tag, tool))
            vals[lab] = _num(v[0]) if v else None
        present = [(v, l) for l, v in vals.items() if v is not None]
        best = min(present)[1] if present else None
        md.append(f"| {tag} | {tool} | " + " | ".join(
            (f"{vals[l]:.3g}" if vals[l] is not None else "") for l in labels) + " |")
        h.append(f"<tr><td>{html.escape(tag)}</td><td>{html.escape(tool)}</td>" + "".join(
            (f"<td class='num best'>{vals[l]:.3g}</td>" if l == best else
             (f"<td class='num'>{vals[l]:.3g}</td>" if vals[l] is not None else "<td></td>"))
            for l in labels) + "</tr>")
    h.append("</table></body></html>")
    return "\n".join(h), "\n".join(md)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results", type=Path, default=Path("results"))
    args = p.parse_args(argv)
    hdoc, mdoc = build(args.results)
    (args.results / "variants.html").write_text(hdoc)
    (args.results / "variants.md").write_text(mdoc)
    print(f"wrote {args.results/'variants.html'} and {args.results/'variants.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
