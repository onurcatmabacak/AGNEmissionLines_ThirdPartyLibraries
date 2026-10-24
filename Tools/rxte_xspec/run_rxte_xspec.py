#!/usr/bin/env python3
"""Official RXTE/PCA spectral fitting with HEASoft/PyXspec.

This is the production entry point for the ``rxte_xspec`` tool.  It reads the
official HEASARC ``stdprod`` PCA Standard2 source spectrum, the official PCA
background model and the official PCA response matrix (5 PCUs summed), then
fits an absorbed power law with an optional Fe K-alpha line.

The production model in the observed 3-20 keV band is::

    tbabs * (zpowerlw + zgauss)

``zpowerlw`` and ``zgauss`` use the source redshift; the Fe K-alpha line
energy is 6.4 keV in the rest frame and the narrow-core width is fixed to
50 eV.  Free-width and free-centroid fits are diagnostics.  A second fit in
the 3-10 keV line band and a conservative fit with N_H frozen to the
continuum-only value are also produced.

Nothing here runs ``pcabackest`` or ``saextrct``.  The HEASARC ``stdprod``
products are the official reduced PCA products (source spectrum, background
model, response matrix); see ``provenance.md`` for the exact files and hashes.

Usage (inside the container)::

    python run_rxte_xspec.py --input-dir /app/input --out /app/output \
        --config /app/config --source-key 3C120_z_0.0330 --redshift 0.0330
"""
from __future__ import annotations

import argparse
import csv
import gzip
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
LINE_COMPONENT = 3  # fallback: tbabs(1) * (zpowerlw(2) + zgauss(3))
TOOL_VERSION = "1.0.0"


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
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
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
        delta = max(abs(float(value)) * 0.02, 1e-6)
        # values = [value, delta, hardmin, softmin, softmax, hardmax]
        p.values = (float(value), delta, float(lo), float(lo),
                    float(hi), float(hi))
    if frozen is not None:
        p.frozen = bool(frozen)


def run_command(cmd: list[str]) -> str:
    try:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, timeout=60)
        return proc.stdout.strip()
    except Exception as exc:  # pragma: no cover - diagnostic only
        return f"unavailable: {exc}"


def software_versions() -> dict:
    xspec = run_command(["xspec", "--version"])
    headas = run_command(["fversion"])
    out = {
        "xspec": xspec.splitlines()[0].strip() if xspec else "",
        "xspec_raw": xspec,
        "heasoft": headas,
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pyxspec_path": getattr(sys.modules.get("xspec"), "__file__", ""),
        "headas_env": os.environ.get("HEADAS", ""),
    }
    for line in xspec.splitlines():
        if "XSPEC version" in line:
            out["xspec_version"] = line.split("XSPEC version:", 1)[1].strip()
    return out


# ---------------------------------------------------------------------------
# input discovery and preparation
# ---------------------------------------------------------------------------
def _one(paths: list[Path], role: str) -> Path:
    if len(paths) != 1:
        raise FileNotFoundError(
            f"{role}: expected exactly one file, found {len(paths)}: "
            f"{[p.name for p in paths]}")
    return paths[0]


def discover_products(input_dir: Path, config: dict) -> dict:
    overrides = config.get("products", {})
    if overrides:
        return {k: (input_dir / v) for k, v in overrides.items()}

    def glob(patterns):
        out = []
        for pat in patterns:
            out.extend(sorted(input_dir.glob(pat)))
        # De-duplicate while preserving order.
        return list(dict.fromkeys(out))

    source = _one(glob(["*_s2.pha.gz", "*_s2.pha", "*s2*.pha.gz",
                        "*s2*.pha"]), "PCA source spectrum")
    background = _one(glob(["*_b2.pha.gz", "*_b2.pha", "*b2*.pha.gz",
                            "*b2*.pha"]), "PCA background model")
    response = _one(glob(["*.rsp.gz", "*.rsp", "*.rmf.gz", "*.rmf"]),
                    "PCA response matrix")
    return {"source": source, "background": background, "response": response}


