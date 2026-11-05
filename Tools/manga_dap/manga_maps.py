#!/usr/bin/env python3
"""Shared MaNGA DAP MAPS helpers: line extraction, BPT classes and figures.

This module contains no fitting code.  It reads the official DAP MAPS data
model (Westfall et al. 2019; Belfiore et al. 2019) and provides the small set
of derived quantities used by both the production runner and the independent
comparison to the published MAPS.

Units follow the DAP: Gaussian line fluxes are 1e-17 erg/s/cm^2/spaxel,
velocities and velocity dispersions are km/s, and equivalent widths are
Angstrom.  No extinction correction is applied anywhere.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from matplotlib import pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

# DAP channels used throughout.  Names are the values of the C01..C35 header
# keywords in EMLINE_GFLUX; they are stable across DAP versions.
LINE_KEYS = {
    "ha": "Ha-6564",
    "hb": "Hb-4862",
    "oiii_5007": "OIII-5008",
    "oiii_4959": "OIII-4960",
    "nii_6584": "NII-6585",
    "nii_6548": "NII-6549",
    "sii_6716": "SII-6718",
    "sii_6731": "SII-6732",
    "oi_6300": "OI-6302",
    "oi_6364": "OI-6365",
}
KEY_LINES = ("ha", "hb", "oiii_5007", "nii_6584", "sii_6716", "sii_6731")
CLASS_NAMES = ("unclassified", "star_forming", "composite", "seyfert", "liner",
               "agn_unclassified")
CLASS_COLORS = ("#bdbdbd", "#2c7bb6", "#abd9e9", "#d7191c", "#fdae61", "#984ea3")
CLASS_CMAP = ListedColormap(CLASS_COLORS)
CLASS_NORM = BoundaryNorm(np.arange(-0.5, len(CLASS_NAMES) + 0.5), len(CLASS_NAMES))


# ---------------------------------------------------------------------------
# small I/O helpers
# ---------------------------------------------------------------------------
def jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, np.ndarray):
        return jsonable(obj.tolist())
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        value = float(obj)
        return None if (math.isnan(value) or math.isinf(value)) else value
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
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
    fields = fieldnames or list(rows[0].keys())
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def md5_file(path: Path, chunk: int = 1024 * 1024) -> str:
    digest = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# MAPS reading
# ---------------------------------------------------------------------------
def get_line_names(hdul) -> list[str]:
    """Read the C01..C35 line labels from EMLINE_GFLUX."""
    header = hdul["EMLINE_GFLUX"].header
    names = []
    for i in range(1, 200):
        key = f"C{i:02d}"
        if key not in header:
            break
        names.append(str(header[key]).strip())
    if not names:
        raise ValueError("No C01..Cnn line labels found in EMLINE_GFLUX")
    return names


def load_maps(path: Path) -> dict:
    """Load the MAPS arrays needed for line measurements and figures."""
    path = Path(path)
    with fits.open(path, memmap=False) as hdul:
        names = get_line_names(hdul)
        data = {
            "path": str(path),
            "line_names": names,
            "prihdr": dict(hdul[0].header),
            "linehdr": dict(hdul["EMLINE_GFLUX"].header),
            "gflux": hdul["EMLINE_GFLUX"].data.astype(float),
            "gflux_ivar": hdul["EMLINE_GFLUX_IVAR"].data.astype(float),
            "gflux_mask": hdul["EMLINE_GFLUX_MASK"].data.astype(np.int32),
            "gvel": hdul["EMLINE_GVEL"].data.astype(float),
            "gvel_ivar": hdul["EMLINE_GVEL_IVAR"].data.astype(float),
            "gvel_mask": hdul["EMLINE_GVEL_MASK"].data.astype(np.int32),
            "gsigma": hdul["EMLINE_GSIGMA"].data.astype(float),
            "gsigma_ivar": hdul["EMLINE_GSIGMA_IVAR"].data.astype(float),
            "gsigma_mask": hdul["EMLINE_GSIGMA_MASK"].data.astype(np.int32),
            "gew": hdul["EMLINE_GEW"].data.astype(float),
            "gew_ivar": hdul["EMLINE_GEW_IVAR"].data.astype(float),
            "gew_mask": hdul["EMLINE_GEW_MASK"].data.astype(np.int32),
            "sflux": hdul["EMLINE_SFLUX"].data.astype(float),
            "sflux_ivar": hdul["EMLINE_SFLUX_IVAR"].data.astype(float),
            "sflux_mask": hdul["EMLINE_SFLUX_MASK"].data.astype(np.int32),
            "stellar_vel": hdul["STELLAR_VEL"].data.astype(float),
            "stellar_vel_ivar": hdul["STELLAR_VEL_IVAR"].data.astype(float),
            "stellar_vel_mask": hdul["STELLAR_VEL_MASK"].data.astype(np.int32),
            "stellar_sigma": hdul["STELLAR_SIGMA"].data.astype(float),
            "stellar_sigma_ivar": hdul["STELLAR_SIGMA_IVAR"].data.astype(float),
            "stellar_sigma_mask": hdul["STELLAR_SIGMA_MASK"].data.astype(np.int32),
            "spx_snr": hdul["SPX_SNR"].data.astype(float),
            "binid": hdul["BINID"].data.astype(np.int32),
            "skycoo": hdul["SPX_SKYCOO"].data.astype(float),
        }
        try:
            data["binned_snr"] = hdul["BIN_SNR"].data.astype(float)
        except KeyError:
            data["binned_snr"] = None
        try:
            data["sasuke_mask"] = hdul["SASUKE_MASK"].data.astype(np.int32)
        except KeyError:
            data["sasuke_mask"] = None
        # WCS for the spaxel grid (2D, arcsec offsets are also available).
        data["wcs"] = WCS(hdul["EMLINE_GFLUX"].header, naxis=2)
        # Convert every pixel to RA/Dec once.
        ny, nx = data["gflux"].shape[1:]
        yy, xx = np.mgrid[0:ny, 0:nx]
        ra, dec = data["wcs"].pixel_to_world_values(xx, yy)
        data["ra"] = np.asarray(ra, dtype=float)
        data["dec"] = np.asarray(dec, dtype=float)
    return data


def line_index(maps: dict, key: str) -> int:
    name = LINE_KEYS[key]
    try:
        return maps["line_names"].index(name)
    except ValueError as exc:
        raise KeyError(f"line {name!r} not in MAPS; available={maps['line_names']}") from exc


def line_arrays(maps: dict, key: str):
    i = line_index(maps, key)
    flux = maps["gflux"][i]
    ivar = maps["gflux_ivar"][i]
    mask = maps["gflux_mask"][i]
    good = (mask == 0) & (ivar > 0) & np.isfinite(flux)
    err = np.full_like(flux, np.nan, dtype=float)
    err[good] = 1.0 / np.sqrt(ivar[good])
    out = np.where(good, flux, np.nan)
    return out, err, good


def key_fluxes(maps: dict) -> dict:
    """Return key-line flux, error and validity arrays plus ratio diagnostics."""
    out = {}
    for key in KEY_LINES + ("oi_6300", "oi_6364", "nii_6548", "oiii_4959"):
        flux, err, good = line_arrays(maps, key)
        out[key] = flux
        out[f"{key}_err"] = err
        out[f"{key}_good"] = good
    # [S II] total and [O I] total.  Errors are added in quadrature, which is
    # exact for independent measurements but ignores covariance between the
    # two lines in the same DAP fit (documented limitation).
    for total, parts in (("sii_total", ("sii_6716", "sii_6731")),
                         ("oi_total", ("oi_6300", "oi_6364"))):
        f1, f2 = out[parts[0]], out[parts[1]]
        e1, e2 = out[f"{parts[0]}_err"], out[f"{parts[1]}_err"]
        out[total] = np.where(np.isfinite(f1) & np.isfinite(f2), f1 + f2, np.nan)
        out[f"{total}_err"] = np.sqrt(np.nan_to_num(e1) ** 2 + np.nan_to_num(e2) ** 2)
        out[f"{total}_good"] = out[f"{parts[0]}_good"] & out[f"{parts[1]}_good"]
    # Ratios and analytic errors.
    for key, (num, den) in {
        "o3_hb": ("oiii_5007", "hb"),
        "n2_ha": ("nii_6584", "ha"),
        "s2_ha": ("sii_total", "ha"),
        "oi_ha": ("oi_total", "ha"),
        "ha_hb": ("ha", "hb"),
    }.items():
        out[key] = ratio_with_error(out[num], out[f"{num}_err"],
                                    out[den], out[f"{den}_err"])[0]
        out[f"{key}_err"] = ratio_with_error(out[num], out[f"{num}_err"],
                                             out[den], out[f"{den}_err"])[1]
    classes, codes, s2_sub, oi_sub = classify_bpt(out["o3_hb"], out["n2_ha"],
                                                  out["s2_ha"], out["oi_ha"])
    out["bpt_class"] = classes
    out["bpt_code"] = codes
    out["seyfert_liner_s2"] = s2_sub
    out["seyfert_liner_oi"] = oi_sub
    return out


def ratio_with_error(num: np.ndarray, num_err: np.ndarray,
                     den: np.ndarray, den_err: np.ndarray):
    good = (np.isfinite(num) & np.isfinite(den) & np.isfinite(num_err)
            & np.isfinite(den_err) & (num > 0) & (den > 0))
    ratio = np.full_like(num, np.nan, dtype=float)
    err = np.full_like(num, np.nan, dtype=float)
    ratio[good] = num[good] / den[good]
    err[good] = ratio[good] * np.sqrt((num_err[good] / num[good]) ** 2
                                      + (den_err[good] / den[good]) ** 2)
    return ratio, err, good


def classify_bpt(o3_hb: np.ndarray, n2_ha: np.ndarray,
                 s2_ha: np.ndarray | None = None,
                 oi_ha: np.ndarray | None = None):
    """Classify spaxels with the standard N2-BPT and Seyfert/LINER boundaries.

    N2-BPT: Kauffmann et al. (2003) star-forming limit and Kewley et al.
    (2001) AGN limit.  Seyfert/LINER: Kewley et al. (2006) [S II] and [O I]
    divisions.  A spaxel is left ``agn_unclassified`` if it is an AGN by N2
    but the S II (or O I) ratio is unavailable.
    """
    # The inputs are linear line ratios; the BPT boundaries are defined in
    # log10.  Convert here so every caller uses the same convention.
    n2 = np.asarray(n2_ha, dtype=float)
    o3 = np.asarray(o3_hb, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        x = np.where(n2 > 0, np.log10(n2), np.nan)
        y = np.where(o3 > 0, np.log10(o3), np.nan)
    finite = np.isfinite(x) & np.isfinite(y)
    classes = np.full(x.shape, "unclassified", dtype=object)
    codes = np.zeros(x.shape, dtype=np.int16)
    s2_sub = np.full(x.shape, "", dtype=object)
    oi_sub = np.full(x.shape, "", dtype=object)
    if not np.any(finite):
        return classes, codes, s2_sub, oi_sub

    ka = 0.61 / (x - 0.05) + 1.30
    ke = 0.61 / (x - 0.47) + 1.19
    sf = finite & (y < ka)
    comp = finite & (y >= ka) & (y < ke)
    agn = finite & (y >= ke)
    classes[sf] = "star_forming"
    codes[sf] = 1
    classes[comp] = "composite"
    codes[comp] = 2
    classes[agn] = "agn_unclassified"
    codes[agn] = 5

    if s2_ha is not None:
        s2_lin = np.asarray(s2_ha, dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            s2 = np.where(s2_lin > 0, np.log10(s2_lin), np.nan)
        s2_ok = np.isfinite(s2)
        liner = agn & s2_ok & (y > 1.05 + 0.45 * s2)
        seyfert = agn & s2_ok & ~(y > 1.05 + 0.45 * s2)
        classes[seyfert] = "seyfert"
        codes[seyfert] = 3
        classes[liner] = "liner"
        codes[liner] = 4
        s2_sub[seyfert] = "seyfert"
        s2_sub[liner] = "liner"
    if oi_ha is not None:
        oi_lin = np.asarray(oi_ha, dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            oi = np.where(oi_lin > 0, np.log10(oi_lin), np.nan)
        oi_ok = np.isfinite(oi)
        liner = agn & oi_ok & (y > 1.33 + 0.45 * oi)
        seyfert = agn & oi_ok & ~(y > 1.33 + 0.45 * oi)
        oi_sub[seyfert] = "seyfert"
        oi_sub[liner] = "liner"
    return classes, codes, s2_sub, oi_sub


def line_ew(maps: dict, key: str):
    """Return the DAP Gaussian equivalent width and its formal error."""
    i = line_index(maps, key)
    ew = maps["gew"][i]
    ivar = maps["gew_ivar"][i]
    mask = maps["gew_mask"][i]
    good = (mask == 0) & (ivar > 0) & np.isfinite(ew)
    out = np.where(good, ew, np.nan)
    err = np.full_like(out, np.nan, dtype=float)
    err[good] = 1.0 / np.sqrt(ivar[good])
    return out, err, good


def stellar_arrays(maps: dict):
    vel_ok = ((maps["stellar_vel_mask"] == 0) & (maps["stellar_vel_ivar"] > 0)
              & np.isfinite(maps["stellar_vel"]))
    sig_ok = ((maps["stellar_sigma_mask"] == 0) & (maps["stellar_sigma_ivar"] > 0)
              & np.isfinite(maps["stellar_sigma"]))
    vel = np.where(vel_ok, maps["stellar_vel"], np.nan)
    sig = np.where(sig_ok, maps["stellar_sigma"], np.nan)
    vel_err = np.full_like(vel, np.nan)
    sig_err = np.full_like(sig, np.nan)
    vel_err[vel_ok] = 1.0 / np.sqrt(maps["stellar_vel_ivar"][vel_ok])
    sig_err[sig_ok] = 1.0 / np.sqrt(maps["stellar_sigma_ivar"][sig_ok])
    return vel, vel_err, sig, sig_err


def line_kinematics(maps: dict, key: str):
    i = line_index(maps, key)
    v = maps["gvel"][i]
    vi = maps["gvel_ivar"][i]
    vm = maps["gvel_mask"][i]
    s = maps["gsigma"][i]
    si = maps["gsigma_ivar"][i]
    sm = maps["gsigma_mask"][i]
    vgood = (vm == 0) & (vi > 0) & np.isfinite(v)
    sgood = (sm == 0) & (si > 0) & np.isfinite(s)
    # The fast fixed-continuum product retains the original SASUKE quality
    # mask.  Reject NEAR_BOUND / FIT_FAILED / MATHERROR (bits 6-8) for the
    # kinematics only; the fluxes remain usable.
    if maps.get("sasuke_mask") is not None:
        bad = (maps["sasuke_mask"][i] & 0b111000000) != 0
        vgood &= ~bad
        sgood &= ~bad
    vout = np.where(vgood, v, np.nan)
    sout = np.where(sgood, s, np.nan)
    verr = np.full_like(vout, np.nan)
    serr = np.full_like(sout, np.nan)
    verr[vgood] = 1.0 / np.sqrt(vi[vgood])
    serr[sgood] = 1.0 / np.sqrt(si[sgood])
    return vout, verr, sout, serr


# ---------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------
def robust_compare(ours: np.ndarray, ours_err: np.ndarray,
                   ref: np.ndarray, ref_err: np.ndarray,
                   require_positive: bool = True) -> dict:
    """Compare two per-spaxel arrays and return robust, reproducible metrics."""
    ours = np.asarray(ours, dtype=float)
    ref = np.asarray(ref, dtype=float)
    good = np.isfinite(ours) & np.isfinite(ref)
    if require_positive:
        good &= (ours > 0) & (ref > 0)
    n = int(np.sum(good))
    out = {"n": n, "n_total": int(ours.size)}
    if n < 3:
        out.update({"status": "insufficient_overlap"})
        return out
    a = ours[good]
    b = ref[good]
    ratio = a / b
    frac = (a - b) / b
    out.update({
        "status": "ok",
        "median_ratio": float(np.median(ratio)),
        "ratio_p16": float(np.percentile(ratio, 16)),
        "ratio_p84": float(np.percentile(ratio, 84)),
        "median_frac_diff": float(np.median(frac)),
        "frac_diff_mad": float(1.4826 * np.median(np.abs(frac - np.median(frac)))),
        "frac_diff_p16": float(np.percentile(frac, 16)),
        "frac_diff_p84": float(np.percentile(frac, 84)),
        "pearson_r": float(np.corrcoef(a, b)[0, 1]),
        "median_ours": float(np.median(a)),
        "median_ref": float(np.median(b)),
    })
    slope, intercept = np.polyfit(b, a, 1)
    out["linear_slope"] = float(slope)
    out["linear_intercept"] = float(intercept)
    if ours_err is not None and ref_err is not None:
        ea = np.asarray(ours_err, dtype=float)[good]
        eb = np.asarray(ref_err, dtype=float)[good]
        eok = np.isfinite(ea) & np.isfinite(eb) & (ea > 0) & (eb > 0)
        if np.sum(eok) > 2:
            er = ea[eok] / eb[eok]
            out["n_error"] = int(np.sum(eok))
            out["median_error_ratio"] = float(np.median(er))
            out["error_ratio_p16"] = float(np.percentile(er, 16))
            out["error_ratio_p84"] = float(np.percentile(er, 84))
            pull = (a[eok] - b[eok]) / np.sqrt(ea[eok] ** 2 + eb[eok] ** 2)
            out["pull_median"] = float(np.median(pull))
            out["pull_scatter"] = float(1.4826 * np.median(np.abs(pull - np.median(pull))))
            out["pull_rms"] = float(np.sqrt(np.mean(pull ** 2)))
    return out


def kinematic_compare(ours: np.ndarray, ours_err: np.ndarray,
                     ref: np.ndarray, ref_err: np.ndarray) -> dict:
    """Compare two kinematic maps (velocities or dispersions)."""
    ours = np.asarray(ours, dtype=float)
    ref = np.asarray(ref, dtype=float)
    good = np.isfinite(ours) & np.isfinite(ref)
    n = int(np.sum(good))
    out = {"n": n, "n_total": int(ours.size)}
    if n < 3:
        out["status"] = "insufficient_overlap"
        return out
    a = ours[good]
    b = ref[good]
    diff = a - b
    med = float(np.median(diff))
    out.update({
        "status": "ok",
        "median_offset": med,
        "offset_mad": float(1.4826 * np.median(np.abs(diff - med))),
        "scatter": float(1.4826 * np.median(np.abs(diff - med))),
        "p16": float(np.percentile(diff, 16)),
        "p84": float(np.percentile(diff, 84)),
        "pearson_r": float(np.corrcoef(a, b)[0, 1]),
        "median_ours": float(np.median(a)),
        "median_ref": float(np.median(b)),
    })
    if ours_err is not None and ref_err is not None:
        ea = np.asarray(ours_err, dtype=float)[good]
        eb = np.asarray(ref_err, dtype=float)[good]
        eok = np.isfinite(ea) & np.isfinite(eb) & (ea > 0) & (eb > 0)
        if np.sum(eok) > 2:
            er = ea[eok] / eb[eok]
            pull = (a[eok] - b[eok]) / np.sqrt(ea[eok] ** 2 + eb[eok] ** 2)
            out.update({
                "n_error": int(np.sum(eok)),
                "median_error_ratio": float(np.median(er)),
                "error_ratio_p16": float(np.percentile(er, 16)),
                "error_ratio_p84": float(np.percentile(er, 84)),
                "pull_median": float(np.median(pull)),
                "pull_scatter": float(1.4826 * np.median(np.abs(pull - np.median(pull)))),
                "pull_rms": float(np.sqrt(np.mean(pull ** 2))),
            })
    return out


def bpt_agreement(ours: dict, ref: dict) -> dict:
    co = ours["bpt_class"]
    cr = ref["bpt_class"]
    valid = (co != "unclassified") & (cr != "unclassified")
    n = int(np.sum(valid))
    out = {"n": n, "n_ours_classified": int(np.sum(co != "unclassified")),
           "n_ref_classified": int(np.sum(cr != "unclassified"))}
    if n == 0:
        out["status"] = "insufficient_overlap"
        return out
    out["status"] = "ok"
    out["agreement_fraction"] = float(np.mean(co[valid] == cr[valid]))
    out["agreement_fraction_agn_vs_sf"] = float(np.mean(
        _agn_group(co[valid]) == _agn_group(cr[valid])))
    labels = list(CLASS_NAMES)
    matrix = []
    for a in labels:
        row = []
        for b in labels:
            row.append(int(np.sum((co[valid] == a) & (cr[valid] == b))))
        matrix.append(row)
    out["confusion_matrix_labels"] = labels
    out["confusion_matrix"] = matrix
    for name in ("star_forming", "composite", "seyfert", "liner", "agn_unclassified"):
        out[f"n_ours_{name}"] = int(np.sum(co[valid] == name))
        out[f"n_ref_{name}"] = int(np.sum(cr[valid] == name))
    return out


def _agn_group(classes: np.ndarray) -> np.ndarray:
    out = np.full(classes.shape, "other", dtype=object)
    out[np.isin(classes, ["star_forming"])] = "star_forming"
    out[np.isin(classes, ["composite"])] = "composite"
    out[np.isin(classes, ["seyfert", "liner", "agn_unclassified"])] = "agn"
    return out


def bpt_fractions(classes: np.ndarray) -> dict:
    valid = classes != "unclassified"
    n = int(np.sum(valid))
    out = {"n_classified": n, "n_total": int(classes.size)}
    if n == 0:
        return out
    for name in CLASS_NAMES[1:]:
        out[name] = int(np.sum(classes[valid] == name))
        out[f"{name}_fraction"] = float(np.mean(classes[valid] == name))
    return out


def summary_stats(values: np.ndarray) -> dict:
    values = np.asarray(values, dtype=float)
    good = np.isfinite(values)
    if np.sum(good) < 1:
        return {"n": 0}
    v = values[good]
    return {"n": int(v.size), "median": float(np.median(v)),
            "p16": float(np.percentile(v, 16)), "p84": float(np.percentile(v, 84)),
            "min": float(np.min(v)), "max": float(np.max(v))}


# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------
def _extent(maps: dict):
    x = maps["skycoo"][0]
    y = maps["skycoo"][1]
    return [float(np.nanmin(x)), float(np.nanmax(x)),
            float(np.nanmin(y)), float(np.nanmax(y))]


def _show(ax, image, extent, title, cmap="viridis", vmin=None, vmax=None,
          label=None, origin="lower"):
    im = ax.imshow(image, origin=origin, extent=extent, cmap=cmap,
                   vmin=vmin, vmax=vmax, interpolation="nearest")
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("arcsec", fontsize=8)
    ax.set_ylabel("arcsec", fontsize=8)
    ax.tick_params(labelsize=7)
    if label:
        cb = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
        cb.set_label(label, fontsize=7)
        cb.ax.tick_params(labelsize=6)
    return im


def plot_maps(maps: dict, out_png: Path, title_prefix: str = "MaNGA DAP"):
    """Pedagogical 3x3 panel of the DAP's key products."""
    f = key_fluxes(maps)
    sv, sve, ss, sse = stellar_arrays(maps)
    extent = _extent(maps)
    fig, axes = plt.subplots(3, 3, figsize=(13.5, 12.5))
    panels = [
        (f["ha"], "H-alpha (Gaussian)", "1e-17 erg/s/cm2/spaxel", "magma"),
        (f["hb"], "H-beta (Gaussian)", "1e-17 erg/s/cm2/spaxel", "magma"),
        (f["oiii_5007"], "[O III] 5007 (Gaussian)", "1e-17 erg/s/cm2/spaxel", "magma"),
        (f["nii_6584"], "[N II] 6584 (Gaussian)", "1e-17 erg/s/cm2/spaxel", "magma"),
        (f["sii_total"], "[S II] 6716+6731 (Gaussian)", "1e-17 erg/s/cm2/spaxel", "magma"),
        (f["ha_hb"], "H-alpha / H-beta (observed)", "ratio", "coolwarm"),
        (sv, "Stellar velocity", "km/s", "RdBu_r"),
        (ss, "Stellar velocity dispersion", "km/s", "viridis"),
        (maps["spx_snr"], "Continuum S/N per spaxel", "S/N", "viridis"),
    ]
    for ax, (image, title, label, cmap) in zip(axes.ravel(), panels):
        # Symmetric velocity scale and a finite Balmer-decrement scale.  A
        # handful of spaxels with near-zero H-beta would otherwise dominate
        # the colour bar at 10^3.
        vmin = vmax = None
        if title == "Stellar velocity":
            lim = float(np.nanpercentile(np.abs(image), 95)) if np.any(np.isfinite(image)) else 50.0
            vmin, vmax = -max(lim, 5.0), max(lim, 5.0)
        if title.startswith("H-alpha / H-beta"):
            image = np.where(np.isfinite(image) & (image > 0) & (image < 20), image, np.nan)
            vmin, vmax = 2.0, 8.0
        _show(ax, image, extent, title, cmap=cmap, vmin=vmin, vmax=vmax, label=label)
        ax.set_aspect("equal")
    fig.suptitle(f"{title_prefix}: MAPS products for NGC 1194 (9193-12701)", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_png.with_suffix(".pdf"))
    plt.close(fig)


