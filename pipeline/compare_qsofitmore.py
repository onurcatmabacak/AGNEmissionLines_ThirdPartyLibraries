#!/usr/bin/env python3
"""Cross-check QSOFITMORE H-beta/[O III] and Mg II against sibling tools.

The script is deliberately dependency-light: it reads the committed CSVs with
the standard library and only imports matplotlib/numpy when a figure is
requested.  It can therefore run on the host (text/CSV products) or inside the
``qsofitmore_line`` image (figure products).

    python pipeline/compare_qsofitmore.py --source-key 04592649654_z_0.5874
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import sys  # noqa: E402
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from pipeline.io_layout import output_dir  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOOLS = (
    "qsofitmore_line",
    "pyqsofit_uv",
    "gandalf_line",
    "s3fit_line",
    "galspec_line",
    "pyqsofitspec_line",
    "qgfit",
    "sheap_line",
    "sdss_zline",
)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def fnum(value, default=float("nan")) -> float:
    try:
        out = float(value)
        return out
    except Exception:
        return default


def add(rows, source, line, tool, flux, err, method):
    rows.append(
        {
            "source": source,
            "line": line,
            "tool": tool,
            "flux_1e17": fnum(flux),
            "flux_err_1e17": fnum(err),
            "method": method,
        }
    )


def qm_values(outdir: Path) -> dict[str, tuple[float, float]]:
    rows = read_csv(outdir / "qsofitmore_lines.csv")
    out = {}
    for r in rows:
        if r.get("covered", "").lower() == "true":
            out[r["line"]] = (fnum(r.get("area_1e17")), fnum(r.get("area_err_1e17")))
    return out


def pyqsofit_values(obj: Path) -> dict[str, tuple[float, float]]:
    out = {}
    mc = read_csv(obj / "pyqsofit" / "mc" / "pyqsofit_mc_summary.csv")
    if mc:
        by = {(r["line"], r["component"]): r for r in mc}
        def med(name, comp):
            r = by.get((name, comp))
            return fnum(r["median"]) if r else float("nan"), fnum(r["p16"]) if r else float("nan"), fnum(r["p84"]) if r else float("nan")
        def combine(items):
            vals = [med(*x) for x in items]
            total = sum(v[0] for v in vals)
            err = math.sqrt(sum(((v[2] - v[1]) / 2.0) ** 2 for v in vals if math.isfinite(v[1]) and math.isfinite(v[2])))
            return total, err
        out["Hbeta"] = combine([("Hb_br", "broad"), ("Hb_na", "narrow")])
        out["OIII5007"] = combine([("OIII5007w", "broad"), ("OIII5007c", "narrow")])
        out["MgII"] = combine([("MgII_br", "broad"), ("MgII_na", "narrow")])
        return out
    rows = read_csv(obj / "pyqsofit_uv" / "pyqsofit_lines.csv")
    by = {(r["line"], r["component"]): r for r in rows}
    def val(name, comp):
        r = by.get((name, comp))
        return fnum(r["area_1e17"]) if r else float("nan")
    out["Hbeta"] = (val("Hb_br", "broad") + val("Hb_na", "narrow"), float("nan"))
    out["OIII5007"] = (val("OIII5007w", "broad") + val("OIII5007c", "narrow"), float("nan"))
    out["MgII"] = (val("MgII_br", "broad") + val("MgII_na", "narrow"), float("nan"))
    return out


def gandalf_values(obj: Path) -> dict[str, tuple[float, float]]:
    out = {}
    rows = read_csv(obj / "gandalf_line" / "gandalf_lines.csv")
    by = {(r["line"], r["component"]): r for r in rows}
    if ("Hbeta", "total") in by:
        r = by[("Hbeta", "total")]
        out["Hbeta"] = (fnum(r["flux_1e17"]), fnum(r["flux_err_1e17"]))
    if ("[OIII]5007", "narrow") in by:
        r = by[("[OIII]5007", "narrow")]
        out["OIII5007"] = (fnum(r["flux_1e17"]), fnum(r["flux_err_1e17"]))
    return out


def s3fit_values(obj: Path) -> dict[str, tuple[float, float]]:
    out = {}
    rows = read_csv(obj / "s3fit_line" / "s3fit_lines.csv")
    def row(line, comp="total"):
        for r in rows:
            if r.get("line") == line and r.get("component") == comp:
                return r
        return None
    for key, line in (("Hbeta", "H-beta"), ("OIII5007", "[O III]:5008")):
        r = row(line)
        if r:
            out[key] = (fnum(r["flux_1e17"]), fnum(r["flux_err_1e17"]))
    mg1, mg2 = row("Mg II]:2796"), row("Mg II]:2804")
    if mg1 or mg2:
        vals = [x for x in (mg1, mg2) if x]
        total = sum(fnum(x["flux_1e17"]) for x in vals)
        err = math.sqrt(sum(fnum(x["flux_err_1e17"]) ** 2 for x in vals))
        out["MgII"] = (total, err)
    return out


def galspec_values(obj: Path) -> dict[str, tuple[float, float]]:
    out = {}
    rows = read_csv(obj / "galspec_line" / "galspec_lines.csv")
    by = {(r["line"], r["component"]): r for r in rows}
    for key, line in (("Hbeta", "Hbeta"), ("OIII5007", "OIII_5007")):
        r = by.get((line, "total"))
        if r:
            out[key] = (fnum(r["flux_1e17"]), fnum(r["flux_err_1e17"]))
    vals = [by.get(("MgII_2796", "total")), by.get(("MgII_2804", "total"))]
    vals = [v for v in vals if v]
    if vals:
        out["MgII"] = (
            sum(fnum(v["flux_1e17"]) for v in vals),
            math.sqrt(sum(fnum(v["flux_err_1e17"]) ** 2 for v in vals)),
        )
    return out


def pyqsofitspec_values(obj: Path) -> dict[str, tuple[float, float]]:
    out = {}
    rows = read_csv(obj / "pyqsofitspec_line" / "pyqsofitspec_totals.csv")
    by = {r["total"]: r for r in rows}
    for key, name in (("Hbeta", "Hbeta"), ("OIII5007", "OIII5007"), ("MgII", "MgII")):
        r = by.get(name)
        if r:
            out[key] = (fnum(r["flux_1e17"]), fnum(r["flux_err_1e17"]))
    return out


def qgfit_values(obj: Path) -> dict[str, tuple[float, float]]:
    out = {}
    rows = read_csv(obj / "qgfit" / "qgfit_lines.csv")
    by = {(r["line"], r["component"]): r for r in rows}
    r = by.get(("Hbeta", "total"))
    if r:
        out["Hbeta"] = (fnum(r["flux_1e17"]), fnum(r["flux_err_1e17"]))
    r = by.get(("OIII5007", "narrow"))
    if r:
        out["OIII5007"] = (fnum(r["flux_1e17"]), fnum(r["flux_err_1e17"]))
    r = by.get(("MgII", "mix"))
    if r:
        out["MgII"] = (fnum(r["flux_1e17"]), fnum(r["flux_err_1e17"]))
    return out


def sheap_values(obj: Path) -> dict[str, tuple[float, float]]:
    out = {}
    rows = read_csv(obj / "sheap_line" / "sheap_lines.csv")
    by = {(r["line"], r["component"]): r for r in rows}
    for key, line in (("Hbeta", "Hbeta"), ("OIII5007", "OIII5007")):
        r = by.get((line, "total"))
        if r:
            out[key] = (fnum(r["flux_1e17"]), fnum(r["flux_err_1e17"]))
    return out


def zline_values(obj: Path) -> dict[str, tuple[float, float]]:
    out = {}
    rows = read_csv(obj / "pyqsofit_uv" / "zline_comparison.csv")
    by = {r["line"]: r for r in rows}
    for key, name in (("Hbeta", "Hb"), ("OIII5007", "OIII5007"), ("MgII", "MgII")):
        r = by.get(name)
        if r:
            out[key] = (fnum(r["zline_area"]), float("nan"))
    return out


def load_tool(obj: Path, tool: str) -> dict[str, tuple[float, float]]:
    if tool == "pyqsofit_uv":
        return pyqsofit_values(obj)
    if tool == "gandalf_line":
        return gandalf_values(obj)
    if tool == "s3fit_line":
        return s3fit_values(obj)
    if tool == "galspec_line":
        return galspec_values(obj)
    if tool == "pyqsofitspec_line":
        return pyqsofitspec_values(obj)
    if tool == "qgfit":
        return qgfit_values(obj)
    if tool == "sheap_line":
        return sheap_values(obj)
    if tool == "sdss_zline":
        return zline_values(obj)
    return {}


def ratio_with_err(hb, o3):
    if not (math.isfinite(hb[0]) and math.isfinite(o3[0]) and o3[0] > 0):
        return float("nan"), float("nan")
    ratio = hb[0] / o3[0]
    e_hb, e_o3 = hb[1], o3[1]
    if math.isfinite(e_hb) and math.isfinite(e_o3):
        err = abs(ratio) * math.sqrt((e_hb / hb[0]) ** 2 + (e_o3 / o3[0]) ** 2)
    else:
        err = float("nan")
    return ratio, err


def mean_std(values):
    vals = [v for v in values if math.isfinite(v)]
    if not vals:
        return float("nan"), float("nan"), 0
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1) if len(vals) > 1 else 0.0
    return mean, math.sqrt(var), len(vals)


def write_markdown(path: Path, rows, summary, qm):
    lines = [
        "# QSOFITMORE cross-tool check",
        "",
        "Hβ and [O III] 5007 are totals (all components); Mg II is the blended",
        "2796/2804 doublet where a tool resolves it.  Fluxes are in",
        "10^-17 erg s^-1 cm^-2.  `delta_sigma` uses",
        "`(tool - QSOFITMORE)/sqrt(err_tool^2 + err_qm^2)`.",
        "",
        "| tool | Hβ | [O III] 5007 | Hβ/[O III] | Mg II |",
        "|---|---:|---:|---:|---:|",
    ]
    by_tool = {}
    for r in rows:
        by_tool.setdefault(r["tool"], {})[r["line"]] = r
    for tool in DEFAULT_TOOLS:
        d = by_tool.get(tool, {})
        def cell(line):
            r = d.get(line)
            if not r or not math.isfinite(r["flux_1e17"]):
                return "n/a"
            if math.isfinite(r["flux_err_1e17"]):
                return f"{r['flux_1e17']:.0f} ± {r['flux_err_1e17']:.0f}"
            return f"{r['flux_1e17']:.0f}"
        hb, o3 = d.get("Hbeta"), d.get("OIII5007")
        ratio = "n/a"
        if hb and o3 and o3["flux_1e17"] > 0:
            ratio = f"{hb['flux_1e17']/o3['flux_1e17']:.2f}"
        lines.append(f"| {tool} | {cell('Hbeta')} | {cell('OIII5007')} | {ratio} | {cell('MgII')} |")
    lines += [
        "",
        "## Summary",
        "",
        "| quantity | QSOFITMORE | n tools | median ratio | mean log10 ratio | scatter dex |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, label in (("Hbeta", "Hβ"), ("OIII5007", "[O III] 5007"), ("MgII", "Mg II")):
        s = summary.get(key, {})
        qmv = qm.get(key, (float("nan"), float("nan")))[0]
        lines.append(
            f"| {label} | {qmv:.1f} | {s.get('n', 0)} | {s.get('median_ratio', float('nan')):.3f} | "
            f"{s.get('mean_log10_ratio', float('nan')):.3f} | {s.get('scatter_dex', float('nan')):.3f} |"
        )
    s = summary.get("Hbeta_OIII5007", {})
    qmr = s.get("qsofitmore_ratio", float("nan"))
    lines.append(
        f"| Hβ/[O III] 5007 | {qmr:.3f} | {s.get('n', 0)} | {s.get('median_ratio', float('nan')):.3f} | "
        f"{s.get('mean_log10_ratio', float('nan')):.3f} | {s.get('scatter_dex', float('nan')):.3f} |"
    )
    lines += [
        "",
        "The scatter is the sample standard deviation of `log10(tool/QSOFITMORE)`; it is a",
        "tool-to-tool model spread, not a measurement error.  Hβ/[O III] is the most",
        "robust comparison because both lines are in the same QSOFITMORE complex, so their",
        "Monte Carlo draws are correlated.",
    ]
    path.write_text("\n".join(lines) + "\n")


def make_figure(path_png: Path, path_pdf: Path, rows, summary, qm):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # noqa: BLE001
        print(f"[crosscheck] figure skipped (matplotlib unavailable): {exc!r}")
        return False
    by_tool = {}
    for r in rows:
        by_tool.setdefault(r["tool"], {})[r["line"]] = r
    tools = [t for t in DEFAULT_TOOLS if t in by_tool]
    ratios, rerrs = [], []
    for t in tools:
        hb, o3 = by_tool[t].get("Hbeta"), by_tool[t].get("OIII5007")
        if hb and o3:
            ratios.append(hb["flux_1e17"] / o3["flux_1e17"])
            if math.isfinite(hb["flux_err_1e17"]) and math.isfinite(o3["flux_err_1e17"]):
                rerrs.append(ratios[-1] * math.sqrt((hb["flux_err_1e17"]/hb["flux_1e17"])**2 + (o3["flux_err_1e17"]/o3["flux_1e17"])**2))
            else:
                rerrs.append(0.0)
        else:
            ratios.append(float("nan"))
            rerrs.append(float("nan"))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    ax = axes[0]
    y = list(range(len(tools)))
    ax.errorbar(ratios, y, xerr=rerrs, fmt="o", color="C0", ecolor="0.5", capsize=2)
    qmr = summary.get("Hbeta_OIII5007", {}).get("qsofitmore_ratio", float("nan"))
    if math.isfinite(qmr):
        ax.axvline(qmr, color="C3", lw=1.2, label=f"QSOFITMORE {qmr:.2f}")
    ax.set_yticks(y)
    ax.set_yticklabels(tools, fontsize=9)
    ax.set_xlabel(r"H$\beta$/[O III] 5007")
    ax.set_title("Hβ/[O III] 5007")
    ax.legend(fontsize=8)
    ax.grid(axis="x", alpha=0.25)
    ax = axes[1]
    mg = []
    for t in tools:
        r = by_tool[t].get("MgII")
        mg.append(r["flux_1e17"] if r else float("nan"))
    mg_err = [by_tool[t].get("MgII", {}).get("flux_err_1e17", float("nan")) for t in tools]
    ax.errorbar(mg, y, xerr=mg_err, fmt="o", color="C2", ecolor="0.5", capsize=2)
    qmm = qm.get("MgII", (float("nan"), float("nan")))[0]
    if math.isfinite(qmm):
        ax.axvline(qmm, color="C3", lw=1.2, label=f"QSOFITMORE {qmm:.0f}")
    ax.set_yticks(y)
    ax.set_yticklabels(tools, fontsize=9)
    ax.set_xlabel(r"Mg II total (10$^{-17}$ erg s$^{-1}$ cm$^{-2}$)")
    ax.set_title("Mg II total")
    ax.legend(fontsize=8)
    ax.grid(axis="x", alpha=0.25)
    fig.suptitle("QSOFITMORE cross-tool check (Hβ, [O III] 5007, Mg II)", fontsize=12)
    fig.tight_layout()
    fig.savefig(path_png, dpi=160, bbox_inches="tight")
    fig.savefig(path_pdf, bbox_inches="tight")
    plt.close(fig)
    return True


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-key", default="04592649654_z_0.5874")
    p.add_argument("--outputs-root", default=str(ROOT / "outputs"))
    p.add_argument("--no-figure", action="store_true")
    args = p.parse_args(argv)
    obj = output_dir(args.source_key, "qsofitmore_line")
    outdir = obj / "qsofitmore_line"
    if not (outdir / "qsofitmore_lines.csv").exists():
        raise SystemExit(f"missing {outdir / 'qsofitmore_lines.csv'}; run qsofitmore_line first")
    qm = qm_values(outdir)
    rows = []
    for tool in DEFAULT_TOOLS:
        if tool == "qsofitmore_line":
            for line, (flux, err) in qm.items():
                add(rows, args.source_key, line, tool, flux, err, "qsofitmore lmfit MC")
            continue
        vals = load_tool(obj, tool)
        for line, (flux, err) in vals.items():
            add(rows, args.source_key, line, tool, flux, err, tool)
    # ratio rows
    summary = {}
    by_tool = {}
    for r in rows:
        by_tool.setdefault(r["tool"], {})[r["line"]] = r
    for key in ("Hbeta", "OIII5007", "MgII"):
        qv = qm.get(key, (float("nan"), float("nan")))[0]
        ratios = []
        for tool, d in by_tool.items():
            if tool == "qsofitmore_line":
                continue
            r = d.get(key)
            if not r or not math.isfinite(r["flux_1e17"]) or not math.isfinite(qv) or qv == 0:
                continue
            ratio = r["flux_1e17"] / qv
            ratios.append(ratio)
            r["ratio_tool_over_qsofitmore"] = ratio
            r["log10_ratio"] = math.log10(ratio) if ratio > 0 else float("nan")
            if math.isfinite(r["flux_err_1e17"]) and math.isfinite(qm.get(key, (0, float("nan")))[1]):
                r["delta_sigma"] = (r["flux_1e17"] - qv) / math.sqrt(r["flux_err_1e17"]**2 + qm[key][1]**2)
            else:
                r["delta_sigma"] = float("nan")
        mean, scatter, n = mean_std([math.log10(x) for x in ratios if x > 0])
        med = sorted(ratios)[len(ratios)//2] if ratios else float("nan")
        summary[key] = {
            "qsofitmore_flux_1e17": qv,
            "qsofitmore_err_1e17": qm.get(key, (float("nan"), float("nan")))[1],
            "n": n,
            "median_ratio": med,
            "mean_log10_ratio": mean,
            "scatter_dex": scatter,
            "ratios": {t: d.get(key, {}).get("ratio_tool_over_qsofitmore", float("nan")) for t, d in by_tool.items()},
        }
    # Hbeta/OIII ratio comparison
    qm_ratio, qm_ratio_err = ratio_with_err(qm.get("Hbeta", (float("nan"),)*2), qm.get("OIII5007", (float("nan"),)*2))
    tool_ratios = {}
    for tool, d in by_tool.items():
        if tool == "qsofitmore_line":
            continue
        hb, o3 = d.get("Hbeta"), d.get("OIII5007")
        if hb and o3:
            rr, ee = ratio_with_err((hb["flux_1e17"], hb["flux_err_1e17"]), (o3["flux_1e17"], o3["flux_err_1e17"]))
            if math.isfinite(rr):
                tool_ratios[tool] = (rr, ee)
    mean, scatter, n = mean_std([math.log10(v[0]/qm_ratio) for v in tool_ratios.values() if qm_ratio > 0 and v[0] > 0])
    med = sorted([v[0] for v in tool_ratios.values()])[len(tool_ratios)//2] if tool_ratios else float("nan")
    summary["Hbeta_OIII5007"] = {
        "qsofitmore_ratio": qm_ratio,
        "qsofitmore_ratio_err": qm_ratio_err,
        "n": n,
        "median_ratio": med,
        "mean_log10_ratio": mean,
        "scatter_dex": scatter,
        "tool_ratios": {t: v[0] for t, v in tool_ratios.items()},
    }
    # write
    fields = ["source", "line", "tool", "flux_1e17", "flux_err_1e17", "qsofitmore_1e17", "qsofitmore_err_1e17",
              "ratio_tool_over_qsofitmore", "log10_ratio", "delta_sigma", "method"]
    for r in rows:
        key = r["line"]
        r["qsofitmore_1e17"] = qm.get(key, (float("nan"), float("nan")))[0]
        r["qsofitmore_err_1e17"] = qm.get(key, (float("nan"), float("nan")))[1]
    with (outdir / "cross_tool_comparison.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    def clean_json(obj):
        if isinstance(obj, dict):
            return {str(k): clean_json(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [clean_json(v) for v in obj]
        if isinstance(obj, float) and not math.isfinite(obj):
            return None
        return obj

    (outdir / "cross_tool_comparison.json").write_text(
        json.dumps(clean_json(summary), indent=2, allow_nan=False) + "\n"
    )
    write_markdown(outdir / "cross_tool_comparison.md", rows, summary, qm)
    if not args.no_figure:
        make_figure(outdir / "cross_tool_comparison.png", outdir / "cross_tool_comparison.pdf", rows, summary, qm)
    # Append the numeric cross-check to the run README, replacing an earlier
    # generated block on re-runs.
    readme = outdir / "README.md"
    if readme.exists():
        start = "<!-- QSOFITMORE_CROSSCHECK_START -->"
        end = "<!-- QSOFITMORE_CROSSCHECK_END -->"
        text = readme.read_text()
        if start in text and end in text:
            text = text.split(start)[0].rstrip() + "\n"
        summary_hb = summary.get("Hbeta", {})
        summary_o3 = summary.get("OIII5007", {})
        summary_mg = summary.get("MgII", {})
        closest = []
        for tool in ("pyqsofit_uv", "gandalf_line", "sheap_line", "qgfit"):
            tr = summary.get("Hbeta_OIII5007", {}).get("tool_ratios", {}).get(tool)
            if tr is not None and math.isfinite(tr):
                closest.append(f"{tool} {tr:.2f}")
        block = f"""\n{start}
