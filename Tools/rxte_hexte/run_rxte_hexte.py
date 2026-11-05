#!/usr/bin/env python3
"""RXTE/HEXTE 15-250 keV: the high-energy cutoff above the PCA band.

The PCA tools stop at 20 keV and the NuSTAR path needs the SDC CALDB.  HEXTE's
official HEASARC `stdprod` products are the third way: reduced spectra *and*
responses, 15-250 keV, no CALDB and no reduction, published next to the PCA files
in the same `stdprod` directory.

Two HEXTE clusters (A/B) are fitted simultaneously with their own backgrounds and
the official ARF/RMF.  The scientific target is the exponential cutoff: with
Tbabs*cutoffpl the fit constrains E_cut, and a model with no cutoff (E_cut frozen
at 1e3 keV) is compared through the C-statistic.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path


def log(msg: str) -> None:
    print(f"[rxte_hexte] {msg}", flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--source-key", default=None)
    args = ap.parse_args(argv)

    cfg = json.loads(args.config.read_text()) if args.config and args.config.exists() else {}
    emin, emax = (float(v) for v in cfg.get("band_keV", [15.0, 100.0]))
    outdir = args.output
    outdir.mkdir(parents=True, exist_ok=True)

    # PAL = cluster A (0), PAL = cluster B (1) in the stdprod naming.
    pairs = []
    for cl, tag in (("A", "pwa"), ("B", "pwb013")):
        idx = "0" if cl == "A" else "1"
        src = next(iter(sorted(args.input.glob(f"*_s{idx}.pha*"))), None)
        bkg = next(iter(sorted(args.input.glob(f"*_b{idx}.pha*"))), None)
        rmf = next(iter(sorted(args.input.glob(f"*{tag}.rmf*"))), None)
        arf = next(iter(sorted(args.input.glob(f"*{tag}.arf*"))), None)
        if all((src, bkg, rmf, arf)):
            pairs.append({"cluster": cl, "src": src, "bkg": bkg, "rmf": rmf, "arf": arf})
        else:
            log(f"cluster {cl} incomplete: {[p.name if p else None for p in (src,bkg,rmf,arf)]}")
    if not pairs:
        raise SystemExit(f"no complete HEXTE cluster under {args.input}")

    # Normalise the PHA headers before XSPEC sees them: the stdprod files carry
    # RESPFILE="none" and CHANTYPE="PHA", which makes PyXspec prompt for a
    # response on read and then fail.  Write patched copies with CHANTYPE=PI and
    # the real RESPFILE/ANCRFILE/BACKFILE, which is what XSPEC expects.
    from astropy.io import fits
    work = outdir / "input"
    work.mkdir(exist_ok=True)
    for p in pairs:
        for key in ("src", "bkg"):
            src = p[key]
            dst = work / src.name
            with fits.open(src) as hdul:
                hdul[1].header["CHANTYPE"] = "PI"
                if key == "src":
                    # absolute paths: XSPEC resolves the keywords relative to its
                    # own CWD, not the spectrum's directory
                    hdul[1].header["RESPFILE"] = str((work / p["rmf"].name).resolve())
                    hdul[1].header["ANCRFILE"] = str((work / p["arf"].name).resolve())
                    hdul[1].header["BACKFILE"] = str((work / p["bkg"].name).resolve())
                hdul.writeto(dst, overwrite=True)
            p[key] = dst
        for key in ("rmf", "arf"):
            dst = work / p[key].name
            if not dst.exists():
                dst.write_bytes(p[key].read_bytes())
            p[key] = dst

    import xspec
    xspec.Xset.chatter = 0
    # HEXTE PHA files carry RESPFILE="none", so XSPEC otherwise prompts for a
    # response on read and dies on the empty answer.
    try:
        xspec.Xset.query = "no"
    except Exception:
        pass
    xspec.Fit.statMethod = "cstat"
    for p in pairs:
        s = xspec.Spectrum(str(p["src"]))
        s.response = str(p["rmf"])
        s.response.arf = str(p["arf"])
        s.background = str(p["bkg"])
        s.ignore(f"**-{emin}")
        s.ignore(f"{emax}-**")
        log(f"cluster {p['cluster']}: {len(s.values)} bins in {emin}-{emax} keV")

    def fit(cut_free: bool):
        m = xspec.Model("tbabs*cutoffpl+zgauss")
        m.TBabs.nH = 0.01
        m.TBabs.nH.frozen = False
        m.cutoffpl.PhoIndex = 1.8
        m.cutoffpl.HighECut = 100.0
        m.cutoffpl.HighECut.frozen = not cut_free
        m.cutoffpl.norm = 1e-2
        m.zgauss.LineE = 6.4
        m.zgauss.Sigma = 0.3
        m.zgauss.norm = 1e-4
        xspec.Fit.perform()
        # Read every parameter out NOW: creating the next model invalidates this
        # Python Model object ("reference no longer corresponds to ...").
        vals = {
            "E_cut_keV": float(m.cutoffpl.HighECut.values[0]),
            "phoindex": float(m.cutoffpl.PhoIndex.values[0]),
            "nh": float(m.TBabs.nH.values[0]),
        }
        return float(xspec.Fit.statistic), int(xspec.Fit.dof), vals

    stat_cut, dof_cut, p_cut = fit(True)
    log(f"cutoff free: C-stat {stat_cut:.1f}/{dof_cut} = {stat_cut/dof_cut:.2f}, "
        f"E_cut = {p_cut['E_cut_keV']:.1f} keV, Gamma = {p_cut['phoindex']:.2f}")
    stat_nocut, dof_nocut, p_nocut = fit(False)
    log(f"cutoff frozen at 1e3 keV: C-stat {stat_nocut:.1f}/{dof_nocut} = {stat_nocut/dof_nocut:.2f}")
    dstat = stat_nocut - stat_cut
    log(f"Delta C-stat for the cutoff = {dstat:+.1f}")

    rows = [
        {"model": "tbabs*cutoffpl+zgauss (E_cut free)", "statistic": stat_cut,
         "dof": dof_cut, "cstat_dof": stat_cut / max(dof_cut, 1),
         "E_cut_keV": p_cut["E_cut_keV"], "phoindex": p_cut["phoindex"]},
        {"model": "tbabs*cutoffpl+zgauss (E_cut=1e3)", "statistic": stat_nocut,
         "dof": dof_nocut, "cstat_dof": stat_nocut / max(dof_nocut, 1),
         "E_cut_keV": 1000.0, "phoindex": p_nocut["phoindex"]},
    ]
    with open(outdir / "hexte_models.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    (outdir / "run.json").write_text(json.dumps({
        "tool": "rxte_hexte", "status": "ok",
        "source_key": args.source_key or args.input.name,
        "clusters": [p["cluster"] for p in pairs],
        "band_keV": [emin, emax],
        "E_cut_keV": p_cut["E_cut_keV"],
        "phoindex": p_cut["phoindex"],
        "delta_cstat_cutoff": float(dstat),
        "cstat_dof": stat_cut / max(dof_cut, 1),
    }, indent=2) + "\n")
    log(f"wrote {outdir/'hexte_models.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
