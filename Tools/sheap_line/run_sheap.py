#!/usr/bin/env python3
"""SHEAP adapter for the canonical SDSS QSO inputs.

SHEAP (Avila-Vera et al., PyPI ``sheap``) is a JAX spectral-fitting code.  This
adapter runs it on the H-beta/[O III] 4959,5007 region of one SDSS spectrum and
writes:

    sheap_lines.csv          line fluxes, FWHM, velocities, components
    sheap_model.csv          rest-frame data / model / residual
    sheap_mc_samples.csv     the 50 Monte-Carlo draws of the derived lines
    sheap_fit.png/.pdf       data/model/residual figure
    sheap_fit_native.png     SHEAP's own component plot
    sheap_uncertainty.png/pdf histograms of the Monte-Carlo line posteriors
    sheap_comparison.csv     SHEAP vs sibling PyQSOFit/GANDALF/S3Fit fluxes
    sheap_ratio_comparison.csv
    run.json                 provenance, JAX device, controls, timings

Method labelling
----------------
* Optimiser: SHEAP's JAX gradient minimiser (Adam), not an MCMC sampler.
* Uncertainties: SHEAP's ``estimate_posteriors(sampling_method='montecarlo')``
  covariance-based draws (50 samples here).  This is a real MC propagation but
  **not** an MCMC posterior.
* SHEAP advertises GPU acceleration; this adapter runs on CPU
  (``JAX_PLATFORMS=cpu``).  ``run.json`` records the JAX devices actually used.

SHEAP is AGPL-3.0.  It is installed from PyPI inside the Docker image; no SHEAP
source is vendored in this MIT repository.  See the tool README.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
import traceback
import warnings
from pathlib import Path
from typing import Any

os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.io import fits
import jax

jax.config.update("jax_enable_x64", True)

from sheap import Sheapectral
from sheap import __version__ as SHEAP_VERSION

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)

FLUX_FACTOR = 1e-17
C_KMS = 299792.458

LINE_INFO = {
    "Hbeta": ("Hbeta", 4861.333),
    "OIIIc": ("OIII5007", 5006.803),
    "OIIIb": ("OIII4959", 4958.896),
    "HeIId": ("HeIId", 4685.710),
    "Halpha": ("Halpha", 6562.82),
    "NIIb": ("NII6585", 6583.45),
    "NIIa": ("NII6548", 6548.05),
}


def log(msg: str) -> None:
    print(msg, flush=True)


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return [jsonable(v) for v in value.tolist()]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def find_spectrum(path: Path) -> Path:
    if path.is_file():
        return path
    if not path.is_dir():
        raise FileNotFoundError(f"input path does not exist: {path}")
    files = sorted(path.glob("spec-*.fits"))
    if not files:
        files = sorted(path.rglob("spec-*.fits"))
    if not files:
        files = sorted(path.rglob("*.fits"))
    if not files:
        raise FileNotFoundError(f"no FITS spectrum in {path}")
    if len(files) > 1:
        log(f"[input] {len(files)} FITS files found; using {files[0].name}")
    return files[0]


def read_sdss(path: Path, mask_and_mask: bool) -> dict:
    with fits.open(path, memmap=False) as hdul:
        hdr0 = hdul[0].header
        table = None
        for hdu in hdul:
            if getattr(hdu, "columns", None) is None or hdu.data is None:
                continue
            names = {c.lower() for c in hdu.columns.names}
            if {"flux", "loglam"} <= names:
                table = hdu
                break
        if table is None:
            raise ValueError(f"{path}: expected an SDSS COADD table with FLUX/LOGLAM")
        data = table.data
        cols = {c.lower(): c for c in data.columns.names}
        flux = np.asarray(data[cols["flux"]], dtype=float)
        wave = 10.0 ** np.asarray(data[cols["loglam"]], dtype=float)
        ivar = np.asarray(data[cols["ivar"]], dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            fluxerr = 1.0 / np.sqrt(ivar)
        and_mask = np.asarray(data[cols["and_mask"]], dtype=int) if "and_mask" in cols else None
        z = ra = dec = None
        for key in ("Z", "z", "REDSHIFT"):
            if key in hdr0:
                z = float(hdr0[key])
                break
        for key in ("PLUG_RA", "RA"):
            if key in hdr0:
                ra = float(hdr0[key])
                break
        for key in ("PLUG_DEC", "DEC"):
            if key in hdr0:
                dec = float(hdr0[key])
                break
        try:
            spall = hdul["SPALL"].data
            if z is None:
                z = float(spall["Z"][0])
            if ra is None:
                ra = float(spall["PLUG_RA"][0])
            if dec is None:
                dec = float(spall["PLUG_DEC"][0])
        except Exception:
            pass
        bunit = str(hdr0.get("BUNIT", "")).upper().replace(" ", "")
    good = np.isfinite(wave) & np.isfinite(flux) & np.isfinite(fluxerr) & (fluxerr > 0)
    if mask_and_mask and and_mask is not None:
        good &= (and_mask == 0)
    if ivar is not None:
        good &= np.isfinite(ivar) & (ivar > 0)
    n_total = int(wave.size)
    wave, flux, fluxerr = wave[good], flux[good], fluxerr[good]
    if wave.size < 50:
        raise ValueError(f"{path}: only {wave.size} good pixels after masking")
    return {
        "path": str(path),
        "wave": wave,
        "flux": flux,
        "fluxerr": fluxerr,
        "z": z,
        "ra": ra,
        "dec": dec,
        "n_total": n_total,
        "n_good": int(wave.size),
        "bunit": bunit,
    }


def load_config(path: Path) -> dict:
    with path.open() as fh:
        cfg = json.load(fh)
    cfg.setdefault("sheap", {})
    cfg.setdefault("reference_tools", ["pyqsofit_uv", "gandalf_line", "s3fit_line"])
    return cfg


def region_indices(lines: list[str], wanted: str) -> int | None:
    try:
        return list(lines).index(wanted)
    except ValueError:
        return None


def build_line_table(best: dict, mc: dict, z: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Derive H-beta/[O III] line rows and the MC sample table."""
    bnames = [str(x) for x in best["broad"]["lines"]]
    nnames = [str(x) for x in best["narrow"]["lines"]]
    bflux = np.asarray(best["broad"]["flux"][0], dtype=float)
    nflux = np.asarray(best["narrow"]["flux"][0], dtype=float)
    bfwhm = np.asarray(best["broad"]["fwhm_kms"][0], dtype=float)
    nfwhm = np.asarray(best["narrow"]["fwhm_kms"][0], dtype=float)
    bcenter = np.asarray(best["broad"]["center"][0], dtype=float)
    ncenter = np.asarray(best["narrow"]["center"][0], dtype=float)

    mcb = np.asarray(mc["broad"]["flux"], dtype=float)      # (nsamp, nlines)
    mcn = np.asarray(mc["narrow"]["flux"], dtype=float)
    mcb_f = np.asarray(mc["broad"]["fwhm_kms"], dtype=float)
    mcn_f = np.asarray(mc["narrow"]["fwhm_kms"], dtype=float)
    nsamp = mcb.shape[0]

    ib_hb = region_indices(bnames, "Hbeta")
    ib_hei = region_indices(bnames, "HeIId")
    in_hb = region_indices(nnames, "Hbeta")
    in_o3c = region_indices(nnames, "OIIIc")
    in_o3b = region_indices(nnames, "OIIIb")
    in_hei = region_indices(nnames, "HeIId")

    samples = {}
    samples["Hbeta_broad"] = mcb[:, ib_hb] if ib_hb is not None else np.zeros(nsamp)
    samples["Hbeta_narrow"] = mcn[:, in_hb] if in_hb is not None else np.zeros(nsamp)
    samples["Hbeta_total"] = samples["Hbeta_broad"] + samples["Hbeta_narrow"]
    samples["OIII5007"] = mcn[:, in_o3c] if in_o3c is not None else np.zeros(nsamp)
    samples["OIII4959"] = mcn[:, in_o3b] if in_o3b is not None else np.zeros(nsamp)
    samples["Hbeta_OIII5007"] = np.divide(
        samples["Hbeta_total"], samples["OIII5007"],
        out=np.full(nsamp, np.nan), where=samples["OIII5007"] > 0)

    def qerr(arr):
        arr = np.asarray(arr, dtype=float)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return 0.0
        q16, q84 = np.quantile(arr, [0.16, 0.84])
        return float((q84 - q16) / 2.0)

    rows = []

    def add_line(canonical: str, sheap_name: str, component: str,
                 flux: float, fwhm: float, center: float,
                 mc_flux: np.ndarray, mc_fwhm: np.ndarray) -> None:
        flux_1e17 = float(flux) / FLUX_FACTOR
        err_1e17 = qerr(mc_flux) / FLUX_FACTOR
        snr = flux_1e17 / err_1e17 if err_1e17 > 0 else np.nan
        lam_ref = LINE_INFO.get(sheap_name, (canonical, center))[1]
        vel = (center / lam_ref - 1.0) * C_KMS if lam_ref else np.nan
        rows.append({
            "line": canonical,
            "sheap_line": sheap_name,
            "component": component,
            "lambda_rest": float(center),
            "flux_1e17": flux_1e17,
            "flux_err_1e17": err_1e17,
            "flux_erg_s_cm2": flux_1e17 * FLUX_FACTOR,
            "flux_err_erg_s_cm2": err_1e17 * FLUX_FACTOR,
            "fwhm_kms": float(fwhm),
            "fwhm_err_kms": float(np.nanstd(mc_fwhm)) if np.size(mc_fwhm) else np.nan,
            "velocity_kms": float(vel),
            "amplitude": np.nan,
            "snr": snr,
            "detected": bool(flux_1e17 > 0 and (not np.isfinite(snr) or snr >= 3.0)),
            "method": "sheap_jax_adam",
            "notes": ("SHEAP SPAF Gaussian; flux in cgs observed-frame "
                      "convention; 1-sigma from 50 covariance Monte-Carlo draws "
                      "(not MCMC)"),
        })

    for j, name in enumerate(bnames):
        if name == "Hbeta":
            add_line("Hbeta", name, "broad", bflux[j], bfwhm[j], bcenter[j],
                     samples["Hbeta_broad"], mcb_f[:, j])
        elif name == "HeIId":
            add_line("HeIId", name, "broad", bflux[j], bfwhm[j], bcenter[j],
                     mcb[:, j], mcb_f[:, j])
    for j, name in enumerate(nnames):
        if name == "Hbeta":
            add_line("Hbeta", name, "narrow", nflux[j], nfwhm[j], ncenter[j],
                     samples["Hbeta_narrow"], mcn_f[:, j])
        elif name == "OIIIc":
            add_line("OIII5007", name, "narrow", nflux[j], nfwhm[j], ncenter[j],
                     samples["OIII5007"], mcn_f[:, j])
        elif name == "OIIIb":
            add_line("OIII4959", name, "narrow", nflux[j], nfwhm[j], ncenter[j],
                     samples["OIII4959"], mcn_f[:, j])
        elif name == "HeIId":
            add_line("HeIId", name, "narrow", nflux[j], nfwhm[j], ncenter[j],
                     mcn[:, j], mcn_f[:, j])

    # Total rows for the comparison.
    for canonical, mc_name in [("Hbeta", "Hbeta_total"),
                               ("OIII5007", "OIII5007"),
                               ("OIII4959", "OIII4959")]:
        sub = [r for r in rows if r["line"] == canonical]
        if not sub:
            continue
        best_1e17 = float(sum(r["flux_1e17"] for r in sub))
        err_1e17 = qerr(samples[mc_name]) / FLUX_FACTOR
        pos = [r for r in sub if r["flux_1e17"] > 0]
        fwhm = (float(np.average([r["fwhm_kms"] for r in pos],
                                 weights=[r["flux_1e17"] for r in pos]))
                if pos else np.nan)
        rows.append({
            "line": canonical,
            "sheap_line": "+".join(r["sheap_line"] for r in sub),
            "component": "total",
            "lambda_rest": sub[0]["lambda_rest"],
            "flux_1e17": best_1e17,
            "flux_err_1e17": err_1e17,
            "flux_erg_s_cm2": best_1e17 * FLUX_FACTOR,
            "flux_err_erg_s_cm2": err_1e17 * FLUX_FACTOR,
            "fwhm_kms": fwhm,
            "fwhm_err_kms": np.nan,
            "velocity_kms": np.nan,
            "amplitude": np.nan,
            "snr": best_1e17 / err_1e17 if err_1e17 > 0 else np.nan,
            "detected": bool(best_1e17 > 0 and (err_1e17 <= 0 or best_1e17 / err_1e17 >= 3.0)),
            "method": "sheap_jax_adam",
            "notes": "sum of SHEAP components; MC errors propagated on the sum",
        })

    table = pd.DataFrame(rows)
    table = table.sort_values(["lambda_rest", "component"], na_position="last").reset_index(drop=True)
    sample_table = pd.DataFrame({
        "sample": np.arange(nsamp),
        "Hbeta_broad_1e17": samples["Hbeta_broad"] / FLUX_FACTOR,
        "Hbeta_narrow_1e17": samples["Hbeta_narrow"] / FLUX_FACTOR,
        "Hbeta_total_1e17": samples["Hbeta_total"] / FLUX_FACTOR,
        "OIII5007_1e17": samples["OIII5007"] / FLUX_FACTOR,
        "OIII4959_1e17": samples["OIII4959"] / FLUX_FACTOR,
        "Hbeta_OIII5007": samples["Hbeta_OIII5007"],
    })
    return table, sample_table


