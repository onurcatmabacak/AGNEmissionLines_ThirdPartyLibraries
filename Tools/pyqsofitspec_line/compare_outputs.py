#!/usr/bin/env python3
"""Compare the PyQSOFitSpec line fluxes with the sibling tools in this repo.

Reads the outputs already written under ``outputs/<tool>/<source_key>/`` (PyQSOFit,
GANDALF, S3Fit, GalSpec, QGfit) and the PyQSOFitSpec totals, and writes
``cross_tool_comparison.csv`` / ``.json`` into the PyQSOFitSpec output
directory.  Standard library only; run it on the host after the container.

    python3 Tools/pyqsofitspec_line/compare_outputs.py \
        outputs/<tool>/04592649654_z_0.5874

Totals compared (1e-17 erg s-1 cm-2, rest-frame vacuum wavelengths):

  MgII       Mg II 2798 blend (broad + narrow)
  Hbeta      H-beta broad + narrow
  OIII5007   [O III] 5007 core + broad wing

Per tool the *closest available equivalent* is used and recorded in the
"definition" column; the tools do not decompose the blends identically.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

LINE_KEYS = ("MgII", "Hbeta", "OIII5007")


def read_csv(path: Path):
    if not path.is_file():
        return []
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def as_float(value):
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out:  # NaN
        return None
    return out


def pyqsofitspec_totals(out_dir: Path):
    rows = read_csv(out_dir / "pyqsofitspec_totals.csv")
    out = {}
    for row in rows:
        key = row["total"]
        out[key] = {
            "flux": as_float(row["flux_1e17"]),
            "err": as_float(row["flux_err_1e17"]),
            "definition": "+".join(row["components"].split("+")),
            "snr": as_float(row["snr"]),
        }
    return out


def pyqsofit_totals(root: Path):
    """pyqsofit_uv/pyqsofit_lines.csv: area_1e17, no flux errors."""
    path = root / "pyqsofit_uv" / "pyqsofit_lines.csv"
    rows = {row["line"]: row for row in read_csv(path)}
    if not rows:
        return {}
    def total(parts):
        vals = [as_float(rows.get(p, {}).get("area_1e17")) for p in parts]
        if any(v is None for v in vals):
            return None
        return sum(vals)
    out = {
        "MgII": total(["MgII_br", "MgII_na"]),
        "Hbeta": total(["Hb_br", "Hb_na"]),
        "OIII5007": total(["OIII5007w", "OIII5007c"]),
    }
    return {
        key: {"flux": val, "err": None,
              "definition": {"MgII": "MgII_br+MgII_na",
                             "Hbeta": "Hb_br+Hb_na",
                             "OIII5007": "OIII5007w+OIII5007c"}[key],
              "snr": None}
        for key, val in out.items() if val is not None
    }


def gandalf_totals(root: Path):
    """gandalf_line/gandalf_lines.csv: Hbeta broad+narrow, [O III] 5007."""
    path = root / "gandalf_line" / "gandalf_lines.csv"
    rows = read_csv(path)
    if not rows:
        return {}
    by = {}
    for row in rows:
        by[(row["line"], row["component"])] = row

    def flux(line, component):
        row = by.get((line, component))
        return as_float(row["flux_1e17"]) if row else None

    out = {}
    hb_total = flux("Hbeta", "total")
    hb = [flux("Hbeta", "broad"), flux("Hbeta", "narrow")]
    if hb_total is not None:
        out["Hbeta"] = {"flux": hb_total, "err": None,
                        "definition": "Hbeta total (GANDALF)", "snr": None}
    elif all(v is not None for v in hb):
        out["Hbeta"] = {"flux": sum(hb), "err": None,
                        "definition": "Hbeta broad+narrow (GANDALF)", "snr": None}
    o3 = flux("[OIII]5007", "narrow") or flux("[OIII]5007", "total")
    if o3 is not None:
        out["OIII5007"] = {"flux": o3, "err": None,
                           "definition": "OIII5007 narrow line", "snr": None}
    mg2 = None
    for (line, component), row in by.items():
        if line.lower().startswith("mgii") or line.lower() == "mg2":
            value = as_float(row["flux_1e17"])
            if value is not None:
                mg2 = (mg2 or 0.0) + value
    if mg2 is not None:
        out["MgII"] = {"flux": mg2, "err": None,
                       "definition": "sum of Mg II components (GANDALF)", "snr": None}
    return out


def s3fit_totals(root: Path):
    """s3fit_line/s3fit_lines.csv: component total rows."""
    path = root / "s3fit_line" / "s3fit_lines.csv"
    rows = read_csv(path)
    if not rows:
        return {}
    totals = {}
    for row in rows:
        if row["component"] != "total":
            continue
        name = row["line"]
        flux = as_float(row["flux_1e17"])
        err = as_float(row["flux_err_1e17"])
        if flux is None:
            continue
        if name.startswith("Mg II"):
            # Mg II 2796 + 2804 doublet
            totals["MgII"] = totals.get("MgII", 0.0) + flux
            totals.setdefault("_errMgII", 0.0)
        elif name in ("H-beta",):
            totals["Hbeta"] = flux
            totals["_errHbeta"] = err
        elif name in ("[O III]:5008",):
            totals["OIII5007"] = flux
            totals["_errOIII5007"] = err
    out = {}
    for key in LINE_KEYS:
        if key in totals:
            out[key] = {
                "flux": totals[key],
                "err": totals.get(f"_err{key}"),
                "definition": {"MgII": "Mg II 2796+2804 total (S3Fit)",
                               "Hbeta": "H-beta total (S3Fit)",
                               "OIII5007": "[O III] 5007 total (S3Fit)"}[key],
                "snr": None,
            }
    return out


def galspec_totals(root: Path):
    """galspec_line/galspec_lines.csv: component total rows."""
    path = root / "galspec_line" / "galspec_lines.csv"
    rows = read_csv(path)
    if not rows:
        return {}
    out = {}
    for row in rows:
        if row.get("component") != "total":
            continue
        name = row.get("line", "")
        flux = as_float(row.get("flux_1e17"))
        err = as_float(row.get("flux_err_1e17"))
        if flux is None:
            continue
        if name == "Hbeta":
            out["Hbeta"] = {"flux": flux, "err": err,
                            "definition": "H-beta total (GalSpec)", "snr": None}
        elif name in ("OIII_5007", "OIII5007"):
            out["OIII5007"] = {"flux": flux, "err": err,
                               "definition": "[O III] 5007 total (GalSpec)",
                               "snr": None}
    return out


def qgfit_totals(root: Path):
    """qgfit/qgfit_lines.csv: total row where present, else the single component."""
    path = root / "qgfit" / "qgfit_lines.csv"
    rows = read_csv(path)
    if not rows:
        return {}
    out = {}
    by = {}
    for row in rows:
        by.setdefault(row.get("line", ""), []).append(row)
    for key, names in (("Hbeta", ("Hbeta",)), ("OIII5007", ("OIII5007",)),
                       ("MgII", ("MgII",))):
        candidates = [r for name in names for r in by.get(name, [])]
        if not candidates:
            continue
        total = next((r for r in candidates if r.get("component") == "total"), None)
        row = total or candidates[0]
        flux = as_float(row.get("flux_1e17"))
        err = as_float(row.get("flux_err_1e17"))
        if flux is None:
            continue
        if key == "OIII5007":
            definition = ("[O III] 5007 total (QGfit)" if total is not None
                          else "[O III] 5007 narrow component only (QGfit)")
        elif key == "MgII":
            definition = "Mg II 2798 blended profile (QGfit)"
        else:
            definition = "H-beta total (QGfit)"
        out[key] = {"flux": flux, "err": err, "definition": definition, "snr": None}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source_dir", help="outputs/<tool>/<source_key> directory")
    args = ap.parse_args(argv)
    root = Path(args.source_dir).resolve()
    out_dir = root / "pyqsofitspec_line"
    if not out_dir.is_dir():
        raise SystemExit(f"missing {out_dir}")

    ours = pyqsofitspec_totals(out_dir)
    tools = {
        "pyqsofitspec": ours,
        "pyqsofit": pyqsofit_totals(root),
        "gandalf": gandalf_totals(root),
        "s3fit": s3fit_totals(root),
        "galspec": galspec_totals(root),
        "qgfit": qgfit_totals(root),
    }
    rows = []
    for key in LINE_KEYS:
        base = tools["pyqsofitspec"].get(key, {})
        base_flux = base.get("flux")
        for tool, values in tools.items():
            entry = values.get(key)
            if not entry or entry.get("flux") is None:
                continue
            ratio = (entry["flux"] / base_flux) if base_flux else None
            rows.append({
                "line": key,
                "tool": tool,
                "flux_1e17": f"{entry['flux']:.4f}",
                "flux_err_1e17": "" if entry.get("err") is None else f"{entry['err']:.4f}",
                "flux_erg_s_cm2": f"{entry['flux'] * 1e-17:.6e}",
                "ratio_to_pyqsofitspec": "" if ratio is None else f"{ratio:.4f}",
                "difference_1e17": "" if ratio is None else f"{entry['flux'] - base_flux:.4f}",
                "definition": entry.get("definition", ""),
            })

    out_csv = out_dir / "cross_tool_comparison.csv"
    with out_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "source": root.name,
        "reference": "pyqsofitspec_line/pyqsofitspec_totals.csv",
        "units": "1e-17 erg s-1 cm-2",
        "lines": {},
    }
    for key in LINE_KEYS:
        base = tools["pyqsofitspec"].get(key)
        if not base:
            continue
        entry = {"pyqsofitspec_flux_1e17": base["flux"],
                 "pyqsofitspec_err_1e17": base.get("err"),
                 "tools": {}}
        for tool in ("pyqsofit", "gandalf", "s3fit", "galspec", "qgfit"):
            other = tools[tool].get(key)
            if not other or other.get("flux") is None:
                continue
            entry["tools"][tool] = {
                "flux_1e17": other["flux"],
                "ratio": other["flux"] / base["flux"],
                "difference_1e17": other["flux"] - base["flux"],
                "definition": other.get("definition", ""),
            }
        summary["lines"][key] = entry
    with (out_dir / "cross_tool_comparison.json").open("w") as fh:
        json.dump(summary, fh, indent=2)

    print(f"wrote {out_csv}")
    for row in rows:
        print(f"  {row['line']:<10} {row['tool']:<14} {row['flux_1e17']:>12}  "
              f"ratio={row['ratio_to_pyqsofitspec'] or '-':>7}  {row['definition']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
