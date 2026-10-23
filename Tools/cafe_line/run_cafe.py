#!/usr/bin/env python3
"""CAFE spectral decomposition for JWST/MIRI MRS spectra (Docker tool).

This is the production driver around the upstream CAFE fitter
(https://github.com/GOALS-survey/CAFE, pinned commit).  It

* reads the canonical ``inputs/<source>/raw/*_x1d.fits`` products through
  :mod:`read_jwst_x1d` (never copying the input into the output directory),
* builds an *effective* configuration from ``--config`` + ``--tables`` and
  masks line/PAH features that fall in zeroed detector gaps,
* runs the CAFE/lmfit decomposition (trust-region reflective least squares),
* performs one robust outlier-clipping pass and refits,
* writes the native CAFE products plus harmonised line/continuum/PAH tables,
* and runs a post-fit multivariate-normal Monte Carlo from the lmfit
  covariance (explicitly labelled ``lmfit_covariance``; this is **not** an
  MCMC).

The most important caveat for the committed PDS 456 test is that the
canonical x1d files only contain the MRS "L" sub-bands; the [Ne II] 12.81,
[Ne III] 15.56 and [S III] 18.71 lines fall in the zeroed gaps.  The driver
reports those lines as ``not_covered`` rather than fitting interpolated
continuum across the gap.
"""
from __future__ import annotations

import argparse
import copy
import datetime as _dt
import hashlib
import json
import math
import os
import re
import shutil
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Ellipse
import astropy.units as u
from astropy.nddata import StdDevUncertainty
from specutils import Spectrum1D

import CAFE
from CAFE.cafe_io import cafe_io
from CAFE.cafe_helper import (
    CAFE_param_generator,
    CAFE_prof_generator,
    CAFE_cube_generator,
    parobj2parcube,
)
from CAFE.cafe import specmod, cafe_grinder
from CAFE.cafe_lib import mask_spec, get_model_fluxes, get_feat_pars, cafeplot

sys.path.insert(0, str(Path(__file__).resolve().parent))
from read_jwst_x1d import (build_spectrum, write_cafe_text, sha256,  # noqa: E402
                           find_segments)

class ForceAllError(RuntimeError):
    """Raised when CAFE cannot construct its force_all line parameter set."""


C_UM_S = 2.99792458e14          # micron / s
C_KMS = 2.99792458e5
GAUSS_INT = 1.0 / np.sqrt(np.pi * np.log(2.0))   # CAFE's Gaussian normalisation
DRUDE_INT = np.pi / 2.0

# PAH complex windows copied from CAFE/cafe_io.py (cafe_io.pah_table).
PAH_COMPLEX_RANGES = {
    "PAH33": (3.25, 3.32),
    "ali34": (3.35, 3.44),
    "ali345": (3.45, 3.50),
    "PAH62": (6.2, 6.3),
    "PAH77_C": (7.3, 7.9),
    "PAH83": (8.3, 8.4),
    "PAH86": (8.6, 8.7),
    "PAH113_C": (11.2, 11.4),
    "PAH120": (11.9, 12.1),
    "PAH126_C": (12.6, 12.7),
    "PAH136": (13.4, 13.6),
    "PAH142": (14.1, 14.2),
    "PAH164": (16.4, 16.5),
    "PAH170_C": (16.4, 17.9),
    "PAH174": (17.35, 17.45),
}
PAH_CENTRAL = {
    "PAH33": 3.29, "ali34": 3.40, "ali345": 3.48, "PAH62": 6.22,
    "PAH77_C": 7.6, "PAH83": 8.33, "PAH86": 8.61, "PAH113_C": 11.3,
    "PAH120": 11.99, "PAH126_C": 12.65, "PAH136": 13.5, "PAH142": 14.19,
    "PAH164": 16.45, "PAH170_C": 17.0, "PAH174": 17.4,
}

# Key science lines.  ``cafe_base`` is the CAFE parameter name without the
# trailing N/B component suffix (see CAFE.cafe_lib.get_feat_pars).
KEY_LINES = [
    ("NeII_12.81", 12.813550, "NeII_128136", "narrow"),
    ("NeIII_15.56", 15.555100, "NeIII_155551", "narrow+broad"),
    ("SIII_18.71", 18.713000, "SIII_187130", "narrow"),
    ("SIII_33.48", 33.481000, "SIII_334810", "narrow"),
    ("NeV_14.32", 14.321700, "NeV_143217", "narrow+broad"),
    ("NeV_24.32", 24.317500, "NeV_243175", "narrow+broad"),
    ("NeVI_7.65", 7.652400, "NeVI_76524", "narrow+broad"),
    ("ArIII_8.99", 8.991380, "ArIII_89914", "narrow+broad"),
    ("SIV_10.51", 10.510500, "SIV_105105", "narrow+broad"),
    ("ArV_13.10", 13.102200, "ArV_131022", "narrow"),
    ("ClII_14.37", 14.367800, "ClII_143678", "narrow"),
    ("FeII_17.94", 17.935950, "FeII_179359", "narrow"),
    ("ArIII_21.83", 21.830200, "ArIII_218302", "narrow"),
    ("FeIII_22.93", 22.925000, "FeIII_229250", "narrow"),
    ("H2_S1_17.03", 17.035000, "H200S1_170350", "narrow"),
    ("H2_S2_12.28", 12.279000, "H200S2_122790", "narrow"),
    ("H2_S3_9.66", 9.664900, "H200S3_96649", "narrow"),
    ("H2_S4_8.03", 8.025800, "H200S4_80258", "narrow"),
    ("H2_S5_6.91", 6.909100, "H200S5_69091", "narrow"),
    ("H2_S6_6.11", 6.108800, "H200S6_61088", "narrow"),
]
KEY_PAHS = [
    ("PAH_3.3", "PAH33", 3.29),
    ("PAH_6.2", "PAH62", 6.22),
    ("PAH_7.7", "PAH77_C", 7.60),
    ("PAH_8.6", "PAH86", 8.61),
    ("PAH_11.3", "PAH113_C", 11.30),
    ("PAH_12.7", "PAH126_C", 12.65),
    ("PAH_13.5", "PAH136", 13.50),
    ("PAH_14.2", "PAH142", 14.19),
    ("PAH_17.0", "PAH170_C", 17.00),
]
KEY_RATIOS = [
    ("NeIII_15.56/NeII_12.81", "line", "NeIII_155551", "line", "NeII_128136"),
    ("SIII_18.71/SIII_33.48", "line", "SIII_187130", "line", "SIII_334810"),
    ("PAH_6.2/PAH_11.3", "pah", "PAH62", "pah", "PAH113_C"),
    ("PAH_7.7/PAH_6.2", "pah", "PAH77_C", "pah", "PAH62"),
    ("PAH_8.6/PAH_6.2", "pah", "PAH86", "pah", "PAH62"),
    ("H2_S3/PAH_6.2", "line", "H200S3_96649", "pah", "PAH62"),
    ("NeV_14.32/NeV_24.32", "line", "NeV_143217", "line", "NeV_243175"),
]


# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------
class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_stem(text: str) -> str:
    """CAFE strips everything after the last '.', so remove dots."""
    text = str(text).replace(".", "p").replace("+", "p")
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text)
    return text.strip("_") or "cafe_spectrum"


def json_default(obj):
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (pd.DataFrame, pd.Series)):
        return obj.to_dict()
    return str(obj)


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=json_default) + "\n")


def relative_to(path: Path, root: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve()))
    except Exception:
        return str(path)


def _segment_mask(wave: np.ndarray, segments) -> np.ndarray:
    """Boolean mask for a list of index pairs (kept for internal use)."""
    m = np.zeros(len(wave), dtype=bool)
    for a, b in segments:
        m[a:b] = True
    return m


def _coverage_mask(wave: np.ndarray, segments_um) -> np.ndarray:
    """Boolean mask for a list of observed-frame segment dicts."""
    m = np.zeros(len(wave), dtype=bool)
    for seg in segments_um:
        m |= (wave >= float(seg["start"])) & (wave <= float(seg["stop"]))
    return m


def is_covered(obs_um: float, segments_um) -> bool:
    return any(float(s["start"]) <= float(obs_um) <= float(s["stop"])
               for s in segments_um)


def _pah_complex_for_wave(wave: float):
    for name, (lo, hi) in PAH_COMPLEX_RANGES.items():
        if lo <= wave < hi:
            return name
    return None


def _sum_component_rows(table: pd.DataFrame, base: str, z: float):
    """Sum narrow+broad CAFE line rows for one base name."""
    if table is None or len(table) == 0:
        return None
    names = []
    for name in table.index:
        s = str(name)
        if s == base or s == base + "N" or s == base + "B":
            names.append(name)
    if not names:
        return None
    sub = table.loc[names]
    def col(name):
        if name not in sub:
            return np.full(len(sub), np.nan)
        return pd.to_numeric(sub[name], errors="coerce").to_numpy(dtype=float)
    int_flux = float(np.nansum(col("line_strength_int")))
    obs_flux = float(np.nansum(col("line_strength_obs")))
    int_err = float(np.sqrt(np.nansum(col("line_strength_int_unc") ** 2)))
    obs_err = float(np.sqrt(np.nansum(col("line_strength_obs_unc") ** 2)))
    rest = _nanmedian(col("line_lam"))
    gamma = _nanmedian(col("line_gamma"))
    peak = float(np.nansum(col("line_peak")))
    return {
        "rows": list(names), "n_components": len(names),
        "rest_um": rest, "obs_um": rest * (1.0 + z),
        "flux_int": int_flux, "flux_int_err": int_err,
        "flux_obs": obs_flux, "flux_obs_err": obs_err,
        "gamma": gamma, "peak_jy": peak,
    }


def _as_float(value):
    try:
        out = float(value)
        return out if np.isfinite(out) else float("nan")
    except Exception:
        return float("nan")


def _nanmedian(values):
    arr = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(dtype=float)
    good = np.isfinite(arr)
    return float(np.median(arr[good])) if good.any() else float("nan")


def _snr(flux, err):
    try:
        flux = float(flux); err = float(err)
        if np.isfinite(flux) and np.isfinite(err) and err > 0:
            return flux / err
    except Exception:
        pass
    return float("nan")


def _feature_status(flux, err, covered: bool) -> str:
    if not covered:
        return "not_covered"
    flux = _as_float(flux)
    err = _as_float(err)
    if not np.isfinite(flux):
        return "not_in_model"
    if flux == 0.0:
        return "fixed_at_zero"
    if np.isfinite(err) and err > 10.0 * abs(flux):
        return "unconstrained"
    snr = _snr(flux, err)
    if np.isfinite(snr) and snr >= 3.0:
        return "detected"
    if np.isfinite(snr) and snr >= 2.0:
        return "marginal"
    return "not_detected"


def _upper_limit_combine(local_ul, flux_err):
    vals = [v for v in (local_ul, 3.0 * flux_err if np.isfinite(flux_err) else np.nan)
            if np.isfinite(v)]
    return float(max(vals)) if vals else float("nan")


