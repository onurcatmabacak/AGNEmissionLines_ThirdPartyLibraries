#!/usr/bin/env python3
"""Dedicated FIR line fitter: one Gaussian + local continuum per line.

Lines: [OI]63, [OIII]88, [NII]122, [OI]145, [CII]158 (rest-frame micron).
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from pipeline_ir.spectrum import read_spectrum, C_KMS

LINES = [("OI63", 63.184), ("OIII88", 88.356), ("NII122", 121.898),
         ("OI145", 145.525), ("CII158", 157.741)]


def gauss(x, a, b, amp, c, sig):
    return a + b * (x - c) + amp * np.exp(-0.5 * ((x - c) / sig) ** 2)


def fit_one(spec, name, rest, z, half_res=5.0):
    c = rest * (1 + z)
    dx = float(np.nanmedian(np.diff(spec.wave_um[spec.mask])))
    half = max(half_res * dx, c * 700.0 / C_KMS)
    m = spec.mask & (np.abs(spec.wave_um - c) <= half)
    x, y, e = spec.wave_um[m], spec.flux[m], spec.error[m]
    if x.size < 6:
        return None
    cont = float(np.median(y)); peak = float(np.max(y - cont))
    p0 = [cont, 0.0, max(peak, 0.05 * cont), c, max(dx, c * 300.0 / C_KMS)]
    lo = [cont - 10 * abs(cont) - 10 * np.median(e), -0.01, 0.0, c - 0.02 * c, 0.3 * dx]
    hi = [cont + 10 * abs(cont) + 10 * np.median(e), 0.01, 10 * max(peak, np.median(e)),
          c + 0.02 * c, 20 * dx]
    try:
        popt, pcov = curve_fit(gauss, x, y, p0=p0, sigma=e, absolute_sigma=True,
                               bounds=(lo, hi), maxfev=20000)
    except Exception:
        return None
    a, b, amp, cen, sig = popt
    perr = np.sqrt(np.clip(np.diag(pcov), 0, None))
    flux = amp * sig * np.sqrt(2 * np.pi) * 1e4
    rel = np.sqrt((perr[2] / amp) ** 2 + (perr[4] / sig) ** 2) if amp > 0 and sig > 0 else np.nan
    ferr = abs(flux) * rel if np.isfinite(rel) else np.nan
    snr = flux / ferr if (np.isfinite(ferr) and ferr > 0) else np.nan
    detected = bool(np.isfinite(snr) and snr >= 3 and amp > 0)
    fwhm = 2.354820045 * sig / cen * C_KMS
    return dict(line=name, rest_um=rest, obs_um=cen, flux=flux, flux_err=ferr,
                fwhm_kms=fwhm, snr=snr, detected=detected,
                ew_a=(flux / a) if a else np.nan, n_pix=int(x.size))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--z", type=float, required=True)
    args = p.parse_args(argv)
    spec = read_spectrum(args.input, z_override=args.z)
    args.output.mkdir(parents=True, exist_ok=True)
    rows = [r for r in (fit_one(spec, n, l, args.z) for n, l in LINES) if r]
    import csv
    with (args.output / f"{spec.object_id}.fir_lines.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["line"])
        w.writeheader(); w.writerows(rows)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(spec.wave_um[spec.mask], spec.flux[spec.mask], color="0.35", lw=0.7)
    for r in rows:
        if r["detected"]:
            ax.axvline(r["obs_um"], color="C3", alpha=0.5)
            ax.text(r["obs_um"], np.nanmax(spec.flux[spec.mask]) * 0.92, r["line"],
                    rotation=90, fontsize=7, color="C3", ha="right", va="top")
    ax.set_xlabel("observed wavelength (um)"); ax.set_ylabel("flux (1e-17)")
    ax.set_title(f"{spec.object_id}  z={spec.z:.3f}  FIR lines")
    fig.tight_layout(); fig.savefig(args.output / f"{spec.object_id}.fir_fit.png", dpi=140)
    fig.savefig(args.output / f"{spec.object_id}.fir_fit.pdf"); plt.close(fig)
    (args.output / f"{spec.object_id}.fir_summary.json").write_text(
        json.dumps({"object_id": spec.object_id, "z": spec.z, "n_lines": len(rows),
                    "detected": sum(r["detected"] for r in rows)}, indent=2))
    print(f"[fir] {spec.object_id}: {len(rows)} lines, {sum(r['detected'] for r in rows)} detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
