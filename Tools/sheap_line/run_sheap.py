#!/usr/bin/env python3
"""SHEAP adapter for the canonical SDSS QSO inputs.

SHEAP (Avila-Vera et al., PyPI ``sheap``) is a JAX spectral-fitting code.  This
adapter runs it on the rest-frame H-beta/[O III] 4959,5007 region of one SDSS
spectrum and writes:

    sheap_lines.csv          line fluxes, FWHM, velocities, components, totals
    sheap_model.csv          rest-frame data / total model / residual / components
    sheap_mc_samples.csv     the parametric-bootstrap MC draws of the lines
    sheap_fit.png/.pdf       full-region data/model/component/residual figure
    sheap_zoom_hbeta.png/pdf H-beta zoom (data/model/components/residual)
    sheap_zoom_oiii.png/pdf  [O III] 4959/5007 zoom
    sheap_residual.png/pdf   residual/sigma over the fitted region
    sheap_fit_native.png     SHEAP's own component plot
    sheap_uncertainty.png/pdf histograms of the MC line posteriors
    sheap_comparison.csv     SHEAP vs sibling PyQSOFit/GANDALF/S3Fit fluxes
    sheap_ratio_comparison.csv
    sheap_systematics.csv    optional model-variant ensemble (``--variants``)
    run.json                 provenance, model, fit, quality gates, timings

Method labelling
----------------
* Optimiser: SHEAP's JAX gradient minimiser (Adam), not an MCMC sampler.
* ``estimate_posteriors(sampling_method='montecarlo')`` is a **parametric
  bootstrap**: SHEAP resamples every pixel from the observed flux and its
  1-sigma error, then re-runs the JAX optimiser.  It is not an MCMC posterior
  and it is not a draw from the fit covariance.
* ``covariance_error=True`` separately computes SHEAP's local JAX
  Jacobian/JTJ parameter covariance.  The two estimates answer different
  questions and are both recorded in ``run.json``.
* SHEAP advertises GPU acceleration; this adapter runs on CPU
  (``JAX_PLATFORMS=cpu``).  ``run.json`` records the JAX devices actually used.

Production model (2026 audit)
-----------------------------
The original adapter fitted rest-frame 4600-5150 A with one narrow component,
no Fe II and SHEAP's default 600 km/s narrow-FWHM cap.  For this luminous QSO
that model cannot describe the spectrum: chi2_nu ~= 46, the narrow component
saturates at 592 km/s while the observed [O III] lines are ~950 km/s wide, and
the broad H-beta is pushed to +1877 km/s (near its +2000 km/s bound) to fill
the [O III] wings.  The result was H-beta/[O III] 5007 = 4.00.

The production model is the data-driven correction: a wider rest-frame
4450-5450 A window (constrains the continuum and Fe II), two narrow SPAF
components (NLR core plus a blueshifted [O III] wing), one broad H-beta/He II
component, the SHEAP Fe II UV/optical template, and a power-law continuum.
The narrow-FWHM prior is widened to 2000 km/s so it is not active.  This model
gives chi2_nu ~= 2.9 and H-beta/[O III] 5007 ~= 2.03, consistent with
PyQSOFit/GANDALF/S3Fit.  See ``docs/SHEAP_ASSESSMENT.md``.

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

# SHEAP line name -> (canonical name, laboratory rest wavelength [A]).
CANONICAL_LINES = {
    "Hgamma": ("Hgamma", 4340.471),
    "Hg": ("Hgamma", 4340.471),
    "OIIIa": ("OIII4363", 4363.209),
    "HeId": ("HeI4471", 4471.479),
    "HeIId": ("HeIId", 4685.710),
    "Hbeta": ("Hbeta", 4861.333),
    "OIIIb": ("OIII4959", 4958.896),
    "OIIIc": ("OIII5007", 5006.803),
    "Halpha": ("Halpha", 6562.820),
    "NIIb": ("NII6585", 6583.450),
    "NIIa": ("NII6548", 6548.050),
}

DEFAULT_REGION = (4450.0, 5450.0)
DEFAULT_GATES = {
    "max_chi2_red": 8.0,
    "ratio_min": 1.8,
    "ratio_max": 2.5,
    "max_broad_hbeta_fwhm_kms": 7000.0,
    "max_reference_deviation": 0.30,
    "min_reference_tools": 2,
    "oiii_doublet_min": 2.5,
    "oiii_doublet_max": 3.8,
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


def _as_list(value: Any, cast=float) -> list:
    if isinstance(value, (list, tuple)):
        return [cast(v) for v in value]
    return [cast(value)]


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
    gates = dict(DEFAULT_GATES)
    gates.update(cfg.get("quality_gates", {}))
    cfg["quality_gates"] = gates
    return cfg


def make_spectra_array(spec: dict) -> np.ndarray:
    """SHEAP expects (n_objects, 3, n_pixels); the 0.0.11 wheel does not add it."""
    return np.array([spec["wave"],
                     spec["flux"] * FLUX_FACTOR,
                     spec["fluxerr"] * FLUX_FACTOR])[None, :, :]


def build_sheap(spec: dict, z: float, name: str, scfg: dict) -> Sheapectral:
    sc = Sheapectral(
        make_spectra_array(spec), z=z, coords=None, names=[name],
        extinction_correction="done", redshift_correction="pending")
    region = tuple(scfg.get("region_rest", DEFAULT_REGION))
    sc.makemodel(
        region,
        n_broad=int(scfg.get("n_broad", 1)),
        n_narrow=int(scfg.get("n_narrow", 2)),
        fe_mode=str(scfg.get("fe_mode", "template")),
        continuum_profile=str(scfg.get("continuum_profile", "powerlaw")),
        verbose=False,
        add_outflow=bool(scfg.get("add_outflow", False)),
        add_balmer_continuum=bool(scfg.get("add_balmer_continuum", False)),
        add_balmerhighorder_continuum=bool(scfg.get("add_balmerhighorder_continuum", False)),
    )
    return sc


def fit_sheap(sc: Sheapectral, scfg: dict) -> tuple[float, list[int], list[float]]:
    steps = _as_list(scfg.get("num_steps", 4000), int)
    lrs = _as_list(scfg.get("learning_rate", 1e-2), float)
    if len(steps) != len(lrs):
        raise ValueError("num_steps and learning_rate must have the same length")
    sc.fitmodel(
        list_num_steps=steps,
        list_learning_rate=lrs,
        method=str(scfg.get("method", "adam")),
        profile=str(scfg.get("profile", "gaussian")),
        covariance_error=bool(scfg.get("covariance_error", True)),
        limits_overrides=dict(scfg.get("limits_overrides", {})),
    )
    return float(np.asarray(sc.result.chi2_red)[0]), steps, lrs


def component_labels(sc: Sheapectral) -> list[str]:
    labels: list[str] = []
    for i, sp in enumerate(getattr(sc.result, "region_list", [])):
        region = getattr(sp, "region", "")
        line = getattr(sp, "line_name", f"component{i}")
        comp = getattr(sp, "component", 0)
        if region == "continuum":
            labels.append(f"continuum:{getattr(sp, 'profile', '')}")
        elif region == "fe":
            labels.append("FeII template")
        elif region in ("broad", "narrow", "outflow", "winds", "bal"):
            labels.append(f"SPAF {region}{comp}")
        else:
            labels.append(f"{line} {region}")
    return labels


def _qerr(arr: np.ndarray) -> float:
    arr = np.asarray(arr, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return 0.0
    q16, q84 = np.quantile(arr, [0.16, 0.84])
    return float((q84 - q16) / 2.0)


def build_line_table(best: dict, mc: dict, z: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Derive component/total line rows and the MC sample table.

    ``best`` and ``mc`` are SHEAP ``basic_params`` dictionaries.  ``mc`` may be
    the one-sample ``single`` posterior (used for model variants); in that case
    the errors are zero and only the best-fit fluxes matter.
    """
    entries: list[dict] = []
    nsamp = 1
    for region_key in ("broad", "narrow", "outflow", "winds", "bal"):
        if region_key not in best:
            continue
        b = best[region_key]
        names = [str(x) for x in b["lines"]]
        comps = [int(x) for x in b.get("component", [0] * len(names))]
        flux = np.asarray(b["flux"][0], dtype=float)
        fwhm = np.asarray(b["fwhm_kms"][0], dtype=float)
        center = np.asarray(b["center"][0], dtype=float)
        amp = np.asarray(b.get("amplitude", np.full(len(names), np.nan))[0], dtype=float)
        mflux = np.asarray(mc[region_key]["flux"], dtype=float)
        mfwhm = np.asarray(mc[region_key]["fwhm_kms"], dtype=float)
        mamp = np.asarray(mc[region_key].get("amplitude", np.full_like(mflux, np.nan)), dtype=float)
        nsamp = max(nsamp, mflux.shape[0])
        for j, sheap_name in enumerate(names):
            if sheap_name in CANONICAL_LINES:
                canonical, lam_lab = CANONICAL_LINES[sheap_name]
            else:
                canonical, lam_lab = sheap_name, float(center[j])
            comp_label = f"{region_key}{comps[j]}" if region_key != "broad" else "broad"
            if region_key == "narrow" and len(set(comps)) == 1:
                comp_label = "narrow"
            entries.append({
                "line": canonical,
                "sheap_line": sheap_name,
                "component": comp_label,
                "component_index": comps[j],
                "lambda_lab": float(lam_lab),
                "lambda_rest": float(center[j]),
                "flux_1e17": float(flux[j]) / FLUX_FACTOR,
                "fwhm_kms": float(fwhm[j]),
                "velocity_kms": (float(center[j]) / lam_lab - 1.0) * C_KMS if lam_lab else np.nan,
                "amplitude_1e17": float(amp[j]) / FLUX_FACTOR if np.isfinite(amp[j]) else np.nan,
                "mc_flux": mflux[:, j] / FLUX_FACTOR,
                "mc_fwhm": mfwhm[:, j],
                "mc_amp": mamp[:, j] / FLUX_FACTOR if np.size(mamp) else np.full(nsamp, np.nan),
                "notes": ("SHEAP SPAF Gaussian; rest-frame f_lambda; 1-sigma from "
                          f"{mflux.shape[0]}-sample parametric-bootstrap MC (spectrum "
                          "resampling + re-optimisation, not MCMC)"),
            })

    rows: list[dict] = []
    for e in entries:
        err = _qerr(e["mc_flux"])
        snr = e["flux_1e17"] / err if err > 0 else np.nan
        rows.append({
            "line": e["line"],
            "sheap_line": e["sheap_line"],
            "component": e["component"],
            "component_index": e["component_index"],
            "lambda_rest": e["lambda_rest"],
            "lambda_lab": e["lambda_lab"],
            "flux_1e17": e["flux_1e17"],
            "flux_err_1e17": err,
            "flux_erg_s_cm2": e["flux_1e17"] * FLUX_FACTOR,
            "flux_err_erg_s_cm2": err * FLUX_FACTOR,
            "fwhm_kms": e["fwhm_kms"],
            "fwhm_err_kms": float(np.nanstd(e["mc_fwhm"])) if e["mc_fwhm"].size > 1 else np.nan,
            "velocity_kms": e["velocity_kms"],
            "amplitude_1e17": e["amplitude_1e17"],
            "snr": snr,
            "detected": bool(e["flux_1e17"] > 0 and (not np.isfinite(snr) or snr >= 3.0)),
            "method": "sheap_jax_adam",
            "notes": e["notes"],
        })

    # Totals are sums over every component of the same canonical line.
    totals: dict[str, tuple[float, float, float, float]] = {}
    for canonical in sorted({e["line"] for e in entries}):
        sub = [e for e in entries if e["line"] == canonical]
        if not sub:
            continue
        best_total = float(sum(e["flux_1e17"] for e in sub))
        mc_total = np.sum([e["mc_flux"] for e in sub], axis=0)
        err_total = _qerr(mc_total)
        pos = [e for e in sub if e["flux_1e17"] > 0]
        fwhm_total = (float(np.average([e["fwhm_kms"] for e in pos],
                                       weights=[e["flux_1e17"] for e in pos]))
                      if pos else np.nan)
        snr_total = best_total / err_total if err_total > 0 else np.nan
        rows.append({
            "line": canonical,
            "sheap_line": "+".join(sorted({e["sheap_line"] for e in sub})),
            "component": "total",
            "component_index": 0,
            "lambda_rest": float(np.average([e["lambda_rest"] for e in sub],
                                            weights=[max(e["flux_1e17"], 0) for e in sub]))
            if best_total > 0 else sub[0]["lambda_rest"],
            "lambda_lab": sub[0]["lambda_lab"],
            "flux_1e17": best_total,
            "flux_err_1e17": err_total,
            "flux_erg_s_cm2": best_total * FLUX_FACTOR,
            "flux_err_erg_s_cm2": err_total * FLUX_FACTOR,
            "fwhm_kms": fwhm_total,
            "fwhm_err_kms": np.nan,
            "velocity_kms": np.nan,
            "amplitude_1e17": np.nan,
            "snr": snr_total,
            "detected": bool(best_total > 0 and (err_total <= 0 or snr_total >= 3.0)),
            "method": "sheap_jax_adam",
            "notes": f"sum of {len(sub)} SHEAP component(s); MC errors propagated on the sum",
        })
        totals[canonical] = (best_total, err_total, fwhm_total, snr_total)

    table = pd.DataFrame(rows)
    table = table.sort_values(["lambda_lab", "component"], na_position="last").reset_index(drop=True)

    # Sample table: one column per component plus the standard totals.
    sample = {"sample": np.arange(nsamp)}
    for e in entries:
        key = f"{e['line']}_{e['component']}_1e17".replace(" ", "")
        sample[key] = e["mc_flux"]
    for canonical in ("Hbeta", "OIII5007", "OIII4959", "HeIId", "HeI4471"):
        sub = [e for e in entries if e["line"] == canonical]
        if sub:
            sample[f"{canonical}_total_1e17"] = np.sum([e["mc_flux"] for e in sub], axis=0)
    if "Hbeta_total_1e17" in sample and "OIII5007_total_1e17" in sample:
        sample["Hbeta_OIII5007"] = np.divide(
            sample["Hbeta_total_1e17"], sample["OIII5007_total_1e17"],
            out=np.full(nsamp, np.nan), where=sample["OIII5007_total_1e17"] > 0)
    if "OIII5007_total_1e17" in sample and "OIII4959_total_1e17" in sample:
        sample["OIII5007_OIII4959"] = np.divide(
            sample["OIII5007_total_1e17"], sample["OIII4959_total_1e17"],
            out=np.full(nsamp, np.nan), where=sample["OIII4959_total_1e17"] > 0)
    hb_broad = [e["mc_flux"] for e in entries if e["line"] == "Hbeta" and e["component"] == "broad"]
    hb_narrow = [e["mc_flux"] for e in entries if e["line"] == "Hbeta" and e["component"].startswith("narrow")]
    if hb_broad:
        sample["Hbeta_broad_1e17"] = np.sum(hb_broad, axis=0)
    if hb_narrow:
        sample["Hbeta_narrow_1e17"] = np.sum(hb_narrow, axis=0)
    sample_table = pd.DataFrame(sample)
    return table, sample_table


