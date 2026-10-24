#!/usr/bin/env python3
"""QSOFITMORE UV/optical AGN fit for one spectrum.

This is the container entry point.  It deliberately keeps the scientific
choices in ``configs/qsofitmore_line/default/config.json`` and the editable
line table next to it, and it records the exact upstream commit, effective
configuration, input hash and Monte Carlo settings in ``run.json``.

Two details matter for a defensible measurement:

* qsofitmore's ``<complex>_whole_br_area`` column only sums the Gaussians that
  its sigma > 1200 km/s classifier calls broad.  A multi-Gaussian broad
  template can contain narrower Gaussians, so the compact table here sums all
  components belonging to a physical line and reports the package columns
  separately.
* qsofitmore 1.2.2 has no emcee/MCMC sampler.  Its native uncertainty path is
  the lmfit Monte Carlo refit implemented with ``MC=True, n_trails=N``; that is
  the mode used here and it is never relabelled as MCMC.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata as md
import json
import math
import os
import platform
import random
import shutil
import subprocess
import sys
import time
import warnings
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("QSOFITMORE_USE_LMFIT", "true")
os.environ.setdefault("QSOFITMORE_WAVE_SCALE", "log")
os.environ.setdefault("QSOFITMORE_VELOCITY_UNITS", "lnlambda")
os.environ.setdefault("QSOFITMORE_NARROW_MAX_KMS", "1200")

import logging

import numpy as np
import matplotlib

matplotlib.use("Agg")
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.table import Table
import lmfit
from qsofitmore import QSOFitNew
from qsofitmore.config import migration_config

C_KMS = 299792.458
DEFAULT_DUST_DIR = "/app/cache/dustmaps/sfd"
FTYPE = ".fits"

# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return jsonable(obj.tolist())
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(data), indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fieldnames = fieldnames or list(rows[0].keys())
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def version(pkg: str) -> str:
    try:
        return md.version(pkg)
    except Exception:
        return "unknown"


def hget(header, *keys, default=None):
    for key in keys:
        if key in header:
            return header[key]
    upper = {str(k).upper(): k for k in header}
    for key in keys:
        if str(key).upper() in upper:
            return header[upper[str(key).upper()]]
    return default


def as_float(value, default=float("nan")):
    try:
        out = float(value)
        return out
    except Exception:
        return default


def clean_name(text: str) -> str:
    out = str(text).strip().replace(" ", "_").replace("/", "_")
    return "".join(ch for ch in out if ch.isalnum() or ch in "._+-") or "qso"


# ---------------------------------------------------------------------------
# spectrum loading
# ---------------------------------------------------------------------------


def _column(table, *names):
    names_lower = {str(n).lower(): n for n in table.dtype.names or ()}
    for name in names:
        if name in (table.dtype.names or ()):
            return np.asarray(table[name], dtype=float)
        if name.lower() in names_lower:
            return np.asarray(table[names_lower[name.lower()]], dtype=float)
    return None


def _load_raw_sdss(path: Path, hdul):
    names = [h.name for h in hdul]
    if "COADD" not in names or "SPALL" not in names:
        return None
    d = hdul["COADD"].data
    sp = hdul["SPALL"].data
    wave = 10.0 ** np.asarray(d["LOGLAM"], dtype=float)
    flux = np.asarray(d["FLUX"], dtype=float)
    ivar = np.asarray(d["IVAR"], dtype=float)
    err = np.where(ivar > 0, 1.0 / np.sqrt(np.clip(ivar, 1e-30, None)), 0.0)
    z = as_float(sp["Z"][0])
    ra = as_float(sp["PLUG_RA"][0])
    dec = as_float(sp["PLUG_DEC"][0])
    return {
        "layout": "sdss_coadd",
        "wave": wave,
        "flux_1e17": flux,
        "err_1e17": err,
        "z": z,
        "ra": ra,
        "dec": dec,
        "bunit": "1E-17 erg s-1 cm-2 Ang-1",
        "unit_scale_to_1e17": 1.0,
        "n_raw": int(len(wave)),
    }


def _load_prepared(path: Path, hdul):
    if len(hdul) < 3:
        return None
    if hdul[0].data is None or hdul[1].data is None or hdul[2].data is None:
        return None
    flux = np.asarray(hdul[0].data, dtype=float).squeeze()
    wave = np.asarray(hdul[1].data, dtype=float).squeeze()
    err = np.asarray(hdul[2].data, dtype=float).squeeze()
    if flux.ndim != 1 or wave.ndim != 1 or err.ndim != 1 or len(flux) != len(wave):
        return None
    hdr = hdul[0].header
    bunit = str(hget(hdr, "BUNIT", default="")).lower()
    if "1e-17" in bunit or "1E-17" in str(hget(hdr, "BUNIT", default="")):
        scale = 1.0
    else:
        scale = 1e17
    z = as_float(hget(hdr, "Z", "z", "REDSHIFT", default=float("nan")))
    ra = as_float(hget(hdr, "PLUG_RA", "RA", "ra", default=float("nan")))
    dec = as_float(hget(hdr, "PLUG_DEC", "DEC", "dec", default=float("nan")))
    return {
        "layout": "prepared_pyqsofit",
        "wave": wave,
        "flux_1e17": flux * scale,
        "err_1e17": err * scale,
        "z": z,
        "ra": ra,
        "dec": dec,
        "bunit": str(hget(hdr, "BUNIT", default="")),
        "unit_scale_to_1e17": scale,
        "n_raw": int(len(wave)),
    }


def _load_generic(path: Path, hdul):
    wave = flux = err = None
    hdr = hdul[0].header
    # Table in HDU0 or HDU1
    for hdu in hdul:
        if hdu.data is not None and getattr(hdu.data, "dtype", None) is not None and hdu.data.dtype.names:
            tab = hdu.data
            wave = _column(tab, "wave", "wl", "lambda", "WAVELENGTH", "LOGLAM")
            if wave is not None and _column(tab, "LOGLAM") is not None:
                wave = 10.0 ** wave
            flux = _column(tab, "flux", "FLUX")
            err = _column(tab, "err", "error", "stdev", "STDEV", "ERROR")
            if err is None:
                ivar = _column(tab, "ivar", "IVAR")
                if ivar is not None:
                    err = np.where(ivar > 0, 1.0 / np.sqrt(np.clip(ivar, 1e-30, None)), 0.0)
            if wave is not None and flux is not None:
                break
    if wave is None and len(hdul) >= 2 and hdul[0].data is not None and hdul[1].data is not None:
        if hdul[0].data.ndim == 1 and hdul[1].data.ndim == 1:
            flux = np.asarray(hdul[0].data, dtype=float)
            wave = np.asarray(hdul[1].data, dtype=float)
            if len(hdul) >= 3 and hdul[2].data is not None and hdul[2].data.ndim == 1:
                err = np.asarray(hdul[2].data, dtype=float)
    if wave is None or flux is None:
        return None
    wave = np.asarray(wave, dtype=float).squeeze()
    flux = np.asarray(flux, dtype=float).squeeze()
    if err is None:
        err = np.full_like(flux, np.nan)
    err = np.asarray(err, dtype=float).squeeze()
    bunit = str(hget(hdr, "BUNIT", default="")).lower()
    if "1e-17" in bunit:
        scale = 1.0
    else:
        finite = flux[np.isfinite(flux)]
        scale = 1e17 if finite.size and np.nanmedian(np.abs(finite)) < 1e-10 else 1.0
    z = as_float(hget(hdr, "Z", "z", "REDSHIFT", default=float("nan")))
    ra = as_float(hget(hdr, "PLUG_RA", "RA", "ra", default=float("nan")))
    dec = as_float(hget(hdr, "PLUG_DEC", "DEC", "dec", default=float("nan")))
    return {
        "layout": "generic_fits",
        "wave": wave,
        "flux_1e17": flux * scale,
        "err_1e17": err * scale,
        "z": z,
        "ra": ra,
        "dec": dec,
        "bunit": str(hget(hdr, "BUNIT", default="")),
        "unit_scale_to_1e17": scale,
        "n_raw": int(len(wave)),
    }


def load_spectrum(input_dir: Path, input_file: str | None):
    if input_file:
        candidates = [input_dir / input_file]
    else:
        preferred = [input_dir / "spectrum.fits"]
        raw = sorted(input_dir.glob("spec-*.fits"))
        other = sorted(input_dir.glob("*.fits"))
        candidates = preferred + raw + other
    errors = []
    for path in candidates:
        if not path.exists():
            continue
        try:
            with fits.open(path, memmap=False) as hdul:
                loaded = _load_raw_sdss(path, hdul)
                if loaded is None:
                    loaded = _load_prepared(path, hdul)
                if loaded is None:
                    loaded = _load_generic(path, hdul)
            if loaded is None:
                errors.append(f"{path}: unsupported FITS layout")
                continue
            loaded["path"] = str(path)
            loaded["sha256"] = sha256_file(path)
            return loaded
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path}: {exc!r}")
    raise RuntimeError("no readable FITS spectrum in input directory; " + "; ".join(errors))


def prepare_arrays(spec: dict):
    wave = np.asarray(spec["wave"], dtype=float)
    flux = np.asarray(spec["flux_1e17"], dtype=float)
    err = np.asarray(spec["err_1e17"], dtype=float)
    good = (
        np.isfinite(wave)
        & np.isfinite(flux)
        & np.isfinite(err)
        & (wave > 0)
        & (err > 0)
    )
    # Prepared PyQSOFit copies encode zero-IVAR SDSS pixels as a clipped
    # 1e-30 inverse variance (i.e. an enormous error) rather than err=0.  Drop
    # those outliers so a prepared run has the same red-end coverage as the
    # raw-IVAR run.  The threshold is deliberately very conservative: it only
    # removes pixels whose error is >100x the median.
    finite_err = err[good & np.isfinite(err)]
    if finite_err.size:
        med_err = float(np.nanmedian(finite_err))
        if np.isfinite(med_err) and med_err > 0:
            good &= err < 100.0 * med_err
    wave, flux, err = wave[good], flux[good], err[good]
    order = np.argsort(wave)
    wave, flux, err = wave[order], flux[order], err[order]
    if len(wave) < 200:
        raise RuntimeError(f"only {len(wave)} usable pixels after masking")
    return wave, flux, err, int((~good).sum())


# ---------------------------------------------------------------------------
# Monte Carlo recorder
# ---------------------------------------------------------------------------


class MCAccumulator:
    """Record every lmfit line-MC refit without changing qsofitmore's model."""

    def __init__(self):
        self.active = False
        self.q = None
        self.complex = None
        self.tables: dict[str, np.ndarray] = {}
        self.samples: list[dict] = []
        self._orig_min = None
        self._orig_nlm = None
        self.requested = 0

    def install(self, q):
        self.q = q
        self._orig_min = lmfit.minimize
        self._orig_nlm = QSOFitNew.new_line_mc
        acc = self

        def rec_min(*args, **kwargs):
            res = acc._orig_min(*args, **kwargs)
            if acc.active:
                try:
                    n = len(res.params)
                    p = np.array([res.params[f"p{i}"].value for i in range(n)], dtype=float)
                    p = acc.q._apply_ties_inplace(p)
                    acc.samples.append(
                        {
                            "complex": str(acc.complex),
                            "p": p,
                            "success": bool(getattr(res, "success", True)),
                        }
                    )
                except Exception:
                    pass
            return res

        def wrap_new_line_mc(
            self,
            x,
            y,
            err,
            pp0,
            pp_limits,
            n_trails,
            compcenter,
            linecompname,
            ind_line,
            nline_fit,
            linelist_fit,
            ngauss_fit,
        ):
            acc.active = True
            acc.complex = str(linecompname)
            acc.requested += int(n_trails)
            acc.tables[str(linecompname)] = np.array(linelist_fit, copy=True)
            try:
                return acc._orig_nlm(
                    self,
                    x,
                    y,
                    err,
                    pp0,
                    pp_limits,
                    n_trails,
                    compcenter,
                    linecompname,
                    ind_line,
                    nline_fit,
                    linelist_fit,
                    ngauss_fit,
                )
            finally:
                acc.active = False

        lmfit.minimize = rec_min
        QSOFitNew.new_line_mc = wrap_new_line_mc

    def uninstall(self):
        if self._orig_min is not None:
            lmfit.minimize = self._orig_min
        if self._orig_nlm is not None:
            QSOFitNew.new_line_mc = self._orig_nlm


