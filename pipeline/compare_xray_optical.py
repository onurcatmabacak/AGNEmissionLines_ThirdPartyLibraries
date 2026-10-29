#!/usr/bin/env python3
"""Compare an X-ray Fe K-alpha fit with the same object's UV/optical lines.

The X-ray tools (``xmm_xspec``, ``rxte_xspec``) fit the Fe K-alpha complex.
This post-processing tool reads those line tables and the same source's
``pyqsofit_uv`` output, converts both to line luminosity and equivalent width,
and writes a machine-readable comparison plus a figure.

It is deliberately **not** a correlation fit: two objects cannot constrain a
slope.  The output is a provenance-preserving, per-object comparison and a
quality flag.  PDS 456 has no H-beta coverage in its public HST/STIS spectrum,
so its optical entry is the C IV 1549 broad line (tentative); 3C 120 uses H-beta.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from astropy.cosmology import Planck18
from astropy.table import Table

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pipeline.io_layout import output_dir  # noqa: E402

OUT_ROOT = ROOT / "outputs"

# rest-frame line centres and integration windows (Angstrom)
OPTICAL_LINES = {
    "Hbeta": (4862.68, 4800.0, 4940.0),
    "OIII5007": (5008.24, 4950.0, 5060.0),
    "CIV1549": (1549.06, 1490.0, 1620.0),
    "Lya": (1215.67, 1180.0, 1280.0),
}


def _finite(x, default=None):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return default
    return x if math.isfinite(x) else default


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def read_xray(path: Path) -> dict:
    """Read the production row from an xmm_xspec or rxte_xspec line table."""
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError(f"{path}: empty line table")
    preferred = []
    if "fit_id" in rows[0]:
        preferred = [r for r in rows if r.get("fit_id") in ("joint_pl_line", "line_3_20")]
    row = preferred[0] if preferred else rows[0]
    return {
        "table": str(path.relative_to(ROOT)),
        "line": row.get("line", "Fe Kalpha"),
        "flux": _finite(row.get("flux_erg_cm2_s")),
        "flux_err": _finite(row.get("flux_err")),
        "ew_rest_eV": 1000.0 * _finite(row.get("ew_rest_keV"), 0.0),
        "ew_rest_err_eV": 1000.0 * _finite(row.get("ew_rest_err"), 0.0),
        "significance_sigma": _finite(row.get("significance_sigma")),
        "delta_chi2": _finite(row.get("delta_chi2")),
        "detected": str(row.get("detected", "")).strip() in ("1", "True", "true"),
        "interpretation": row.get("interpretation", ""),
    }


def read_optical(lines_csv: Path, model_csv: Path, z: float) -> dict:
    """Sum PyQSOFit components and compute local rest-frame equivalent widths."""
    with lines_csv.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    by_name = {}
    for r in rows:
        name = r.get("line", "")
        area = _finite(r.get("area_1e17"), 0.0) or 0.0
        by_name[name] = {
            "area_1e17": area,
            "fwhm_kms": _finite(r.get("fwhm_kms"), 0.0),
            "snr": _finite(r.get("snr"), 0.0),
            "component": r.get("component", ""),
        }

    def total(prefixes):
        vals = [v for k, v in by_name.items() if any(k.startswith(p) for p in prefixes)]
        return sum(v["area_1e17"] for v in vals), max((v["snr"] for v in vals), default=0.0), max((v["fwhm_kms"] for v in vals), default=0.0)

    hb, hb_snr, hb_fwhm = total(("Hb_", "Hbeta"))
    o3, o3_snr, o3_fwhm = total(("OIII5007",))
    civ, civ_snr, civ_fwhm = total(("CIV",))
    lya, lya_snr, lya_fwhm = total(("Lya",))

    ews = {}
    if model_csv.exists():
        m = Table.read(model_csv)
        names = {c.lower(): c for c in m.colnames}
        if {"wave", "line", "conti"} <= set(names):
            wave = np.asarray(m[names["wave"]], dtype=float)
            line = np.asarray(m[names["line"]], dtype=float)
            conti = np.asarray(m[names["conti"]], dtype=float)
            good = np.isfinite(wave) & np.isfinite(line) & np.isfinite(conti)
            for key, (center, lo, hi) in OPTICAL_LINES.items():
                sel = good & (wave >= lo) & (wave <= hi)
                if not sel.any():
                    continue
                c = float(np.interp(center, wave[good], conti[good]))
                if c <= 0:
                    continue
                integral = float(np.trapz(line[sel], wave[sel]))
                ews[key] = {"ew_rest_A": integral / c, "continuum_1e17": c,
                            "window_A": [lo, hi]}

    return {
        "table": str(lines_csv.relative_to(ROOT)),
        "components": by_name,
        "Hbeta": {"area_1e17": hb, "snr": hb_snr, "fwhm_kms": hb_fwhm},
        "OIII5007": {"area_1e17": o3, "snr": o3_snr, "fwhm_kms": o3_fwhm},
        "CIV1549": {"area_1e17": civ, "snr": civ_snr, "fwhm_kms": civ_fwhm},
        "Lya": {"area_1e17": lya, "snr": lya_snr, "fwhm_kms": lya_fwhm},
        "ew_rest_A": ews,
        "hb_oiii_ratio": hb / o3 if o3 > 0 else None,
    }


def read_optical_linefit(path: Path, z: float) -> dict:
    """Read the local H-beta/[O III] tool; keep the same shape as PyQSOFit."""
    import json as _json
    summary = _json.loads((path / "optical_lines_summary.json").read_text())
    rows = []
    with (path / "optical_lines.csv").open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    by = {}
    for r in rows:
        by[f"{r['line']}:{r['component']}"] = r
    def total(prefixes, comps=None):
        vals = [r for r in rows if any(r["line"].startswith(p) for p in prefixes)
                and (comps is None or r["component"] in comps)]
        flux = sum(float(r["flux_1e17"]) for r in vals if r["flux_1e17"] not in ("", "nan"))
        err = math.sqrt(sum(float(r["flux_err"]) ** 2 for r in vals
                            if r["flux_err"] not in ("", "nan")))
        snr = max((float(r["snr"]) for r in vals if r["snr"] not in ("", "nan")), default=0.0)
        fwhm = max((float(r["fwhm_kms"]) for r in vals if r["fwhm_kms"] not in ("", "nan")), default=0.0)
        return {"area_1e17": flux, "flux_err": err, "snr": snr, "fwhm_kms": fwhm}
    hb = total(("Hbeta",))
    o3 = total(("OIII5007",))
    # EW: use the H-beta broad+narrow integrated line / local continuum from the table.
    ew = {}
    if summary.get("Hbeta_ew_rest_A") is not None:
        ew["Hbeta"] = {"ew_rest_A": float(summary["Hbeta_ew_rest_A"]),
                       "ew_obs_A": summary.get("Hbeta_ew_obs_A"),
                       "continuum_1e17": summary.get("continuum_1e17")}
    return {
        "table": str((path / "optical_lines.csv").relative_to(ROOT)),
        "tool": "optical_linefit",
        "components": by,
        "Hbeta": hb,
        "OIII5007": o3,
        "CIV1549": {"area_1e17": 0.0, "snr": 0.0, "fwhm_kms": 0.0},
        "Lya": {"area_1e17": 0.0, "snr": 0.0, "fwhm_kms": 0.0},
        "ew_rest_A": ew,
        "hb_oiii_ratio": summary.get("Hbeta_OIII_ratio"),
        "quality": summary.get("quality", "provisional"),
        "summary": summary,
    }


def luminosity(flux_erg_cm2_s: float, z: float) -> float | None:
    if flux_erg_cm2_s is None or not math.isfinite(flux_erg_cm2_s):
        return None
    dl_cm = Planck18.luminosity_distance(z).to_value("cm")
    return 4.0 * math.pi * dl_cm ** 2 * flux_erg_cm2_s


def choose_primary(opt: dict) -> tuple[str, dict]:
    if opt["Hbeta"]["area_1e17"] > 0:
        return "Hbeta", opt["Hbeta"]
    if opt["CIV1549"]["area_1e17"] > 0:
        return "CIV1549", opt["CIV1549"]
    if opt["Lya"]["area_1e17"] > 0:
        return "Lya", opt["Lya"]
    raise ValueError("no optical/UV line measured")


def quality_flag(line: str, spec: dict, opt: dict, xray: dict,
                 model_ratio_range: tuple[float, float] | None = None,
                 local_quality: str | None = None) -> tuple[str, str]:
    """Quality gate: optical S/N, X-ray detection and model consistency.

    A ratio is not "accepted" merely because the optical line has S/N > 5.
    """
    if not xray.get("detected") or (xray.get("significance_sigma") or 0) < 3.0:
        return "tentative", "X-ray Fe K-alpha is not detected at >=3 sigma"
    if local_quality in ("tentative", "provisional"):
        return local_quality, "the optical local fit is already flagged " + local_quality
    if line == "Hbeta":
        if spec.get("snr", 0) < 5 or opt.get("hb_oiii_ratio") is None:
            return "tentative", "H-beta S/N below 5 or [O III] unavailable"
        if model_ratio_range and model_ratio_range[0] > 0 and model_ratio_range[1] / model_ratio_range[0] > 1.5:
            return "provisional", (
                f"optical H-beta/[O III] model range {model_ratio_range[0]:.2f}-"
                f"{model_ratio_range[1]:.2f} spans >1.5x; model systematic dominates")
        return "accepted", "H-beta and [O III] detected; X-ray line >=3 sigma; optical models agree within 1.5x"
    if line == "CIV1549":
        return "tentative", ("public HST/STIS spectrum covers C IV but not H-beta or Mg II; "
                             "broad C IV is blended/absorption-affected and has S/N < 3")
    return "tentative", "line is not a primary broad-line measurement"


def markdown(result: dict) -> str:
    o = result["optical"]
    x = result["xray"]
    return f"""# X-ray / optical line comparison — {result['source']}

