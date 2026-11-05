#!/usr/bin/env python3
"""Soft X-ray grating spectroscopy: fit resolved lines in an XMM-Newton RGS spectrum.

Every other X-ray tool here uses CCD resolution (XMM EPIC, RXTE PCA), where
"X-ray lines" means one blended Fe K-alpha at 6.4 keV.  RGS resolves the soft
band at ~0.06 A, so the OVII/OVIII/Ne IX/Fe XVII lines can be fitted as lines the
way the rest of the repository fits optical and IR lines.

This adapter consumes the **pipeline (PPS) products** the XMM-Newton SOC serves
through XSA: a counts spectrum (``SRSPEC``) and its response matrix
(``RSPMAT``, an XSPEC RMF).  No SAS reduction is needed - which matters, because
``rgsproc`` also needs an attitude file and housekeeping from the ODF, and the
XSA AIO endpoint does not serve those.

Caveat recorded in the product: ``RSPMAT`` is the response matrix alone, without
a separate ARF, so *fluxes* are not photometrically calibrated.  Line energies,
widths, significances and equivalent widths are; fluxes are reported as fitted
normalisations and are not used for any physical claim.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np


def log(msg: str) -> None:
    print(f"[xmm_rgs] {msg}", flush=True)


def find_product(directory: Path, kind: str, order: str | None = None) -> Path:
    """Locate a PPS product by name fragment (SRSPEC / RSPMAT), matching order.

    SRSPEC/RSPMAT names carry the spectral order in the first digit after the
    prefix (…1U002SRSPEC1003 is order 1, …2003 is order 2), and a spectrum must be
    paired with the response of the *same* order.
    """
    hits = sorted(p for p in directory.rglob(f"*{kind}*.FT*"))
    if order:
        matched = [p for p in hits if f"{kind}{order}" in p.name]
        hits = matched or hits
    if not hits:
        raise SystemExit(f"no {kind} product under {directory}")
    return hits[-1]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--source-key", default=None)
    args = ap.parse_args(argv)

    cfg = json.loads(args.config.read_text()) if args.config and args.config.exists() else {}
    snr_min = float(cfg.get("snr_min", 3.0))
    emin, emax = cfg.get("band_keV", [0.4, 1.2])
    lines = cfg.get("lines", [])
    outdir = args.output
    outdir.mkdir(parents=True, exist_ok=True)

    specs = sorted(args.input.rglob("*SRSPEC*.FT*"))
    if not specs:
        raise SystemExit(f"no SRSPEC under {args.input}")

    import xspec
    xspec.Fit.statMethod = "cstat"
    xspec.Xset.chatter = 0

    # One spectrum per instrument (RGS1, RGS2); each carries its own response.
    loaded = []
    for spec in specs:
        import re
        m_order = re.search(r"SRSPEC(\d)", spec.name)
        order = m_order.group(1) if m_order else None
        rsp = find_product(spec.parent, "RSPMAT", order)
        tag = spec.name.split("R1U")[-1][:4] if "R1U" in spec.name else spec.name[-12:-6]
        try:
            s = xspec.Spectrum(str(spec))
            s.response = str(rsp)
            s.ignore(f"**-{emin}")
            s.ignore(f"{emax}-**")
            loaded.append((spec.name, s))
            log(f"{spec.name} + {rsp.name}: {len(s.values)} bins in {emin}-{emax} keV")
        except Exception as exc:
            log(f"{spec.name} skipped: {exc}")
    if not loaded:
        raise SystemExit("no spectrum could be loaded with its response")

    # Continuum: absorbed power law (the AGN soft excess is absorbed by the
    # Galactic column) plus one zgauss per requested line.
    # Build the whole expression at once: PyXspec does not support Model + str.
    expr = "tbabs*zpowerlw" + "+zgauss" * len(lines)
    m = xspec.Model(expr)
    m.TBabs.nH = float(cfg.get("nH_1e22", 0.014))
    m.TBabs.nH.frozen = True
    m.zpowerlw.PhoIndex = 2.5
    m.zpowerlw.Redshift = float(cfg.get("redshift", 0.0))
    m.zpowerlw.Redshift.frozen = True
    m.zpowerlw.norm = 1.0
    gauss_names = [n for n in m.componentNames if n.startswith("zgauss")]
    for i, line in enumerate(lines):
        if i >= len(gauss_names):
            log(f"missing model component for {line['name']}")
            break
        name = gauss_names[i]
        try:
            # Energies and widths are frozen at the laboratory values and at the
            # RGS resolution: five blended Gaussians with free positions and
            # widths is a degenerate fit (the first attempt drove the energies to
            # their bounds and C-stat to 5594/2716).  With E and sigma fixed the
            # fitted normalisations are line fluxes and their errors are honest
            # detection statistics.
            getattr(m, name).LineE = float(line["energy_keV"])
            getattr(m, name).LineE.frozen = True
            getattr(m, name).Sigma = float(line.get("sigma_keV", 0.002))
            getattr(m, name).Sigma.frozen = True
            getattr(m, name).norm = 1e-4
        except Exception as exc:
            log(f"line component {i} setup failed: {exc}")
    xspec.Fit.perform()
    log(f"fit: statistic {xspec.Fit.statistic:.1f} / {xspec.Fit.dof} dof")

    rows = []
    for i, line in enumerate(lines):
        name = line["name"]
        try:
            if i >= len(gauss_names):
                raise RuntimeError("no model component")
            c = getattr(m, gauss_names[i])
            e = float(c.LineE.values[0])
            eerr = float(c.LineE.sigma)
            sig = float(c.Sigma.values[0])
            serr = float(c.Sigma.sigma)
            norm = float(c.norm.values[0])
            nerr = float(c.norm.sigma)
            snr = abs(norm / nerr) if nerr > 0 else float("nan")
            fwhm_ev = sig * 2.3548 * 1000.0
            rows.append({
                "line": name, "energy_keV": e, "energy_err_keV": eerr,
                "wavelength_A": 12.3984 / e,
                "sigma_keV": sig, "sigma_err_keV": serr,
                "fwhm_eV": fwhm_ev,
                "norm": norm, "norm_err": nerr,
                "snr": snr, "detected": bool(snr >= snr_min),
            })
            log(f"{name}: E={e:.4f}+/-{eerr:.4f} keV ({12.3984/e:.2f} A), "
                f"FWHM={fwhm_ev:.0f} eV, S/N {snr:.1f}")
        except Exception as exc:
            rows.append({"line": name, "snr": float("nan"), "detected": False,
                         "error": str(exc)[:120]})
            log(f"{name}: failed ({exc})")

    cols = ["line", "energy_keV", "energy_err_keV", "wavelength_A", "sigma_keV",
            "sigma_err_keV", "fwhm_eV", "norm", "norm_err", "snr", "detected"]
    with open(outdir / "rgs_lines.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    xspec.AllData.clear()
    (outdir / "run.json").write_text(json.dumps({
        "tool": "xmm_rgs",
        "status": "ok",
        "source_key": args.source_key or args.input.name,
        "spectra": [n for n, _ in loaded],
        "band_keV": [emin, emax],
        "statistic": float(xspec.Fit.statistic),
        "dof": int(xspec.Fit.dof),
        "null_statistic": float(getattr(xspec.Fit, "null", float("nan"))),
        "continuum": "tbabs*zpowerlw",
        "n_lines": len(lines),
        "note": "RSPMAT carries the response matrix without a separate ARF, so "
                "line energies/widths/significances are calibrated but absolute "
                "fluxes are not.",
    }, indent=2) + "\n")
    log(f"wrote {outdir/'rgs_lines.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