def write_model(sc: Sheapectral, region: tuple[float, float], out: Path) -> tuple[pd.DataFrame, list[str]]:
    """Write data/model/residual and every component, restricted to the fit region.

    The previous adapter evaluated SHEAP's *local* model over the full
    2247-6510 A spectrum.  A local power law extrapolated that far is meaningless
    and made the residual plot look far worse than the actual fit.  Only the
    fitted pixels are written here.
    """
    wave = np.asarray(sc.spectra[0, 0, :], dtype=float)
    flux = np.asarray(sc.spectra[0, 1, :], dtype=float)
    err = np.asarray(sc.spectra[0, 2, :], dtype=float)
    params = np.asarray(sc.result.params[0], dtype=float)
    model = np.asarray(sc.spectral_model(wave, params), dtype=float)

    mask = np.asarray(sc.result.mask[0], dtype=bool)
    sel = (~mask) & (wave >= region[0]) & (wave <= region[1])
    labels = component_labels(sc)
    df = pd.DataFrame({
        "wave_rest": wave[sel],
        "flux": flux[sel],
        "flux_err": err[sel],
        "model": model[sel],
        "residual": flux[sel] - model[sel],
        "residual_sigma": (flux[sel] - model[sel]) / err[sel],
    })
    fused = sc.spectral_model
    splits = getattr(fused, "param_splits", None)
    subs = getattr(fused, "sub_funcs", None)
    if splits is not None and subs is not None:
        for i, fn in enumerate(subs):
            p_i = params[splits[i]:splits[i + 1]]
            y = np.asarray(fn(wave, p_i), dtype=float)
            label = labels[i] if i < len(labels) else f"component{i}"
            df[f"component_{i:03d}"] = y[sel]
    df.to_csv(out / "sheap_model.csv", index=False)
    return df, labels