def _pah_rows(table: pd.DataFrame, complex_name: str):
    if table is None or len(table) == 0 or complex_name not in table.index:
        return None
    row = table.loc[complex_name]
    return {
        "flux_int": _as_float(row.get("pah_strength_int", np.nan)),
        "flux_int_err": _as_float(row.get("pah_strength_int_unc", np.nan)),
        "flux_obs": _as_float(row.get("pah_strength_obs", np.nan)),
        "flux_obs_err": _as_float(row.get("pah_strength_obs_unc", np.nan)),
        "eqw_um": _as_float(row.get("pah_complex_eqw", np.nan)),
        "rest_um": PAH_CENTRAL.get(complex_name, float("nan")),
    }


# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------
def _find_tables(config: Path, tables: Path | None) -> Path:
    candidates = []
    if tables is not None:
        candidates.append(Path(tables))
    candidates += [config.parent / "tables", config / "tables"]
    for c in candidates:
        if (c / "lines.atomic_AGN.txt").exists() and \
                (c / "resolving_power").is_dir():
            return c.resolve()
    raise FileNotFoundError(
        "CAFE tables directory not found.  Pass --tables or place the tables "
        f"next to the config; tried: {[str(c) for c in candidates]}"
    )


def _copy_tables(src: Path, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns("*.png", "*.jpg", "*.jpeg", "*~")
    for item in sorted(src.iterdir()):
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=ignore, dirs_exist_ok=True)
        elif item.suffix.lower() not in (".png", ".jpg", ".jpeg") \
                and not item.name.endswith("~"):
            shutil.copy2(item, target)


def _rewrite_mask_table(src: Path, dst: Path, wave_col: int, mask_col: int,
                        z: float, segments_um, margin: float = 0.0):
    out = []
    n_total = n_masked = 0
    for line in src.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            out.append(line)
            continue
        parts = stripped.split()
        try:
            wave = float(parts[wave_col])
        except Exception:
            out.append(line)
            continue
        n_total += 1
        obs = wave * (1.0 + z)
        keep = any(float(s["start"]) - margin <= obs <= float(s["stop"]) + margin
                   for s in segments_um)
        if not keep:
            parts[mask_col] = "1"
            n_masked += 1
        out.append("   ".join(parts))
    dst.write_text("\n".join(out) + "\n")
    return n_total, n_masked


def _trim_pah_table(src: Path, dst: Path, z: float, segments_um,
                    margin: float = 0.0):
    rows, n_total = [], 0
    for line in src.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        parts = stripped.split()
        if len(parts) < 4:
            continue
        try:
            wave = float(parts[0])
        except Exception:
            continue
        n_total += 1
        obs = wave * (1.0 + z)
        if any(float(s["start"]) - margin <= obs <= float(s["stop"]) + margin
               for s in segments_um):
            rows.append("   ".join(parts))
    dst.write_text("; PAH table trimmed to the observed spectral coverage\n"
                   + "\n".join(rows) + ("\n" if rows else ""))
    return n_total, len(rows)


def _set_opt_value(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"(?mi)^\s*{re.escape(key)}\s*=.*$")
    repl = f"{key} = {value}"
    if pattern.search(text):
        return pattern.sub(repl, text, count=1)
    # append to [FIT OPTIONS] / [SWITCHES] / [MODEL OPTIONS] block
    return text


def prepare_effective_config(config: Path, tables: Path, z: float,
                             segments_um, work_dir: Path,
                             fit_lines: bool, fit_pahs: bool,
                             max_loops: int, error_floor: float,
                             coverage_mask: bool = True,
                             margin_um: float = 0.0,
                             ftol: float | None = None) -> dict:
    config = Path(config).resolve()
    inpar = config / "inpars.ini"
    opt = config / "default_opt.cafe"
    if not inpar.exists():
        raise FileNotFoundError(f"missing CAFE ini: {inpar}")
    if not opt.exists():
        raise FileNotFoundError(f"missing CAFE opt: {opt}")

    eff = Path(work_dir) / "config_effective"
    if eff.exists():
        shutil.rmtree(eff)
    (eff / "tables").mkdir(parents=True)

    shutil.copy2(inpar, eff / "inpars.ini")
    opt_text = opt.read_text()
    tables = _find_tables(config, tables)
    _copy_tables(tables, eff / "tables")
    # CAFE concatenates tablePath with 'opacity/...', so keep the trailing slash.
    opt_text = re.sub(r"(?mi)^\s*tabpath\s*=.*$",
                      f"tabpath = '{eff / 'tables'}/'", opt_text, count=1)
    opt_text = _set_opt_value(opt_text, "ErrSpec", f"{float(error_floor):.6g}")
    opt_text = _set_opt_value(opt_text, "MAX_LOOPS", str(int(max_loops)))
    opt_text = _set_opt_value(opt_text, "FitLINs", str(bool(fit_lines)))
    opt_text = _set_opt_value(opt_text, "FitPAHs", str(bool(fit_pahs)))
    if ftol is not None:
        opt_text = _set_opt_value(opt_text, "ftol", f"{float(ftol):.6g}")
    (eff / "default_opt.cafe").write_text(opt_text)

    line_info = {}
    if coverage_mask:
        for fname, wc, mc in [
            ("lines.atomic_AGN.txt", 1, 3),
            ("lines.molecular_AGN.txt", 1, 2),
            ("lines.H_recombination_AGN.txt", 1, 2),
        ]:
            src = eff / "tables" / fname
            if src.exists():
                n, m = _rewrite_mask_table(src, src, wc, mc, z, segments_um,
                                           margin=margin_um)
                line_info[fname] = {"n_rows": n, "n_masked_by_coverage": m}
        pah_src = eff / "tables" / "pah_template.txt"
        if pah_src.exists():
            n, kept = _trim_pah_table(pah_src, pah_src, z, segments_um,
                                      margin=margin_um)
            line_info["pah_template.txt"] = {"n_rows": n, "n_kept": kept}
            if kept == 0 and fit_pahs:
                # Keep the full table so CAFE's PAH-reference guesser can run,
                # but turn the PAH component off.
                shutil.copy2(tables / "pah_template.txt", pah_src)
                opt_text = _set_opt_value(opt_text, "FitPAHs", "False")
                (eff / "default_opt.cafe").write_text(opt_text)
                line_info["pah_template.txt"]["fallback"] = (
                    "no PAH in coverage; FitPAHs=False, full table retained"
                )

    return {
        "config": str(config),
        "tables": str(tables),
        "effective_dir": str(eff),
        "inpars": str(eff / "inpars.ini"),
        "opt": str(eff / "default_opt.cafe"),
        "tabpath": str(eff / "tables") + "/",
        "line_tables": line_info,
        "sha256": {
            "inpars.ini": sha256(inpar),
            "default_opt.cafe": sha256(opt),
            "tables": {p.name: sha256(p) for p in sorted(tables.glob("*"))
                       if p.is_file() and p.suffix.lower() not in
                       (".png", ".jpg", ".jpeg")},
        },
    }


def copy_config_used(eff: dict, out_dir: Path):
    dst = Path(out_dir) / "config_used"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    shutil.copy2(eff["inpars"], dst / "inpars.ini")
    shutil.copy2(eff["opt"], dst / "default_opt.cafe")
    for name in ("lines.atomic_AGN.txt", "lines.molecular_AGN.txt",
                 "lines.H_recombination_AGN.txt", "pah_template.txt"):
        src = Path(eff["tabpath"]) / name
        if src.exists():
            shutil.copy2(src, dst / name)
    write_json(dst / "tables_manifest.json", {
        "source_tables": eff["tables"],
        "note": ("Only the effective ini/opt and the line/PAH tables are "
                 "copied here; the unchanged opacity/resolving-power/SED "
                 "tables live in configs/cafe_line/tables and are listed "
                 "with hashes in the run.json config block."),
        "line_tables": eff["line_tables"],
    })


# ---------------------------------------------------------------------------
# fit driving
# ---------------------------------------------------------------------------
def _make_spec_object(spec_path: Path, z: float, config: dict):
    cafe_path = os.path.dirname(CAFE.__file__) + "/"
    s = specmod(cafe_path)
    s.read_spec(spec_path.name, file_dir=str(spec_path.parent) + "/", z=z)
    wave, flux, unc, bandname, mask = mask_spec(s)
    spec = Spectrum1D(spectral_axis=wave * u.micron, flux=flux * u.Jy,
                      uncertainty=StdDevUncertainty(unc), redshift=s.z)
    spec_dict = {"wave": wave, "flux": flux, "flux_unc": unc,
                 "weight": 1.0 / unc ** 2}
    s.spec_dict = spec_dict
    s.phot_dict = None
    s.fitphot = False
    s.inparfile = config["inpars"]
    s.optfile = config["opt"]
    s.inpars = cafe_io().read_inifile(config["inpars"])
    s.inopts = cafe_io().read_inifile(config["opt"])
    return s, spec, spec_dict


def fit_once(spec_path: Path, z: float, config: dict, native_root: Path,
             force_all_lines: bool, max_loops: int,
             segments_um=None) -> dict:
    t0 = time.time()
    cafe_path = os.path.dirname(CAFE.__file__) + "/"
    s, spec, spec_dict = _make_spec_object(spec_path, z, config)
    s.inopts["FIT OPTIONS"]["MAX_LOOPS"] = int(max_loops)

    param_gen = CAFE_param_generator(spec, config["inpars"], config["opt"],
                                     cafe_path=cafe_path)
    _, out_path = cafe_io().init_paths(
        s.inopts, cafe_path=cafe_path, file_name=s.result_file_name,
        output_path=str(native_root) + "/")
    out_path = Path(out_path)

    all_params = param_gen.make_parobj(get_all=True)
    parcube = CAFE_cube_generator(s).make_parcube(all_params)
    try:
        init_params = param_gen.make_parobj(force_all=force_all_lines)
    except ValueError as exc:
        # CAFE's force_all branch needs at least one positive line guess.
        if force_all_lines:
            raise ForceAllError(
                "CAFE force_all line initialisation failed (no positive "
                "line guess); the line set would be silently dropped"
            ) from exc
        raise
    prof_gen = CAFE_prof_generator(spec, config["inpars"], config["opt"],
                                   None, cafe_path=cafe_path)
    s.cont_profs = prof_gen.make_cont_profs()

    result = cafe_grinder(s, init_params, spec_dict, None)
    runtime = time.time() - t0

    s.params = result.params
    s.parcube = parobj2parcube(result.params, parcube)
    comp_fluxes, comp_fluxes_0, ext_comps, e0, tau0, vgrad = get_model_fluxes(
        s.params, s.spec_dict["wave"], s.cont_profs, comps=True)
    s.compdict = {
        "CompFluxes": comp_fluxes,
        "CompFluxes_0": comp_fluxes_0,
        "extComps": ext_comps,
        "e0": e0,
        "tau0": tau0,
    }
    if segments_um is None:
        obs_wave = np.asarray(spec_dict["wave"], float) * (1.0 + z)
        seg_idx = find_segments(obs_wave)
        segments_um = [
            {"start": float(obs_wave[a]),
             "stop": float(obs_wave[b - 1]), "n": int(b - a)}
            for a, b in seg_idx
        ]
    else:
        segments_um = [dict(s) for s in segments_um]
    return {
        "specmod": s, "result": result, "spec": spec,
        "native_dir": out_path, "runtime_s": runtime,
        "n_params_total": len(result.params),
        "n_params_free": int(result.nvarys),
        "wave": spec_dict["wave"], "flux": spec_dict["flux"],
        "err": spec_dict["flux_unc"], "segments_um": segments_um,
    }