def plot_bpt(maps: dict, out_png: Path, title: str = "MaNGA DAP BPT"):
    """BPT diagram and spatial ionization-class map."""
    f = key_fluxes(maps)
    x = np.log10(f["n2_ha"])
    y = np.log10(f["o3_hb"])
    good = np.isfinite(x) & np.isfinite(y) & (f["n2_ha"] > 0) & (f["o3_hb"] > 0)
    classes = f["bpt_class"]
    codes = f["bpt_code"]
    extent = _extent(maps)

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.8),
                             gridspec_kw={"width_ratios": [1.05, 1.0]})
    ax = axes[0]
    # Dense scatter, colored by class.
    order = [1, 2, 3, 4, 5]
    for code, color, label in zip(order, CLASS_COLORS[1:], CLASS_NAMES[1:]):
        use = good & (codes == code)
        if not np.any(use):
            continue
        ax.scatter(x[use], y[use], s=7, c=color, label=label, alpha=0.75,
                   edgecolors="none")
    xs = np.linspace(-2.5, 0.45, 400)
    ka = 0.61 / (xs - 0.05) + 1.30
    ke = 0.61 / (xs - 0.47) + 1.19
    ax.plot(xs, ka, "k--", lw=1.2, label="Kauffmann+2003")
    ax.plot(xs, ke, "k-", lw=1.2, label="Kewley+2001")
    ax.set_xlim(-2.5, 0.45)
    ax.set_ylim(-1.5, 1.6)
    ax.set_xlabel(r"$\log_{10}$([N II] 6584 / H$\alpha$)")
    ax.set_ylabel(r"$\log_{10}$([O III] 5007 / H$\beta$)")
    ax.set_title("N2-BPT diagram (per spaxel)", fontsize=10)
    ax.legend(fontsize=7, loc="upper left", frameon=True)
    ax.grid(alpha=0.2)

    ax = axes[1]
    im = ax.imshow(np.where(good, codes, 0), origin="lower", extent=extent,
                   cmap=CLASS_CMAP, norm=CLASS_NORM, interpolation="nearest")
    ax.set_aspect("equal")
    ax.set_title("Ionization class map", fontsize=10)
    ax.set_xlabel("arcsec")
    ax.set_ylabel("arcsec")
    handles = [Patch(facecolor=CLASS_COLORS[i], label=CLASS_NAMES[i])
               for i in range(1, len(CLASS_NAMES))]
    ax.legend(handles=handles, fontsize=7, loc="upper right", framealpha=0.9)
    fig.suptitle(title + " (NGC 1194, 9193-12701)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_png.with_suffix(".pdf"))
    plt.close(fig)


def plot_spectrum_fit(spectra: dict, out_png: Path, title: str):
    """Plot the observed, stellar, emission-line and total DAP models.

    ``spectra`` must contain wave, flux, error, model, emline, stellar and
    the spaxel coordinates/name selected by the caller.
    """
    wave = spectra["wave"]
    fig, axes = plt.subplots(2, 2, figsize=(14, 8.5))
    windows = [(4820, 5050, "H-beta + [O III]"), (6450, 6800, "H-alpha + [N II] + [S II]")]
    for row, (lo, hi, label) in enumerate(windows):
        sel = (wave >= lo) & (wave <= hi)
        ax = axes[row, 0]
        ax.plot(wave[sel], spectra["flux"][sel], color="k", lw=1.0, label="observed (DAP binned)")
        ax.plot(wave[sel], spectra["model"][sel], color="C0", lw=1.2, label="total model")
        ax.plot(wave[sel], spectra["stellar"][sel], color="C2", lw=1.0, alpha=0.8,
                label="stellar continuum")
        ax.plot(wave[sel], spectra["emline"][sel], color="C3", lw=1.0, alpha=0.9,
                label="emission-line model")
        ax.set_xlabel("observed wavelength (A)")
        ax.set_ylabel("flux (1e-17 erg/s/cm2/A/spaxel)")
        ax.set_title(label)
        ax.legend(fontsize=7)
        ax.grid(alpha=0.2)
        ax = axes[row, 1]
        resid = spectra["flux"] - spectra["model"]
        ax.plot(wave[sel], resid[sel], color="C1", lw=1.0, label="data - model")
        ax.axhline(0, color="k", lw=0.6, ls=":")
        ax.set_xlabel("observed wavelength (A)")
        ax.set_ylabel("residual")
        ax.set_title(label + " residual")
        ax.legend(fontsize=7)
        ax.grid(alpha=0.2)
    fig.suptitle(title, fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_png.with_suffix(".pdf"))
    plt.close(fig)


def plot_comparison_scatter(ours: dict, ref: dict, out_png: Path,
                            title: str = "DAP 4.5.0 vs published DAP 3.1.0"):
    """2x3 flux scatter for the key lines, with 1:1 and fitted lines."""
    fig, axes = plt.subplots(2, 3, figsize=(14, 9))
    for ax, key, label in zip(axes.ravel(), KEY_LINES,
                              ("H-alpha", "H-beta", "[O III] 5007", "[N II] 6584",
                               "[S II] 6716", "[S II] 6731")):
        a = ours[key]
        b = ref[key]
        good = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
        if np.sum(good) < 3:
            ax.set_title(label + " (no overlap)")
            continue
        x = b[good]
        y = a[good]
        # Use a log-log density display; the dynamic range is large.
        ax.hexbin(x, y, gridsize=55, bins="log", cmap="Blues", mincnt=1)
        lim = [max(np.percentile(x, 0.5), 1e-3), np.percentile(x, 99.5) * 1.5]
        ax.plot(lim, lim, "k--", lw=1.0, label="1:1")
        slope, intercept = np.polyfit(x, y, 1)
        ax.plot(np.array(lim), slope * np.array(lim) + intercept, "C3-", lw=1.0,
                label=f"fit {slope:.3f}x+{intercept:.3g}")
        med = np.median(y / x)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.set_xlabel("published MAPS flux (1e-17)")
        ax.set_ylabel("this DAP run flux (1e-17)")
        ax.set_title(f"{label}: N={np.sum(good)}, median ratio={med:.3f}", fontsize=9)
        ax.legend(fontsize=7, loc="upper left")
    fig.suptitle(title, fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_png.with_suffix(".pdf"))
    plt.close(fig)


def plot_comparison_residual_maps(ours: dict, ref: dict, out_png: Path,
                                  title: str = "DAP flux residual maps",
                                  extent: list | None = None):
    """Fractional difference maps for H-alpha, [O III], [N II] and H-beta."""
    if extent is None:
        extent = _extent(ours)
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 10))
    for ax, key, label in zip(axes.ravel(), ("ha", "hb", "oiii_5007", "nii_6584"),
                              ("H-alpha", "H-beta", "[O III] 5007", "[N II] 6584")):
        a = ours[key]
        b = ref[key]
        good = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
        frac = np.where(good, (a - b) / b, np.nan)
        lim = 0.25
        im = ax.imshow(frac, origin="lower", extent=extent, cmap="RdBu_r",
                       vmin=-lim, vmax=lim, interpolation="nearest")
        ax.set_aspect("equal")
        ax.set_title(f"{label}: (ours - published)/published", fontsize=9)
        ax.set_xlabel("arcsec")
        ax.set_ylabel("arcsec")
        cb = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
        cb.set_label("fractional difference", fontsize=8)
        med = np.nanmedian(frac)
        ax.text(0.03, 0.97, f"median={med:+.3f}", transform=ax.transAxes,
                va="top", fontsize=8, bbox=dict(fc="white", alpha=0.7, lw=0))
    fig.suptitle(title, fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_png.with_suffix(".pdf"))
    plt.close(fig)


