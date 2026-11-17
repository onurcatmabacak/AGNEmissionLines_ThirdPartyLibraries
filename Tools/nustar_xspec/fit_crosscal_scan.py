#!/usr/bin/env python
"""Profile joint fit of FPMA/FPMB with a free cross-calibration factor.

For each candidate FPMB/FPMA ratio ``c`` the FPMB source and background counts
are divided by ``c`` and both spectra are fitted jointly with one absorbed
cutoff power law (all physical parameters shared).  The scan returns the factor
that minimises the total C-statistic.

This is the method behind the c = 1.07 result in
``outputs/nustar_xspec/NGC1365_z_0.0035/``.  Run it inside the
``nustar_xspec`` image, with the joint spectra/ARFs mounted at ``--joint-dir``.
"""
import argparse
import json
import os

import numpy as np
from astropy.io import fits
from xspec import AllData, AllModels, Fit, Model, Xset


def scale_pha(src, dst, factor):
    """Copy a PHA and multiply COUNTS/STAT_ERR by ``factor``."""
    with fits.open(src) as h:
        hdul = fits.HDUList([h[0].copy(), h["SPECTRUM"].copy()])
    d = hdul["SPECTRUM"].data
    d["COUNTS"] = np.asarray(d["COUNTS"], float) * factor
    if "STAT_ERR" in d.columns.names:
        d["STAT_ERR"] = np.asarray(d["STAT_ERR"], float) * factor
    hdul.writeto(dst, overwrite=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--joint-dir", required=True)
    ap.add_argument("--a-src", default="A_src_clean.pha")
    ap.add_argument("--a-bkg", default="A_bkg_clean.pha")
    ap.add_argument("--b-src", default="B_src_clean.pha")
    ap.add_argument("--b-bkg", default="B_bkg_clean.pha")
    ap.add_argument("--a-rmf", required=True)
    ap.add_argument("--a-arf", required=True)
    ap.add_argument("--b-rmf", required=True)
    ap.add_argument("--b-arf", required=True)
    ap.add_argument("--c-min", type=float, default=0.80)
    ap.add_argument("--c-max", type=float, default=1.20)
    ap.add_argument("--c-step", type=float, default=0.02)
    ap.add_argument("--band", default="3.0 79.0")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    joint = os.path.abspath(args.joint_dir)
    scan = os.path.join(joint, "scan")
    os.makedirs(scan, exist_ok=True)
    a_src = os.path.join(joint, args.a_src)
    a_bkg = os.path.join(joint, args.a_bkg)
    b_src = os.path.join(joint, args.b_src)
    b_bkg = os.path.join(joint, args.b_bkg)
    b_src_scan = os.path.join(scan, "B_src_scan.pha")
    b_bkg_scan = os.path.join(scan, "B_bkg_scan.pha")
    lo, hi = (float(x) for x in args.band.split())

    Xset.abund = "wilm"
    Fit.statMethod = "cstat"
    Fit.nIterations = 500

    rows = []
    for c in np.round(np.arange(args.c_min, args.c_max + 1e-9, args.c_step), 4):
        scale_pha(b_src, b_src_scan, 1.0 / c)
        scale_pha(b_bkg, b_bkg_scan, 1.0 / c)
        AllData.clear()
        AllModels.clear()
        AllData(f"1:1 {a_src} 2:2 {b_src_scan}")
        s1 = AllData(1)
        s1.response = args.a_rmf
        s1.response.arf = args.a_arf
        s1.background = a_bkg
        s1.ignore(f"**-{lo}"); s1.ignore(f"{hi}-**")
        s2 = AllData(2)
        s2.response = args.b_rmf
        s2.response.arf = args.b_arf
        s2.background = b_bkg_scan
        s2.ignore(f"**-{lo}"); s2.ignore(f"{hi}-**")
        m = Model("constant*tbabs*cutoffpl", "m", 1)
        m.constant.factor.values = [1.0, 1.0]
        m.constant.factor.frozen = True
        m.TBabs.nH = 15.0
        m.cutoffpl.PhoIndex = 1.1
        m.cutoffpl.HighECut = 150.0
        m.cutoffpl.norm = 5e-3
        Fit.perform()
        rows.append({
            "c": float(c),
            "stat": float(Fit.statistic),
            "dof": int(Fit.dof),
            "nH": float(m.TBabs.nH.values[0]),
            "gamma": float(m.cutoffpl.PhoIndex.values[0]),
            "highECut": float(m.cutoffpl.HighECut.values[0]),
            "norm": float(m.cutoffpl.norm.values[0]),
        })
    best = min(rows, key=lambda r: r["stat"])
    payload = {"best": best, "rows": rows}
    with open(args.output, "w") as fh:
        json.dump(payload, fh, indent=2)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