def _model_and_residuals(fit: dict):
    s = fit["specmod"]
    model = get_model_fluxes(s.params, s.spec_dict["wave"], s.cont_profs)
    resid = s.spec_dict["flux"] - np.asarray(model, dtype=float)
    return np.asarray(model, dtype=float), resid


def outlier_mask(resid: np.ndarray, err: np.ndarray, sigma: float = 5.0,
                 rel_threshold: float = 0.10, flux=None) -> tuple:
    med = float(np.nanmedian(resid))
    mad = float(1.4826 * np.nanmedian(np.abs(resid - med)))
    # never let a too-good fit make the threshold absurdly small
    scale = max(mad, float(np.nanmedian(err)), 1e-30)
    bad_mad = np.abs(resid - med) > float(sigma) * scale
    if flux is not None and rel_threshold and rel_threshold > 0:
        bad_rel = np.abs(resid) > float(rel_threshold) * np.abs(flux)
        bad = bad_mad & bad_rel
    else:
        bad_rel = np.ones(len(resid), dtype=bool)
        bad = bad_mad
    return bad, {
        "median_residual_jy": med, "mad_jy": mad,
        "threshold_jy": float(sigma) * scale, "sigma": float(sigma),
        "rel_threshold": float(rel_threshold),
        "n_mad_candidates": int(bad_mad.sum()),
        "n_gross_candidates": int((bad_mad & bad_rel).sum()),
    }


def refit_with_mask(fit: dict, spec_path: Path, z: float, config: dict,
                    native_root: Path, force_all_lines: bool,
                    max_loops: int, out_spec: Path,
                    rel_threshold: float = 0.10) -> dict:
    s = fit["specmod"]
    _, resid = _model_and_residuals(fit)
    bad, info = outlier_mask(resid, fit["err"], rel_threshold=rel_threshold,
                             flux=fit["flux"])
    info["n_outliers"] = int(bad.sum())
    if bad.sum() == 0 or bad.sum() > 0.5 * len(bad):
        info["applied"] = False
        return fit, info
    wave = s.spec_dict["wave"]
    flux = s.spec_dict["flux"]
    err = s.spec_dict["flux_unc"]
    keep = ~bad
    write_cafe_text(out_spec, wave[keep], flux[keep], err[keep],
                    header=("CAFE input after 5-sigma residual clipping; "
                            "columns: wave_um flux_Jy flux_unc_Jy"))
    new_fit = fit_once(out_spec, z, config, native_root,
                       force_all_lines, max_loops,
                       segments_um=fit["segments_um"])
    info["applied"] = True
    info["masked_wave_um"] = [float(x) for x in wave[bad][:20]]
    return new_fit, info


def _stats(fit: dict, segments=None, outlier_info=None) -> dict:
    s = fit["specmod"]
    result = fit["result"]
    wave = s.spec_dict["wave"]
    flux = s.spec_dict["flux"]
    err = s.spec_dict["flux_unc"]
    model, resid = _model_and_residuals(fit)
    med_flux = float(np.nanmedian(np.abs(flux)))
    rms_rel = float(np.sqrt(np.nanmean(resid ** 2)) / max(med_flux, 1e-30))
    mad = float(1.4826 * np.nanmedian(np.abs(resid - np.nanmedian(resid))))
    stats = {
        "success": bool(result.success),
        "errorbars": bool(result.errorbars),
        "covariance_available": result.covar is not None,
        "message": str(result.message),
        "nfev": int(result.nfev),
        "ndata": int(result.ndata),
        "nvarys": int(result.nvarys),
        "nfree": int(result.nfree),
        "chi2": float(result.chisqr),
        "redchi": float(result.redchi),
        "aic": float(result.aic),
        "bic": float(result.bic),
        "rms_rel": rms_rel,
        "residual_mad_jy": mad,
        "median_abs_rel": float(np.nanmedian(np.abs(resid)) / max(med_flux, 1e-30)),
        "p95_abs_rel": float(np.nanpercentile(np.abs(resid), 95) / max(med_flux, 1e-30)),
        "n_pixels": int(len(wave)),
        "n_params_total": int(fit["n_params_total"]),
        "n_params_free": int(fit["n_params_free"]),
        "fit_runtime_s": float(fit["runtime_s"]),
        "method": "lmfit least_squares (trust region reflective)",
        "cafe_commit": os.environ.get("CAFE_COMMIT", ""),
        "cafe_version": _package_version("CAFE"),
    }
    at_bounds = []
    for name in result.params:
        par = result.params[name]
        # Keep varied parameters, and feature parameters that were fixed at a
        # non-zero bound by CAFE's post-fit checks (e.g. the broad [Ne V]
        # component in the PDS 456 fit).  Fixed continuum components at zero
        # are by design and would only add noise.
        if not par.vary:
            if not (str(name).startswith(("g_", "d_")) and abs(par.value) > 1e-30):
                continue
        hit = None
        if np.isfinite(par.min) and np.isclose(par.value, par.min,
                                               rtol=1e-4, atol=1e-8):
            hit = "min"
        elif np.isfinite(par.max) and np.isclose(par.value, par.max,
                                                 rtol=1e-4, atol=1e-8):
            hit = "max"
        if hit:
            at_bounds.append({"name": str(name), "bound": hit,
                              "value": float(par.value),
                              "min": float(par.min), "max": float(par.max)})
    stats["parameters_at_bounds"] = at_bounds
    if outlier_info is not None:
        stats["outlier_clip"] = outlier_info
    stats["stable"] = bool(stats["success"] and stats["rms_rel"] < 0.5
                           and stats["redchi"] < 100.0)
    return stats


def _package_version(name: str) -> str:
    try:
        from importlib.metadata import version
        return version(name)
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# native products
# ---------------------------------------------------------------------------
def save_native_products(fit: dict) -> dict:
    s = fit["specmod"]
    out = Path(fit["native_dir"])
    out.mkdir(parents=True, exist_ok=True)
    stem = s.result_file_name
    paths = {}
    cafeio = cafe_io()

    try:
        path = out / f"{stem}_parcube.fits"
        s.parcube.writeto(path, overwrite=True)
        paths["parcube"] = str(path)
    except Exception as exc:
        paths["parcube_error"] = f"{type(exc).__name__}: {exc}"

    try:
        cube_gen = CAFE_cube_generator(s)
        s.contcube = cube_gen.make_profcube(
            s.inparfile, s.optfile,
            prof_names={"fCon": ["Comp", "fCON"], "fDSK": ["Comp", "fDSK"],
                        "fHOT": ["Comp", "fHOT"]})
        path = out / f"{stem}_contcube.fits"
        s.contcube.writeto(path, overwrite=True)
        paths["contcube"] = str(path)
    except Exception as exc:
        paths["contcube_error"] = f"{type(exc).__name__}: {exc}"

    try:
        path = out / f"{stem}_fitpars.ini"
        cafeio.write_inifile(s.params, s.inpars, str(path))
        paths["fitpars"] = str(path)
    except Exception as exc:
        paths["fitpars_error"] = f"{type(exc).__name__}: {exc}"

    try:
        cafeio.save_asdf(s, file_name=str(out / f"{stem}_cafefit"))
        paths["asdf"] = str(out / f"{stem}_cafefit.asdf")
    except Exception as exc:
        paths["asdf_error"] = f"{type(exc).__name__}: {exc}"

    try:
        comp = s.compdict["CompFluxes"]
        gauss, drude, gauss_opc = get_feat_pars(s.params,
                                                apply_vgrad2waves=True)
        save_name = str(out / f"{stem}_fitfigure.png")
        fig = cafeplot(s.spec_dict, s.phot_dict, comp, gauss, drude,
                       vgrad=float(s.params["VGRAD"].value),
                       pahext=s.compdict["extComps"]["extPAH"],
                       save_name=save_name, params=s.params)
        paths["fitfigure"] = save_name
        if isinstance(fig, (list, tuple)):
            for f in fig:
                plt.close(f)
        else:
            plt.close(fig)
    except Exception as exc:
        paths["fitfigure_error"] = f"{type(exc).__name__}: {exc}"

    try:
        path = out / f"{stem}_pahtable.ecsv"
        s.pahtable = cafeio.pah_table(s.parcube, s.compdict, pah_obs=True,
                                      savetbl=str(path))
        paths["pahtable"] = str(path)
    except Exception as exc:
        s.pahtable = pd.DataFrame()
        paths["pahtable_error"] = f"{type(exc).__name__}: {exc}"

    try:
        path = out / f"{stem}_linetable.ecsv"
        s.linetable = cafeio.line_table(s.parcube, s.compdict,
                                        line_obs=True, savetbl=str(path))
        paths["linetable"] = str(path)
    except Exception as exc:
        s.linetable = pd.DataFrame()
        paths["linetable_error"] = f"{type(exc).__name__}: {exc}"

    return paths


# ---------------------------------------------------------------------------
# tables
# ---------------------------------------------------------------------------
def _line_table_dataframe(fit: dict, z: float) -> pd.DataFrame:
    s = fit["specmod"]
    tab = getattr(s, "linetable", None)
    if tab is None or len(tab) == 0:
        return pd.DataFrame(columns=[
            "line_name", "component", "base_name", "rest_um", "obs_um",
            "flux_int_w_m2", "flux_int_err_w_m2", "flux_obs_w_m2",
            "flux_obs_err_w_m2", "flux_int_erg_s_cm2",
            "flux_obs_erg_s_cm2", "fwhm_kms", "peak_jy", "snr_int",
            "snr_obs", "detected", "covered", "in_cafe_model", "note",
        ])
    rows = []
    for name, row in tab.iterrows():
        sname = str(name)
        comp = "broad" if sname.endswith("B") else (
            "narrow" if sname.endswith("N") else "unknown")
        base = sname[:-1] if comp in ("broad", "narrow") else sname
        rest = _as_float(row.get("line_lam", np.nan))
        obs = rest * (1.0 + z) if np.isfinite(rest) else np.nan
        fint = _as_float(row.get("line_strength_int", np.nan))
        fint_e = _as_float(row.get("line_strength_int_unc", np.nan))
        fobs = _as_float(row.get("line_strength_obs", np.nan))
        fobs_e = _as_float(row.get("line_strength_obs_unc", np.nan))
        gamma = _as_float(row.get("line_gamma", np.nan))
        snr = fint / fint_e if np.isfinite(fint_e) and fint_e > 0 else np.nan
        rows.append({
            "line_name": sname, "component": comp, "base_name": base,
            "rest_um": rest, "obs_um": obs,
            "flux_int_w_m2": fint, "flux_int_err_w_m2": fint_e,
            "flux_obs_w_m2": fobs, "flux_obs_err_w_m2": fobs_e,
            "flux_int_erg_s_cm2": fint * 1e3,
            "flux_obs_erg_s_cm2": fobs * 1e3,
            "fwhm_kms": gamma * C_KMS,
            "peak_jy": _as_float(row.get("line_peak", np.nan)),
            "snr_int": snr, "snr_obs": (fobs / fobs_e)
            if np.isfinite(fobs_e) and fobs_e > 0 else np.nan,
            "detected": bool(np.isfinite(snr) and snr >= 3.0 and fint > 0),
            "covered": bool(np.isfinite(obs) and is_covered(obs, fit["segments_um"])),
            "in_cafe_model": True,
            "status": _feature_status(fint, fint_e,
                                      bool(np.isfinite(obs) and
                                           is_covered(obs, fit["segments_um"]))),
            "note": "CAFE lmfit component",
        })
    return pd.DataFrame(rows)