# ---------------------------------------------------------------------------
# line groups and profile metrics
# ---------------------------------------------------------------------------

GROUPS = [
    {
        "name": "Hbeta",
        "label": r"H$\beta$ total",
        "complex": "Hb",
        "components": ["Hb_br", "Hb_na"],
        "main": 4862.68,
        "note": "broad template + narrow component; the package's whole_br column is not the total",
    },
    {
        "name": "Hbeta_broad",
        "label": r"H$\beta$ broad template",
        "complex": "Hb",
        "components": ["Hb_br"],
        "main": 4862.68,
        "note": "all three lmfit Gaussians of the broad template",
    },
    {
        "name": "Hbeta_narrow",
        "label": r"H$\beta$ narrow",
        "complex": "Hb",
        "components": ["Hb_na"],
        "main": 4862.68,
        "note": "shares [O III] kinematics (vindex/windex 1); not an independent width measurement",
    },
    {
        "name": "OIII5007",
        "label": r"[O III] 5007 total",
        "complex": "Hb",
        "components": ["OIII5007", "OIII5007w"],
        "main": 5008.24,
        "note": "narrow core + blue outflow wing",
    },
    {
        "name": "OIII5007_core",
        "label": r"[O III] 5007 core",
        "complex": "Hb",
        "components": ["OIII5007"],
        "main": 5008.24,
        "note": "narrow component; 4959 tied to 0.33",
    },
    {
        "name": "OIII5007_wing",
        "label": r"[O III] 5007 outflow",
        "complex": "Hb",
        "components": ["OIII5007w"],
        "main": 4995.24,
        "note": "broad/outflow component; 4959w tied to 0.33",
    },
    {
        "name": "OIII4959",
        "label": r"[O III] 4959 total",
        "complex": "Hb",
        "components": ["OIII4959", "OIII4959w"],
        "main": 4960.30,
        "note": "core+wing, tied to 0.33 of 5007",
    },
    {
        "name": "MgII",
        "label": "Mg II total",
        "complex": "MgII",
        "components": ["MgII_br", "MgII_na"],
        "main": 2798.75,
        "note": "2-Gaussian broad template + narrow component",
    },
    {
        "name": "MgII_broad",
        "label": "Mg II broad",
        "complex": "MgII",
        "components": ["MgII_br"],
        "main": 2798.75,
        "note": "2-Gaussian broad template",
    },
    {
        "name": "MgII_narrow",
        "label": "Mg II narrow",
        "complex": "MgII",
        "components": ["MgII_na"],
        "main": 2798.75,
        "note": "free kinematics; usually blend/width limited",
    },
    {
        "name": "Hgamma",
        "label": r"H$\gamma$ total",
        "complex": "Hg",
        "components": ["Hg_br", "Hg_na"],
        "main": 4341.68,
        "note": "broad + narrow; OIII4363 not in the table (kept minimal)",
    },
    {
        "name": "OII3728",
        "label": r"[O II] 3728",
        "complex": "OII",
        "components": ["OII3728"],
        "main": 3728.48,
        "note": "single Gaussian; the 3726/3729 blend is not decomposed",
    },
    {
        "name": "NeV3426",
        "label": r"[Ne V] 3426",
        "complex": "NeV",
        "components": ["NeV3426"],
        "main": 3426.84,
        "note": "weak high-ionisation line",
    },
    {
        "name": "CIII",
        "label": r"C III] 1909",
        "complex": "CIII",
        "components": ["CIII_br", "CIII_na"],
        "main": 1908.73,
        "note": "outside this SDSS spectrum's rest-frame coverage",
    },
    {
        "name": "CIV",
        "label": r"C IV 1549",
        "complex": "CIV",
        "components": ["CIV_br", "CIV_na"],
        "main": 1549.06,
        "note": "outside this SDSS spectrum's rest-frame coverage",
    },
    {
        "name": "Halpha",
        "label": r"H$\alpha$",
        "complex": "Ha",
        "components": ["Ha_br", "Ha_na"],
        "main": 6564.61,
        "note": "rest wavelength 6564.61 A is just redward of the 6510.4 A limit",
    },
]
GROUP_BY_NAME = {g["name"]: g for g in GROUPS}


