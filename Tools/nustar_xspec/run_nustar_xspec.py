#!/usr/bin/env python3
"""NuSTAR 3-79 keV spectral fitting: Compton-thick diagnostics above 20 keV.

The XMM EPIC and RXTE PCA tools stop at 10-20 keV, which is exactly where the
Compton-thick signature lives (the >10 keV turnover and the reflection hump).
NuSTAR covers 3-79 keV.

Reduction: public Level-2 cleaned event files are used, so `nupipeline` is
skipped and only `nuproducts` runs, producing the ARF/RMF/spectrum per focal
plane.  Fitting is PyXspec with the C-statistic.

Models compared, because the point of going above 20 keV is to separate them:

``tbabs*cutoffpl``            - absorbed power law with an exponential cutoff
``tbabs*(cutoffpl+pexrav)``   - plus a Compton reflection component

and an Fe K-alpha ``zgauss`` in both cases.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np


def log(msg: str) -> None:
    print(f"[nustar_xspec] {msg}", flush=True)


def headas_env() -> dict:
    """Environment for the HEASoft tasks, with a usable LHEAPERL.

    headas-init.sh sets LHEAPERL to the *build-time* perl of the conda recipe
    (/opt/conda/conda-bld/.../perl), which does not exist in the runtime image,
    and nuproducts then dies with "LHEAPERL variable does not point to a usable
    perl".  Override it with a perl that is actually present.
    """
    import shutil

    env = dict(os.environ)
    headas = env.get("HEADAS", "")
    init = Path(headas) / "headas-init.sh"
    if init.exists():
        out = subprocess.run(["bash", "-lc", f'source "{init}" && env'],
                             capture_output=True, text=True)
        for line in out.stdout.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                env[k] = v
    # Prefer the conda perl: Debian's minimal /usr/bin/perl lacks the core
    # modules nuproducts needs (it dies on Math::Trig).
    candidates = ["/opt/conda/bin/perl", shutil.which("perl"), "/usr/bin/perl"]
    perl = next((c for c in candidates if c and Path(c).exists()), None)
    if perl:
        env["LHEAPERL"] = perl
    return env


def reduce_events(indir: Path, outdir: Path, env: dict, cfg_region=None) -> list[dict]:
    """Run nuproducts for each focal plane; return the product triples.

    The input directory is mounted read-only, so the event files are decompressed
    into a scratch copy here before nuproducts runs.
    """
    # Stage *everything*: nuproducts also needs the detector reference (_det1),
    # the bad-pixel map (_bp) and the alignment (_oa) files, not just the events.
    srcs = [p for p in sorted(indir.iterdir()) if p.is_file()]
    if not any("_cl.evt" in p.name for p in srcs):
        raise SystemExit(f"no Level-2 event files under {indir}")
    work = outdir / "events"
    work.mkdir(parents=True, exist_ok=True)
    for src in srcs:
        if src.name.endswith(".gz"):
            dst = work / src.name[:-3]
            if not dst.exists():
                subprocess.run(["gunzip", "-cf", str(src)], stdout=open(dst, "wb"), check=True)
        else:
            dst = work / src.name
            if not dst.exists():
                dst.write_bytes(src.read_bytes())
    indir = work
    stems = sorted({p.name.replace("_cl.evt", "") for p in work.glob("nu*_cl.evt")})
    if not stems:
        raise SystemExit(f"no Level-2 event files under {work}")
    att = next(iter(sorted(work.glob("nu*_att.fits"))), None)
    src_reg = None
    ra, dec = cfg_region[:2] if cfg_region else (None, None)
    if ra is not None and dec is not None:
        src_reg = work / "src.reg"
        src_reg.write_text(f'# Region file format: DS9\nfk5\ncircle({ra},{dec},{cfg_region[2]})\n')
        log(f"source region: RA={ra} Dec={dec} radius={cfg_region[2]}")
    products = []
    for stem in stems:
        # nuproducts appends the focal-plane letter and segment itself, so the
        # stem must stop before them: nu60002046001A01 -> nu60002046001
        fp = "A"
        if len(stem) > 3 and stem[-2:].isdigit() and stem[-3] in "AB":
            fp, base = stem[-3], stem[:-3]
        else:
            base = stem
        # nuproducts concatenates outdir with file names, so both paths need a
        # trailing slash or it tries to mkdir an empty name.
        cmd = ["nuproducts", f"indir={indir}/", f"outdir={outdir}/",
               f"instrument={'FPMA' if fp == 'A' else 'FPMB'}",
               f"steminputs={base}", "clobber=YES",
               "extended=NO", "bkgextract=NO"]
        if att is not None:
            cmd.append(f"attfile={att}")
        # The SOC mast-aspect file is not in this observation's auxil/ or
        # event_cl/ directory; NONE is accepted and the attitude file is used.
        mast = next(iter(sorted(work.glob("*mast*"))), None)
        cmd.append(f"mastaspectfile={mast if mast else 'NONE'}")
        # Without a source region nuproducts assumes RA=Dec=0 and fails with
        # "Sky X coordinate out of range".
        if src_reg is not None:
            cmd.append(f"srcregionfile={src_reg}")
        log(" ".join(cmd))
        # nuproducts creates "<pid>_tmp_nuproducts" in the *current* directory and
        # the default image CWD is not writable for the calling uid.
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=str(work))
        if res.returncode != 0:
            log(f"nuproducts failed ({res.returncode}); tail:")
            for line in (res.stderr or res.stdout).splitlines()[-8:]:
                log("  " + line)
            continue
        pha = sorted(outdir.glob(f"nu{base[2:]}*{stem[-1]}*01.pha")) or sorted(outdir.glob("*.pha"))
        rmf = sorted(outdir.glob("*.rmf"))
        arf = sorted(outdir.glob("*.arf"))
        if pha and rmf and arf:
            products.append({"stem": stem, "pha": str(pha[0]), "rmf": str(rmf[-1]),
                             "arf": str(arf[-1]),
                             "instrument": "FPMA" if fp == "A" else "FPMB"})
    return products


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--source-key", default=None)
    ap.add_argument("--reduce-only", action="store_true")
    args = ap.parse_args(argv)

    cfg = json.loads(args.config.read_text()) if args.config and args.config.exists() else {}
    outdir = args.output
    outdir.mkdir(parents=True, exist_ok=True)
    reddir = outdir / "nuproducts"
    reddir.mkdir(exist_ok=True)

    env = headas_env()
    log(f"HEADAS={env.get('HEADAS')} CALDB={env.get('CALDB')}")
    region = cfg.get("source_region")
    region = (region[0], region[1], region[2]) if region else None
    products = reduce_events(args.input, reddir, env, cfg_region=region)
    log(f"products: {[p['instrument'] for p in products]}")
    if args.reduce_only or not products:
        return 0 if products else 1

    import xspec
    xspec.Xset.chatter = 0
    xspec.Fit.statMethod = "cstat"

    spec_ids = []
    for prod in products:
        s = xspec.Spectrum(prod["pha"])
        s.response = prod["rmf"]
        s.response.arf = prod["arf"]
        s.ignore("**-3.0")
        s.ignore("79.0-**")
        spec_ids.append(s)
        log(f"{prod['instrument']}: {len(s.values)} bins, exposure "
            f"{prod.get('exposure', 'n/a')}")

    e_min, e_max = (float(v) for v in cfg.get("line_band_keV", [5.4, 7.2]))
    results = {}

    def fit_model(expr: str, tbabs_nh: float, frozen_nh: bool):
        m = xspec.Model(expr)
        try:
            m.TBabs.nH = tbabs_nh
            m.TBabs.nH.frozen = frozen_nh
        except Exception:
            pass
        for comp in ("cutoffpl",):
            try:
                getattr(m, comp).PhoIndex = 1.8
                getattr(m, comp).HighECut = 100.0
                getattr(m, comp).norm = 1e-3
            except Exception:
                pass
        gname = next((n for n in m.componentNames if n.startswith("zgauss")), None)
        if gname:
            c = getattr(m, gname)
            c.LineE = float(cfg.get("line_energy_keV", 6.4))
            c.Sigma = 0.05
            c.norm = 1e-5
        xspec.Fit.perform()
        stat, dof = float(xspec.Fit.statistic), int(xspec.Fit.dof)
        params = {}
        for name in m.componentNames:
            comp = getattr(m, name)
            for par in comp.parameterNames:
                p = getattr(comp, par)
                params[f"{name}.{par}"] = {"value": float(p.values[0]),
                                            "error": float(p.sigma) if p.sigma == p.sigma else None,
                                            "frozen": bool(p.frozen)}
        return {"statistic": stat, "dof": dof, "cstat_dof": stat / max(dof, 1),
                "params": params}

    nh0 = float(cfg.get("nH_1e22", 0.1))
    base_expr = "tbabs*cutoffpl"
    refl_expr = "tbabs*(cutoffpl+pexrav)"
    rows = []

    fit_pl = fit_model(base_expr + "+zgauss", nh0, False)
    log(f"tbabs*cutoffpl+zgauss: C-stat {fit_pl['statistic']:.1f}/{fit_pl['dof']} "
        f"({fit_pl['cstat_dof']:.2f})")
    rows.append({"model": "tbabs*cutoffpl+zgauss", **{k: fit_pl[k] for k in ("statistic", "dof", "cstat_dof")}})

    try:
        fit_refl = fit_model(refl_expr + "+zgauss", nh0, False)
        log(f"tbabs*(cutoffpl+pexrav)+zgauss: C-stat {fit_refl['statistic']:.1f}/"
            f"{fit_refl['dof']} ({fit_refl['cstat_dof']:.2f})")
        rows.append({"model": "tbabs*(cutoffpl+pexrav)+zgauss",
                     **{k: fit_refl[k] for k in ("statistic", "dof", "cstat_dof")}})
        delta = fit_pl["statistic"] - fit_refl["statistic"]
        log(f"Delta C-stat (no reflection - reflection) = {delta:+.1f}")
    except Exception as exc:
        log(f"reflection model failed: {exc}")
        fit_refl, delta = None, float("nan")

    # Fe K-alpha line significance: refit the best continuum without the line
    try:
        best_expr = refl_expr if fit_refl and fit_refl["statistic"] < fit_pl["statistic"] else base_expr
        best = fit_refl if best_expr == refl_expr else fit_pl
        m_noline = xspec.Model(best_expr)
        m_noline.TBabs.nH = best["params"].get("TBabs.nH", {}).get("value", nh0)
        for name, val in best["params"].items():
            comp, _, par = name.partition(".")
            if comp in m_noline.componentNames:
                try:
                    getattr(getattr(m_noline, comp), par).values = val["value"]
                except Exception:
                    pass
        xspec.Fit.perform()
        stat_noline = float(xspec.Fit.statistic)
        dchi2 = best["statistic"] - stat_noline
        sigma = float(np.sqrt(max(dchi2, 0.0)))
        log(f"Fe K-alpha: DeltaC-stat = {dchi2:.2f} (~{sigma:.1f} sigma)")
    except Exception as exc:
        log(f"line significance failed: {exc}")
        dchi2, sigma = float("nan"), float("nan")

    with open(outdir / "nustar_models.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["model", "statistic", "dof", "cstat_dof"])
        w.writeheader()
        w.writerows(rows)

    (outdir / "run.json").write_text(json.dumps({
        "tool": "nustar_xspec",
        "status": "ok",
        "source_key": args.source_key or args.input.name,
        "products": products,
        "band_keV": [3.0, 79.0],
        "line_band_keV": [e_min, e_max],
        "best_model": (fit_refl if fit_refl and fit_refl["statistic"] < fit_pl["statistic"] else fit_pl),
        "delta_cstat_reflection": float(delta),
        "fe_kalpha_delta_cstat": float(dchi2),
        "fe_kalpha_sigma": float(sigma),
    }, indent=2, default=str) + "\n")
    log(f"wrote {outdir/'nustar_models.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
