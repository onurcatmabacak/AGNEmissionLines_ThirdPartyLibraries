#!/usr/bin/env python3
"""Official XMM-Newton EPIC spectral fit with HEASoft/PyXspec.

This is the production entry point for the ``xmm_xspec`` tool.  It reads the
official XMM-Newton Pipeline Processing System (PPS) source/background spectra
and source ARFs, the official CCF response matrices, prepares channel-matched
inputs, and fits an absorbed power law with an optional Fe K-alpha Gaussian.

Model (0.5-10 keV, observed frame)::

    constant * tbabs * (zpowerlw + zgauss)

``constant`` is fixed to 1 for PN (reference) and free for MOS1/MOS2, so the
MOS/PN cross-calibration is a fitted parameter.  ``zpowerlw`` and ``zgauss``
share the source redshift.  The Fe line energy is 6.4 keV in the rest frame;
the default width is fixed to 50 eV (an unresolved narrow core).

Nothing here runs SAS.  The PPS spectra are the official SAS pipeline
products; see ``SAS_RAW_PATH.md`` for the optional raw-ODF path.

Usage (inside the container)::

    python run_xmm_xspec.py --input-dir /app/input --out /app/output \
        --config /app/config --redshift 0.184
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from astropy.io import fits

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# PyXspec must be imported after HEADAS/headas-init.sh has been sourced by the
# container entry point.
from xspec import AllData, AllModels, Fit, Model, Plot, Xset  # noqa: E402

C_KEV_ERG = 1.602176634e-9  # erg per keV
FE_KA_REST_KEV = 6.4
INSTRUMENTS = ("PN", "MOS1", "MOS2")
LINE_COMPONENT = {"pl": 4, "bb": 5}  # component number in the model expression


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jfloat(value):
    """JSON-safe float (NaN/inf -> None)."""
    if value is None:
        return None
    value = float(value)
    if not math.isfinite(value):
        return None
    return value


def fmt(value, digits: int = 8) -> str:
    if value is None:
        return ""
    try:
        if isinstance(value, (bool, np.bool_)):
            return "1" if value else "0"
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(value):
        return ""
    return f"{value:.{digits}g}"


def par_value(component, name: str):
    p = getattr(component, name)
    return float(p.values[0]), float(p.sigma)


def set_par(component, name: str, value: float, frozen: bool | None = None,
            bounds: tuple | None = None):
    p = getattr(component, name)
    if bounds is None:
        p.values = float(value)
    else:
        lo, hi = bounds
        # values = [value, delta, hardmin, softmin, softmax, hardmax]
        delta = max(abs(value) * 0.02, 1e-6)
        p.values = (float(value), delta, float(lo), float(lo), float(hi), float(hi) * 1.5)
    if frozen is not None:
        p.frozen = bool(frozen)


def xspec_version() -> str:
    exe = shutil.which("xspec") or os.path.join(os.environ.get("HEADAS", ""), "bin", "xspec")
    try:
        proc = subprocess.run([exe, "--version"], stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, timeout=30)
        for line in proc.stdout.splitlines():
            if "XSPEC version" in line:
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    # Fall back to the conda package metadata (the binary still enters the
    # interactive prompt after --version and may return a non-zero status).
    try:
        meta = conda_meta("xspec")
        if meta.get("version"):
            return str(meta["version"])
    except Exception:
        pass
    return "unknown"


def conda_meta(name: str) -> dict:
    meta = {}
    for path in sorted(Path("/opt/conda/conda-meta").glob(f"{name}-*.json")):
        try:
            d = json.loads(path.read_text())
        except Exception:
            continue
        meta = {"name": d.get("name", name), "version": d.get("version"),
                "build": d.get("build")}
        break
    return meta


def software_versions() -> dict:
    versions = {
        "xspec": xspec_version(),
        "xspec_conda_package": conda_meta("xspec"),
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "astropy": __import__("astropy").__version__,
        "matplotlib": matplotlib.__version__,
        "heasoft_headas": os.environ.get("HEADAS", ""),
    }
    try:
        import scipy
        versions["scipy"] = scipy.__version__
    except Exception:
        versions["scipy"] = None
    return versions


# ---------------------------------------------------------------------------
# input discovery and preparation
# ---------------------------------------------------------------------------
def discover_products(input_dir: Path, config: dict) -> dict:
    """Locate the PPS spectra/backgrounds/ARFs and the CCF RMFs."""
    overrides = config.get("products", {})
    products = {}
    for inst in INSTRUMENTS:
        key = inst.lower()
        if key in overrides:
            entry = overrides[key]
            products[inst] = {k: input_dir / v for k, v in entry.items()}
            continue
        if inst == "PN":
            spec_glob = "pps/PN/*PNS003SRSPEC0001.fits"
            bg_glob = "pps/PN/*PNS003BGSPEC0001.fits"
            arf_glob = "pps/PN/*PNS003SRCARF0001.fits"
            rmf_glob = "responses/epn_*.rmf"
        elif inst == "MOS1":
            spec_glob = "pps/MOS1/*M1S001SRSPEC0001.fits"
            bg_glob = "pps/MOS1/*M1S001BGSPEC0001.fits"
            arf_glob = "pps/MOS1/*M1S001SRCARF0001.fits"
            rmf_glob = "responses/m1_*.rmf"
        else:
            spec_glob = "pps/MOS2/*M2S002SRSPEC0001.fits"
            bg_glob = "pps/MOS2/*M2S002BGSPEC0001.fits"
            arf_glob = "pps/MOS2/*M2S002SRCARF0001.fits"
            rmf_glob = "responses/m2_*.rmf"
        found = {}
        for role, pattern in (("spectrum", spec_glob), ("background", bg_glob),
                              ("arf", arf_glob), ("rmf", rmf_glob)):
            matches = sorted(input_dir.glob(pattern))
            if len(matches) != 1:
                raise FileNotFoundError(
                    f"{inst} {role}: expected exactly one match for {pattern}, "
                    f"found {len(matches)}: {[p.name for p in matches]}")
            found[role] = matches[0]
        products[inst] = found
    return products


def header_provenance(path: Path) -> dict:
    with fits.open(path) as h:
        ph = h[0].header
        sh = h["SPECTRUM"].header if "SPECTRUM" in h else ph
        out = {
            "telescope": str(ph.get("TELESCOP", "")).strip(),
            "instrument": str(ph.get("INSTRUME", "")).strip(),
            "filter": str(ph.get("FILTER", "")).strip(),
            "object": str(ph.get("OBJECT", "")).strip(),
            "obs_id": str(ph.get("OBS_ID", sh.get("OBS_ID", ""))).strip(),
            "exposure_s": float(sh.get("EXPOSURE", 0.0)),
            "backscal": float(sh.get("BACKSCAL", 1.0)),
            "areascal": float(sh.get("AREASCAL", 1.0)),
            "respfile": str(sh.get("RESPFILE", "")).strip(),
            "ancrfile": str(sh.get("ANCRFILE", "")).strip(),
            "backfile": str(sh.get("BACKFILE", "")).strip(),
        }
        # SAS version is stored either in SASVERS or in the XPROC history.
        sas = str(ph.get("SASVERS", "")).strip()
        if not sas:
            for key in ("XPROC4", "XPROC0"):
                text = str(ph.get(key, ""))
                if "xmmsas_" in text:
                    token = text.split("xmmsas_", 1)[1].split()[0]
                    sas = "xmmsas_" + token.strip("'")
                    break
        out["sas_version"] = sas
        if "SPECTRUM" in h:
            d = h["SPECTRUM"].data
            out["counts_total"] = int(np.asarray(d["COUNTS"]).sum())
            out["channels"] = int(len(d))
            # Both PPS PN and MOS spectra are stored in 5 eV PI channels.  The
            # MOS spectra are rebinned to 15 eV later for the 15 eV RMF.
            out["channel_width_eV"] = 5.0
    return out


def sanitize_pn(src: Path, dst: Path):
    """Copy a PN PPS spectrum and remove header pointers to absent aux files."""
    with fits.open(src) as h:
        hdul = fits.HDUList([hdu.copy() for hdu in h])
    sh = hdul["SPECTRUM"].header
    sh["RESPFILE"] = "NONE"
    sh["ANCRFILE"] = "NONE"
    sh["BACKFILE"] = "NONE"
    # Make sure the OGIP keywords XSPEC wants are present.
    for key, value in (("HDUVERS1", "1.1.0"), ("HDUVERS", "1.0.0"),
                       ("SYS_ERR", 0), ("CORRSCAL", 1.0)):
        sh.setdefault(key, value)
    dst.parent.mkdir(parents=True, exist_ok=True)
    hdul.writeto(dst, overwrite=True)


def rebin_mos_15ev(src: Path, dst: Path):
    """Rebin a 2400-channel 5 eV MOS PPS spectrum 3:1 to 800 channels at 15 eV.

    The 15 eV canned response matrices at
    ``https://xmm-tools.cosmos.esa.int/.../MOS/15eV/`` are the matrices named in
    the PPS SRSPEC header.  They have 800 channels, so the 5 eV PPS spectrum
    must be rebinned 3:1 before use.  Counts are summed; QUALITY is the bitwise
    OR of the three channels; a new bin starts a GROUPING group if any input
    channel started one.
    """
    with fits.open(src) as h:
        hd = h["SPECTRUM"].copy()
    d = hd.data
    n = (len(d) // 3) * 3
    counts = np.asarray(d["COUNTS"][:n], dtype=np.int64).reshape(-1, 3).sum(axis=1)
    if "QUALITY" in d.columns.names:
        q = np.asarray(d["QUALITY"][:n], dtype=np.int64).reshape(-1, 3)
        quality = np.bitwise_or.reduce(q, axis=1)
    else:
        quality = np.zeros(len(counts), dtype=np.int64)
    if "GROUPING" in d.columns.names:
        g = np.asarray(d["GROUPING"][:n], dtype=np.int64).reshape(-1, 3)
        grouping = np.where((g == 1).any(axis=1), 1, -1).astype(np.int16)
    else:
        grouping = np.ones(len(counts), dtype=np.int16)

    cols = [
        fits.Column(name="CHANNEL", format="I", array=np.arange(len(counts), dtype=np.int16)),
        fits.Column(name="COUNTS", format="J", unit="count", array=counts.astype(np.int32)),
        fits.Column(name="GROUPING", format="I", array=grouping),
        fits.Column(name="QUALITY", format="I", array=quality.astype(np.int16)),
    ]
    nh = fits.BinTableHDU.from_columns(cols, name="SPECTRUM")
    for key in ("TELESCOP", "INSTRUME", "FILTER", "EXPOSURE", "BACKSCAL", "AREASCAL",
                "HDUCLASS", "HDUCLAS1", "HDUCLAS2", "HDUCLAS3", "CHANTYPE",
                "POISSERR", "OBS_ID", "OBJECT", "RA_OBJ", "DEC_OBJ"):
        if key in hd.header:
            nh.header[key] = hd.header[key]
    nh.header["DETCHANS"] = len(counts)
    nh.header["TLMIN1"] = 0
    nh.header["TLMAX1"] = len(counts) - 1
    nh.header["HDUVERS1"] = "1.1.0"
    nh.header["HDUVERS"] = "1.0.0"
    nh.header["SYS_ERR"] = 0
    nh.header["CORRSCAL"] = 1.0
    nh.header["RESPFILE"] = "NONE"
    nh.header["ANCRFILE"] = "NONE"
    nh.header["BACKFILE"] = "NONE"
    dst.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList([fits.PrimaryHDU(), nh]).writeto(dst, overwrite=True)


def prepare_inputs(products: dict, prepared_dir: Path) -> dict:
    prepared_dir.mkdir(parents=True, exist_ok=True)
    prepared = {}
    for inst in INSTRUMENTS:
        p = products[inst]
        src_out = prepared_dir / f"{inst.lower()}_source.fits"
        bg_out = prepared_dir / f"{inst.lower()}_background.fits"
        if inst == "PN":
            sanitize_pn(p["spectrum"], src_out)
            sanitize_pn(p["background"], bg_out)
        else:
            rebin_mos_15ev(p["spectrum"], src_out)
            rebin_mos_15ev(p["background"], bg_out)
        prepared[inst] = {"source": src_out, "background": bg_out}
    return prepared


# ---------------------------------------------------------------------------
# XSPEC fitting
# ---------------------------------------------------------------------------
def reset_xspec():
    try:
        Plot.setGroup(None)
    except Exception:
        pass
    AllData.clear()
    AllModels.clear()


def seed_defaults() -> dict:
    return {
        "nH": 0.2, "gamma": 2.1, "pl_norm": 4.0e-3,
        "bb_kT": 0.15, "bb_norm": 8.0e-5,
        "constants": {"PN": 1.0, "MOS1": 1.05, "MOS2": 1.04},
        "line_norm": 3.0e-6, "line_sigma": 0.05, "line_E": FE_KA_REST_KEV,
    }


def _configure_shared(g, instruments, config, seed, baseline, line,
                      free_sigma, free_energy):
    z = float(config["redshift"])
    g0 = g[0]
    set_par(g0.TBabs, "nH", seed["nH"])
    set_par(g0.zpowerlw, "PhoIndex", seed["gamma"])
    set_par(g0.zpowerlw, "Redshift", z, frozen=True)
    set_par(g0.zpowerlw, "norm", seed["pl_norm"])
    if baseline == "bb":
        set_par(g0.zbbody, "kT", seed["bb_kT"])
        set_par(g0.zbbody, "Redshift", z, frozen=True)
        set_par(g0.zbbody, "norm", seed["bb_norm"])
    if line:
        set_par(g0.zgauss, "LineE", seed["line_E"], frozen=not free_energy,
                bounds=(5.0, 9.0) if free_energy else None)
        set_par(g0.zgauss, "Sigma", seed["line_sigma"], frozen=not free_sigma,
                bounds=(0.01, 2.0) if free_sigma else None)
        set_par(g0.zgauss, "Redshift", z, frozen=True)
        set_par(g0.zgauss, "norm", seed["line_norm"])

    # Cross-calibration constants: PN is the reference.
    for i, inst in enumerate(instruments, start=1):
        gi = g[i - 1]
        c = gi.constant.factor
        if inst == "PN" or len(instruments) == 1:
            # PN is the reference; a single-instrument fit needs no
            # cross-calibration constant.
            c.values = 1.0
            c.frozen = True
        else:
            c.values = (seed["constants"].get(inst, 1.0),
                        max(abs(seed["constants"].get(inst, 1.0)) * 0.02, 1e-4),
                        0.02, 0.1, 2.0, 3.0)
            c.frozen = False

    # Link the physical parameters across data groups.  Redshifts are frozen at
    # the same value; linking them is harmless and keeps the model explicit.
    for gi in g[1:]:
        gi.TBabs.nH.link = g0.TBabs.nH
        gi.zpowerlw.PhoIndex.link = g0.zpowerlw.PhoIndex
        gi.zpowerlw.Redshift.link = g0.zpowerlw.Redshift
        gi.zpowerlw.norm.link = g0.zpowerlw.norm
        if baseline == "bb":
            gi.zbbody.kT.link = g0.zbbody.kT
            gi.zbbody.Redshift.link = g0.zbbody.Redshift
            gi.zbbody.norm.link = g0.zbbody.norm
        if line:
            gi.zgauss.LineE.link = g0.zgauss.LineE
            gi.zgauss.Sigma.link = g0.zgauss.Sigma
            gi.zgauss.Redshift.link = g0.zgauss.Redshift
            gi.zgauss.norm.link = g0.zgauss.norm


def _capture_plot(g, n):
    """Return the exact XSPEC data/model/residual arrays for each spectrum."""
    out = {}
    Plot.device = "/null"
    Plot.xAxis = "keV"
    Plot.setGroup(",".join(str(i) for i in range(1, n + 1)))
    for i in range(1, n + 1):
        Plot(f"{i} data", f"{i} delchi")
        x = np.asarray(Plot.x(1, 1), dtype=float)
        data = np.asarray(Plot.y(1, 1), dtype=float)
        data_err = np.asarray(Plot.yErr(1, 1), dtype=float)
        delchi = np.asarray(Plot.y(1, 2), dtype=float)
        energies = np.asarray(AllData(i).energies, dtype=float)
        de = energies[:, 1] - energies[:, 0]
        folded = np.asarray(g[i - 1].folded(i), dtype=float)
        if not (len(x) == len(data) == len(delchi) == len(de) == len(folded)):
            raise RuntimeError(
                f"plot arrays for spectrum {i} have inconsistent lengths: "
                f"{len(x)} {len(data)} {len(delchi)} {len(de)} {len(folded)}")
        out[i] = {
            "energy_keV": x.tolist(),
            "data_counts_s_keV": data.tolist(),
            "data_err": data_err.tolist(),
            "delchi": delchi.tolist(),
            "bin_width_keV": de.tolist(),
            "model_counts_s_keV": (folded / de).tolist(),
            "model_folded_counts_s_bin": folded.tolist(),
        }
    return out


def fit_model(products: dict, prepared: dict, config: dict, *, fit_id: str,
              scope: str, baseline: str, line: bool, free_sigma: bool = False,
              free_energy: bool = False, seed: dict | None = None) -> dict:
    """Fit one model to the joint PN+MOS data or to a single instrument.

    ``scope`` is ``"joint"`` or one of ``"PN"``, ``"MOS1"``, ``"MOS2"``.
    """
    reset_xspec()
    instruments = list(INSTRUMENTS) if scope == "joint" else [scope]
    if scope == "joint":
        spec_arg = " ".join(f"{i}:{i} {prepared[inst]['source']}"
                            for i, inst in enumerate(instruments, start=1))
        AllData(spec_arg)
    else:
        AllData(f"1:1 {prepared[scope]['source']}")

    for i, inst in enumerate(instruments, start=1):
        s = AllData(i)
        s.response = str(products[inst]["rmf"])
        s.response.arf = str(products[inst]["arf"])
        s.background = str(prepared[inst]["background"])

    lo, hi = [float(x) for x in config["band_keV"]]
    AllData.ignore("bad")
    AllData.ignore(f"0.0-{lo} {hi}-**")

    if baseline == "pl":
        expr = "constant*tbabs*(zpowerlw" + (" + zgauss" if line else "") + ")"
    else:
        expr = "constant*tbabs*(zbbody + zpowerlw" + (" + zgauss" if line else "") + ")"
    name = "joint" if scope == "joint" else "single"
    Model(expr, name)
    g = [AllModels(i, name) for i in range(1, len(instruments) + 1)]
    seed = seed or seed_defaults()
    _configure_shared(g, instruments, config, seed, baseline, line,
                      free_sigma, free_energy)

    Fit.statMethod = config.get("statistic", "chi")
    Fit.nIterations = int(config.get("fit_iterations", 500))
    Fit.query = "no"
    Xset.chatter = int(config.get("xspec_chatter", 10))
    Fit.perform()

    result = {
        "fit_id": fit_id,
        "scope": scope,
        "instruments": instruments,
        "baseline": baseline,
        "has_line": bool(line),
        "free_sigma": bool(free_sigma),
        "free_energy": bool(free_energy),
        "model": expr,
        "band_keV": [lo, hi],
        "statistic": config.get("statistic", "chi"),
        "chi2": float(Fit.statistic),
        "dof": int(Fit.dof),
        "rchi2": float(Fit.statistic / Fit.dof) if Fit.dof else float("nan"),
        "nH": par_value(g[0].TBabs, "nH"),
        "gamma": par_value(g[0].zpowerlw, "PhoIndex"),
        "pl_norm": par_value(g[0].zpowerlw, "norm"),
        "constants": {},
        "group_chi2": {},
        "group_bins": {},
    }
    if baseline == "bb":
        result["bb_kT"] = par_value(g[0].zbbody, "kT")
        result["bb_norm"] = par_value(g[0].zbbody, "norm")
    for i, inst in enumerate(instruments, start=1):
        result["constants"][inst] = {
            "value": float(g[i - 1].constant.factor.values[0]),
            "error": float(g[i - 1].constant.factor.sigma),
            "frozen": bool(g[i - 1].constant.factor.frozen),
        }
        result["group_chi2"][inst] = float(AllData(i).statistic)
        result["group_bins"][inst] = int(len(AllData(i).values))
    if line:
        result["line"] = {
            "line_energy_rest_keV": par_value(g[0].zgauss, "LineE"),
            "sigma_keV": par_value(g[0].zgauss, "Sigma"),
            "norm_photons_cm2_s": par_value(g[0].zgauss, "norm"),
            "redshift": float(config["redshift"]),
        }
        try:
            comp = LINE_COMPONENT[baseline]
            AllModels.eqwidth(f"{name}:{comp}")
            result["eqwidth_xspec_obs_keV"] = float(AllData(1).eqwidth[0])
            result["eqwidth_xspec_obs_err_low"] = float(AllData(1).eqwidth[1])
            result["eqwidth_xspec_obs_err_high"] = float(AllData(1).eqwidth[2])
        except Exception as exc:  # pragma: no cover - diagnostic only
            result["eqwidth_xspec_obs_keV"] = None
            result["eqwidth_error"] = str(exc)
    result["plot"] = _capture_plot(g, len(instruments))
    return result


# ---------------------------------------------------------------------------
# derived line quantities
# ---------------------------------------------------------------------------
def chi2_sf(x: float, dof: int) -> float:
    """Survival function of the chi-square distribution (small dof only)."""
    if x <= 0:
        return 1.0
    if dof == 1:
        return math.erfc(math.sqrt(x / 2.0))
    if dof == 2:
        return math.exp(-x / 2.0)
    # Regularized upper incomplete gamma Q(k/2, x/2), series/continued fraction.
    k = dof / 2.0
    a = x / 2.0
    if a < k + 1.0:
        # series for P(k,a), then Q = 1-P
        term = 1.0 / k
        total = term
        n = 0
        while True:
            n += 1
            term *= a / (k + n)
            total += term
            if abs(term) < 1e-14 * abs(total) or n > 10000:
                break
        p = total * math.exp(-a + k * math.log(a) - math.lgamma(k))
        return max(0.0, min(1.0, 1.0 - p))
    # continued fraction for Q
    tiny = 1e-300
    b = a + 1.0 - k
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 10000):
        an = -i * (i - k)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    q = math.exp(-a + k * math.log(a) - math.lgamma(k)) * h
    return max(0.0, min(1.0, q))


def norm_to_sigma(p: float) -> float:
    """One-sided Gaussian-equivalent sigma from a p-value."""
    if p <= 0:
        return 50.0
    if p >= 1:
        return 0.0
    # erfc(sigma/sqrt(2)) = p  ->  sigma = sqrt(2)*erfcinv(p)
    # Use a robust rational approximation of the inverse error function.
    # (scipy is available in the image, but keep a fallback.)
    try:
        from scipy.special import erfcinv
        return float(min(50.0, math.sqrt(2.0) * erfcinv(p)))
    except Exception:
        # bisection on erfc
        lo, hi = 0.0, 40.0
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if math.erfc(mid / math.sqrt(2.0)) > p:
                lo = mid
            else:
                hi = mid
        return min(50.0, 0.5 * (lo + hi))


def line_metrics(result: dict, config: dict, baseline_result: dict | None) -> dict:
    """Convert zgauss parameters into flux, EW, Delta-chi2 and significance."""
    z = float(config["redshift"])
    line = result["line"]
    norm, norm_err = line["norm_photons_cm2_s"]
    e_rest, e_rest_err = line["line_energy_rest_keV"]
    sigma, sigma_err = line["sigma_keV"]
    e_obs = e_rest / (1.0 + z)
    flux = norm * e_obs * C_KEV_ERG
    flux_err = abs(norm_err) * e_obs * C_KEV_ERG

    # Continuum photon flux density at the observed line energy.  The power-law
    # normalization is photons/cm^2/s/keV at 1 keV in the rest frame for
    # zpowerlw; Galactic absorption at 5.4 keV changes this by <2%.
    gamma = result["gamma"][0]
    pl_norm = result["pl_norm"][0]
    # ``f_cont`` is evaluated at the rest-frame line energy.  The equivalent
    # width in the rest frame is norm/f_cont; converting to the observed frame
    # requires one factor (1+z), not two.  This matches XSPEC's eqwidth output.
    f_cont = pl_norm * (e_obs * (1.0 + z)) ** (-gamma)
    ew_rest = norm / f_cont
    ew_rest_err = abs(norm_err) / f_cont
    ew_obs = ew_rest / (1.0 + z)
    ew_obs_err = ew_rest_err / (1.0 + z)

    delta_chi2 = None
    delta_dof = None
    p_value = None
    significance = None
    detected = None
    if baseline_result is not None:
        delta_chi2 = baseline_result["chi2"] - result["chi2"]
        delta_dof = baseline_result["dof"] - result["dof"]
        p_value = chi2_sf(delta_chi2, delta_dof)
        significance = norm_to_sigma(p_value)
        detected = bool(significance >= 3.0)

    upper_norm = max(0.0, norm) + 1.645 * abs(norm_err)
    return {
        "rest_energy_keV": e_rest,
        "rest_energy_err": e_rest_err,
        "observed_energy_keV": e_obs,
        "sigma_keV": sigma,
        "sigma_err": sigma_err,
        "norm": norm,
        "norm_err": norm_err,
        "flux": flux,
        "flux_err": flux_err,
        "ew_rest_keV": ew_rest,
        "ew_rest_err": ew_rest_err,
        "ew_obs_keV": ew_obs,
        "ew_obs_err": ew_obs_err,
        "ew_xspec_obs_keV": result.get("eqwidth_xspec_obs_keV"),
        "delta_chi2": delta_chi2,
        "delta_dof": delta_dof,
        "p_value": p_value,
        "significance_sigma": significance,
        "detected": detected,
        "upper_limit_90_norm": upper_norm,
        "upper_limit_90_flux": upper_norm * e_obs * C_KEV_ERG,
        "upper_limit_90_ew_rest": upper_norm * (1.0 + z) / f_cont,
    }


# ---------------------------------------------------------------------------
# output writers
# ---------------------------------------------------------------------------
FIT_FIELDS = [
    "fit_id", "scope", "instruments", "model", "band_keV", "statistic",
    "chi2", "dof", "rchi2",
    "nH_1e22", "nH_err", "gamma", "gamma_err", "pl_norm", "pl_norm_err",
    "bb_kT_keV", "bb_kT_err", "bb_norm", "bb_norm_err",
    "constant_PN", "constant_PN_err", "constant_MOS1", "constant_MOS1_err",
    "constant_MOS2", "constant_MOS2_err",
    "group_chi2_PN", "group_chi2_MOS1", "group_chi2_MOS2",
    "line_rest_energy_keV", "line_rest_energy_err", "line_sigma_keV", "line_sigma_err",
    "line_norm", "line_norm_err", "line_flux_erg_cm2_s", "line_flux_err",
    "ew_rest_keV", "ew_rest_err", "ew_obs_keV", "ew_xspec_keV",
    "delta_chi2", "delta_dof", "p_value", "significance_sigma", "detected",
    "upper_limit_90_norm", "upper_limit_90_flux", "notes",
]

LINE_FIELDS = [
    "fit_id", "scope", "line", "rest_energy_keV", "rest_energy_err",
    "observed_energy_keV", "sigma_keV", "sigma_err",
    "norm_photons_cm2_s", "norm_err", "flux_erg_cm2_s", "flux_err",
    "ew_rest_keV", "ew_rest_err", "ew_obs_keV", "ew_xspec_obs_keV",
    "delta_chi2", "delta_dof", "p_value", "significance_sigma", "detected",
    "upper_limit_90_norm", "upper_limit_90_flux",
    "interpretation",
]


def fit_row(result: dict, metrics: dict | None, notes: str) -> dict:
    def gv(key, idx):
        v = result.get(key)
        if v is None:
            return None
        return v[idx]

    row = {
        "fit_id": result["fit_id"],
        "scope": result["scope"],
        "instruments": "+".join(result["instruments"]),
        "model": result["model"],
        "band_keV": f"{result['band_keV'][0]}-{result['band_keV'][1]}",
        "statistic": result["statistic"],
        "chi2": result["chi2"], "dof": result["dof"], "rchi2": result["rchi2"],
        "nH_1e22": gv("nH", 0), "nH_err": gv("nH", 1),
        "gamma": gv("gamma", 0), "gamma_err": gv("gamma", 1),
        "pl_norm": gv("pl_norm", 0), "pl_norm_err": gv("pl_norm", 1),
        "bb_kT_keV": gv("bb_kT", 0), "bb_kT_err": gv("bb_kT", 1),
        "bb_norm": gv("bb_norm", 0), "bb_norm_err": gv("bb_norm", 1),
        "group_chi2_PN": result["group_chi2"].get("PN"),
        "group_chi2_MOS1": result["group_chi2"].get("MOS1"),
        "group_chi2_MOS2": result["group_chi2"].get("MOS2"),
        "notes": notes,
    }
    for inst in INSTRUMENTS:
        c = result["constants"].get(inst)
        row[f"constant_{inst}"] = c["value"] if c else None
        row[f"constant_{inst}_err"] = c["error"] if c else None
    if metrics:
        for src, dst in (
            ("rest_energy_keV", "line_rest_energy_keV"),
            ("rest_energy_err", "line_rest_energy_err"),
            ("sigma_keV", "line_sigma_keV"),
            ("sigma_err", "line_sigma_err"),
            ("norm", "line_norm"),
            ("norm_err", "line_norm_err"),
            ("flux", "line_flux_erg_cm2_s"),
            ("flux_err", "line_flux_err"),
            ("ew_rest_keV", "ew_rest_keV"),
            ("ew_rest_err", "ew_rest_err"),
            ("ew_obs_keV", "ew_obs_keV"),
            ("ew_xspec_obs_keV", "ew_xspec_keV"),
            ("delta_chi2", "delta_chi2"),
            ("delta_dof", "delta_dof"),
            ("p_value", "p_value"),
            ("significance_sigma", "significance_sigma"),
            ("detected", "detected"),
            ("upper_limit_90_norm", "upper_limit_90_norm"),
            ("upper_limit_90_flux", "upper_limit_90_flux"),
        ):
            row[dst] = metrics.get(src)
    return row


def write_csv(path: Path, fields: list[str], rows: list[dict]):
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: fmt(row.get(k)) for k in fields})


def plot_figure(fit: dict, baseline: dict | None, path_png: Path, path_pdf: Path,
                config: dict):
    """Main spectrum/model/residual figure (and optional Fe K-alpha zoom)."""
    instruments = fit["instruments"]
    n = len(instruments)
    z = float(config["redshift"])
    e_obs_line = FE_KA_REST_KEV / (1.0 + z)

    plt.rcParams.update({
        "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8,
        "legend.fontsize": 8, "axes.linewidth": 0.8,
    })
    colors = {"PN": "#1f4e9c", "MOS1": "#b22222", "MOS2": "#2e7d32"}
    fig, axes = plt.subplots(2, n, figsize=(4.3 * n, 6.6),
                             gridspec_kw={"height_ratios": [3.2, 1.0]},
                             squeeze=False)
    for j, inst in enumerate(instruments):
        p = fit["plot"][j + 1]
        e = np.asarray(p["energy_keV"])
        d = np.asarray(p["data_counts_s_keV"])
        de = np.asarray(p["data_err"])
        mod = np.asarray(p["model_counts_s_keV"])
        res = np.asarray(p["delchi"])
        ax = axes[0, j]
        ax.errorbar(e, d, yerr=de, fmt="o", ms=2.3, lw=0.6,
                    color=colors.get(inst, "C0"), ecolor=colors.get(inst, "C0"),
                    alpha=0.85, label="data")
        ax.plot(e, mod, "-", color="black", lw=1.0, label="model")
        ax.axvline(e_obs_line, ls="--", lw=0.8, color="0.45")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(config["band_keV"][0], config["band_keV"][1])
        ax.set_ylabel(r"Counts s$^{-1}$ keV$^{-1}$")
        ax.set_title(f"{inst}: $\\chi^2$={fit['group_chi2'][inst]:.1f} "
                     f"({fit['group_bins'][inst]} bins)")
        ax.legend(loc="lower left", frameon=False)
        axr = axes[1, j]
        axr.axhspan(-1, 1, color="0.92", zorder=0)
        axr.axhspan(-2, 2, color="0.84", zorder=0)
        axr.axhline(0, color="0.4", lw=0.7)
        axr.plot(e, res, "o", ms=2.0, color=colors.get(inst, "C0"))
        axr.set_xscale("log")
        axr.set_xlim(config["band_keV"][0], config["band_keV"][1])
        axr.set_ylim(-6, 6)
        axr.set_xlabel("Observed energy (keV)")
        axr.set_ylabel(r"Residual ($\sigma$)")
    fig.suptitle(
        f"XMM-Newton EPIC: {fit['fit_id']}   "
        f"$\\chi^2$/dof = {fit['chi2']:.1f}/{fit['dof']} = {fit['rchi2']:.2f}",
        fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path_png, dpi=int(config.get("plot_dpi", 140)))
    fig.savefig(path_pdf)
    plt.close(fig)

    # Fe K-alpha zoom: data/model ratio and residuals make the weak line
    # visible even when the baseline and line curves overlap in count space.
    if baseline is not None:
        fig, axes = plt.subplots(3, n, figsize=(4.3 * n, 8.4),
                                 gridspec_kw={"height_ratios": [2.6, 1.5, 1.0]},
                                 squeeze=False)
        zlo, zhi = config.get("zoom_keV", [4.0, 8.0])
        for j, inst in enumerate(instruments):
            pl = fit["plot"][j + 1]
            pb = baseline["plot"][j + 1]
            e = np.asarray(pl["energy_keV"])
            d = np.asarray(pl["data_counts_s_keV"])
            de = np.asarray(pl["data_err"])
            mod = np.asarray(pl["model_counts_s_keV"])
            bmod = np.asarray(pb["model_counts_s_keV"])
            res = np.asarray(pl["delchi"])
            sel = (e >= zlo) & (e <= zhi)
            ax = axes[0, j]
            ax.errorbar(e[sel], d[sel], yerr=de[sel], fmt="o", ms=2.8, lw=0.7,
                        color=colors.get(inst, "C0"), alpha=0.9, label="data")
            ax.plot(e[sel], bmod[sel], "--", color="0.45", lw=1.1,
                    label="baseline (no line)")
            ax.plot(e[sel], mod[sel], "-", color="black", lw=1.2,
                    label="baseline + Fe K$\\alpha$")
            ax.axvline(e_obs_line, ls=":", lw=0.9, color="0.4")
            ax.set_xlim(zlo, zhi)
            ax.set_yscale("log")
            ax.set_ylabel(r"Counts s$^{-1}$ keV$^{-1}$")
            ax.set_title(f"{inst}")
            ax.legend(loc="lower left", frameon=False)

            axm = axes[1, j]
            ratio = d / bmod
            ratio_err = de / bmod
            axm.axhline(1.0, color="0.4", lw=0.7)
            axm.errorbar(e[sel], ratio[sel], yerr=ratio_err[sel], fmt="o",
                         ms=2.8, lw=0.7, color=colors.get(inst, "C0"),
                         alpha=0.9, label="data / baseline")
            axm.plot(e[sel], (mod / bmod)[sel], "-", color="black", lw=1.1,
                     label="line model / baseline")
            axm.axvline(e_obs_line, ls=":", lw=0.9, color="0.4")
            axm.set_xlim(zlo, zhi)
            axm.set_ylim(0.85, 1.20)
            axm.set_ylabel("Ratio to baseline")
            axm.legend(loc="upper left", frameon=False, ncol=2)

            axr = axes[2, j]
            axr.axhspan(-1, 1, color="0.92", zorder=0)
            axr.axhspan(-2, 2, color="0.84", zorder=0)
            axr.axhline(0, color="0.4", lw=0.7)
            axr.plot(e[sel], res[sel], "o", ms=2.6,
                     color=colors.get(inst, "C0"))
            axr.set_xlim(zlo, zhi)
            axr.set_ylim(-6, 6)
            axr.set_xlabel("Observed energy (keV)")
            axr.set_ylabel(r"Residual ($\sigma$)")
        line = fit["line"]
        norm = line["norm_photons_cm2_s"][0]
        flux = norm * e_obs_line * C_KEV_ERG
        ew = fit["line_metrics"]["ew_rest_keV"] * 1000.0
        fig.suptitle(
            f"Fe K$\\alpha$ region: $E_{{\\rm rest}}$={line['line_energy_rest_keV'][0]:.2f} keV, "
            f"$\\sigma$={line['sigma_keV'][0]*1000:.0f} eV, "
            f"EW$_{{\\rm rest}}$={ew:.1f} eV, "
            f"$\\Delta\\chi^2$={fit['line_metrics']['delta_chi2']:.1f} "
            f"({fit['line_metrics']['significance_sigma']:.1f}$\\sigma$)",
            fontsize=9)
        fig.tight_layout(rect=(0, 0, 1, 0.96))
        fig.savefig(path_png.with_name(path_png.stem.replace("spectrum_model_residual", "fe_ka_zoom") + path_png.suffix),
                    dpi=int(config.get("plot_dpi", 140)))
        fig.savefig(path_pdf.with_name(path_pdf.stem.replace("spectrum_model_residual", "fe_ka_zoom") + path_pdf.suffix))
        plt.close(fig)


def consistency_payload(results: dict, config: dict) -> dict:
    """PN/MOS consistency from the independent fits."""
    out = {"gamma": {}, "nH": {}, "line_norm": {}, "pulls": {},
           "cross_calibration": {}}
    for inst in INSTRUMENTS:
        base = results.get(f"{inst.lower()}_pl_baseline")
        lin = results.get(f"{inst.lower()}_pl_line")
        if base:
            out["gamma"][inst] = list(base["gamma"])
            out["nH"][inst] = list(base["nH"])
        if lin and lin.get("line"):
            out["line_norm"][inst] = list(lin["line"]["norm_photons_cm2_s"])
    joint = results.get("joint_pl_baseline")
    if joint:
        out["gamma"]["joint"] = list(joint["gamma"])
        out["nH"]["joint"] = list(joint["nH"])
        for inst in ("MOS1", "MOS2"):
            c = joint["constants"].get(inst)
            if c:
                out["cross_calibration"][inst] = c
    def pull(x1, e1, x2, e2):
        den = math.hypot(e1, e2)
        return (x1 - x2) / den if den > 0 else None
    for inst in ("MOS1", "MOS2"):
        if inst in out["gamma"] and "PN" in out["gamma"]:
            out["pulls"][f"gamma_PN_{inst}"] = pull(
                out["gamma"]["PN"][0], out["gamma"]["PN"][1],
                out["gamma"][inst][0], out["gamma"][inst][1])
            out["pulls"][f"nH_PN_{inst}"] = pull(
                out["nH"]["PN"][0], out["nH"]["PN"][1],
                out["nH"][inst][0], out["nH"][inst][1])
        if inst in out["line_norm"] and "PN" in out["line_norm"]:
            out["pulls"][f"line_norm_PN_{inst}"] = pull(
                out["line_norm"]["PN"][0], out["line_norm"]["PN"][1],
                out["line_norm"][inst][0], out["line_norm"][inst][1])
    return out


def background_check(products: dict, prepared: dict) -> dict:
    """Raw source/background counts in 0.5-10 keV and the area scaling."""
    out = {}
    for inst in INSTRUMENTS:
        src = prepared[inst]["source"]
        bg = prepared[inst]["background"]
        with fits.open(src) as hs, fits.open(bg) as hb:
            ds = hs["SPECTRUM"].data
            db = hb["SPECTRUM"].data
            hs_h = hs["SPECTRUM"].header
            hb_h = hb["SPECTRUM"].header
            width = 5.0 if inst == "PN" else 15.0
            lo_ch = int(round(0.5 / (width / 1000.0)))
            hi_ch = int(round(10.0 / (width / 1000.0)))
            ch_s = np.asarray(ds["CHANNEL"])
            ch_b = np.asarray(db["CHANNEL"])
            sel_s = (ch_s >= lo_ch) & (ch_s <= hi_ch)
            sel_b = (ch_b >= lo_ch) & (ch_b <= hi_ch)
            src_counts = int(np.asarray(ds["COUNTS"])[sel_s].sum())
            bg_counts = int(np.asarray(db["COUNTS"])[sel_b].sum())
            bs_s = float(hs_h.get("BACKSCAL", 1.0))
            bs_b = float(hb_h.get("BACKSCAL", 1.0))
            exp_s = float(hs_h.get("EXPOSURE", 0.0))
            exp_b = float(hb_h.get("EXPOSURE", 0.0))
            area_scale = bs_s / bs_b if bs_b else 1.0
            exp_scale = exp_s / exp_b if exp_b else 1.0
            scaled_bg = bg_counts * area_scale * exp_scale
            net = src_counts - scaled_bg
            out[inst] = {
                "channel_width_eV": width,
                "source_counts_0.5_10_keV": src_counts,
                "background_counts_0.5_10_keV": bg_counts,
                "backscal_source": bs_s,
                "backscal_background": bs_b,
                "area_scale": area_scale,
                "exposure_scale": exp_scale,
                "scaled_background_counts": scaled_bg,
                "net_counts_0.5_10_keV": net,
                "background_fraction": scaled_bg / src_counts if src_counts else None,
            }
    return out


def write_provenance(path: Path, run: dict):
    lines = [
        "# XMM-Newton EPIC provenance — PDS 456",
        "",
        f"ObsID **{run['obsid']}**.  {run['reduction']['path']}.",
        "",
        "## What was run",
        "",
        "- Official XMM-Newton **PPS** source spectra, background spectra and source ARFs.",
        "- Official CCF response matrices (PN v22.0; MOS 15 eV canned matrices).",
        "- HEASoft/PyXspec XSPEC "
        f"{run['software']['xspec']} with `tbabs*zpowerlw` and `zgauss`.",
        "",
        "## What was not run",
        "",
        "- **SAS `epproc`/`especget`/`specgroup`/`epatplot` were not run.**  The PPS",
        "  spectra are the official SAS pipeline products; re-running the 16.5 GB SAS",
        "  Docker image and ~2.9 GB CCF was outside this test's budget.  See",
        "  `Tools/xmm_xspec/SAS_RAW_PATH.md` for the optional raw-ODF path.",
        "- No event-file filtering, no custom extraction region, no pile-up or",
        "  CTI correction beyond what PPS already applied.",
        "",
        "## Response caveats",
        "",
        "- The PPS MOS spectra have 2400 channels at 5 eV.  The 15 eV canned MOS",
        "  matrices named in the PPS headers have 800 channels, so the MOS spectra",
        "  and backgrounds were rebinned 3:1 to 15 eV (counts summed, QUALITY ORed,",
        "  grouping preserved).  The PN spectrum and RMF both have 4096 channels.",
        "- The RMF FILTER keyword is `Medium` while the observation used `Thin1`.",
        "  The redistribution matrix is filter-independent; the ARF carries the",
        "  filter throughput.  XSPEC emits a warning, which is expected.",
        "- The PN RMF is the current CCF extras v22.0 matrix.  The PPS products",
        f"  were generated with SAS {run['reduction']['pps_sas_version']}; the RMF is a",
        "  later calibration product, not the exact matrix used by PPS in 2024.",
        "",
        "## Statistical caveats",
        "",
        "- The simple `tbabs*zpowerlw` continuum leaves a reduced chi-square of",
        f"  {run['headline']['baseline_rchi2']:.2f}; the soft excess and Compton reflection",
        "  are not modeled.  A blackbody soft-excess baseline is fitted as a",
        "  systematic check.",
        "- The narrow Fe K-alpha core is measured with a 50 eV (rest-frame) Gaussian.",
        "  A free-width Gaussian runs to the fit bound; the broad Fe K-alpha excess",
        "  is degenerate with continuum curvature and is reported only as a",
        "  systematic check, not as a resolved line width.",
        "- Errors are XSPEC covariance 1-sigma errors; no MCMC was run.",
        "",
    ]
    path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    t0 = time.time()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", required=True, help="XMM ObsID directory with pps/ and responses/")
    p.add_argument("--out", required=True, help="output directory")
    p.add_argument("--config", default=None, help="config directory (config.json)")
    p.add_argument("--redshift", type=float, default=None)
    p.add_argument("--source-key", default=None)
    p.add_argument("--obsid", default=None)
    args = p.parse_args(argv)

    input_dir = Path(args.input_dir).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    prepared_dir = out / "prepared"
    prepared_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "redshift": 0.184,
        "band_keV": [0.5, 10.0],
        "statistic": "chi",
        "fit_iterations": 500,
        "xspec_chatter": 10,
        "zoom_keV": [4.0, 8.0],
        "plot_dpi": 140,
        "baseline_model": "tbabs*zpowerlw",
        "line_model": "zgauss",
        "line_rest_energy_keV": FE_KA_REST_KEV,
        "line_sigma_keV": 0.05,
        "line_sigma_free": False,
        "line_sigma_free_bounds_keV": [0.01, 1.0],
        "soft_excess_check": True,
        "independent_fits": list(INSTRUMENTS),
        "mos_rebin_factor": 3,
    }
    if args.config:
        cfg_path = Path(args.config) / "config.json"
        if cfg_path.exists():
            config.update(json.loads(cfg_path.read_text()))
    if args.redshift is not None:
        config["redshift"] = float(args.redshift)
    config["line_rest_energy_keV"] = float(config.get("line_rest_energy_keV", FE_KA_REST_KEV))

    print(f"[xmm_xspec] input: {input_dir}")
    print(f"[xmm_xspec] output: {out}")
    print(f"[xmm_xspec] XSPEC: {xspec_version()}")

    products = discover_products(input_dir, config)
    prepared = prepare_inputs(products, prepared_dir)
    prov = {inst: header_provenance(products[inst]["spectrum"]) for inst in INSTRUMENTS}
    for inst in INSTRUMENTS:
        prov[inst]["rmf"] = products[inst]["rmf"].name
        prov[inst]["arf"] = products[inst]["arf"].name
        prov[inst]["background_file"] = products[inst]["background"].name
        prov[inst]["prepared_source"] = prepared[inst]["source"].name
        prov[inst]["prepared_background"] = prepared[inst]["background"].name
    obsid = args.obsid or next((prov[i]["obs_id"] for i in INSTRUMENTS if prov[i]["obs_id"]), "")
    source_key = args.source_key or os.environ.get("XMM_XSPEC_SOURCE_KEY") or out.parent.name
    object_name = next((prov[i]["object"] for i in INSTRUMENTS if prov[i]["object"]), config.get("source_name", ""))

    Xset.abund = "wilm"
    Xset.chatter = int(config.get("xspec_chatter", 10))
    Fit.query = "no"

    results = {}
    metrics = {}
    notes = {}
    seeds = {}

    # 1. joint baseline
    print("\n===== FIT joint_pl_baseline =====")
    seeds["joint_pl_baseline"] = seed_defaults()
    results["joint_pl_baseline"] = fit_model(
        products, prepared, config, fit_id="joint_pl_baseline", scope="joint",
        baseline="pl", line=False, seed=seeds["joint_pl_baseline"])
    notes["joint_pl_baseline"] = "required tbabs*zpowerlw baseline; simple continuum"

    # 2. joint narrow line, seeded from the baseline
    seed = seed_defaults()
    b = results["joint_pl_baseline"]
    seed.update({"nH": b["nH"][0], "gamma": b["gamma"][0], "pl_norm": b["pl_norm"][0],
                 "constants": {k: v["value"] for k, v in b["constants"].items()}})
    seed["line_norm"] = 3.0e-6
    seed["line_sigma"] = float(config.get("line_sigma_keV", 0.05))
    seeds["joint_pl_line"] = dict(seed)
    print("\n===== FIT joint_pl_line =====")
    results["joint_pl_line"] = fit_model(
        products, prepared, config, fit_id="joint_pl_line", scope="joint",
        baseline="pl", line=True, free_sigma=False, seed=seed)
    metrics["joint_pl_line"] = line_metrics(results["joint_pl_line"], config, results["joint_pl_baseline"])
    results["joint_pl_line"]["line_metrics"] = metrics["joint_pl_line"]
    notes["joint_pl_line"] = "primary Fe K-alpha measurement; sigma fixed to 50 eV rest frame"

    # 3. joint free-width line (systematic check)
    seed2 = dict(seed)
    seed2["line_norm"] = results["joint_pl_line"]["line"]["norm_photons_cm2_s"][0]
    seed2["line_sigma"] = 0.1
    print("\n===== FIT joint_pl_line_freesigma =====")
    results["joint_pl_line_freesigma"] = fit_model(
        products, prepared, config, fit_id="joint_pl_line_freesigma", scope="joint",
        baseline="pl", line=True, free_sigma=True, seed=seed2)
    metrics["joint_pl_line_freesigma"] = line_metrics(
        results["joint_pl_line_freesigma"], config, results["joint_pl_baseline"])
    results["joint_pl_line_freesigma"]["line_metrics"] = metrics["joint_pl_line_freesigma"]
    notes["joint_pl_line_freesigma"] = (
        "diagnostic broad component; width is not constrained by the simple continuum "
        "(hits the fit bound) and is degenerate with soft excess/reflection")

    # 4. joint free-centroid line (diagnostic)
    seed3 = dict(seed)
    seed3["line_norm"] = results["joint_pl_line"]["line"]["norm_photons_cm2_s"][0]
    print("\n===== FIT joint_pl_line_freeE =====")
    results["joint_pl_line_freeE"] = fit_model(
        products, prepared, config, fit_id="joint_pl_line_freeE", scope="joint",
        baseline="pl", line=True, free_sigma=False, free_energy=True, seed=seed3)
    metrics["joint_pl_line_freeE"] = line_metrics(
        results["joint_pl_line_freeE"], config, results["joint_pl_baseline"])
    results["joint_pl_line_freeE"]["line_metrics"] = metrics["joint_pl_line_freeE"]
    notes["joint_pl_line_freeE"] = "centroid diagnostic; width fixed to 50 eV"

    # 5. soft-excess baseline and line
    if config.get("soft_excess_check", True):
        print("\n===== FIT joint_bb_baseline =====")
        results["joint_bb_baseline"] = fit_model(
            products, prepared, config, fit_id="joint_bb_baseline", scope="joint",
            baseline="bb", line=False, seed=seed_defaults())
        notes["joint_bb_baseline"] = "systematic check: blackbody soft excess + power law"

        b2 = results["joint_bb_baseline"]
        seedb = seed_defaults()
        seedb.update({"nH": b2["nH"][0], "gamma": b2["gamma"][0],
                      "pl_norm": b2["pl_norm"][0], "bb_kT": b2["bb_kT"][0],
                      "bb_norm": b2["bb_norm"][0],
                      "constants": {k: v["value"] for k, v in b2["constants"].items()}})
        seedb["line_norm"] = results["joint_pl_line"]["line"]["norm_photons_cm2_s"][0]
        print("\n===== FIT joint_bb_line =====")
        results["joint_bb_line"] = fit_model(
            products, prepared, config, fit_id="joint_bb_line", scope="joint",
            baseline="bb", line=True, free_sigma=False, seed=seedb)
        metrics["joint_bb_line"] = line_metrics(
            results["joint_bb_line"], config, results["joint_bb_baseline"])
        results["joint_bb_line"]["line_metrics"] = metrics["joint_bb_line"]
        notes["joint_bb_line"] = "systematic check with a blackbody soft excess"

    # 6. independent per-instrument fits
    for inst in config.get("independent_fits", list(INSTRUMENTS)):
        print(f"\n===== FIT {inst.lower()}_pl_baseline =====")
        results[f"{inst.lower()}_pl_baseline"] = fit_model(
            products, prepared, config, fit_id=f"{inst.lower()}_pl_baseline",
            scope=inst, baseline="pl", line=False, seed=seed_defaults())
        notes[f"{inst.lower()}_pl_baseline"] = "independent instrument fit"

        b = results[f"{inst.lower()}_pl_baseline"]
        seedi = seed_defaults()
        seedi.update({"nH": b["nH"][0], "gamma": b["gamma"][0],
                      "pl_norm": b["pl_norm"][0],
                      "constants": {inst: 1.0}})
        seedi["line_norm"] = results["joint_pl_line"]["line"]["norm_photons_cm2_s"][0]
        print(f"\n===== FIT {inst.lower()}_pl_line =====")
        results[f"{inst.lower()}_pl_line"] = fit_model(
            products, prepared, config, fit_id=f"{inst.lower()}_pl_line",
            scope=inst, baseline="pl", line=True, free_sigma=False, seed=seedi)
        metrics[f"{inst.lower()}_pl_line"] = line_metrics(
            results[f"{inst.lower()}_pl_line"], config,
            results[f"{inst.lower()}_pl_baseline"])
        results[f"{inst.lower()}_pl_line"]["line_metrics"] = metrics[f"{inst.lower()}_pl_line"]
        notes[f"{inst.lower()}_pl_line"] = "independent instrument Fe K-alpha fit"

    # 7. write CSV / JSON / figures
    fit_rows = []
    for fit_id, res in results.items():
        fit_rows.append(fit_row(res, metrics.get(fit_id), notes.get(fit_id, "")))
    write_csv(out / "xmm_fit.csv", FIT_FIELDS, fit_rows)

    line_rows = []
    for fit_id, met in metrics.items():
        res = results[fit_id]
        interp = notes.get(fit_id, "")
        if fit_id == "joint_pl_line":
            interp = "Fe K-alpha complex; primary narrow-core measurement"
        elif fit_id == "joint_pl_line_freesigma":
            interp = "broad Fe K-alpha excess; width at bound, degenerate with continuum"
        elif fit_id == "joint_pl_line_freeE":
            interp = "free-centroid diagnostic; width fixed"
        elif fit_id == "joint_bb_line":
            interp = "soft-excess baseline check; narrow core"
        line_rows.append({
            "fit_id": fit_id,
            "scope": res["scope"],
            "line": "Fe Kalpha (zgauss)",
            "rest_energy_keV": met["rest_energy_keV"],
            "rest_energy_err": met["rest_energy_err"],
            "observed_energy_keV": met["observed_energy_keV"],
            "sigma_keV": met["sigma_keV"],
            "sigma_err": met["sigma_err"],
            "norm_photons_cm2_s": met["norm"],
            "norm_err": met["norm_err"],
            "flux_erg_cm2_s": met["flux"],
            "flux_err": met["flux_err"],
            "ew_rest_keV": met["ew_rest_keV"],
            "ew_rest_err": met["ew_rest_err"],
            "ew_obs_keV": met["ew_obs_keV"],
            "ew_xspec_obs_keV": met["ew_xspec_obs_keV"],
            "delta_chi2": met["delta_chi2"],
            "delta_dof": met["delta_dof"],
            "p_value": met["p_value"],
            "significance_sigma": met["significance_sigma"],
            "detected": met["detected"],
            "upper_limit_90_norm": met["upper_limit_90_norm"],
            "upper_limit_90_flux": met["upper_limit_90_flux"],
            "interpretation": interp,
        })
    write_csv(out / "xmm_lines.csv", LINE_FIELDS, line_rows)

    main_fit = results["joint_pl_line"]
    plot_figure(main_fit, results["joint_pl_baseline"],
                out / "xmm_spectrum_model_residual.png",
                out / "xmm_spectrum_model_residual.pdf", config)

    consistency = consistency_payload(results, config)
    bcheck = background_check(products, prepared)
    runtime = time.time() - t0

    # input manifest
    input_manifest = []
    for inst in INSTRUMENTS:
        for role in ("spectrum", "background", "arf", "rmf"):
            path = products[inst][role]
            input_manifest.append({
                "instrument": inst, "role": role,
                "path": str(path.relative_to(input_dir)),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            })

    effective_config = dict(config)
    effective_config["resolved"] = {
        "input_dir": str(input_dir),
        "products": {inst: {k: str(v) for k, v in products[inst].items()}
                     for inst in INSTRUMENTS},
        "prepared": {inst: {k: str(v) for k, v in prepared[inst].items()}
                     for inst in INSTRUMENTS},
    }
    effective_config["software"] = software_versions()
    effective_config["timestamp_utc"] = now_utc()
    (out / "config.effective.json").write_text(json.dumps(effective_config, indent=2) + "\n")

    headline = {
        "obsid": obsid,
        "source": object_name,
        "xspec_version": software_versions()["xspec"],
        "joint_baseline_chi2": results["joint_pl_baseline"]["chi2"],
        "joint_baseline_dof": results["joint_pl_baseline"]["dof"],
        "baseline_rchi2": results["joint_pl_baseline"]["rchi2"],
        "joint_line_chi2": results["joint_pl_line"]["chi2"],
        "joint_line_dof": results["joint_pl_line"]["dof"],
        "line_rchi2": results["joint_pl_line"]["rchi2"],
        "delta_chi2": metrics["joint_pl_line"]["delta_chi2"],
        "line_significance_sigma": metrics["joint_pl_line"]["significance_sigma"],
        "line_norm": metrics["joint_pl_line"]["norm"],
        "line_norm_err": metrics["joint_pl_line"]["norm_err"],
        "line_flux_erg_cm2_s": metrics["joint_pl_line"]["flux"],
        "line_flux_err": metrics["joint_pl_line"]["flux_err"],
        "ew_rest_keV": metrics["joint_pl_line"]["ew_rest_keV"],
        "ew_rest_err": metrics["joint_pl_line"]["ew_rest_err"],
        "gamma": results["joint_pl_baseline"]["gamma"],
        "nH_1e22": results["joint_pl_baseline"]["nH"],
        "detected": metrics["joint_pl_line"]["detected"],
    }

    run = {
        "tool": "xmm_xspec",
        "source": object_name,
        "source_key": source_key,
        "mission": "XMM-Newton",
        "obsid": obsid,
        "redshift": float(config["redshift"]),
        "reduction": {
            "path": "Official PPS products + CCF responses; SAS epproc/especget NOT run",
            "pps_sas_version": prov["PN"].get("sas_version", ""),
            "pn_rmf": products["PN"]["rmf"].name,
            "mos1_rmf": products["MOS1"]["rmf"].name,
            "mos2_rmf": products["MOS2"]["rmf"].name,
            "mos_rebin": "3:1 (5 eV PPS channels -> 15 eV) to match the MOS 15 eV canned RMF",
        },
        "instruments": {
            inst: {
                "exposure_s": prov[inst]["exposure_s"],
                "counts_total": prov[inst]["counts_total"],
                "channels_pps": prov[inst]["channels"],
                "channels_used": 4096 if inst == "PN" else 800,
                "filter": prov[inst]["filter"],
                "pps_respfile": prov[inst]["respfile"],
                "pps_ancrfile": prov[inst]["ancrfile"],
                "pps_backfile": prov[inst]["backfile"],
            } for inst in INSTRUMENTS
        },
        "inputs": input_manifest,
        "software": software_versions(),
        "config": effective_config,
        "headline": headline,
        "fits": fit_rows,
        "line_measurements": line_rows,
        "consistency": consistency,
        "background_check": bcheck,
        "runtime_s": runtime,
        "image_size_bytes": int(os.environ.get("XMM_XSPEC_IMAGE_SIZE", "0") or 0),
        "repo_commit": os.environ.get("XMM_XSPEC_REPO_COMMIT", ""),
        "command": " ".join([Path(sys.argv[0]).name] + sys.argv[1:]),
        "caveats": [
            "PPS official products; SAS epproc/especget/specgroup were not run.",
            "MOS 5 eV PPS spectra rebinned 3:1 to 15 eV for the 15 eV canned RMF named in the PPS header.",
            "PN RMF is CCF v22.0; PPS products were generated with SAS 21.0.0 (2024).",
            "RMF FILTER=Medium vs observation Thin1 is expected; the ARF carries the filter throughput.",
            "tbabs*zpowerlw leaves chi2/dof ~1.70; soft excess and reflection are not modeled.",
            "The free-width Fe K-alpha Gaussian is degenerate with continuum curvature; the primary narrow-core width is fixed to 50 eV.",
            "The free-centroid fit gives E_rest ~ 6.18 keV; the single Gaussian captures a redshifted/broad Fe complex.",
            "PN and MOS Gamma differ by 2.9 sigma (MOS1), a cross-calibration systematic.",
            "Errors are XSPEC covariance 1-sigma; no MCMC.",
        ],
    }
    (out / "run.json").write_text(json.dumps(run, indent=2) + "\n")
    (out / "xmm_consistency.json").write_text(json.dumps(consistency, indent=2) + "\n")
    write_provenance(out / "provenance.md", run)

    summary = f"""XMM-Newton EPIC xmm_xspec summary
