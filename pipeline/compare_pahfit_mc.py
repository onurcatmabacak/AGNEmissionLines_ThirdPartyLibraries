#!/usr/bin/env python3
"""Compare PAHFIT Monte Carlo uncertainty runs across objects and methods.

Reads ``pahfit_uncertainties.csv`` + ``pahfit_summary.json`` from one or more
PAHFIT output directories and writes a cross-object comparison table/figure.

Example
-------
    python pipeline/compare_pahfit_mc.py
    python pipeline/compare_pahfit_mc.py \
        --run "PDS456 short=bootstrap"=outputs/PDS456_z_0.1840/pahfit_mir/short \
        --run "NGC4151"=outputs/NGC4151_z_0.0033/pahfit_mir
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_RUNS = [
    ("PDS456 short (bootstrap)", ROOT / "outputs/PDS456_z_0.1840/pahfit_mir/short"),
    ("PDS456 short (covariance)", ROOT / "outputs/PDS456_z_0.1840/pahfit_mir/short_covariance"),
    ("PDS456 long (bootstrap)", ROOT / "outputs/PDS456_z_0.1840/pahfit_mir/long"),
    ("PDS456 both (bootstrap)", ROOT / "outputs/PDS456_z_0.1840/pahfit_mir/both"),
    ("NGC4151 (covariance)", ROOT / "outputs/NGC4151_z_0.0033/pahfit_mir"),
    ("NGC4151 (bootstrap)", ROOT / "outputs/NGC4151_z_0.0033/pahfit_mir/bootstrap_200"),
    ("VV114 (covariance)", ROOT / "outputs/VV114_z_0.0200/pahfit_mir"),
    ("VV114 (bootstrap)", ROOT / "outputs/VV114_z_0.0200/pahfit_mir/bootstrap_200"),
    ("NGC253 (bootstrap)", ROOT / "outputs/NGC253_z_0.0008/pahfit_mir"),
]

# Curated common features; the script skips any that a run does not contain.
FEATURES = [
    "[NeII]", "[NeIII]", "[SIII]_18", "[OIV]", "[ArII]", "[ArIII]",
    "H2_S(6)", "PAH_6.2", "PAH_7.7", "PAH_8.6", "PAH_11.3", "PAH_17",
    "dust_cont02", "starlight",
]

OBJECT_COLORS = {
    "PDS456 short (bootstrap)": "#d62728",
    "PDS456 short (covariance)": "#ff9896",
    "PDS456 long (bootstrap)": "#9467bd",
    "PDS456 both (bootstrap)": "#8c564b",
    "NGC4151 (covariance)": "#1f77b4",
    "NGC4151 (bootstrap)": "#aec7e8",
    "VV114 (covariance)": "#2ca02c",
    "VV114 (bootstrap)": "#98df8a",
    "NGC253 (bootstrap)": "#ff7f0e",
}


def read_run(label: str, path: Path) -> list[dict]:
    unc = path / "pahfit_uncertainties.csv"
    if not unc.exists():
        print(f"[skip] {label}: no {unc}")
        return []
    summary = {}
    sp = path / "pahfit_summary.json"
    if sp.exists():
        try:
            summary = json.loads(sp.read_text())
        except Exception:
            summary = {}
    mc = summary.get("mc", {}) or {}
    cov = mc.get("covariance", {}) or {}
    rows = []
    with unc.open() as fh:
        for r in csv.DictReader(fh):
            try:
                flux = float(r["flux"])
                err = float(r["err"])
            except Exception:
                continue
            if not (np.isfinite(flux) and np.isfinite(err) and flux != 0):
                continue
            rows.append({
                "run": label,
                "object": label.split()[0],
                "method": r.get("method", mc.get("method", "")),
                "feature": r["feature"],
                "kind": r.get("kind", ""),
                "quantity": r.get("quantity", ""),
                "unit": r.get("unit", ""),
                "flux": flux,
                "err": err,
                "rel_err": err / abs(flux),
                "n_samples": int(float(r.get("n_samples", mc.get("n_samples", 0)) or 0)),
                "status": r.get("status", ""),
                "fit_rms_rel": float(summary.get("rms_rel", np.nan)),
                "chi2_red": float(summary.get("chi2_red", np.nan) or np.nan),
                "mc_runtime_s": float(mc.get("runtime_s", np.nan)),
                "rank": int(cov.get("rank", -1)),
                "n_free": int(cov.get("n_free", -1)),
                "rank_deficient": bool(cov.get("rank_deficient", False)),
            })
    return rows


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", action="append", default=None,
                   metavar="LABEL=PATH",
                   help="add/replace a run; repeatable")
    p.add_argument("--out", type=Path,
                   default=ROOT / "outputs/pahfit_mc_comparison.png")
    p.add_argument("--csv", type=Path,
                   default=ROOT / "outputs/pahfit_mc_comparison.csv")
    args = p.parse_args(argv)

    runs = []
    if args.run:
        for item in args.run:
            if "=" not in item:
                raise SystemExit(f"--run expects LABEL=PATH, got {item!r}")
            label, path = item.split("=", 1)
            runs.append((label, Path(path)))
    else:
        runs = DEFAULT_RUNS

    all_rows = []
    for label, path in runs:
        all_rows.extend(read_run(label, path))
    if not all_rows:
        raise SystemExit("no uncertainty rows found")

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    cols = list(all_rows[0].keys())
    with args.csv.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(all_rows)
    print(f"[compare] wrote {args.csv} ({len(all_rows)} rows)")

    by_run = {}
    for r in all_rows:
        by_run.setdefault(r["run"], {})[r["feature"]] = r
    labels = [label for label, _ in runs if label in by_run]
    feats = [f for f in FEATURES if any(f in by_run[label] for label in labels)]
    if not feats:
        feats = sorted({r["feature"] for r in all_rows})[:20]

    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.25, 1.0])
    ax = fig.add_subplot(gs[0, :])
    x = np.arange(len(feats))
    for label in labels:
        d = by_run[label]
        xs, ys = [], []
        for i, f in enumerate(feats):
            if f in d:
                xs.append(i)
                ys.append(d[f]["rel_err"])
        ax.scatter(xs, ys, s=46, label=label,
                   color=OBJECT_COLORS.get(label, None),
                   edgecolor="k", linewidth=0.3, zorder=3)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(feats, rotation=50, ha="right", fontsize=8)
    ax.set_ylabel("1-sigma / |flux|")
    ax.set_title("PAHFIT feature-flux uncertainties across objects and MC methods")
    ax.grid(alpha=0.25, axis="y")
    ax.legend(fontsize=8, ncol=2)

    def method_compare(ax, obj_prefix, title):
        cov_label = next((l for l in labels if l.startswith(obj_prefix)
                          and "covariance" in l), None)
        boot_label = next((l for l in labels if l.startswith(obj_prefix)
                           and "bootstrap" in l), None)
        if not cov_label or not boot_label:
            ax.text(0.5, 0.5, f"no covariance+bootstrap pair for {obj_prefix}",
                    ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            return
        common = [f for f in FEATURES
                  if f in by_run[cov_label] and f in by_run[boot_label]]
        if not common:
            ax.text(0.5, 0.5, f"no common features for {obj_prefix}",
                    ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            return
        xv = np.array([by_run[cov_label][f]["rel_err"] for f in common])
        yv = np.array([by_run[boot_label][f]["rel_err"] for f in common])
        ax.scatter(xv, yv, s=55, color="#444444", edgecolor="k", linewidth=0.3)
        lim = [min(xv.min(), yv.min()) * 0.5, max(xv.max(), yv.max()) * 2.0]
        ax.plot(lim, lim, "k--", lw=0.8)
        for f, a, b in zip(common, xv, yv):
            ax.annotate(f, (a, b), fontsize=6, xytext=(3, 2),
                        textcoords="offset points")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.set_xlabel(f"{cov_label}: 1-sigma / |flux|")
        ax.set_ylabel(f"{boot_label}: 1-sigma / |flux|")
        ax.set_title(title, fontsize=9)
        ax.grid(alpha=0.25)
        sample = next(iter(by_run[cov_label].values()))
        if sample["rank_deficient"]:
            ax.text(0.02, 0.98,
                    f"covariance rank {sample['rank']}/{sample['n_free']} "
                    f"(rank-deficient; null line errors omitted)",
                    transform=ax.transAxes, va="top", fontsize=7, color="0.35")

    method_compare(fig.add_subplot(gs[1, 0]), "PDS456",
                   "PDS 456 short: covariance vs bootstrap")
    method_compare(fig.add_subplot(gs[1, 1]), "NGC4151",
                   "NGC 4151: covariance vs bootstrap")

    lines = []
    for label in labels:
        d = by_run[label]
        sample = next(iter(d.values()))
        lines.append(
            f"{label}: method={sample['method']}, N={sample['n_samples']}, "
            f"MC={sample['mc_runtime_s']:.1f}s, rms_rel={sample['fit_rms_rel']:.4f}, "
            f"chi2_red={sample['chi2_red']:.3g}, "
            f"cov_rank={sample['rank']}/{sample['n_free']}"
            + (" (rank-deficient)" if sample["rank_deficient"] else "")
        )
    fig.text(0.01, 0.005, "\n".join(lines), fontsize=7, color="0.3",
             va="bottom")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[compare] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
