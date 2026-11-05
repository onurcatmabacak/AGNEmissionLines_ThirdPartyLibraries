#!/usr/bin/env python3
"""Build a real cross-band CSV from PAHFIT MIR features and FIR line fits."""
from __future__ import annotations

import ast
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pipeline.io_layout import load_source, output_dir, prepared_dir  # noqa: E402

MIR_LINES = {
    "[NeII]": "NeII12814",
    "[NeIII]": "NeIII15555",
    "[SIII]_18": "SIII18713",
    "[SIII]_33": "SIII33480",
    "[SIV]": "SIV10511",
    "[OIV]": "OIV25890",
}


def first(value):
    if value is None:
        return float("nan")
    s = str(value)
    try:
        return float(ast.literal_eval(s)[0])
    except Exception:
        try:
            return float(s.strip("()").split(",")[0])
        except Exception:
            return float("nan")


def main(key: str) -> int:
    src = load_source(key)
    out = output_dir(key, "pahfit_mir")
    rows = []
    for feat in (out / "pahfit_features.csv", *out.glob("pahfit_features.csv")):
        if not feat.exists():
            continue
        with feat.open() as fh:
            for r in csv.DictReader(fh):
                name = r.get("name", "")
                if name not in MIR_LINES:
                    continue
                p = first(r.get("power"))
                if p == p and p > 0:
                    rows.append({"object": src["name"], "line": MIR_LINES[name],
                                 "band": "MIR", "flux": p, "flux_err": 0.1 * p})
        break
    fir = output_dir(key, "fir_linefit")
    for f in fir.glob("*.fir_lines.csv"):
        with f.open() as fh:
            for r in csv.DictReader(fh):
                if r.get("detected", "").lower() not in ("true", "1"):
                    continue
                rows.append({"object": src["name"], "line": r["line"],
                             "band": "FIR", "flux": float(r["flux"]),
                             "flux_err": float(r["flux_err"]) if r.get("flux_err") not in ("", "nan") else float("nan")})
    if not rows:
        print("no crossband lines")
        return 1
    dest = prepared_dir(key, "crossband") / "crossband.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["object", "line", "band", "flux", "flux_err"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {dest} ({len(rows)} lines)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: build_crossband_from_outputs.py <source_key>")
    raise SystemExit(main(sys.argv[1]))