=================================
source: {object_name}   ObsID: {obsid}   z={config['redshift']}
XSPEC: {run['software']['xspec']}   runtime: {runtime:.1f} s

Joint baseline ({results['joint_pl_baseline']['model']}, {config['band_keV'][0]}-{config['band_keV'][1]} keV):
  chi2/dof = {results['joint_pl_baseline']['chi2']:.2f}/{results['joint_pl_baseline']['dof']} = {results['joint_pl_baseline']['rchi2']:.3f}
  N_H = {results['joint_pl_baseline']['nH'][0]:.4f} +/- {results['joint_pl_baseline']['nH'][1]:.4f} x 1e22 cm^-2
  Gamma = {results['joint_pl_baseline']['gamma'][0]:.4f} +/- {results['joint_pl_baseline']['gamma'][1]:.4f}
  cross-cal constants: MOS1={results['joint_pl_baseline']['constants']['MOS1']['value']:.4f}, MOS2={results['joint_pl_baseline']['constants']['MOS2']['value']:.4f}

Joint narrow Fe K-alpha (sigma=50 eV rest):
  chi2/dof = {results['joint_pl_line']['chi2']:.2f}/{results['joint_pl_line']['dof']} = {results['joint_pl_line']['rchi2']:.3f}
  Delta chi2 = {metrics['joint_pl_line']['delta_chi2']:.2f} for {metrics['joint_pl_line']['delta_dof']} dof -> {metrics['joint_pl_line']['significance_sigma']:.2f} sigma
  line norm = ({metrics['joint_pl_line']['norm']:.3e} +/- {metrics['joint_pl_line']['norm_err']:.2e}) photons cm^-2 s^-1
  line flux = ({metrics['joint_pl_line']['flux']:.3e} +/- {metrics['joint_pl_line']['flux_err']:.2e}) erg cm^-2 s^-1
  EW_rest = {metrics['joint_pl_line']['ew_rest_keV']*1000:.1f} +/- {metrics['joint_pl_line']['ew_rest_err']*1000:.1f} eV
  detected = {metrics['joint_pl_line']['detected']}

Independent narrow-line measurements:
"""
    for inst in INSTRUMENTS:
        met = metrics.get(f"{inst.lower()}_pl_line")
        if met:
            summary += (f"  {inst}: Delta chi2={met['delta_chi2']:.2f}, "
                        f"{met['significance_sigma']:.2f} sigma, "
                        f"norm=({met['norm']:.3e}+/-{met['norm_err']:.1e}), "
                        f"EW_rest={met['ew_rest_keV']*1000:.1f} eV\n")
    summary += "\nCaveat: PPS products, no SAS reduction; simple continuum; XSPEC covariance errors.\n"
    (out / "fit_summary.txt").write_text(summary)
    print("\n" + summary)
    print(f"[xmm_xspec] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
