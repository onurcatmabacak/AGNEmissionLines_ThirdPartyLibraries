#!/usr/bin/env python3
"""Visualise the statistical confirmation (parameter uncertainties) of every
tool for every object.

For each ``runs/<object>/outputs/<tool>/`` it extracts the line-flux estimate and
its uncertainty from the tool's native posterior/Monte-Carlo products, and
writes one figure per (object, tool) to::

    statistical confirmation/<tool>/<object>_<tool>.pdf
    statistical confirmation/<tool>/<object>_<tool>.png

plus a per-object overview (all five tools) and a machine-readable summary::

    statistical confirmation/by_object/<object>_all_tools.pdf
    statistical confirmation/summary.csv

Uncertainty sources
-------------------
badass      emcee MCMC: results/lines.csv flux + 68%/95% CI from par_table.fits
            (the *_FLUX parameters are log10(flux); CI columns are dex errors)
pyqsofit    emcee MCMC: results/lines.csv (output.fits *_err columns)
fantasy_agn Monte-Carlo: results/lines.csv (my_sdss_pars.csv refit scatter)
gelato      bootstrap (NBoot=100): results/lines.csv (PARAMS row scatter)
gleam       LMFIT analytic: results/lines.csv (linefits*.fits *_err columns)

Usage
-----
    python pipeline/make_statistical_confirmation.py
    python pipeline/make_statistical_confirmation.py --objects 06872228427
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from score_fits import REST  # noqa: E402

TOOLS = ("pyqsofit", "badass", "fantasy_agn", "gelato", "gleam")
LINE_ORDER = {k: i for i, k in enumerate(["OII3727", "Hb4861", "OIII4959", "OIII5007",
                                          "NII6548", "Ha6563", "NII6585",
                                          "SII6718", "SII6732"])}
COMP_ORDER = {"broad": 0, "total": 1, "narrow": 2, "outflow": 3}
COMP_COLOR = {"broad": "#c0392b", "total": "#7f8c8d", "narrow": "#2471a3", "outflow": "#8e44ad"}

# BADASS parameter prefix -> (line, component)
BADASS_MAP = {
    "BR_H_ALPHA": ("Ha6563", "broad"), "NA_H_ALPHA": ("Ha6563", "narrow"),
    "H_ALPHA_COMP": ("Ha6563", "total"),
    "BR_H_BETA": ("Hb4861", "broad"), "NA_H_BETA": ("Hb4861", "narrow"),
    "H_BETA_COMP": ("Hb4861", "total"),
    "BR_OIII_b": ("OIII5007", "broad"), "NA_OIII_b": ("OIII5007", "narrow"),
    "OIII_b_COMP": ("OIII5007", "total"),
    "BR_OIII_a": ("OIII4959", "broad"), "NA_OIII_a": ("OIII4959", "narrow"),
    "OIII_a_COMP": ("OIII4959", "total"),
    "NA_NII_6585": ("NII6585", "narrow"), "NA_NII_6549": ("NII6548", "narrow"),
    "NA_SII_6716": ("SII6718", "narrow"), "NA_SII_6731": ("SII6732", "narrow"),
    "NA_OII": ("OII3727", "narrow"),
}
METHOD = {
    "badass": "BADASS emcee MCMC",
    "pyqsofit": "PyQSOFit emcee MCMC",
    "fantasy_agn": "FANTASY Monte-Carlo (refits)",
    "gelato": "GELATO bootstrap (NBoot)",
    "gleam": "GLEAM LMFIT (analytic)",
}


def _f(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else np.nan
    except (TypeError, ValueError):
        return np.nan


def load_lines(results: Path):
    """dict[(tag, tool)] -> list of line rows."""
    table = {}
    p = results / "lines.csv"
    if not p.exists():
        return table
    with p.open() as fh:
        for r in csv.DictReader(fh):
            table.setdefault((r["tag"], r["tool"]), []).append(r)
    return table


def badass_points(out: Path, line_rows):
    """Line flux + asymmetric 68% error from the emcee CI table."""
    from astropy.io import fits
    pars = None
    for cand in out.rglob("par_table.fits"):
        try:
            pars = fits.open(cand)[1].data
            break
        except Exception:
            continue
    if pars is None:
        return []
    param = {str(p): i for i, p in enumerate(pars["parameter"])}
    best_flux = {(r["line"], r["component"]): _f(r["flux_1e17"]) for r in line_rows}
    pts = []
    for prefix, (line, comp) in BADASS_MAP.items():
        k = f"{prefix}_FLUX"
        if k not in param:
            continue
        i = param[k]
        logflux = _f(pars["best_fit"][i])
        lo68 = _f(pars["ci_68_low"][i])
        up68 = _f(pars["ci_68_upp"][i])
        flux = best_flux.get((line, comp), np.nan)
        if not math.isfinite(flux) and math.isfinite(logflux):
            flux = 10.0 ** logflux * 1e17
        if not (math.isfinite(flux) and math.isfinite(lo68) and math.isfinite(up68)):
            continue
        e_lo = abs(flux) * (1.0 - 10.0 ** (-lo68))
        e_hi = abs(flux) * (10.0 ** (up68) - 1.0)
        pts.append(dict(line=line, comp=comp, flux=flux, elo=e_lo, ehi=e_hi,
                        method=METHOD["badass"]))
    return pts


def csv_points(tool: str, line_rows):
    pts = []
    for r in line_rows:
        flux = _f(r["flux_1e17"])
        err = _f(r["flux_err_1e17"])
        if not math.isfinite(flux):
            continue
        pts.append(dict(line=r["line"], comp=r["component"], flux=flux,
                        elo=err, ehi=err, method=METHOD[tool]))
    return pts


def gather(obj_dir: Path, tool: str, lines_table):
    out = obj_dir / "outputs" / tool
    if not out.is_dir():
        return []
    rows = lines_table.get((obj_dir.name, tool), [])
    if tool == "badass":
        # Use the emcee CI table; never fall back to the (zero) log-derived
        # errors.  An empty result means the MCMC did not run for this object.
        return badass_points(out, rows)
    return csv_points(tool, rows)


def _sort_key(p):
    return (LINE_ORDER.get(p["line"], 99), COMP_ORDER.get(p["comp"], 9))


def draw_flux(ax, pts, title):
    pts = sorted(pts, key=_sort_key)
    if not pts:
        ax.text(0.5, 0.5, "no uncertainty data", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return
    y = np.arange(len(pts))[::-1]
    x = np.array([p["flux"] for p in pts], float)
    elo = np.array([p["elo"] for p in pts], float)
    ehi = np.array([p["ehi"] for p in pts], float)
    cols = [COMP_COLOR.get(p["comp"], "k") for p in pts]
    for xi, yi, lo, hi, c in zip(x, y, elo, ehi, cols):
        if math.isfinite(hi) and math.isfinite(lo):
            ax.errorbar(xi, yi, xerr=np.array([[lo], [hi]]), fmt="o", color=c,
                        ms=5, elinewidth=1.2, capsize=2)
        else:
            ax.plot(xi, yi, "o", color=c, ms=5)
    labels = [f"{p['line']} {p['comp']}" for p in pts]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("line flux (10$^{-17}$ erg s$^{-1}$ cm$^{-2}$)", fontsize=9)
    ax.set_title(title, fontsize=10)
    ax.grid(axis="x", ls=":", alpha=0.5)
    ax.tick_params(axis="x", labelsize=8)
    # legend by component
    seen = []
    for p in pts:
        if p["comp"] not in seen:
            seen.append(p["comp"])
    for comp in seen:
        ax.plot([], [], "o", color=COMP_COLOR.get(comp, "k"), label=comp, ms=5)
    if seen:
        ax.legend(fontsize=7, frameon=False, loc="lower right")


def draw_rel(ax, pts, title):
    pts = sorted(pts, key=_sort_key)
    if not pts:
        ax.set_axis_off()
        return
    rel = []
    for p in pts:
        e = np.nanmax([abs(p["elo"]), abs(p["ehi"])]) if (math.isfinite(p["elo"]) or math.isfinite(p["ehi"])) else np.nan
        rel.append(100.0 * e / abs(p["flux"]) if (math.isfinite(e) and p["flux"]) else np.nan)
    y = np.arange(len(pts))[::-1]
    for xi, yi, p, rr in zip(rel, y, pts, rel):
        if math.isfinite(rr):
            ax.barh(yi, rr, color=COMP_COLOR.get(p["comp"], "k"), alpha=0.75, height=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{p['line']} {p['comp']}" for p in pts], fontsize=8)
    ax.set_xlabel("relative uncertainty (%)", fontsize=9)
    ax.set_title(title, fontsize=10)
    ax.grid(axis="x", ls=":", alpha=0.5)
    ax.tick_params(axis="x", labelsize=8)


def has_mcmc_chain(out: Path) -> bool:
    return any(out.rglob("MCMC_chain.csv"))


def make_one(obj_dir: Path, tool: str, pts, outdir: Path):
    pdir = outdir / tool
    pdir.mkdir(parents=True, exist_ok=True)
    method = METHOD[tool]
    if tool == "badass" and not has_mcmc_chain(obj_dir / "outputs" / tool):
        method += "  [NO CHAIN — max-likelihood/stale]"
    n = len(pts)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, max(4.0, 0.33 * n + 2.2)),
                                 gridspec_kw={"width_ratios": [1.35, 1.0]})
    draw_flux(a1, pts, f"{obj_dir.name} — {tool}: line flux ± 68%")
    draw_rel(a2, pts, "relative uncertainty")
    fig.suptitle(f"{tool} — {obj_dir.name}  |  {method}  |  N={n}", fontsize=11, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    stem = pdir / f"{obj_dir.name}_{tool}"
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".png"), dpi=130, bbox_inches="tight")
    plt.close(fig)


def make_overview(obj_dir: Path, per_tool, outdir: Path):
    bdir = outdir / "by_object"
    bdir.mkdir(parents=True, exist_ok=True)
    rows = [(t, per_tool.get(t, [])) for t in TOOLS]
    nmax = max(4, max((len(p) for _, p in rows), default=4))
    fig, axes = plt.subplots(len(TOOLS), 1, figsize=(12, max(6, 0.22 * nmax * len(TOOLS) + 3)),
                             squeeze=False)
    for ax, (tool, pts) in zip(axes[:, 0], rows):
        draw_flux(ax, pts, f"{tool}  (N={len(pts)})")
    fig.suptitle(f"{obj_dir.name} — statistical confirmation across tools", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    fig.savefig(bdir / f"{obj_dir.name}_all_tools.pdf", bbox_inches="tight")
    fig.savefig(bdir / f"{obj_dir.name}_all_tools.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--runs", type=Path, default=Path("runs"))
    p.add_argument("--results", type=Path, default=Path("results"))
    p.add_argument("--out", type=Path, default=Path("statistical confirmation"))
    p.add_argument("--objects", nargs="*", default=None)
    p.add_argument("--tools", nargs="*", default=None, choices=TOOLS)
    args = p.parse_args(argv)

    tools = args.tools or list(TOOLS)
    args.out.mkdir(parents=True, exist_ok=True)
    lines_table = load_lines(args.results)
    objs = sorted(d for d in args.runs.iterdir()
                  if d.is_dir() and d.name.isdigit() and (d / "outputs").is_dir())
    if args.objects:
        objs = [d for d in objs if d.name in set(args.objects)]

    summary = []
    for obj_dir in objs:
        per_tool = {}
        for tool in tools:
            pts = gather(obj_dir, tool, lines_table)
            if not pts:
                continue
            per_tool[tool] = pts
            make_one(obj_dir, tool, pts, args.out)
            for q in pts:
                rel = (np.nanmax([abs(q["elo"]), abs(q["ehi"])]) / abs(q["flux"]) * 100.0
                       if q["flux"] else np.nan)
                summary.append({"tag": obj_dir.name, "tool": tool, "line": q["line"],
                                "component": q["comp"], "flux_1e17": q["flux"],
                                "err_lo_1e17": q["elo"], "err_hi_1e17": q["ehi"],
                                "rel_err_pct": rel, "method": q["method"]})
        if per_tool:
            make_overview(obj_dir, per_tool, args.out)
        print(f"[statconf] {obj_dir.name}: " + ", ".join(f"{t}={len(per_tool.get(t, []))}" for t in tools))

    sp = args.out / "summary.csv"
    with sp.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["tag", "tool", "line", "component", "flux_1e17",
                                           "err_lo_1e17", "err_hi_1e17", "rel_err_pct", "method"])
        w.writeheader(); w.writerows(summary)
    print(f"[statconf] wrote {len(summary)} rows -> {sp}")
    print(f"[statconf] figures under {args.out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