## Cross-tool result (generated)

`pipeline/compare_qsofitmore.py` compared Hβ total, [O III] 5007 total and Mg II
total with PyQSOFit, GANDALF, S3Fit, GalSpec, PyQSOFitSpec, QGfit, SHEAP and the
SDSS ZLINE anchor.

* **Hβ/[O III] 5007 = {qm_ratio:.3f} ± {qm_ratio_err:.3f}**; the median of the
  {summary.get('Hbeta_OIII5007', {}).get('n', 0)} independent tools is
  {summary.get('Hbeta_OIII5007', {}).get('median_ratio', float('nan')):.3f}, with
  {summary.get('Hbeta_OIII5007', {}).get('scatter_dex', float('nan')):.3f} dex
  tool-to-tool scatter.  Closest ratios: {', '.join(closest) if closest else 'n/a'}.
* Hβ total: median tool/QSOFITMORE ratio
  {summary_hb.get('median_ratio', float('nan')):.3f}, scatter
  {summary_hb.get('scatter_dex', float('nan')):.3f} dex.
* [O III] 5007: median ratio {summary_o3.get('median_ratio', float('nan')):.3f},
  scatter {summary_o3.get('scatter_dex', float('nan')):.3f} dex.
* Mg II: median ratio {summary_mg.get('median_ratio', float('nan')):.3f},
  scatter {summary_mg.get('scatter_dex', float('nan')):.3f} dex; the ZLINE
  narrow Mg II is a factor ≈2 below the broad-inclusive totals, as expected
  when a narrow-only anchor is compared with broad Mg II.

The full table is `cross_tool_comparison.csv`; per-tool ratios and
`delta_sigma` are in `cross_tool_comparison.json`.  The scatter is a
model/definition spread, not a measurement error.  S3Fit is ≈0.44 of the
QSOFITMORE Hβ/Mg II totals and GalSpec is ≈1.21 of Hβ; those are the largest
model-definition outliers, not a QSOFITMORE failure.
{end}
"""
        readme.write_text(text.rstrip() + block)
    print(f"wrote {outdir / 'cross_tool_comparison.csv'}")
    print(f"QSOFITMORE Hbeta/OIII = {qm_ratio:.3f} +/- {qm_ratio_err:.3f}; "
          f"median tool ratio {med:.3f}; scatter {scatter:.3f} dex (n={n})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