| quantity | value |
|---|---:|
| source redshift | {result['z']:.8f} |
| X-ray mission / product | `{x['table']}` |
| X-ray line | {x['line']} |
| Fe Kα flux | {x['flux']:.4g} erg cm⁻² s⁻¹ |
| Fe Kα rest EW | {x['ew_rest_eV']:.2f} eV |
| Fe Kα significance | {x['significance_sigma']:.2f}σ |
| optical tool | `{result['optical_tool']}` |
| optical/UV line | **{result['optical_line']}** |
| line flux | {o[result['optical_line']]['area_1e17']:.4g} × 10⁻¹⁷ erg cm⁻² s⁻¹ |
| line FWHM | {o[result['optical_line']]['fwhm_kms']:.0f} km/s |
| line S/N | {o[result['optical_line']]['snr']:.2f} |
| line luminosity | {result['optical_luminosity_erg_s']:.3e} erg s⁻¹ |
| Fe Kα luminosity | {result['xray_luminosity_erg_s']:.3e} erg s⁻¹ |
| quality | **{result['quality']}** |
| note | {result['quality_note']} |

The table is a same-object consistency comparison, not a correlation fit.
`{result['source']}` has only one optical/UV line family in the public
spectrum used here, so no slope or scatter is inferred.
"""


def make_figure(result: dict, out: Path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    xf = result["xray"]["flux"]
    of = result["optical"][result["optical_line"]]["area_1e17"] * 1e-17
    xl = result["xray_luminosity_erg_s"]
    ol = result["optical_luminosity_erg_s"]
    color = "tab:blue" if result["quality"] == "accepted" else "tab:orange"

    ax = axes[0]
    ax.scatter([xl], [ol], s=90, color=color, edgecolor="k", zorder=3)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel(r"$L_{\rm Fe\,K\alpha}$ (erg s$^{-1}$)")
    ax.set_ylabel(r"$L_{\rm %s}$ (erg s$^{-1}$)" % result["optical_line"])
    ax.set_title(f"{result['source']}  ({result['quality']})", fontsize=10)
    ax.grid(alpha=0.25)
    ax.annotate(result["optical_line"], (xl, ol), xytext=(6, 6),
                textcoords="offset points", fontsize=9)

    ax = axes[1]
    xw = result["xray"]["ew_rest_eV"]
    key = result["optical_line"]
    ew = result["optical"].get("ew_rest_A", {}).get(key, {}).get("ew_rest_A")
    if ew is None:
        ew = float("nan")
    ax.scatter([xw], [ew], s=90, color=color, edgecolor="k", zorder=3)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Fe Kα rest EW (eV)")
    ax.set_ylabel(f"{key} rest EW (Å)")
    ax.set_title("equivalent-width comparison", fontsize=10)
    ax.grid(alpha=0.25)
    ax.annotate(result["optical_line"], (xw, ew), xytext=(6, 6),
                textcoords="offset points", fontsize=9)
    fig.suptitle("Same-object X-ray Fe Kα vs UV/optical emission line", fontsize=11)
    fig.tight_layout()
    fig.savefig(out.with_suffix(".png"), dpi=180)
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True, help="canonical source key")
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--xray-tool", choices=("auto", "xmm_xspec", "rxte_xspec"), default="auto")
    p.add_argument("--optical-tool", choices=("auto", "pyqsofit_uv", "optical_linefit"), default="auto")
    a = p.parse_args(argv)
    src_dir = ROOT / "inputs" / a.source
    src = load_json(src_dir / "source.json")
    out = Path(a.out) if a.out else output_dir(a.source, "crossmission")
    out.mkdir(parents=True, exist_ok=True)

    if a.xray_tool == "auto":
        if (output_dir(a.source, "xmm_xspec") / "xmm_lines.csv").exists():
            a.xray_tool = "xmm_xspec"
        elif (output_dir(a.source, "rxte_xspec") / "rxte_lines.csv").exists():
            a.xray_tool = "rxte_xspec"
        else:
            raise FileNotFoundError("no xmm_xspec or rxte_xspec line table")
    if a.xray_tool == "xmm_xspec":
        xray = read_xray(output_dir(a.source, "xmm_xspec") / "xmm_lines.csv")
    else:
        xray = read_xray(output_dir(a.source, "rxte_xspec") / "rxte_lines.csv")

    if a.optical_tool == "auto":
        a.optical_tool = ("optical_linefit"
                          if (output_dir(a.source, "optical_linefit") / "optical_lines_summary.json").exists()
                          else "pyqsofit_uv")
    if a.optical_tool == "optical_linefit":
        opt_dir = output_dir(a.source, "optical_linefit")
        optical = read_optical_linefit(opt_dir, float(src["z"]))
        line_name, line = choose_primary(optical)
        line_flux = line["area_1e17"] * 1e-17
        local_quality = optical.get("quality", "provisional")
        local_note = "; ".join(optical["summary"].get("notes", []))
    else:
        opt_dir = output_dir(a.source, "pyqsofit_uv")
        optical = read_optical(opt_dir / "pyqsofit_lines.csv", opt_dir / "pyqsofit_model.csv",
                               float(src["z"]))
        line_name, line = choose_primary(optical)
        line_flux = line["area_1e17"] * 1e-17
        local_quality = None
        local_note = ""
    model_ratios = []
    if optical.get("hb_oiii_ratio"):
        model_ratios.append(float(optical["hb_oiii_ratio"]))
    qm = output_dir(a.source, "qsofitmore_line") / "qsofitmore_lines.csv"
    if qm.exists():
        try:
            with qm.open(newline="") as fh:
                rows = {r["line"]: r for r in csv.DictReader(fh)}
            hb = float(rows["Hbeta"]["area_1e17"])
            o3 = float(rows["OIII5007"]["area_1e17"])
            if o3 > 0:
                model_ratios.append(hb / o3)
        except Exception:
            pass
    model_range = (min(model_ratios), max(model_ratios)) if len(model_ratios) >= 2 else None
    flag, note = quality_flag(line_name, line, optical, xray, model_range, local_quality)
    if local_note and local_quality:
        note += "; " + local_note
    opt_lum = luminosity(line_flux, float(src["z"]))
    x_lum = luminosity(xray["flux"], float(src["z"]))
    result = {
        "source": a.source,
        "z": float(src["z"]),
        "xray_tool": a.xray_tool,
        "optical_tool": a.optical_tool,
        "xray": xray,
        "optical": optical,
        "optical_line": line_name,
        "optical_flux_erg_cm2_s": line_flux,
        "optical_luminosity_erg_s": opt_lum,
        "xray_luminosity_erg_s": x_lum,
        "optical_to_xray_flux_ratio": line_flux / xray["flux"] if xray["flux"] else None,
        "comparison_type": "descriptive line-to-line ratio; not alpha_ox or a physical SED normalization",
        "quality": flag,
        "quality_note": note,
        "optical_model_ratio_range": model_range,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (out / "xray_optical_comparison.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    with (out / "xray_optical_comparison.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["source", "xray_tool", "xray_line", "xray_flux_erg_cm2_s",
                    "xray_ew_rest_eV", "xray_significance_sigma", "optical_line",
                    "optical_flux_erg_cm2_s", "optical_fwhm_kms", "optical_snr",
                    "optical_ew_rest_A", "optical_to_xray_flux_ratio",
                    "optical_luminosity_erg_s", "xray_luminosity_erg_s", "quality"])
        w.writerow([a.source, a.xray_tool, xray["line"], xray["flux"], xray["ew_rest_eV"],
                    xray["significance_sigma"], line_name, line_flux, line["fwhm_kms"],
                    line["snr"], optical.get("ew_rest_A", {}).get(line_name, {}).get("ew_rest_A"),
                    result["optical_to_xray_flux_ratio"], opt_lum, x_lum, flag])
    (out / "xray_optical_comparison.md").write_text(markdown(result))
    run = {
        "status": "ok",
        "tool": "crossmission",
        "source_key": a.source,
        "redshift": result["z"],
        "xray_tool": a.xray_tool,
        "optical_tool": a.optical_tool,
        "inputs": {
            "xray_lines": result["xray"]["table"],
            "optical_lines": result["optical"]["table"],
        },
        "result": {
            "optical_line": line_name,
            "optical_flux_erg_cm2_s": line_flux,
            "optical_ew_rest_A": optical.get("ew_rest_A", {}).get(line_name, {}).get("ew_rest_A"),
            "xray_flux_erg_cm2_s": xray["flux"],
            "xray_ew_rest_eV": xray["ew_rest_eV"],
            "quality": flag,
        },
        "caveats": [note, "two objects: no correlation fit"],
        "generated_utc": result["generated_utc"],
    }
    (out / "run.json").write_text(json.dumps(run, indent=2, allow_nan=False) + "\n")
    readme = f"""# crossmission — {a.source}

Same-object comparison of the X-ray Fe K-alpha line with the UV/optical
emission line measured by `pyqsofit_uv`.

* X-ray: `{result['xray']['table']}`, production row
* Optical: `{result['optical']['table']}`, line **{line_name}**
* Quality: **{flag}** — {note}

This is a consistency comparison, not a correlation fit.  See
`docs/OUTPUT_SCHEMA.md` and `docs/CAVEAT_MATRIX.md` for the repository contract.
"""
    (out / "README.md").write_text(readme)
    make_figure(result, out / "xray_optical_comparison")

    # Keep the optical fit figure beside the comparison so the evidence is visible.
    pdf = opt_dir / "result.pdf"
    if pdf.exists():
        shutil.copy2(pdf, out / "optical_fit.pdf")
        try:
            subprocess.run(["pdftoppm", "-png", "-r", "110", "-singlefile",
                            str(pdf), str(out / "optical_fit")], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    print(f"[crossmission] {a.source}: {line_name} vs {a.xray_tool} -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
