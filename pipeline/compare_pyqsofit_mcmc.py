#!/usr/bin/env python3
"""Compare PyQSOFit MCMC line fluxes with the committed MC and other line tools.

This is intentionally a reporting helper, not part of the fit.  It reads the
per-tool CSV products already stored under ``outputs/<tool>/<source_key>/`` and writes
one tidy comparison table next to the PyQSOFit MCMC products.

    python pipeline/compare_pyqsofit_mcmc.py 04592649654_z_0.5874
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import sys  # noqa: E402
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from pipeline.io_layout import output_dir  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: str | None) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if out == out and abs(out) != float("inf") else None


def keyed(rows: list[dict[str, str]], line_col: str, comp_col: str,
          value_col: str, err_col: str | None = None):
    out = {}
    for row in rows:
        line = (row.get(line_col) or "").strip()
        comp = (row.get(comp_col) or "").strip().lower()
        if not line:
            continue
        out[(line, comp)] = (as_float(row.get(value_col)),
                             as_float(row.get(err_col)) if err_col else None)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_key")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    mcmc_dir = output_dir(args.source_key, "pyqsofit") / "mcmc"
    mc_dir = output_dir(args.source_key, "pyqsofit") / "mc"

    mcmc = keyed(read_csv(mcmc_dir / "pyqsofit_mcmc_summary.csv"),
                 "line", "component", "mcmc_median", None)
    mcmc_bounds = {}
    for row in read_csv(mcmc_dir / "pyqsofit_mcmc_summary.csv"):
        key = ((row.get("line") or "").strip(), (row.get("component") or "").strip().lower())
        mcmc_bounds[key] = (as_float(row.get("mcmc_p16")), as_float(row.get("mcmc_p84")),
                            as_float(row.get("n_posterior")))
    mc = keyed(read_csv(mc_dir / "pyqsofit_mc_summary.csv"),
               "line", "component", "median", None)
    mle = keyed(read_csv(output_dir(args.source_key, "pyqsofit_uv") / "pyqsofit_lines.csv"),
                "line", "component", "area_1e17", None)

    gandalf = keyed(read_csv(output_dir(args.source_key, "gandalf_line") / "gandalf_lines.csv"),
                    "line", "component", "flux_1e17", "flux_err_1e17")
    s3fit = keyed(read_csv(output_dir(args.source_key, "s3fit_line") / "s3fit_lines.csv"),
                  "line", "component", "flux_1e17", "flux_err_1e17")
    galspec = keyed(read_csv(output_dir(args.source_key, "galspec_line") / "galspec_lines.csv"),
                    "line", "component", "flux_1e17", "flux_err_1e17")
    qgfit = keyed(read_csv(output_dir(args.source_key, "qgfit") / "qgfit_lines.csv"),
                  "qgfit_line", "component", "flux_1e17", "flux_err_1e17")

    targets = [
        ("Hb", "broad", [("gandalf", "Hbeta", "broad"), ("s3fit", "H-beta", "BLR"),
                          ("galspec", "Hbeta", "broad"), ("qgfit", "Hbeta_br", "broad")],
         [("Hb_br", "broad")]),
        ("Hb", "narrow", [("gandalf", "Hbeta", "narrow"), ("s3fit", "H-beta", "NLR"),
                           ("galspec", "Hbeta", "narrow"), ("qgfit", "Hbeta_na", "narrow")],
         [("Hb_na", "narrow")]),
        ("Hb", "total", [("gandalf", "Hbeta", "total"), ("s3fit", "H-beta", "total"),
                          ("galspec", "Hbeta", "total"), ("qgfit", "Hbeta_br+Hbeta_na", "total")],
         [("Hb_br", "broad"), ("Hb_na", "narrow")]),
        ("OIII5007", "broad", [("galspec", "OIII_5007", "wing")],
         [("OIII5007w", "broad")]),
        ("OIII5007", "narrow", [("gandalf", "[OIII]5007", "narrow"), ("s3fit", "[O III]:5008", "NLR"),
                                 ("galspec", "OIII_5007", "narrow"), ("qgfit", "OIII5007", "narrow")],
         [("OIII5007c", "narrow")]),
        ("OIII5007", "total", [("galspec", "OIII_5007", "total"), ("s3fit", "[O III]:5008", "total")],
         [("OIII5007w", "broad"), ("OIII5007c", "narrow")]),
        ("MgII", "broad", [("s3fit", "Mg II]:2796", "BLR"), ("qgfit", "MgII", "mix")],
         [("MgII_br", "broad")]),
    ]
    tool_maps = {"gandalf": gandalf, "s3fit": s3fit, "galspec": galspec, "qgfit": qgfit}

    rows = []
    for line, comp, refs, components in targets:
        medians = []
        errors = []
        ns = []
        for mline, mcomp in components:
            med, _ = mcmc.get((mline, mcomp), (None, None))
            p16, p84, n = mcmc_bounds.get((mline, mcomp), (None, None, None))
            if med is not None:
                medians.append(med)
            if p16 is not None and p84 is not None:
                errors.append(0.5 * (p84 - p16))
            if n is not None:
                ns.append(n)
        median = sum(medians) if medians else None
        err = (sum(e * e for e in errors) ** 0.5) if errors else None
        p16 = (median - err) if median is not None and err is not None else None
        p84 = (median + err) if median is not None and err is not None else None
        mc_components = [mc.get((mline, mcomp), (None, None))[0] for mline, mcomp in components]
        mc_median = sum(v for v in mc_components if v is not None) if any(v is not None for v in mc_components) else None
        mle_components = [mle.get((mline, mcomp), (None, None))[0] for mline, mcomp in components]
        mle_flux = sum(v for v in mle_components if v is not None) if any(v is not None for v in mle_components) else None
        row = {
            "line": line, "component": comp,
            "mcmc_line": "+".join(f"{a}_{b}" for a, b in components),
            "mcmc_component": comp, "mcmc_n": min(ns) if ns else None,
            "mcmc_median_1e17": median,
            "mcmc_p16_1e17": p16, "mcmc_p84_1e17": p84,
            "mcmc_err_1e17": err,
            "mc_median_1e17": mc_median,
            "pyqsofit_mle_1e17": mle_flux,
        }
        if len(components) > 1:
            row["note"] = "MCMC total: broad+narrow medians; error added in quadrature"
        for tool, rline, rcomp in refs:
            val, err = tool_maps[tool].get((rline, rcomp.lower()), (None, None))
            row[f"{tool}_flux_1e17"] = val
            row[f"{tool}_err_1e17"] = err
        if median is not None and mc_median not in (None, 0):
            row["mcmc_over_mc"] = median / mc_median
        rows.append(row)

    out = Path(args.out) if args.out else (mcmc_dir / "comparison_mc_tools.csv")
    fieldnames = sorted({key for row in rows for key in row})
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