def _comp_columns(labels: list[str]) -> list[tuple[str, str]]:
    out = []
    for i, label in enumerate(labels):
        out.append((f"component_{i:03d}", label))
    return out


def _style(label: str) -> dict:
    low = label.lower()
    if "continuum" in low:
        return {"color": "0.55", "ls": "-", "lw": 1.0}
    if "feii" in low:
        return {"color": "tab:orange", "ls": ":", "lw": 1.0}
    if "broad" in low:
        return {"color": "tab:red", "ls": "--", "lw": 1.0}
    if "narrow1" in low:
        return {"color": "tab:green", "ls": "-", "lw": 1.1}
    if "narrow2" in low:
        return {"color": "tab:purple", "ls": "-", "lw": 1.1}
    return {"color": "tab:blue", "ls": "-", "lw": 0.9}


def plot_fit(df: pd.DataFrame, labels: list[str], region: tuple[float, float],
             chi2: float, z: float, out: Path) -> None:
    wave = df["wave_rest"].values
    fig = plt.figure(figsize=(12.5, 10))
    gs = fig.add_gridspec(3, 1, height_ratios=[2.2, 1.3, 1.0], hspace=0.06)
    ax0 = fig.add_subplot(gs[0])
    ax0.plot(wave, df["flux"], color="0.15", lw=0.8, label="SDSS data")
    ax0.fill_between(wave, df["flux"] - df["flux_err"], df["flux"] + df["flux_err"],
                     color="0.75", alpha=0.35, linewidth=0, label="1$\\sigma$")
    ax0.plot(wave, df["model"], color="tab:red", ls="--", lw=1.2, label="SHEAP total")
    for x, label in [(4861.333, r"H$\beta$"), (4958.896, "[O III] 4959"),
                     (5006.803, "[O III] 5007")]:
        ax0.axvline(x, color="0.55", lw=0.6, ls="-.")
        ax0.text(x, ax0.get_ylim()[1], label, rotation=90, va="top", ha="right",
                 fontsize=7, color="0.35")
    ax0.set_xlim(region)
    ax0.set_ylabel(r"$f_\lambda$ (erg s$^{-1}$ cm$^{-2}$ $\AA^{-1}$)")
    ax0.set_title(f"SHEAP JAX/Adam fit (CPU)  z={z:.6f}  $\\chi^2_\\nu$={chi2:.2f}")
    ax0.legend(loc="upper right", fontsize=8, frameon=False)
    ax0.grid(alpha=0.2, ls=":")

    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    for col, label in _comp_columns(labels):
        if col not in df:
            continue
        ax1.plot(wave, df[col], label=label, **_style(label))
    ax1.set_ylabel("line components")
    ax1.legend(loc="upper right", fontsize=6, ncol=3, frameon=False)
    ax1.grid(alpha=0.2, ls=":")

    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    ax2.axhline(0, color="0.3", lw=0.7, ls=":")
    for y in (-1, 1):
        ax2.axhline(y, color="0.6", lw=0.5, ls="--")
    ax2.plot(wave, df["residual_sigma"], color="tab:blue", lw=0.8)
    ax2.set_ylabel("residual / $\\sigma$")
    ax2.set_xlabel(r"Rest-frame wavelength ($\AA$)")
    ax2.set_xlim(region)
    ax2.grid(alpha=0.2, ls=":")
    fig.savefig(out / "sheap_fit.png", dpi=170, bbox_inches="tight")
    fig.savefig(out / "sheap_fit.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_zoom(df: pd.DataFrame, labels: list[str], xlim: tuple[float, float],
              title: str, out_png: Path, out_pdf: Path) -> None:
    s = (df["wave_rest"] >= xlim[0]) & (df["wave_rest"] <= xlim[1])
    d = df.loc[s]
    fig, axs = plt.subplots(2, 1, figsize=(10.5, 6.6), sharex=True,
                            gridspec_kw={"height_ratios": [2.6, 1.0], "hspace": 0.05})
    ax = axs[0]
    ax.plot(d["wave_rest"], d["flux"], color="0.15", lw=1.0, label="SDSS data")
    ax.fill_between(d["wave_rest"], d["flux"] - d["flux_err"], d["flux"] + d["flux_err"],
                    color="0.75", alpha=0.35, linewidth=0)
    ax.plot(d["wave_rest"], d["model"], color="tab:red", ls="--", lw=1.3, label="total")
    for col, label in _comp_columns(labels):
        if col not in d:
            continue
        if "continuum" in label.lower() or "feii" in label.lower():
            continue
        ax.plot(d["wave_rest"], d[col], label=label, **_style(label))
    ax.set_xlim(xlim)
    ax.set_ylabel(r"$f_\lambda$ (erg s$^{-1}$ cm$^{-2}$ $\AA^{-1}$)")
    ax.set_title(title)
    ax.legend(loc="upper right", fontsize=7, frameon=False)
    ax.grid(alpha=0.2, ls=":")
    ax2 = axs[1]
    ax2.axhline(0, color="0.3", lw=0.7, ls=":")
    for y in (-1, 1):
        ax2.axhline(y, color="0.6", lw=0.5, ls="--")
    ax2.plot(d["wave_rest"], d["residual_sigma"], color="tab:blue", lw=0.9)
    ax2.set_ylabel("residual / $\\sigma$")
    ax2.set_xlabel(r"Rest-frame wavelength ($\AA$)")
    ax2.set_xlim(xlim)
    ax2.grid(alpha=0.2, ls=":")
    fig.savefig(out_png, dpi=170, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)


