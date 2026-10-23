#!/usr/bin/env python3
"""Compare line fluxes/ratios and kinematics across the line-fitting tools.

Reads the compact tables produced by PyQSOFit, the generic IR fitter, S3Fit,
CAFE, GANDALF and PAHFIT.  The comparison deliberately uses line ratios and
FWHM as well as absolute fluxes: ratios are insensitive to overall flux
calibration and expose disagreement in the decomposition itself.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


def canon(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "", str(name).lower())
    aliases = {
        "hb": "hbeta", "hbeta": "hbeta", "hbeta4861": "hbeta", "hbbr": "hbeta", "hbna": "hbeta",
        "hbeta": "hbeta", "hβ": "hbeta", "h-beta": "hbeta", "hbeta": "hbeta",
        "ha": "halpha", "halpha": "halpha", "halpha6563": "halpha", "habr": "halpha", "hana": "halpha",
        "h-alpha": "halpha", "hα": "halpha",
        "oiii5007": "oiii5007", "oiii5007c": "oiii5007", "oiii5007w": "oiii5007",
        "oiii5008": "oiii5007", "oiii4960": "oiii4959", "oiii5007": "oiii5007",
        "oiii4959": "oiii4959", "nii6585": "nii6585", "nii6548": "nii6548",
        "neiii15555": "neiii", "neiii": "neiii", "neii12814": "neii", "neii": "neii",
        "siii18713": "siii187", "siii187": "siii187", "siii33480": "siii335", "siii335": "siii335",
        "paalpha": "paalpha", "paalpha18756": "paalpha", "pabeta": "pabeta", "pabeta12822": "pabeta",
        "brgamma": "brgamma", "brgamma21661": "brgamma", "bralpha": "bralpha",
        "siv10511": "siv", "siv": "siv", "oi63184": "oi63", "oi63": "oi63",
        "ciii1908": "ciii", "mgii2798": "mgii",
        "nev143217": "nev", "nevi3426": "nevi", "neii128136": "neii",
        "neiii155551": "neiii", "siii187130": "siii187", "siii334810": "siii335",
        "arii6985": "arii", "ariii89914": "ariii", "siv10511": "siv",
        "h2s1": "h2", "h2s2": "h2", "h2s3": "h2", "h2s4": "h2", "h2s5": "h2", "h2s6": "h2",
    }
    # CAFE appends B/N to a line name; strip that suffix for comparison.
    if len(s) > 2 and s[-1] in ("b", "n") and s[-2].isdigit():
        s = s[:-1]
    # component suffixes used by PyQSOFit/S3Fit line tables
    for base in ("hbeta", "halpha", "oiii5007", "mgii", "ciii", "civ", "lyalpha"):
        for suf in ("br", "na", "broad", "narrow"):
            aliases[base + suf] = aliases.get(base + suf, base)
    return aliases.get(s, s)


def _f(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def add(rows, source, tool, line, comp, flux, err, fwhm, snr=None):
    line = canon(line)
    if not line:
        return
    comp = str(comp or "").lower()
    if comp in ("blr", "broad") or "broad" in comp:
        comp = "broad"
    elif comp in ("nlr", "narrow") or "narrow" in comp:
        comp = "narrow"
    else:
        comp = "total"
    rows.append(dict(source=source, tool=tool, line=line, component=comp,
                     flux=flux, flux_err=err, fwhm_kms=fwhm, snr=snr))


def read_pyqsofit(path: Path, source: str, rows):
    mc = {}
    for base in (path.parent / "mc", path.parent.parent / "pyqsofit" / "mc"):
        f = base / "pyqsofit_mc_summary.csv"
        if f.exists():
            with f.open() as fh:
                for r in csv.DictReader(fh):
                    k = (canon(r["line"]), "broad" if "broad" in r["component"].lower() else "narrow")
                    try:
                        mc[k] = (float(r["median"]), (float(r["p84"]) - float(r["p16"])) / 2.0)
                    except Exception:
                        pass
            break
    with path.open() as fh:
        for r in csv.DictReader(fh):
            comp = "broad" if "broad" in str(r.get("component", "")).lower() else "narrow"
            median, err = mc.get((canon(r.get("line")), comp), (None, None))
            add(rows, source, "pyqsofit_uv", r.get("line"), r.get("component"),
                median if median is not None else _f(r.get("area_1e17")),
                err if err is not None else _f(r.get("flux_err")),
                _f(r.get("fwhm_kms")), _f(r.get("snr")))


def read_ir(path: Path, source: str, rows):
    with path.open() as fh:
        for r in csv.DictReader(fh):
            if str(r.get("status", "ok")).lower() not in ("ok", "detected", "1", "true"):
                continue
            if _f(r.get("detected")) == 0:
                continue
            add(rows, source, "ir_linefit", r.get("line"), r.get("component", "narrow"),
                _f(r.get("flux_1e17")), _f(r.get("flux_err")),
                _f(r.get("fwhm_kms")), _f(r.get("snr")))


def read_standard(path: Path, source: str, tool: str, rows):
    """S3Fit/CAFE/GANDALF compact tables: line,component,flux[,err],fwhm_kms."""
    with path.open() as fh:
        for r in csv.DictReader(fh):
            def pick(*keys):
                for key in keys:
                    if key in r and r[key] not in ("", "nan", "None"):
                        return _f(r[key])
                return None

            flux = pick("flux", "flux_1e17", "flux_int_erg_s_cm2", "flux_observed")
            err = pick("flux_err", "flux_err_1e17", "flux_int_err_w_m2", "flux_int_err_erg_s_cm2", "flux_error")
            fwhm = pick("fwhm_kms", "fwhm", "sigma_kms")
            add(rows, source, tool, r.get("line") or r.get("name"),
                r.get("component") or r.get("comp") or "total",
                flux, err, fwhm, pick("snr", "snr_int"))


def load():
    rows = []
    for src in sorted(OUT.glob("*_z_*")):
        if not src.is_dir():
            continue
        source = src.name
        p = src / "pyqsofit_uv" / "pyqsofit_lines.csv"
        if p.exists():
            read_pyqsofit(p, source, rows)
        for p in (src / "ir_linefit").glob("*.measurements.csv"):
            read_ir(p, source, rows)
        for tool, names in {
            "s3fit_line": ("s3fit_lines.csv", "s3fit_line.csv"),
            "cafe_line": ("cafe_lines.csv", "cafe_line.csv"),
            "gandalf_line": ("gandalf_lines.csv", "gandalf_line.csv"),
            "galspec_line": ("galspec_lines.csv",),
            "pyqsofitspec_line": ("pyqsofitspec_lines.csv",),
            "qgfit": ("qgfit_lines.csv",),
            "sheap_line": ("sheap_lines.csv",),
            "pahfit_mir": ("pahfit_lines.csv",),
        }.items():
            for n in names:
                p = src / tool / n
                if p.exists():
                    try:
                        read_standard(p, source, tool, rows)
                    except Exception:
                        pass
    return rows


def ratios(rows):
    """Per-source/tool line ratios, summing broad+narrow when appropriate."""
    idx = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["flux"] is not None and r["flux"] > 0:
            idx[(r["source"], r["tool"])][r["line"]].append(r)
    out = []
    specs = [
        ("Hbeta/OIII5007", "hbeta", "oiii5007"),
        ("Halpha/NII6585", "halpha", "nii6585"),
        ("NeIII/NeII", "neiii", "neii"),
        ("SIII18.7/SIII33.5", "siii187", "siii335"),
        ("Paalpha/Brgamma", "paalpha", "brgamma"),
        ("OIII5007/Hbeta", "oiii5007", "hbeta"),
    ]
    for (source, tool), d in idx.items():
        for label, a, b in specs:
            if a not in d or b not in d:
                continue
            def total_flux(line):
                recs = [x for x in d[line] if x["flux"] is not None and x["flux"] > 0]
                if not recs:
                    return None
                tot = [x for x in recs if x["component"] == "total"]
                use = tot[:1] if tot else [x for x in recs if x["component"] in ("broad", "narrow")]
                if not use:
                    use = recs[:1]
                f = sum(x["flux"] for x in use)
                e = math.sqrt(sum((x["flux_err"] or 0) ** 2 for x in use))
                return f, e

            ta, tb = total_flux(a), total_flux(b)
            if ta is None or tb is None or tb[0] <= 0:
                continue
            fa, ea = ta
            fb, eb = tb
            val = fa / fb
            if not (0.02 <= val <= 50.0):
                continue
            err = abs(val) * math.sqrt((ea / fa) ** 2 + (eb / fb) ** 2) if fa and eb >= 0 else None
            out.append(dict(source=source, tool=tool, ratio=label, value=val, err=err))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "docs")
    args = p.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    rows = load()
    rr = ratios(rows)
    with (args.output / "line_tool_comparison.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["source", "tool", "line", "component",
                                           "flux", "flux_err", "fwhm_kms", "snr"])
        w.writeheader(); w.writerows(rows)
    with (args.output / "line_ratio_comparison.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["source", "tool", "ratio", "value", "err"])
        w.writeheader(); w.writerows(rr)
    if not rr:
        print("no comparable ratios yet; wrote empty tables")
        return 0

    labels = sorted({r["ratio"] for r in rr})
    sources = sorted({r["source"] for r in rr})
    groups = []
    for label in labels:
        sub = [r for r in rr if r["ratio"] == label
               and 0.02 <= r["value"] <= 50.0]
        if sub:
            groups.append((label, sub))
    fig, axes = plt.subplots(len(groups), 1,
                             figsize=(11, max(2.6, 2.4 * len(groups))),
                             squeeze=False)
    for ax, (label, sub) in zip(axes[:, 0], groups):
        y = np.arange(len(sub))[::-1]
        for yi, r in zip(y, sub):
            ax.errorbar(r["value"], yi,
                        xerr=r["err"] if r["err"] and np.isfinite(r["err"]) and r["err"] > 0 else None,
                        fmt="o", ms=5, capsize=2)
        ax.set_yticks(y)
        ax.set_yticklabels([f"{r['source'].split('_z_')[0]}  {r['tool']}" for r in sub], fontsize=8)
        ax.set_xscale("log")
        ax.set_xlabel(label)
        ax.grid(axis="x", ls=":", alpha=0.5)
    fig.suptitle("Line-ratio comparison across line-fitting tools", y=0.995)
    fig.tight_layout()
    fig.savefig(args.output / "line_tool_comparison.png", dpi=140)
    fig.savefig(args.output / "line_tool_comparison.pdf")
    plt.close(fig)

    # Inter-tool dispersion for ratios measured by >=2 tools.
    summary = []
    for label in labels:
        for source in sources:
            vals = [r["value"] for r in rr if r["ratio"] == label and r["source"] == source]
            if len(vals) >= 2:
                vals = np.asarray(vals, float)
                rng = np.random.default_rng(42)
                boots = [float(np.median(rng.choice(vals, vals.size, replace=True)))
                         for _ in range(1000)]
                summary.append(dict(source=source, ratio=label, n=len(vals),
                                    median=float(np.median(vals)),
                                    ci16=float(np.percentile(boots, 16)),
                                    ci84=float(np.percentile(boots, 84)),
                                    log_scatter=float(np.std(np.log(vals)))))
    with (args.output / "line_ratio_scatter.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["source", "ratio", "n", "median", "ci16", "ci84", "log_scatter"])
        w.writeheader(); w.writerows(summary)
    print(f"read {len(rows)} line measurements, {len(rr)} ratios, {len(summary)} multi-tool groups")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