def decompress(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix == ".gz":
        with gzip.open(src, "rb") as fin, dst.open("wb") as fout:
            shutil.copyfileobj(fin, fout)
    else:
        shutil.copyfile(src, dst)
    return dst


def sanitize_pha(src: Path, dst: Path) -> Path:
    """Copy a PCA PHA and remove header pointers to absent auxiliary files."""
    with fits.open(src) as h:
        hdul = fits.HDUList([hdu.copy() for hdu in h])
    sh = hdul["SPECTRUM"].header
    sh["RESPFILE"] = "NONE"
    sh["ANCRFILE"] = "NONE"
    sh["BACKFILE"] = "NONE"
    for key, value in (("HDUVERS1", "1.1.0"), ("HDUVERS", "1.0.0"),
                       ("SYS_ERR", 0), ("CORRSCAL", 1.0)):
        sh.setdefault(key, value)
    hdul.writeto(dst, overwrite=True)
    return dst


def prepare_inputs(products: dict, prepared_dir: Path) -> dict:
    prepared_dir.mkdir(parents=True, exist_ok=True)
    src_tmp = decompress(products["source"], prepared_dir / "source.decompressed.pha")
    bg_tmp = decompress(products["background"],
                        prepared_dir / "background.decompressed.pha")
    resp = decompress(products["response"], prepared_dir / "response.rsp")
    source = sanitize_pha(src_tmp, prepared_dir / "source.pha")
    background = sanitize_pha(bg_tmp, prepared_dir / "background.pha")
    src_tmp.unlink(missing_ok=True)
    bg_tmp.unlink(missing_ok=True)
    return {"source": source, "background": background, "response": resp,
            "raw": products}


def header_provenance(path: Path) -> dict:
    out = {}
    with fits.open(path) as h:
        ph = h[0].header
        sh = h["SPECTRUM"].header if "SPECTRUM" in h else ph
        out.update({
            "telescope": str(ph.get("TELESCOP", "")).strip(),
            "instrument": str(ph.get("INSTRUME", "")).strip(),
            "object": str(ph.get("OBJECT", "")).strip(),
            "date_obs": str(ph.get("DATE-OBS", "")).strip(),
            "date_end": str(ph.get("DATE-END", "")).strip(),
            "ra_obj_deg": jfloat(ph.get("RA_OBJ")),
            "dec_obj_deg": jfloat(ph.get("DEC_OBJ")),
            "exposure_s": jfloat(sh.get("EXPOSURE")),
            "backscal": jfloat(sh.get("BACKSCAL")),
            "areascal": jfloat(sh.get("AREASCAL")),
            "respfile": str(sh.get("RESPFILE", "")).strip(),
            "backfile": str(sh.get("BACKFILE", "")).strip(),
            "channels": int(sh.get("DETCHANS", len(h["SPECTRUM"].data))),
        })
        if "SPECTRUM" in h:
            d = h["SPECTRUM"].data
            counts = np.asarray(d["COUNTS"], dtype=float)
            out["counts_total"] = float(counts.sum())
            if "STAT_ERR" in d.columns.names:
                out["stat_err_total"] = float(
                    np.asarray(d["STAT_ERR"], dtype=float).sum())
    return out


def response_provenance(path: Path) -> dict:
    out = {}
    with fits.open(path) as h:
        out["hdus"] = [hdu.name for hdu in h]
        out["channels_ebounds"] = int(len(h["EBOUNDS"].data))
        mat = h["SPECRESP MATRIX"]
        out["energy_bins"] = int(len(mat.data))
        e_lo = np.asarray(mat.data["ENERG_LO"], dtype=float)
        e_hi = np.asarray(mat.data["ENERG_HI"], dtype=float)
        out["energy_range_keV"] = [float(e_lo.min()), float(e_hi.max())]
        out["matrix_format"] = str(mat.header.get("TFORM6", ""))
        out["pcount"] = int(mat.header.get("PCOUNT", 0))
        out["history_note"] = (
            "marfrmf 3.2.6; PCA RMF multiplied by the 5-PCU ARF and the "
            "5 individual PCU RMFs summed (see the RSP HISTORY cards)")
        out["history"] = [str(x) for x in mat.header.get("HISTORY", [])][:12]
    return out


# ---------------------------------------------------------------------------
# XSPEC fits
# ---------------------------------------------------------------------------
def reset_xspec():
    # Keep Xset's log file open across fits; only clear the data/model state.
    try:
        Plot.setGroup(None)
    except Exception:
        pass
    AllData.clear()
    AllModels.clear()


def load_data(prepared: dict, band: tuple[float, float], config: dict,
              statistic: str | None = None):
    reset_xspec()
    AllData(f"1:1 {prepared['source']}")
    s = AllData(1)
    s.response = str(prepared["response"])
    s.background = str(prepared["background"])
    AllData.ignore("bad")
    AllData.ignore(f"0.0-{band[0]} {band[1]}-**")
    Xset.abund = config.get("abund", "wilm")
    Fit.statMethod = statistic or config.get("statistic", "chi")
    Fit.nIterations = int(config.get("fit_iterations", 500))
    Fit.query = "no"
    Xset.chatter = int(config.get("xspec_chatter", 10))
    return s


def seed_continuum(m, config):
    z = float(config["redshift"])
    set_par(m.TBabs, "nH", float(config.get("seed_nH_1e22", 0.1)),
            bounds=(0.0, float(config.get("nH_max_1e22", 20.0))))
    set_par(m.zpowerlw, "PhoIndex", float(config.get("seed_gamma", 1.8)),
            bounds=(-2.0, 9.0))
    set_par(m.zpowerlw, "Redshift", z, frozen=True)
    set_par(m.zpowerlw, "norm", float(config.get("seed_pl_norm", 0.02)))
    if hasattr(m, "zbbody"):
        set_par(m.zbbody, "kT", float(config.get("seed_bb_kT_keV", 0.2)),
                bounds=(0.01, 20.0))
        set_par(m.zbbody, "Redshift", z, frozen=True)
        set_par(m.zbbody, "norm", float(config.get("seed_bb_norm", 1e-4)))


def seed_line(m, config, free_sigma: bool, free_energy: bool):
    z = float(config["redshift"])
    e0 = float(config.get("line_rest_energy_keV", FE_KA_REST_KEV))
    sig = float(config.get("line_sigma_keV", 0.05))
    set_par(m.zgauss, "LineE", e0, frozen=not free_energy,
            bounds=tuple(config.get("line_energy_free_bounds_keV", [5.0, 8.0]))
            if free_energy else None)
    if free_sigma:
        set_par(m.zgauss, "Sigma",
                float(config.get("seed_line_sigma_keV", 0.3)), frozen=False,
                bounds=tuple(config.get("line_sigma_free_bounds_keV",
                                        [0.01, 1.0])))
    else:
        set_par(m.zgauss, "Sigma", sig, frozen=True)
    set_par(m.zgauss, "Redshift", z, frozen=True)
    set_par(m.zgauss, "norm", float(config.get("seed_line_norm", 1e-5)))


def capture_plot(m) -> dict:
    Plot.device = "/null"
    Plot.xAxis = "keV"
    Plot("data", "delchi")
    x = np.asarray(Plot.x(1, 1), dtype=float)
    data = np.asarray(Plot.y(1, 1), dtype=float)
    data_err = np.asarray(Plot.yErr(1, 1), dtype=float)
    delchi = np.asarray(Plot.y(1, 2), dtype=float)
    energies = np.asarray(AllData(1).energies, dtype=float)
    de = energies[:, 1] - energies[:, 0]
    folded = np.asarray(m.folded(1), dtype=float)
    n = min(len(x), len(data), len(data_err), len(delchi), len(de), len(folded))
    if n == 0:
        raise RuntimeError("empty XSPEC plot arrays")
    return {
        "energy_keV": x[:n].tolist(),
        "data_counts_s_keV": data[:n].tolist(),
        "data_err": data_err[:n].tolist(),
        "delchi": delchi[:n].tolist(),
        "bin_width_keV": de[:n].tolist(),
        "model_counts_s_keV": (folded[:n] / de[:n]).tolist(),
    }


def fit_model(prepared: dict, config: dict, *, fit_id: str,
              band: tuple[float, float], line: bool,
              seed: dict | None = None,
              nH_fixed: float | None = None,
              free_sigma: bool = False,
              free_energy: bool = False,
              soft_excess: bool = False,
              statistic: str | None = None) -> dict:
    """Fit one model to the single PCA spectrum."""
    load_data(prepared, band, config, statistic=statistic)
    expr = "tbabs*(zpowerlw" + (" + zbbody" if soft_excess else "")
    expr += (" + zgauss" if line else "") + ")"
    m = Model(expr)
    seed_continuum(m, config)
    if seed:
        set_par(m.TBabs, "nH", seed["nH"], bounds=(0.0, 20.0))
        set_par(m.zpowerlw, "PhoIndex", seed["gamma"], bounds=(-2.0, 9.0))
        set_par(m.zpowerlw, "norm", seed["pl_norm"])
    if nH_fixed is not None:
        set_par(m.TBabs, "nH", nH_fixed, frozen=True)
    if line:
        seed_line(m, config, free_sigma, free_energy)

    Fit.perform()

    result = {
        "fit_id": fit_id,
        "band_keV": [float(band[0]), float(band[1])],
        "model": expr,
        "line": bool(line),
        "free_sigma": bool(free_sigma),
        "free_energy": bool(free_energy),
        "nH_fixed": nH_fixed is not None,
        "soft_excess": bool(soft_excess),
        "chi2": float(Fit.statistic),
        "dof": int(Fit.dof),
        "rchi2": float(Fit.statistic / Fit.dof) if Fit.dof else float("nan"),
        "statistic": statistic or config.get("statistic", "chi"),
        "nH": par_value(m.TBabs, "nH"),
        "gamma": par_value(m.zpowerlw, "PhoIndex"),
        "pl_norm": par_value(m.zpowerlw, "norm"),
        "group_chi2": float(AllData(1).statistic),
        "group_bins": int(len(AllData(1).values)),
        "plot": capture_plot(m),
    }
    if line:
        result["line_params"] = {
            "energy_rest_keV": par_value(m.zgauss, "LineE"),
            "sigma_keV": par_value(m.zgauss, "Sigma"),
            "norm_photons_cm2_s": par_value(m.zgauss, "norm"),
            "redshift": float(config["redshift"]),
        }
        try:
            line_comp = list(m.componentNames).index("zgauss") + 1
        except ValueError:
            line_comp = LINE_COMPONENT
        result["line_component"] = line_comp
        try:
            AllModels.eqwidth(str(line_comp))
            ew = AllData(1).eqwidth
            result["eqwidth_obs_keV"] = [float(x) for x in ew]
        except Exception as exc:  # pragma: no cover - diagnostic only
            result["eqwidth_obs_keV"] = None
            result["eqwidth_error"] = str(exc)
    return result


def statistic_crosscheck(prepared: dict, config: dict) -> dict:
    """Refit the production baseline and narrow line with pgstat and cstat."""
    band = tuple(float(x) for x in config["band_keV"])
    out = {}
    for stat in ("pgstat", "cstat"):
        cfg = dict(config)
        cfg["statistic"] = stat
        base = fit_model(prepared, cfg, fit_id=f"baseline_{stat}", band=band,
                         line=False, statistic=stat)
        seed = {"nH": base["nH"][0], "gamma": base["gamma"][0],
                "pl_norm": base["pl_norm"][0]}
        line = fit_model(prepared, cfg, fit_id=f"line_{stat}", band=band,
                         line=True, seed=seed, statistic=stat)
        out[stat] = {
            "baseline_stat": base["chi2"],
            "line_stat": line["chi2"],
            "delta_stat": base["chi2"] - line["chi2"],
            "dof": line["dof"],
            "gamma": line["gamma"],
            "nH": line["nH"],
            "line_norm": line["line_params"]["norm_photons_cm2_s"],
        }
    return out


def fit_all(prepared: dict, config: dict) -> dict:
    primary_band = tuple(float(x) for x in config["band_keV"])
    line_band = tuple(float(x) for x in config.get("line_band_keV", [3.0, 10.0]))
    results = {}

    # Continuum-only baseline in the production band.
    base = fit_model(prepared, config, fit_id="baseline_3_20", band=primary_band,
                     line=False)
    results["baseline_3_20"] = base
    seed = {"nH": base["nH"][0], "gamma": base["gamma"][0],
            "pl_norm": base["pl_norm"][0]}

    # Production: joint continuum + narrow Fe K-alpha in 3-20 keV.
    results["line_3_20"] = fit_model(
        prepared, config, fit_id="line_3_20", band=primary_band, line=True,
        seed=seed)
    # Conservative variant: N_H frozen to the continuum-only value.  The
    # matching fixed-N_H baseline is required for a nested Delta-chi2.
    results["baseline_3_20_fixed_nH"] = fit_model(
        prepared, config, fit_id="baseline_3_20_fixed_nH", band=primary_band,
        line=False, seed=seed, nH_fixed=base["nH"][0])
    results["line_3_20_fixed_nH"] = fit_model(
        prepared, config, fit_id="line_3_20_fixed_nH", band=primary_band,
        line=True, seed=seed, nH_fixed=base["nH"][0])

    # Continuum-systematic check: allow a soft blackbody excess.  The
    # simple power law leaves significant residuals in 3-20 keV; this
    # diagnostic tests whether the Fe line survives a more flexible
    # continuum.  It is not the production model.
    if config.get("soft_excess_check", True):
        soft_base = fit_model(
            prepared, config, fit_id="baseline_3_20_soft_excess",
            band=primary_band, line=False, soft_excess=True)
        results["baseline_3_20_soft_excess"] = soft_base
        results["line_3_20_soft_excess"] = fit_model(
            prepared, config, fit_id="line_3_20_soft_excess",
            band=primary_band, line=True, soft_excess=True)

    # Line-band cross-check: the simple power law is a good description in
    # 3-10 keV and the Fe K-alpha is measured with a local continuum.
    base10 = fit_model(prepared, config, fit_id="baseline_3_10", band=line_band,
                       line=False)
    results["baseline_3_10"] = base10
    seed10 = {"nH": base10["nH"][0], "gamma": base10["gamma"][0],
              "pl_norm": base10["pl_norm"][0]}
    results["line_3_10"] = fit_model(
        prepared, config, fit_id="line_3_10", band=line_band, line=True,
        seed=seed10)

    # Diagnostics: free width and free centroid in the line band.
    if config.get("line_sigma_free", True):
        results["line_3_10_free_sigma"] = fit_model(
            prepared, config, fit_id="line_3_10_free_sigma", band=line_band,
            line=True, seed=seed10, free_sigma=True)
    if config.get("line_energy_free", True):
        results["line_3_10_free_energy"] = fit_model(
            prepared, config, fit_id="line_3_10_free_energy", band=line_band,
            line=True, seed=seed10, free_sigma=True, free_energy=True)
    return results


# ---------------------------------------------------------------------------
# derived line quantities and statistics
# ---------------------------------------------------------------------------
def chi2_sf(x: float, dof: int) -> float:
    """Survival function of the chi-square distribution."""
    if x <= 0:
        return 1.0
    if dof == 1:
        return math.erfc(math.sqrt(x / 2.0))
    if dof == 2:
        return math.exp(-x / 2.0)
    k = dof / 2.0
    a = x / 2.0
    if a < k + 1.0:
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
    if p <= 0:
        return 50.0
    if p >= 1:
        return 0.0
    try:
        from scipy.special import erfcinv
        return float(min(50.0, math.sqrt(2.0) * erfcinv(p)))
    except Exception:
        lo, hi = 0.0, 40.0
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if math.erfc(mid / math.sqrt(2.0)) > p:
                lo = mid
            else:
                hi = mid
        return min(50.0, 0.5 * (lo + hi))


def line_metrics(fit: dict, baseline: dict, config: dict) -> dict:
    z = float(config["redshift"])
    p = fit["line_params"]
    norm, norm_err = p["norm_photons_cm2_s"]
    e_rest, e_rest_err = p["energy_rest_keV"]
    sigma, sigma_err = p["sigma_keV"]
    e_obs = e_rest / (1.0 + z)
    flux = norm * e_obs * C_KEV_ERG
    flux_err = abs(norm_err) * e_obs * C_KEV_ERG

    gamma = fit["gamma"][0]
    pl_norm = fit["pl_norm"][0]
    f_cont_rest = pl_norm * e_rest ** (-gamma)
    ew_rest_analytic = norm / f_cont_rest
    ew_rest_err = abs(norm_err) / f_cont_rest
    ew_obs_analytic = ew_rest_analytic / (1.0 + z)
    ew_xspec = fit.get("eqwidth_obs_keV")
    if ew_xspec:
        ew_obs = float(ew_xspec[0])
        ew_obs_low = float(ew_xspec[1])
        ew_obs_high = float(ew_xspec[2])
        if ew_obs_low == 0.0 and ew_obs_high == 0.0:
            ew_obs_low = ew_obs_high = ew_rest_err / (1.0 + z)
    else:
        ew_obs = ew_obs_analytic
        ew_obs_low = ew_obs_high = ew_rest_err / (1.0 + z)

    delta = baseline["chi2"] - fit["chi2"]
    ddof = baseline["dof"] - fit["dof"]
    p_value = chi2_sf(delta, ddof) if ddof > 0 else 1.0
    significance = norm_to_sigma(p_value)
    detected = bool(significance >= 3.0)
    ul_norm = max(0.0, norm) + 1.645 * abs(norm_err)
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
        "ew_obs_keV": ew_obs,
        "ew_obs_err_low": ew_obs_low,
        "ew_obs_err_high": ew_obs_high,
        "ew_rest_keV": ew_obs * (1.0 + z),
        "ew_rest_err": ew_rest_err,
        "ew_rest_analytic_keV": ew_rest_analytic,
        "ew_xspec_obs_keV": ew_xspec[0] if ew_xspec else None,
        "delta_chi2": delta,
        "delta_dof": ddof,
        "p_value": p_value,
        "significance_sigma": significance,
        "detected": detected,
        "upper_limit_90_norm": ul_norm,
        "upper_limit_90_flux": ul_norm * e_obs * C_KEV_ERG,
        "upper_limit_90_ew_rest_keV": ul_norm / f_cont_rest,
        "continuum_photon_flux_at_line": f_cont_rest,
    }


