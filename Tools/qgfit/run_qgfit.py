#!/usr/bin/env python3
"""QGfit adapter for the canonical SDSS QSO inputs.

The adapter reads one SDSS spectrum (``spec-*.fits`` with a ``COADD``-style
table), calls QGfit's ``QGfitObj`` continuum + emission-line fitter, and writes
a compact, tool-neutral product set:

    qgfit_lines.csv                 line fluxes, FWHM, velocity, components
    qgfit_model.csv                 rest-frame data / continuum / line / total
    qgfit_fit.png/.pdf              data, continuum and H-beta/[O III] zoom
    qgfit_zoom.png/.pdf             per-complex emission-line zooms
    qgfit_residual.png/.pdf         full and H-beta/[O III] residuals
    qgfit_uncertainty.png/.pdf      continuum-MCMC corner plot
    qgfit_line_errors.png           line-flux error bars
    qgfit_mcmc_summary.csv          per-parameter continuum-MCMC quantiles
    qgfit_line_mcmc_summary.csv     per-complex line-MCMC diagnostics
    qgfit_mcmc_chain.npz            flattened continuum chain (compressed)
    qgfit_comparison.csv            QGfit vs sibling total line fluxes
    qgfit_component_comparison.csv  broad/narrow/wing component comparison
    qgfit_ratio_comparison.csv      H-beta/[O III] 5007 for QGfit and siblings
    qgfit_config.effective.json     effective QGfit configuration
    run.json                        provenance, controls, method and timings

Method labelling
----------------
* Continuum and lines: QGfit's lmfit least-squares fit.  QGfit's KMPFIT
  fallback is attempted exactly as configured and the chosen method is
  recorded.
* Continuum uncertainties: a real emcee chain.  The production configuration
  uses 100 walkers x 1500 steps (burn 300).  The adapter reports the
  acceptance fraction, integrated autocorrelation time and N_tau, and sets
  ``converged`` only when N_tau >= 50 and the acceptance is sane.
* Line uncertainties: QGfit's per-complex emcee chain when it is stable.
  QGfit runs one independent chain per emission-line complex.  If a complex
  has only one varying line QGfit does not run a chain; those lines keep the
  least-squares covariance error and are labelled ``qgfit_leastsq``.  If a
  chain is unstable the adapter keeps the LSQ errors and labels the run
  ``lsq_lines``; it is never described as MCMC in that case.

Flux units
-----------
SDSS ``FLUX`` is in 1e-17 erg s-1 cm-2 A-1.  QGfit converts the observed
spectrum to the rest frame with ``f_rest = f_obs (1+z)^3`` and
``lambda_rest = lambda_obs/(1+z)``.  Its ``line_info['flux']`` is the integral
over rest-frame wavelength in units of 1e-17 erg s-1 cm-2.  The observed-frame
line flux is the rest-frame integral divided by (1+z)^2.  The adapter records
both quantities.  ``qgfit_model.csv`` is rest-frame f_lambda, i.e. it is a
factor (1+z)^3 above the observed-frame flux density plotted by some sibling
tools; do not compare raw continuum levels without that factor.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import pickle
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
from qgfit.line import LineFit, many_lines
from qgfit import __version__ as QGFIT_VERSION

try:  # emcee is a hard QGfit dependency, but keep the adapter importable.
    import emcee
except Exception:  # noqa: BLE001
    emcee = None

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
    "OIII5007c": "OIII5007",
    "OIII5007w": "OIII5007",
    "OIII4959": "OIII4959",
    "OIII4959c": "OIII4959",
    "OIII4959w": "OIII4959",
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

COMPONENT_ORDER = {"broad": 0, "mix": 1, "narrow": 2, "total": 3}


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
    cfg.setdefault("reference_tools", [
        "pyqsofit_uv", "gandalf_line", "s3fit_line",
        "galspec_line", "pyqsofitspec_line",
    ])
    return cfg


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _to_float(value: Any) -> float | None:
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def _num(value: Any) -> float:
    v = _to_float(value)
    return v if v is not None else float("nan")


def _fwhm_from_sigma(sigma: Any) -> float | None:
    s = _to_float(sigma)
    return s * 2.354820045 if s is not None else None


def _finite_array(value: Any) -> np.ndarray | None:
    if value is None:
        return None
    try:
        arr = np.asarray(value, dtype=float)
    except Exception:
        return None
    if arr.size == 0 or not np.all(np.isfinite(arr)):
        return None
    return arr


# ---------------------------------------------------------------------------
# Line table
# ---------------------------------------------------------------------------

def line_table(data: dict, line_mcmc_stable: bool) -> pd.DataFrame:
    """Build the compact line table from a QGfit result dictionary.

    The flux stored by QGfit in ``line_info`` is the integral of the fitted
    profile over rest-frame wavelength.  The least-squares error is derived
    from the covariance of the profile norm (``norm_stderr``); when a stable
    line-MCMC chain exists QGfit's own ``flux_err`` from that chain is used
    instead and the row is labelled ``qgfit_line_mcmc``.
    """
    z = float(data["z"])
    df = pd.DataFrame(data["line"].get("result", [None])[0]).copy()
    info = pd.DataFrame(data["line"].get("line_info", [None])[0]).copy()
    if df.empty or info.empty:
        raise RuntimeError("QGfit result has no line table (line_fit=False?)")
    df["linename"] = df["linename"].astype(str)
    info["linename"] = info["linename"].astype(str)
    df["compname"] = df["compname"].astype(str)
    info["comp"] = info["comp"].astype(str)

    chain_cols = [c for c in df.columns if c.endswith("_chain")]

    rows_meta = []
    for (comp, qname), sub in df.groupby(["compname", "linename"], sort=False):
        first = sub.iloc[0]
        norm_vals = pd.to_numeric(sub["norm"], errors="coerce").values
        norm = float(np.nansum(norm_vals))
        err_vals = pd.to_numeric(sub["norm_stderr"], errors="coerce").values
        norm_err = float(np.sqrt(np.nansum(err_vals ** 2)))
        chain = None
        if len(sub) == 1 and "norm_chain" in sub.columns:
            chain = _finite_array(sub.iloc[0]["norm_chain"])
        rows_meta.append({
            "comp": comp,
            "linename": qname,
            "lambda": _num(first["lambda"]),
            "ln_shift": _num(first["ln_shift"]),
            "ln_sigma": _num(first["ln_sigma"]),
            "skew": _num(first["skew"]),
            "gamma_ratio": _num(first["gamma_ratio"]),
            "FWHM": _num(first["FWHM"]),
            "FWHM_stderr": _num(first["FWHM_stderr"]),
            "type": str(first["type"]),
            "norm": norm,
            "norm_stderr": norm_err,
            "n_gauss": int(len(sub)),
            "norm_chain": chain,
        })
    meta = pd.DataFrame(rows_meta)
    merged = info.merge(meta, left_on=["comp", "linename"],
                        right_on=["comp", "linename"], how="left",
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
        norm = float(r["norm"]) if pd.notna(r["norm"]) else 0.0
        norm_err = float(r["norm_stderr"]) if pd.notna(r["norm_stderr"]) else 0.0
        fwhm = float(r["FWHM"]) if pd.notna(r["FWHM"]) else np.nan
        fwhm_err = (float(r["FWHM_stderr"])
                    if pd.notna(r["FWHM_stderr"]) else np.nan)
        fwhm_err_mcmc = _to_float(r.get("FWHM_err"))
        shift = float(r["ln_shift"]) if pd.notna(r["ln_shift"]) else np.nan
        component = str(r["type"]) if pd.notna(r["type"]) else "unknown"
        # First-order LSQ covariance: flux is linear in norm, so
        # sigma(flux) = flux * sigma(norm)/norm.  This includes the profile
        # integral factor and is more accurate than sigma(norm)*lambda.
        rest_err_lsq = abs(rest_flux * norm_err / norm) if norm > 0 else 0.0
        rest_err_mcmc = _to_float(r.get("flux_err"))
        norm_chain = r.get("norm_chain")
        draw = None
        if norm_chain is not None and norm > 0:
            draw = np.asarray(norm_chain, dtype=float) * (rest_flux / norm)
        use_mcmc = bool(
            line_mcmc_stable
            and rest_err_mcmc is not None
            and rest_err_mcmc > 0
            and draw is not None
            and draw.size > 10
        )
        rest_err = float(rest_err_mcmc) if use_mcmc else float(rest_err_lsq)
        obs_flux = rest_flux / (1.0 + z) ** 2
        obs_err = rest_err / (1.0 + z) ** 2
        snr = obs_flux / obs_err if obs_err > 0 else np.nan
        detected = bool(obs_flux > 0 and (not np.isfinite(snr) or snr >= 3.0))
        p16 = p84 = np.nan
        if use_mcmc and draw is not None:
            p16, _, p84 = np.quantile(draw, [0.16, 0.50, 0.84])
            p16 = float(p16 / (1.0 + z) ** 2)
            p84 = float(p84 / (1.0 + z) ** 2)
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
            "fwhm_err_kms": (float(fwhm_err_mcmc) if use_mcmc and
                             fwhm_err_mcmc is not None else fwhm_err),
            "velocity_kms": shift * C_KMS if np.isfinite(shift) else np.nan,
            "norm": norm,
            "norm_err": norm_err,
            "n_gauss": int(r["n_gauss"]) if pd.notna(r["n_gauss"]) else 1,
            "snr": snr,
            "detected": detected,
            "flux_err_method": "mcmc" if use_mcmc else "leastsq",
            "flux_p16_1e17": p16,
            "flux_p84_1e17": p84,
            "method": "qgfit_line_mcmc" if use_mcmc else "qgfit_leastsq",
            "notes": ("QGfit profile type=%s; flux is the rest-frame integral "
                      "divided by (1+z)^2; error from %s"
                      % (component, "the per-complex emcee chain"
                         if use_mcmc else
                         "the least-squares norm covariance (width/shift "
                         "terms neglected)")),
        })

    table = pd.DataFrame(rows)
    if table.empty:
        return table

    # Build total rows for the lines used in the cross-tool comparison.
    # When every component has a stable chain the total flux error is measured
    # from the sum of the *draws*, so correlated components (the [O III]
    # doublet and the broad/narrow Balmer components) are handled correctly.
    totals = []
    for line in sorted(set(table["line"]) & TOTAL_LINES):
        sub = table[table["line"] == line]
        if len(sub) < 2:
            continue
        comp_rows = merged[merged["linename"].isin(sub["qgfit_line"])]
        draws = []
        all_mcmc = True
        for _, rr in comp_rows.iterrows():
            norm = float(rr["norm"]) if pd.notna(rr["norm"]) else 0.0
            rest_flux = float(rr["flux"]) if pd.notna(rr["flux"]) else 0.0
            chain = _finite_array(rr.get("norm_chain"))
            if rest_flux == 0 or norm <= 0:
                # A component whose BIC-cleaned norm is exactly zero does not
                # contribute flux or uncertainty; do not let it break the
                # correlated-error calculation for the remaining components.
                continue
            if line_mcmc_stable and chain is not None:
                draws.append(chain * (rest_flux / norm))
            else:
                all_mcmc = False
        f = float(sub["flux_1e17"].sum())
        total_draw = None
        if all_mcmc and draws and len({d.size for d in draws}) == 1:
            total_draw = np.sum(np.vstack(draws), axis=0) / (1.0 + z) ** 2
        if total_draw is not None and np.all(np.isfinite(total_draw)):
            e = float((np.quantile(total_draw, 0.84) -
                       np.quantile(total_draw, 0.16)) / 2.0)
            p16 = float(np.quantile(total_draw, 0.16))
            p84 = float(np.quantile(total_draw, 0.84))
            method = "qgfit_line_mcmc"
            err_method = "mcmc"
        else:
            e = float(np.sqrt(np.sum(sub["flux_err_1e17"].values ** 2)))
            p16 = p84 = np.nan
            method = "qgfit_leastsq"
            err_method = "leastsq"
        positive = sub[sub["flux_1e17"] > 0]
        if len(positive) > 0 and positive["flux_1e17"].sum() > 0:
            fwhm = float(np.average(positive["fwhm_kms"].fillna(0),
                                    weights=positive["flux_1e17"]))
        else:
            fwhm = (float(sub["fwhm_kms"].dropna().iloc[0])
                    if sub["fwhm_kms"].notna().any() else np.nan)
        lam = (float(sub["lambda_rest"].dropna().iloc[0])
               if sub["lambda_rest"].notna().any() else np.nan)
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
            "flux_err_method": err_method,
            "flux_p16_1e17": p16,
            "flux_p84_1e17": p84,
            "method": method,
            "notes": ("sum of QGfit components; error from the sum of the "
                      "MCMC draws" if err_method == "mcmc" else
                      "sum of QGfit components; errors added in quadrature; "
                      "flux-weighted FWHM"),
        })
    table = pd.concat([table, pd.DataFrame(totals)], ignore_index=True)
    table["_component_order"] = table["component"].map(COMPONENT_ORDER).fillna(9)
    table = table.sort_values(["lambda_rest", "_component_order"],
                              na_position="last").drop(columns=["_component_order"])
    return table.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Model and figures
# ---------------------------------------------------------------------------

def build_model(data: dict, out: Path):
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
        norm = float(r["norm"]) if pd.notna(r["norm"]) else 0.0
        if norm <= 0:
            continue
        pp = [norm, r["ln_shift"], r["ln_sigma"], r["skew"],
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


def _line_component(wave: np.ndarray, row, mask: np.ndarray | None = None) -> np.ndarray:
    norm = float(row["norm"]) if pd.notna(row["norm"]) else 0.0
    if norm <= 0:
        return np.zeros_like(wave)
    pp = [norm, row["ln_shift"], row["ln_sigma"], row["skew"],
          row["gamma_ratio"], row["FWHM"]]
    return many_lines(np.log(wave), pp, float(row["ln_lambda"]))


def plot_fit(wave, flux, err, conti, line_model, total, data, out: Path) -> None:
    z = float(data["z"])
    fig = plt.figure(figsize=(14, 10.0))
    gs = fig.add_gridspec(3, 1, height_ratios=[2.2, 1.25, 0.9], hspace=0.08)
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

    m = (wave > 4580) & (wave < 5160)
    ax2 = fig.add_subplot(gs[1])
    ax2.plot(wave[m], (flux - conti)[m], color="0.15", lw=0.9,
             drawstyle="steps-mid", label="data - continuum")
    ax2.fill_between(wave[m], (flux - conti - err)[m], (flux - conti + err)[m],
                     color="0.7", alpha=0.35, linewidth=0)
    ax2.plot(wave[m], line_model[m], color="r", ls="--", lw=1.2,
             label="total line model")
    df = pd.DataFrame(data["line"]["result"][0])
    colors = {"Hbeta_br": "tab:blue", "Hbeta_na": "tab:green",
              "OIII4959": "tab:orange", "OIII5007": "tab:purple",
              "OIII4959w": "tab:olive", "OIII5007w": "tab:brown"}
    labels = {"Hbeta_br": r"H$\beta$ broad", "Hbeta_na": r"H$\beta$ narrow",
              "OIII4959": "[O III] 4959", "OIII5007": "[O III] 5007",
              "OIII4959w": "[O III] 4959 wing",
              "OIII5007w": "[O III] 5007 wing"}
    for qname, color in colors.items():
        sub = df[df["linename"] == qname]
        if sub.empty:
            continue
        r = sub.iloc[0]
        comp = _line_component(wave[m], r)
        if np.nanmax(np.abs(comp)) <= 0:
            continue
        ax2.plot(wave[m], comp, color=color, lw=1.3, label=labels[qname])
    ax2.axhline(0, color="0.3", lw=0.6, ls=":")
    ax2.set_xlim(4580, 5160)
    ax2.set_ylabel(r"$f_\lambda$ ($10^{-17}$)")
    ax2.legend(loc="upper right", fontsize=7, frameon=False, ncol=2)
    ax2.grid(alpha=0.2, ls=":")

    ax3 = fig.add_subplot(gs[2], sharex=ax2)
    resid = flux - total
    ax3.axhspan(-1, 1, color="0.85", alpha=0.6, label=r"$\pm1\sigma$")
    ax3.plot(wave[m], (resid / err)[m], color="0.15", lw=0.8,
             drawstyle="steps-mid")
    ax3.axhline(0, color="0.3", lw=0.6, ls=":")
    ax3.set_xlabel(r"Rest-frame wavelength ($\AA$)")
    ax3.set_ylabel(r"residual / $\sigma$")
    ax3.set_ylim(-8, 8)
    ax3.grid(alpha=0.2, ls=":")
    fig.savefig(out / "qgfit_fit.png", dpi=170, bbox_inches="tight")
    fig.savefig(out / "qgfit_fit.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_zoom(wave, flux, err, conti, line_model, total, data, out: Path) -> None:
    """One zoom panel per fitted emission-line complex."""
    comps = pd.DataFrame(data["line"]["comps"][0])
    df = pd.DataFrame(data["line"]["result"][0])
    comps = comps[comps["ndata"] > 0]
    if comps.empty:
        return
    ncols = 3
    nrows = int(math.ceil(len(comps) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.0 * ncols, 3.0 * nrows),
                             squeeze=False)
    resid = flux - total
    for i, (_, comp) in enumerate(comps.iterrows()):
        ax = axes[i // ncols][i % ncols]
        name = str(comp["compname"])
        lo = max(float(comp["minwav"]), float(wave.min()))
        hi = min(float(comp["maxwav"]), float(wave.max()))
        m = (wave >= lo) & (wave <= hi)
        if m.sum() < 5:
            ax.axis("off")
            continue
        ax.plot(wave[m], flux[m], color="0.15", lw=0.7, label="data")
        ax.fill_between(wave[m], flux[m] - err[m], flux[m] + err[m],
                        color="0.75", alpha=0.3, linewidth=0)
        ax.plot(wave[m], conti[m], color="c", ls=":", lw=1.1,
                label="continuum")
        ax.plot(wave[m], total[m], color="r", ls="--", lw=1.0,
                label="model")
        sub = df[df["compname"] == name]
        for j, (_, r) in enumerate(sub.iterrows()):
            comp_model = _line_component(wave[m], r)
            if np.nanmax(np.abs(comp_model)) <= 0:
                continue
            ax.plot(wave[m], comp_model, lw=1.0, alpha=0.9,
                    label=str(r["linename"]))
        ax.set_title("%s  $\\chi^2_r$=%.2f" % (name, float(comp["redchi"])),
                     fontsize=9)
        ax.set_xlim(lo, hi)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.2, ls=":")
        if i == 0:
            ax.legend(fontsize=6, frameon=False, loc="best")
    for j in range(len(comps), nrows * ncols):
        axes[j // ncols][j % ncols].axis("off")
    fig.suptitle("QGfit emission-line complexes (rest frame; all fitted lines)",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out / "qgfit_zoom.png", dpi=150, bbox_inches="tight")
    fig.savefig(out / "qgfit_zoom.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_residual(wave, flux, err, total, out: Path) -> None:
    resid = (flux - total) / err
    fig, axes = plt.subplots(2, 1, figsize=(13, 6.0),
                             gridspec_kw={"height_ratios": [2.0, 1.2]})
    ax = axes[0]
    ax.plot(wave, resid, color="0.15", lw=0.7)
    ax.axhline(0, color="0.3", lw=0.7, ls=":")
    for y in (-1, 1):
        ax.axhline(y, color="tab:red", lw=0.7, ls="--")
    for y in (-2, 2):
        ax.axhline(y, color="tab:orange", lw=0.5, ls=":")
    ax.set_xlim(max(2200.0, float(wave.min())), min(6600.0, float(wave.max())))
    ax.set_ylabel(r"$(\mathrm{data}-\mathrm{model})/\sigma$")
    ax.set_title("QGfit full-spectrum residual")
    ax.grid(alpha=0.2, ls=":")
    ax2 = axes[1]
    m = (wave > 4580) & (wave < 5160)
    ax2.plot(wave[m], resid[m], color="0.15", lw=0.9, drawstyle="steps-mid")
    ax2.axhline(0, color="0.3", lw=0.7, ls=":")
    for y in (-1, 1):
        ax2.axhline(y, color="tab:red", lw=0.7, ls="--")
    ax2.set_xlabel(r"Rest-frame wavelength ($\AA$)")
    ax2.set_ylabel(r"residual / $\sigma$")
    ax2.set_xlim(4580, 5160)
    ax2.grid(alpha=0.2, ls=":")
    fig.tight_layout()
    fig.savefig(out / "qgfit_residual.png", dpi=170, bbox_inches="tight")
    fig.savefig(out / "qgfit_residual.pdf", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# MCMC diagnostics
# ---------------------------------------------------------------------------

def _autocorr(flat: np.ndarray, nwalkers: int) -> tuple[np.ndarray | None, int]:
    """Return per-parameter integrated autocorrelation times and N_steps."""
    if emcee is None or flat.ndim != 2 or nwalkers < 2:
        return None, 0
    nsteps = flat.shape[0] // nwalkers
    if nsteps < 10:
        return None, nsteps
    chain = flat[: nsteps * nwalkers].reshape(nsteps, nwalkers, flat.shape[1])
    try:
        tau = np.asarray(emcee.autocorr.integrated_time(chain, quiet=True),
                         dtype=float)
    except Exception:
        return None, nsteps
    if not np.all(np.isfinite(tau)):
        return None, nsteps
    return tau, nsteps


def continuum_mcmc_diagnostics(obj, data: dict, out: Path) -> dict:
    cfg = data["config"]
    summary = {
        "enabled": bool(cfg.get("conti_mcmc", False)),
        "note": "continuum MCMC was not run",
        "converged": False,
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
    nwalkers = int(cfg.get("conti_nwalkers", 0) or 0)
    steps = int(cfg.get("conti_steps", 0) or 0)
    burn = int(cfg.get("conti_burn", 0) or 0)
    thin = int(cfg.get("conti_thin", 1) or 1)
    acc = (np.asarray(out_mcmc.acceptance_fraction, dtype=float)
           if hasattr(out_mcmc, "acceptance_fraction") else np.array([]))
    acc_mean = float(np.mean(acc)) if acc.size else None
    acc_min = float(np.min(acc)) if acc.size else None
    tau, nsteps = _autocorr(samples, nwalkers)
    tau_max = float(np.max(tau)) if tau is not None and tau.size else None
    n_tau = float(nsteps / tau_max) if tau_max and tau_max > 0 else None

    # Posterior-width check.  lmfit's LSQ stderr is scaled by sqrt(redchi);
    # for a Gaussian posterior with the known per-pixel errors the emcee
    # marginal width should be stderr_lsq/sqrt(redchi).  A short chain
    # initialised in a tiny ball around the LSQ solution gives a width that
    # is far too small; this check catches that failure mode.
    stderr_lsq = data.get("conti", {}).get("stderr_set", [{}])[0]
    redchi = float(data["conti"].get("redchi", np.nan))
    width_rows = []
    for i, name in enumerate(labels):
        p = None
        if hasattr(obj, "parf"):
            try:
                p = obj.parf[name]
            except (KeyError, TypeError):
                p = None
        lsq = _to_float(stderr_lsq.get(name))
        med = float(np.median(samples[:, i]))
        scaled = (lsq / math.sqrt(redchi)
                  if lsq is not None and redchi > 0 else None)
        at_bound = False
        if p is not None and p.min is not None and p.max is not None:
            lo, hi = float(p.min), float(p.max)
            if hi > lo:
                at_bound = (abs(med - lo) < 1e-3 * (hi - lo) or
                            abs(med - hi) < 1e-3 * (hi - lo))
        well = bool(scaled is not None and scaled > 0 and not at_bound
                    and abs(med) > 0 and scaled < 0.5 * abs(med))
        ratio = float(np.std(samples[:, i], ddof=1) / scaled) if well else None
        width_rows.append({
            "parameter": name, "mcmc_std": float(np.std(samples[:, i], ddof=1)),
            "lsq_stderr": lsq, "lsq_stderr_scaled": scaled,
            "mcmc_over_lsq": ratio, "width_well_constrained": well,
        })
    ratios = [r["mcmc_over_lsq"] for r in width_rows
              if r["mcmc_over_lsq"] is not None]
    width_median = float(np.median(ratios)) if ratios else None
    width_pass = bool(width_median is not None and 0.5 <= width_median <= 2.0)
    redchi_mcmc = float(out_mcmc.redchi)
    redchi_ok = bool(np.isfinite(redchi_mcmc) and
                     redchi_mcmc < max(10.0 * redchi, 1e3))
    converged = bool(
        n_tau is not None and n_tau >= 50.0
        and acc_mean is not None and 0.05 <= acc_mean <= 0.70
        and np.all(np.isfinite(samples))
        and width_pass and redchi_ok
    )
    note = ("continuum emcee chain; converged when N_tau >= 50, "
            "0.05 <= acceptance <= 0.70 and the median posterior width is "
            "0.5-2.0 times stderr_lsq/sqrt(redchi)")
    summary.update({
        "note": note,
        "n_samples": int(samples.shape[0]),
        "n_params": int(samples.shape[1]),
        "nwalkers": nwalkers,
        "steps": steps,
        "burn": burn,
        "thin": thin,
        "steps_after_burn": int(nsteps),
        "acceptance_fraction_mean": acc_mean,
        "acceptance_fraction_min": acc_min,
        "redchi": redchi_mcmc,
        "redchi_ok": redchi_ok,
        "tau_max": tau_max,
        "n_tau": n_tau,
        "width_ratio_median": width_median,
        "width_ratio_n": len(ratios),
        "width_check_pass": width_pass,
        "converged": converged,
        "convergence_note": (
            "N_tau=%.1f (target >= 50), acceptance=%.3f (target 0.05-0.70), "
            "median MCMC/LSQ width=%.2f (target 0.5-2.0)"
            % (n_tau if n_tau is not None else float("nan"),
               acc_mean if acc_mean is not None else float("nan"),
               width_median if width_median is not None else float("nan"))),
    })

    # Per-parameter quantiles, autocorrelation times and bound checks.
    q16, q50, q84 = np.quantile(samples, [0.16, 0.50, 0.84], axis=0)
    rows = []
    for i, name in enumerate(labels):
        p = None
        if hasattr(obj, "parf"):
            try:
                p = obj.parf[name]
            except (KeyError, TypeError):
                p = None
        lo = float(p.min) if p is not None and p.min is not None else np.nan
        hi = float(p.max) if p is not None and p.max is not None else np.nan
        med = float(q50[i])
        tol = 1e-3 * max(abs(med), 1.0)
        at_bound = bool(
            np.isfinite(lo) and np.isfinite(hi) and hi > lo and
            (abs(med - lo) < tol or abs(med - hi) < tol)
        )
        w = next((x for x in width_rows if x["parameter"] == name), {})
        rows.append({
            "parameter": name,
            "q16": float(q16[i]),
            "median": med,
            "q84": float(q84[i]),
            "err_1sigma": float((q84[i] - q16[i]) / 2.0),
            "mean": float(samples[:, i].mean()),
            "std": float(samples[:, i].std(ddof=1)),
            "tau": float(tau[i]) if tau is not None else np.nan,
            "n_tau": (float(nsteps / tau[i])
                      if tau is not None and tau[i] > 0 else np.nan),
            "bound_min": lo,
            "bound_max": hi,
            "at_bound": at_bound,
            "lsq_stderr": w.get("lsq_stderr"),
            "lsq_stderr_scaled": w.get("lsq_stderr_scaled"),
            "mcmc_over_lsq": w.get("mcmc_over_lsq"),
            "width_well_constrained": w.get("width_well_constrained"),
        })
    pd.DataFrame(rows).to_csv(out / "qgfit_mcmc_summary.csv", index=False)

    # Flattened chain (compressed, thinned to 20000 samples to keep the
    # repository output small).  The same thinning is used in qgfit.pkl.
    try:
        step = max(1, int(math.ceil(samples.shape[0] / 20000)))
        # Note: lmfit returns lnprob as a (steps, nwalkers) array while
        # flatchain is flattened step-major.  Saving a thinned lnprob next to
        # a differently thinned sample array would silently mis-align them, so
        # the chain file stores only the samples and their metadata.
        np.savez_compressed(
            out / "qgfit_mcmc_chain.npz",
            samples=samples[::step],
            labels=np.asarray(labels),
            acceptance_fraction=acc,
            tau=(tau if tau is not None else np.array([])),
            thin=step,
        )
        summary["chain_file"] = "qgfit_mcmc_chain.npz"
        summary["chain_thin"] = step
    except Exception as exc:  # noqa: BLE001
        log(f"[warn] continuum chain save failed: {exc}")
        summary["chain_error"] = str(exc)

    # Corner plot, thinned for plotting speed.
    try:
        import logging
        import corner
        root_level = logging.root.level
        logging.getLogger().setLevel(logging.ERROR)
        keep_names = ["pl_norm", "pl_slope1", "pl_slope2", "fe_uv_norm",
                      "fe_op_norm", "m_s", "a_v", "sigma", "age_young",
                      "age_old", "f_old", "host_shift"]
        keep = [i for i, n in enumerate(labels) if n in keep_names]
        if not keep:
            keep = list(range(len(labels)))
        step = max(1, int(math.ceil(samples.shape[0] / 20000)))
        plot_samples = samples[::step][:, keep]
        plot_labels = [labels[i] for i in keep]
        fig = plt.figure(figsize=(12, 12))
        corner.corner(plot_samples, labels=plot_labels, show_titles=True,
                      title_fmt=".4g", quantiles=[0.16, 0.5, 0.84],
                      plot_datapoints=True, plot_density=False,
                      fill_contours=True, color="tab:blue", fig=fig,
                      label_kwargs={"fontsize": 9})
        logging.getLogger().setLevel(root_level)
        fig.suptitle(
            "QGfit continuum MCMC: %d walkers x %d steps (burn %d), "
            "acceptance %.3f, N_tau %.1f - %s"
            % (nwalkers, steps, burn,
               acc_mean if acc_mean is not None else float("nan"),
               n_tau if n_tau is not None else float("nan"),
               "converged" if converged else "NOT converged"),
            y=0.995, fontsize=11)
        fig.savefig(out / "qgfit_uncertainty.png", dpi=150,
                    bbox_inches="tight")
        fig.savefig(out / "qgfit_uncertainty.pdf", bbox_inches="tight")
        plt.close(fig)
        summary["figure"] = "qgfit_uncertainty.png"
    except Exception as exc:  # noqa: BLE001
        log(f"[warn] corner plot failed: {exc}")
        summary["figure_error"] = str(exc)
    return summary


def line_mcmc_diagnostics(obj, data: dict, out: Path,
                          line_mcmc_out: list | None = None) -> dict:
    cfg = data["config"]
    enabled = bool(cfg.get("line_mcmc", False))
    comps = pd.DataFrame(data["line"]["comps"][0])
    # QGfit keeps only the last complex's emcee result on the LineFit object;
    # the adapter's minimiser wrapper records one result per complex instead.
    by_comp = {}
    for item in (line_mcmc_out or []):
        by_comp.setdefault(str(item.get("compname")), []).append(item.get("out"))
    rows = []
    for _, comp in comps.iterrows():
        outs = by_comp.get(str(comp["compname"]), [])
        mout = outs[-1] if outs else None
        n_vary = int(comp.get("nvarys", 0) or 0)
        has = bool(mout is not None and hasattr(mout, "flatchain"))
        row = {
            "complex": str(comp["compname"]),
            "n_gauss": int(comp["n_gauss"]),
            "n_params_fit": n_vary,
            "fit_method": str(comp["method"]),
            "ndata": int(comp["ndata"]),
            "redchi": float(comp["redchi"]),
            "bic": float(comp["bic"]),
            "mcmc": has,
            "nwalkers": int(cfg.get("line_nwalkers", 0) or 0),
            "steps": int(cfg.get("line_steps", 0) or 0),
            "burn": int(cfg.get("line_burn", 0) or 0),
            "thin": int(cfg.get("line_thin", 1) or 1),
        }
        if has:
            out_mcmc = mout
            flat = out_mcmc.flatchain
            samples = np.asarray(flat, dtype=float)
            acc = (np.asarray(out_mcmc.acceptance_fraction, dtype=float)
                   if hasattr(out_mcmc, "acceptance_fraction") else np.array([]))
            nwalkers = int(cfg.get("line_nwalkers", 0) or 0)
            tau, nsteps = _autocorr(samples, nwalkers)
            tau_max = float(np.max(tau)) if tau is not None and tau.size else None
            n_tau = float(nsteps / tau_max) if tau_max and tau_max > 0 else None
            acc_mean = float(np.mean(acc)) if acc.size else None
            acc_min = float(np.min(acc)) if acc.size else None
            # Compare the dominant line's chain width with the LSQ covariance
            # (scaled by sqrt(redchi)).  This is the line analogue of the
            # continuum width check and catches a chain that never expanded
            # out of lmfit's 1e-4 initial ball.
            width_ratio = None
            lres = pd.DataFrame(data["line"]["result"][0])
            lsub = lres[lres["compname"].astype(str) == str(comp["compname"])]
            if not lsub.empty:
                dom = lsub.loc[lsub["norm"].astype(float).idxmax()]
                nrm = float(dom["norm"])
                nerr = _to_float(dom.get("norm_stderr"))
                nchain = _finite_array(dom.get("norm_chain"))
                if (nerr is not None and nerr > 0 and nchain is not None
                        and nchain.size > 10 and float(comp["redchi"]) > 0):
                    scaled = nerr / math.sqrt(float(comp["redchi"]))
                    if scaled > 0:
                        width_ratio = float(np.std(nchain, ddof=1) / scaled)
            width_pass = bool(width_ratio is None or 0.3 <= width_ratio <= 3.0)
            redchi_mcmc = float(out_mcmc.redchi)
            redchi_ok = bool(np.isfinite(redchi_mcmc) and
                             redchi_mcmc < max(100.0 * float(comp["redchi"]),
                                               1e4))
            stable = bool(
                n_tau is not None and n_tau >= 20.0
                and acc_mean is not None and 0.02 <= acc_mean <= 0.80
                and np.all(np.isfinite(samples))
                and width_pass and redchi_ok
            )
            row.update({
                "n_samples": int(samples.shape[0]),
                "n_params": int(samples.shape[1]),
                "steps_after_burn": int(nsteps),
                "acceptance_mean": acc_mean,
                "acceptance_min": acc_min,
                "tau_max": tau_max,
                "n_tau": n_tau,
                "width_ratio_dominant": width_ratio,
                "width_check_pass": width_pass,
                "redchi_ok": redchi_ok,
                "stable": stable,
                "redchi_mcmc": redchi_mcmc,
            })
        else:
            row.update({"stable": False,
                        "reason": ("line MCMC disabled in the configuration"
                                   if not enabled else
                                   "no chain (QGfit n_line_vary <= 1)")})
        rows.append(row)
    summary = pd.DataFrame(rows)
    if not summary.empty:
        summary.to_csv(out / "qgfit_line_mcmc_summary.csv", index=False)
    mcmc_rows = [r for r in rows if r["mcmc"]]
    any_mcmc = len(mcmc_rows) > 0
    stable = bool(enabled and any_mcmc and all(r.get("stable") for r in mcmc_rows))
    if not enabled:
        reason = "line MCMC disabled in the configuration"
    elif not any_mcmc:
        reason = "no complex had more than one varying line; QGfit skipped the chains"
    elif not stable:
        bad = [r["complex"] for r in mcmc_rows if not r.get("stable")]
        reason = "unstable chains in: " + ", ".join(bad)
    else:
        reason = "all per-complex chains pass N_tau >= 20 and acceptance 0.02-0.80"
    return {
        "enabled": enabled,
        "any_mcmc": any_mcmc,
        "stable": stable,
        "reason": reason,
        "note": cfg.get("line_mcmc_note"),
        "complexes": rows,
        "n_complexes": len(rows),
        "n_complexes_with_mcmc": len(mcmc_rows),
    }


# ---------------------------------------------------------------------------
# Cross-tool comparison
# ---------------------------------------------------------------------------

def _add_component(store: dict, line: str, comp: str, flux, err=None,
                   fwhm=None, note: str = "") -> None:
    f = _to_float(flux)
    if f is None:
        return
    store.setdefault(line, {})[comp] = {
        "flux": f,
        "err": _to_float(err),
        "fwhm": _to_float(fwhm),
        "note": note,
    }


def _finish_reference(store: dict) -> dict:
    """Add total entries by summing components when the tool has no total row."""
    for line, comps in list(store.items()):
        if "total" in comps:
            continue
        parts = [(k, v) for k, v in comps.items() if k != "total"]
        if not parts:
            continue
        f = sum(v["flux"] for _, v in parts)
        errs = [v["err"] for _, v in parts if v["err"] is not None]
        e = math.sqrt(sum(x * x for x in errs)) if errs else None
        store[line]["total"] = {"flux": f, "err": e, "fwhm": None,
                                "note": "sum of components"}
    return store


def read_reference(reference: Path, tool: str) -> dict:
    """Return component and total line fluxes in observed-frame 1e-17 units."""
    store: dict[str, dict] = {}
    if tool == "pyqsofit_uv":
        path = reference / "pyqsofit_uv" / "pyqsofit_lines.csv"
        if not path.exists():
            return store
        for r in csv.DictReader(path.open()):
            name = r.get("line", "")
            if name in ("Hb_br", "Hb_na"):
                comp = "broad" if name.endswith("br") else "narrow"
                _add_component(store, "Hbeta", comp, r.get("area_1e17"),
                               fwhm=r.get("fwhm_kms"),
                               note="PyQSOFit component; no error column")
            elif name in ("OIII5007w", "OIII5007c"):
                comp = "broad" if name.endswith("w") else "narrow"
                _add_component(store, "OIII5007", comp, r.get("area_1e17"),
                               fwhm=r.get("fwhm_kms"),
                               note="PyQSOFit component; no error column")
    elif tool == "gandalf_line":
        path = reference / "gandalf_line" / "gandalf_lines.csv"
        if not path.exists():
            return store
        for r in csv.DictReader(path.open()):
            name = r.get("line", "")
            if name == "Hbeta":
                _add_component(store, "Hbeta", r.get("component", ""),
                               r.get("flux_1e17"), r.get("flux_err_1e17"),
                               _fwhm_from_sigma(r.get("sigma_kms")),
                               "GANDALF; FWHM from sigma")
            elif name == "[OIII]5007":
                _add_component(store, "OIII5007", r.get("component", ""),
                               r.get("flux_1e17"), r.get("flux_err_1e17"),
                               _fwhm_from_sigma(r.get("sigma_kms")),
                               "GANDALF; FWHM from sigma")
    elif tool == "s3fit_line":
        path = reference / "s3fit_line" / "s3fit_lines.csv"
        if not path.exists():
            return store
        for r in csv.DictReader(path.open()):
            name = r.get("line", "")
            comp_raw = r.get("component", "")
            comp = {"BLR": "broad", "NLR": "narrow",
                    "total": "total"}.get(comp_raw, comp_raw.lower())
            if name in ("H-beta", "Hbeta"):
                _add_component(store, "Hbeta", comp, r.get("flux_1e17"),
                               r.get("flux_err_1e17"), r.get("fwhm_kms"),
                               "S3Fit")
            elif name in ("[O III]:5008", "[OIII]5007"):
                _add_component(store, "OIII5007", comp, r.get("flux_1e17"),
                               r.get("flux_err_1e17"), r.get("fwhm_kms"),
                               "S3Fit")
    elif tool == "galspec_line":
        path = reference / "galspec_line" / "galspec_lines.csv"
        if not path.exists():
            return store
        for r in csv.DictReader(path.open()):
            name = r.get("line", "")
            comp_raw = r.get("component", "")
            comp = {"wing": "broad", "broad": "broad",
                    "narrow": "narrow", "total": "total"}.get(
                        comp_raw, comp_raw.lower())
            if name == "Hbeta":
                _add_component(store, "Hbeta", comp, r.get("flux_1e17"),
                               r.get("flux_err_1e17"), r.get("fwhm_kms"),
                               "GalSpec")
            elif name in ("OIII_5007", "OIII5007"):
                _add_component(store, "OIII5007", comp, r.get("flux_1e17"),
                               r.get("flux_err_1e17"), r.get("fwhm_kms"),
                               "GalSpec")
    elif tool == "pyqsofitspec_line":
        path = reference / "pyqsofitspec_line" / "pyqsofitspec_lines.csv"
        if not path.exists():
            return store
        for r in csv.DictReader(path.open()):
            name = r.get("line", "")
            if name in ("Hb_br", "Hb_na"):
                comp = "broad" if name.endswith("br") else "narrow"
                _add_component(store, "Hbeta", comp, r.get("flux_1e17"),
                               r.get("flux_err_1e17"), r.get("fwhm_kms"),
                               "PyQSOFitSpec; bootstrap errors")
            elif name in ("OIII5007c", "OIII5007w"):
                comp = "narrow" if name.endswith("c") else "broad"
                _add_component(store, "OIII5007", comp, r.get("flux_1e17"),
                               r.get("flux_err_1e17"), r.get("fwhm_kms"),
                               "PyQSOFitSpec; bootstrap errors")
    return _finish_reference(store)


def _qgfit_store(table: pd.DataFrame) -> dict:
    store: dict[str, dict] = {}
    for _, r in table.iterrows():
        line = str(r["line"])
        comp = str(r["component"])
        if comp == "mix":
            comp = "broad"
        store.setdefault(line, {})[comp] = {
            "flux": float(r["flux_1e17"]),
            "err": float(r["flux_err_1e17"]),
            "fwhm": float(r["fwhm_kms"]) if pd.notna(r["fwhm_kms"]) else None,
            "note": str(r.get("method", "")),
        }
    # A single-component line has no explicit total row.  Add one so the
    # cross-tool comparison always sees a total flux.
    for line, comps in store.items():
        if "total" not in comps:
            parts = [v for k, v in comps.items() if k != "total"]
            if len(parts) == 1:
                comps["total"] = dict(parts[0])
    return store


def write_comparison(table: pd.DataFrame, reference: Path | None,
                     tools: list[str], out: Path) -> dict:
    qg = _qgfit_store(table)
    rows = []
    comp_rows = []
    ratios = []
    qg_ratio = qg_ratio_err = None

    def total(store: dict, line: str):
        entry = store.get(line, {}).get("total")
        if entry is None:
            return None
        return entry["flux"], entry["err"]

    hb = total(qg, "Hbeta")
    o3 = total(qg, "OIII5007")
    if hb and o3 and o3[0] > 0:
        qg_ratio = hb[0] / o3[0]
        if hb[1] and o3[1]:
            qg_ratio_err = abs(qg_ratio) * math.sqrt(
                (hb[1] / hb[0]) ** 2 + (o3[1] / o3[0]) ** 2)
        ratios.append({"ratio": "Hbeta/OIII5007", "tool": "qgfit",
                       "value": qg_ratio, "err": qg_ratio_err})

    # QGfit component rows.
    for line in ("Hbeta", "OIII5007"):
        for comp, entry in qg.get(line, {}).items():
            comp_rows.append({
                "tool": "qgfit", "line": line, "component": comp,
                "flux_1e17": entry["flux"], "flux_err_1e17": entry["err"],
                "fwhm_kms": entry["fwhm"], "notes": entry["note"],
            })

    for tool in tools:
        ref = read_reference(reference, tool) if reference else {}
        if not ref:
            log(f"[warn] no reference table found for {tool}")
            continue
        for line in ("Hbeta", "OIII5007"):
            if line not in qg or line not in ref or "total" not in ref[line]:
                continue
            qv, qe = qg[line]["total"]["flux"], qg[line]["total"]["err"]
            rv = ref[line]["total"]["flux"]
            re = ref[line]["total"]["err"]
            rows.append({
                "line": line,
                "qgfit_1e17": qv,
                "qgfit_err_1e17": qe,
                "reference_tool": tool,
                "reference_1e17": rv,
                "reference_err_1e17": re,
                "ratio_qgfit_over_reference": (qv / rv) if rv else None,
                "notes": ("QGfit observed-frame flux = rest-frame integral "
                          "/(1+z)^2; reference is the sibling's published "
                          "total line flux"),
            })
            for comp, entry in ref[line].items():
                comp_rows.append({
                    "tool": tool, "line": line, "component": comp,
                    "flux_1e17": entry["flux"],
                    "flux_err_1e17": entry["err"],
                    "fwhm_kms": entry["fwhm"], "notes": entry["note"],
                })
        if "Hbeta" in ref and "OIII5007" in ref:
            h = ref["Hbeta"].get("total")
            o = ref["OIII5007"].get("total")
            if h and o and o["flux"]:
                val = h["flux"] / o["flux"]
                err = None
                if h["err"] and o["err"]:
                    err = abs(val) * math.sqrt(
                        (h["err"] / h["flux"]) ** 2 +
                        (o["err"] / o["flux"]) ** 2)
                ratios.append({"ratio": "Hbeta/OIII5007", "tool": tool,
                               "value": val, "err": err})

    comp_df = pd.DataFrame(comp_rows)
    if not comp_df.empty:
        comp_df = comp_df.sort_values(["line", "tool", "component"])
    comp_df.to_csv(out / "qgfit_component_comparison.csv", index=False)
    pd.DataFrame(rows).to_csv(out / "qgfit_comparison.csv", index=False)
    pd.DataFrame(ratios).to_csv(out / "qgfit_ratio_comparison.csv", index=False)
    return {
        "qgfit_hbeta_oiii5007": qg_ratio,
        "qgfit_hbeta_oiii5007_err": qg_ratio_err,
        "references": rows,
        "component_references": comp_rows,
        "ratios": ratios,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _mcmc_positions(params, nwalkers: int, config: dict):
    """Initial walker positions drawn from the least-squares covariance.

    lmfit's emcee initialises every walker in a 1e-4 relative ball around the
    least-squares solution.  For QGfit's highly correlated continuum and line
    parameters that ball is far too small: a 100-step chain never reaches the
    posterior width and reports errors that are an order of magnitude too
    small.  Drawing the initial state from the LSQ covariance (with a diagonal
    fallback and clipping to the parameter bounds) removes that failure mode
    without changing the likelihood.
    """
    free = [p for p in params.values() if p.vary and not p.expr]
    n = len(free)
    if n == 0 or nwalkers < 2:
        return None
    mean = np.array([float(p.value) for p in free])
    sig = []
    for p in free:
        s = p.stderr
        if s is None or not np.isfinite(s) or s <= 0:
            s = max(abs(float(p.value)) * 1e-3, 1e-6)
        sig.append(float(s))
    sig = np.array(sig)
    # Covariance-based initial states were tested and rejected: for QGfit's
    # strongly correlated host/Fe II parameters they put walkers in invalid
    # corners (redchi_mcmc ~1e9-1e10) from which the chain does not recover.
    # The production default is therefore lmfit's own small-ball start
    # (mcmc_init_scale=0) with a long chain that has time to expand.
    scale = float(config.get("mcmc_init_scale", 0.0) or 0.0)
    if scale <= 0:
        return None
    sig *= scale
    lo = np.array([float(p.min) if p.min is not None else -np.inf for p in free])
    hi = np.array([float(p.max) if p.max is not None else np.inf for p in free])
    span = hi - lo
    # Do not start walkers across a range much wider than the prior: the LSQ
    # covariance of an unconstrained host parameter can exceed its bounds by
    # orders of magnitude.
    for i in range(n):
        if np.isfinite(span[i]) and span[i] > 0:
            sig[i] = min(sig[i], 0.25 * span[i])
    # A diagonal initial scatter is the safe default.  Sampling the full LSQ
    # correlation matrix can place walkers in pathological corners of a
    # highly correlated line model (zero norm / FWHM at a bound), from which
    # the chain does not recover.  Correlations can be enabled explicitly.
    corr = np.eye(n)
    if config.get("mcmc_use_correlations", False):
        for i, pi in enumerate(free):
            for j in range(i + 1, n):
                c = 0.0
                if getattr(pi, "correl", None):
                    c = float(pi.correl.get(free[j].name, 0.0) or 0.0)
                if not np.isfinite(c):
                    c = 0.0
                c = float(np.clip(c, -0.999, 0.999))
                corr[i, j] = corr[j, i] = c
    cov = np.outer(sig, sig) * corr
    cov = 0.5 * (cov + cov.T)
    jitter = 1e-10 * max(1.0, float(np.max(sig)) ** 2)
    cov = cov + np.eye(n) * jitter
    rng = np.random.default_rng(int(config.get("mcmc_seed", 42)))
    try:
        chol = np.linalg.cholesky(cov)
        pos = mean + rng.standard_normal((nwalkers, n)) @ chol.T
    except np.linalg.LinAlgError:
        pos = mean + rng.standard_normal((nwalkers, n)) * sig
    margin = np.where(np.isfinite(span), 1e-6 * span, 0.0)
    pos = np.clip(pos, lo + margin, hi - margin)
    return pos


def _timing_wrappers(obj, timings: dict, line_mcmc_out: list | None = None):
    """Wrap the QGfit minimisers so run.json can report a runtime breakdown.

    The line wrapper also records each per-complex emcee result.  QGfit's
    ``LineFit.out_mcmc`` attribute is overwritten for every complex, so this
    is the only place where the individual chains are still available.
    """
    orig_conti_min = obj._minimize

    def conti_min(params, method="leastsq", **kwargs):
        t0 = time.time()
        if method == "emcee" and "pos" not in kwargs:
            pos = _mcmc_positions(params, int(kwargs.get("nwalkers", 0)),
                                  getattr(obj, "config", {}))
            if pos is not None:
                kwargs["pos"] = pos
        out = orig_conti_min(params, method=method, **kwargs)
        key = "continuum_mcmc_sec" if method == "emcee" else "continuum_fit_sec"
        timings[key] = timings.get(key, 0.0) + (time.time() - t0)
        return out

    obj._minimize = conti_min
    orig_line_min = LineFit._minimize

    def line_min(self, params, data_line, comp_name, method="leastsq", **kwargs):
        t0 = time.time()
        if method == "emcee" and "pos" not in kwargs:
            pos = _mcmc_positions(params, int(kwargs.get("nwalkers", 0)),
                                  getattr(self, "config", {}))
            if pos is not None:
                kwargs["pos"] = pos
        out = orig_line_min(self, params, data_line, comp_name,
                            method=method, **kwargs)
        key = "line_mcmc_sec" if method == "emcee" else "line_fit_sec"
        timings[key] = timings.get(key, 0.0) + (time.time() - t0)
        if method == "emcee" and line_mcmc_out is not None:
            line_mcmc_out.append({"compname": str(comp_name), "out": out})
        return out

    LineFit._minimize = line_min
    return orig_conti_min, orig_line_min


def _restore_wrappers(obj, orig_conti_min, orig_line_min):
    obj._minimize = orig_conti_min
    LineFit._minimize = orig_line_min


def _thin_data_for_pickle(data: dict, max_samples: int = 20000) -> dict:
    """Drop per-line chains and thin the continuum chain before pickling."""
    m = data.get("conti", {}).get("mcmc")
    if isinstance(m, dict):
        flat = m.get("flatchain")
        if flat is not None:
            n = len(flat)
            step = max(1, int(math.ceil(n / max_samples)))
            if isinstance(flat, pd.DataFrame):
                m["flatchain"] = flat.iloc[::step].reset_index(drop=True)
            else:
                m["flatchain"] = np.asarray(flat)[::step]
            # Drop lnprob: it has a (steps, nwalkers) shape while flatchain
            # is flattened step-major, so thinning them independently would
            # mis-align the arrays.  The samples and quantiles are the
            # products used downstream.
            m.pop("lnprob", None)
    for i, df in enumerate(data.get("line", {}).get("result", []) or []):
        cols = [c for c in df.columns if c.endswith("_chain")]
        if cols:
            data["line"]["result"][i] = df.drop(columns=cols)
    return data


def _boundary_hits(obj, pars: dict) -> list[dict]:
    hits = []
    for name, value in pars.items():
        p = None
        if hasattr(obj, "parf"):
            try:
                p = obj.parf[name]
            except (KeyError, TypeError):
                p = None
        if p is None or not getattr(p, "vary", False):
            continue
        lo, hi = p.min, p.max
        if lo is None or hi is None or not np.isfinite(lo) or not np.isfinite(hi):
            continue
        if hi <= lo:
            continue
        tol = 1e-3 * max(abs(float(value)), 1.0)
        at_lo = abs(value - lo) < tol
        at_hi = abs(value - hi) < tol
        if at_lo or at_hi:
            hits.append({"parameter": name, "value": float(value),
                         "min": float(lo), "max": float(hi),
                         "side": "min" if at_lo else "max"})
    return hits


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
    qcfg.setdefault("save_line_chains", True)
    qcfg.setdefault("write", True)
    qcfg.setdefault("prop", True)
    qcfg.setdefault("plot_conti_mcmc_corner", True)
    qcfg.setdefault("comp_plot", ["Ha", "Hb", "Hd", "He", "Hr", "MgII",
                                  "CIII", "CIV", "Lya"])

    # Resolve a line template shipped next to the config file.  In the
    # pipeline the config directory is mounted at /app/config.
    line_file = qcfg.get("line_file")
    line_template_path = None
    if line_file:
        lf = Path(str(line_file))
        if not lf.is_absolute():
            cand = Path(args.config).parent / lf
            if cand.exists():
                qcfg["line_file"] = str(cand)
                lf = cand
        if lf.exists():
            line_template_path = lf
        else:
            raise FileNotFoundError(f"line_file not found: {line_file}")

    # Sanity checks on MCMC sizes (emcee needs > 2*n_params walkers).
    if qcfg.get("conti_mcmc", False):
        if int(qcfg.get("conti_steps", 0)) <= int(qcfg.get("conti_burn", 0)):
            raise ValueError("conti_steps must exceed conti_burn")
        if int(qcfg.get("conti_nwalkers", 0)) < 32:
            raise ValueError("conti_nwalkers must be >= 32 for 16 continuum parameters")
    if qcfg.get("line_mcmc", False):
        if int(qcfg.get("line_steps", 0)) <= int(qcfg.get("line_burn", 0)):
            raise ValueError("line_steps must exceed line_burn")
        if int(qcfg.get("line_nwalkers", 0)) < 40:
            raise ValueError("line_nwalkers must be >= 40")

    log(f"[qgfit] input={spectrum_path}")
    log(f"[qgfit] z={z:.8f} ra={ra} dec={dec}")
    log(f"[qgfit] good pixels={spec['n_good']}/{spec['n_total']} "
        f"rest range={spec['wave'].min()/(1+z):.1f}-"
        f"{spec['wave'].max()/(1+z):.1f} A")
    conti_msg = (f"{qcfg.get('conti_nwalkers')}x{qcfg.get('conti_steps')}, "
                 f"burn {qcfg.get('conti_burn')}"
                 if qcfg.get("conti_mcmc", False) else "disabled")
    line_msg = (f"{qcfg.get('line_nwalkers')}x{qcfg.get('line_steps')}, "
                f"burn {qcfg.get('line_burn')}"
                if qcfg.get("line_mcmc", False) else "disabled")
    log(f"[qgfit] conti_mcmc={qcfg.get('conti_mcmc', False)} ({conti_msg}), "
        f"line_mcmc={qcfg.get('line_mcmc', False)} ({line_msg})")

    sfd_maps = list(Path(os.environ["SFD_PATH"]).glob("SFD_dust_*.fits")) \
        if Path(os.environ["SFD_PATH"]).is_dir() else []
    if qcfg.get("do_deredden", True) and not sfd_maps:
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
    timings: dict[str, float] = {}
    line_mcmc_out: list = []
    orig_conti_min, orig_line_min = _timing_wrappers(obj, timings,
                                                     line_mcmc_out)
    try:
        data = obj.run_fit()
    finally:
        _restore_wrappers(obj, orig_conti_min, orig_line_min)
    timings["fit_total_sec"] = time.time() - t0
    log(f"[qgfit] fit finished in {timings['fit_total_sec']:.1f}s")

    line_diag = line_mcmc_diagnostics(obj, data, out, line_mcmc_out)
    table = line_table(data, bool(line_diag.get("stable", False)))
    table.to_csv(out / "qgfit_lines.csv", index=False)
    wave, flux, err, conti, line_model, total = build_model(data, out)
    plot_fit(wave, flux, err, conti, line_model, total, data, out)
    plot_zoom(wave, flux, err, conti, line_model, total, data, out)
    plot_residual(wave, flux, err, total, out)
    mcmc_summary = continuum_mcmc_diagnostics(obj, data, out)
    plot_line_errors(table, out, line_diag)
    t_fig = time.time()

    # Native QGfit PDF/corner.  Thin the in-memory chains first so the native
    # corner plot does not have to render hundreds of thousands of samples.
    _thin_data_for_pickle(data, max_samples=20000)
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
    timings["figures_sec"] = time.time() - t_fig

    comparison = write_comparison(
        table, Path(args.reference) if args.reference else None,
        list(cfg.get("reference_tools", [])), out)

    # Persist the trimmed native result (the full continuum chain is in
    # qgfit_mcmc_chain.npz).
    try:
        with (out / "qgfit.pkl").open("wb") as fh:
            pickle.dump(data, fh, protocol=4)
    except Exception as exc:  # noqa: BLE001
        log(f"[warn] pkl save failed: {exc}")

    def first_line(line: str, component: str = "total"):
        sub = table[(table["line"] == line) & (table["component"] == component)]
        if sub.empty:
            sub = table[table["line"] == line]
        return sub.iloc[0] if not sub.empty else None

    hb = first_line("Hbeta")
    o3 = first_line("OIII5007")
    hb_b = first_line("Hbeta", "broad")
    hb_n = first_line("Hbeta", "narrow")
    o3_components = table[table["line"] == "OIII5007"] if o3 is not None else table.iloc[0:0]

    import scipy as _scipy
    import astropy as _astropy
    import lmfit as _lmfit
    import kapteyn as _kapteyn
    versions = {
        "python": sys.version.split()[0],
        "qgfit": QGFIT_VERSION,
        "numpy": np.__version__,
        "scipy": _scipy.__version__,
        "pandas": pd.__version__,
        "astropy": _astropy.__version__,
        "lmfit": _lmfit.__version__,
        "emcee": emcee.__version__ if emcee is not None else None,
        "kapteyn": _kapteyn.__version__,
        "matplotlib": matplotlib.__version__,
    }

    # Effective configuration: all scalar QGfit controls plus the template
    # identity.  DataFrames and lmfit helper attributes are not serialised.
    skip = {"line_list", "line_input", "out_attr", "out_types",
            "out_attr_mcmc_conti", "out_attr_mcmc_line",
            "out_types_mcmc_line", "window", "init_values", "var_names"}
    effective = {k: jsonable(v) for k, v in data.get("config", {}).items()
                 if k not in skip}
    if line_template_path is not None:
        effective["line_file"] = str(line_template_path)
        effective["line_file_sha256"] = _sha256(line_template_path)
        try:
            effective["line_template_rows"] = int(
                len(pd.read_csv(line_template_path)))
        except Exception:
            pass
    with (out / "qgfit_config.effective.json").open("w") as fh:
        json.dump(jsonable(effective), fh, indent=2)

    conti_pars = data["conti"]["pars_set"][0]
    line_summary = {
        "n_rows": int(len(table)),
        "n_detected": int(table["detected"].sum()),
        "Hbeta_total_1e17": float(hb["flux_1e17"]) if hb is not None else None,
        "Hbeta_err_1e17": float(hb["flux_err_1e17"]) if hb is not None else None,
        "Hbeta_broad_1e17": float(hb_b["flux_1e17"]) if hb_b is not None else None,
        "Hbeta_narrow_1e17": float(hb_n["flux_1e17"]) if hb_n is not None else None,
        "Hbeta_total_method": str(hb["method"]) if hb is not None else None,
        "OIII5007_total_1e17": float(o3["flux_1e17"]) if o3 is not None else None,
        "OIII5007_err_1e17": float(o3["flux_err_1e17"]) if o3 is not None else None,
        "OIII5007_total_method": str(o3["method"]) if o3 is not None else None,
        "OIII5007_components": o3_components[
            ["qgfit_line", "component", "flux_1e17", "flux_err_1e17",
             "fwhm_kms", "method"]].to_dict(orient="records")
        if not o3_components.empty else [],
        "Hbeta_OIII5007": comparison.get("qgfit_hbeta_oiii5007"),
        "Hbeta_OIII5007_err": comparison.get("qgfit_hbeta_oiii5007_err"),
    }
    line_summary["Hbeta_OIII5007_note"] = (
        "native QGfit template: single narrow [O III] component capped at "
        "FWHM<=1200 km/s; expanded template adds a broad [O III] wing"
    )

    method = "qgfit_lmfit_leastsq"
    if qcfg.get("conti_mcmc", False):
        method += "+emcee_continuum"
    if line_diag.get("stable"):
        method += "+emcee_lines"
    elif line_diag.get("enabled"):
        method += "+lsq_lines(line_mcmc_rejected)"
    else:
        method += "+lsq_lines"

    products = []
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != "run.json":
            products.append({"name": p.name, "bytes": int(p.stat().st_size)})

    run = {
        "tool": "qgfit",
        "method": method,
        "native_code": ("QGfit 1.0.0 (github.com/qian-yang/QGfit, commit "
                        "3aed692); vendored copy patched for the LSQ-only "
                        "UnboundLocalError (fitter.run_fit_conti, "
                        "line.run_fit_line_one) and the missing-MCMC-block "
                        "KeyError in prop.cal_prop"),
        "versions": versions,
        "input": {
            "file": str(spectrum_path),
            "z": z,
            "ra": ra,
            "dec": dec,
            "n_pixels_total": spec["n_total"],
            "n_pixels_used": spec["n_good"],
            "n_pixels_masked": int(spec["n_total"] - spec["n_good"]),
            "wave_obs_range_A": [float(spec["wave"].min()), float(spec["wave"].max())],
            "wave_rest_range_A": [float(spec["wave"].min() / (1 + z)),
                                   float(spec["wave"].max() / (1 + z))],
            "flux_unit": "1e-17 erg s-1 cm-2 A-1 (observed frame)",
            "bunit_header": spec["bunit"],
            "mask_and_mask": bool(cfg.get("mask_and_mask", True)),
        },
        "config_file": str(Path(args.config)),
        "config_effective": effective,
        "units": {
            "input_flux_density": "1e-17 erg s-1 cm-2 A-1 (observed)",
            "qgfit_rest_flux_density": "observed f_lambda * (1+z)^3",
            "qgfit_line_flux": "integral over rest-frame wavelength, 1e-17 erg s-1 cm-2",
            "observed_line_flux": "rest-frame integral / (1+z)^2",
            "qgfit_model_csv": ("rest-frame f_lambda (observed * (1+z)^3); "
                                "do not compare directly with observed-frame "
                                "continuum columns from sibling tools"),
        },
        "continuum": {
            "redchi": float(data["conti"]["redchi"]),
            "chisqr": float(data["conti"]["chisqr"]),
            "ndata": int(data["conti"]["ndata"]),
            "nvarys": int(data["conti"]["nvarys"]),
            "method": data["conti"]["method"],
            "kmpfit_attempted": bool(
                qcfg.get("check_kmpfit") and
                float(data["conti"]["redchi"]) >
                float(qcfg.get("conti_redchi_limit") or 0)),
            "mcmc": mcmc_summary,
            "mcmc_seed": int(qcfg.get("mcmc_seed", 42)),
            "mcmc_init_scale": float(qcfg.get("mcmc_init_scale", 0.0)),
            "pars": jsonable(conti_pars),
            "stderr": jsonable(data["conti"]["stderr_set"][0]),
            "boundary_hits": _boundary_hits(obj, conti_pars),
        },
        "line_fit": {
            "controls": {
                "line_mcmc": bool(qcfg.get("line_mcmc", False)),
                "line_nwalkers": int(qcfg.get("line_nwalkers", 0) or 0),
                "line_steps": int(qcfg.get("line_steps", 0) or 0),
                "line_burn": int(qcfg.get("line_burn", 0) or 0),
                "line_thin": int(qcfg.get("line_thin", 1) or 1),
                "mcmc_init_scale": float(qcfg.get("mcmc_init_scale", 0.0)),
                "mask_lowSN": bool(effective.get("mask_lowSN")),
                "test_add_broad": bool(effective.get("test_add_broad")),
                "tie_width": bool(effective.get("tie_width")),
                "tie_shift": bool(effective.get("tie_shift")),
                "tie_flux": bool(effective.get("tie_flux")),
                "line_file": effective.get("line_file"),
            },
            "complexes": data["line"]["comps"][0][
                ["compname", "n_gauss", "method", "ndata", "nvarys",
                 "chisqr", "redchi", "bic"]].to_dict(orient="records"),
            "line_mcmc": line_diag,
            **line_summary,
        },
        "statistical_mode": {
            "continuum": ("emcee MCMC via lmfit (%d walkers x %d steps, "
                          "burn %d)" % (
                              int(qcfg.get("conti_nwalkers", 0) or 0),
                              int(qcfg.get("conti_steps", 0) or 0),
                              int(qcfg.get("conti_burn", 0) or 0))
                          if qcfg.get("conti_mcmc", False) else
                          "least-squares only"),
            "line": ("per-complex emcee chains" if line_diag.get("stable")
                     else "least-squares covariance from QGfit norm_stderr"),
            "continuum_converged": bool(mcmc_summary.get("converged", False)),
            "line_converged": bool(line_diag.get("stable", False)),
            "converged": bool(mcmc_summary.get("converged", False) and
                              (not line_diag.get("enabled") or
                               line_diag.get("stable", False))),
            "note": ("Line MCMC is run independently per emission-line "
                     "complex and does not propagate continuum "
                     "uncertainty. " + str(line_diag.get("reason", "")) +
                     ((" " + str(line_diag.get("note")))
                      if line_diag.get("note") else "")),
        },
        "comparison": comparison,
        "runtime": {
            "total_sec": round(time.time() - t0, 1),
            "wall_clock_sec": round(time.time() - t0, 1),
            **{k: round(v, 1) for k, v in timings.items()},
        },
        "scope": {
            "galactic_dereddening": bool(qcfg.get("do_deredden", False)),
            "sfd_maps_present": bool(sfd_maps),
            "host_galaxy": bool(qcfg.get("conti_host", True)),
            "fe_uv": bool(qcfg.get("conti_fe_uv", True)),
            "fe_optical": bool(qcfg.get("conti_fe_op", True)),
            "balmer_continuum": bool(qcfg.get("conti_balmer", False)),
            "line_mcmc": bool(qcfg.get("line_mcmc", False)),
            "line_template": str(line_template_path) if line_template_path else "QGfit default",
            "line_template_sha256": effective.get("line_file_sha256"),
            "native_plot": native_note,
            "note": ("QGfit is run on the observed SDSS spectrum without "
                     "Galactic dereddening; the sibling tools also use the "
                     "observed SDSS spectrum with EBV=0.  The H-beta total is "
                     "the sum of the QGfit broad+narrow components; QGfit's "
                     "BIC test can remove a narrow component when it is not "
                     "required.  The native QGfit narrow-line profile is hard "
                     "capped at FWHM=1200 km/s, so a broad [O III] wing can "
                     "only be represented with an expanded line template."),
        },
        "products": products,
        "line_measurements": table.to_dict(orient="records"),
    }
    with (out / "run.json").open("w") as fh:
        json.dump(jsonable(run), fh, indent=2, sort_keys=False)
    log(f"[qgfit] done in {time.time() - t0:.1f}s -> {out}")
    return 0


def plot_line_errors(table: pd.DataFrame, out: Path, line_diag: dict) -> None:
    wanted = [("Hbeta", "broad", r"H$\beta$ broad"),
              ("Hbeta", "total", r"H$\beta$ total"),
              ("OIII5007", "total", r"[O III] 5007"),
              ("OIII4959", "total", r"[O III] 4959")]
    vals, errs, labels, methods = [], [], [], []
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
        methods.append(str(r.get("method", "")))
    if not vals:
        return
    use_mcmc = any(m == "qgfit_line_mcmc" for m in methods)
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    x = np.arange(len(vals))
    ax.bar(x, vals, yerr=errs, capsize=4, color="tab:blue", alpha=0.75)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel(r"Line flux ($10^{-17}$ erg s$^{-1}$ cm$^{-2}$)")
    ax.set_title("QGfit line fluxes and errors (%s)\ncontinuum corner: "
                 "qgfit_uncertainty.png" %
                 ("per-complex MCMC" if use_mcmc else
                  "least-squares covariance"))
    for xi, (v, e) in enumerate(zip(vals, errs)):
        ax.text(xi, v + max(e, 0.01 * max(vals)), f"{v:.1f} ± {e:.1f}",
                ha="center", va="bottom", fontsize=8)
    ax.grid(axis="y", alpha=0.2, ls=":")
    fig.tight_layout()
    fig.savefig(out / "qgfit_line_errors.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


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
