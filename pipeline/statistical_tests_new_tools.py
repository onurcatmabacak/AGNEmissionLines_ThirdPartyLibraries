#!/usr/bin/env python3
"""Statistical comparison of the new IR/UV/SED tools.

Outputs:
  docs/statistical_tests_new_tools.csv
  docs/statistical_analysis_new_tools.png / .pdf
"""
from __future__ import annotations

import csv
import json
import math
import warnings
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pipeline.io_layout import OUTPUT_ROOT, output_dir  # noqa: E402

OUT = ROOT / "outputs"
DOCS = ROOT / "docs"

FIR_TRUTH = {"OI63": 500.0, "OIII88": 1000.0, "NII122": 300.0, "CII158": 2000.0}


def read_csv(path):
    if not path.exists():
        return []
    with path.open() as fh:
        return list(csv.DictReader(fh))


def fl(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else np.nan
    except Exception:
        return np.nan


def boot_ci(vals, fn=np.median, n=2000, seed=42):
    x = np.asarray([v for v in vals if np.isfinite(v)], float)
    if x.size == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    out = [fn(rng.choice(x, x.size, replace=True)) for _ in range(n)]
    return (float(np.percentile(out, 16)), float(np.percentile(out, 84)))


def test_row(scope, name, values, null=1.0, note=""):
    x = np.asarray([v for v in values if np.isfinite(v)], float)
    if x.size < 2:
        return {"scope": scope, "test": name, "n": int(x.size), "median": "",
                "ci16": "", "ci84": "", "p_wilcoxon": "", "p_ttest": "", "note": note}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pw = stats.wilcoxon(x - null).pvalue if x.size >= 5 else np.nan
        pt = stats.ttest_1samp(x, null, nan_policy="omit").pvalue
    except Exception:
        pw, pt = np.nan, np.nan
    lo, hi = boot_ci(x)
    return {"scope": scope, "test": name, "n": int(x.size),
            "median": f"{np.median(x):.4g}", "ci16": f"{lo:.4g}", "ci84": f"{hi:.4g}",
            "p_wilcoxon": f"{pw:.4g}" if np.isfinite(pw) else "",
            "p_ttest": f"{pt:.4g}" if np.isfinite(pt) else "", "note": note}


def uv_tests():
    rows = read_csv(DOCS / "pyqsofit_zline_comparison.csv")
    tests = []
    line_vals = {}
    for line in ["MgII", "CIII", "CIV", "Hb", "OIII5007"]:
        tot = [fl(r["total/zline"]) for r in rows if r["line"] == line]
        nar = [fl(r["narrow/zline"]) for r in rows if r["line"] == line]
        line_vals[line] = {"total": tot, "narrow": nar}
        tests.append(test_row("PyQSOFit UV", f"{line} total/ZLINE", tot,
                              note="broad+narrow; C III] broad is blend-limited"))
        if line in ("CIII", "MgII"):
            tests.append(test_row("PyQSOFit UV", f"{line} narrow/ZLINE", nar,
                                  note="narrow component"))
    return rows, tests, line_vals


def sed_tests():
    rows = read_csv(DOCS / "sed_family_comparison.csv")
    by = {}
    for r in rows:
        by.setdefault(r["source"], []).append(r)
    pairs = []
    for src, rs in by.items():
        cig = [r for r in rs if r["engine"] == "CIGALE"]
        ag = [r for r in rs if r["engine"] == "AGNfitter-rx"]
        if not cig or not ag:
            continue
        best = min(cig, key=lambda r: fl(r["chi2_red"]) if np.isfinite(fl(r["chi2_red"])) else 1e9)
        pairs.append((src, best, ag[0], cig))
    tests = []
    for key, label in [("logLAGN_Lsun", "log L_AGN"), ("logMstar", "log M*"),
                       ("fracAGN", "AGN fraction")]:
        cv = [fl(p[1][key]) for p in pairs]
        av = [fl(p[2][key]) for p in pairs]
        diff = [a - c for c, a in zip(cv, av)]
        tests.append(test_row("SED families", f"AGNfitter - best CIGALE {label}", diff, null=0.0,
                              note="paired difference; best CIGALE = lower chi2 family"))
        if np.isfinite(cv).sum() >= 3:
            rho, p = stats.spearmanr(cv, av, nan_policy="omit")
            tests.append({"scope": "SED families", "test": f"Spearman {label}",
                          "n": int(np.isfinite(cv).sum()), "median": f"{rho:.4g}",
                          "ci16": "", "ci84": "", "p_wilcoxon": "",
                          "p_ttest": f"{p:.4g}", "note": "CIGALE vs AGNfitter"})
    return pairs, tests


def fir_tests():
    path = output_dir("synthetic_fir_z_0.5000", "fir_linefit") / "spectrum.fir_lines.csv"
    rows = read_csv(path)
    rec = {r["line"]: r for r in rows}
    ratios = []
    for line, truth in FIR_TRUTH.items():
        r = rec.get(line)
        if r:
            ratios.append(fl(r["flux"]) / truth)
    tests = [test_row("FIR synthetic", "recovered/truth", ratios,
                      note="OI63/OIII88/NII122/CII158")]
    return rows, ratios, tests


def cross_tests():
    rows = []
    for p in OUTPUT_ROOT.glob("crossband/*/crossband_ratios.csv"):
        for r in read_csv(p):
            r["_source"] = p.parent.parent.name
            rows.append(r)
    cons = [r for r in rows if str(r.get("consistent", "")).lower() in ("true", "1")]
    p = stats.binomtest(len(cons), len(rows), 0.5).pvalue if rows else np.nan
    tests = [{"scope": "crossband", "test": "consistent ratios",
              "n": len(rows), "median": f"{len(cons)/len(rows):.3f}" if rows else "",
              "ci16": "", "ci84": "", "p_wilcoxon": "",
              "p_ttest": f"{p:.4g}" if np.isfinite(p) else "",
              "note": f"{len(cons)}/{len(rows)} within broad priors"}]
    return rows, tests


def pahfit_tests():
    rows = []
    for p in OUTPUT_ROOT.glob("pahfit_mir/*/**/pahfit_summary.json"):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        rows.append({"source": p.parts[-4], "segment": d.get("segment", "full"),
                     "rms": d.get("rms_rel", np.nan), "unstable": d.get("unstable", None)})
    good = [r for r in rows if r["unstable"] is False]
    tests = [{"scope": "PAHFIT", "test": "stable segments", "n": len(rows),
              "median": f"{len(good)}/{len(rows)}", "ci16": "", "ci84": "",
              "p_wilcoxon": "", "p_ttest": "", "note": "rms_rel<0.5 and status ok"}]
    return rows, tests


def main():
    uv_rows, uv_t, uv_vals = uv_tests()
    pairs, sed_t = sed_tests()
    fir_rows, fir_ratios, fir_t = fir_tests()
    cb_rows, cb_t = cross_tests()
    pf_rows, pf_t = pahfit_tests()
    tests = uv_t + sed_t + fir_t + cb_t + pf_t
    with (DOCS / "statistical_tests_new_tools.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(tests[0]))
        w.writeheader(); w.writerows(tests)

    fig, axes = plt.subplots(2, 3, figsize=(17, 10))
    # 1 UV ratios
    ax = axes[0, 0]
    for line, marker in [("MgII", "o"), ("CIII", "s"), ("CIV", "^"), ("Hb", "D"), ("OIII5007", "v")]:
        tv = [v for v in uv_vals[line]["total"] if np.isfinite(v)]
        if tv:
            ax.scatter([line] * len(tv), tv, marker=marker, s=24, alpha=0.7)
    ax.axhline(1, color="k", lw=0.8)
    ax.set_yscale("log"); ax.set_ylabel("total / SDSS ZLINE")
    ax.set_title("PyQSOFit UV/optical vs ZLINE"); ax.tick_params(axis="x", rotation=30)

    # 2 SED logLAGN comparison
    ax = axes[0, 1]
    cv = [fl(p[1]["logLAGN_Lsun"]) for p in pairs]
    av = [fl(p[2]["logLAGN_Lsun"]) for p in pairs]
    ax.scatter(cv, av, s=45)
    lo = np.nanmin(cv + av); hi = np.nanmax(cv + av)
    ax.plot([lo, hi], [lo, hi], "k--", lw=0.8)
    ax.set_xlabel("CIGALE best log L_AGN/Lsun"); ax.set_ylabel("AGNfitter log L_AGN/Lsun")
    ax.set_title("SED family: L_AGN")

    # 3 AGN fraction
    ax = axes[0, 2]
    for i, p in enumerate(pairs):
        c = fl(p[1]["fracAGN"]); a = fl(p[2]["fracAGN"])
        ax.plot([i, i], [c, a], color="0.6", lw=1)
        ax.scatter([i], [c], color="C0", label="CIGALE best" if i == 0 else None)
        ax.scatter([i], [a], color="C1", label="AGNfitter" if i == 0 else None)
    ax.set_xticks(range(len(pairs))); ax.set_xticklabels([p[0].split("_")[0] for p in pairs], rotation=60, fontsize=7)
    ax.set_ylim(0, 1.05); ax.set_ylabel("AGN fraction"); ax.set_title("SED family: AGN fraction")
    ax.legend(fontsize=7, frameon=False)

    # 4 FIR recovery
    ax = axes[1, 0]
    names = list(FIR_TRUTH)
    byline = {r["line"]: fl(r["flux"]) for r in fir_rows}
    vals = [byline.get(n, np.nan) / FIR_TRUTH[n] for n in names]
    ax.bar(names, vals, color=["C2" if np.isfinite(v) else "0.7" for v in vals])
    ax.axhline(1, color="k", lw=0.8); ax.set_ylabel("recovered / truth")
    ax.set_title("FIR synthetic recovery"); ax.tick_params(axis="x", rotation=30)

    # 5 crossband ratios
    ax = axes[1, 1]
    y = np.arange(len(cb_rows)); rr = [fl(r["value"]) for r in cb_rows]
    lo = [fl(r["expected_low"]) for r in cb_rows]; hi = [fl(r["expected_high"]) for r in cb_rows]
    for i, r in enumerate(cb_rows):
        ax.plot([lo[i], hi[i]], [i, i], color="0.8", lw=5)
        ax.plot(rr[i], i, "o", color="C2" if str(r["consistent"]).lower() == "true" else "C3", ms=6)
    ax.set_yticks(y); ax.set_yticklabels([f"{r['_source'].split('_')[0]} {r['ratio']}" for r in cb_rows], fontsize=7)
    ax.set_xscale("log"); ax.set_xlabel("ratio"); ax.set_title("Cross-band ratios")

    # 6 PAHFIT rms
    ax = axes[1, 2]
    x = np.arange(len(pf_rows)); rms = [fl(r["rms"]) for r in pf_rows]
    colors = ["C2" if r["unstable"] is False else "C3" for r in pf_rows]
    ax.bar(x, rms, color=colors)
    ax.set_xticks(x); ax.set_xticklabels([f"{r['source'].split('_')[0]}\n{r['segment']}" for r in pf_rows], rotation=60, fontsize=6)
    ax.set_ylabel("rms_rel"); ax.set_title("PAHFIT stability")
    fig.suptitle("Statistical comparison of the new IR/UV/SED tools", fontsize=13)
    fig.tight_layout()
    fig.savefig(DOCS / "statistical_analysis_new_tools.png", dpi=150)
    fig.savefig(DOCS / "statistical_analysis_new_tools.pdf")
    print("wrote", DOCS / "statistical_tests_new_tools.csv")
    print(f"UV tests={len(uv_t)} SED={len(sed_t)} FIR={len(fir_t)} cross={len(cb_t)} PAHFIT={len(pf_t)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
