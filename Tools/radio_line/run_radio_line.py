#!/usr/bin/env python3
"""Radio / sub-mm spectral-line fitting with pyspeckit.

Fits a set of Gaussian components (emission, or absorption with
``absorption: true``) on top of a polynomial baseline to a radio or sub-mm
spectrum, converts the result to the repository line-table convention
(velocity in km/s, FWHM, integrated flux, S/N) and writes ``run.json``.

Input is a 1-D FITS spectrum (``--input`` may be the file itself) with either a
frequency axis, a velocity axis, or a plain channel axis plus ``--freq-start``/
``--freq-step``; FITS ``CRVAL1``/``CDELT1``/``CTYPE1`` are honoured.  ASCII
two-column files (``x y``) also work.

pyspeckit is used for the model evaluation and the least-squares fit, so the
line shapes and units come from the same code the radio community uses;
``lmfit`` is used only for the parameter bookkeeping.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def log(msg: str) -> None:
    print(f"[radio_line] {msg}", flush=True)


def read_spectrum(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Return (x, flux, error, meta) from FITS or ASCII."""
    suffix = path.suffix.lower()
    if suffix in (".fits", ".fit", ".fz"):
        from astropy.io import fits

        with fits.open(path) as hdul:
            data = None
            hdu_index = 0
            for i, hdu in enumerate(hdul):
                if hdu.data is None:
                    continue
                arr = np.asarray(hdu.data)
                if arr.ndim == 1:
                    data, hdu_index = arr, i
                    break
                if arr.ndim >= 2:  # take the first row of a 2-D array
                    data, hdu_index = np.asarray(arr).reshape(arr.shape[-1] and (arr.shape[0], -1))[0], i
                    break
            if data is None:
                raise SystemExit(f"no 1-D spectrum in {path}")
            hdr = hdul[hdu_index].header
        flux = np.asarray(data, dtype=float).ravel()
        n = flux.size
        crval = float(hdr.get("CRVAL1", 0.0))
        cdelt = float(hdr.get("CDELT1", 1.0))
        ctype = str(hdr.get("CTYPE1", ""))
        x = crval + cdelt * np.arange(n)
        meta = {"ctype": ctype, "crval": crval, "cdelt": cdelt, "n": n}
        # A FITS error extension (ERR/ERROR/STAT) is used when present.
        err = None
        for name in ("ERR", "ERROR", "STAT", "BERROR"):
            if name in hdul:
                err = np.asarray(hdul[name].data, dtype=float).ravel()[:n]
                break
        if err is None:
            mad = np.median(np.abs(np.diff(flux))) * 1.4826 or 1.0
            err = np.full(n, max(mad, 1e-12))
        return x, flux, np.asarray(err, dtype=float), meta

    # ASCII: "x y [err]"
    arr = np.loadtxt(path)
    if arr.ndim == 1:
        arr = arr[:, None]
    x = arr[:, 0].astype(float)
    flux = arr[:, 1].astype(float)
    err = arr[:, 2].astype(float) if arr.shape[1] > 2 else np.full(
        x.size, max(np.median(np.abs(np.diff(flux))) * 1.4826, 1e-12))
    return x, flux, err, {"ctype": "ASCII", "n": x.size}