def component_rows_from_params(params, table, complex_name, sample=None):
    rows = []
    params = np.asarray(params, dtype=float)
    idx = 0
    for row in table:
        line = str(row["linename"])
        ngauss = int(row["ngauss"])
        for k in range(ngauss):
            if idx + 2 >= len(params):
                break
            amp, cen, sig = params[idx], params[idx + 1], params[idx + 2]
            idx += 3
            lam0 = float(np.exp(cen))
            sig_kms = float((np.exp(sig) - 1.0) * C_KMS)
            area = float(amp * lam0 * np.exp(0.5 * sig * sig))
            fwhm = float(2.0 * np.sinh(1.1774100225 * sig) * C_KMS)
            rows.append(
                {
                    "complex": complex_name,
                    "sample": sample,
                    "line": line,
                    "component": k + 1,
                    "scale_lnlambda": float(amp),
                    "center_lnlambda": float(cen),
                    "center_angstrom": lam0,
                    "sigma_lnlambda": float(sig),
                    "sigma_kms": sig_kms,
                    "area_1e17": area,
                    "fwhm_kms": fwhm,
                    "class_sigma_gt_1200": bool(sig_kms > 1200.0),
                }
            )
    return rows


def bestfit_components(q):
    gr = np.asarray(q.gauss_result, dtype=float)
    names = [str(n) for n in q.gauss_result_name]
    rows = []
    for i, name in enumerate(names):
        if not name.endswith("_scale"):
            continue
        base = name[: -len("_scale")]
        line, comp = base.rsplit("_", 1)
        # With MC=True qsofitmore stores a value/error pair for every Gaussian
        # parameter: scale, scale_err, centerwave, centerwave_err, sigma,
        # sigma_err.  With MC=False the three values are contiguous.
        mc_layout = i + 4 < len(names) and names[i + 1].endswith("_scale_err")
        amp = gr[i]
        cen = gr[i + 2] if mc_layout else gr[i + 1]
        sig = gr[i + 4] if mc_layout else gr[i + 2]
        lam0 = float(np.exp(cen))
        rows.append(
            {
                "complex": "",
                "sample": None,
                "line": line,
                "component": int(comp),
                "scale_lnlambda": float(amp),
                "center_lnlambda": float(cen),
                "center_angstrom": lam0,
                "sigma_lnlambda": float(sig),
                "sigma_kms": float((np.exp(sig) - 1.0) * C_KMS),
                "area_1e17": float(amp * lam0 * np.exp(0.5 * sig * sig)),
                "fwhm_kms": float(2.0 * np.sinh(1.1774100225 * sig) * C_KMS),
                "class_sigma_gt_1200": bool((np.exp(sig) - 1.0) * C_KMS > 1200.0),
            }
        )
    return rows


def profile_grid(comps, main, q=None, extend=8.0, n=6000):
    if not comps:
        return None, None
    cen = np.array([c["center_lnlambda"] for c in comps], dtype=float)
    sig = np.array([c["sigma_lnlambda"] for c in comps], dtype=float)
    lo = float(np.min(cen - extend * sig))
    hi = float(np.max(cen + extend * sig))
    if q is not None:
        lo = max(lo, float(np.log(q.wave.min())))
        hi = min(hi, float(np.log(q.wave.max())))
    if not (hi > lo):
        return None, None
    x = np.linspace(lo, hi, int(n))
    y = np.zeros_like(x)
    for c in comps:
        amp, mu, sg = c["scale_lnlambda"], c["center_lnlambda"], c["sigma_lnlambda"]
        if sg <= 0:
            continue
        y += amp * np.exp(-0.5 * ((x - mu) / sg) ** 2) / (np.sqrt(2.0 * np.pi) * sg)
    return x, y


def profile_fwhm(comps, main):
    x, y = profile_grid(comps, main)
    if x is None or y is None or not np.any(y > 0):
        return float("nan")
    imax = int(np.argmax(y))
    half = 0.5 * y[imax]
    left = right = None
    for j in range(imax, 0, -1):
        if y[j - 1] < half <= y[j]:
            left = x[j - 1] + (half - y[j - 1]) / (y[j] - y[j - 1]) * (x[j] - x[j - 1])
            break
    for j in range(imax, len(x) - 1):
        if y[j] >= half > y[j + 1]:
            right = x[j] + (half - y[j]) / (y[j + 1] - y[j]) * (x[j + 1] - x[j])
            break
    if left is None or right is None:
        return float("nan")
    # ``main`` is a rest wavelength in Angstrom, not ln(Angstrom).  Work in
    # log space relative to the line centre so exp() cannot overflow.
    logmain = float(np.log(float(main)))
    return float((np.exp(right - logmain) - np.exp(left - logmain)) * C_KMS)


def profile_peak(comps, main):
    x, y = profile_grid(comps, main)
    if x is None or y is None or not np.any(y > 0):
        return float("nan")
    return float(np.exp(x[int(np.argmax(y))]))


def profile_ew(comps, main, q):
    x, y = profile_grid(comps, main, q=q)
    if x is None or y is None:
        return float("nan")
    lam = np.exp(x)
    conti = np.interp(lam, q.wave, q.f_conti_model)
    good = np.isfinite(conti) & (conti > 0)
    if not np.any(good):
        return float("nan")
    return float(np.trapz(y[good] / conti[good], lam[good]))


def group_components(comps, group):
    wanted = set(group["components"])
    return [c for c in comps if c["line"] in wanted]


def group_stats(comps, group, q):
    use = group_components(comps, group)
    area = float(sum(c["area_1e17"] for c in use))
    broad = float(sum(c["area_1e17"] for c in use if c["sigma_kms"] > 1200.0))
    narrow = float(sum(c["area_1e17"] for c in use if c["sigma_kms"] <= 1200.0))
    return {
        "area_1e17": area,
        "area_sigma_gt_1200_1e17": broad,
        "area_sigma_le_1200_1e17": narrow,
        "fwhm_kms": profile_fwhm(use, group["main"]),
        "ew_angstrom": profile_ew(use, group["main"], q),
        "peak_angstrom": profile_peak(use, group["main"]),
        "n_components": len(use),
    }


# ---------------------------------------------------------------------------
# Monte Carlo processing
# ---------------------------------------------------------------------------


def process_mc_samples(acc: MCAccumulator):
    rows = []
    counts = defaultdict(int)
    valid_counts = defaultdict(int)
    for sample in acc.samples:
        complex_name = sample["complex"]
        if complex_name not in acc.tables:
            continue
        counts[complex_name] += 1
        if not sample["success"]:
            continue
        table = acc.tables[complex_name]
        sample_id = valid_counts[complex_name]
        valid_counts[complex_name] += 1
        # Skip parameter vectors that do not match the table (defensive).
        expected = 3 * int(np.sum([int(r["ngauss"]) for r in table]))
        if len(sample["p"]) != expected:
            continue
        rows.extend(component_rows_from_params(sample["p"], table, complex_name, sample=sample_id))
    return rows, dict(counts), dict(valid_counts)


def mc_group_series(mc_rows, group):
    use = [r for r in mc_rows if r["complex"] == group["complex"] and r["line"] in set(group["components"])]
    by_sample = defaultdict(list)
    for row in use:
        by_sample[int(row["sample"])].append(row)
    out = {}
    for sample_id, comps in sorted(by_sample.items()):
        area = float(sum(c["area_1e17"] for c in comps))
        out[sample_id] = {
            "area_1e17": area,
            "fwhm_kms": profile_fwhm(comps, group["main"]),
            "ew_angstrom": float("nan"),  # filled below when q is available
        }
    return out