def plot_comparison_kinematics(ours_v, ours_ve, ours_s, ours_se,
                               ref_v, ref_ve, ref_s, ref_se, out_png: Path,
                               title: str = "DAP kinematics comparison"):
    fig, axes = plt.subplots(2, 2, figsize=(11, 9.5))
    for ax, (a, b, label, unit) in zip(
            axes.ravel(),
            [(ours_v, ref_v, "Stellar velocity", "km/s"),
             (ours_s, ref_s, "Stellar sigma", "km/s"),
             (ours_v, ref_v, "Gas velocity (H-alpha)", "km/s"),
             (ours_s, ref_s, "Gas sigma (H-alpha)", "km/s")]):
        good = np.isfinite(a) & np.isfinite(b)
        if np.sum(good) < 3:
            ax.set_title(label + " (no overlap)")
            continue
        ax.hexbin(b[good], a[good], gridsize=50, bins="log", cmap="Blues", mincnt=1)
        lo = min(np.percentile(b[good], 1), np.percentile(a[good], 1))
        hi = max(np.percentile(b[good], 99), np.percentile(a[good], 99))
        ax.plot([lo, hi], [lo, hi], "k--", lw=1.0)
        med = np.median(a[good] - b[good])
        scat = 1.4826 * np.median(np.abs((a[good] - b[good]) - med))
        ax.set_title(f"{label}: offset={med:+.2f}, scatter={scat:.2f} {unit}", fontsize=9)
        ax.set_xlabel("published MAPS " + unit)
        ax.set_ylabel("this DAP run " + unit)
    fig.suptitle(title, fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_png.with_suffix(".pdf"))
    plt.close(fig)