def write_model(sc, out: Path) -> None:
    try:
        wave = np.asarray(sc.spectra[0, 0, :], dtype=float)
        flux = np.asarray(sc.spectra[0, 1, :], dtype=float)
        err = np.asarray(sc.spectra[0, 2, :], dtype=float)
        params = np.asarray(sc.result.params[0], dtype=float)
        model = np.asarray(sc.spectral_model(wave, params), dtype=float)
        pd.DataFrame({
            "wave_rest": wave,
            "flux": flux,
            "flux_err": err,
            "model": model,
            "residual": flux - model,
        }).to_csv(out / "sheap_model.csv", index=False)
    except Exception as exc:  # noqa: BLE001
        log(f"[warn] could not write sheap_model.csv: {exc}")


def plot_fit(sc, table: pd.DataFrame, out: Path) -> None:
    # SHEAP's own component plot.
    try:
        sc.modelplot.plot(0, save=str(out / "sheap_fit_native.png"),
                          add_lines_name=True)
    except Exception as exc:  # noqa: BLE001
        log(f"[warn] native SHEAP plot failed: {exc}")
    # Compact data/model/residual figure from the native model arrays.
    if not (out / "sheap_model.csv").exists():
        return
    d = pd.read_csv(out / "sheap_model.csv")
    wave_all = d["wave_rest"].values
    xmin, xmax = 4580.0, 5160.0
    sel = (wave_all >= xmin) & (wave_all <= xmax)
    d = d.loc[sel].reset_index(drop=True)
    wave = d["wave_rest"].values
    fig, axs = plt.subplots(2, 1, figsize=(12, 7), sharex=True,
                            gridspec_kw={"height_ratios": [2.2, 1.0], "hspace": 0.05})
    ax = axs[0]
    ax.plot(wave, d["flux"], color="0.15", lw=0.8, label="SDSS data")
    ax.fill_between(wave, d["flux"] - d["flux_err"], d["flux"] + d["flux_err"],
                    color="0.7", alpha=0.35, linewidth=0)
    ax.plot(wave, d["model"], color="r", ls="--", lw=1.2, label="SHEAP model")
    for x, label in [(4861.333, r"H$\beta$"), (4958.896, "[O III] 4959"),
                     (5006.803, "[O III] 5007")]:
        ax.axvline(x, color="0.4", lw=0.7, ls="-.")
        ax.text(x, ax.get_ylim()[1], label, rotation=90, va="top",
                ha="right", fontsize=8, color="0.3")
    ax.set_xlim(xmin, xmax)
    ax.set_ylabel(r"$f_\lambda$ (erg s$^{-1}$ cm$^{-2}$ $\AA^{-1}$)")
    chi2 = float(np.asarray(sc.result.chi2_red)[0])
    ax.set_title(f"SHEAP JAX/Adam fit (CPU)  z={float(sc.z[0]):.6f}  "
                 f"$\\chi^2_r$={chi2:.2f}")
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    ax.grid(alpha=0.2, ls=":")
    ax2 = axs[1]
    resid = d["residual"] / d["flux_err"]
    ax2.axhline(0, color="0.3", lw=0.7, ls=":")
    ax2.plot(wave, resid, color="tab:blue", lw=0.8)
    ax2.set_ylabel("residual / error")
    ax2.set_xlabel(r"Rest-frame wavelength ($\AA$)")
    ax2.set_xlim(xmin, xmax)
    ax2.grid(alpha=0.2, ls=":")
    fig.savefig(out / "sheap_fit.png", dpi=170, bbox_inches="tight")
    fig.savefig(out / "sheap_fit.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_uncertainty(sample_table: pd.DataFrame, out: Path, nsamp: int) -> dict:
    specs = [
        ("Hbeta_total_1e17", r"H$\beta$ total"),
        ("OIII5007_1e17", "[O III] 5007"),
        ("Hbeta_OIII5007", r"H$\beta$ / [O III] 5007"),
    ]
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.2))
    summary = {}
    for ax, (col, label) in zip(axs, specs):
        vals = sample_table[col].dropna().values
        q16, q50, q84 = np.quantile(vals, [0.16, 0.50, 0.84])
        err = (q84 - q16) / 2.0
        summary[col] = {"median": float(q50), "err_1sigma": float(err),
                        "q16": float(q16), "q84": float(q84),
                        "n_samples": int(vals.size)}
        ax.hist(vals, bins=12, color="tab:blue", alpha=0.75, edgecolor="white")
        ax.axvline(q16, color="0.3", ls="--", lw=1)
        ax.axvline(q50, color="k", lw=1.2)
        ax.axvline(q84, color="0.3", ls="--", lw=1)
        ax.set_title(f"{label}\n{q50:.3g} ± {err:.3g}", fontsize=10)
        ax.set_xlabel(label)
        ax.grid(alpha=0.2, ls=":")
    fig.suptitle(f"SHEAP covariance Monte-Carlo draws ({nsamp} samples; not MCMC)",
                 y=1.02, fontsize=11)
    fig.tight_layout()
    fig.savefig(out / "sheap_uncertainty.png", dpi=170, bbox_inches="tight")
    fig.savefig(out / "sheap_uncertainty.pdf", bbox_inches="tight")
    plt.close(fig)
    return summary