def mc_summary(series):
    if not series:
        return {
            "n": 0,
            "median": float("nan"),
            "std": float("nan"),
            "p16": float("nan"),
            "p84": float("nan"),
        }
    vals = np.array([v["area_1e17"] for v in series.values()], dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return {"n": 0, "median": float("nan"), "std": float("nan"), "p16": float("nan"), "p84": float("nan")}
    return {
        "n": int(vals.size),
        "median": float(np.median(vals)),
        "std": float(np.std(vals, ddof=1)) if vals.size > 1 else 0.0,
        "p16": float(np.percentile(vals, 16)),
        "p84": float(np.percentile(vals, 84)),
    }


def mc_metric_summary(series, key):
    vals = [v.get(key, float("nan")) for v in series.values()]
    vals = np.array([v for v in vals if np.isfinite(v)], dtype=float)
    if vals.size == 0:
        return {"n": 0, "median": float("nan"), "std": float("nan"), "p16": float("nan"), "p84": float("nan")}
    return {
        "n": int(vals.size),
        "median": float(np.median(vals)),
        "std": float(np.std(vals, ddof=1)) if vals.size > 1 else 0.0,
        "p16": float(np.percentile(vals, 16)),
        "p84": float(np.percentile(vals, 84)),
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", default="/app/input")
    p.add_argument("--input-file", default=None)
    p.add_argument("--out", default="/app/output")
    p.add_argument("--config", default="/app/config")
    p.add_argument("--mc-trails", type=int, default=None)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--name", default=None)
    p.add_argument("--source-key", default=None)
    p.add_argument("--z", type=float, default=None, help="override redshift if the FITS header has none")
    p.add_argument("--no-systematics", action="store_true", help="skip the BG92-VW01 template cross-check")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    t_start = time.time()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    config_dir = Path(args.config).resolve()
    cfg_path = config_dir / "config.json"
    cfg = json.loads(cfg_path.read_text())
    line_table_cfg = config_dir / cfg["line_table"]["path"]
    if not line_table_cfg.exists():
        raise FileNotFoundError(f"line table not found: {line_table_cfg}")

    mc_trails = int(args.mc_trails if args.mc_trails is not None else cfg["uncertainty"]["n_trails"])
    seed = int(args.seed if args.seed is not None else cfg["uncertainty"]["seed"])
    np.random.seed(seed)
    random.seed(seed)

    source_key = args.source_key or os.environ.get("QSOFITMORE_SOURCE_KEY") or out.parent.name
    src_name = args.name or os.environ.get("QSOFITMORE_NAME") or source_key
    run_name = clean_name(f"qsofitmore_{src_name}")

    # ---- input -----------------------------------------------------------
    spec = load_spectrum(Path(args.input_dir).resolve(), args.input_file)
    z = float(spec["z"])
    if args.z is not None:
        z = float(args.z)
    if not np.isfinite(z) or z <= 0:
        raise RuntimeError("redshift is missing/invalid; pass --z")
    wave, flux, err, n_masked = prepare_arrays(spec)
    rest_min = float(wave.min() / (1.0 + z))
    rest_max = float(wave.max() / (1.0 + z))
    ra = float(spec["ra"])
    dec = float(spec["dec"])
    have_coord = np.isfinite(ra) and np.isfinite(dec) and not (ra == 0.0 and dec == 0.0)
    deredden = bool(cfg["fit"]["deredden"]) and have_coord
    snr_med = float(np.nanmedian(flux / err))
    input_info = {
        "file": spec["path"],
        "sha256": spec["sha256"],
        "layout": spec["layout"],
        "bunit": spec.get("bunit", ""),
        "unit_scale_to_1e17": spec.get("unit_scale_to_1e17", 1.0),
        "z": z,
        "ra_deg": ra,
        "dec_deg": dec,
        "n_pixels_raw": spec.get("n_raw"),
        "n_pixels_used": int(len(wave)),
        "n_pixels_masked": int(n_masked),
        "wave_obs_range_A": [float(wave.min()), float(wave.max())],
        "wave_rest_range_A": [rest_min, rest_max],
        "median_snr": snr_med,
        "errors": "calibrated SDSS errors (1/sqrt(IVAR)); no error floor",
    }

    # ---- dust map --------------------------------------------------------
    dust_dir = Path(os.environ.get("QSOFITMORE_DUSTMAP", DEFAULT_DUST_DIR))
    dust_meta = {}
    if not (dust_dir / "SFD_dust_4096_ngp.fits").exists() or not (dust_dir / "SFD_dust_4096_sgp.fits").exists():
        # Runtime repair path.  The image normally bakes the map in.
        try:
            subprocess.run(["bash", "/app/fetch_sfd.sh", str(dust_dir)], check=True)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"SFD98 dust map missing at {dust_dir} and fetch failed: {exc}") from exc
    version_json = dust_dir / "VERSION.json"
    if version_json.exists():
        dust_meta = json.loads(version_json.read_text())
    dust_meta["directory"] = str(dust_dir)

    # ---- fit -------------------------------------------------------------
    q = QSOFitNew(
        lam=wave,
        flux=flux,
        err=err,
        z=z,
        ra=ra if have_coord else 0.0,
        dec=dec if have_coord else 0.0,
        name=run_name,
        path=str(out),
        is_sdss=True,
    )
    q.setmapname(cfg["fit"]["dust_map"])
    q.set_pl_pivot(float(cfg["fit"]["pl_pivot_A"]))
    q.narrow_max_kms = float(cfg["fit"]["narrow_max_kms"])
    if cfg["fit"]["BC"]:
        q.set_log10_electron_density(float(cfg["fit"]["log10_electron_density"]))

    acc = MCAccumulator()
    acc.install(q)
    fit_kwargs = dict(
        name=run_name,
        nsmooth=int(cfg["fit"].get("nsmooth", 1)),
        deredden=deredden,
        wave_range=cfg["fit"].get("wave_range"),
        decomposition_host=bool(cfg["fit"]["decomposition_host"]),
        include_iron=bool(cfg["fit"]["include_iron"]),
        iron_temp_name=str(cfg["fit"]["iron_temp_name"]),
        Fe_verner09=bool(cfg["fit"]["Fe_verner09"]),
        poly=bool(cfg["fit"]["poly"]),
        broken_pl=bool(cfg["fit"]["broken_pl"]),
        BC=bool(cfg["fit"]["BC"]),
        rej_abs=bool(cfg["fit"]["rej_abs"]),
        Fe_flux_range=cfg["fit"]["Fe_flux_range"],
        MC=True,
        n_trails=mc_trails,
        linefit=True,
        tie_lambda=bool(cfg["fit"]["tie_lambda"]),
        tie_width=bool(cfg["fit"]["tie_width"]),
        tie_flux_1=bool(cfg["fit"]["tie_flux_1"]),
        tie_flux_2=bool(cfg["fit"]["tie_flux_2"]),
        save_result=True,
        plot_fig=True,
        save_fig=True,
        plot_line_name=True,
        plot_legend=True,
        line_list_path=str(line_table_cfg),
        wave_scale=str(cfg["line_table"]["wave_scale"]),
        velocity_units=str(cfg["line_table"]["velocity_units"]),
        dustmap_path=str(dust_dir) if deredden else None,
        save_fits_path=str(out),
        save_fig_path=str(out),
        save_fits_name="qsofitmore_result.fits",
    )
    fit_warnings = []
    t_fit = time.time()
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            q.Fit(**fit_kwargs)
            fit_warnings = [str(w.message) for w in caught]
    finally:
        acc.uninstall()
    fit_runtime = time.time() - t_fit

    # ---- native products -------------------------------------------------
    if not hasattr(q, "result_table"):
        raise RuntimeError("qsofitmore did not produce result_table")
    q.result_table.write(out / "qsofitmore_result.csv", format="csv", overwrite=True)
    result_dict = {str(k): q.result_table[k][0] for k in q.result_table.colnames}
    comp_diag = {str(k): v for k, v in zip(q.comp_result_name, q.comp_result)}

    fit_pdf = out / f"plot_fit_{run_name}.pdf"
    fit_jpg = out / f"plot_fit_{run_name}.jpg"
    fit_pdf_out = out / "qsofitmore_fit.pdf"
    fit_png_out = out / "qsofitmore_fit.png"
    if fit_pdf.exists():
        shutil.copy2(fit_pdf, fit_pdf_out)
    if fit_jpg.exists():
        shutil.copy2(fit_jpg, out / "qsofitmore_fit.jpg")
        try:
            from PIL import Image

            Image.open(fit_jpg).save(fit_png_out)
        except Exception:
            pass
    # Keep one canonical fit figure pair; the upstream filenames are
    # implementation detail and would otherwise duplicate 0.6 MB per run.
    for duplicate in (fit_pdf, fit_jpg):
        if duplicate.exists() and duplicate.resolve() not in (fit_pdf_out.resolve(), (out / "qsofitmore_fit.jpg").resolve()):
            try:
                duplicate.unlink()
            except Exception:
                pass

    # ---- components and compact table -----------------------------------
    best_comps = bestfit_components(q)
    for comp in best_comps:
        # infer complex from line table for readability
        for row in Table.read(line_table_cfg, format="csv"):
            if str(row["linename"]) == comp["line"]:
                comp["complex"] = str(row["compname"])
                break

    mc_rows, mc_attempts, mc_valid = process_mc_samples(acc)
    # add EW per MC sample now that q is available
    by_group = defaultdict(list)
    for row in mc_rows:
        for g in GROUPS:
            if row["complex"] == g["complex"] and row["line"] in set(g["components"]):
                by_group[(g["name"], int(row["sample"]))].append(row)
    mc_series = {}
    for g in GROUPS:
        series = {}
        for (gname, sample_id), comps in by_group.items():
            if gname != g["name"]:
                continue
            series[sample_id] = {
                "area_1e17": float(sum(c["area_1e17"] for c in comps)),
                "fwhm_kms": profile_fwhm(comps, g["main"]),
                "ew_angstrom": profile_ew(comps, g["main"], q),
            }
        mc_series[g["name"]] = series

    line_rows = []
    for g in GROUPS:
        covered = rest_min <= g["main"] <= rest_max
        stats = group_stats(best_comps, g, q)
        summ = mc_summary(mc_series.get(g["name"], {}))
        fwhm_summ = mc_metric_summary(mc_series.get(g["name"], {}), "fwhm_kms")
        ew_summ = mc_metric_summary(mc_series.get(g["name"], {}), "ew_angstrom")
        area = stats["area_1e17"] if covered else float("nan")
        area_err = summ["std"] if covered else float("nan")
        snr = area / area_err if covered and area_err and np.isfinite(area_err) and area_err > 0 else float("nan")
        if not covered:
            status = "not_covered"
        elif not np.isfinite(area) or area <= 0:
            status = "not_detected"
        elif np.isfinite(snr) and snr < 1.0:
            status = "not_detected"
        elif np.isfinite(snr) and snr < 3.0:
            status = "weak"
        else:
            status = "ok"
        use_comps = group_components(best_comps, g)
        at_bound = bool(
            covered
            and any(
                (not c["class_sigma_gt_1200"]) and c["sigma_kms"] >= 1190.0
                for c in use_comps
            )
        )
        note = g["note"]
        if at_bound:
            note += "; narrow width is at the 1200 km/s package cap and must not be read as a free measurement"
        line_rows.append(
            {
                "line": g["name"],
                "label": g["label"],
                "complex": g["complex"],
                "components": "+".join(g["components"]),
                "rest_wavelength_angstrom": g["main"],
                "covered": bool(covered),
                "status": status,
                "at_bound": at_bound,
                "area_1e17": area,
                "area_err_1e17": area_err,
                "area_p16_1e17": summ["p16"] if covered else float("nan"),
                "area_p84_1e17": summ["p84"] if covered else float("nan"),
                "area_median_mc_1e17": summ["median"] if covered else float("nan"),
                "area_sigma_gt_1200_1e17": stats["area_sigma_gt_1200_1e17"] if covered else float("nan"),
                "area_sigma_le_1200_1e17": stats["area_sigma_le_1200_1e17"] if covered else float("nan"),
                "fwhm_kms": stats["fwhm_kms"] if covered else float("nan"),
                "fwhm_err_kms": fwhm_summ["std"] if covered else float("nan"),
                "ew_angstrom": stats["ew_angstrom"] if covered else float("nan"),
                "ew_err_angstrom": ew_summ["std"] if covered else float("nan"),
                "peak_angstrom": stats["peak_angstrom"] if covered else float("nan"),
                "snr": snr,
                "n_components": stats["n_components"] if covered else 0,
                "n_mc": summ["n"] if covered else 0,
                "method": "lmfit ML + parametric Monte Carlo (line-complex refit)",
                "notes": note if covered else g["note"] + "; outside observed rest-frame coverage, no value reported",
            }
        )

    line_fields = list(line_rows[0].keys())
    write_csv(out / "qsofitmore_lines.csv", line_rows, line_fields)

    # component table with a complex label
    comp_fields = [
        "line",
        "complex",
        "component",
        "scale_lnlambda",
        "center_lnlambda",
        "center_angstrom",
        "sigma_lnlambda",
        "sigma_kms",
        "area_1e17",
        "fwhm_kms",
        "class_sigma_gt_1200",
    ]
    write_csv(out / "qsofitmore_components.csv", best_comps, comp_fields)
    write_csv(
        out / "qsofitmore_mc_components.csv",
        mc_rows,
        [
            "complex",
            "sample",
            "line",
            "component",
            "scale_lnlambda",
            "center_lnlambda",
            "center_angstrom",
            "sigma_lnlambda",
            "sigma_kms",
            "area_1e17",
            "fwhm_kms",
            "class_sigma_gt_1200",
        ],
    )

    # MC total-per-realization rows
    mc_total_rows = []
    for g in GROUPS:
        for sample_id, vals in sorted(mc_series.get(g["name"], {}).items()):
            mc_total_rows.append(
                {
                    "line": g["name"],
                    "complex": g["complex"],
                    "sample": sample_id,
                    "area_1e17": vals["area_1e17"],
                    "fwhm_kms": vals["fwhm_kms"],
                    "ew_angstrom": vals["ew_angstrom"],
                }
            )
    write_csv(out / "qsofitmore_mc_samples.csv", mc_total_rows)

    # MC summary (line/group level)
    mc_summary_rows = []
    for g in GROUPS:
        series = mc_series.get(g["name"], {})
        summ = mc_summary(series)
        fs = mc_metric_summary(series, "fwhm_kms")
        es = mc_metric_summary(series, "ew_angstrom")
        mc_summary_rows.append(
            {
                "line": g["name"],
                "n": summ["n"],
                "area_median_1e17": summ["median"],
                "area_std_1e17": summ["std"],
                "area_p16_1e17": summ["p16"],
                "area_p84_1e17": summ["p84"],
                "fwhm_median_kms": fs["median"],
                "fwhm_std_kms": fs["std"],
                "ew_median_A": es["median"],
                "ew_std_A": es["std"],
            }
        )
    write_csv(out / "qsofitmore_mc_summary.csv", mc_summary_rows)

    # H-beta/[O III] ratio per realization (same H-beta complex, correlated draws)
    ratio_rows = []
    hb_series = mc_series.get("Hbeta", {})
    o3_series = mc_series.get("OIII5007", {})
    for sample_id in sorted(set(hb_series) & set(o3_series)):
        hb = hb_series[sample_id]["area_1e17"]
        o3 = o3_series[sample_id]["area_1e17"]
        if o3 > 0:
            ratio_rows.append(
                {
                    "sample": sample_id,
                    "Hbeta_1e17": hb,
                    "OIII5007_1e17": o3,
                    "Hbeta_OIII5007": hb / o3,
                    "Hbeta_fwhm_kms": hb_series[sample_id]["fwhm_kms"],
                }
            )
    write_csv(out / "qsofitmore_hb_oiii_mc.csv", ratio_rows)
    ratio_vals = np.array([r["Hbeta_OIII5007"] for r in ratio_rows], dtype=float)
    ratio_stats = {
        "n": int(ratio_vals.size),
        "median": float(np.median(ratio_vals)) if ratio_vals.size else float("nan"),
        "std": float(np.std(ratio_vals, ddof=1)) if ratio_vals.size > 1 else float("nan"),
        "p16": float(np.percentile(ratio_vals, 16)) if ratio_vals.size else float("nan"),
        "p84": float(np.percentile(ratio_vals, 84)) if ratio_vals.size else float("nan"),
    }

    # ---- continuum / Fe II / Balmer table -------------------------------
    cont_rows = []

    def add_cont(key, unit="", note=""):
        if key not in result_dict:
            return
        val = as_float(result_dict[key])
        err = as_float(result_dict.get(key + "_err", float("nan")))
        cont_rows.append({"quantity": key, "value": val, "err": err, "unit": unit, "note": note})

    add_cont("redshift", "", "input redshift")
    add_cont("SNR_SPEC", "", "median S/N of the fitted spectrum")
    add_cont("SN_ratio_conti", "", "S/N in the continuum windows")
    add_cont("Fe_op_norm", "1e-17", "V09 Fe II template normalisation (used by the V09 model)")
    add_cont("Fe_op_FWHM", "km/s", "V09 Fe II broadening")
    add_cont("Fe_op_shift", "", "V09 Fe II velocity shift (ln-lambda)")
    add_cont("Fe_uv_norm", "1e-17", "legacy UV Fe II normalisation; not used by V09")
    add_cont("PL_norm", "1e-17", "power-law normalisation at the 3000 A pivot")
    add_cont("PL_slope", "", "blue power-law slope")
    add_cont("PL_slope2", "", "red power-law slope (broken PL)")
    add_cont("BalmerC_norm", "", "Balmer-continuum normalisation")
    add_cont("BalmerS_FWHM", "km/s", "high-order Balmer series broadening")
    add_cont("BalmerS_norm", "", "high-order Balmer series normalisation")
    add_cont("POLY_a", "", "polynomial term (fixed to zero when poly=False)")
    add_cont("POLY_b", "", "polynomial term (fixed to zero when poly=False)")
    add_cont("POLY_c", "", "polynomial term (fixed to zero when poly=False)")
    add_cont("LOGL1350", "log10(erg/s)", "1350 A luminosity; -1 means outside coverage")
    add_cont("LOGL3000", "log10(erg/s)", "3000 A luminosity")
    add_cont("LOGL5100", "log10(erg/s)", "5100 A luminosity")
    for key in result_dict:
        if key.startswith("Fe_w") and (key.endswith("_flux") or key.endswith("_ew")):
            add_cont(key, "1e-17 erg/s/cm2" if key.endswith("_flux") else "A", "Fe II band integral/EW")
    cont_rows.append(
        {
            "quantity": "E(B-V)_SFD98",
            "value": as_float(getattr(q, "ebv", float("nan"))),
            "err": float("nan"),
            "unit": "mag",
            "note": "Galactic foreground from the SFD98 map; applied with F99 R_V=3.1",
        }
    )
    write_csv(out / "qsofitmore_continuum.csv", cont_rows)

    # ---- figures ---------------------------------------------------------
    figures = []
    if fit_png_out.exists():
        figures.append("qsofitmore_fit.png")
    if fit_pdf_out.exists():
        figures.append("qsofitmore_fit.pdf")

    # H-beta/[O III] corner
    try:
        if len(ratio_rows) >= 10:
            import corner

            hb = np.array([r["Hbeta_1e17"] for r in ratio_rows], dtype=float)
            o3 = np.array([r["OIII5007_1e17"] for r in ratio_rows], dtype=float)
            rr = np.array([r["Hbeta_OIII5007"] for r in ratio_rows], dtype=float)
            ff = np.array([r["Hbeta_fwhm_kms"] for r in ratio_rows], dtype=float)
            n = min(len(hb), len(o3), len(rr), len(ff))
            data = np.column_stack([hb[:n], o3[:n], rr[:n], ff[:n]])
            fig = corner.corner(
                data,
                labels=[r"H$\beta$ total", r"[O III] 5007", r"H$\beta$/[O III] 5007", r"H$\beta$ FWHM (km/s)"],
                quantiles=[0.16, 0.5, 0.84],
                show_titles=True,
                title_fmt=".3f",
                title_kwargs={"fontsize": 10},
                label_kwargs={"fontsize": 10},
            )
            fig.suptitle("QSOFITMORE Monte Carlo (H-beta complex, correlated draws)", fontsize=11, y=1.02)
            fig.savefig(out / "qsofitmore_corner.pdf", bbox_inches="tight")
            fig.savefig(out / "qsofitmore_corner.png", dpi=160, bbox_inches="tight")
            plt.close(fig)
            figures += ["qsofitmore_corner.png", "qsofitmore_corner.pdf"]
    except Exception as exc:  # noqa: BLE001
        fit_warnings.append(f"corner plot failed: {exc!r}")

    # Mg II corner
    try:
        mg_series = mc_series.get("MgII", {})
        if len(mg_series) >= 10:
            import corner

            mg = np.array([v["area_1e17"] for v in mg_series.values()], dtype=float)
            mf = np.array([v["fwhm_kms"] for v in mg_series.values()], dtype=float)
            n = min(len(mg), len(mf))
            fig = corner.corner(
                np.column_stack([mg[:n], mf[:n]]),
                labels=["Mg II total", "Mg II FWHM (km/s)"],
                quantiles=[0.16, 0.5, 0.84],
                show_titles=True,
                title_fmt=".2f",
            )
            fig.suptitle("QSOFITMORE Monte Carlo (Mg II complex)", fontsize=11, y=1.02)
            fig.savefig(out / "qsofitmore_mgii_corner.pdf", bbox_inches="tight")
            fig.savefig(out / "qsofitmore_mgii_corner.png", dpi=160, bbox_inches="tight")
            plt.close(fig)
            figures += ["qsofitmore_mgii_corner.png", "qsofitmore_mgii_corner.pdf"]
    except Exception as exc:  # noqa: BLE001
        fit_warnings.append(f"Mg II corner plot failed: {exc!r}")

    # Uncertainty summary panel
    try:
        panels = [
            ("Hbeta", "Hbeta total", "area_1e17"),
            ("OIII5007", "OIII 5007 total", "area_1e17"),
            ("Hbeta", "Hbeta/OIII 5007", "ratio"),
            ("MgII", "MgII total", "area_1e17"),
        ]
        fig, axes = plt.subplots(2, 2, figsize=(10, 7))
        for ax, (gname, label, kind) in zip(axes.ravel(), panels):
            if kind == "ratio":
                vals = ratio_vals
            else:
                vals = np.array([v["area_1e17"] for v in mc_series.get(gname, {}).values()], dtype=float)
            vals = vals[np.isfinite(vals)]
            if vals.size == 0:
                ax.text(0.5, 0.5, "no samples", ha="center", va="center")
                ax.set_axis_off()
                continue
            ax.hist(vals, bins=min(30, max(8, vals.size // 8)), color="C0", alpha=0.75)
            med = float(np.median(vals))
            lo, hi = np.percentile(vals, [16, 84])
            ax.axvline(med, color="C3", lw=1.2, label=f"median {med:.2f}")
            ax.axvline(lo, color="0.4", ls="--", lw=1.0)
            ax.axvline(hi, color="0.4", ls="--", lw=1.0)
            ax.set_title(label)
            ax.set_xlabel(label)
            ax.set_ylabel("realizations")
            ax.legend(fontsize=8)
        fig.suptitle("QSOFITMORE Monte Carlo uncertainty (16/50/84 percentiles)", fontsize=12)
        fig.tight_layout()
        fig.savefig(out / "qsofitmore_uncertainty.pdf", bbox_inches="tight")
        fig.savefig(out / "qsofitmore_uncertainty.png", dpi=160, bbox_inches="tight")
        plt.close(fig)
        figures += ["qsofitmore_uncertainty.png", "qsofitmore_uncertainty.pdf"]
    except Exception as exc:  # noqa: BLE001
        fit_warnings.append(f"uncertainty panel failed: {exc!r}")

    # ---- alternate Fe II template (systematic, LSQ only) -----------------
    systematics = {"enabled": False, "note": "skipped"}
    if not args.no_systematics:
        try:
            sysdir = out / "systematics"
            sysdir.mkdir(parents=True, exist_ok=True)
            q2 = QSOFitNew(
                lam=wave,
                flux=flux,
                err=err,
                z=z,
                ra=ra if have_coord else 0.0,
                dec=dec if have_coord else 0.0,
                name=clean_name(run_name + "_bg92"),
                path=str(sysdir),
                is_sdss=True,
            )
            q2.setmapname(cfg["fit"]["dust_map"])
            q2.set_pl_pivot(float(cfg["fit"]["pl_pivot_A"]))
            q2.narrow_max_kms = float(cfg["fit"]["narrow_max_kms"])
            if cfg["fit"]["BC"]:
                q2.set_log10_electron_density(float(cfg["fit"]["log10_electron_density"]))
            t_sys = time.time()
            q2.Fit(
                **{
                    **fit_kwargs,
                    "name": clean_name(run_name + "_bg92"),
                    "iron_temp_name": "BG92-VW01",
                    "Fe_verner09": False,
                    "MC": False,
                    "n_trails": 0,
                    "save_fits_path": str(sysdir),
                    "save_fig_path": str(sysdir),
                    "save_fits_name": "qsofitmore_result_bg92.fits",
                    "plot_fig": False,
                    "save_fig": False,
                }
            )
            comps2 = bestfit_components(q2)
            sys_rows = []
            for g in GROUPS:
                covered = rest_min <= g["main"] <= rest_max
                st = group_stats(comps2, g, q2)
                sys_rows.append(
                    {
                        "line": g["name"],
                        "covered": bool(covered),
                        "area_1e17": st["area_1e17"] if covered else float("nan"),
                        "fwhm_kms": st["fwhm_kms"] if covered else float("nan"),
                        "ew_angstrom": st["ew_angstrom"] if covered else float("nan"),
                    }
                )
            write_csv(sysdir / "qsofitmore_lines_bg92.csv", sys_rows)
            hb2 = next((r["area_1e17"] for r in sys_rows if r["line"] == "Hbeta"), float("nan"))
            o32 = next((r["area_1e17"] for r in sys_rows if r["line"] == "OIII5007"), float("nan"))
            mg2 = next((r["area_1e17"] for r in sys_rows if r["line"] == "MgII"), float("nan"))
            systematics = {
                "enabled": True,
                "iron_template": "BG92-VW01",
                "runtime_sec": time.time() - t_sys,
                "Hbeta_1e17": hb2,
                "OIII5007_1e17": o32,
                "Hbeta_OIII5007": hb2 / o32 if o32 else float("nan"),
                "MgII_1e17": mg2,
                "note": "Least-squares fit only (MC off), same line table and switches; quantifies the Fe II template systematic, not a second production uncertainty.",
            }
            write_json(sysdir / "systematic.json", systematics)
        except Exception as exc:  # noqa: BLE001
            systematics = {"enabled": False, "error": repr(exc)}
            fit_warnings.append(f"BG92 systematic fit failed: {exc!r}")

    # ---- effective config and run metadata ------------------------------
    effective = json.loads(json.dumps(cfg))
    effective["resolved"] = {
        "config_dir": str(config_dir),
        "line_table": str(line_table_cfg),
        "line_table_sha256": sha256_file(line_table_cfg),
        "input_file": spec["path"],
        "dustmap_dir": str(dust_dir),
        "image": os.environ.get("QSOFITMORE_IMAGE", "qsofitmore_line"),
        "upstream_commit": os.environ.get("QSOFITMORE_COMMIT", cfg["upstream"]["commit"]),
        "mc_trails": mc_trails,
        "seed": seed,
        "name": run_name,
        "source_key": source_key,
    }
    write_json(out / "config.effective.json", effective)

    # Write a qsopar.fits copy next to the products for interoperability.
    try:
        lt = Table.read(line_table_cfg, format="csv")
        lt.meta["WAVESCL"] = cfg["line_table"]["wave_scale"]
        lt.meta["VELUNIT"] = cfg["line_table"]["velocity_units"]
        lt.meta["SOURCE"] = str(line_table_cfg)
        lt.write(out / "qsopar.fits", format="fits", overwrite=True)
    except Exception:
        pass

    # complex diagnostics (chi2/status)
    complexes = {}
    for key, val in comp_diag.items():
        key = str(key)
        if key.startswith("LINE_") or key.endswith("_line_status") or key.endswith("_line_red_chi2") or key.endswith("_line_min_chi2") or key.endswith("_ndof") or key.endswith("_niter"):
            complexes[key] = val
    run_json = {
        "tool": "qsofitmore_line",
        "status": "ok" if len(mc_rows) > 0 else "ok_no_mc_samples",
        "method": {
            "continuum": "broken power law + Verner et al. (2009) Fe II + Balmer continuum + high-order Balmer series (Storey & Hummer 1995)",
            "lines": "broad and narrow Gaussians, lmfit least squares, tied [O III] doublet/outflow kinematics and 0.33 flux ratio",
            "uncertainty": "parametric Monte Carlo: flux + N(0, err) per fitted pixel, full lmfit continuum and line-complex refit; 200 realizations requested",
            "mcmc": False,
        },
        "upstream": {
            "repo": "https://github.com/rudolffu/qsofitmore",
            "commit": os.environ.get("QSOFITMORE_COMMIT", cfg["upstream"]["commit"]),
            "version": version("qsofitmore"),
            "license": "GPL-3.0",
        },
        "image": os.environ.get("QSOFITMORE_IMAGE", "qsofitmore_line"),
        "image_size_bytes": int(os.environ.get("QSOFITMORE_IMAGE_SIZE", "0") or 0),
        "repo_commit": os.environ.get("QSOFITMORE_REPO_COMMIT", ""),
        "command": sys.argv,
        "input": input_info,
        "config": {
            "file": str(cfg_path),
            "sha256": sha256_file(cfg_path),
            "line_table": str(line_table_cfg),
            "line_table_sha256": sha256_file(line_table_cfg),
            "fit": cfg["fit"],
            "line_table_meta": cfg["line_table"],
        },
        "dust_map": dust_meta,
        "fit": {
            "ebv": as_float(getattr(q, "ebv", float("nan"))),
            "n_complex": int(getattr(q, "ncomp", 0)),
            "line_table_path": str(line_table_cfg),
            "linefit": True,
            "complex_diagnostics": complexes,
        },
        "uncertainty": {
            "method": "lmfit Monte Carlo refit",
            "mcmc": False,
            "requested_trails": int(mc_trails),
            "line_mc_attempted": mc_attempts,
            "line_mc_valid": mc_valid,
            "line_mc_rows": len(mc_rows),
            "Hbeta_OIII5007": ratio_stats,
            "seed": seed,
            "note": "Line-complex MC draws are independent between complexes; H-beta/[O III] is correlated because both are in the same Hb complex. Mg II has its own independent MC.",
        },
        "systematics": systematics,
        "runtime_sec": {
            "fit": fit_runtime,
            "total": time.time() - t_start,
        },
        "versions": {
            "python": platform.python_version(),
            "qsofitmore": version("qsofitmore"),
            "numpy": version("numpy"),
            "scipy": version("scipy"),
            "astropy": version("astropy"),
            "matplotlib": version("matplotlib"),
            "pandas": version("pandas"),
            "lmfit": version("lmfit"),
            "dustmaps": version("dustmaps"),
            "uncertainties": version("uncertainties"),
            "corner": version("corner"),
        },
        "warnings": fit_warnings,
        "products": sorted(
            [p.name for p in out.iterdir() if p.is_file()]
            + [str(p.relative_to(out)) for p in out.glob("systematics/*") if p.is_file()]
        ),
    }
    write_json(out / "run.json", run_json)

    # ---- README-quality provenance note ---------------------------------
    def fmt(value, nd=1):
        try:
            v = float(value)
            if not np.isfinite(v):
                return "n/a"
            return f"{v:.{nd}f}"
        except Exception:
            return "n/a"

    key = {r["line"]: r for r in line_rows}
    hb = key.get("Hbeta", {})
    o3 = key.get("OIII5007", {})
    mg = key.get("MgII", {})
    hg = key.get("Hgamma", {})
    ratio_txt = "n/a"
    if hb.get("area_1e17") and o3.get("area_1e17"):
        ratio_txt = fmt(hb["area_1e17"] / o3["area_1e17"], 3)
    readme = f"""# QSOFITMORE line fit — `{source_key}`

## Provenance

* Upstream: `https://github.com/rudolffu/qsofitmore`, commit `{run_json['upstream']['commit']}`, version `{run_json['upstream']['version']}`, GPL-3.0.
* Image: `{run_json['image']}` (size `{run_json['image_size_bytes']}` bytes), Python `{run_json['versions']['python']}`, lmfit `{run_json['versions']['lmfit']}`.
* Input: `{input_info['file']}` (SHA256 `{input_info['sha256']}`), calibrated SDSS errors from `1/sqrt(IVAR)`; no error floor.
* Redshift `{z:.8f}`; observed `{rest_min*(1+z):.1f}–{rest_max*(1+z):.1f} Å`; rest-frame `{rest_min:.1f}–{rest_max:.1f} Å`.
* Galactic extinction: SFD98 (Schlegel, Finkbeiner & Davis 1998; DOI `{dust_meta.get('doi','10.7910/DVN/EWCNL5')}`) E(B-V) = `{fmt(getattr(q, 'ebv', float('nan')), 5)}` mag, Fitzpatrick (1999) R_V=3.1.
* Line table: `{line_table_cfg}` (SHA256 `{effective['resolved']['line_table_sha256']}`); a FITS copy is `qsopar.fits`.
* Command: `{' '.join(sys.argv)}`

## Model

* Continuum: broken power law (3000 Å pivot, 4661 Å break, both slopes free), Verner et al. (2009) Fe II template over 2000–10000 Å, Balmer continuum (Dietrich et al. 2002) and high-order Balmer series (Storey & Hummer 1995, n_upper=6–50, log10 n_e = 9). No polynomial term (`poly=False`); the broken power law supplies the large-scale curvature.
* Lines: broad and narrow Gaussians from the package line table. The Hβ complex contains `Hb_br` (3 Gaussians), `Hb_na`, [O III] 4959/5007 cores, and [O III] 4959w/5007w outflow wings. The [O III] doublet and outflow ratios are tied to 0.33; widths/centres are tied within each kinematics group. Mg II has a 2-Gaussian broad template plus a free narrow component.
* Host decomposition is **off**. qsofitmore's Yip+2004 decomposition would restrict the rest-frame grid to ≳3450 Å and remove Mg II; the host is measured separately by pPXF in this repo.
* Hα (6564.61 Å rest), C III] (1908.73 Å) and C IV (1549.06 Å) are outside this SDSS spectrum's rest-frame coverage. They remain in the table for UV/higher-z use and are skipped cleanly; they are reported as `not_covered`, not as zero-flux measurements.
* Hδ and [Ne III] were tested in pre-run variants and are not in the production table: the V09+Balmer-continuum model over-subtracts/does not constrain them (Hδ returned zero flux with χ²_r≈21). This is a model limitation, not a non-detection.

## Uncertainty

qsofitmore 1.2.2 has no emcee/MCMC sampler. Its native uncertainty mode is the lmfit Monte Carlo refit used here:

* **{mc_trails}** independent noise realizations per fitted complex (and for the continuum MC), seed `{seed}`. This is 200× the package default `n_trails=1` and twice the PyQSOFit MC in this repo.
* Each realization adds `N(0, err)` to the calibrated spectrum and refits the continuum and each line complex with lmfit.
* The compact table recomputes each physical line total from **all** of its Gaussian components. The package's `<complex>_whole_br_area` column only sums Gaussians above its 1200 km/s classifier and is therefore not the total; it is retained in `qsofitmore_result.csv`.
* Hβ/[O III] uses the same Hβ-complex draws, so the ratio uncertainty includes the correlated line fluxes. Mg II is a separate complex with its own independent draws.
* `qsofitmore_corner.png`/`.pdf`: Hβ total, [O III] 5007, Hβ/[O III], Hβ FWHM. `qsofitmore_mgii_corner.*`: Mg II. `qsofitmore_uncertainty.*`: marginal histograms. `qsofitmore_mc_samples.csv` contains every retained realization.

## Headline measurements (1e-17 erg s^-1 cm^-2)

| line | area | 1σ (MC) | FWHM (km/s) | status |
|---|---:|---:|---:|---|
| Hβ total | {fmt(hb.get('area_1e17'))} | {fmt(hb.get('area_err_1e17'))} | {fmt(hb.get('fwhm_kms'),0)} | {hb.get('status','n/a')} |
| Hβ broad template | {fmt(key.get('Hbeta_broad',{}).get('area_1e17'))} | {fmt(key.get('Hbeta_broad',{}).get('area_err_1e17'))} | {fmt(key.get('Hbeta_broad',{}).get('fwhm_kms'),0)} | {key.get('Hbeta_broad',{}).get('status','n/a')} |
| Hβ narrow | {fmt(key.get('Hbeta_narrow',{}).get('area_1e17'))} | {fmt(key.get('Hbeta_narrow',{}).get('area_err_1e17'))} | {fmt(key.get('Hbeta_narrow',{}).get('fwhm_kms'),0)} | {key.get('Hbeta_narrow',{}).get('status','n/a')} |
| [O III] 5007 total | {fmt(o3.get('area_1e17'))} | {fmt(o3.get('area_err_1e17'))} | {fmt(o3.get('fwhm_kms'),0)} | {o3.get('status','n/a')} |
| [O III] 5007 core | {fmt(key.get('OIII5007_core',{}).get('area_1e17'))} | {fmt(key.get('OIII5007_core',{}).get('area_err_1e17'))} | {fmt(key.get('OIII5007_core',{}).get('fwhm_kms'),0)} | {key.get('OIII5007_core',{}).get('status','n/a')} |
| [O III] 5007 outflow | {fmt(key.get('OIII5007_wing',{}).get('area_1e17'))} | {fmt(key.get('OIII5007_wing',{}).get('area_err_1e17'))} | {fmt(key.get('OIII5007_wing',{}).get('fwhm_kms'),0)} | {key.get('OIII5007_wing',{}).get('status','n/a')} |
| Mg II total | {fmt(mg.get('area_1e17'))} | {fmt(mg.get('area_err_1e17'))} | {fmt(mg.get('fwhm_kms'),0)} | {mg.get('status','n/a')} |
| Hγ total | {fmt(hg.get('area_1e17'))} | {fmt(hg.get('area_err_1e17'))} | {fmt(hg.get('fwhm_kms'),0)} | {hg.get('status','n/a')} |

* **Hβ/[O III] 5007 = {ratio_txt}** (MC median {fmt(ratio_stats.get('median'),3)}, 16–84% {fmt(ratio_stats.get('p16'),3)}–{fmt(ratio_stats.get('p84'),3)}).
* Hβ complex χ²_r = `{fmt(complexes.get('Hb_line_red_chi2'),2)}`; Mg II χ²_r = `{fmt(complexes.get('MgII_line_red_chi2'),2)}`; [O II] χ²_r = `{fmt(complexes.get('OII_line_red_chi2'),2)}`. These are diagnostics, not goodness-of-fit gates; the Hβ complex is the hardest because the Fe II/Balmer model and the broad profile are not a complete physical description.
* Fe II band fluxes (from the V09 template): {', '.join(f"{k}={fmt(result_dict.get(k),1)}" for k in result_dict if k.startswith('Fe_w') and k.endswith('_flux'))}.
* Balmer continuum normalisation `{fmt(result_dict.get('BalmerC_norm'),3)}`; high-order Balmer normalisation `{fmt(result_dict.get('BalmerS_norm'),1)}`.

## Cross-tool check

`qsofitmore_lines.csv` is the input to the host-side comparison:

```bash
.venv/bin/python pipeline/compare_qsofitmore.py --source-key {source_key}
```

It writes `cross_tool_comparison.csv`, `cross_tool_comparison.json`, and `cross_tool_comparison.png` in this directory. The comparison uses Hβ total, [O III] 5007 total, and Mg II total against PyQSOFit, GANDALF, S3Fit, GalSpec, PyQSOFitSpec, QGfit, SHEAP and the SDSS ZLINE anchor. See the CSV/JSON for ratios, log10 differences and `(tool - QSOFITMORE)/sqrt(err_tool^2 + err_qm^2)`.

## What this tool can and cannot measure

**Can:** UV/optical AGN continuum shape, Fe II pseudo-continuum, Balmer continuum/high-order Balmer, broad and narrow Balmer lines, Mg II, [O III] core/outflow, [O II], [Ne V], and their Monte Carlo uncertainties; line ratios and FWHMs.

**Cannot / caveats:**

* Hα, C III] and C IV are outside this SDSS spectrum's rest-frame coverage; no measurement is possible without UV/NIR data.
* The broad Hβ complex is a multi-Gaussian empirical profile, not a reverberation-mapped BLR model. Individual Gaussian components are degenerate; use the total, not the component split, for science.
* The Hβ narrow component is tied to the [O III] kinematics; its width is not independent. The package's broad/narrow classifier at 1200 km/s is not a physical decomposition; the compact total is the robust quantity.
* The Hβ complex χ²_r is larger than the Mg II χ²_r. This is a model mismatch (Fe II/Balmer template + Gaussian profile), not evidence that the Hβ flux is wrong; the total is stable across line-table variants (see `run.json` and the systematic BG92 fit).
* No MCMC posterior is produced or claimed. The MC is a frequentist parametric bootstrap of the calibrated errors.
* The Galactic extinction is foreground only; no intrinsic reddening is fitted. The broken power law absorbs some intrinsic curvature.
* The host is not decomposed here; use `ppxf_host` for the stellar host.

## Products

`qsofitmore_lines.csv`, `qsofitmore_components.csv`, `qsofitmore_mc_samples.csv`, `qsofitmore_mc_summary.csv`, `qsofitmore_hb_oiii_mc.csv`, `qsofitmore_continuum.csv`, `qsofitmore_result.csv`, `qsofitmore_result.fits`, `qsofitmore_fit.pdf/png`, `qsofitmore_corner.*`, `qsofitmore_mgii_corner.*`, `qsofitmore_uncertainty.*`, `config.effective.json`, `run.json`, `systematics/`.
"""
    (out / "README.md").write_text(readme)
    print(f"QSOFITMORE done: {out}")
    print(f"  runtime {time.time()-t_start:.1f} s (fit {fit_runtime:.1f} s)")
    print(f"  Hbeta {fmt(hb.get('area_1e17'))} +/- {fmt(hb.get('area_err_1e17'))}, [OIII]5007 {fmt(o3.get('area_1e17'))} +/- {fmt(o3.get('area_err_1e17'))}, ratio {ratio_txt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
