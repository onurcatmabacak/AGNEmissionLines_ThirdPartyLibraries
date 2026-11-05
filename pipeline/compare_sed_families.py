#!/usr/bin/env python3
"""Compare CIGALE SKIRTOR/Fritz with AGNfitter-rx for each QSO."""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pipeline.io_layout import iter_sources, output_dir  # noqa: E402

LSUN_W = 3.828e26


def main():
    rows = []
    for src in iter_sources():
        key = src["key"]
        cig = output_dir(key, "cigale_sed") / "model_family.csv"
        if cig.exists():
            with cig.open() as fh:
                for r in csv.DictReader(fh):
                    try:
                        lagn = math.log10(float(r["agn_luminosity_W"]) / LSUN_W)
                    except Exception:
                        lagn = float("nan")
                    try:
                        lmstar = math.log10(float(r["m_star_Msun"]))
                    except Exception:
                        lmstar = float("nan")
                    rows.append({
                        "source": key, "engine": "CIGALE", "family": r["agn_model"],
                        "fracAGN": r.get("fracAGN", ""),
                        "logLAGN_Lsun": f"{lagn:.3f}" if math.isfinite(lagn) else "",
                        "logMstar": f"{lmstar:.3f}" if math.isfinite(lmstar) else "",
                        "chi2_red": r.get("reduced_chi2", ""),
                    })
        ag = output_dir(key, "agnfitter_sed") / "agnfitter_summary.csv"
        if ag.exists():
            d = {}
            with ag.open() as fh:
                for r in csv.DictReader(fh):
                    try:
                        d[r["quantity"]] = float(r["median"])
                    except Exception:
                        pass
            rows.append({
                "source": key, "engine": "AGNfitter-rx", "family": "SKIRTOR_1P",
                "fracAGN": f"{d.get('AGNfrac(0.1-1)', float('nan')):.4g}",
                "logLAGN_Lsun": f"{d.get('LAGN(0.1-30)', float('nan')) - math.log10(3.828e33):.3f}",
                "logMstar": f"{d.get('logMstar', float('nan')):.3f}",
                "chi2_red": "",
            })
    out = ROOT / "docs" / "sed_family_comparison.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["source", "engine", "family", "fracAGN",
                                           "logLAGN_Lsun", "logMstar", "chi2_red"])
        w.writeheader(); w.writerows(rows)
    for src in iter_sources():
        sub = [r for r in rows if r["source"] == src["key"]]
        if not sub:
            continue
        p = output_dir(src["key"], "cigale_sed") / "sed_family_comparison.csv"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(sub[0]))
            w.writeheader(); w.writerows(sub)
    print(f"wrote {out} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
