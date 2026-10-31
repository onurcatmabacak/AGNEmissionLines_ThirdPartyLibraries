#!/usr/bin/env python3
"""Sub-mm spectral-line fitting with McFine (hyperfine structure, multi-component).

McFine models the line with an optical-depth radiative-transfer profile
(``hyperfine_structure_lte``: excitation temperature, optical depth, systemic
velocity and width, applied to every hyperfine component of the transition) and
ships the hyperfine tables for ``n2hp10`` (N2H+ 1-0, 93 GHz), ``co21`` (CO 2-1,
230 GHz) and ``hi21cm``.

The adapter converts a 1-D spectrum to a velocity axis about the rest
frequency, fits N such components plus a global amplitude scale (the
Jy-per-K/beam-filling nuisance) with lmfit, and writes the repository line
table so sub-mm fluxes sit beside the optical ones.

Velocity convention: ``v = c (nu_rest (1+z) - nu) / nu`` (radio/optical hybrid
as used by McFine's ``v_lines``), i.e. positive velocity is redshifted.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

C_KMS = 299792.458


def log(msg: str) -> None:
    print(f"[submm_line] {msg}", flush=True)


def read_spectrum(path: Path):
    if path.suffix.lower() in (".fits", ".fit", ".fz"):
        from astropy.io import fits

        with fits.open(path) as hdul:
            data, hdr = None, None
            for hdu in hdul:
                if hdu.data is not None and np.asarray(hdu.data).ndim >= 1:
                    data, hdr = np.asarray(hdu.data, dtype=float), hdu.header
                    break
            if data is None:
                raise SystemExit(f"no spectrum in {path}")
            err = None
            for name in ("ERR", "ERROR", "STAT"):
                if name in hdul:
                    err = np.asarray(hdul[name].data, dtype=float)
                    break
        flux = data.ravel()
        crval, cdelt = float(hdr.get("CRVAL1", 0.0)), float(hdr.get("CDELT1", 1.0))
        x = crval + cdelt * np.arange(flux.size)
        ctype = str(hdr.get("CTYPE1", ""))
    else:
        arr = np.loadtxt(path)
        if arr.ndim == 1:
            arr = arr[:, None]
        x, flux = arr[:, 0].astype(float), arr[:, 1].astype(float)
        err = arr[:, 2].astype(float) if arr.shape[1] > 2 else None
        ctype = "ASCII"
    if err is None:
        err = np.full(flux.size, max(np.median(np.abs(np.diff(flux))) * 1.4826, 1e-12))
    return x, flux, np.asarray(err, float).ravel()[: flux.size], ctype


def to_velocity(x: np.ndarray, ctype: str, freq_rest_ghz: float, z: float):
    """Return velocity in km/s, the observed-frame rest frequency, and the axis kind.

    CTYPE decides first: a VELO axis is already km/s, and a frequency axis is
    Hz above 1e6 or GHz otherwise.  The fallback heuristic treats a strictly
    positive axis between 50 and 1000 as GHz (radio spectra are usually given
    in GHz) and anything else within +/-5e4 as km/s -- the earlier version
    tested the GHz range before the VELO ctype and misread every velocity axis.
    """
    nu_rest = freq_rest_ghz * (1.0 + z)
    up = ctype.upper()
    if "VELO" in up:
        return x.astype(float), nu_rest, "velocity"
    if "FREQ" in up or x.max() > 1e6:
        nu = x / 1e9 if x.max() > 1e6 else x
        return C_KMS * (nu_rest - nu) / nu, nu_rest, "frequency"
    if x.min() > 0 and 50.0 <= x.max() <= 1000.0:
        return C_KMS * (nu_rest - x) / x, nu_rest, "frequency"
    if np.nanmax(np.abs(x)) < 5e4:
        return x.astype(float), nu_rest, "velocity"
    raise SystemExit(f"cannot interpret the spectral axis (CTYPE1={ctype!r})")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=Path("/app/input"))
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("/app/config/config.json"))
    ap.add_argument("--z", type=float, default=None)
    ap.add_argument("--source-key", default=None)
    ap.add_argument("--line", default=None)
    ap.add_argument("--ncomp", type=int, default=None)
    ap.add_argument("--fit-type", default=None)
    args = ap.parse_args(argv)

    cfg = json.loads(args.config.read_text()) if args.config.exists() else {}
    line = str(args.line or cfg.get("line", "n2hp10")).lower()
    ncomp = int(args.ncomp or cfg.get("n_components", 2))
    fit_type = str(args.fit_type or cfg.get("fit_type", "lte"))
    z = float(args.z if args.z is not None else cfg.get("redshift", 0.0))

    from mcfine.fitting import multiple_components
    from mcfine.line_info import freq_lines, strength_lines_dict, v_lines_dict

    # McFine groups the individual hyperfine transitions: freq_lines holds all
    # of them but strength_lines_dict / v_lines_dict only the merged groups.
    keys = [k for k in freq_lines if k.startswith(line)
            and k in strength_lines_dict and k in v_lines_dict]
    if not keys:
        raise SystemExit(f"unknown McFine line {line!r}; available: "
                         f"{sorted({k.split('_')[0] for k in freq_lines})}")
    # strongest (main) hyperfine component sets the rest frequency
    main = max(keys, key=lambda k: strength_lines_dict.get(k, 0.0))
    freq_rest = float(freq_lines[main])
    strengths = np.array([strength_lines_dict[k] for k in keys], dtype=float)
    v_lines = np.array([v_lines_dict.get(k, 0.0) for k in keys], dtype=float)
    strengths /= strengths.sum()
    log(f"line {line}: {len(keys)} hyperfine components, rest {freq_rest:.6f} GHz, "
        f"strongest v-offset {v_lines[np.argmax(strengths)]:+.3f} km/s")

    src = args.input
    if src.is_dir():
        cands = sorted(p for p in src.rglob("*")
                       if p.suffix.lower() in (".fits", ".fit", ".fz", ".txt", ".dat", ".csv"))
        if not cands:
            raise SystemExit(f"no spectrum under {src}")
        src = cands[0]
    x, flux, err, ctype = read_spectrum(src)
    vel, nu_rest, axis_kind = to_velocity(x, ctype, freq_rest, z)
    order = np.argsort(vel)
    vel, flux, err = vel[order], flux[order], err[order]
    outdir = args.output
    outdir.mkdir(parents=True, exist_ok=True)
    log(f"{flux.size} channels, {axis_kind} axis, v = {vel.min():.0f}..{vel.max():.0f} km/s")

    pri = cfg.get("priors", {})
    tex_rng = pri.get("tex_K", [5.0, 200.0])
    tau_rng = pri.get("log_tau", [-2.0, 2.0])
    vc_rng = pri.get("v_centre_kms", [-600.0, 600.0])
    w_rng = pri.get("width_kms", [5.0, 500.0])
    props = ["tex", "tau", "voff", "width"]      # len(props) == prop_len for lte

    def model(vel_array, scale, *theta, _ncomp=None):
        n = ncomp if _ncomp is None else int(_ncomp)
        return scale * multiple_components(np.asarray(theta, float), vel_array,
                                           strengths, v_lines, props, n,
                                           fit_type=fit_type)

    import lmfit

    # start from the strongest peak (or trough, for absorption)
    signal = flux - np.median(flux)
    sign = -1.0 if np.nanmin(signal) < -3 * np.nanstd(signal) and \
                    abs(np.nanmin(signal)) > abs(np.nanmax(signal)) else 1.0
    work = sign * signal
    order_pk = np.argsort(work)[::-1]
    starts, min_sep = [], max(3, vel.size // (4 * ncomp))
    for idx in order_pk:
        if all(abs(idx - s) >= min_sep for s in starts):
            starts.append(int(idx))
        if len(starts) == ncomp:
            break
    while len(starts) < ncomp:
        starts.append(int(vel.size * (len(starts) + 1) / (ncomp + 1)))

    pars = lmfit.Parameters()
    pars.add("scale", value=max(abs(np.nanmax(work)), 1e-6), min=1e-12, max=1e6, vary=True)
    for i, idx in enumerate(sorted(starts)):
        pars.add(f"tex_{i}", value=float(np.clip(20.0, *tex_rng)), min=tex_rng[0], max=tex_rng[1])
        pars.add(f"tau_{i}", value=float(np.clip(-0.3, *tau_rng)), min=tau_rng[0], max=tau_rng[1])
        pars.add(f"voff_{i}", value=float(np.clip(vel[idx], *vc_rng)), min=vc_rng[0], max=vc_rng[1])
        pars.add(f"width_{i}", value=float(np.clip(30.0, *w_rng)), min=w_rng[0], max=w_rng[1])

    def residual(params):
        theta = []
        for i in range(ncomp):
            theta += [params[f"tex_{i}"].value, params[f"tau_{i}"].value,
                      params[f"voff_{i}"].value, params[f"width_{i}"].value]
        return (model(vel, params["scale"].value, *theta) - flux) / err

    fit = lmfit.minimize(residual, pars, method="least_squares", max_nfev=4000)
    best = fit.params
    theta = []
    for i in range(ncomp):
        theta += [best[f"tex_{i}"].value, best[f"tau_{i}"].value,
                  best[f"voff_{i}"].value, best[f"width_{i}"].value]
    model_flux = model(vel, best["scale"].value, *theta)
    resid = flux - model_flux
    rms = float(np.nanstd(resid))
    chi2 = float(np.nansum((resid / np.maximum(err, 1e-30)) ** 2))
    dof = int(flux.size - len(best))

    rows = []
    for i in range(ncomp):
        voff = float(best[f"voff_{i}"].value)
        width = float(best[f"width_{i}"].value)
        # velocity-integrated model flux of this component alone
        theta_i = [best[f"tex_{i}"].value, best[f"tau_{i}"].value, voff, width]
        single = model(vel, best["scale"].value, *theta_i, _ncomp=1)
        rows.append({
            "line": line,
            "component": f"c{i + 1}",
            "component_type": "emission" if np.nanmax(single) >= abs(np.nanmin(single)) else "absorption",
            "velocity_kms": voff,
            "fwhm_kms": width * 2.3548,
            "tex_K": float(best[f"tex_{i}"].value),
            "log_tau": float(best[f"tau_{i}"].value),
            "tau": float(10 ** best[f"tau_{i}"].value),
            "flux_integrated": float(np.trapezoid(np.abs(single), vel)),
            "snr": float(np.nanmax(np.abs(single)) / max(rms, 1e-30)),
            "detected": bool(np.nanmax(np.abs(single)) / max(rms, 1e-30)
                             >= float(cfg.get("snr_min", 3.0))),
        })

    import pandas as pd

    pd.DataFrame(rows).to_csv(outdir / "submm_lines.csv", index=False)
    pd.DataFrame({"velocity_kms": vel, "flux": flux, "err": err, "model": model_flux,
                  "residual": resid}).to_csv(outdir / "submm_model.csv", index=False)
    if cfg.get("plots", True):
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, (a0, a1) = plt.subplots(2, 1, figsize=(9, 6), sharex=True,
                                         gridspec_kw={"height_ratios": [3, 1]})
            a0.plot(vel, flux, "k", lw=0.8, label="data")
            a0.plot(vel, model_flux, "C3", lw=1.0, label=f"McFine {fit_type}")
            a0.set_ylabel("intensity")
            a0.legend()
            a1.plot(vel, resid, "C0", lw=0.7)
            a1.axhline(0, color="k", lw=0.5)
            a1.set_xlabel("velocity (km/s)")
            a1.set_ylabel("residual")
            fig.tight_layout()
            fig.savefig(outdir / "submm_fit.png", dpi=140)
            fig.savefig(outdir / "submm_fit.pdf")
            plt.close(fig)
        except Exception as exc:  # noqa: BLE001
            log(f"plot skipped: {exc}")

    run = {
        "tool": "submm_line", "status": "ok" if rows else "no_components",
        "source_key": args.source_key or src.stem, "spectrum": str(src),
        "axis": axis_kind, "ctype": ctype, "n_channels": int(flux.size),
        "redshift": z, "line": line, "rest_frequency_ghz": freq_rest,
        "rest_frequency_observed_ghz": nu_rest,
        "hyperfine_components": len(keys), "fit_type": fit_type,
        "fit": {"n_components": ncomp, "chi2": chi2, "dof": dof,
                "chi2nu": chi2 / dof if dof > 0 else None, "rms": rms,
                "scale": float(best["scale"].value), "success": bool(fit.success)},
        "components": rows,
        "limitations": [
            "LTE optical-depth model; RADEX non-LTE is available in McFine but not wired here.",
            "One velocity width per component (all hyperfine members share it).",
            "The Jy-per-K scale is a free nuisance parameter, not a physical filling factor.",
            "Hyperfine tables cover n2hp10, co21 and hi21cm only.",
        ],
    }
    (outdir / "run.json").write_text(json.dumps(run, indent=2) + "\n")
    (outdir / "config.effective.json").write_text(json.dumps(cfg, indent=2) + "\n")
    log(f"wrote {outdir} ({len(rows)} components, chi2/nu="
        f"{chi2 / dof if dof > 0 else float('nan'):.2f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