def plot_comparison_bpt(ours: dict, ref: dict, out_png: Path,
                        title: str = "BPT comparison"):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6))
    for ax, maps, name in ((axes[0], ours, "this DAP run (4.5.0)"),
                           (axes[1], ref, "published MAPS (3.1.0)")):
        f = key_fluxes(maps)
        x = np.log10(f["n2_ha"])
        y = np.log10(f["o3_hb"])
        good = np.isfinite(x) & np.isfinite(y) & (f["n2_ha"] > 0) & (f["o3_hb"] > 0)
        codes = f["bpt_code"]
        for code, color, label in zip([1, 2, 3, 4, 5], CLASS_COLORS[1:], CLASS_NAMES[1:]):
            use = good & (codes == code)
            if np.any(use):
                ax.scatter(x[use], y[use], s=5, c=color, alpha=0.65,
                           edgecolors="none", label=label)
        xs = np.linspace(-2.5, 0.45, 400)
        ax.plot(xs, 0.61 / (xs - 0.05) + 1.30, "k--", lw=1.0)
        ax.plot(xs, 0.61 / (xs - 0.47) + 1.19, "k-", lw=1.0)
        ax.set_xlim(-2.5, 0.45)
        ax.set_ylim(-1.5, 1.6)
        ax.set_xlabel(r"$\log_{10}$([N II]/H$\alpha$)")
        ax.set_ylabel(r"$\log_{10}$([O III]/H$\beta$)")
        ax.set_title(name, fontsize=10)
        ax.grid(alpha=0.2)
    axes[0].legend(fontsize=7, loc="upper left")
    fig.suptitle(title + " (NGC 1194)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_png.with_suffix(".pdf"))
    plt.close(fig)