# ---------------------------------------------------------------------------
# output writers
# ---------------------------------------------------------------------------
FIT_FIELDS = [
    "fit_id", "band_keV", "model", "statistic", "chi2", "dof", "rchi2",
    "nH_1e22", "nH_err", "nH_fixed", "gamma", "gamma_err", "pl_norm",
    "pl_norm_err", "line_norm", "line_norm_err", "line_flux_erg_cm2_s",
    "line_flux_err", "line_energy_rest_keV", "line_sigma_keV",
    "ew_obs_keV", "ew_rest_keV", "delta_chi2", "delta_dof", "p_value",
    "significance_sigma", "detected", "notes",
]

LINE_FIELDS = [
    "fit_id", "line", "band_keV", "rest_energy_keV", "rest_energy_err",
    "observed_energy_keV", "sigma_keV", "sigma_err", "norm_photons_cm2_s",
    "norm_err", "flux_erg_cm2_s", "flux_err", "ew_obs_keV",
    "ew_obs_err_low", "ew_obs_err_high", "ew_rest_keV", "ew_rest_err",
    "ew_xspec_obs_keV", "delta_chi2", "delta_dof", "p_value",
    "significance_sigma", "detected", "upper_limit_90_norm",
    "upper_limit_90_flux", "upper_limit_90_ew_rest_keV", "interpretation",
]


