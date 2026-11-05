#!/usr/bin/env python3
"""Self-test for the IR slice: SDSS DR18 routing/fitting + synthetic IR recovery.

Run:  .venv/bin/python -m pipeline_ir.selftest
Exit code 0 = all checks passed.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

from .spectrum import read_spectrum, zline_table
from .router import route
from .fit import fit_group
from .synthetic import make_spectrum

ROOT = Path(__file__).resolve().parent.parent
SDSS = [
    ROOT / "input/spec-00000-59345-04492075003.fits",
    ROOT / "input/spec-00000-59345-04545183216.fits",
    ROOT / "input/spec-00000-59345-04570493016.fits",
]
CHECKS = []


def check(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + ("  " + detail if detail else ""))


def fit_object(path):
    spec = read_spectrum(path)
    rt = route(spec)
    rows = []
    for key, group in rt.groups.items():
        rr, chi = fit_group(spec, group, spec.z)
        rows.extend(rr)
    return spec, rt, rows


def total(rows, line):
    return float(np.nansum([r.flux for r in rows if r.line == line and r.detected]))


def test_sdss_router():
    print("\n--- SDSS DR18: router ---")
    for p in SDSS:
        spec, rt, _ = fit_object(p)
        names = {c.line.name for c in rt.lines if c.covered}
        check(f"{p.name}: status ok", rt.status == "ok", f"z={spec.z:.4f} band={spec.band}")
        for need in ("Halpha6563", "Hbeta4861", "OIII5007", "NII6585"):
            check(f"{p.name}: {need} covered", need in names)


def test_sdss_fit():
    print("\n--- SDSS DR18: line fits vs SDSS ZLINE ---")
    spec, rt, rows = fit_object(SDSS[0])
    zl = zline_table(SDSS[0])
    ha = total(rows, "Halpha6563")
    hb = total(rows, "Hbeta4861")
    o3 = total(rows, "OIII5007")
    zha = zl.get("H_alpha", {}).get("area", np.nan)
    zhb = zl.get("H_beta", {}).get("area", np.nan)
    zo3 = zl.get("[O_III] 5007", {}).get("area", np.nan)
    check("Halpha detected", ha > 0, f"fit={ha:.1f} ZLINE={zha:.1f}")
    check("Hbeta detected", hb > 0, f"fit={hb:.1f} ZLINE={zhb:.1f}")
    check("OIII5007 detected", o3 > 0, f"fit={o3:.1f} ZLINE={zo3:.1f}")
    if np.isfinite(zha) and zha > 0:
        check("Halpha within 50% of ZLINE", abs(ha / zha - 1) < 0.5, f"ratio={ha/zha:.2f}")
    if np.isfinite(zhb) and zhb > 0:
        check("Hbeta within 50% of ZLINE", abs(hb / zhb - 1) < 0.5, f"ratio={hb/zhb:.2f}")
    if np.isfinite(zo3) and zo3 > 0:
        check("OIII5007 within 30% of ZLINE", abs(o3 / zo3 - 1) < 0.3, f"ratio={o3/zo3:.2f}")


def test_synthetic():
    print("\n--- synthetic NIR/MIR/FIR recovery ---")
    cases = {
        "nir": (1.0, {"Pabeta12822": (500.0, 1200.0), "Paalpha18756": (800.0, 1200.0),
                      "Brgamma21661": (300.0, 1200.0)}, 50),
        "mir": (0.1, {"NeII12814": (1000.0, 500.0), "NeIII15555": (500.0, 500.0),
                      "SIII18713": (300.0, 500.0), "OIV25890": (200.0, 500.0)}, 50),
        "fir": (0.5, {"OIII88356": (2000.0, 300.0), "CII157741": (4000.0, 300.0),
                      "OI63184": (1000.0, 300.0)}, 50),
    }
    for band, (z, lines, snr) in cases.items():
        spec = make_spectrum(z, band, lines, snr=snr, R=2000, seed=2)
        rt = route(spec)
        check(f"{band}: router status ok", rt.status == "ok", f"groups={len(rt.groups)}")
        found = {}
        for key, group in rt.groups.items():
            rr, chi = fit_group(spec, group, spec.z)
            for r in rr:
                if r.line in lines and r.detected:
                    found.setdefault(r.line, r)
        for name, (truth, fwhm) in lines.items():
            r = found.get(name)
            ok = r is not None and abs(r.flux / truth - 1) < 0.15 and abs(r.fwhm_kms / fwhm - 1) < 0.25
            check(f"{band}: {name} recovered", ok,
                  f"flux={r.flux:.1f}/{truth} fwhm={r.fwhm_kms:.0f}/{fwhm}" if r else "not detected")


def test_zgt05():
    print("\n--- z>0.5 SDSS DR18 dataset ---")
    d = ROOT / "input_zgt05"
    files = sorted(d.glob("*.fits")) if d.is_dir() else []
    if not files:
        check("z>0.5 dataset present", False, "run the fetch commands in input_zgt05/README.md")
        return
    check("z>0.5 dataset present", len(files) >= 5, f"{len(files)} spectra")
    results = {}
    for p in files:
        spec, rt, rows = fit_object(p)
        check(f"{p.name}: z>0.5", spec.z > 0.5, f"z={spec.z:.4f}")
        check(f"{p.name}: router ok", rt.status == "ok", f"suites={rt.suites}")
        names = {c.line.name for c in rt.lines if c.covered}
        check(f"{p.name}: Halpha not covered (z>0.5)", "Halpha6563" not in names,
              f"wave_max={spec.wave_max:.3f} um")
        results[round(spec.z, 3)] = (spec, rt, rows, zline_table(p))
    # object-specific detections (z ~ 0.65, 0.99, 1.83)
    def has(rows, line):
        return any(r.line == line and r.detected for r in rows)
    zs = sorted(results)
    for z in zs:
        spec, rt, rows, zl = results[z]
        if 0.60 < spec.z < 1.05:
            check(f"z={spec.z:.3f}: Hbeta detected", has(rows, "Hbeta4861"))
            check(f"z={spec.z:.3f}: OIII5007 detected", has(rows, "OIII5007"))
        if spec.z > 1.5:
            check(f"z={spec.z:.3f}: CIV detected", has(rows, "CIV1549"))
            check(f"z={spec.z:.3f}: MgII detected", has(rows, "MgII2798"))
    # Pre-declared ZLINE checks (bright, unblended).  O III at z=0.65 and the
    # broad Mg II at z=1.83 are diagnostics only: the former is affected by the
    # H-beta broad wing, the latter by UV Fe II / continuum blending.
    checks = [(0.651, "Hbeta4861", "H_beta"), (0.990, "Hbeta4861", "H_beta"),
              (0.990, "OIII5007", "[O_III] 5007"), (1.830, "CIV1549", "C_IV 1549")]
    for zc, line, key in checks:
        spec, rt, rows, zl = results[zc]
        fit = total(rows, line)
        ref = zl.get(key, {}).get("area", np.nan)
        if np.isfinite(ref) and ref > 0 and fit > 0:
            check(f"z={spec.z:.3f}: {line} within 50% of ZLINE",
                  abs(fit / ref - 1) < 0.5, f"ratio={fit/ref:.2f}")
    for zc, line, key in [(0.651, "OIII5007", "[O_III] 5007"),
                          (1.830, "MgII2798", "Mg_II 2799")]:
        spec, rt, rows, zl = results[zc]
        fit = total(rows, line)
        ref = zl.get(key, {}).get("area", np.nan)
        if np.isfinite(ref) and ref > 0:
            print(f"DIAG z={spec.z:.3f}: {line} fit/ZLINE={fit/ref:.2f} (blend/systematic; not a pass gate)")


def main():
    test_sdss_router()
    test_sdss_fit()
    test_zgt05()
    test_synthetic()
    n = len(CHECKS)
    bad = [c for c in CHECKS if not c[1]]
    print(f"\n{sum(c[1] for c in CHECKS)}/{n} checks passed")
    if bad:
        print("FAILED:")
        for name, _, detail in bad:
            print(" -", name, detail)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
