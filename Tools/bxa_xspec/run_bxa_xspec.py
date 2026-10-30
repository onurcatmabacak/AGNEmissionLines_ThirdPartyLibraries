#!/usr/bin/env python3
"""BXA (Bayesian X-ray Analysis) evidence comparison for XMM-Newton EPIC data.

Same data and band as ``xmm_xspec`` (official PPS spectra, PN+MOS1+MOS2,
0.5-10 keV), but the fit is Bayesian:

* priors are built with BXA's prior transforms (``bxa.prior``) over the
  physically meaningful ranges;
* the evidence ``ln Z`` is computed with nested sampling (UltraNest, the engine
  BXA wraps), so models are compared by Bayes factors rather than Delta chi2;
* the Cash/C-stat statistic is used, as required for Poisson data.

The model suite is configurable (``configs/bxa_xspec/default/config.json``):
continuum null hypothesis, narrow and broad Fe K-alpha, an ionized (warm)
absorber, a partial-covering absorber and a Compton-thick cut-off power law —
the last three are the torus/absorption proxies that XSPEC provides without
external table models (MYTorus/RELUXILL tables are licence/download gated and
are reported as unavailable rather than silently skipped).

Outputs: run.json (evidence table, posterior medians, priors), bxa_evidence.csv,
bxa_posteriors.csv, bxa_evidence.png, config.effective.json, xspec.log.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

# The image ships the xmm_xspec adapter; reuse its product discovery and
# spectrum preparation so both tools see byte-identical inputs.
sys.path.insert(0, "/app/run")
import run_xmm_xspec as xx  # noqa: E402

from xspec import AllData, AllModels, Fit, Model, Xset  # noqa: E402

INSTRUMENTS = ("PN", "MOS1", "MOS2")


def log(msg: str) -> None:
    print(f"[bxa] {msg}", flush=True)


def reset_xspec() -> None:
    AllData.clear()
    AllModels.clear()
    Xset.chatter = 0
    Xset.logChatter = 0


def load_spectra(products: dict, prepared: dict, band: tuple[float, float]) -> None:
    spec_arg = " ".join(
        f"{i}:{i} {prepared[inst]['source']}" for i, inst in enumerate(INSTRUMENTS, start=1)
    )
    AllData(spec_arg)
    for i, inst in enumerate(INSTRUMENTS, start=1):
        d = AllData(i)
        d.response = str(products[inst]["rmf"])
        d.response.arf = str(products[inst]["arf"])
        d.background = str(prepared[inst]["background"])
    lo, hi = band
    AllData.ignore("bad")
    AllData.ignore(f"0.0-{lo} {hi}-**")


def _par(model, path: str):
    comp, _, name = path.partition(".")
    holder = getattr(model, comp) if comp else model
    return getattr(holder, name)


def build_model(expr: str, spec: dict, redshift: float, seed_vals: dict | None = None):
    """Create the XSPEC model and set initial values (chi-square starter)."""
    Model(expr, "bxa")
    mdl = AllModels(1, "bxa")
    Fit.statMethod = "chi"
    Fit.nIterations = 500
    Fit.query = "no"
    for p in spec["params"]:
        par = _par(mdl, p["path"])
        idx = par._Parameter__index
        if p.get("kind") == "fixed":
            if p["path"].lower().endswith("redshift"):
                value = redshift
            elif "init" in p:
                value = float(p["init"])
            else:
                value = float(par.values[0])
            AllModels.setPars(mdl, {idx: float(value)})
            par.frozen = True
            continue
        init = float(p.get("init", 1.0))
        if p["path"].endswith("LineE") and seed_vals is not None:
            init = float(seed_vals.get("line_energy", init))
        if p["path"].endswith("norm") and seed_vals is not None:
            init = float(seed_vals.get(p["path"], init))
        AllModels.setPars(mdl, {idx: float(init)})
        par.frozen = False
    return mdl


def quick_fit(mdl) -> dict:
    """Least-squares starter: fixes the cross-calibration constants."""
    Fit.perform()
    out = {"chi2": float(Fit.statistic), "dof": int(Fit.dof)}
    # constant factors are per spectrum; freeze them at the fitted values so
    # every model in the suite is compared under one calibration.
    try:
        for i in range(1, len(INSTRUMENTS) + 1):
            g = AllModels(i, "bxa")
            g.constant.factor.frozen = True
    except Exception:
        pass
    return out


def make_transformations(mdl, spec: dict, redshift: float, fitted: dict):
    """Turn the config parameter list into BXA prior transformations."""
    from bxa.xspec.solver import create_prior_function  # noqa: F401  (API check)

    transformations = []
    for p in spec["params"]:
        if p.get("kind") == "fixed":
            continue
        par = _par(mdl, p["path"])
        idx = getattr(par, "_Parameter__index")
        kind = p["kind"]
        if kind == "log":
            lo, hi = (float(x) for x in p["range"])
            if "norm" in p["path"] and p.get("centre_on_fit", True):
                centre = float(getattr(par, "values")[0])
                if centre > 0 and not (lo <= centre <= hi):
                    lo, hi = centre / 100.0, centre * 100.0
            lo, hi = max(lo, 1e-30), max(hi, lo * 1.0001)

            def transform(x, lo=lo, hi=hi):
                return 10.0 ** (np.log10(lo) + x * (np.log10(hi) - np.log10(lo)))

        elif kind == "uniform":
            if "range_factor" in p:
                base = float(p.get("init", 6.4)) / (1.0 + redshift) if p["path"].endswith("LineE") else float(p.get("init"))
                f0, f1 = (float(x) for x in p["range_factor"])
                lo, hi = base * f0, base * f1
            else:
                lo, hi = (float(x) for x in p["range"])

            def transform(x, lo=lo, hi=hi):
                return lo + x * (hi - lo)

        else:
            raise ValueError(f"unknown prior kind {kind} for {p['path']}")

        transformations.append(
            dict(
                model=mdl,
                index=idx,
                name=p["path"],
                transform=transform,
                aftertransform=lambda x: x,
                prior_kind=kind,
                prior_lo=float(lo),
                prior_hi=float(hi),
            )
        )
    return transformations


def run_model(product_dir: Path, products: dict, prepared: dict, cfg: dict,
              spec: dict, redshift: float, seed_vals: dict) -> dict:
    lo, hi = cfg["band_keV"]
    reset_xspec()
    load_spectra(products, prepared, (lo, hi))
    t0 = time.time()
    mdl = build_model(spec["expr"], spec, redshift, seed_vals)
    start = quick_fit(mdl)
    fitted = {p["path"]: float(_par(mdl, p["path"]).values[0]) for p in spec["params"]}
    log(f"{spec['name']}: chi2/dof = {start['chi2']:.1f}/{start['dof']}")

    transformations = make_transformations(mdl, spec, redshift, fitted)
    Fit.statMethod = cfg.get("statistic", "cstat")
    Fit.query = "no"

    from bxa.xspec.solver import BXASolver

    chains = product_dir / "chains" / spec["name"]
    chains.mkdir(parents=True, exist_ok=True)
    solver = BXASolver(transformations, outputfiles_basename=str(chains))
    solver.run(
        sampler_kwargs={"resume": "overwrite"},
        n_live_points=int(cfg["n_live_points"]),
        evidence_tolerance=float(cfg["evidence_tolerance"]),
        # "auto" switches UltraNest to slice sampling after a 40k-call warm-up;
        # "safe" (the default) is what stalled at ~2 % efficiency on the
        # partial-covering model.
        speed=str(cfg.get("speed", "safe")),
    )
    res = solver.results
    points = np.asarray(res["weighted_samples"]["points"], dtype=float)
    weights = np.asarray(res["weighted_samples"]["weights"], dtype=float)
    order = np.argsort(points[:, 0]) if len(points) else np.array([], dtype=int)

    post = {}
    for j, t in enumerate(transformations):
        vals = points[:, j]
        if not len(vals):
            continue
        q16, q50, q84 = np.percentile(vals, [16, 50, 84])
        post[t["name"]] = {
            "median": float(q50),
            "p16": float(q16),
            "p84": float(q84),
            "prior_kind": t["prior_kind"],
            "prior_lo": t["prior_lo"],
            "prior_hi": t["prior_hi"],
        }
    _ = order
    return {
        "name": spec["name"],
        "family": spec.get("family", "pl"),
        "description": spec.get("description", ""),
        "model": spec["expr"],
        "free_parameters": [t["name"] for t in transformations],
        "log_z": float(res["logz"]),
        "log_z_err": float(res["logzerr"]),
        "n_live": int(res.get("nlive", cfg["n_live_points"])),
        "n_calls": int(res.get("ncall", 0)),
        "chi2_start": start["chi2"],
        "dof": start["dof"],
        "posterior": post,
        "runtime_sec": time.time() - t0,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=Path("/app/input"))
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("/app/config/config.json"))
    ap.add_argument("--z", type=float, default=None)
    ap.add_argument("--source-key", default=None)
    ap.add_argument("--models", default=None,
                    help="comma-separated subset of model names")
    ap.add_argument("--n-live", type=int, default=None)
    ap.add_argument("--dlogz", type=float, default=None)
    args = ap.parse_args(argv)

    cfg = json.loads(args.config.read_text())
    if args.n_live:
        cfg["n_live_points"] = args.n_live
    if args.dlogz is not None:
        cfg["evidence_tolerance"] = args.dlogz
    outdir = args.output
    outdir.mkdir(parents=True, exist_ok=True)

    products = xx.discover_products(args.input, cfg)
    prepared = xx.prepare_inputs(products, outdir / "prepared")
    redshift = float(args.z if args.z is not None else cfg["redshift"])
    log(f"redshift {redshift}  band {cfg['band_keV']} keV  statistic {cfg.get('statistic')}")

    wanted = [s.strip() for s in args.models.split(",")] if args.models else None
    specs = [s for s in cfg["models"] if not wanted or s["name"] in wanted]

    # Seed the line energy and normalisations from the production xmm_xspec
    # solution when it is available (same binning, so it is a good starter).
    seed_vals = {}
    ref = os.environ.get("BXA_SEED_JSON")
    if ref and Path(ref).exists():
        try:
            d = json.loads(Path(ref).read_text())
            seed_vals = {"line_energy": 6.4 / (1.0 + redshift)}
            seed_vals["zpowerlw.norm"] = float(d.get("line", {}).get("pl_norm", 1e-3))
        except Exception:
            seed_vals = {}

    results = []
    for spec in specs:
        try:
            results.append(run_model(outdir, products, prepared, cfg, spec, redshift, seed_vals))
        except Exception as exc:  # noqa: BLE001 - one model must not kill the run
            log(f"{spec['name']} FAILED: {type(exc).__name__}: {exc}")
            results.append({"name": spec["name"], "model": spec["expr"],
                            "status": "failed", "error": f"{type(exc).__name__}: {exc}"})

    ok = [r for r in results if "log_z" in r]
    base = next((r for r in ok if r["name"] == "pl"), ok[0] if ok else None)
    # Bayes factors are only meaningful inside one continuum family: a broad
    # line in a power-law-only model can absorb continuum curvature.
    family_base = {}
    for name in ("pl", "plbb", "absorbed"):
        fam = [r for r in ok if r.get("family") == name]
        family_base[name] = min(fam, key=lambda r: len(r["free_parameters"]))["name"] if fam else None
    base_by_name = {r["name"]: r for r in ok}
    for r in ok:
        r["delta_log_z_vs_pl"] = r["log_z"] - base["log_z"] if base else None
        r["bayes_factor_vs_pl"] = (
            float(np.exp(r["delta_log_z_vs_pl"])) if r["delta_log_z_vs_pl"] is not None else None
        )
        fb = base_by_name.get(family_base.get(r.get("family")))
        r["family_base"] = family_base.get(r.get("family"))
        r["delta_log_z_vs_family"] = (r["log_z"] - fb["log_z"]) if fb else None

    # Evidence table + posterior table
    import csv

    with (outdir / "bxa_evidence.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["model", "family", "description", "log_z", "log_z_err", "delta_log_z_vs_pl",
                    "delta_log_z_vs_family", "family_base", "bayes_factor_vs_pl", "n_free",
                    "n_live", "n_calls", "runtime_sec", "status"])
        for r in results:
            if "log_z" in r:
                w.writerow([r["name"], r.get("family", ""), r["description"],
                            f"{r['log_z']:.4f}", f"{r['log_z_err']:.4f}",
                            f"{r['delta_log_z_vs_pl']:.4f}",
                            "" if r.get("delta_log_z_vs_family") is None else f"{r['delta_log_z_vs_family']:.4f}",
                            r.get("family_base") or "", f"{r['bayes_factor_vs_pl']:.4g}",
                            len(r["free_parameters"]), r["n_live"], r["n_calls"],
                            f"{r['runtime_sec']:.1f}", "ok"])
            else:
                w.writerow([r["name"], r.get("family", ""), r.get("model", ""), "", "", "", "",
                            "", "", "", "", "", "", "failed"])

    post_rows = []
    for r in ok:
        for par, v in r["posterior"].items():
            post_rows.append([r["name"], par, f"{v['median']:.6g}", f"{v['p16']:.6g}",
                              f"{v['p84']:.6g}", v["prior_kind"], f"{v['prior_lo']:.6g}",
                              f"{v['prior_hi']:.6g}"])
    with (outdir / "bxa_posteriors.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["model", "parameter", "median", "p16", "p84", "prior_kind", "prior_lo", "prior_hi"])
        w.writerows(post_rows)

    # Evidence bar chart
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        if ok:
            names = [r["name"] for r in ok]
            dz = [r["delta_log_z_vs_pl"] for r in ok]
            fig, ax = plt.subplots(figsize=(7, 0.6 * len(names) + 1.4))
            ax.barh(names, dz, color="#4477aa")
            ax.axvline(0, color="k", lw=0.8)
            ax.set_xlabel(r"$\Delta \ln Z$ vs absorbed power law")
            ax.set_title("BXA model comparison (nested sampling)")
            for i, v in enumerate(dz):
                ax.text(v, i, f" {v:+.1f}", va="center")
            ax.invert_yaxis()
            fig.tight_layout()
            fig.savefig(outdir / "bxa_evidence.png", dpi=140)
            fig.savefig(outdir / "bxa_evidence.pdf")
            plt.close(fig)
    except Exception as exc:  # noqa: BLE001
        log(f"plot skipped: {exc}")

    run = {
        "tool": "bxa_xspec",
        "status": "ok" if ok else "failed",
        "source_key": args.source_key or Path(args.input).name,
        "redshift": redshift,
        "band_keV": cfg["band_keV"],
        "statistic": cfg.get("statistic", "cstat"),
        "engine": {"nested_sampling": "ultranest", "bxa": xx_versions()},
        "n_live_points": cfg["n_live_points"],
        "evidence_tolerance": cfg["evidence_tolerance"],
        "models": results,
        "baseline": base["name"] if base else None,
        "headline": {
            "best_model": max(ok, key=lambda r: r["log_z"])["name"] if ok else None,
            "best_log_z": max(ok, key=lambda r: r["log_z"])["log_z"] if ok else None,
        },
        "notes": [
            "Bayes factors use Jeffreys' scale: Delta ln Z > 2.5 substantial, > 5 strong, > 11 decisive.",
            "MYTorus/UXCLUMPY/RELXILL table models are not bundled: they need external FITS tables and, for "
            "UXCLUMPY/XARS, licence review.  The absorption family here is the built-in XSPEC set "
            "(zxipcf warm absorber, pcfabs partial covering, cabs Compton-thick) so the comparison is reproducible offline.",
            "Constants (cross-calibration) are fixed at the chi-square best fit; the band and spectra are identical to xmm_xspec.",
        ],
    }
    (outdir / "run.json").write_text(json.dumps(run, indent=2) + "\n")
    (outdir / "config.effective.json").write_text(json.dumps(cfg, indent=2) + "\n")
    log(f"wrote {outdir} ({len(ok)}/{len(results)} models)")
    return 0 if ok else 1


def xx_versions() -> dict:
    out = {}
    try:
        import bxa
        out["bxa"] = getattr(bxa, "__version__", "unknown")
    except Exception:
        pass
    try:
        import ultranest
        out["ultranest"] = getattr(ultranest, "__version__", "unknown")
    except Exception:
        pass
    try:
        out["xspec"] = xx.xspec_version()
    except Exception:
        pass
    return out


if __name__ == "__main__":
    raise SystemExit(main())