def write_csv(path: Path, fields: list[str], rows: list[dict]):
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: fmt(row.get(k)) for k in fields})


def fmt_band(band):
    return f"{band[0]}-{band[1]}"


def fit_row(fit: dict, metrics: dict | None, notes: str) -> dict:
    row = {
        "fit_id": fit["fit_id"],
        "band_keV": fmt_band(fit["band_keV"]),
        "model": fit["model"],
        "statistic": fit["statistic"],
        "chi2": fit["chi2"],
        "dof": fit["dof"],
        "rchi2": fit["rchi2"],
        "nH_1e22": fit["nH"][0],
        "nH_err": fit["nH"][1],
        "nH_fixed": int(fit["nH_fixed"]),
        "gamma": fit["gamma"][0],
        "gamma_err": fit["gamma"][1],
        "pl_norm": fit["pl_norm"][0],
        "pl_norm_err": fit["pl_norm"][1],
        "notes": notes,
    }
    if metrics:
        row.update({
            "line_norm": metrics["norm"],
            "line_norm_err": metrics["norm_err"],
            "line_flux_erg_cm2_s": metrics["flux"],
            "line_flux_err": metrics["flux_err"],
            "line_energy_rest_keV": metrics["rest_energy_keV"],
            "line_sigma_keV": metrics["sigma_keV"],
            "ew_obs_keV": metrics["ew_obs_keV"],
            "ew_rest_keV": metrics["ew_rest_keV"],
            "delta_chi2": metrics["delta_chi2"],
            "delta_dof": metrics["delta_dof"],
            "p_value": metrics["p_value"],
            "significance_sigma": metrics["significance_sigma"],
            "detected": int(metrics["detected"]),
        })
    return row


