#!/usr/bin/env python3
"""Compare a sharded MaNGA DAP product against the serial one.

The pPXF shard is exact by construction (the unmodified upstream fit method is
called on slices), but the claim is only credible if the *products* agree.  This
script compares a sharded product tree against a serial reference:

    python pipeline/compare_manga_shard.py \
        outputs/manga_dap/NGC1194_z_0.0136/full \
        outputs/manga_dap/NGC1194_z_0.0136/full_shard4

It checks the line-flux summary (median / summed flux per line), the spaxel
BPT census and the run status, and exits non-zero when a difference exceeds the
tolerance.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compare(serial: Path, sharded: Path, rtol: float = 1e-6) -> list[str]:
    problems: list[str] = []

    for name in ("run.json", "line_summary.csv", "maps_stats.json"):
        if not (sharded / name).exists():
            problems.append(f"sharded product is missing {name}")
    if problems:
        return problems

    run_s = json.loads((serial / "run.json").read_text())
    run_h = json.loads((sharded / "run.json").read_text())
    if run_h.get("status") != "ok":
        problems.append(f"sharded status is {run_h.get('status')!r}, not 'ok'")
    if run_h.get("dap_status_code") not in (0, None):
        problems.append(f"sharded dap_status_code is {run_h.get('dap_status_code')}")

    # line fluxes per line
    s_rows = {r["line"]: r for r in _read_csv(serial / "line_summary.csv")}
    h_rows = {r["line"]: r for r in _read_csv(sharded / "line_summary.csv")}
    if set(s_rows) != set(h_rows):
        problems.append(f"line sets differ: {sorted(set(s_rows) ^ set(h_rows))}")
    worst = 0.0
    for line in sorted(set(s_rows) & set(h_rows)):
        for col in ("median_flux_1e17", "sum_flux_1e17", "median_snr", "n_spaxels"):
            a, b = _num(s_rows[line].get(col)), _num(h_rows[line].get(col))
            if a is None or b is None:
                continue
            denom = abs(a) if abs(a) > 1e-12 else 1.0
            rel = abs(a - b) / denom
            worst = max(worst, rel)
            if rel > rtol:
                problems.append(f"{line}.{col}: serial={a} sharded={b} rel={rel:.3e}")

    # BPT census
    s_bpt = json.loads((serial / "maps_stats.json").read_text()).get("bpt", {})
    h_bpt = json.loads((sharded / "maps_stats.json").read_text()).get("bpt", {})
    for key in ("seyfert", "liner", "composite", "star_forming", "agn_unclassified", "n_total"):
        if key in s_bpt and s_bpt.get(key) != h_bpt.get(key):
            problems.append(f"BPT {key}: serial={s_bpt.get(key)} sharded={h_bpt.get(key)}")

    print(f"serial : {serial}")
    print(f"sharded: {sharded}  ({run_h.get('runtime_seconds', 0):.0f} s)")
    print(f"worst relative difference in line fluxes: {worst:.2e} (rtol={rtol:g})")
    if s_bpt and h_bpt:
        print("BPT serial :", {k: s_bpt.get(k) for k in ("seyfert", "liner", "composite", "star_forming", "n_total")})
        print("BPT sharded:", {k: h_bpt.get(k) for k in ("seyfert", "liner", "composite", "star_forming", "n_total")})
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("serial", type=Path)
    ap.add_argument("sharded", type=Path)
    ap.add_argument("--rtol", type=float, default=1e-6)
    args = ap.parse_args(argv)
    problems = compare(args.serial, args.sharded, args.rtol)
    if problems:
        print("\nFAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print("\nOK: sharded product matches the serial reference")
    return 0


if __name__ == "__main__":
    sys.exit(main())
