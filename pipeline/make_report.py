#!/usr/bin/env python3
"""Build a comparison report from the collected results.

Reads ``results/scores.csv`` and ``results/lines.csv`` (written by
``pipeline/score_fits.py``) and produces:

    results/report.html   self-contained comparison report
    results/report.md     the same, in Markdown

For every input object the report shows each tool's reduced chi-square (with the
kind of statistic it is), a line-by-line flux comparison, and links to each
tool's products.  Lower chi-square ranks first, but the statistic differs per
tool, so the ranking is a guide, not a verdict.
"""

from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path

LINES = ["OII3727", "Hb4861", "OIII4959", "OIII5007", "Ha6563", "NII6585", "SII6718", "SII6732"]
TOOLS = ["pyqsofit", "badass", "fantasy_agn", "gelato", "gleam"]


def read_csv(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open() as fh:
        return list(csv.DictReader(fh))


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def build(runs: Path, results: Path) -> tuple[str, str]:
    scores = read_csv(results / "scores.csv")
    lines = read_csv(results / "lines.csv")

    tags = sorted({r["tag"] for r in scores} | {r["tag"] for r in lines})
    md = ["# Cross-tool AGN emission-line comparison", ""]
    h = ["<!doctype html><html><head><meta charset='utf-8'>",
         "<title>Cross-tool AGN comparison</title>",
         "<style>body{font-family:system-ui,sans-serif;margin:2rem;max-width:1200px}",
         "table{border-collapse:collapse;margin:1rem 0}th,td{border:1px solid #ccc;padding:4px 8px;font-size:13px}",
         "th{background:#f0f0f0}.best{background:#d7f5d7;font-weight:600}.num{text-align:right}",
         "small{color:#666}.tool{font-weight:600}details{margin:.4rem 0}</style></head><body>",
         "<h1>Cross-tool AGN emission-line comparison</h1>"]

    for tag in tags:
        st = {r["tool"]: r for r in scores if r["tag"] == tag}
        # rank tools by chi2 where available
        ranked = sorted(((_num(r["chi2_red"]), r["tool"]) for r in scores if r["tag"] == tag
                         and _num(r["chi2_red"]) is not None))
        best_tool = ranked[0][1] if ranked else None

        md += [f"## Object `{tag}`", "", "| tool | reduced chi^2 | statistic |", "|---|---:|---|"]
        h += [f"<h2>Object <code>{html.escape(tag)}</code></h2>",
              "<table><tr><th>tool</th><th>reduced &chi;&sup2;</th><th>statistic</th></tr>"]
        for tool in TOOLS:
            r = st.get(tool)
            if not r:
                continue
            c = r["chi2_red"]
            cls = " class='best'" if tool == best_tool else ""
            md.append(f"| {tool} | {c} | {r['chi2_kind']} |")
            h.append(f"<tr{cls}><td class='tool'>{tool}</td><td class='num'>{html.escape(str(c))}</td>"
                     f"<td><small>{html.escape(r['chi2_kind'])}</small></td></tr>")
        md += ["", f"_lowest &chi;&sup2;: **{best_tool or 'n/a'}**_", ""]
        h += ["</table>", f"<p><small>lowest &chi;&sup2;: <b>{best_tool or 'n/a'}</b></small></p>"]

        # line flux matrix: rows = line/component, cols = tools
        cells: dict[tuple[str, str], dict[str, float]] = {}
        for r in lines:
            if r["tag"] != tag:
                continue
            comp = r.get("component") or "-"
            key = (r["line"], comp)
            cells.setdefault(key, {})[r["tool"]] = _num(r["flux_1e17"])
        order = [(ln, c) for ln in LINES for c in ("broad", "narrow", "outflow", "total", "-")
                 if (ln, c) in cells]
        md += ["| line | component | " + " | ".join(TOOLS) + " |",
               "|---|---|" + "---:|" * len(TOOLS)]
        h += ["<table><tr><th>line</th><th>component</th>" +
              "".join(f"<th>{t}</th>" for t in TOOLS) + "</tr>"]
        for key in order:
            vals = cells[key]
            mdrow = f"| {key[0]} | {key[1]} | " + " | ".join(
                (f"{vals[t]:.3g}" if t in vals and vals[t] is not None else "") for t in TOOLS) + " |"
            md.append(mdrow)
            h.append(f"<tr><td>{key[0]}</td><td>{key[1]}</td>" + "".join(
                f"<td class='num'>{vals[t]:.3g}</td>" if t in vals and vals[t] is not None else "<td></td>"
                for t in TOOLS) + "</tr>")
        if order:
            md += ["", "_flux in 1e-17 erg s-1 cm-2_", ""]
            h += ["</table>", "<p><small>flux in 1e-17 erg s<sup>-1</sup> cm<sup>-2</sup></small></p>"]

        # artifact links
        md.append("**products:**")
        h.append("<p><small>products:</small></p><ul>")
        for tool in TOOLS:
            tdir = results / tool / tag
            if not tdir.is_dir():
                continue
            files = sorted(f for f in tdir.rglob("*") if f.is_file())
            rels = [f.relative_to(results).as_posix() for f in files]
            md.append(f"- `{tool}`: " + ", ".join(f"[{Path(r).name}]({r})" for r in rels))
            h.append(f"<li><b>{tool}</b>: " + ", ".join(
                f"<a href='{html.escape(r)}'>{html.escape(Path(r).name)}</a>" for r in rels) + "</li>")
        h.append("</ul>")
        md.append("")

    h.append("</body></html>")
    return "\n".join(h), "\n".join(md)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", type=Path, default=Path("runs"))
    p.add_argument("--results", type=Path, default=Path("results"))
    args = p.parse_args(argv)
    hdoc, mdoc = build(args.runs, args.results)
    (args.results / "report.html").write_text(hdoc)
    (args.results / "report.md").write_text(mdoc)
    print(f"wrote {args.results/'report.html'} and {args.results/'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
