#!/usr/bin/env python3
"""Cross-band emission-line ratios with uncertainties and expected ranges."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# name, numerator aliases, denominator aliases, expected (low, high), note
RATIOS = [
    ("Paalpha/Halpha", ["Paalpha18756", "Paalpha", "Pa-alpha"], ["Halpha6563", "Halpha"], (0.04, 0.25), "case-B NIR/optical"),
    ("Brgamma/Halpha", ["Brgamma21661", "Brgamma", "Br-gamma"], ["Halpha6563", "Halpha"], (0.005, 0.10), "case-B NIR/optical"),
    ("OIII88/OIII5007", ["OIII88356", "OIII88", "[OIII]88"], ["OIII5007", "[OIII]5007"], (0.1, 2.0), "PDR/AGN"),
    ("NeIII/NeII", ["NeIII15555", "NeIII", "[NeIII]15.6"], ["NeII12814", "NeII", "[NeII]12.8"], (0.1, 5.0), "ionization"),
    ("SIII18.7/SIII33.5", ["SIII18713", "SIII18.7", "[SIII]18.7"], ["SIII33480", "SIII33.5", "[SIII]33.5"], (0.5, 5.0), "density/PDR"),
    ("CII158/OI63", ["CII157741", "CII158", "[CII]158"], ["OI63184", "OI63", "[OI]63"], (1.0, 20.0), "PDR/AGN FIR"),
    ("CII158/NII122", ["CII157741", "CII158", "[CII]158"], ["NII121898", "NII122", "[NII]122"], (1.0, 20.0), "PDR FIR"),
]


def norm(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


def load(path):
    data = {}
    with open(path) as fh:
        for r in csv.DictReader(fh):
            obj = r["object"]
            line = norm(r["line"])
            data.setdefault(obj, {})[line] = (float(r["flux"]), float(r.get("flux_err", "nan") or "nan"))
    return data


def find(d, aliases):
    for a in aliases:
        k = norm(a)
        if k in d:
            return d[k]
    return None


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    data = load(args.input)
    rows = []
    for obj, d in sorted(data.items()):
        for name, num_alias, den_alias, (lo, hi), note in RATIOS:
            num = find(d, num_alias); den = find(d, den_alias)
            if not num or not den or den[0] == 0:
                continue
            ratio = num[0] / den[0]
            err = abs(ratio) * np.sqrt((num[1] / num[0]) ** 2 + (den[1] / den[0]) ** 2) if num[0] and num[1] >= 0 and den[1] >= 0 else np.nan
            rows.append({"object": obj, "ratio": name, "value": ratio, "err": err,
                         "expected_low": lo, "expected_high": hi, "note": note,
                         "consistent": bool(np.isfinite(err)
                                            and lo * (1 - 1e-6) <= ratio <= hi * (1 + 1e-6))})
    out = args.output / "crossband_ratios.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["object", "ratio"])
        w.writeheader(); w.writerows(rows)
    (args.output / "crossband_summary.json").write_text(json.dumps(
        {"n_objects": len(data), "n_ratios": len(rows),
         "consistent": sum(r["consistent"] for r in rows)}, indent=2))
    if rows:
        objs = sorted({r["object"] for r in rows})
        fig, ax = plt.subplots(figsize=(10, max(3, 0.7 * len(rows) + 1)))
        y = np.arange(len(rows))[::-1]
        for yi, r in zip(y, rows):
            ax.errorbar(r["value"], yi, xerr=r["err"] if np.isfinite(r["err"]) else None,
                        fmt="o", color="C2" if r["consistent"] else "C3", ms=5)
            ax.plot([r["expected_low"], r["expected_high"]], [yi, yi], color="0.6", lw=4, alpha=0.35)
        ax.set_yticks(y); ax.set_yticklabels([f"{r['object']}  {r['ratio']}" for r in rows], fontsize=7)
        ax.set_xscale("log"); ax.set_xlabel("line ratio (log scale)")
        ax.set_title("Cross-band line ratios (bars = expected range)")
        ax.grid(axis="x", ls=":", alpha=0.5)
        fig.tight_layout(); fig.savefig(args.output / "crossband_ratios.png", dpi=140)
        fig.savefig(args.output / "crossband_ratios.pdf"); plt.close(fig)
    print(f"[crossband] {len(rows)} ratios for {len(data)} object(s) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
