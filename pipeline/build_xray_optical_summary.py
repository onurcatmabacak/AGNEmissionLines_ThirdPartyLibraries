#!/usr/bin/env python3
"""Combine the per-source crossmission JSONs into a two-object overview."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("3C120_z_0.0330", "PDS456_z_0.1840")
OUT = ROOT / "docs"


def main() -> int:
    rows = []
    for source in SOURCES:
        p = ROOT / "outputs" / source / "crossmission" / "xray_optical_comparison.json"
        if not p.exists():
            raise SystemExit(f"missing {p}; run crossmission first")
        rows.append(json.loads(p.read_text()))
    OUT.mkdir(exist_ok=True)
    with (OUT / "xray_optical_comparison.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["source", "xray_tool", "optical_line", "optical_flux_erg_cm2_s",
                    "xray_flux_erg_cm2_s", "optical_ew_rest_A", "xray_ew_rest_eV",
                    "optical_luminosity_erg_s", "xray_luminosity_erg_s", "quality"])
        for r in rows:
            line = r["optical_line"]
            w.writerow([r["source"], r["xray_tool"], line,
                        r["optical_flux_erg_cm2_s"], r["xray"]["flux"],
                        r["optical"].get("ew_rest_A", {}).get(line, {}).get("ew_rest_A"),
                        r["xray"]["ew_rest_eV"], r["optical_luminosity_erg_s"],
                        r["xray_luminosity_erg_s"], r["quality"]])

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
    for r in rows:
        line = r["optical_line"]
        color = "tab:blue" if r["quality"] == "accepted" else "tab:orange"
        ax = axes[0]
        ax.scatter(r["xray_luminosity_erg_s"], r["optical_luminosity_erg_s"],
                   s=100, color=color, edgecolor="k", zorder=3)
        dx, ha = (-8, "right") if r["source"].startswith("PDS") else (7, "left")
        ax.annotate(f"{r['source'].split('_z_')[0]} ({line})",
                    (r["xray_luminosity_erg_s"], r["optical_luminosity_erg_s"]),
                    xytext=(dx, 7), textcoords="offset points", fontsize=9, ha=ha)
        ax = axes[1]
        ew = r["optical"].get("ew_rest_A", {}).get(line, {}).get("ew_rest_A")
        ax.scatter(r["xray"]["ew_rest_eV"], ew, s=100, color=color,
                   edgecolor="k", zorder=3)
        ax.annotate(f"{r['source'].split('_z_')[0]} ({line})",
                    (r["xray"]["ew_rest_eV"], ew), xytext=(7, 7),
                    textcoords="offset points", fontsize=9)
    axes[0].set_xscale("log"); axes[0].set_yscale("log")
    axes[0].set_xlim(1.0e42, 3.0e42)
    axes[0].set_ylim(5.0e41, 2.0e44)
    axes[0].set_xticks([1.2e42, 1.5e42, 2.0e42, 2.5e42])
    axes[0].set_xticklabels(["1.2", "1.5", "2.0", "2.5"])
    axes[0].set_xlabel(r"$L_{\rm Fe\,K\alpha}$ ($10^{42}$ erg s$^{-1}$)")
    axes[0].set_ylabel("UV/optical line luminosity (erg s$^{-1}$)")
    axes[0].set_title("same-object luminosity comparison", fontsize=10)
    axes[1].set_xscale("log"); axes[1].set_yscale("log")
    axes[1].set_xlim(20, 120)
    ew_values = [r["optical"].get("ew_rest_A", {}).get(r["optical_line"], {}).get("ew_rest_A")
                 for r in rows]
    ew_values = [float(v) for v in ew_values if v is not None]
    if ew_values:
        lo, hi = min(ew_values), max(ew_values)
        pad = max(5.0, 0.2 * (hi - lo))
        axes[1].set_ylim(max(0.1, lo - pad), hi + pad)
    axes[1].set_xlabel("Fe Kα rest EW (eV)")
    axes[1].set_ylabel("UV/optical line rest EW (Å)")
    axes[1].set_title("equivalent-width comparison", fontsize=10)
    for ax in axes:
        ax.grid(alpha=0.25)
    axes[0].text(0.03, 0.95, "orange = provisional\n(model/X-ray gate)",
                 transform=axes[0].transAxes, fontsize=7, va="top",
                 bbox={"facecolor": "white", "alpha": 0.7, "edgecolor": "0.8"})
    fig.suptitle("X-ray Fe Kα vs same-object UV/optical emission lines", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "xray_optical_comparison.png", dpi=180)
    fig.savefig(OUT / "xray_optical_comparison.pdf")
    plt.close(fig)
    print("wrote docs/xray_optical_comparison.{png,pdf,csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