def _to_float(value: Any) -> float | None:
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def read_reference(reference: Path, tool: str) -> dict:
    out: dict[str, tuple[float | None, float | None]] = {}
    if tool == "pyqsofit_uv":
        path = reference / "pyqsofit_uv" / "pyqsofit_lines.csv"
        if not path.exists():
            return out
        rows = list(csv.DictReader(path.open()))
        hb = [r for r in rows if r["line"] in ("Hb_br", "Hb_na")]
        o3 = [r for r in rows if r["line"] in ("OIII5007w", "OIII5007c")]
        if hb:
            out["Hbeta"] = (sum(_to_float(r["area_1e17"]) or 0.0 for r in hb), None)
        if o3:
            out["OIII5007"] = (sum(_to_float(r["area_1e17"]) or 0.0 for r in o3), None)
    elif tool == "gandalf_line":
        path = reference / "gandalf_line" / "gandalf_lines.csv"
        if not path.exists():
            return out
        rows = list(csv.DictReader(path.open()))
        for canon, names in [("Hbeta", ("Hbeta",)), ("OIII5007", ("[OIII]5007",))]:
            sub = [r for r in rows if r.get("line") in names]
            if not sub:
                continue
            total = [r for r in sub if r.get("component") == "total"]
            use = total[0] if total else sub[0]
            out[canon] = (_to_float(use.get("flux_1e17")),
                          _to_float(use.get("flux_err_1e17")))
    elif tool == "s3fit_line":
        path = reference / "s3fit_line" / "s3fit_lines.csv"
        if not path.exists():
            return out
        rows = list(csv.DictReader(path.open()))
        for canon, names in [("Hbeta", ("H-beta", "Hbeta")),
                             ("OIII5007", ("[O III]:5008", "[OIII]5007"))]:
            sub = [r for r in rows if r.get("line") in names]
            if not sub:
                continue
            total = [r for r in sub if r.get("component") == "total"]
            use = total[0] if total else sub[0]
            out[canon] = (_to_float(use.get("flux_1e17")),
                          _to_float(use.get("flux_err_1e17")))
    return out