def line_row(fit: dict, metrics: dict, interpretation: str,
             baseline_id: str) -> dict:
    return {
        "fit_id": fit["fit_id"],
        "line": "Fe K-alpha",
        "band_keV": fmt_band(fit["band_keV"]),
        "rest_energy_keV": metrics["rest_energy_keV"],
        "rest_energy_err": metrics["rest_energy_err"],
        "observed_energy_keV": metrics["observed_energy_keV"],
        "sigma_keV": metrics["sigma_keV"],
        "sigma_err": metrics["sigma_err"],
        "norm_photons_cm2_s": metrics["norm"],
        "norm_err": metrics["norm_err"],
        "flux_erg_cm2_s": metrics["flux"],
        "flux_err": metrics["flux_err"],
        "ew_obs_keV": metrics["ew_obs_keV"],
        "ew_obs_err_low": metrics["ew_obs_err_low"],
        "ew_obs_err_high": metrics["ew_obs_err_high"],
        "ew_rest_keV": metrics["ew_rest_keV"],
        "ew_rest_err": metrics["ew_rest_err"],
        "ew_xspec_obs_keV": metrics["ew_xspec_obs_keV"],
        "delta_chi2": metrics["delta_chi2"],
        "delta_dof": metrics["delta_dof"],
        "p_value": metrics["p_value"],
        "significance_sigma": metrics["significance_sigma"],
        "detected": int(metrics["detected"]),
        "upper_limit_90_norm": metrics["upper_limit_90_norm"],
        "upper_limit_90_flux": metrics["upper_limit_90_flux"],
        "upper_limit_90_ew_rest_keV": metrics["upper_limit_90_ew_rest_keV"],
        "interpretation": interpretation,
    }


def _arrays(plot: dict):
    x = np.asarray(plot["energy_keV"], dtype=float)
    y = np.asarray(plot["data_counts_s_keV"], dtype=float)
    yerr = np.asarray(plot["data_err"], dtype=float)
    model = np.asarray(plot["model_counts_s_keV"], dtype=float)
    delchi = np.asarray(plot["delchi"], dtype=float)
    n = min(len(x), len(y), len(yerr), len(model), len(delchi))
    return x[:n], y[:n], yerr[:n], model[:n], delchi[:n]


def plot_main(fit: dict, baseline: dict, path_png: Path, path_pdf: Path,
              config: dict):
    x, y, yerr, model, delchi = _arrays(fit["plot"])
    xb, _, _, model_b, _ = _arrays(baseline["plot"])
    n = min(len(x), len(xb))
    x, y, yerr, model, delchi, model_b = (
        x[:n], y[:n], yerr[:n], model[:n], delchi[:n], model_b[:n])
    z = float(config["redshift"])
    e_line = float(config.get("line_rest_energy_keV", FE_KA_REST_KEV)) / (1.0 + z)

    fig, (ax, axr) = plt.subplots(
        2, 1, figsize=(7.4, 6.2), sharex=True,
        gridspec_kw={"height_ratios": [3.0, 1.0], "hspace": 0.06})
    ax.errorbar(x, y, yerr=yerr, fmt="o", ms=2.5, lw=0.7, color="black",
                ecolor="0.55", capsize=0, label="PCA Standard2 data")
    ax.plot(x, model, color="C0", lw=1.5,
            label=fit["model"])
    ax.plot(x, model_b, color="C1", lw=1.1, ls="--",
            label="tbabs*zpowerlw baseline")
    ax.axvline(e_line, color="0.4", lw=0.8, ls=":")
    ax.text(e_line * 1.02, ax.get_ylim()[1] * 0.55,
            "Fe K$\\alpha$ (rest 6.4 keV)", fontsize=8, color="0.3")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylabel("counts s$^{-1}$ keV$^{-1}$")
    ax.set_title(
        f"{config.get('source_name', 'RXTE/PCA')}  "
        f"{fit['band_keV'][0]:g}-{fit['band_keV'][1]:g} keV  "
        f"$\\chi^2$/dof={fit['chi2']:.1f}/{fit['dof']}="
        f"{fit['rchi2']:.3f}", fontsize=10)
    ax.legend(loc="upper right", fontsize=8, frameon=False)

    axr.axhline(0.0, color="0.4", lw=0.8)
    axr.errorbar(x, delchi, yerr=1.0, fmt="o", ms=2.5, lw=0.7,
                 color="black", ecolor="0.55", capsize=0)
    axr.set_ylabel("(data-model)/$\\sigma$")
    axr.set_xlabel("Observed energy (keV)")
    axr.set_ylim(-5.5, 5.5)
    fig.align_ylabels([ax, axr])
    fig.tight_layout()
    fig.savefig(path_png, dpi=int(config.get("plot_dpi", 150)))
    fig.savefig(path_pdf)
    plt.close(fig)


