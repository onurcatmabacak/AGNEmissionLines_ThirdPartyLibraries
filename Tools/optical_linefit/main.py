#!/usr/bin/env python3
"""Joint local H-beta/[O III] fit for one optical spectrum.

This is deliberately a *local* fit, not a global QSO model.  It is used for
objects where a global fit is known to misallocate flux (for example the
PDS 456 X-SHOOTER spectrum).  The model is:

    linear local continuum
    + H-beta broad Gaussian
    + H-beta narrow Gaussian
    + [O III] 4959/5007 narrow doublet, tied to the 1:2.98 ratio

The H-beta and [O III] components are fitted **simultaneously**, so the broad
H-beta wing cannot be absorbed into a separate [O III] fit.  The underlying
implementation is the repository's ``pipeline_ir.fit`` local-Gaussian engine.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pipeline_ir.spectrum import read_spectrum
from pipeline_ir.lines import BY_NAME
from pipeline_ir.router import LineCoverage
from pipeline_ir.fit import fit_group


def _f(x):
    try:
        x = float(x)
    except Exception:
        return None
    return x if math.isfinite(x) else None


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fits", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--z", required=True, type=float)
    p.add_argument("--name", default="")
    a = p.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    spec = read_spectrum(a.fits, z_override=a.z, band="optical")
    lines = [BY_NAME[x] for x in ("Hbeta4861", "OIII4959", "OIII5007")]
    group = [LineCoverage(ln, ln.rest_um * (1.0 + a.z), "optical", True, True, 10.0)
             for ln in lines]
    rows, chi2_red = fit_group(spec, group, a.z)
    by = {(r.line, r.component): r for r in rows}
    hb = [r for r in rows if r.line == "Hbeta4861"]
    o3 = [r for r in rows if r.line == "OIII5007"]
    hb_total = sum(r.flux for r in hb if np.isfinite(r.flux))
    hb_err = math.sqrt(sum((r.flux_err ** 2) for r in hb if np.isfinite(r.flux_err)))
    o3_total = sum(r.flux for r in o3 if np.isfinite(r.flux))
    o3_err = math.sqrt(sum((r.flux_err ** 2) for r in o3 if np.isfinite(r.flux_err)))
    detected = [r for r in rows if r.detected]
    quality = "accepted"
    notes = []
    if chi2_red > 10:
        quality = "provisional"
        notes.append(f"local fit chi2_red={chi2_red:.1f} > 10; absorption/continuum mismatch")
    if hb_total <= 0 or o3_total <= 0:
        quality = "tentative"
        notes.append("one of H-beta or [O III] is not detected")
    if not any(r.detected for r in hb):
        quality = "tentative"
        notes.append("H-beta not detected at S/N >= 3")

    with (a.out / "optical_lines.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["line", "component", "flux_1e17", "flux_err", "fwhm_kms",
                    "center_um", "ew_a", "snr", "detected", "chi2_red"])
        for r in rows:
            w.writerow([r.line, r.component, r.flux, r.flux_err,
                        r.fwhm_kms, r.center_um, r.ew_a, r.snr, int(r.detected), r.chi2_red])
    hb_center = 4862.68 / 1e4 * (1.0 + a.z)
    near = spec.mask & (np.abs(spec.wave_um - hb_center) < 0.03)
    continuum = float(np.nanmedian(spec.flux[near])) if near.any() else float("nan")
    summary = {
        "tool": "optical_linefit",
        "status": "ok",
        "source": a.name or a.fits.stem,
        "z": a.z,
        "input": str(a.fits),
        "model": "linear continuum + Hbeta broad/narrow + [OIII] 4959/5007 tied doublet",
        "chi2_red": chi2_red,
        "Hbeta_total_1e17": hb_total,
        "Hbeta_total_err_1e17": hb_err,
        "OIII5007_total_1e17": o3_total,
        "OIII5007_total_err_1e17": o3_err,
        "Hbeta_OIII_ratio": hb_total / o3_total if o3_total > 0 else None,
        "continuum_1e17": continuum,
        "Hbeta_ew_obs_A": hb_total / continuum if continuum > 0 else None,
        "Hbeta_ew_rest_A": (hb_total / continuum) * (1.0 + a.z) if continuum > 0 else None,
        "quality": quality,
        "notes": notes,
        "n_components_detected": len(detected),
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (a.out / "optical_lines_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (a.out / "run.json").write_text(json.dumps({**summary, "caveats": notes}, indent=2) + "\n")

    m = spec.mask & (spec.wave_um > 0.54) & (spec.wave_um < 0.65)
    ylo, yhi = np.nanpercentile(spec.flux[m], [1, 99]) if m.any() else (None, None)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(spec.wave_um[m] * 1e4, spec.flux[m], "k", lw=0.8, label="data")
    for r in rows:
        if r.detected:
            ax.axvline(r.center_um * 1e4, color="C3", alpha=0.5, lw=0.8)
            ax.text(r.center_um * 1e4, np.nanpercentile(spec.flux[m], 90),
                    f"{r.line}\n{r.component}", rotation=90, fontsize=7,
                    ha="right", va="top")
    ax.set_xlim(5500, 6500)
    if ylo is not None and np.isfinite(ylo) and np.isfinite(yhi) and yhi > ylo:
        ax.set_ylim(ylo - 0.05 * (yhi - ylo), yhi + 0.15 * (yhi - ylo))
    ax.set_xlabel("observed wavelength (A)")
    ax.set_ylabel("flux (1e-17 erg s-1 cm-2 A-1)")
    ax.set_title(f"{summary['source']}  local H-beta/[O III]  z={a.z:.4f}")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(a.out / "optical_fit.png", dpi=160)
    fig.savefig(a.out / "optical_fit.pdf")
    plt.close(fig)

    readme = f"""# optical_linefit — {summary['source']}

Local simultaneous H-beta + [O III] 4959/5007 fit.

| quantity | value |
|---|---:|
| H-beta total | {hb_total:.3f} x 1e-17 erg cm-2 s-1 |
| [O III] 5007 total | {o3_total:.3f} x 1e-17 |
| H-beta/[O III] | {summary['Hbeta_OIII_ratio'] if summary['Hbeta_OIII_ratio'] is not None else 'n/a'} |
| chi2_red | {chi2_red:.2f} |
| quality | **{quality}** |

{chr(10).join('- ' + x for x in notes) if notes else '- no additional fit warning'}

The model is local and uses the repository's `pipeline_ir` engine.  It is
independent of PyQSOFit/QSOFITMORE and is intended for the PDS 456 H-beta
measurement that the HST/STIS UV spectrum cannot provide.
"""
    (a.out / "README.md").write_text(readme)
    print(f"[optical_linefit] {summary['source']} Hbeta={hb_total:.1f} OIII={o3_total:.1f} "
          f"ratio={summary['Hbeta_OIII_ratio']} quality={quality}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