def write_comparison(table: pd.DataFrame, reference: Path, tools: list[str],
                     out: Path) -> dict:
    qg = {}
    for line in ("Hbeta", "OIII5007"):
        sub = table[(table["line"] == line) & (table["component"] == "total")]
        if sub.empty:
            sub = table[table["line"] == line]
        if not sub.empty:
            r = sub.iloc[0]
            qg[line] = (float(r["flux_1e17"]), float(r["flux_err_1e17"]))
    rows, ratios = [], []
    qg_ratio = qg_ratio_err = None
    if "Hbeta" in qg and "OIII5007" in qg and qg["OIII5007"][0] > 0:
        qg_ratio = qg["Hbeta"][0] / qg["OIII5007"][0]
        qg_ratio_err = abs(qg_ratio) * math.sqrt(
            (qg["Hbeta"][1] / qg["Hbeta"][0]) ** 2 +
            (qg["OIII5007"][1] / qg["OIII5007"][0]) ** 2)
        ratios.append({"ratio": "Hbeta/OIII5007", "tool": "sheap_line",
                       "value": qg_ratio, "err": qg_ratio_err})
    for tool in tools:
        ref = read_reference(reference, tool)
        for line in ("Hbeta", "OIII5007"):
            if line not in qg or line not in ref:
                continue
            qv, qe = qg[line]
            rv, re = ref[line]
            rows.append({
                "line": line,
                "sheap_1e17": qv,
                "sheap_err_1e17": qe,
                "reference_tool": tool,
                "reference_1e17": rv,
                "reference_err_1e17": re,
                "ratio_sheap_over_reference": qv / rv if rv else None,
                "notes": "SHEAP fluxes are observed-frame cgs / 1e-17; "
                         "reference values are the siblings' published tables",
            })
        if "Hbeta" in ref and "OIII5007" in ref and ref["OIII5007"][0]:
            hv, he = ref["Hbeta"]
            ov, oe = ref["OIII5007"]
            val = hv / ov
            err = None
            if he and oe:
                err = abs(val) * math.sqrt((he / hv) ** 2 + (oe / ov) ** 2)
            ratios.append({"ratio": "Hbeta/OIII5007", "tool": tool,
                           "value": val, "err": err})
    pd.DataFrame(rows).to_csv(out / "sheap_comparison.csv", index=False)
    pd.DataFrame(ratios).to_csv(out / "sheap_ratio_comparison.csv", index=False)
    return {
        "sheap_hbeta_oiii5007": qg_ratio,
        "sheap_hbeta_oiii5007_err": qg_ratio_err,
        "references": rows,
        "ratios": ratios,
    }


