#!/usr/bin/env python3
"""QGfit adapter for the canonical SDSS QSO inputs.

The adapter reads one SDSS spectrum (``spec-*.fits`` with a ``COADD``-style
table), calls QGfit's ``QGfitObj`` continuum + emission-line fitter, and writes
a compact, tool-neutral product set:

    qgfit_lines.csv           line fluxes, FWHM, velocity, component table
    qgfit_model.csv           rest-frame data / continuum / line / total model
    qgfit_fit.png/.pdf        data, continuum and H-beta/[O III] decomposition
    qgfit_uncertainty.png/pdf corner plot of the short continuum MCMC
    qgfit_line_errors.png     line-flux error bars (least-squares covariance)
    qgfit_mcmc_summary.csv    per-parameter MCMC quantiles
    qgfit_comparison.csv      QGfit vs sibling PyQSOFit/GANDALF/S3Fit fluxes
    qgfit_ratio_comparison.csv
    run.json                  provenance, controls, method and timings

Method labelling
----------------
* Continuum + lines: QGfit's lmfit least-squares fit (KMPFIT fallback is
  enabled exactly as in QGfit's defaults and its result is recorded).
* Statistical mode: a **short, real emcee MCMC of the continuum only**
  (40 walkers x 100 steps by default).  It is not a converged posterior and
  the adapter says so in run.json.
* Line uncertainties come from QGfit's least-squares covariance
  (``norm_stderr``); they are not MCMC errors.  Line MCMC is disabled by
  default because QGfit runs one emcee chain per emission-line complex and
  that is much slower than the continuum chain.

Flux units
-----------
SDSS ``FLUX`` is in 1e-17 erg s-1 cm-2 A-1.  QGfit works in the rest frame and
its ``line_info['flux']`` is an integral over rest-frame wavelength in units of
1e-17 erg s-1 cm-2.  The observed-frame line flux is the rest-frame integral
divided by (1+z)^2 (the extra (1+z) from dlambda_rest = dlambda_obs/(1+z));
the adapter records both quantities in the table.
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

# QGfit refuses to import unless SFD_PATH exists.  We do not need the maps when
# do_deredden is false; the empty directory is created in the image.
os.environ.setdefault("SFD_PATH", "/opt/sfd")
os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.io import fits

from qgfit.fitter import QGfitObj
from qgfit.model import conti_model
from qgfit.line import many_lines
from qgfit import __version__ as QGFIT_VERSION

warnings.filterwarnings("ignore", category=RuntimeWarning)

FLUX_FACTOR = 1e-17  # SDSS native unit: 1e-17 erg s-1 cm-2 A-1
C_KMS = 299792.458

# QGfit line names -> canonical line names used by the repository comparison.
LINE_MAP = {
    "Halpha_br": "Halpha",
    "Halpha_na": "Halpha",
    "Hbeta_br": "Hbeta",
    "Hbeta_na": "Hbeta",
    "Hgamma_br": "Hgamma",
    "Hgamma_na": "Hgamma",
    "Hdelta_br": "Hdelta",
    "Hdelta_na": "Hdelta",
    "Hepsilon_br": "Hepsilon",
    "Hepsilon_na": "Hepsilon",
    "OIII5007": "OIII5007",
    "OIII4959": "OIII4959",
    "OIII4363": "OIII4363",
    "NII6549": "NII6549",
    "NII6585": "NII6585",
    "SII6718": "SII6718",
    "SII6732": "SII6732",
    "OII3727": "OII3727",
    "NeIII": "NeIII3869",
    "MgII": "MgII",
    "CIII": "CIII",
    "CIV": "CIV",
    "Lya": "Lya",
    "NI5200": "NI5200",
    "OI6302": "OI6302",
    "OI6365": "OI6365",
    "HeI3889_br": "HeI3889",
    "HeI3889_na": "HeI3889",
    "HeI5877_br": "HeI5877",
    "HeI5877_na": "HeI5877",
    "HeII1640": "HeII1640",
    "AlIII1857": "AlIII1857",
    "FeVII": "FeVII",
    "NV1240": "NV1240",
}

TOTAL_LINES = {
    "Halpha", "Hbeta", "Hgamma", "Hdelta", "Hepsilon",
    "OIII5007", "OIII4959", "MgII", "CIII", "CIV", "Lya",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def jsonable(value: Any) -> Any:
    """Return a JSON-serialisable copy of common NumPy/pandas containers."""
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return [jsonable(v) for v in value.tolist()]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if not np.isfinite(value):
            return None
        return float(value)
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
    """Read an SDSS COADD table or a prepared PyQSOFit-style FITS file."""
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
        if table is not None:
            data = table.data
            cols = {c.lower(): c for c in data.columns.names}
            flux = np.asarray(data[cols["flux"]], dtype=float)
            wave = 10.0 ** np.asarray(data[cols["loglam"]], dtype=float)
            ivar = np.asarray(data[cols["ivar"]], dtype=float) if "ivar" in cols else None
            if ivar is None:
                err = np.asarray(data[cols["stdev"]], dtype=float) if "stdev" in cols else None
                if err is None:
                    raise ValueError(f"{path}: no IVAR or STDEV column")
                fluxerr = err
            else:
                with np.errstate(divide="ignore", invalid="ignore"):
                    fluxerr = 1.0 / np.sqrt(ivar)
            and_mask = np.asarray(data[cols["and_mask"]], dtype=int) if "and_mask" in cols else None
            wdisp = np.asarray(data[cols["wdisp"]], dtype=float) if "wdisp" in cols else None
        else:
            # Prepared PyQSOFit layout: HDU0 flux, HDU1 wavelength, HDU2 error.
            if len(hdul) < 2:
                raise ValueError(f"{path}: unsupported FITS layout")
            flux = np.asarray(hdul[0].data, dtype=float).squeeze()
            wave = np.asarray(hdul[1].data, dtype=float).squeeze()
            if len(hdul) > 2 and hdul[2].data is not None:
                fluxerr = np.asarray(hdul[2].data, dtype=float).squeeze()
            else:
                fluxerr = np.full_like(flux, np.nan)
            ivar = None
            and_mask = None
            wdisp = None

        z = None
        ra = None
        dec = None
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
        if bunit and "1E-17" not in bunit and "ERG" in bunit and "CM" in bunit:
            # Flux is in cgs; QGfit expects 1e-17 units.
            flux = flux / FLUX_FACTOR
            if fluxerr is not None:
                fluxerr = fluxerr / FLUX_FACTOR

    wave = np.asarray(wave, dtype=float)
    flux = np.asarray(flux, dtype=float)
    fluxerr = np.asarray(fluxerr, dtype=float)
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
        "wdisp": wdisp[good] if wdisp is not None else None,
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
    cfg.setdefault("qgfit", {})
    cfg.setdefault("reference_tools", ["pyqsofit_uv", "gandalf_line", "s3fit_line"])
    return cfg


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def line_table(data: dict) -> pd.DataFrame:
    """Build the compact line table from a QGfit result dictionary."""
    z = float(data["z"])
    df = data["line"].get("result", [None])[0]
    info = data["line"].get("line_info", [None])[0]
    if df is None or info is None:
        raise RuntimeError("QGfit result has no line table (line_fit=False?)")
    df = pd.DataFrame(df).copy()
    info = pd.DataFrame(info).copy()
    df["linename"] = df["linename"].astype(str)
    info["linename"] = info["linename"].astype(str)
    df["compname"] = df["compname"].astype(str)
    info["comp"] = info["comp"].astype(str)

    # One result row per Gaussian.  Lines in the QGfit template are normally
    # one Gaussian; if a future line uses several, keep the first for the
    # metadata columns and the summed integrated flux for the flux value.
    meta = (df.groupby(["compname", "linename"], as_index=False)
              .agg({"lambda": "first", "ln_shift": "first", "ln_sigma": "first",
                    "skew": "first", "gamma_ratio": "first", "FWHM": "first",
                    "norm": "first", "norm_stderr": "first",
                    "FWHM_stderr": "first", "type": "first"}))
    merged = info.merge(meta, left_on=["comp", "linename"],
                        right_on=["compname", "linename"], how="left",
                        suffixes=("", "_meta"))
    if merged["lambda"].isna().any():
        missing = merged.loc[merged["lambda"].isna(), "linename"].tolist()
        log(f"[warn] QGfit line metadata missing for: {missing}")

    rows = []
    for _, r in merged.iterrows():
        qname = str(r["linename"])
        canonical = LINE_MAP.get(qname, qname)
        rest_flux = float(r["flux"]) if pd.notna(r["flux"]) else 0.0
        lam = float(r["lambda"]) if pd.notna(r["lambda"]) else np.nan
        norm_err = float(r["norm_stderr"]) if pd.notna(r["norm_stderr"]) else 0.0
        # First-order covariance: the integrated line flux is norm * lambda
        # to zeroth order for a profile normalised in ln(lambda).  This is the
        # only line uncertainty QGfit exposes when line_mcmc is off.
        rest_err = abs(norm_err * lam) if np.isfinite(lam) else 0.0
        fwhm = float(r["FWHM"]) if pd.notna(r["FWHM"]) else np.nan
        fwhm_err = float(r["FWHM_stderr"]) if pd.notna(r["FWHM_stderr"]) else np.nan
        shift = float(r["ln_shift"]) if pd.notna(r["ln_shift"]) else np.nan
        component = str(r["type"]) if pd.notna(r["type"]) else "unknown"
        obs_flux = rest_flux / (1.0 + z) ** 2
        obs_err = rest_err / (1.0 + z) ** 2
        snr = obs_flux / obs_err if obs_err > 0 else np.nan
        detected = bool(obs_flux > 0 and (not np.isfinite(snr) or snr >= 3.0))
        rows.append({
            "line": canonical,
            "qgfit_line": qname,
            "component": component,
            "lambda_rest": lam,
            "flux_rest_1e17": rest_flux,
            "flux_1e17": obs_flux,
            "flux_err_1e17": obs_err,
            "flux_erg_s_cm2": obs_flux * FLUX_FACTOR,
            "flux_err_erg_s_cm2": obs_err * FLUX_FACTOR,
            "fwhm_kms": fwhm,
            "fwhm_err_kms": fwhm_err,
            "velocity_kms": shift * C_KMS if np.isfinite(shift) else np.nan,
            "norm": float(r["norm"]) if pd.notna(r["norm"]) else np.nan,
            "norm_err": norm_err,
            "n_gauss": int(r["n_gauss"]) if pd.notna(r["n_gauss"]) else 1,
            "snr": snr,
            "detected": detected,
            "method": "qgfit_leastsq",
            "notes": ("QGfit profile type=%s; flux is the rest-frame integral "
                      "divided by (1+z)^2; error from least-squares norm "
                      "covariance (width/shift terms neglected)" % component),
        })

    table = pd.DataFrame(rows)
    if table.empty:
        return table

    # Add total rows for the lines used in the cross-tool comparison.  A total
    # row makes the downstream comparison unambiguous and also documents that
    # QGfit sometimes removes a narrow component via its BIC test.
    totals = []
    for line in sorted(set(table["line"]) & TOTAL_LINES):
        sub = table[table["line"] == line]
        # Only add a total row when there is more than one component; a
        # single-component line is already unambiguous in the comparison.
        if len(sub) < 2:
            continue
        f = float(sub["flux_1e17"].sum())
        e = float(np.sqrt(np.sum(sub["flux_err_1e17"].values ** 2)))
        positive = sub[sub["flux_1e17"] > 0]
        if len(positive) > 0 and positive["flux_1e17"].sum() > 0:
            fwhm = float(np.average(positive["fwhm_kms"].fillna(0),
                                    weights=positive["flux_1e17"]))
        else:
            fwhm = float(sub["fwhm_kms"].dropna().iloc[0]) if sub["fwhm_kms"].notna().any() else np.nan
        lam = float(sub["lambda_rest"].dropna().iloc[0]) if sub["lambda_rest"].notna().any() else np.nan
        totals.append({
            "line": line,
            "qgfit_line": "+".join(sub["qgfit_line"].astype(str)),
            "component": "total",
            "lambda_rest": lam,
            "flux_rest_1e17": float(sub["flux_rest_1e17"].sum()),
            "flux_1e17": f,
            "flux_err_1e17": e,
            "flux_erg_s_cm2": f * FLUX_FACTOR,
            "flux_err_erg_s_cm2": e * FLUX_FACTOR,
            "fwhm_kms": fwhm,
            "fwhm_err_kms": np.nan,
            "velocity_kms": np.nan,
            "norm": np.nan,
            "norm_err": np.nan,
            "n_gauss": int(sub["n_gauss"].sum()),
            "snr": f / e if e > 0 else np.nan,
            "detected": bool(f > 0 and (e <= 0 or f / e >= 3.0)),
            "method": "qgfit_leastsq",
            "notes": "sum of QGfit components; errors added in quadrature; "
                     "flux-weighted FWHM",
        })
    table = pd.concat([table, pd.DataFrame(totals)], ignore_index=True)
    table = table.sort_values(["lambda_rest", "component"], na_position="last").reset_index(drop=True)
    return table


def build_model(data: dict, out: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    wave, flux, err = data["data_rest"][0]
    wave = np.asarray(wave, dtype=float)
    flux = np.asarray(flux, dtype=float)
    err = np.asarray(err, dtype=float)
    cfg = data["config"]
    pars = data["conti"]["pars_set"][0]
    conti = conti_model(wave, pars, cfg)
    line_model = np.zeros_like(wave)
    df = pd.DataFrame(data["line"]["result"][0])
    for _, r in df.iterrows():
        pp = [r["norm"], r["ln_shift"], r["ln_sigma"], r["skew"],
              r["gamma_ratio"], r["FWHM"]]
        line_model += many_lines(np.log(wave), pp, float(r["ln_lambda"]))
    total = conti + line_model
    pd.DataFrame({
        "wave_rest": wave,
        "flux": flux,
        "flux_err": err,
        "continuum": conti,
        "line_model": line_model,
        "total_model": total,
        "residual": flux - total,
    }).to_csv(out / "qgfit_model.csv", index=False)
    return wave, flux, err, conti, line_model, total


def plot_fit(wave, flux, err, conti, line_model, total, data, out: Path) -> None:
    z = float(data["z"])
    cfg = data["config"]
    fig = plt.figure(figsize=(14, 8.5))
    gs = fig.add_gridspec(2, 1, height_ratios=[2.0, 1.15], hspace=0.08)
    ax = fig.add_subplot(gs[0])
    ax.plot(wave, flux, color="0.15", lw=0.7, label="SDSS data")
    ax.fill_between(wave, flux - err, flux + err, color="0.7", alpha=0.35,
                    linewidth=0)
    ax.plot(wave, conti, color="c", ls=":", lw=1.5, label="QGfit continuum")
    ax.plot(wave, total, color="r", ls="--", lw=1.0,
            label="continuum + emission lines")
    for x, label in [(4862.68, r"H$\beta$"), (4960.30, "[O III] 4959"),
                     (5008.24, "[O III] 5007")]:
        ax.axvline(x, color="0.4", lw=0.7, ls="-.")
        ax.text(x, ax.get_ylim()[1], label, rotation=90, va="top", ha="right",
                fontsize=8, color="0.3")
    ax.set_xlim(max(2200.0, float(wave.min())), min(6600.0, float(wave.max())))
    ax.set_ylabel(r"$f_\lambda$ ($10^{-17}$ erg s$^{-1}$ cm$^{-2}$ $\AA^{-1}$)")
    ax.set_title(f"QGfit fit  z={z:.6f}  $\\chi^2_r$={data['conti']['redchi']:.2f}  "
                 f"(rest frame; line model includes all fitted complexes)")
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    ax.grid(alpha=0.2, ls=":")

    ax2 = fig.add_subplot(gs[1])
    m = (wave > 4580) & (wave < 5160)
    ax2.plot(wave[m], (flux - conti)[m], color="0.15", lw=0.9,
             drawstyle="steps-mid", label="data - continuum")
    ax2.fill_between(wave[m], (flux - conti - err)[m], (flux - conti + err)[m],
                     color="0.7", alpha=0.35, linewidth=0)
    ax2.plot(wave[m], line_model[m], color="r", ls="--", lw=1.2,
             label="total line model")
    df = pd.DataFrame(data["line"]["result"][0])
    colors = {"Hbeta_br": "tab:blue", "Hbeta_na": "tab:green",
              "OIII4959": "tab:orange", "OIII5007": "tab:purple"}
    labels = {"Hbeta_br": r"H$\beta$ broad", "Hbeta_na": r"H$\beta$ narrow",
              "OIII4959": "[O III] 4959", "OIII5007": "[O III] 5007"}
    for qname, color in colors.items():
        sub = df[df["linename"] == qname]
        if sub.empty:
            continue
        r = sub.iloc[0]
        if float(r["norm"]) <= 0:
            continue
        pp = [r["norm"], r["ln_shift"], r["ln_sigma"], r["skew"],
              r["gamma_ratio"], r["FWHM"]]
        comp = many_lines(np.log(wave[m]), pp, float(r["ln_lambda"]))
        if np.nanmax(np.abs(comp)) <= 0:
            continue
        ax2.plot(wave[m], comp, color=color, lw=1.3, label=labels[qname])
    ax2.axhline(0, color="0.3", lw=0.6, ls=":")
    ax2.set_xlim(4580, 5160)
    ax2.set_xlabel(r"Rest-frame wavelength ($\AA$)")
    ax2.set_ylabel(r"$f_\lambda$ ($10^{-17}$)")
    ax2.legend(loc="upper right", fontsize=7, frameon=False, ncol=2)
    ax2.grid(alpha=0.2, ls=":")
    fig.savefig(out / "qgfit_fit.png", dpi=170, bbox_inches="tight")
    fig.savefig(out / "qgfit_fit.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_uncertainty(obj, out: Path, data: dict) -> dict:
    """Corner plot + summary of the short continuum MCMC."""
    summary = {
        "enabled": False,
        "note": "continuum MCMC was not run",
    }
    if not hasattr(obj, "out_mcmc"):
        return summary
    out_mcmc = obj.out_mcmc
    flat = out_mcmc.flatchain
    if isinstance(flat, pd.DataFrame):
        samples = np.asarray(flat, dtype=float)
        labels = [str(x) for x in flat.columns]
    else:
        samples = np.asarray(flat, dtype=float)
        labels = [str(x) for x in out_mcmc.var_names]
    summary.update({
        "enabled": True,
        "note": "short emcee chain; plotted subset of free continuum parameters",
        "n_samples": int(samples.shape[0]),
        "n_params": int(samples.shape[1]),
        "nwalkers": int(data["config"].get("conti_nwalkers", 0)),
        "steps": int(data["config"].get("conti_steps", 0)),
        "burn": int(data["config"].get("conti_burn", 0)),
        "thin": int(data["config"].get("conti_thin", 1)),
        "acceptance_fraction_mean": (
            float(np.mean(np.asarray(out_mcmc.acceptance_fraction)))
            if hasattr(out_mcmc, "acceptance_fraction") else None),
        "redchi": float(out_mcmc.redchi),
        "converged": False,
        "convergence_note": (
            "Short demonstration chain; emcee warns that the chain is shorter "
            "than 50 integrated autocorrelation times.  Do not treat the "
            "quantiles as a converged posterior."),
    })
    # Per-parameter quantiles.
    q16, q50, q84 = np.quantile(samples, [0.16, 0.50, 0.84], axis=0)
    pd.DataFrame({
        "parameter": labels,
        "q16": q16,
        "median": q50,
        "q84": q84,
        "err_1sigma": (q84 - q16) / 2.0,
        "mean": samples.mean(axis=0),
        "std": samples.std(axis=0),
    }).to_csv(out / "qgfit_mcmc_summary.csv", index=False)

    try:
        import logging
        import corner
        root_level = logging.root.level
        logging.getLogger().setLevel(logging.ERROR)
        # Plot the continuum parameters that control the shape and
        # normalization of the model.  The full chain is preserved in the
        # pickled QGfit result and summarised in qgfit_mcmc_summary.csv.
        keep_names = ["pl_norm", "pl_slope1", "pl_slope2", "fe_uv_norm",
                      "fe_op_norm", "m_s", "a_v", "sigma", "age_young",
                      "age_old", "f_old", "host_shift"]
        keep = [i for i, n in enumerate(labels) if n in keep_names]
        if not keep:
            keep = list(range(len(labels)))
        plot_samples = samples[:, keep]
        plot_labels = [labels[i] for i in keep]
        fig = plt.figure(figsize=(13, 13))
        corner.corner(plot_samples, labels=plot_labels, show_titles=True,
                      title_fmt=".4g", quantiles=[0.16, 0.5, 0.84],
                      plot_datapoints=True, plot_density=False,
                      fill_contours=True, color="tab:blue", fig=fig,
                      label_kwargs={"fontsize": 9})
        logging.getLogger().setLevel(root_level)
        fig.suptitle(
            "QGfit continuum MCMC (short: %d walkers x %d steps; not converged)"
            % (summary["nwalkers"], summary["steps"]),
            y=0.995, fontsize=12)
        fig.savefig(out / "qgfit_uncertainty.png", dpi=150, bbox_inches="tight")
        fig.savefig(out / "qgfit_uncertainty.pdf", bbox_inches="tight")
        plt.close(fig)
        summary["figure"] = "qgfit_uncertainty.png"
    except Exception as exc:  # noqa: BLE001
        log(f"[warn] corner plot failed: {exc}")
        summary["figure_error"] = str(exc)
    return summary


def plot_line_errors(table: pd.DataFrame, out: Path) -> None:
    wanted = [("Hbeta", "broad", r"H$\beta$ broad"),
              ("Hbeta", "total", r"H$\beta$ total"),
              ("OIII5007", "total", r"[O III] 5007"),
              ("OIII4959", "total", r"[O III] 4959")]
    vals, errs, labels = [], [], []
    for line, comp, label in wanted:
        sub = table[(table["line"] == line) & (table["component"] == comp)]
        if sub.empty and comp == "total":
            sub = table[table["line"] == line]
        if sub.empty:
            continue
        r = sub.iloc[0]
        vals.append(float(r["flux_1e17"]))
        errs.append(float(r["flux_err_1e17"]))
        labels.append(label)
    if not vals:
        return
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    x = np.arange(len(vals))
    ax.bar(x, vals, yerr=errs, capsize=4, color="tab:blue", alpha=0.75)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel(r"Line flux ($10^{-17}$ erg s$^{-1}$ cm$^{-2}$)")
    ax.set_title("QGfit line fluxes and least-squares covariance errors\n"
                 "(not MCMC; see qgfit_uncertainty.png for the continuum chain)")
    for xi, (v, e) in enumerate(zip(vals, errs)):
        ax.text(xi, v + max(e, 0.01 * max(vals)), f"{v:.1f} ± {e:.1f}",
                ha="center", va="bottom", fontsize=8)
    ax.grid(axis="y", alpha=0.2, ls=":")
    fig.tight_layout()
    fig.savefig(out / "qgfit_line_errors.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def _to_float(value: Any) -> float | None:
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def read_reference(reference: Path, tool: str) -> dict:
    """Return observed-frame line fluxes in 1e-17 units for a sibling tool."""
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
    rows = []
    ratios = []
    qg_ratio = None
    if "Hbeta" in qg and "OIII5007" in qg and qg["OIII5007"][0] > 0:
        qg_ratio = qg["Hbeta"][0] / qg["OIII5007"][0]
        qg_ratio_err = abs(qg_ratio) * math.sqrt(
            (qg["Hbeta"][1] / qg["Hbeta"][0]) ** 2 +
            (qg["OIII5007"][1] / qg["OIII5007"][0]) ** 2) if qg["Hbeta"][0] else None
    else:
        qg_ratio_err = None
    if qg_ratio is not None:
        ratios.append({"ratio": "Hbeta/OIII5007", "tool": "qgfit",
                       "value": qg_ratio, "err": qg_ratio_err})
    for tool in tools:
        ref = read_reference(reference, tool)
        for line in ("Hbeta", "OIII5007"):
            if line not in qg or line not in ref:
                continue
            qv, qe = qg[line]
            rv, re = ref[line]
            ratio = qv / rv if rv else None
            rows.append({
                "line": line,
                "qgfit_1e17": qv,
                "qgfit_err_1e17": qe,
                "reference_tool": tool,
                "reference_1e17": rv,
                "reference_err_1e17": re,
                "ratio_qgfit_over_reference": ratio,
                "notes": ("QGfit observed-frame flux = rest-frame integral "
                          "/(1+z)^2; reference values are the siblings' "
                          "published tables"),
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
    pd.DataFrame(rows).to_csv(out / "qgfit_comparison.csv", index=False)
    pd.DataFrame(ratios).to_csv(out / "qgfit_ratio_comparison.csv", index=False)
    return {
        "qgfit_hbeta_oiii5007": qg_ratio,
        "qgfit_hbeta_oiii5007_err": qg_ratio_err,
        "references": rows,
        "ratios": ratios,
    }


def run(args) -> int:
    t0 = time.time()
    cfg = load_config(Path(args.config))
    out = ensure_dir(Path(args.output))
    spectrum_path = find_spectrum(Path(args.input))
    spec = read_sdss(spectrum_path, bool(cfg.get("mask_and_mask", True)))
    z = args.z if args.z is not None else cfg.get("z")
    if z is None:
        z = spec.get("z")
    if z is None:
        raise ValueError("redshift not supplied and not found in the FITS header")
    z = float(z)
    ra = args.ra if args.ra is not None else spec.get("ra")
    dec = args.dec if args.dec is not None else spec.get("dec")
    name = args.name or "qgfit"

    qcfg = dict(cfg.get("qgfit", {}))
    qcfg.setdefault("line_fit", True)
    qcfg.setdefault("plot", False)
    qcfg.setdefault("save_conti_chains", True)
    qcfg.setdefault("write", True)
    qcfg.setdefault("prop", True)
    qcfg.setdefault("comp_plot", ["Ha", "Hb", "Hd", "He", "Hr", "MgII",
                                  "CIII", "CIV", "Lya"])

    log(f"[qgfit] input={spectrum_path}")
    log(f"[qgfit] z={z:.8f} ra={ra} dec={dec}")
    log(f"[qgfit] good pixels={spec['n_good']}/{spec['n_total']} "
        f"rest range={spec['wave'].min()/(1+z):.1f}-"
        f"{spec['wave'].max()/(1+z):.1f} A")
    if qcfg.get("do_deredden", True) and not list(Path(os.environ["SFD_PATH"]).glob("SFD_dust_*.fits")):
        raise RuntimeError(
            "do_deredden=true but no SFD maps were found in SFD_PATH; mount "
            "the four sfdmap FITS files at /opt/sfd or set do_deredden=false")

    input_spec = {
        "wave": spec["wave"],
        "flux": spec["flux"],
        "fluxerr": spec["fluxerr"],
        "ra": ra,
        "dec": dec,
    }
    obj = QGfitObj([input_spec], z=z, path=str(out) + "/", name=name, **qcfg)
    log(f"[qgfit] fitting (conti_mcmc={qcfg.get('conti_mcmc', False)}, "
        f"line_mcmc={qcfg.get('line_mcmc', False)})")
    data = obj.run_fit()
    elapsed = time.time() - t0

    table = line_table(data)
    table.to_csv(out / "qgfit_lines.csv", index=False)
    wave, flux, err, conti, line_model, total = build_model(data, out)
    plot_fit(wave, flux, err, conti, line_model, total, data, out)
    mcmc_summary = plot_uncertainty(obj, out, data)
    plot_line_errors(table, out)

    # Try QGfit's native PDF; it is not required for the product set.
    native_note = "ok"
    try:
        from qgfit import plot as qgplot
        native_pdf = out / "qgfit_native.pdf"
        qgplot.PlotObj(data, str(native_pdf)).plot_obj()
        log(f"[qgfit] native figure: {native_pdf.name}")
    except Exception as exc:  # noqa: BLE001
        native_note = f"native plot skipped: {exc}"
        log(f"[warn] {native_note}")
        for p in (out / "qgfit_native.pdf", out / "qgfit_native_corner.jpg"):
            try:
                p.unlink()
            except FileNotFoundError:
                pass

    comparison = write_comparison(
        table, Path(args.reference) if args.reference else Path("/nonexistent"),
        list(cfg.get("reference_tools", [])), out)

    def first_line(line: str, component: str = "total"):
        sub = table[(table["line"] == line) & (table["component"] == component)]
        if sub.empty:
            sub = table[table["line"] == line]
        return sub.iloc[0] if not sub.empty else None

    hb = first_line("Hbeta")
    o3 = first_line("OIII5007")
    hb_b = first_line("Hbeta", "broad")
    line_summary = {
        "n_rows": int(len(table)),
        "n_detected": int(table["detected"].sum()),
        "Hbeta_total_1e17": float(hb["flux_1e17"]) if hb is not None else None,
        "Hbeta_broad_1e17": float(hb_b["flux_1e17"]) if hb_b is not None else None,
        "OIII5007_total_1e17": float(o3["flux_1e17"]) if o3 is not None else None,
        "Hbeta_OIII5007": comparison.get("qgfit_hbeta_oiii5007"),
        "Hbeta_OIII5007_err": comparison.get("qgfit_hbeta_oiii5007_err"),
    }

    import numpy as _np
    import scipy as _scipy
    import pandas as _pd
    import astropy as _astropy
    import lmfit as _lmfit
    import emcee as _emcee
    import kapteyn as _kapteyn
    versions = {
        "python": sys.version.split()[0],
        "qgfit": QGFIT_VERSION,
        "numpy": _np.__version__,
        "scipy": _scipy.__version__,
        "pandas": _pd.__version__,
        "astropy": _astropy.__version__,
        "lmfit": _lmfit.__version__,
        "emcee": _emcee.__version__,
        "kapteyn": _kapteyn.__version__,
        "matplotlib": matplotlib.__version__,
    }
    config_keys = [
        "wave_range", "do_deredden", "conti_pl", "conti_fe_uv", "conti_fe_op",
        "conti_balmer", "conti_host", "host_zcut", "host_tie", "check_kmpfit",
        "check_nelder", "conti_redchi_limit", "line_redchi_limit",
        "conti_mcmc", "conti_nwalkers", "conti_steps", "conti_burn",
        "conti_thin", "line_fit", "line_mcmc", "mask_lowSN", "SN_mask",
        "test_add_broad", "tie_width", "tie_shift", "tie_flux",
        "fwhm_broad_min", "fwhm_broad_max", "fwhm_narrow_min",
        "fwhm_narrow_max", "comp_plot", "plot", "prop",
    ]
    effective = {k: data["config"].get(k) for k in config_keys}
    run = {
        "tool": "qgfit",
        "method": "qgfit_lmfit_leastsq",
        "native_code": "QGfit 1.0.0 (github.com/qian-yang/QGfit, commit 3aed692)",
        "versions": versions,
        "input": {
            "file": str(spectrum_path),
            "z": z,
            "ra": ra,
            "dec": dec,
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
        "config_effective": effective,
        "continuum": {
            "redchi": float(data["conti"]["redchi"]),
            "chisqr": float(data["conti"]["chisqr"]),
            "ndata": int(data["conti"]["ndata"]),
            "nvarys": int(data["conti"]["nvarys"]),
            "method": data["conti"]["method"],
            "kmpfit_attempted": bool(
                effective.get("check_kmpfit") and
                float(data["conti"]["redchi"]) > float(effective.get("conti_redchi_limit") or 0)),
            "mcmc": mcmc_summary,
            "pars": jsonable(data["conti"]["pars_set"][0]),
            "stderr": jsonable(data["conti"]["stderr_set"][0]),
        },
        "line_fit": {
            "controls": {
                "line_mcmc": bool(effective.get("line_mcmc")),
                "mask_lowSN": bool(effective.get("mask_lowSN")),
                "test_add_broad": bool(effective.get("test_add_broad")),
                "tie_width": bool(effective.get("tie_width")),
                "tie_shift": bool(effective.get("tie_shift")),
                "tie_flux": bool(effective.get("tie_flux")),
            },
            **line_summary,
        },
        "statistical_mode": {
            "continuum": "emcee MCMC via lmfit (real chain, short demonstration)",
            "line": "least-squares covariance from QGfit norm_stderr",
            "converged": False,
            "note": ("The MCMC is intentionally short (see continuum.mcmc). "
                     "Line flux errors are not MCMC errors."),
        },
        "comparison": comparison,
        "runtime": {"total_sec": elapsed},
        "scope": {
            "galactic_dereddening": bool(qcfg.get("do_deredden", False)),
            "host_galaxy": bool(qcfg.get("conti_host", True)),
            "fe_uv": bool(qcfg.get("conti_fe_uv", True)),
            "fe_optical": bool(qcfg.get("conti_fe_op", True)),
            "balmer_continuum": bool(qcfg.get("conti_balmer", False)),
            "line_mcmc": bool(qcfg.get("line_mcmc", False)),
            "native_plot": native_note,
            "note": ("QGfit is run on the observed SDSS spectrum without "
                     "Galactic dereddening; the sibling tools also use the "
                     "SDSS spectrum with EBV=0.  The H-beta flux is the sum "
                     "of the QGfit broad+narrow components; QGfit's BIC test "
                     "can remove a narrow component when it is not required."),
        },
        "line_measurements": table.to_dict(orient="records"),
    }
    with (out / "run.json").open("w") as fh:
        json.dump(jsonable(run), fh, indent=2, sort_keys=False)
    log(f"[qgfit] done in {elapsed:.1f}s -> {out}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True,
                   help="SDSS FITS file or a directory containing spec-*.fits")
    p.add_argument("--output", required=True)
    p.add_argument("--config", default="/app/config/config.json")
    p.add_argument("--z", type=float, default=None)
    p.add_argument("--ra", type=float, default=None)
    p.add_argument("--dec", type=float, default=None)
    p.add_argument("--name", default="qgfit")
    p.add_argument("--reference", default=None,
                   help="directory with sibling tool outputs (pyqsofit_uv, ...)")
    args = p.parse_args(argv)
    try:
        return run(args)
    except Exception as exc:  # noqa: BLE001
        log(f"[qgfit] ERROR: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