def guess_peaks(flux: np.ndarray, ncomp: int, absorption: bool, err: float):
    """Start values from the N strongest local extrema."""
    signal = -flux if absorption else flux
    order = np.argsort(signal)[::-1]
    picked: list[int] = []
    min_sep = max(3, flux.size // (4 * max(ncomp, 1)))
    for idx in order:
        if signal[idx] <= 0:
            break
        if all(abs(idx - p) >= min_sep for p in picked):
            picked.append(int(idx))
        if len(picked) == ncomp:
            break
    while len(picked) < ncomp:  # degenerate spectrum: spread the starts out
        picked.append(int(flux.size * (len(picked) + 1) / (ncomp + 1)))
    return sorted(picked)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=Path("/app/input"))
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("/app/config/config.json"))
    ap.add_argument("--z", type=float, default=0.0)
    ap.add_argument("--source-key", default=None)
    ap.add_argument("--ncomp", type=int, default=None)
    ap.add_argument("--absorption", action="store_true")
    args = ap.parse_args(argv)

    cfg = json.loads(args.config.read_text()) if args.config.exists() else {}
    ncomp = int(args.ncomp or cfg.get("n_components", 2))
    absorption = bool(args.absorption or cfg.get("absorption", False))
    order = int(cfg.get("baseline_order", 1))
    line = cfg.get("line", {})
    rest_ghz = float(line.get("rest_frequency_ghz", 1.420405751))
    outdir = args.output
    outdir.mkdir(parents=True, exist_ok=True)

    # Locate the spectrum: a file, or the first FITS/ASCII file in a directory.
    src = args.input
    if src.is_dir():
        cands = sorted([p for p in src.rglob("*") if p.suffix.lower() in (".fits", ".fit", ".fz", ".txt", ".dat", ".csv")])
        if not cands:
            raise SystemExit(f"no spectrum found under {src}")
        src = cands[0]
    log(f"spectrum: {src}")

    x, flux, err, meta = read_spectrum(src)
    # Frequency axis if the header says so, else derive velocity from x.
    ctype = meta.get("ctype", "").upper()
    freq = None
    if "FREQ" in ctype or (x.max() > 1e6):        # Hz or GHz
        freq = x / 1e9 if x.max() > 1e6 else x     # -> GHz
    import pyspeckit

    if freq is not None:
        sp = pyspeckit.Spectrum(data=flux, error=err, xarr=freq,
                                xarrkwargs={"unit": "GHz"}, header=src.name)
        x_kind = "frequency"
    else:
        sp = pyspeckit.Spectrum(data=flux, error=err, xarr=x, header=src.name)
        x_kind = "channel/velocity"
    # pyspeckit keeps xarr as an astropy Quantity; arithmetic needs plain floats
    xv = np.asarray(getattr(sp.xarr, "value", sp.xarr), dtype=float)
    log(f"{len(sp.data)} channels, {x_kind} axis, median S/N "
        f"{np.nanmedian(np.abs(flux) / np.maximum(err, 1e-30)):.1f}")

    # Baseline: fit a polynomial to the line-free edges and subtract it here
    # rather than through pyspeckit's interactive baseline (its exclude
    # semantics differ between versions and silently corrupted the fit).
    edge = max(5, len(sp.data) // 6)
    mask = np.zeros(len(sp.data), dtype=bool)
    mask[:edge] = True
    mask[-edge:] = True
    if order >= 0:
        coef = np.polyfit(xv[mask], flux[mask], order)
        baseline = np.polyval(coef, xv)
    else:
        baseline = np.zeros_like(flux)
    flux_sub = flux - baseline
    sp = pyspeckit.Spectrum(data=flux_sub, error=err, xarr=xv,
                            xarrkwargs={"unit": "GHz"} if freq is not None else {},
                            header=src.name)

    peaks = guess_peaks(flux_sub, ncomp, absorption, float(np.median(err)))
    guesses, limits_min, limits_max = [], [], []
    span = float(xv.max() - xv.min())
    for i in peaks:
        amp = abs(flux_sub[i]) * (-1.0 if absorption else 1.0)
        guesses += [amp, float(xv[i]), span / (40.0 * ncomp)]
        limits_min += [-np.inf, float(xv.min()), span / 1000.0]
        limits_max += [np.inf, float(xv.max()), span]
    sp.specfit(fittype="gaussian", guesses=guesses, limitedmin=[True] * len(guesses),
               limitedmax=[True] * len(guesses), minpars=limits_min, maxpars=limits_max,
               negamp=absorption, verbose=False)

    pars = np.asarray(sp.specfit.modelpars, dtype=float).reshape(-1, 3)
    perr = np.asarray(getattr(sp.specfit, "modelerrs", np.full(pars.shape, np.nan)), dtype=float).reshape(-1, 3)
    resid = flux_sub - sp.specfit.model
    rms = float(np.nanstd(resid))
    chi2 = float(np.nansum((resid / np.maximum(err, 1e-30)) ** 2))
    dof = int(flux.size - 3 * ncomp - (order + 1))

    c_kms = 299792.458
    rows = []
    for k, (amp, centre, sigma) in enumerate(pars):
        if not np.isfinite(amp) or not np.isfinite(centre) or sigma <= 0:
            continue
        # velocity relative to the line rest frequency (frequency axis only)
        if freq is not None:
            vel = c_kms * (rest_ghz * (1.0 + args.z) - centre) / centre
        else:
            vel = np.nan
        fwhm_kms = abs(sigma) * (c_kms / centre) * 2.3548 if freq is not None else np.nan
        integrated = abs(amp) * abs(sigma) * np.sqrt(2 * np.pi)
        rows.append({
            "line": line.get("name", "unknown"),
            "component": f"c{k + 1}",
            "component_type": "absorption" if amp < 0 else "emission",
            "centre": float(centre),
            "centre_err": float(perr[k, 1]) if perr.shape == pars.shape else None,
            "amplitude": float(amp),
            "sigma": float(sigma),
            "flux_integrated": float(integrated),
            "fwhm_kms": float(fwhm_kms) if np.isfinite(fwhm_kms) else None,
            "velocity_kms": float(vel) if np.isfinite(vel) else None,
            "snr": float(abs(amp) / max(rms, 1e-30)),
            "detected": bool(abs(amp) / max(rms, 1e-30) >= float(cfg.get("snr_min", 3.0))),
        })

    import pandas as pd

    pd.DataFrame(rows).to_csv(outdir / "radio_lines.csv", index=False)
    pd.DataFrame({"x": x, "flux": flux, "baseline": baseline, "flux_sub": flux_sub, "err": err, "model": sp.specfit.model,
                  "residual": resid}).to_csv(outdir / "radio_model.csv", index=False)

    if cfg.get("plots", True):
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, (a0, a1) = plt.subplots(2, 1, figsize=(9, 6), sharex=True,
                                         gridspec_kw={"height_ratios": [3, 1]})
            a0.plot(x, flux, "k", lw=0.8, alpha=0.5, label="data")
            a0.plot(x, flux_sub, "C7", lw=0.7, label="baseline-subtracted")
            a0.plot(x, sp.specfit.model, "C3", lw=1.0, label="model")
            a0.set_ylabel("flux")
            a0.legend()
            a1.plot(x, resid, "C0", lw=0.7)
            a1.axhline(0, color="k", lw=0.5)
            a1.set_ylabel("residual")
            a1.set_xlabel(meta.get("ctype", "x") or "x")
            fig.tight_layout()
            fig.savefig(outdir / "radio_fit.png", dpi=140)
            fig.savefig(outdir / "radio_fit.pdf")
            plt.close(fig)
        except Exception as exc:  # noqa: BLE001
            log(f"plot skipped: {exc}")

    run = {
        "tool": "radio_line",
        "status": "ok" if rows else "no_components",
        "source_key": args.source_key or src.stem,
        "spectrum": str(src),
        "axis": x_kind,
        "ctype": meta.get("ctype", ""),
        "n_channels": int(flux.size),
        "redshift": args.z,
        "line": line,
        "fit": {"n_components": ncomp, "absorption": absorption,
                "baseline_order": order, "chi2": chi2, "dof": dof,
                "chi2nu": chi2 / dof if dof > 0 else None, "rms": rms},
        "components": rows,
        "limitations": [
            "Single-spectrum fit; no spatial model, so a cube must be extracted first.",
            "Gaussian components only: hyperfine structure is not modelled here (use the "
            "submm_line tool for McFine-based hyperfine fits).",
            "Velocities assume the configured rest frequency and redshift; an incorrect "
            "redshift shifts every component coherently.",
        ],
    }
    (outdir / "run.json").write_text(json.dumps(run, indent=2) + "\n")
    (outdir / "config.effective.json").write_text(json.dumps(cfg, indent=2) + "\n")
    log(f"wrote {outdir} ({len(rows)} components, chi2/nu="
        f"{chi2 / dof if dof > 0 else float('nan'):.2f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