def plot_zoom(fit: dict, baseline: dict, path_png: Path, path_pdf: Path,
              config: dict):
    x, y, yerr, model, delchi = _arrays(fit["plot"])
    xb, _, _, model_b, _ = _arrays(baseline["plot"])
    n = min(len(x), len(xb))
    x, y, yerr, model, delchi, model_b = (
        x[:n], y[:n], yerr[:n], model[:n], delchi[:n], model_b[:n])
    lo, hi = [float(v) for v in config.get("zoom_keV", [4.0, 8.0])]
    m = (x >= lo) & (x <= hi)
    if not np.any(m):
        raise RuntimeError(f"no bins in zoom range {lo}-{hi} keV")
    z = float(config["redshift"])
    e_line = float(config.get("line_rest_energy_keV", FE_KA_REST_KEV)) / (1.0 + z)

    fig, (ax, axr) = plt.subplots(
        2, 1, figsize=(7.2, 5.2), sharex=True,
        gridspec_kw={"height_ratios": [3.0, 1.0], "hspace": 0.06})
    ax.errorbar(x[m], y[m], yerr=yerr[m], fmt="o", ms=5, lw=1.0,
                color="black", ecolor="0.55", capsize=0, label="PCA data")
    ax.plot(x[m], model[m], color="C0", lw=1.8, label=fit["model"])
    ax.plot(x[m], model_b[m], color="C1", lw=1.3, ls="--",
            label="continuum (no Fe line)")
    ax.fill_between(x[m], model_b[m], model[m],
                    where=model[m] >= model_b[m], color="C0", alpha=0.18,
                    label="Fe K$\\alpha$ model")
    ax.axvline(e_line, color="0.4", lw=0.8, ls=":")
    ax.set_yscale("log")
    ax.set_ylabel("counts s$^{-1}$ keV$^{-1}$")
    ax.set_title(
        f"Fe K$\\alpha$ zoom, {config.get('source_name', '')}  "
        f"$\\Delta\\chi^2$={fit.get('delta_chi2', float('nan')):.1f}",
        fontsize=10)
    ax.legend(loc="upper right", fontsize=8, frameon=False)

    axr.axhline(0.0, color="0.4", lw=0.8)
    axr.errorbar(x[m], delchi[m], yerr=1.0, fmt="o", ms=5, lw=1.0,
                 color="black", ecolor="0.55", capsize=0)
    axr.set_ylabel("(data-model)/$\\sigma$")
    axr.set_xlabel("Observed energy (keV)")
    axr.set_ylim(-5.5, 5.5)
    fig.align_ylabels([ax, axr])
    fig.tight_layout()
    fig.savefig(path_png, dpi=int(config.get("plot_dpi", 150)))
    fig.savefig(path_pdf)
    plt.close(fig)


def write_provenance(path: Path, run: dict):
    inp = run["inputs"]
    src = inp.get("source", {})
    bg = inp.get("background", {})
    rsp = inp.get("response", {})
    lines = [
        "# RXTE/PCA provenance",
        "",
        f"Source: **{run['source']['name']}** "
        f"(ObsID `{run['source']['obs_id']}`, z = {run['source']['redshift']}).",
        "",
        "## Official products",
        "",
        "The spectra are the HEASARC **stdprod** PCA products, i.e. the official",
        "reduced products of the RXTE Guest Observer Facility.  They were not",
        "produced by `pcabackest` or `saextrct` in this repository.",
        "",
        f"* base URL: `{run['source']['archive_url']}`",
        f"* source: `{src.get('name', '')}` "
        f"({src.get('size_bytes', '')} bytes, SHA256 `{src.get('sha256', '')}`)",
        f"* background model: `{bg.get('name', '')}` "
        f"({bg.get('size_bytes', '')} bytes, SHA256 `{bg.get('sha256', '')}`)",
        f"* response: `{rsp.get('name', '')}` "
        f"({rsp.get('size_bytes', '')} bytes, SHA256 `{rsp.get('sha256', '')}`)",
        "",
        "HEASARC does not publish a per-file checksum alongside these stdprod",
        "files.  The SHA256 values above pin the exact bytes downloaded on the",
        "production run and are checked by `download.sh`.",
        "",
        "## Response and background",
        "",
        f"* response: {rsp.get('channels_ebounds', '')} PHA channels, "
        f"{rsp.get('energy_bins', '')} energy bins, "
        f"{rsp.get('energy_range_keV', ['', ''])[0]:.2f}-"
        f"{rsp.get('energy_range_keV', ['', ''])[1]:.2f} keV.",
        "* The RSP HISTORY records `marfrmf 3.2.6`: the five individual PCU",
        "  RMFs were summed and multiplied by the 5-PCU ARF.  No synthetic",
        "  response is used.",
        f"* background: `{bg.get('name', '')}` is the official PCA background",
        "  **model** (`b2`), not a measured background spectrum.  XSPEC",
        "  subtracts it and propagates its `STAT_ERR`.  The background model",
        "  systematics are not included in the statistical errors; this is the",
        "  dominant caveat for PCA line measurements.",
        f"* exposure: {src.get('exposure_s', '')} s; source counts "
        f"{src.get('counts_total', '')}; background counts "
        f"{bg.get('counts_total', '')}; net counts "
        f"{run['observation'].get('net_counts', '')}.",
        "",
        "## Software",
        "",
        f"* XSPEC: {run['software'].get('xspec_version', '')}",
        f"* HEASoft: `{run['software'].get('heasoft', '')}`",
        f"* PyXspec: `{run['software'].get('pyxspec_path', '')}`",
        f"* Python: {run['software'].get('python', '')}",
        "",
        "## Raw vs PPS/PPS-equivalent caveat",
        "",
        "The `stdprod` products are the official PCA screening/reduction",
        "products.  Re-running `pcabackest`/`saextrct` from the raw PCA event",
        "files would change the good-time intervals, the background model and",
        "the response generation; it would not be the same dataset.  This tool",
        "therefore fits the official products and states that choice explicitly.",
        "It does not claim to reproduce the RXTE PCA reduction chain.",
        "",
    ]
    path.write_text("\n".join(lines))