def plot_residual(df: pd.DataFrame, region: tuple[float, float], out: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.axhline(0, color="0.3", lw=0.7, ls=":")
    for y, ls in [(1, "--"), (2, ":"), (-1, "--"), (-2, ":")]:
        ax.axhline(y, color="0.6", lw=0.5, ls=ls)
    ax.plot(df["wave_rest"], df["residual_sigma"], color="tab:blue", lw=0.8)
    ax.set_xlim(region)
    ax.set_xlabel(r"Rest-frame wavelength ($\AA$)")
    ax.set_ylabel("residual / $\\sigma$")
    ax.grid(alpha=0.2, ls=":")
    fig.savefig(out / "sheap_residual.png", dpi=170, bbox_inches="tight")
    fig.savefig(out / "sheap_residual.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_uncertainty(sample_table: pd.DataFrame, out: Path, nsamp: int) -> dict:
    specs = [
        ("Hbeta_total_1e17", r"H$\beta$ total"),
        ("OIII5007_total_1e17", "[O III] 5007"),
        ("Hbeta_OIII5007", r"H$\beta$ / [O III] 5007"),
    ]
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.2))
    summary = {}
    for ax, (col, label) in zip(axs, specs):
        if col not in sample_table:
            ax.axis("off")
            continue
        vals = sample_table[col].dropna().values
        q16, q50, q84 = np.quantile(vals, [0.16, 0.50, 0.84])
        err = (q84 - q16) / 2.0
        summary[col] = {"median": float(q50), "err_1sigma": float(err),
                        "q16": float(q16), "q84": float(q84),
                        "n_samples": int(vals.size)}
        ax.hist(vals, bins=min(20, max(5, vals.size // 2)), color="tab:blue",
                alpha=0.75, edgecolor="white")
        ax.axvline(q16, color="0.3", ls="--", lw=1)
        ax.axvline(q50, color="k", lw=1.2)
        ax.axvline(q84, color="0.3", ls="--", lw=1)
        ax.set_title(f"{label}\n{q50:.3g} $\\pm$ {err:.3g}", fontsize=10)
        ax.set_xlabel(label)
        ax.grid(alpha=0.2, ls=":")
    fig.suptitle(f"SHEAP parametric-bootstrap MC ({nsamp} draws; not MCMC)",
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
                "notes": "SHEAP fluxes are rest-frame f_lambda / 1e-17; reference "
                         "values are the siblings' published rest-frame tables",
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

    ref_median: dict[str, float] = {}
    ref_n: dict[str, int] = {}
    for line in ("Hbeta", "OIII5007"):
        vals = [r["reference_1e17"] for r in rows
                if r["line"] == line and r["reference_1e17"] is not None]
        if vals:
            ref_median[line] = float(np.median(vals))
            ref_n[line] = len(vals)
    return {
        "sheap_hbeta_oiii5007": qg_ratio,
        "sheap_hbeta_oiii5007_err": qg_ratio_err,
        "reference_median_1e17": ref_median,
        "reference_n": ref_n,
        "references": rows,
        "ratios": ratios,
    }


def at_bound_params(sc: Sheapectral, tol: float = 1e-3) -> list[dict]:
    """Line-kinematic parameters sitting on a hard SHEAP bound."""
    p = np.asarray(sc.result.params[0], dtype=float)
    con = np.asarray(sc.result.constraints, dtype=float)
    names = {v: k for k, v in sc.result.params_dict.items()}
    hits = []
    for i, (lo, hi) in enumerate(con):
        name = names.get(i, "")
        if not any(key in name for key in ("vshift", "fwhm", "x_break")):
            continue
        span = hi - lo
        if span <= 0:
            continue
        frac = (p[i] - lo) / span
        if frac < tol or frac > 1.0 - tol:
            hits.append({"name": name, "value": float(p[i]),
                         "lower": float(lo), "upper": float(hi),
                         "fraction_of_range": float(frac)})
    return hits


def assess_quality(table: pd.DataFrame, chi2: float, comparison: dict,
                   gates_cfg: dict, at_bound: list[dict]) -> dict:
    def total(line: str) -> pd.Series | None:
        sub = table[(table["line"] == line) & (table["component"] == "total")]
        if sub.empty:
            return None
        return sub.iloc[0]

    hb, o3 = total("Hbeta"), total("OIII5007")
    ratio = (float(hb["flux_1e17"]) / float(o3["flux_1e17"])
             if hb is not None and o3 is not None and float(o3["flux_1e17"]) > 0
             else float("nan"))
    broad = table[(table["line"] == "Hbeta") & (table["component"] == "broad")]
    broad_fwhm = float(broad.iloc[0]["fwhm_kms"]) if not broad.empty else float("nan")
    o3b = total("OIII4959")
    doublet = (float(o3["flux_1e17"]) / float(o3b["flux_1e17"])
               if o3 is not None and o3b is not None and float(o3b["flux_1e17"]) > 0
               else float("nan"))

    gates = []

    def add(name: str, value: Any, ok: bool, threshold: str, note: str = "") -> None:
        gates.append({"name": name, "value": jsonable(value),
                      "threshold": threshold, "passed": bool(ok), "note": note})

    add("chi2_red", chi2, chi2 <= gates_cfg["max_chi2_red"],
        f"<= {gates_cfg['max_chi2_red']}",
        "reduced chi2 of the fitted region; a value near 46 is a model failure")
    add("Hbeta_OIII5007", ratio,
        np.isfinite(ratio) and gates_cfg["ratio_min"] <= ratio <= gates_cfg["ratio_max"],
        f"{gates_cfg['ratio_min']} <= ratio <= {gates_cfg['ratio_max']}",
        "optical H-beta/[O III] 5007 spread of the sibling fitters")
    add("OIII_5007_4959", doublet,
        np.isfinite(doublet) and gates_cfg["oiii_doublet_min"] <= doublet <= gates_cfg["oiii_doublet_max"],
        f"{gates_cfg['oiii_doublet_min']} <= ratio <= {gates_cfg['oiii_doublet_max']}",
        "the [O III] doublet ratio is tied by SHEAP's line repository")
    add("broad_Hbeta_FWHM_kms", broad_fwhm,
        np.isfinite(broad_fwhm) and broad_fwhm <= gates_cfg["max_broad_hbeta_fwhm_kms"],
        f"<= {gates_cfg['max_broad_hbeta_fwhm_kms']} km/s",
        "the failing baseline reached 8019 km/s")
    add("line_kinematics_at_bound", len(at_bound), len(at_bound) == 0,
        "0 parameters at a hard bound",
        "a fit pinned to a prior bound is not a measurement")

    ref_med = comparison.get("reference_median_1e17", {})
    ref_n = comparison.get("reference_n", {})
    for line, row in (("Hbeta", hb), ("OIII5007", o3)):
        med = ref_med.get(line)
        n = ref_n.get(line, 0)
        if med and row is not None and n >= gates_cfg["min_reference_tools"]:
            dev = abs(float(row["flux_1e17"]) / med - 1.0)
            add(f"{line}_vs_reference_median", dev,
                dev <= gates_cfg["max_reference_deviation"],
                f"<= {gates_cfg['max_reference_deviation']:.0%} of median",
                f"reference median {med:.1f} (1e-17), n={n}")

    ok = all(g["passed"] for g in gates)
    return {
        "production_ok": bool(ok),
        "status": "pass" if ok else "fail",
        "ratio": jsonable(ratio),
        "broad_hbeta_fwhm_kms": jsonable(broad_fwhm),
        "oiii_5007_4959": jsonable(doublet),
        "gates": gates,
        "at_bound_line_params": at_bound,
        "notes": ("A failing gate means the result is retained for diagnostics "
                  "but must not be used as a production line measurement."),
    }


def run_variants(spec: dict, z: float, name: str, scfg: dict, cfg: dict,
                 out: Path, gates_cfg: dict, reference: Path,
                 ref_tools: list[str]) -> dict:
    variants = list(scfg.get("variants", []))
    if not variants:
        return {}
    rows = []
    for i, vcfg in enumerate(variants):
        label = str(vcfg.get("name", f"variant{i + 1}"))
        merged = dict(scfg)
        merged.update(vcfg)
        # Merge the nested limit overrides instead of replacing the whole block.
        if "limits_overrides" in vcfg:
            base_limits = dict(scfg.get("limits_overrides", {}))
            for region, vals in vcfg["limits_overrides"].items():
                base_limits[region] = {**base_limits.get(region, {}), **vals}
            merged["limits_overrides"] = base_limits
        log(f"[sheap] variant {label}: {json.dumps(jsonable(vcfg))}")
        t0 = time.time()
        try:
            sc = build_sheap(spec, z, name, merged)
            chi2, _, _ = fit_sheap(sc, merged)
            sc.estimate_posteriors(sampling_method="single", summarize=False)
            best = sc.result.posterior["single"]["posterior_result"][name]["basic_params"]
            table, _ = build_line_table(best, best, z)
            comparison = {}
            hb = table[(table["line"] == "Hbeta") & (table["component"] == "total")]
            o3 = table[(table["line"] == "OIII5007") & (table["component"] == "total")]
            broad = table[(table["line"] == "Hbeta") & (table["component"] == "broad")]
            ratio = (float(hb.iloc[0]["flux_1e17"]) / float(o3.iloc[0]["flux_1e17"])
                     if not hb.empty and not o3.empty and float(o3.iloc[0]["flux_1e17"]) > 0
                     else np.nan)
            at_bound = at_bound_params(sc)
            q = assess_quality(table, chi2, comparison, gates_cfg, at_bound)
            rows.append({
                "variant": label,
                "region_rest_A": " ".join(f"{x:g}" for x in merged.get("region_rest", DEFAULT_REGION)),
                "n_narrow": int(merged.get("n_narrow", 2)),
                "fe_mode": merged.get("fe_mode", "template"),
                "continuum_profile": merged.get("continuum_profile", "powerlaw"),
                "chi2_red": chi2,
                "Hbeta_total_1e17": float(hb.iloc[0]["flux_1e17"]) if not hb.empty else np.nan,
                "OIII5007_1e17": float(o3.iloc[0]["flux_1e17"]) if not o3.empty else np.nan,
                "Hbeta_OIII5007": ratio,
                "broad_Hbeta_FWHM_kms": float(broad.iloc[0]["fwhm_kms"]) if not broad.empty else np.nan,
                "passes_gates": q["production_ok"],
                "at_bound": len(at_bound),
                "runtime_sec": time.time() - t0,
            })
        except Exception as exc:  # noqa: BLE001
            log(f"[sheap] variant {label} failed: {exc}")
            rows.append({"variant": label, "chi2_red": np.nan,
                         "Hbeta_total_1e17": np.nan, "OIII5007_1e17": np.nan,
                         "Hbeta_OIII5007": np.nan, "broad_Hbeta_FWHM_kms": np.nan,
                         "passes_gates": False, "at_bound": np.nan,
                         "runtime_sec": time.time() - t0})
    df = pd.DataFrame(rows)
    df.to_csv(out / "sheap_systematics.csv", index=False)
    good = df[df["passes_gates"].astype(bool)]
    summary: dict[str, Any] = {"n_variants": int(len(df)), "n_passing": int(len(good)),
                               "variants": df.to_dict(orient="records")}
    if len(good) > 1:
        for col in ("Hbeta_total_1e17", "OIII5007_1e17", "Hbeta_OIII5007"):
            vals = good[col].dropna().values
            if vals.size:
                summary[col] = {"min": float(np.min(vals)), "max": float(np.max(vals)),
                                "std": float(np.std(vals, ddof=1)),
                                "half_range": float((np.max(vals) - np.min(vals)) / 2.0)}
    return summary


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
    reference = Path(args.reference) if args.reference else Path("/nonexistent")

    scfg = dict(cfg.get("sheap", {}))
    scfg.setdefault("region_rest", list(DEFAULT_REGION))
    scfg.setdefault("n_broad", 1)
    scfg.setdefault("n_narrow", 2)
    scfg.setdefault("fe_mode", "template")
    scfg.setdefault("continuum_profile", "powerlaw")
    scfg.setdefault("num_steps", [4000, 1000])
    scfg.setdefault("learning_rate", [1e-2, 1e-2])
    gates_cfg = dict(cfg["quality_gates"])
    n_mc = int(scfg.get("montecarlo_samples", 50))
    seed = int(scfg.get("seed", 42))

    region = tuple(float(x) for x in scfg["region_rest"])
    log(f"[sheap] input={spectrum_path}")
    log(f"[sheap] z={z:.8f} region={region} n_broad={scfg['n_broad']} "
        f"n_narrow={scfg['n_narrow']} fe={scfg['fe_mode']} cont={scfg['continuum_profile']}")
    log(f"[sheap] good pixels={spec['n_good']}/{spec['n_total']} "
        f"rest range={spec['wave'].min() / (1 + z):.1f}-"
        f"{spec['wave'].max() / (1 + z):.1f} A")

    t_fit = time.time()
    sc = build_sheap(spec, z, name, scfg)
    chi2, steps, lrs = fit_sheap(sc, scfg)
    fit_sec = time.time() - t_fit
    log(f"[sheap] fit completed chi2_r={chi2:.3f} in {fit_sec:.1f}s")

    t_post = time.time()
    sc.estimate_posteriors(sampling_method="single", summarize=False)
    best = sc.result.posterior["single"]["posterior_result"][name]["basic_params"]
    log(f"[sheap] parametric-bootstrap MC: {n_mc} draws")
    sc.estimate_posteriors(sampling_method="montecarlo", num_samples=n_mc,
                           key_seed=seed, summarize=False, overwrite=True)
    mc = sc.result.posterior["montecarlo"]["posterior_result"][name]["basic_params"]
    mc_sec = time.time() - t_post
    log(f"[sheap] MC done in {mc_sec:.1f}s")

    table, sample_table = build_line_table(best, mc, z)
    table.to_csv(out / "sheap_lines.csv", index=False)
    sample_table.to_csv(out / "sheap_mc_samples.csv", index=False)

    t_fig = time.time()
    model_df, labels = write_model(sc, region, out)
    try:
        sc.modelplot.plot(0, save=str(out / "sheap_fit_native.png"), add_lines_name=True)
    except Exception as exc:  # noqa: BLE001
        log(f"[warn] native SHEAP plot failed: {exc}")
    plot_fit(model_df, labels, region, chi2, z, out)
    plot_zoom(model_df, labels, (4780.0, 4935.0), r"H$\beta$ zoom",
              out / "sheap_zoom_hbeta.png", out / "sheap_zoom_hbeta.pdf")
    plot_zoom(model_df, labels, (4935.0, 5030.0), r"[O III] 4959/5007 zoom",
              out / "sheap_zoom_oiii.png", out / "sheap_zoom_oiii.pdf")
    plot_residual(model_df, region, out)
    unc = plot_uncertainty(sample_table, out, n_mc)
    fig_sec = time.time() - t_fig
    comparison = write_comparison(table, reference,
                                  list(cfg.get("reference_tools", [])), out)

    at_bound = at_bound_params(sc)
    quality = assess_quality(table, chi2, comparison, gates_cfg, at_bound)

    hb = table[(table["line"] == "Hbeta") & (table["component"] == "total")]
    hbb = table[(table["line"] == "Hbeta") & (table["component"] == "broad")]
    hbn = table[(table["line"] == "Hbeta") & (table["component"].str.startswith("narrow"))]
    o3 = table[(table["line"] == "OIII5007") & (table["component"] == "total")]
    o3b = table[(table["line"] == "OIII4959") & (table["component"] == "total")]
    narrow = table[table["component"].str.startswith("narrow")]
    wing = narrow[narrow["velocity_kms"] < -300.0] if not narrow.empty else narrow
    line_summary = {
        "n_rows": int(len(table)),
        "n_detected": int(table["detected"].sum()),
        "Hbeta_total_1e17": float(hb.iloc[0]["flux_1e17"]) if not hb.empty else None,
        "Hbeta_broad_1e17": float(hbb.iloc[0]["flux_1e17"]) if not hbb.empty else None,
        "Hbeta_narrow_1e17": float(hbn["flux_1e17"].sum()) if not hbn.empty else None,
        "OIII5007_total_1e17": float(o3.iloc[0]["flux_1e17"]) if not o3.empty else None,
        "OIII4959_total_1e17": float(o3b.iloc[0]["flux_1e17"]) if not o3b.empty else None,
        "Hbeta_OIII5007": comparison.get("sheap_hbeta_oiii5007"),
        "Hbeta_OIII5007_err": comparison.get("sheap_hbeta_oiii5007_err"),
        "OIII5007_OIII4959": quality.get("oiii_5007_4959"),
        "Hbeta_broad_fwhm_kms": float(hbb.iloc[0]["fwhm_kms"]) if not hbb.empty else None,
        "narrow_components": int(table[table["component"].str.startswith("narrow")]["component"].nunique()),
        "narrow_wing_velocity_kms": float(wing["velocity_kms"].min()) if not wing.empty else None,
        "narrow_wing_fwhm_kms": float(wing.iloc[0]["fwhm_kms"]) if not wing.empty else None,
    }

    import scipy as _scipy
    import pandas as _pd
    import astropy as _astropy
    import jaxlib as _jaxlib
    versions = {
        "python": sys.version.split()[0],
        "sheap": SHEAP_VERSION,
        "jax": jax.__version__,
        "jaxlib": getattr(_jaxlib, "__version__", None),
        "numpy": np.__version__,
        "scipy": _scipy.__version__,
        "pandas": _pd.__version__,
        "astropy": _astropy.__version__,
        "matplotlib": matplotlib.__version__,
    }
    components = []
    for i, sp in enumerate(getattr(sc.result, "region_list", [])):
        components.append({
            "index": i,
            "line": getattr(sp, "line_name", None),
            "region": getattr(sp, "region", None),
            "component": getattr(sp, "component", None),
            "profile": getattr(sp, "profile", None),
            "center_A": getattr(sp, "center", None),
            "label": labels[i] if i < len(labels) else None,
        })

    variant_summary: dict = {}
    if args.variants:
        log("[sheap] running model-systematics variants")
        variant_summary = run_variants(spec, z, name, scfg, cfg, out, gates_cfg,
                                       reference, list(cfg.get("reference_tools", [])))
        quality["systematics"] = variant_summary

    n_region = int((~np.asarray(sc.result.mask[0], dtype=bool)).sum())
    n_params = int(np.asarray(sc.result.params).shape[-1])
    nsamp = int(sample_table.shape[0])
    statistic_note = (
        "SHEAP's 'montecarlo' sampler resamples the spectrum from the observed "
        "flux and 1-sigma errors and re-runs the JAX optimiser; it is a "
        "parametric bootstrap, not an MCMC posterior and not a draw from the "
        "fit covariance.  The covariance matrix is the separate JAX JTJ "
        "estimate computed by covariance_error=True.")
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
            "flux_unit": "1e-17 erg s-1 cm-2 A-1 (rest-frame f_lambda after SHEAP deredshift)",
            "bunit_header": spec["bunit"],
            "mask_and_mask": bool(cfg.get("mask_and_mask", True)),
        },
        "config_file": str(Path(args.config)),
        "model": {
            "region_rest_A": list(region),
            "n_broad": int(scfg["n_broad"]),
            "n_narrow": int(scfg["n_narrow"]),
            "fe_mode": str(scfg["fe_mode"]),
            "continuum_profile": str(scfg["continuum_profile"]),
            "add_balmer_continuum": bool(scfg.get("add_balmer_continuum", False)),
            "add_balmerhighorder_continuum": bool(scfg.get("add_balmerhighorder_continuum", False)),
            "add_outflow": bool(scfg.get("add_outflow", False)),
            "line_profile": str(scfg.get("profile", "gaussian")),
            "limits_overrides": jsonable(scfg.get("limits_overrides", {})),
            "components": components,
        },
        "fit": {
            "optimizer": str(scfg.get("method", "adam")),
            "stages": [{"num_steps": int(s), "learning_rate": float(l)}
                       for s, l in zip(steps, lrs)],
            "covariance_error": bool(scfg.get("covariance_error", True)),
            "chi2_red": chi2,
            "n_params": n_params,
            "n_pixels_region": n_region,
            "n_free_params": float(np.asarray(sc.result.free_params)[0]),
        },
        "statistical_mode": {
            "method": "parametric bootstrap Monte Carlo (spectrum resampling + re-optimisation)",
            "covariance": "JAX Jacobian/JTJ covariance (covariance_error=true)",
            "n_samples": n_mc,
            "seed": seed,
            "mcmc": False,
            "note": statistic_note,
            "derived_quantiles": unc,
        },
        "quality": quality,
        "line_fit": line_summary,
        "comparison": comparison,
        "systematics": variant_summary,
        "runtime": {
            "fit_sec": fit_sec,
            "posterior_mc_sec": mc_sec,
            "figures_sec": fig_sec,
            "total_sec": time.time() - t0,
        },
        "scope": {
            "accelerator": "CPU; GPU not used",
            "galactic_dereddening": False,
            "fe_ii": str(scfg["fe_mode"]),
            "host_galaxy": False,
            "balmer_continuum": bool(scfg.get("add_balmer_continuum", False)),
            "region": "rest-frame 4450-5450 A: H-beta, [O III] 4959/5007, He I/He II, Fe II",
            "narrow_model": ("two narrow SPAF components: NLR core + blueshifted "
                             "[O III] wing; component kinematics are tied across "
                             "the narrow lines by SHEAP's group method"),
            "fit_quality_note": (
                "chi2_nu and the H-beta/[O III] quality gates are recorded under "
                "'quality'.  The 2026-08 audit replaced the original 4600-5150 A "
                "single-narrow no-Fe-II model, which gave chi2_nu=46 and "
                "H-beta/[O III]=4.00, with the validated model used here."),
        },
        "line_measurements": table.to_dict(orient="records"),
    }
    with (out / "run.json").open("w") as fh:
        json.dump(jsonable(run), fh, indent=2)

    if not quality["production_ok"]:
        failed = [g["name"] for g in quality["gates"] if not g["passed"]]
        log(f"[sheap] QUALITY GATES FAILED: {', '.join(failed)}; "
            "outputs written for diagnostics but this result is NOT a production measurement")
        return 2
    log(f"[sheap] quality gates passed; done in {run['runtime']['total_sec']:.1f}s -> {out}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--config", default="/app/config/config.json")
    p.add_argument("--z", type=float, default=None)
    p.add_argument("--name", default="sheap")
    p.add_argument("--reference", default=None)
    p.add_argument("--variants", action="store_true",
                   help="run the model-systematics variants listed in the config")
    args = p.parse_args(argv)
    try:
        return run(args)
    except Exception as exc:  # noqa: BLE001
        log(f"[sheap] ERROR: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