def _pah_dataframe(fit: dict, z: float) -> pd.DataFrame:
    s = fit["specmod"]
    tab = getattr(s, "pahtable", None)
    if tab is None or len(tab) == 0:
        return pd.DataFrame(columns=[
            "pah_complex", "rest_um", "obs_um", "flux_int_w_m2",
            "flux_int_err_w_m2", "flux_obs_w_m2", "flux_obs_err_w_m2",
            "flux_int_erg_s_cm2", "eqw_um", "snr_int", "detected",
            "covered", "note",
        ])
    rows = []
    for name, row in tab.iterrows():
        cname = str(name)
        rest = float(PAH_CENTRAL.get(cname, np.nan))
        obs = rest * (1.0 + z) if np.isfinite(rest) else np.nan
        fint = _as_float(row.get("pah_strength_int", np.nan))
        fint_e = _as_float(row.get("pah_strength_int_unc", np.nan))
        fobs = _as_float(row.get("pah_strength_obs", np.nan))
        fobs_e = _as_float(row.get("pah_strength_obs_unc", np.nan))
        snr = fint / fint_e if np.isfinite(fint_e) and fint_e > 0 else np.nan
        eqw = row.get("pah_complex_eqw", np.nan)
        rows.append({
            "pah_complex": cname, "rest_um": rest, "obs_um": obs,
            "flux_int_w_m2": fint, "flux_int_err_w_m2": fint_e,
            "flux_obs_w_m2": fobs, "flux_obs_err_w_m2": fobs_e,
            "flux_int_erg_s_cm2": fint * 1e3,
            "eqw_um": _as_float(eqw),
            "snr_int": snr,
            "detected": bool(np.isfinite(snr) and snr >= 3.0 and fint > 0),
            "covered": bool(np.isfinite(obs) and is_covered(obs, fit["segments_um"])),
            "status": _feature_status(fint, fint_e,
                                      bool(np.isfinite(obs) and
                                           is_covered(obs, fit["segments_um"]))),
            "note": "CAFE PAH complex (Drude profiles summed)",
        })
    return pd.DataFrame(rows)


def _continuum_dataframe(fit: dict, z: float) -> tuple[pd.DataFrame, dict]:
    s = fit["specmod"]
    comps = s.compdict["CompFluxes"]
    wave = np.asarray(comps["wave"], dtype=float)
    c_um_s = C_UM_S

    # Rest-frame covered intervals.
    intervals = [(float(seg["start"]) / (1 + z), float(seg["stop"]) / (1 + z))
                 for seg in fit["segments_um"]]
    m = np.zeros(len(wave), dtype=bool)
    for lo, hi in intervals:
        m |= (wave >= lo) & (wave <= hi)

    def integrate(arr):
        arr = np.asarray(arr, dtype=float)
        total = 0.0
        for lo, hi in intervals:
            mm = (wave >= lo) & (wave <= hi)
            if mm.sum() > 1:
                total += float(np.trapezoid(
                    arr[mm] * c_um_s / wave[mm] ** 2, wave[mm])) * 1e-26
        return total

    fcon = np.asarray(comps["fCON"], dtype=float)
    total_cont = integrate(fcon)
    total_model = integrate(np.asarray(comps["fCON"], float)
                            + np.asarray(comps.get("fLIN", 0.0), float)
                            + np.asarray(comps.get("fPAH", 0.0), float))

    params = s.params
    def pval(name):
        return float(params[name].value) if name in params else np.nan
    def perr(name):
        if name not in params or params[name].stderr is None:
            return np.nan
        return float(params[name].stderr)

    comp_rows = [
        ("CIR", "cirrus dust", "Wave_CIR", ["CIR_FLX", "CIR_TMP"]),
        ("CLD", "cold dust", "Wave_CLD", ["CLD_FLX", "CLD_TMP"]),
        ("COO", "cool dust", "Wave_COO", ["COO_FLX", "COO_TMP", "COO_TAU", "COO_MIX", "COO_COV"]),
        ("WRM", "warm dust", "Wave_WRM", ["WRM_FLX", "WRM_TMP", "WRM_TAU", "WRM_MIX", "WRM_COV"]),
        ("HOT", "hot dust", "Wave_HOT", ["HOT_FLX", "HOT_TMP", "HOT_TAU", "HOT_MIX", "HOT_COV"]),
        ("STR", "stellar (ISRF)", "Wave_STR", ["STR_FLX", "STR_TAU", "STR_MIX", "STR_COV"]),
        ("STB", "starburst (SB99)", "Wave_STB", ["STB_FLX", "STB_TAU", "STB_MIX", "STB_COV", "STB_100", "STB_010"]),
        ("DSK", "AGN accretion disk", "Wave_DSK", ["DSK_FLX", "DSK_TAU", "DSK_COV"]),
        ("PAH", "PAH continuum", "Wave_PAH", ["PAH_FLX", "PAH_TAU", "PAH_MIX", "PAH_COV"]),
    ]
    refwaves = s.inopts.get("REFERENCE WAVELENGTHS", {})
    rows = []
    for comp, desc, refkey, pnames in comp_rows:
        key = "f" + comp
        arr = np.asarray(comps.get(key, np.zeros_like(wave)), dtype=float)
        integ = integrate(arr)
        ref = float(refwaves.get(refkey.upper(), np.nan)) if refkey.upper() in refwaves else np.nan
        ref_flux = float(np.interp(ref, wave, arr)) if np.isfinite(ref) else np.nan
        row = {
            "component": comp, "description": desc, "reference_wave_um": ref,
            "flux_at_reference_jy": ref_flux,
            "integrated_flux_w_m2": integ,
            "integrated_flux_erg_s_cm2": integ * 1e3,
            "fraction_of_continuum": integ / total_cont if total_cont > 0 else np.nan,
            "fraction_of_total_model": integ / total_model if total_model > 0 else np.nan,
        }
        for pn in pnames:
            row[pn] = pval(pn)
            row[pn + "_err"] = perr(pn)
        rows.append(row)
    df = pd.DataFrame(rows)
    extra = {
        "total_continuum_integrated_w_m2": total_cont,
        "total_model_integrated_w_m2": total_model,
        "covered_rest_intervals_um": intervals,
    }
    return df, extra