def write_summary(path: Path, run: dict):
    r = run["results"]
    primary = r["line_3_20"]
    cross = r["line_3_10"]
    lines = [
        f"RXTE/PCA Fe K-alpha summary - {run['source']['name']}",
        f"ObsID {run['source']['obs_id']}, z={run['source']['redshift']}, "
        f"exposure {run['observation']['exposure_s']:.0f} s",
        "",
        "Production band 3-20 keV, tbabs*(zpowerlw+zgauss), narrow line:",
        f"  chi2/dof = {primary['chi2']:.2f}/{primary['dof']} = {primary['rchi2']:.3f}",
        f"  Gamma = {primary['gamma'][0]:.4f} +/- {primary['gamma'][1]:.4f}",
        f"  N_H = ({primary['nH'][0]:.4f} +/- {primary['nH'][1]:.4f}) x 1e22 cm^-2",
        f"  Delta chi2 = {primary['delta_chi2']:.2f} for {primary['delta_dof']} dof"
        f" -> {primary['significance_sigma']:.2f} sigma",
        f"  line flux = ({primary['flux']:.3e} +/- {primary['flux_err']:.2e})"
        " erg cm^-2 s^-1",
        f"  EW_rest = {primary['ew_rest_keV']*1000:.1f} eV",
        "",
        "Line-band cross-check 3-10 keV:",
        f"  chi2/dof = {cross['chi2']:.2f}/{cross['dof']} = {cross['rchi2']:.3f}",
        f"  Gamma = {cross['gamma'][0]:.4f} +/- {cross['gamma'][1]:.4f}",
        f"  N_H = ({cross['nH'][0]:.4f} +/- {cross['nH'][1]:.4f}) x 1e22 cm^-2",
        f"  Delta chi2 = {cross['delta_chi2']:.2f} -> "
        f"{cross['significance_sigma']:.2f} sigma",
        f"  line flux = ({cross['flux']:.3e} +/- {cross['flux_err']:.2e})"
        " erg cm^-2 s^-1",
        f"  EW_rest = {cross['ew_rest_keV']*1000:.1f} eV",
        "",
        "Caveats:",
        "  * PPS/stdprod products, no pcabackest/saextrct reduction.",
        "  * b2 is a background model; its systematics are not in the errors.",
        "  * A single absorbed power law is not a complete PCA continuum model.",
        "",
    ]
    path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--source-key", default="")
    p.add_argument("--redshift", type=float, default=None)
    p.add_argument("--source-name", default=None)
    p.add_argument("--source", default=None, help="override source PHA")
    p.add_argument("--background", default=None, help="override background PHA")
    p.add_argument("--response", default=None, help="override response RMF")
    args = p.parse_args(argv)

    t0 = time.time()
    input_dir = Path(args.input_dir).resolve()
    out = Path(args.out).resolve()
    config_dir = Path(args.config).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((config_dir / "config.json").read_text())
    if args.redshift is not None:
        cfg["redshift"] = float(args.redshift)
    if args.source_name:
        cfg["source_name"] = args.source_name
    if args.source:
        cfg.setdefault("products", {})["source"] = args.source
    if args.background:
        cfg.setdefault("products", {})["background"] = args.background
    if args.response:
        cfg.setdefault("products", {})["response"] = args.response
    if not input_dir.exists():
        raise FileNotFoundError(f"input directory not found: {input_dir}")

    # Full XSPEC log in the output directory.
    Xset.openLog(str(out / "xspec.log"))
    Xset.logChatter = int(cfg.get("log_chatter", 10))

    products = discover_products(input_dir, cfg)
    for role, path in products.items():
        if not Path(path).exists():
            raise FileNotFoundError(f"{role} not found: {path}")
    prepared = prepare_inputs(products, out / "prepared")

    src_prov = header_provenance(prepared["source"])
    bg_prov = header_provenance(prepared["background"])
    rsp_prov = response_provenance(prepared["response"])
    net_counts = src_prov.get("counts_total", 0.0) - bg_prov.get("counts_total", 0.0)

    results = fit_all(prepared, cfg)
    stat_crosscheck = statistic_crosscheck(prepared, cfg)

    # Attach line metrics and Delta-chi2 to the fit dictionaries.
    baseline_map = {
        "baseline_3_20": "baseline_3_20",
        "line_3_20": "baseline_3_20",
        "baseline_3_20_fixed_nH": "baseline_3_20_fixed_nH",
        "line_3_20_fixed_nH": "baseline_3_20_fixed_nH",
        "baseline_3_20_soft_excess": "baseline_3_20_soft_excess",
        "line_3_20_soft_excess": "baseline_3_20_soft_excess",
        "baseline_3_10": "baseline_3_10",
        "line_3_10": "baseline_3_10",
        "line_3_10_free_sigma": "baseline_3_10",
        "line_3_10_free_energy": "baseline_3_10",
    }
    metrics = {}
    for fit_id, fit in results.items():
        if not fit["line"]:
            continue
        base = results[baseline_map[fit_id]]
        met = line_metrics(fit, base, cfg)
        fit["delta_chi2"] = met["delta_chi2"]
        fit["delta_dof"] = met["delta_dof"]
        fit["significance_sigma"] = met["significance_sigma"]
        fit["detected"] = met["detected"]
        fit["flux"] = met["flux"]
        fit["flux_err"] = met["flux_err"]
        fit["ew_rest_keV"] = met["ew_rest_keV"]
        fit["ew_obs_keV"] = met["ew_obs_keV"]
        metrics[fit_id] = met

    # CSV tables.
    fit_rows = []
    for fit_id, fit in results.items():
        met = metrics.get(fit_id)
        notes = ""
        if fit_id == "baseline_3_20":
            notes = "production continuum baseline"
        elif fit_id == "line_3_20":
            notes = "production Fe K-alpha fit (narrow 50 eV rest)"
        elif fit_id == "baseline_3_20_fixed_nH":
            notes = "conservative baseline: N_H frozen"
        elif fit_id == "line_3_20_fixed_nH":
            notes = "conservative Fe K-alpha fit: N_H frozen to continuum value"
        elif fit_id == "baseline_3_20_soft_excess":
            notes = "continuum-systematic baseline: soft blackbody excess"
        elif fit_id == "line_3_20_soft_excess":
            notes = "continuum-systematic check: soft blackbody + Fe K-alpha"
        elif fit_id == "baseline_3_10":
            notes = "line-band continuum baseline"
        elif fit_id == "line_3_10":
            notes = "line-band Fe K-alpha cross-check (narrow)"
        elif fit_id == "line_3_10_free_sigma":
            notes = "diagnostic: free Gaussian width"
        elif fit_id == "line_3_10_free_energy":
            notes = "diagnostic: free width and centroid"
        fit_rows.append(fit_row(fit, met, notes))
    write_csv(out / "rxte_fit.csv", FIT_FIELDS, fit_rows)

    line_rows = []
    for fit_id, met in metrics.items():
        fit = results[fit_id]
        if fit_id == "line_3_20":
            interp = ("production narrow Fe K-alpha; background-inclusive "
                      "chi-square")
        elif fit_id == "line_3_20_fixed_nH":
            interp = ("conservative narrow-line measurement with N_H fixed "
                      "to the continuum fit")
        elif fit_id == "line_3_20_soft_excess":
            interp = ("continuum-systematic check with a soft blackbody; "
                      "not the production model")
        elif fit_id == "line_3_10":
            interp = ("line-band cross-check where the simple power law "
                      "describes the continuum")
        elif fit_id == "line_3_10_free_sigma":
            interp = ("diagnostic free width; width is not a resolved "
                      "velocity measurement")
        elif fit_id == "line_3_10_free_energy":
            interp = "diagnostic free centroid and width"
        else:
            interp = ""
        line_rows.append(line_row(fit, met, interp, baseline_map[fit_id]))
    write_csv(out / "rxte_lines.csv", LINE_FIELDS, line_rows)

    # Figures use the production 3-20 fit and its 3-20 baseline.
    primary = results["line_3_20"]
    primary_base = results["baseline_3_20"]
    plot_main(primary, primary_base, out / "rxte_spectrum_model_residual.png",
              out / "rxte_spectrum_model_residual.pdf", cfg)
    plot_zoom(primary, primary_base, out / "rxte_fe_ka_zoom.png",
              out / "rxte_fe_ka_zoom.pdf", cfg)

    # Provenance and run metadata.
    inputs = {}
    for role in ("source", "background", "response"):
        path = prepared["raw"][role]
        entry = {
            "name": path.name,
            "path": str(path.relative_to(input_dir)) if path.is_relative_to(input_dir) else str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "decompressed": str(prepared[role].relative_to(out)),
            "decompressed_sha256": sha256(prepared[role]),
        }
        inputs[role] = entry
    inputs["source"].update(src_prov)
    inputs["background"].update(bg_prov)
    inputs["response"].update(rsp_prov)

    archive_url = cfg.get(
        "archive_url",
        "https://heasarc.gsfc.nasa.gov/FTP/xte/data/archive/")
    run = {
        "tool": "rxte_xspec",
        "tool_version": TOOL_VERSION,
        "created_utc": now_utc(),
        "source": {
            "name": cfg.get("source_name", src_prov.get("object", "")),
            "key": args.source_key or input_dir.parent.parent.name,
            "obs_id": cfg.get("obs_id", input_dir.name.replace("rxte_", "")),
            "redshift": float(cfg["redshift"]),
            "ra_deg": src_prov.get("ra_obj_deg"),
            "dec_deg": src_prov.get("dec_obj_deg"),
            "archive_url": archive_url,
        },
        "observation": {
            "telescope": src_prov.get("telescope"),
            "instrument": src_prov.get("instrument"),
            "date_obs": src_prov.get("date_obs"),
            "exposure_s": src_prov.get("exposure_s"),
            "channels": src_prov.get("channels"),
            "source_counts": src_prov.get("counts_total"),
            "background_counts": bg_prov.get("counts_total"),
            "net_counts": net_counts,
            "net_count_rate_s": (net_counts / src_prov["exposure_s"]
                                 if src_prov.get("exposure_s") else None),
            "background_is_model": True,
        },
        "inputs": inputs,
        "software": software_versions(),
        "container": {
            "image": os.environ.get("RXTE_XSPEC_IMAGE", "rxte_xspec"),
            "image_size_bytes": int(os.environ.get("RXTE_XSPEC_IMAGE_SIZE", "0") or 0),
            "repo_commit": os.environ.get("RXTE_XSPEC_REPO_COMMIT", ""),
            "base_image": "xmm_xspec:latest",
        },
        "config": cfg,
        "statistic_crosscheck": stat_crosscheck,
        "results": {},
        "headline": {},
        "runtime_s": None,
        "caveats": [
            "The HEASARC stdprod PCA products are official reduced products; "
            "pcabackest/saextrct were not run.",
            "b2.pha is a PCA background model, not a measured background; its "
            "systematic uncertainty is not included in the chi-square errors.",
            "A single absorbed power law is not a complete PCA continuum model; "
            "the 3-20 keV reduced chi-square is >1.",
            "The Fe K-alpha significance is a relative Delta-chi-square for a "
            "line at a fixed rest energy; it is not a look-elsewhere-corrected "
            "discovery significance.",
            "Fe K-alpha flux and EW are model-dependent and assume the "
            "tbabs*zpowerlw continuum.",
        ],
    }
    for fit_id, fit in results.items():
        clean = {k: v for k, v in fit.items() if k != "plot"}
        clean["line_metrics"] = metrics.get(fit_id)
        run["results"][fit_id] = clean
    run["headline"] = {
        "primary_fit": "line_3_20",
        "chi2": primary["chi2"],
        "dof": primary["dof"],
        "rchi2": primary["rchi2"],
        "gamma": primary["gamma"][0],
        "gamma_err": primary["gamma"][1],
        "nH_1e22": primary["nH"][0],
        "nH_err_1e22": primary["nH"][1],
        "fe_ka_delta_chi2": primary["delta_chi2"],
        "fe_ka_significance_sigma": primary["significance_sigma"],
        "fe_ka_detected": primary["detected"],
        "fe_ka_flux_erg_cm2_s": primary["flux"],
        "fe_ka_flux_err": primary["flux_err"],
        "fe_ka_ew_rest_keV": primary["ew_rest_keV"],
        "line_band_crosscheck_delta_chi2": results["line_3_10"]["delta_chi2"],
        "line_band_crosscheck_significance_sigma":
            results["line_3_10"]["significance_sigma"],
        "line_band_crosscheck_flux_erg_cm2_s": results["line_3_10"]["flux"],
        "line_band_crosscheck_ew_rest_keV":
            results["line_3_10"]["ew_rest_keV"],
    }
    run["runtime_s"] = time.time() - t0

    (out / "run.json").write_text(json.dumps(run, indent=2, default=str) + "\n")
    cfg_effective = dict(cfg)
    cfg_effective.update({
        "source_key": run["source"]["key"],
        "input_dir": str(input_dir),
        "output_dir": str(out),
        "config_dir": str(config_dir),
        "prepared": {k: str(v.relative_to(out)) for k, v in prepared.items()
                     if isinstance(v, Path)},
        "command": " ".join(sys.argv),
    })
    (out / "config.effective.json").write_text(
        json.dumps(cfg_effective, indent=2, default=str) + "\n")
    write_provenance(out / "provenance.md", run)
    write_summary(out / "fit_summary.txt", run)
    try:
        Xset.closeLog()
    except Exception:
        pass

    print(f"wrote {out}")
    print(f"primary chi2/dof = {primary['chi2']:.2f}/{primary['dof']} "
          f"= {primary['rchi2']:.3f}")
    print(f"Fe K-alpha Delta chi2 = {primary['delta_chi2']:.2f} "
          f"({primary['significance_sigma']:.2f} sigma), "
          f"flux = {primary['flux']:.3e} erg/cm2/s, "
          f"EW_rest = {primary['ew_rest_keV']*1000:.1f} eV")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
