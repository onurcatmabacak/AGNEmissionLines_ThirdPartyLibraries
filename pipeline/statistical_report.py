#!/usr/bin/env python3
"""Reproducible statistics for the line-ratio and cross-mission results.

Inputs are deliberately simple CSV/JSON products, so the report can be
regenerated without running any Docker image:

* ``docs/line_ratio_comparison.csv`` — cross-tool H-beta/[O III] ratios for
  the SDSS QSOs;
* ``outputs/3C120.../pyqsofit_uv`` and ``qsofitmore_line`` — independent
  optical fits of the same HST spectrum;
* ``outputs/PDS.../optical_linefit`` and ``crossmission`` — the local H-beta
  fit and the XMM Fe K-alpha comparison.

The output is a JSON/CSV/Markdown report, not a claim of a correlation.  With
only a few objects, robust summaries and explicit small-N warnings are more
honest than a regression line.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"


def bootstrap_ci(values, n=10000, seed=20250101):
    x = np.asarray([v for v in values if np.isfinite(v)], float)
    if x.size == 0:
        return [None, None]
    rng = np.random.default_rng(seed)
    boot = np.median(rng.choice(x, size=(n, x.size), replace=True), axis=1)
    return [float(np.percentile(boot, 16)), float(np.percentile(boot, 84))]


def robust_stats(values):
    x = np.asarray([v for v in values if np.isfinite(v) and v > 0], float)
    if x.size == 0:
        return None
    med = float(np.median(x))
    mad = float(1.4826 * np.median(np.abs(np.log10(x) - np.median(np.log10(x)))))
    return {
        "n": int(x.size),
        "median": med,
        "mean": float(np.mean(x)),
        "min": float(np.min(x)),
        "max": float(np.max(x)),
        "log10_scatter_mad": mad,
        "log10_scatter_std": float(np.std(np.log10(x))),
        "multiplicative_scatter_mad": float(10 ** mad),
        "multiplicative_scatter_std": float(10 ** float(np.std(np.log10(x)))),
        "bootstrap_median_16_84": bootstrap_ci(x),
    }


def read_line_ratios():
    rows = []
    p = ROOT / "docs" / "line_ratio_comparison.csv"
    if not p.exists():
        return rows
    with p.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("quality", "ok") != "ok":
                continue
            if r["ratio"] != "Hbeta/OIII5007":
                continue
            try:
                v = float(r["value"])
            except ValueError:
                continue
            if math.isfinite(v) and v > 0:
                rows.append({"source": r["source"], "tool": r["tool"], "value": v})
    return rows


def read_hst_ratios():
    """Independent optical fits of the same 3C 120 HST spectrum."""
    out = []
    p = ROOT / "outputs" / "3C120_z_0.0330" / "qsofitmore_line" / "qsofitmore_lines.csv"
    if p.exists():
        with p.open(newline="") as fh:
            rows = {r["line"]: r for r in csv.DictReader(fh)}
        try:
            hb = float(rows["Hbeta"]["area_1e17"])
            o3 = float(rows["OIII5007"]["area_1e17"])
            out.append({"source": "3C120_z_0.0330", "tool": "qsofitmore_line", "value": hb / o3})
        except Exception:
            pass
    p = ROOT / "outputs" / "3C120_z_0.0330" / "pyqsofit_uv" / "pyqsofit_lines.csv"
    if p.exists():
        with p.open(newline="") as fh:
            rows = list(csv.DictReader(fh))
        hb = sum(float(r["area_1e17"]) for r in rows if r["line"].startswith("Hb_"))
        o3 = sum(float(r["area_1e17"]) for r in rows if r["line"].startswith("OIII5007"))
        if o3 > 0:
            out.append({"source": "3C120_z_0.0330", "tool": "pyqsofit_uv", "value": hb / o3})
    return out


def read_pds_hbeta():
    p = ROOT / "outputs" / "PDS456_z_0.1840" / "optical_linefit" / "optical_lines_summary.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    return {"source": "PDS456_z_0.1840", "tool": "optical_linefit",
            "value": d.get("Hbeta_OIII_ratio"), "quality": d.get("quality"),
            "chi2_red": d.get("chi2_red"), "hbeta_flux": d.get("Hbeta_total_1e17"),
            "oiii_flux": d.get("OIII5007_total_1e17")}


def main() -> int:
    line_rows = read_line_ratios()
    by_source = {}
    for r in line_rows:
        by_source.setdefault(r["source"], []).append(r)
    source_stats = {}
    for source, rows in sorted(by_source.items()):
        source_stats[source] = {
            "ratios": rows,
            **robust_stats([r["value"] for r in rows]),
        }
    all_ratios = [r["value"] for r in line_rows]
    # The source with the largest tool set is the only defensible
    # cross-tool headline; pooling different objects would pseudo-replicate.
    canonical_source = max(by_source, key=lambda k: len(by_source[k])) if by_source else None
    global_stats = robust_stats([r["value"] for r in by_source.get(canonical_source, [])]) if canonical_source else None
    tool_bias = {}
    for source, rows in by_source.items():
        med = np.median([r["value"] for r in rows])
        for r in rows:
            tool_bias.setdefault(r["tool"], []).append(math.log10(r["value"] / med))
    tool_bias_summary = {}
    for tool, vals in sorted(tool_bias.items()):
        x = np.asarray(vals, float)
        tool_bias_summary[tool] = {
            "n_sources": int(x.size),
            "median_log10_bias": float(np.median(x)),
            "multiplicative_bias": float(10 ** np.median(x)),
            "log10_scatter_mad": float(1.4826 * np.median(np.abs(x - np.median(x)))),
        }
    hst = read_hst_ratios()
    pds = read_pds_hbeta()
    cross = []
    for source in ("3C120_z_0.0330", "PDS456_z_0.1840"):
        p = ROOT / "outputs" / source / "crossmission" / "xray_optical_comparison.json"
        if p.exists():
            d = json.loads(p.read_text())
            cross.append({
                "source": source,
                "sample_size": 2,
                "optical_tool": d.get("optical_tool"),
                "optical_line": d.get("optical_line"),
                "quality": d.get("quality"),
                "optical_to_xray_flux_ratio": d.get("optical_to_xray_flux_ratio"),
                "optical_luminosity_erg_s": d.get("optical_luminosity_erg_s"),
                "xray_luminosity_erg_s": d.get("xray_luminosity_erg_s"),
            })
    result = {
        "schema_version": "1.0.0",
        "analysis": "cross-tool line-ratio and same-object X-ray/optical case study",
        "line_ratio": "Hbeta/OIII5007",
        "canonical_source": canonical_source,
        "canonical_source_stats": global_stats,
        "global": None,
        "per_source": source_stats,
        "tool_bias_relative_to_source_median": tool_bias_summary,
        "hst_3c120_independent": hst,
        "pds456_local_hbeta": pds,
        "crossmission": cross,
        "warnings": [
            "The cross-tool sample is small; per-source medians are descriptive, not a population distribution.",
            "QSOFITMORE and PyQSOFit are not independent codes: both are PyQSOFit-derived, but their models/priors differ.",
            "PDS 456 H-beta is a local fit to X-SHOOTER with a provisional quality flag; it is not a publication-grade line ratio.",
            "crossmission has N=2 and no correlation/slope is fitted.",
        ],
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "statistical_results.json").write_text(json.dumps(result, indent=2) + "\n")
    with (OUT / "statistical_results.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["source", "tool", "Hbeta_OIII5007", "dataset"])
        for r in line_rows:
            w.writerow([r["source"], r["tool"], r["value"], "SDSS_multi_tool"])
        for r in hst:
            w.writerow([r["source"], r["tool"], r["value"], "HST_3C120_independent"])
        if pds:
            w.writerow([pds["source"], pds["tool"], pds["value"], "XSHOOTER_PDS456_local"])
    lines = [
        "# Science results and statistics",
        "",
        "Generated by `pipeline/statistical_report.py` from committed products.",
        "This is a **descriptive** report, not a population regression.",
        "",
        "## Cross-tool Hβ/[O III] 5007",
        "",
        f"Canonical cross-tool group: `{canonical_source}` with **{global_stats['n']}** tools, "
        f"median **{global_stats['median']:.3f}**, log10 scatter "
        f"**{global_stats['log10_scatter_std']:.3f} dex** "
        f"(multiplicative {global_stats['multiplicative_scatter_std']:.2f}×)." if global_stats else "No ratios found.",
        "", "No population median is computed across different objects.", "",
        "| source | n tools | median | min | max | 16–84% bootstrap |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for source, s in sorted(source_stats.items()):
        if not s:
            continue
        lo, hi = s["bootstrap_median_16_84"]
        lines.append(f"| `{source}` | {s['n']} | {s['median']:.3f} | {s['min']:.3f} | "
                     f"{s['max']:.3f} | {lo:.3f}–{hi:.3f} |")
    if tool_bias_summary:
        lines += ["", "## Per-tool bias relative to the source median", "",
                  "| tool | n sources | multiplicative bias | log10 scatter |",
                  "|---|---:|---:|---:|"]
        for tool, b in sorted(tool_bias_summary.items(), key=lambda kv: abs(kv[1]["median_log10_bias"]), reverse=True):
            lines.append(f"| `{tool}` | {b['n_sources']} | {b['multiplicative_bias']:.3f}× | {b['log10_scatter_mad']:.3f} |")
        lines += ["", "A value of 1.00 means the tool sits at the per-source median; "
                  "this is a descriptive bias, not a calibration.", ""]
    lines += ["", "## Independent optical fits of 3C 120", "",
              "| tool | Hβ/[O III] |", "|---|---:|"]
    for r in hst:
        lines.append(f"| `{r['tool']}` | {r['value']:.3f} |")
    lines += ["", "The two optical models disagree; this is a model-systematic "
              "spread, not a measurement error.  Do not call one of them "
              "\"the truth\" without an external line-flux calibration.", ""]
    if pds:
        lines += ["## PDS 456 local Hβ/[O III]", "",
                  f"- tool: `{pds['tool']}`",
                  f"- ratio: **{pds['value']:.3f}**",
                  f"- quality: **{pds['quality']}**",
                  f"- χ²_red: **{pds['chi2_red']:.1f}**",
                  "", "The X-SHOOTER spectrum gives Hβ coverage but the local "
                  "fit has absorption/continuum residuals; the ratio is "
                  "provisional and should not be used as a publication value "
                  "without a better absorption mask.", ""]
    lines += ["## Same-object X-ray/optical", "",
              "The tabulated quantity is a **line-to-line flux ratio**.  It is "
              "descriptive; it is not alpha_ox or a physical SED normalization.",
              "",
              "| source | optical tool | line | quality | optical line / X-ray line flux |",
              "|---|---|---|---|---:|"]
    for r in cross:
        lines.append(f"| `{r['source']}` | `{r['optical_tool']}` | {r['optical_line']} | "
                     f"**{r['quality']}** | {r['optical_to_xray_flux_ratio']:.3f} |")
    lines += ["", "**N=2. No correlation or slope is fitted.**  This is a "
              "two-object consistency case study, not evidence for a "
              "population relation.", ""]
    (OUT / "SCIENCE_RESULTS.md").write_text("\n".join(lines))
    print(f"wrote docs/SCIENCE_RESULTS.md, statistical_results.json/csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