def _parameters_dataframe(fit: dict) -> pd.DataFrame:
    rows = []
    for name in fit["result"].params:
        p = fit["result"].params[name]
        rows.append({
            "name": name, "value": float(p.value),
            "stderr": float(p.stderr) if p.stderr is not None else np.nan,
            "vary": bool(p.vary),
            "min": float(p.min), "max": float(p.max),
            "expr": p.expr if p.expr is not None else "",
            "init_value": float(p.init_value) if hasattr(p, "init_value") else np.nan,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# post-fit Monte Carlo from the lmfit covariance
# ---------------------------------------------------------------------------
def _free_parameter_names(result) -> list:
    try:
        return list(result.var_names)
    except Exception:
        return [k for k in result.params if result.params[k].vary]


def _sample_from_covariance(result, n_samples: int, seed: int):
    names = _free_parameter_names(result)
    mu = np.asarray([result.params[k].value for k in names], dtype=float)
    info = {"method": "unavailable", "covariance_available": False,
            "regularized": False, "negative_eigenvalues": 0,
            "n_free": len(names)}
    if n_samples <= 0 or not names:
        info["reason"] = "no free parameters or MC disabled"
        return None, info, names
    cov = result.covar
    if cov is not None and result.errorbars:
        cov = np.asarray(cov, dtype=float)
        if cov.shape != (len(names), len(names)):
            info["reason"] = f"covariance shape {cov.shape} != {(len(names), len(names))}"
            cov = None
    if cov is not None and np.all(np.isfinite(cov)):
        cov = 0.5 * (cov + cov.T)
        evals, evecs = np.linalg.eigh(cov)
        info["negative_eigenvalues"] = int(np.sum(evals < -1e-12))
        if info["negative_eigenvalues"] > 0:
            evals = np.clip(evals, 0.0, None)
            cov = (evecs * evals) @ evecs.T
            info["regularized"] = True
        try:
            # jitter for numerical positive-definiteness
            scale = max(float(np.max(np.diag(cov))), 1e-30)
            L = np.linalg.cholesky(cov + 1e-12 * scale * np.eye(len(mu)))
            rng = np.random.default_rng(int(seed))
            z = rng.standard_normal((int(n_samples), len(mu)))
            samples = mu + z @ L.T
            info["method"] = "lmfit_covariance_multivariate_normal"
            info["covariance_available"] = True
        except Exception as exc:
            info["reason"] = f"Cholesky failed: {type(exc).__name__}: {exc}"
            samples = None
    else:
        samples = None
        if cov is None:
            info["reason"] = "lmfit covariance is None"
    if samples is None:
        # Fallback: diagonal stderr only, explicitly labelled.
        stderr = np.asarray([
            result.params[k].stderr if result.params[k].stderr is not None
            else np.nan for k in names], dtype=float)
        if np.all(np.isfinite(stderr)) and np.all(stderr >= 0):
            rng = np.random.default_rng(int(seed))
            samples = mu + rng.standard_normal((int(n_samples), len(mu))) * stderr
            info["method"] = "lmfit_stderr_diagonal_normal"
            info["reason"] = "covariance unavailable; diagonal stderr fallback"
        else:
            info["method"] = "unavailable"
            info["reason"] = "neither covariance nor complete stderr available"
            return None, info, names

    # Clip to lmfit parameter bounds.
    for j, k in enumerate(names):
        p = result.params[k]
        if np.isfinite(p.min):
            samples[:, j] = np.maximum(samples[:, j], p.min)
        if np.isfinite(p.max):
            samples[:, j] = np.minimum(samples[:, j], p.max)
    info["n_samples"] = int(samples.shape[0])
    info["seed"] = int(seed)
    return samples, info, names


def _line_flux_arrays(pars) -> dict:
    gauss, _, _ = get_feat_pars(pars, apply_vgrad2waves=True)
    wave, gamma, peak, name = gauss[0], gauss[1], gauss[2], gauss[3]
    out = {}
    for w, g, pk, nm in zip(wave, gamma, peak, name):
        key = str(nm)
        val = float(1e-26 * GAUSS_INT * (np.pi * C_UM_S / 2.0)
                    * float(pk) * float(g) / float(w))
        out[key] = out.get(key, 0.0) + val
    return out


def _pah_flux_arrays(pars) -> dict:
    _, drude, _ = get_feat_pars(pars, apply_vgrad2waves=True)
    wave, gamma, peak, name = drude[0], drude[1], drude[2], drude[3]
    out = {}
    for w, g, pk, nm in zip(wave, gamma, peak, name):
        cname = _pah_complex_for_wave(float(w))
        if cname is None:
            continue
        val = float(1e-26 * (np.pi * C_UM_S / 2.0)
                    * float(pk) * float(g) / float(w))
        out[cname] = out.get(cname, 0.0) + val
    return out


def _pah_flux_arrays_with_ext(pars, wave_grid, cont_profs) -> dict:
    """PAH complex fluxes including the fitted extinction at each feature."""
    _, drude, _ = get_feat_pars(pars, apply_vgrad2waves=True)
    wave, gamma, peak, name = drude[0], drude[1], drude[2], drude[3]
    comp, _, ext, _, _, _ = get_model_fluxes(pars, wave_grid, cont_profs,
                                             comps=True)
    ext_wave = np.asarray(comp["wave"], dtype=float)
    ext_pah = np.asarray(ext["extPAH"], dtype=float)
    out = {}
    for w, g, pk, nm in zip(wave, gamma, peak, name):
        cname = _pah_complex_for_wave(float(w))
        if cname is None:
            continue
        val = float(1e-26 * DRUDE_INT * C_UM_S * float(pk) * float(g) / float(w))
        scale = float(np.interp(float(w), ext_wave, ext_pah))
        out[cname] = out.get(cname, 0.0) + val * scale
    return out


def run_monte_carlo(fit: dict, n_samples: int, seed: int, z: float,
                    key_lines, key_pahs, key_ratios,
                    model_line_names=None, model_pah_names=None) -> dict:
    t0 = time.time()
    result = fit["result"]
    s = fit["specmod"]
    samples, info, names = _sample_from_covariance(result, n_samples, seed)
    if samples is None:
        info["runtime_s"] = time.time() - t0
        return {"samples": None, "info": info, "quantities": pd.DataFrame(),
                "samples_df": pd.DataFrame(), "arrays": {}}

    line_names = [k[2] for k in key_lines]
    pah_names = [k[1] for k in key_pahs]
    model_line_names = set(model_line_names or line_names)
    model_pah_names = set(model_pah_names or pah_names)
    ratio_specs = key_ratios
    param_names = ["HOT_TMP", "HOT_FLX", "WRM_TMP", "WRM_FLX",
                   "COO_TMP", "COO_FLX", "DSK_FLX", "STB_FLX", "VGRAD"]
    param_names = [p for p in param_names if p in result.params]

    arrays = {k: np.full(len(samples), np.nan) for k in line_names + pah_names}
    arrays.update({k: np.full(len(samples), np.nan) for k in param_names})
    arrays.update({r[0]: np.full(len(samples), np.nan) for r in ratio_specs})

    wave_grid = np.asarray(fit["specmod"].compdict["CompFluxes"]["wave"],
                           dtype=float)
    # A manager makes repeated Parameter copies cheap enough for 200 samples.
    base = result.params
    for i in range(len(samples)):
        pars = copy.deepcopy(base)
        for j, name in enumerate(names):
            pars[name].value = float(samples[i, j])
        lines = _line_flux_arrays(pars)
        pahs = _pah_flux_arrays_with_ext(pars, wave_grid, s.cont_profs)
        for k in line_names:
            if k in model_line_names:
                arrays[k][i] = lines.get(k, 0.0)
        for k in pah_names:
            if k in model_pah_names:
                arrays[k][i] = pahs.get(k, 0.0)
        for k in param_names:
            arrays[k][i] = float(pars[k].value)
        for label, k1, n1, k2, n2 in ratio_specs:
            if (k1 == "line" and n1 not in model_line_names) or \
                    (k1 == "pah" and n1 not in model_pah_names) or \
                    (k2 == "line" and n2 not in model_line_names) or \
                    (k2 == "pah" and n2 not in model_pah_names):
                continue
            a = lines.get(n1, 0.0) if k1 == "line" else pahs.get(n1, 0.0)
            b = lines.get(n2, 0.0) if k2 == "line" else pahs.get(n2, 0.0)
            arrays[label][i] = a / b if b > 0 else np.nan

    rows = []
    for q, arr in arrays.items():
        finite = np.isfinite(arr)
        if finite.sum() == 0:
            rows.append({"quantity": q, "n_valid": 0, "mean": np.nan,
                         "std": np.nan, "p16": np.nan, "p50": np.nan,
                         "p84": np.nan})
        else:
            rows.append({
                "quantity": q, "n_valid": int(finite.sum()),
                "mean": float(np.nanmean(arr)),
                "std": float(np.nanstd(arr, ddof=1)) if finite.sum() > 1 else np.nan,
                "p16": float(np.nanpercentile(arr, 16)),
                "p50": float(np.nanpercentile(arr, 50)),
                "p84": float(np.nanpercentile(arr, 84)),
            })
    quantities = pd.DataFrame(rows)
    samples_df = pd.DataFrame(arrays)
    samples_df.insert(0, "sample", np.arange(len(samples), dtype=int))
    info["runtime_s"] = time.time() - t0
    info["n_quantities"] = len(arrays)
    return {"samples": samples, "info": info, "quantities": quantities,
            "samples_df": samples_df, "arrays": arrays}


# ---------------------------------------------------------------------------
# key-line and uncertainty tables
# ---------------------------------------------------------------------------
def _local_residual_rms(fit: dict, center_obs: float, half_width: float):
    wave = np.asarray(fit["specmod"].spec_dict["wave"], float) * (
        1.0 + float(fit["specmod"].z))
    _, resid = _model_and_residuals(fit)
    m = np.abs(wave - center_obs) <= max(half_width, 1e-4)
    if m.sum() < 5:
        m = np.abs(wave - center_obs) <= max(2.0 * half_width, 2e-3)
    if m.sum() < 3:
        return float("nan")
    r = resid[m]
    return float(1.4826 * np.median(np.abs(r - np.median(r))))


def _resolving_power(fit: dict, obs_um: float) -> float:
    try:
        rows = fit.get("_inst_df")
        if rows is None:
            s = fit["specmod"]
            table_path = os.path.dirname(CAFE.__file__) + "/tables/"
            rows = cafe_io().read_inst(
                s.inpars["MODULES & TABLES"]["RESOLUTIONS"],
                s.spec_dict["wave"], table_path)
            fit["_inst_df"] = rows
        for _, r in rows.iterrows():
            if float(r["wMin"]) <= obs_um <= float(r["wMax"]):
                return float(r["rSlope"] * obs_um + r["rBias"])
    except Exception:
        pass
    return float("nan")


def _upper_limit(fit: dict, obs_um: float, rest_um: float, kind: str):
    rp = _resolving_power(fit, obs_um)
    if not np.isfinite(rp) or rp <= 0:
        return float("nan")
    fwhm = obs_um / rp
    rms = _local_residual_rms(fit, obs_um, 3.0 * fwhm)
    if not np.isfinite(rms):
        return float("nan")
    factor = GAUSS_INT if kind == "line" else DRUDE_INT
    return float(3.0 * 1e-26 * factor * C_UM_S * rms * fwhm / obs_um ** 2)


def _mc_stats(mc: dict, q: str):
    if mc is None or mc.get("quantities") is None or len(mc["quantities"]) == 0:
        return {}
    row = mc["quantities"][mc["quantities"]["quantity"] == q]
    if len(row) == 0:
        return {}
    return row.iloc[0].to_dict()


def build_key_tables(fit: dict, z: float, lines_df: pd.DataFrame,
                     pah_df: pd.DataFrame, mc: dict | None) -> tuple:
    segs = fit["segments_um"]
    line_tab = getattr(fit["specmod"], "linetable", None)
    pah_tab = getattr(fit["specmod"], "pahtable", None)
    model_line_names = set(lines_df["base_name"]) if len(lines_df) else set()
    model_pah_names = set(pah_df["pah_complex"]) if len(pah_df) else set()
    rows = []
    for label, rest, base, comps in KEY_LINES:
        obs = rest * (1 + z)
        covered = is_covered(obs, segs)
        agg = _sum_component_rows(line_tab, base, z) if base in model_line_names else None
        status = (_feature_status(agg["flux_int"], agg["flux_int_err"], covered)
                  if agg else ("not_covered" if not covered else "not_in_model"))
        mcq = _mc_stats(mc, base) if mc else {}
        row = {
            "kind": "line", "label": label, "cafe_name": base,
            "rest_um": rest, "obs_um": obs, "covered": bool(covered),
            "in_model": bool(agg is not None), "status": status,
            "flux_int_w_m2": agg["flux_int"] if agg else np.nan,
            "flux_int_err_w_m2": agg["flux_int_err"] if agg else np.nan,
            "flux_obs_w_m2": agg["flux_obs"] if agg else np.nan,
            "flux_obs_err_w_m2": agg["flux_obs_err"] if agg else np.nan,
            "flux_int_erg_s_cm2": agg["flux_int"] * 1e3 if agg else np.nan,
            "flux_obs_erg_s_cm2": agg["flux_obs"] * 1e3 if agg else np.nan,
            "snr_int": (agg["flux_int"] / agg["flux_int_err"])
            if agg and np.isfinite(agg["flux_int_err"]) and agg["flux_int_err"] > 0
            else np.nan,
            "fwhm_kms": agg["gamma"] * C_KMS if agg else np.nan,
            "flux_3sigma_ul_w_m2": _upper_limit_combine(
                _upper_limit(fit, obs, rest, "line"),
                agg["flux_int_err"] if agg else np.nan)
            if covered and status != "detected" else np.nan,
            "mc_mean": mcq.get("mean", np.nan), "mc_std": mcq.get("std", np.nan),
            "mc_p16": mcq.get("p16", np.nan), "mc_p50": mcq.get("p50", np.nan),
            "mc_p84": mcq.get("p84", np.nan),
            "mc_method": mc["info"]["method"] if mc else "unavailable",
            "note": ("zeroed detector gap in the canonical x1d product"
                     if not covered else ""),
        }
        rows.append(row)
    for label, cname, rest in KEY_PAHS:
        obs = rest * (1 + z)
        covered = is_covered(obs, segs)
        agg = _pah_rows(pah_tab, cname) if cname in model_pah_names else None
        status = (_feature_status(agg["flux_int"], agg["flux_int_err"], covered)
                  if agg else ("not_covered" if not covered else "not_in_model"))
        mcq = _mc_stats(mc, cname) if mc else {}
        rows.append({
            "kind": "pah", "label": label, "cafe_name": cname,
            "rest_um": rest, "obs_um": obs, "covered": bool(covered),
            "in_model": bool(agg is not None), "status": status,
            "flux_int_w_m2": agg["flux_int"] if agg else np.nan,
            "flux_int_err_w_m2": agg["flux_int_err"] if agg else np.nan,
            "flux_obs_w_m2": agg["flux_obs"] if agg else np.nan,
            "flux_obs_err_w_m2": agg["flux_obs_err"] if agg else np.nan,
            "flux_int_erg_s_cm2": agg["flux_int"] * 1e3 if agg else np.nan,
            "flux_obs_erg_s_cm2": agg["flux_obs"] * 1e3 if agg else np.nan,
            "snr_int": (agg["flux_int"] / agg["flux_int_err"])
            if agg and np.isfinite(agg["flux_int_err"]) and agg["flux_int_err"] > 0
            else np.nan,
            "fwhm_kms": np.nan,
            "flux_3sigma_ul_w_m2": _upper_limit_combine(
                _upper_limit(fit, obs, rest, "pah"),
                agg["flux_int_err"] if agg else np.nan)
            if covered and status != "detected" else np.nan,
            "mc_mean": mcq.get("mean", np.nan), "mc_std": mcq.get("std", np.nan),
            "mc_p16": mcq.get("p16", np.nan), "mc_p50": mcq.get("p50", np.nan),
            "mc_p84": mcq.get("p84", np.nan),
            "mc_method": mc["info"]["method"] if mc else "unavailable",
            "note": ("zeroed detector gap in the canonical x1d product"
                     if not covered else ""),
        })
    key = pd.DataFrame(rows)

    ratio_rows = []
    for label, k1, n1, k2, n2 in KEY_RATIOS:
        r1 = key[(key["cafe_name"] == n1)]
        r2 = key[(key["cafe_name"] == n2)]
        v1 = float(r1["flux_int_w_m2"].iloc[0]) if len(r1) else np.nan
        v2 = float(r2["flux_int_w_m2"].iloc[0]) if len(r2) else np.nan
        e1 = float(r1["flux_int_err_w_m2"].iloc[0]) if len(r1) else np.nan
        e2 = float(r2["flux_int_err_w_m2"].iloc[0]) if len(r2) else np.nan
        val = v1 / v2 if np.isfinite(v1) and np.isfinite(v2) and v2 > 0 else np.nan
        err = np.nan
        if np.isfinite(val) and np.isfinite(e1) and np.isfinite(e2):
            err = abs(val) * np.sqrt((e1 / v1) ** 2 + (e2 / v2) ** 2) \
                if v1 > 0 else np.nan
        mcq = _mc_stats(mc, label) if mc else {}
        ratio_rows.append({
            "kind": "ratio", "label": label, "cafe_name": f"{n1}/{n2}",
            "rest_um": np.nan, "obs_um": np.nan,
            "covered": bool(len(r1) and len(r2) and
                            bool(r1["covered"].iloc[0]) and
                            bool(r2["covered"].iloc[0])),
            "in_model": bool(len(r1) and len(r2) and
                             bool(r1["in_model"].iloc[0]) and
                             bool(r2["in_model"].iloc[0])),
            "status": ("ok" if np.isfinite(val) and val > 0 and
                       np.isfinite(_snr(val, err)) and _snr(val, err) >= 3.0
                       else ("marginal" if np.isfinite(val) and val > 0 and
                             np.isfinite(_snr(val, err)) and _snr(val, err) >= 2.0
                             else "undefined")),
            "flux_int_w_m2": val, "flux_int_err_w_m2": err,
            "flux_obs_w_m2": np.nan, "flux_obs_err_w_m2": np.nan,
            "flux_int_erg_s_cm2": np.nan, "flux_obs_erg_s_cm2": np.nan,
            "snr_int": _snr(val, err),
            "fwhm_kms": np.nan, "flux_3sigma_ul_w_m2": np.nan,
            "mc_mean": mcq.get("mean", np.nan), "mc_std": mcq.get("std", np.nan),
            "mc_p16": mcq.get("p16", np.nan), "mc_p50": mcq.get("p50", np.nan),
            "mc_p84": mcq.get("p84", np.nan),
            "mc_method": mc["info"]["method"] if mc else "unavailable",
            "note": "",
        })
    if ratio_rows:
        key = pd.concat([key, pd.DataFrame(ratio_rows)], ignore_index=True)
    return key


def build_uncertainties_table(key: pd.DataFrame, mc: dict | None,
                              fit: dict) -> pd.DataFrame:
    rows = []
    method = mc["info"]["method"] if mc else "unavailable"
    for _, r in key.iterrows():
        q = str(r["label"]) if r["kind"] == "ratio" else str(r["cafe_name"])
        mcq = _mc_stats(mc, q) if mc else {}
        rows.append({
            "quantity": q, "label": r["label"], "kind": r["kind"],
            "unit": "W/m^2" if r["kind"] in ("line", "pah") else "dimensionless",
            "best": r["flux_int_w_m2"],
            "best_err": r["flux_int_err_w_m2"],
            "mean": mcq.get("mean", np.nan),
            "std": mcq.get("std", np.nan),
            "p16": mcq.get("p16", np.nan),
            "p50": mcq.get("p50", np.nan),
            "p84": mcq.get("p84", np.nan),
            "n_valid": mcq.get("n_valid", 0),
            "method": method,
            "covered": bool(r["covered"]), "status": r["status"],
            "note": (r["note"] if str(r["note"]) not in ("", "nan")
                     else ("best-fit component is zero; MC std is from the "
                           "last lmfit covariance and is an upper-limit "
                           "estimate" if str(r["status"]) == "fixed_at_zero"
                           else "")),
        })
    # selected continuum parameters
    if mc:
        for p in ["HOT_TMP", "HOT_FLX", "WRM_TMP", "WRM_FLX",
                  "COO_TMP", "COO_FLX", "DSK_FLX", "STB_FLX", "VGRAD"]:
            if p not in fit["result"].params:
                continue
            mcq = _mc_stats(mc, p)
            rows.append({
                "quantity": p, "label": p, "kind": "parameter",
                "unit": "K" if p.endswith("_TMP") else (
                    "km/s" if p == "VGRAD" else "dimensionless"),
                "best": float(fit["result"].params[p].value),
                "best_err": float(fit["result"].params[p].stderr)
                if fit["result"].params[p].stderr is not None else np.nan,
                "mean": mcq.get("mean", np.nan), "std": mcq.get("std", np.nan),
                "p16": mcq.get("p16", np.nan), "p50": mcq.get("p50", np.nan),
                "p84": mcq.get("p84", np.nan),
                "n_valid": mcq.get("n_valid", 0), "method": method,
                "covered": True, "status": "parameter", "note": "",
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------
def copy_native_figure(fit: dict, out_dir: Path) -> str | None:
    stem = fit["specmod"].result_file_name
    src = Path(fit["native_dir"]) / f"{stem}_fitfigure.png"
    if src.exists():
        dst = Path(out_dir) / "cafe_fit.png"
        shutil.copy2(src, dst)
        return str(dst)
    return None


def plot_fit_and_residuals(fit: dict, out_dir: Path) -> str:
    s = fit["specmod"]
    z = float(s.z)
    wave = np.asarray(s.spec_dict["wave"], dtype=float) * (1.0 + z)
    flux = s.spec_dict["flux"]
    err = s.spec_dict["flux_unc"]
    model, resid = _model_and_residuals(fit)
    comps = s.compdict["CompFluxes"]
    cwave = np.asarray(comps["wave"], dtype=float) * (1.0 + z)

    fig, (ax, axr) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True,
                                  gridspec_kw={"height_ratios": [3, 1]})
    ax.errorbar(wave, flux, yerr=err, fmt=".", ms=2, lw=0.4, color="0.25",
                ecolor="0.75", alpha=0.8, label="JWST/MIRI x1d (used)",
                zorder=5)
    for key, color, label in [
        ("fCON", "0.45", "total continuum"),
        ("fPAH", "C4", "PAHs"),
        ("fLIN", "C0", "lines"),
        ("fHOT", "C1", "hot dust"),
        ("fWRM", "C2", "warm dust"),
        ("fCOO", "C6", "cool dust"),
        ("fDSK", "C5", "AGN disk"),
    ]:
        if key in comps:
            ax.plot(cwave, comps[key], lw=0.9, color=color, alpha=0.8,
                    label=label, zorder=2)
    first_seg = True
    for seg in fit["segments_um"]:
        mseg = (wave >= float(seg["start"])) & (wave <= float(seg["stop"]))
        if mseg.sum() > 1:
            ax.plot(wave[mseg], model[mseg], color="C3", lw=2.0, zorder=10,
                    label="CAFE total model" if first_seg else None)
            first_seg = False
    for seg in fit["segments_um"]:
        ax.axvspan(seg["start"], seg["stop"], color="0.95", zorder=-5)
    ax.set_yscale("log")
    pos = flux[np.isfinite(flux) & (flux > 0)]
    if len(pos):
        ax.set_ylim(max(0.01, 0.3 * float(np.nanmin(pos))),
                    2.0 * float(np.nanmax(pos)))
    ax.set_ylabel(r"$F_\nu$ (Jy)")
    ax.set_title(f"CAFE fit — {s.file_name}  (z={z:.4f})")
    ax.legend(ncol=3, fontsize=7, loc="best")
    ax.grid(alpha=0.2)

    axr.axhline(0, color="0.5", lw=0.8)
    axr.errorbar(wave, 100.0 * resid / np.where(flux != 0, flux, np.nan),
                 yerr=100.0 * err / np.where(flux != 0, np.abs(flux), np.nan),
                 fmt=".", ms=2, lw=0.4, color="0.25", ecolor="0.75", alpha=0.8)
    for seg in fit["segments_um"]:
        axr.axvspan(seg["start"], seg["stop"], color="0.95", zorder=-5)
    # mark the zeroed MRS gaps
    for a, b in zip(fit["segments_um"][:-1], fit["segments_um"][1:]):
        axr.axvspan(a["stop"], b["start"], color="C1", alpha=0.10, zorder=-4)
    axr.set_xlabel("observed wavelength (um)")
    axr.set_ylabel("residual (%)")
    axr.set_ylim(-25, 25)
    axr.grid(alpha=0.2)
    # mark the covered key features (observed frame); labels only for the
    # strongest/most relevant features to avoid clutter
    label_lines = {"NeV_143217", "H200S3_96649", "FeIII_229250"}
    label_pahs = {"PAH62", "PAH86", "PAH136", "PAH142"}
    for label, rest, base, _comps in KEY_LINES:
        obs = rest * (1.0 + z)
        if is_covered(obs, fit["segments_um"]):
            for a in (ax, axr):
                a.axvline(obs, color="C0", lw=0.5, alpha=0.30)
            if base in label_lines:
                ax.text(obs, ax.get_ylim()[1] * 0.75, label, rotation=90,
                        fontsize=6, ha="right", va="top", color="C0", alpha=0.9)
    for label, cname, rest in KEY_PAHS:
        obs = rest * (1.0 + z)
        if is_covered(obs, fit["segments_um"]):
            for a in (ax, axr):
                a.axvline(obs, color="C4", lw=0.5, alpha=0.30)
            if cname in label_pahs:
                ax.text(obs, ax.get_ylim()[1] * 0.55, label, rotation=90,
                        fontsize=6, ha="right", va="top", color="C4", alpha=0.9)
    ax.set_xlim(float(np.nanmin(wave)) - 0.4, float(np.nanmax(wave)) + 0.4)
    fig.tight_layout()
    path = Path(out_dir) / "cafe_fit_residuals.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def plot_uncertainty(fit: dict, mc: dict | None, out_dir: Path) -> str:
    path = Path(out_dir) / "cafe_uncertainty.png"
    info = mc["info"] if mc else {"method": "unavailable", "reason": "MC disabled"}
    method = info.get("method", "unavailable")
    n = info.get("n_samples", 0)
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(3, 4, figure=fig, hspace=0.55, wspace=0.35)
    if not mc or mc.get("samples_df") is None or len(mc["samples_df"]) == 0:
        ax = fig.add_subplot(gs[:, :])
        ax.axis("off")
        ax.text(0.5, 0.5,
                "Post-fit uncertainty unavailable\n\n"
                f"method: {method}\nreason: {info.get('reason', 'unknown')}\n\n"
                "CAFE uses lmfit (least squares), not MCMC.  No covariance /\n"
                "stderr was returned by the fitter for this solution.",
                ha="center", va="center", fontsize=13)
        fig.suptitle("CAFE uncertainty (unavailable)", fontsize=14)
        fig.savefig(path, dpi=140, bbox_inches="tight")
        plt.close(fig)
        return str(path)

    df = mc["samples_df"]
    flux_qs = []
    for q in ["PAH62", "PAH86", "PAH136", "PAH142", "NeV_143217",
              "FeIII_229250", "ArV_131022", "H200S3_96649"]:
        if q in df.columns and np.isfinite(df[q]).sum() >= 10:
            flux_qs.append(q)
    flux_qs = flux_qs[:4]
    param_qs = [q for q in ["HOT_TMP", "WRM_TMP", "COO_TMP", "HOT_FLX",
                            "WRM_FLX", "VGRAD"] if q in df.columns][:4]

    def hist_panel(ax, q):
        arr = np.asarray(df[q], dtype=float)
        arr = arr[np.isfinite(arr)]
        if len(arr) == 0:
            ax.axis("off")
            return
        ax.hist(arr, bins=30, color="C0", alpha=0.75, histtype="stepfilled")
        for p, c in [(16, "C1"), (50, "C3"), (84, "C1")]:
            ax.axvline(np.percentile(arr, p), color=c, lw=1)
        ax.set_title(q, fontsize=9)
        ax.tick_params(labelsize=7)
        ax.set_yticks([])

    for j, q in enumerate(flux_qs):
        hist_panel(fig.add_subplot(gs[0, j]), q)
    for j, q in enumerate(flux_qs):
        ax = fig.add_subplot(gs[1, j])
        arr = np.asarray(df[q], dtype=float)
        ax.plot(np.arange(len(arr)), arr, lw=0.7, color="C0")
        ax.set_title(f"trace: {q}", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_xlabel("sample", fontsize=7)

    pairs = []
    if len(flux_qs) >= 2:
        pairs.append((flux_qs[0], flux_qs[1]))
    if len(param_qs) >= 2:
        pairs.append((param_qs[0], param_qs[1]))
    if len(param_qs) >= 4:
        pairs.append((param_qs[2], param_qs[3]))
    for j, (qx, qy) in enumerate(pairs[:3]):
        ax = fig.add_subplot(gs[2, j])
        x = np.asarray(df[qx], float)
        y = np.asarray(df[qy], float)
        m = np.isfinite(x) & np.isfinite(y)
        ax.scatter(x[m], y[m], s=8, alpha=0.55, color="C0")
        ax.set_xlabel(qx, fontsize=7)
        ax.set_ylabel(qy, fontsize=7)
        ax.tick_params(labelsize=7)
        if m.sum() > 3:
            cov = np.cov(x[m], y[m])
            evals, evecs = np.linalg.eigh(cov)
            order = np.argsort(evals)[::-1]
            evals, evecs = evals[order], evecs[:, order]
            angle = np.degrees(np.arctan2(evecs[1, 0], evecs[0, 0]))
            for ns in (1, 2):
                e = Ellipse(
                    (np.mean(x[m]), np.mean(y[m])),
                    2 * ns * np.sqrt(max(evals[0], 0)),
                    2 * ns * np.sqrt(max(evals[1], 0)),
                    angle=angle, fill=False, lw=0.8,
                    color="C1" if ns == 1 else "C3")
                ax.add_patch(e)
    ax = fig.add_subplot(gs[2, 3])
    ax.axis("off")
    txt = (f"method: {method}\n"
           f"N samples: {n}\n"
           f"covariance available: {info.get('covariance_available', False)}\n"
           f"regularised: {info.get('regularized', False)}\n"
           f"negative eigenvalues: {info.get('negative_eigenvalues', 0)}\n"
           f"{info.get('reason', '')}\n\n"
           "This is NOT an MCMC chain.  Samples are drawn from a\n"
           "multivariate normal built from the lmfit covariance at the\n"
           "best-fit solution.  Fixed parameters are held at their\n"
           "best-fit values.")
    ax.text(0.0, 0.98, txt, va="top", fontsize=8)
    fig.suptitle("CAFE post-fit uncertainty: lmfit covariance Monte Carlo "
                 f"(N={n}; not MCMC)", fontsize=13)
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return str(path)


# ---------------------------------------------------------------------------
# run.json
# ---------------------------------------------------------------------------
def _detection_summary(key: pd.DataFrame) -> dict:
    out = {}
    if key is None or len(key) == 0:
        return out
    for _, r in key.iterrows():
        if r["kind"] == "ratio":
            continue
        out[str(r["label"])] = {
            "cafe_name": str(r["cafe_name"]),
            "rest_um": float(r["rest_um"]),
            "obs_um": float(r["obs_um"]),
            "covered": bool(r["covered"]),
            "in_model": bool(r["in_model"]),
            "status": str(r["status"]),
            "flux_int_w_m2": float(r["flux_int_w_m2"])
            if np.isfinite(r["flux_int_w_m2"]) else None,
            "flux_int_err_w_m2": float(r["flux_int_err_w_m2"])
            if np.isfinite(r["flux_int_err_w_m2"]) else None,
            "snr_int": float(r["snr_int"]) if np.isfinite(r["snr_int"]) else None,
            "flux_3sigma_ul_w_m2": float(r["flux_3sigma_ul_w_m2"])
            if np.isfinite(r["flux_3sigma_ul_w_m2"]) else None,
            "mc_p16": float(r["mc_p16"]) if np.isfinite(r["mc_p16"]) else None,
            "mc_p50": float(r["mc_p50"]) if np.isfinite(r["mc_p50"]) else None,
            "mc_p84": float(r["mc_p84"]) if np.isfinite(r["mc_p84"]) else None,
        }
    return out


def _ratio_summary(key: pd.DataFrame) -> dict:
    out = {}
    if key is None or len(key) == 0:
        return out
    for _, r in key[key["kind"] == "ratio"].iterrows():
        out[str(r["label"])] = {
            "value": float(r["flux_int_w_m2"])
            if np.isfinite(r["flux_int_w_m2"]) else None,
            "err": float(r["flux_int_err_w_m2"])
            if np.isfinite(r["flux_int_err_w_m2"]) else None,
            "status": str(r["status"]),
            "mc_p16": float(r["mc_p16"]) if np.isfinite(r["mc_p16"]) else None,
            "mc_p50": float(r["mc_p50"]) if np.isfinite(r["mc_p50"]) else None,
            "mc_p84": float(r["mc_p84"]) if np.isfinite(r["mc_p84"]) else None,
        }
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True, type=Path,
                   help="input directory with *_x1d.fits (or a FITS file)")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--work", type=Path, default=Path("/app/work"),
                   help="scratch/work directory (outside outputs)")
    p.add_argument("--z", required=True, type=float)
    p.add_argument("--config", type=Path, default=Path("/app/config/default"),
                   help="CAFE config directory with inpars.ini + default_opt.cafe")
    p.add_argument("--tables", type=Path, default=None,
                   help="CAFE tables directory (default: ../tables next to --config)")
    p.add_argument("--segment", choices=["both", "short", "long"], default="both")
    p.add_argument("--dq-policy", choices=["good", "all"], default="good")
    p.add_argument("--min-wave", type=float, default=None)
    p.add_argument("--max-wave", type=float, default=None)
    p.add_argument("--error-floor", type=float, default=0.01,
                   help="fractional error floor applied in the adapter (default 1%%)")
    p.add_argument("--bin-kms", type=float, default=0.0)
    p.add_argument("--edge-trim", type=int, default=2)
    p.add_argument("--gap-factor", type=float, default=10.0)
    p.add_argument("--no-coverage-mask", action="store_true",
                   help="do not mask lines/PAHs outside contiguous coverage")
    p.add_argument("--coverage-margin-um", type=float, default=0.0)
    p.add_argument("--no-lines", action="store_true")
    p.add_argument("--no-pahs", action="store_true")
    p.add_argument("--force-all-lines", dest="force_all_lines",
                   action="store_true", default=True)
    p.add_argument("--no-force-all-lines", dest="force_all_lines",
                   action="store_false")
    p.add_argument("--max-loops", type=int, default=5)
    p.add_argument("--ftol", type=float, default=None)
    p.add_argument("--outlier-sigma", type=float, default=5.0)
    p.add_argument("--outlier-rel-threshold", type=float, default=0.10,
                   help="also require |residual|/|flux| above this value "
                        "before clipping (default 10%%)")
    p.add_argument("--no-outlier-clip", action="store_true")
    p.add_argument("--mc-samples", type=int, default=200)
    p.add_argument("--mc-seed", type=int, default=20250101)
    p.add_argument("--no-mc", action="store_true")
    p.add_argument("--source-key", default=None,
                   help="source key for metadata (default: parent of output dir)")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    out = args.output.resolve()
    work = args.work.resolve()
    out.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    # CAFE.read_spec() creates/removes ./dummy.fits in the process CWD.  Keep
    # that scratch file inside the writable work directory, never in outputs.
    os.chdir(work)
    log_path = out / "cafe_run.log"
    log_fh = open(log_path, "w")
    real_stdout, real_stderr = sys.stdout, sys.stderr
    sys.stdout = Tee(real_stdout, log_fh)
    sys.stderr = Tee(real_stderr, log_fh)

    source_key = args.source_key or out.parent.name
    spectrum_stem = safe_stem(source_key + "_miri")
    run = {
        "tool": "cafe_line",
        "tool_version": "1.0.0",
        "created_utc": utc_now(),
        "status": "running",
        "source": {"key": source_key, "z": args.z},
        "arguments": {k: (str(v) if isinstance(v, Path) else v)
                      for k, v in vars(args).items()},
        "inputs": [],
        "config": {},
        "spectrum": {},
        "fit": {},
        "uncertainty": {},
        "products": {},
        "warnings": [],
        "limitations": [],
    }
    started = time.time()
    try:
        print(f"[cafe_line] CAFE {_package_version('CAFE')} "
              f"commit={os.environ.get('CAFE_COMMIT', 'unknown')}")
        print(f"[cafe_line] input={args.input} output={out} z={args.z}")

        # 1. adapter -> CAFE text spectrum in work/ (never in outputs/)
        spec = build_spectrum(
            [args.input], z=args.z, segment=args.segment,
            dq_policy=args.dq_policy, min_wave=args.min_wave,
            max_wave=args.max_wave, error_floor=args.error_floor,
            bin_kms=args.bin_kms, edge_trim=args.edge_trim,
            gap_factor=args.gap_factor)
        spec_path = work / f"{spectrum_stem}.txt"
        write_cafe_text(spec_path, spec["wave"], spec["flux"], spec["err"],
                        header=(f"CAFE input from {source_key}; z={args.z}; "
                                "columns: wave_um flux_Jy flux_unc_Jy"))
        spec_meta_path = work / f"{spectrum_stem}_meta.json"
        write_json(spec_meta_path, spec["meta"])
        run["inputs"] = [m for m in spec["meta"]["inputs"]]
        run["spectrum"] = {
            "prepared_path": str(spec_path),
            "prepared_sha256": sha256(spec_path),
            "prepared_meta_path": str(spec_meta_path),
            **{k: v for k, v in spec["meta"].items() if k != "inputs"},
        }
        print(f"[cafe_line] spectrum: {len(spec['wave'])} pixels, "
              f"{len(spec['meta']['segments_um'])} segments, "
              f"median S/N={spec['meta']['median_snr']:.1f}")

        # 2. effective config (coverage-aware)
        config = prepare_effective_config(
            args.config, args.tables, args.z, spec["meta"]["segments_um"],
            work, fit_lines=not args.no_lines, fit_pahs=not args.no_pahs,
            max_loops=args.max_loops, error_floor=args.error_floor,
            coverage_mask=not args.no_coverage_mask,
            margin_um=args.coverage_margin_um, ftol=args.ftol)
        run["config"] = {
            "requested_config": str(args.config.resolve()),
            "requested_tables": str(Path(config["tables"])),
            "effective_dir": config["effective_dir"],
            "effective_tabpath": config["tabpath"],
            "line_tables": config["line_tables"],
            "sha256": config["sha256"],
        }
        run["segments_um"] = spec["meta"]["segments_um"]

        # 3. fit pass 1
        native_root = work / "native_pass1"
        if native_root.exists():
            shutil.rmtree(native_root)
        print("[cafe_line] fit pass 1")
        try:
            fit = fit_once(spec_path, args.z, config, native_root,
                           args.force_all_lines, args.max_loops,
                           segments_um=spec["meta"]["segments_um"])
        except ForceAllError as exc:
            run["warnings"].append(str(exc))
            print(f"[cafe_line] WARNING: {exc}; retrying with force_all=False")
            fit = fit_once(spec_path, args.z, config, native_root,
                           False, args.max_loops,
                           segments_um=spec["meta"]["segments_um"])
        print(f"[cafe_line] pass 1: success={fit['result'].success} "
              f"redchi={fit['result'].redchi:.3f} "
              f"runtime={fit['runtime_s']:.1f}s")

        # 4. optional outlier clip + refit
        outlier_info = {"applied": False}
        final_spec_path = spec_path
        if not args.no_outlier_clip:
            final_spec_path = work / f"{spectrum_stem}_clipped.txt"
            native_pass2 = work / "native_pass2"
            if native_pass2.exists():
                shutil.rmtree(native_pass2)
            try:
                new_fit, outlier_info = refit_with_mask(
                    fit, spec_path, args.z, config, native_pass2,
                    args.force_all_lines, args.max_loops, final_spec_path,
                    rel_threshold=args.outlier_rel_threshold)
                if outlier_info.get("applied"):
                    print(f"[cafe_line] clipped {outlier_info['n_outliers']} "
                          "outlier pixels and refit (pass 2)")
                    fit = new_fit
                else:
                    print("[cafe_line] outlier clip not applied")
            except Exception as exc:
                outlier_info = {"applied": False,
                                "error": f"{type(exc).__name__}: {exc}"}
                run["warnings"].append(
                    "outlier-clipped refit failed; first-pass fit retained")
                print("[cafe_line] WARNING: outlier refit failed; "
                      "first-pass fit retained")
                traceback.print_exc()

        # 5. ensure native products exist (pass 1 may not have been saved yet)
        native_paths = save_native_products(fit)
        native_out = out / "cafe_native" / Path(fit["native_dir"]).name
        if native_out.exists():
            shutil.rmtree(native_out)
        shutil.copytree(fit["native_dir"], native_out)

        # 6. tables
        lines_df = _line_table_dataframe(fit, args.z)
        pah_df = _pah_dataframe(fit, args.z)
        comp_df, comp_extra = _continuum_dataframe(fit, args.z)
        params_df = _parameters_dataframe(fit)
        lines_df.to_csv(out / "cafe_lines.csv", index=False)
        pah_df.to_csv(out / "cafe_pah.csv", index=False)
        comp_df.to_csv(out / "cafe_components.csv", index=False)
        params_df.to_csv(out / "cafe_fit_parameters.csv", index=False)

        # 7. Monte Carlo
        if args.no_mc or args.mc_samples <= 0:
            mc = None
            mc_info = {"method": "disabled", "n_samples": 0,
                       "reason": "--no-mc"}
        else:
            print(f"[cafe_line] post-fit MC: {args.mc_samples} samples "
                  "from lmfit covariance")
            mc = run_monte_carlo(
                fit, args.mc_samples, args.mc_seed, args.z,
                KEY_LINES, KEY_PAHS, KEY_RATIOS,
                model_line_names=set(lines_df["base_name"]),
                model_pah_names=set(pah_df["pah_complex"]))
            mc_info = mc["info"]
            if mc["samples_df"] is not None and len(mc["samples_df"]):
                mc["samples_df"].to_csv(out / "cafe_mc_samples.csv", index=False)
            print(f"[cafe_line] MC method={mc_info.get('method')} "
                  f"runtime={mc_info.get('runtime_s', 0):.1f}s")
        run["uncertainty"] = mc_info

        # 8. key tables (need MC stats)
        key_df = build_key_tables(fit, args.z, lines_df, pah_df, mc)
        key_df.to_csv(out / "cafe_key_lines.csv", index=False)
        unc_df = build_uncertainties_table(key_df, mc, fit)
        unc_df.to_csv(out / "cafe_uncertainties.csv", index=False)

        # 9. figures
        fit_png = copy_native_figure(fit, out)
        resid_png = plot_fit_and_residuals(fit, out)
        if fit_png is None:
            # native cafeplot failed: promote our diagnostic figure
            fit_png = str(out / "cafe_fit_residuals.png")
        unc_png = plot_uncertainty(fit, mc, out)

        # 10. config provenance
        copy_config_used(config, out)

        # 11. run.json
        stats = _stats(fit, spec["meta"]["segments_um"], outlier_info)
        stats["pass"] = 2 if outlier_info.get("applied") else 1
        stats["final_spectrum"] = str(final_spec_path)
        stats["final_n_pixels"] = int(len(fit["specmod"].spec_dict["wave"]))
        stats["final_coverage_um"] = [
            [float(seg["start"]), float(seg["stop"])]
            for seg in fit["segments_um"]
        ]
        stats["native_products"] = native_paths
        stats["native_dir"] = relative_to(native_out, out)
        run["fit"] = stats
        if stats.get("parameters_at_bounds"):
            names = ", ".join(f"{p['name']}({p['bound']})"
                              for p in stats["parameters_at_bounds"][:12])
            run["warnings"].append(
                "some feature parameters sit at their fit bounds: " + names +
                (" ..." if len(stats["parameters_at_bounds"]) > 12 else ""))
        run["status"] = "ok" if stats["stable"] else "ok_unstable"
        run["products"] = {
            "cafe_fit.png": relative_to(fit_png, out) if fit_png else None,
            "cafe_fit_residuals.png": relative_to(resid_png, out),
            "cafe_uncertainty.png": relative_to(unc_png, out),
            "cafe_lines.csv": "cafe_lines.csv",
            "cafe_key_lines.csv": "cafe_key_lines.csv",
            "cafe_pah.csv": "cafe_pah.csv",
            "cafe_components.csv": "cafe_components.csv",
            "cafe_fit_parameters.csv": "cafe_fit_parameters.csv",
            "cafe_uncertainties.csv": "cafe_uncertainties.csv",
            "cafe_mc_samples.csv": "cafe_mc_samples.csv"
            if (mc and mc.get("samples_df") is not None) else None,
            "run.json": "run.json",
            "cafe_run.log": "cafe_run.log",
            "cafe_native": relative_to(native_out, out),
            "config_used": "config_used",
        }
        run["line_detections"] = _detection_summary(key_df)
        run["line_ratios"] = _ratio_summary(key_df)
        run["continuum"] = comp_extra
        run["runtime_s"] = time.time() - started
        run["warnings"] += [
            "CAFE uses lmfit least squares, not MCMC; the uncertainty "
            "products are a post-fit multivariate-normal draw from the "
            "lmfit covariance.",
            "CAFE v1.0.1's ErrSpec option is present in default_opt.cafe but "
            "is not applied by the released code; the error floor is applied "
            "by this adapter instead.",
        ]
        if any(not bool(s["covered"]) for s in
               [{"covered": r["covered"]} for _, r in key_df.iterrows()]):
            run["limitations"].append(
                "Some key lines/PAHs fall in zeroed detector gaps of the "
                "canonical x1d product; they are reported as not_covered, "
                "not as non-detections.")
        if spec["meta"]["n_pixels"] < 500:
            run["limitations"].append("Fewer than 500 spectral pixels; "
                                      "the decomposition is under-constrained.")
        if not stats["errorbars"]:
            run["limitations"].append(
                "lmfit did not return error bars; covariance-based MC is "
                "unavailable or falls back to diagonal stderr.")
        write_json(out / "run.json", run)
        print(f"[cafe_line] done status={run['status']} "
              f"redchi={stats['redchi']:.3f} rms_rel={stats['rms_rel']:.3f} "
              f"-> {out}")
        return 0
    except Exception as exc:
        run["status"] = "failed"
        run["error"] = f"{type(exc).__name__}: {exc}"
        run["traceback"] = traceback.format_exc()
        run["runtime_s"] = time.time() - started
        try:
            write_json(out / "run.json", run)
        except Exception:
            pass
        traceback.print_exc()
        print(f"[cafe_line] FAILED: {type(exc).__name__}: {exc}")
        return 2
    finally:
        log_fh.flush()
        sys.stdout = real_stdout
        sys.stderr = real_stderr
        log_fh.close()


if __name__ == "__main__":
    raise SystemExit(main())