def run(args) -> int:
    t0 = time.time()
    cfg = load_config(Path(args.config))
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    spectrum_path = find_spectrum(Path(args.input))
    spec = read_sdss(spectrum_path, bool(cfg.get("mask_and_mask", True)))
    z = args.z if args.z is not None else cfg.get("z")
    if z is None:
        z = spec.get("z")
    if z is None:
        raise ValueError("redshift not supplied and not found in the FITS header")
    z = float(z)
    name = args.name or "sheap"

    scfg = dict(cfg.get("sheap", {}))
    region = tuple(scfg.get("region_rest", [4600.0, 5150.0]))
    n_broad = int(scfg.get("n_broad", 1))
    n_narrow = int(scfg.get("n_narrow", 1))
    fe_mode = str(scfg.get("fe_mode", "None"))
    cont_profile = str(scfg.get("continuum_profile", "brokenpowerlaw"))
    add_balmer = bool(scfg.get("add_balmer_continuum", False))
    add_balmer_hi = bool(scfg.get("add_balmerhighorder_continuum", False))
    num_steps = int(scfg.get("num_steps", 1000))
    lr = float(scfg.get("learning_rate", 1e-2))
    method = str(scfg.get("method", "adam"))
    profile = str(scfg.get("profile", "gaussian"))
    cov = bool(scfg.get("covariance_error", True))
    n_mc = int(scfg.get("montecarlo_samples", 50))
    seed = int(scfg.get("seed", 42))

    log(f"[sheap] input={spectrum_path}")
    log(f"[sheap] z={z:.8f} region={region} n_broad={n_broad} n_narrow={n_narrow}")
    log(f"[sheap] good pixels={spec['n_good']}/{spec['n_total']} "
        f"rest range={spec['wave'].min()/(1+z):.1f}-"
        f"{spec['wave'].max()/(1+z):.1f} A")

    # SHEAP expects (n_objects, 3, n_pixels).  The PyPI wheel (0.0.11) does
    # not add the object axis itself.
    arr = np.array([spec["wave"],
                    spec["flux"] * FLUX_FACTOR,
                    spec["fluxerr"] * FLUX_FACTOR])[None, :, :]
    sc = Sheapectral(
        arr, z=z, coords=None, names=[name],
        extinction_correction="done", redshift_correction="pending")
    sc.makemodel(
        region, n_broad=n_broad, n_narrow=n_narrow, fe_mode=fe_mode,
        continuum_profile=cont_profile, verbose=False,
        add_balmer_continuum=add_balmer,
        add_balmerhighorder_continuum=add_balmer_hi)
    sc.fitmodel(list_num_steps=[num_steps], list_learning_rate=[lr],
                method=method, profile=profile, covariance_error=cov)
    chi2 = float(np.asarray(sc.result.chi2_red)[0])
    log(f"[sheap] fit completed chi2_r={chi2:.3f}")
    sc.estimate_posteriors(sampling_method="single", summarize=False)
    best = sc.result.posterior["single"]["posterior_result"][name]["basic_params"]
    log(f"[sheap] Monte-Carlo covariance draws: {n_mc}")
    sc.estimate_posteriors(sampling_method="montecarlo", num_samples=n_mc,
                           key_seed=seed, summarize=False, overwrite=True)
    mc = sc.result.posterior["montecarlo"]["posterior_result"][name]["basic_params"]
    table, sample_table = build_line_table(best, mc, z)
    table.to_csv(out / "sheap_lines.csv", index=False)
    sample_table.to_csv(out / "sheap_mc_samples.csv", index=False)
    write_model(sc, out)
    plot_fit(sc, table, out)
    unc = plot_uncertainty(sample_table, out, n_mc)
    comparison = write_comparison(
        table, Path(args.reference) if args.reference else Path("/nonexistent"),
        list(cfg.get("reference_tools", [])), out)

    hb = table[(table["line"] == "Hbeta") & (table["component"] == "total")]
    hbb = table[(table["line"] == "Hbeta") & (table["component"] == "broad")]
    o3 = table[(table["line"] == "OIII5007") & (table["component"] == "total")]
    line_summary = {
        "n_rows": int(len(table)),
        "n_detected": int(table["detected"].sum()),
        "Hbeta_total_1e17": float(hb.iloc[0]["flux_1e17"]) if not hb.empty else None,
        "Hbeta_broad_1e17": float(hbb.iloc[0]["flux_1e17"]) if not hbb.empty else None,
        "OIII5007_total_1e17": float(o3.iloc[0]["flux_1e17"]) if not o3.empty else None,
        "Hbeta_OIII5007": comparison.get("sheap_hbeta_oiii5007"),
        "Hbeta_OIII5007_err": comparison.get("sheap_hbeta_oiii5007_err"),
        "Hbeta_broad_fwhm_kms": float(hbb.iloc[0]["fwhm_kms"]) if not hbb.empty else None,
    }
    import numpy as _np
    import scipy as _scipy
    import pandas as _pd
    import astropy as _astropy
    import jaxlib as _jaxlib
    versions = {
        "python": sys.version.split()[0],
        "sheap": SHEAP_VERSION,
        "jax": jax.__version__,
        "jaxlib": getattr(_jaxlib, "__version__", None),
        "numpy": _np.__version__,
        "scipy": _scipy.__version__,
        "pandas": _pd.__version__,
        "astropy": _astropy.__version__,
        "matplotlib": matplotlib.__version__,
    }
    run = {
        "tool": "sheap_line",
        "method": "sheap_jax_adam",
        "native_code": "SHEAP 0.0.11 (PyPI), AGPL-3.0",
        "versions": versions,
        "jax_devices": [str(d) for d in jax.devices()],
        "accelerator": "CPU (JAX_PLATFORMS=cpu)",
        "input": {
            "file": str(spectrum_path),
            "z": z,
            "ra": spec.get("ra"),
            "dec": spec.get("dec"),
            "n_pixels_total": spec["n_total"],
            "n_pixels_used": spec["n_good"],
            "wave_obs_range_A": [float(spec["wave"].min()), float(spec["wave"].max())],
            "wave_rest_range_A": [float(spec["wave"].min() / (1 + z)),
                                   float(spec["wave"].max() / (1 + z))],
            "flux_unit": "1e-17 erg s-1 cm-2 A-1",
            "bunit_header": spec["bunit"],
            "mask_and_mask": bool(cfg.get("mask_and_mask", True)),
        },
        "config_file": str(Path(args.config)),
        "model": {
            "region_rest_A": list(region),
            "n_broad": n_broad,
            "n_narrow": n_narrow,
            "fe_mode": fe_mode,
            "continuum_profile": cont_profile,
            "add_balmer_continuum": add_balmer,
            "add_balmerhighorder_continuum": add_balmer_hi,
            "line_profile": profile,
        },
        "fit": {
            "optimizer": method,
            "num_steps": num_steps,
            "learning_rate": lr,
            "covariance_error": cov,
            "chi2_red": chi2,
            "n_params": int(np.asarray(sc.result.params).shape[-1]),
        },
        "statistical_mode": {
            "method": "covariance Monte-Carlo draws",
            "n_samples": n_mc,
            "seed": seed,
            "mcmc": False,
            "note": ("SHEAP's 'montecarlo' sampler draws from the fit "
                     "covariance.  It is not an MCMC posterior."),
            "derived_quantiles": unc,
        },
        "line_fit": line_summary,
        "comparison": comparison,
        "runtime": {"total_sec": time.time() - t0},
        "scope": {
            "accelerator": "CPU; GPU not used",
            "galactic_dereddening": False,
            "fe_ii": fe_mode,
            "host_galaxy": False,
            "balmer_continuum": add_balmer or add_balmer_hi,
            "region": "H-beta + [O III] 4959/5007 only",
            "fit_quality_note": ("For this luminous QSO SHEAP's H-beta/[O III] "
                                 "fit has a high reduced chi2 and broad H-beta "
                                 "is much wider than in PyQSOFit/GANDALF/S3Fit. "
                                 "The result is reported as a real SHEAP fit, "
                                 "not as a preferred measurement."),
        },
        "line_measurements": table.to_dict(orient="records"),
    }
    with (out / "run.json").open("w") as fh:
        json.dump(jsonable(run), fh, indent=2)
    log(f"[sheap] done in {run['runtime']['total_sec']:.1f}s -> {out}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--config", default="/app/config/config.json")
    p.add_argument("--z", type=float, default=None)
    p.add_argument("--name", default="sheap")
    p.add_argument("--reference", default=None)
    args = p.parse_args(argv)
    try:
        return run(args)
    except Exception as exc:  # noqa: BLE001
        log(f"[sheap] ERROR: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
