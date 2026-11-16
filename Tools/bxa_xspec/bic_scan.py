#!/usr/bin/env python3
"""Prior-free BIC/AIC comparison for the ``bxa_xspec`` model suite.

The nested-sampling evidence in ``run_bxa_xspec.py`` is the production answer,
but it depends on the prior volume (especially the log-uniform line
normalisation and line-energy prior).  This script asks the complementary
question on the *same* prepared PPS spectra and the *same* frozen
cross-calibration constants:

    BIC = chi2 + k ln n        AIC = chi2 + 2k

``n`` is the number of noticed spectral bins (identical for every model), and
``k`` is the number of free model parameters in the config.  The chi-square
starter is the one already recorded by ``run_bxa_xspec.run_model`` before
nested sampling starts.  No sampler is run, so the full suite takes seconds.

Usage (inside the ``bxa_xspec`` image)::

    python /app/run/bic_scan.py \
        --input /app/input --output /app/output \
        --config /app/config/config.json --redshift 0.184

Writes ``bic_scan.csv`` and ``bic_scan.json``.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

# Inside the image both modules live in /app/run; in a checkout they are next
# to this file.
HERE = Path(__file__).resolve().parent
# In the image both modules live in /app/run.  In a checkout, run_xmm_xspec.py
# is one directory over in Tools/xmm_xspec.
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "xmm_xspec"))

import run_bxa_xspec as bx  # noqa: E402
import run_xmm_xspec as xx  # noqa: E402
from xspec import AllData  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=Path("/app/input"))
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("/app/config/config.json"))
    ap.add_argument("--redshift", type=float, default=0.184)
    ap.add_argument("--band", type=float, nargs=2, default=(2.0, 10.0))
    ap.add_argument("--models", default=None,
                    help="comma-separated subset of model names")
    args = ap.parse_args(argv)

    cfg = json.loads(args.config.read_text())
    cfg["band_keV"] = list(args.band)
    outdir = args.output
    outdir.mkdir(parents=True, exist_ok=True)

    products = xx.discover_products(args.input, cfg)
    prepared = xx.prepare_inputs(products, outdir / "prepared")
    bx.reset_xspec()
    bx.load_spectra(products, prepared, tuple(args.band))
    n_bins = int(sum(len(AllData(i).values) for i in range(1, 4)))

    wanted = [s.strip() for s in args.models.split(",")] if args.models else None
    specs = [s for s in cfg["models"] if not wanted or s["name"] in wanted]

    rows = []
    for spec in specs:
        try:
            mdl = bx.build_model(spec["expr"], spec, args.redshift, None)
            start = bx.quick_fit(mdl)
            k = sum(1 for p in spec["params"] if p.get("kind") != "fixed")
            chi2 = float(start["chi2"])
            params = {}
            for par in spec["params"]:
                try:
                    params[par["path"]] = float(bx._par(mdl, par["path"]).values[0])
                except Exception:
                    pass
            bic = chi2 + k * math.log(n_bins)
            aic = chi2 + 2.0 * k
            rows.append({
                "model": spec["name"],
                "family": spec.get("family", "pl"),
                "expr": spec["expr"],
                "chi2": chi2,
                "dof": int(start["dof"]),
                "k": k,
                "n_bins": n_bins,
                "chi2_dof": chi2 / max(int(start["dof"]), 1),
                "BIC": bic,
                "AIC": aic,
                "params": params,
                "status": "ok",
            })
            print(f"{spec['name']}: chi2/dof={chi2:.1f}/{start['dof']} "
                  f"k={k} BIC={bic:.1f} AIC={aic:.1f}", flush=True)
        except Exception as exc:  # noqa: BLE001
            rows.append({"model": spec["name"], "status": "failed",
                         "error": f"{type(exc).__name__}: {exc}"})
            print(f"{spec['name']}: FAILED {type(exc).__name__}: {exc}", flush=True)

    ok = [r for r in rows if r["status"] == "ok"]
    base = next((r for r in ok if r["model"] == "pl"), None)
    for r in ok:
        r["delta_BIC_vs_pl"] = r["BIC"] - base["BIC"] if base else None
        r["delta_AIC_vs_pl"] = r["AIC"] - base["AIC"] if base else None

    (outdir / "bic_scan.json").write_text(json.dumps({
        "band_keV": list(args.band),
        "redshift": args.redshift,
        "statistic": "chi2 (quick fit, constants frozen)",
        "n_bins": n_bins,
        "rows": rows,
    }, indent=2) + "\n")
    with (outdir / "bic_scan.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["model", "family", "chi2", "dof", "k", "n_bins", "chi2_dof",
                    "BIC", "AIC", "delta_BIC_vs_pl", "delta_AIC_vs_pl", "status"])
        for r in rows:
            w.writerow([r.get(k, "") for k in ("model", "family", "chi2", "dof", "k",
                                              "n_bins", "chi2_dof", "BIC", "AIC",
                                              "delta_BIC_vs_pl", "delta_AIC_vs_pl",
                                              "status")])
    print(f"wrote {outdir / 'bic_scan.csv'} ({len(ok)}/{len(rows)} models)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
