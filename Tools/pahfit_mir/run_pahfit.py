#!/usr/bin/env python3
"""PAHFIT 2.0 fit for JWST/MIRI MRS, PAHFIT s1d, or Spitzer IRS spectra.

The fitter is deliberately conservative: it reports the native flux unit,
the number of pixels, a relative residual metric and a stability flag.  MIRI
MRS spectra can be binned to a coarser grid before fitting; this is important
for PDS 456, where the native high-resolution short/long spectra otherwise
drive the PAH solution.

In addition to the historical PAHFIT products this driver can
(1) extract a homogeneous line/feature/continuum table and
(2) estimate feature-flux uncertainties with either a fast linearized
    covariance mode or a full-refit bootstrap.  The default remains the
    historical behaviour (``--mc-samples 0``), so pipeline runs are not
    slowed down unless Monte Carlo is explicitly requested.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import astropy.units as u
from astropy.io import fits
from astropy.nddata import StdDevUncertainty
from astropy.table import Table
from specutils import Spectrum1D
import pahfit
from pahfit.model import Model
from pahfit.scripts.plot_pahfit import default_layout_plot

MIRI_ALL = [
    "jwst.miri.mrs.ch1.A", "jwst.miri.mrs.ch1.B", "jwst.miri.mrs.ch1.C",
    "jwst.miri.mrs.ch2.A", "jwst.miri.mrs.ch2.B", "jwst.miri.mrs.ch2.C",
    "jwst.miri.mrs.ch3.A", "jwst.miri.mrs.ch3.B", "jwst.miri.mrs.ch3.C",
    "jwst.miri.mrs.ch4.A", "jwst.miri.mrs.ch4.B", "jwst.miri.mrs.ch4.C",
]

# NumPy 2 renamed trapz -> trapezoid.  Keep one helper so the code works in
# both the Docker image and a local development environment.
def _trapz(y, x):
    fn = getattr(np, "trapezoid", None)
    if fn is None:
        fn = np.trapz
    return float(fn(np.asarray(y, float), np.asarray(x, float)))


def _config_root() -> Path:
    """Locate ``configs/pahfit_mir`` both in-repo and inside the image."""
    here = Path(__file__).resolve().parent
    for base in (here, here.parent, here.parent.parent):
        cand = base / "configs" / "pahfit_mir"
        if cand.is_dir():
            return cand
    return here.parent.parent / "configs" / "pahfit_mir"


CONFIG_ROOT = _config_root()


def resolve_config(value: str | None) -> tuple[Path | None, dict]:
    """Read a JSON config given a path, a directory name, or a config name."""
    if not value:
        return None, {}
    p = Path(value).expanduser()
    if not p.is_file():
        cand = CONFIG_ROOT / str(value) / "config.json"
        if cand.is_file():
            p = cand
        else:
            raise SystemExit(
                f"config not found: {value!r} (tried {p} and {cand})"
            )
    try:
        cfg = json.loads(p.read_text())
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"cannot read config {p}: {exc}") from exc
    if not isinstance(cfg, dict):
        raise SystemExit(f"config {p} must contain a JSON object")
    return p, cfg


def _cfg_get(cfg: dict, *keys, default=None):
    cur = cfg
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _instrument_default(cfg: dict):
    v = _cfg_get(cfg, "input", "instrument", default=None)
    if isinstance(v, (list, tuple)):
        return ",".join(str(x) for x in v)
    return v


def read_s1d(path: Path):
    with fits.open(path, memmap=False) as h:
        d = h[1].data
        return (np.asarray(d["wavelength"], float), np.asarray(d["flux"], float),
                np.asarray(d["uncertainty"], float), np.zeros(len(d)), "MJy/sr")


def read_x1d(path: Path):
    with fits.open(path, memmap=False) as h:
        d = h["EXTRACT1D"].data
        names = set(d.columns.names)
        w = np.asarray(d["WAVELENGTH"], float)
        if "FLUX" in names:
            fl = np.asarray(d["FLUX"], float)
            er = np.asarray(d["FLUX_ERROR"], float)
            unit = "Jy"
        else:
            fl = np.asarray(d["SURF_BRIGHT"], float)
            er = np.asarray(d["SB_ERROR"], float)
            unit = "MJy/sr"
        dq = np.asarray(d["DQ"], float) if "DQ" in names else np.zeros(len(w))
        return w, fl, er, dq, unit


def read_irs_tbl(path: Path):
    try:
        t = Table.read(path, format="ascii.ipac")
    except Exception:
        t = Table.read(path, format="ascii")
    names = {c.lower(): c for c in t.colnames}
    w = np.asarray(t[names["wavelength"]], float)
    fl = np.asarray(t[names["flux_density"]], float)
    er = np.asarray(t[names.get("error", "flux_density_err")], float)
    good = np.ones(len(w), dtype=bool)
    if "bit-flag" in names:
        good = np.asarray(t[names["bit-flag"]]) == 0
    order = np.asarray(t[names["order"]], int) if "order" in names else np.zeros(len(w), int)
    return w, fl, er, (~good).astype(float), "Jy", order


def bin_spectrum(w, f, e, width: float | None):
    """Median-bin a spectrum; errors combine in quadrature."""
    if not width or width <= 0:
        return w, f, e
    edges = np.arange(float(np.nanmin(w)), float(np.nanmax(w)) + width, width)
    idx = np.digitize(w, edges) - 1
    outw, outf, oute = [], [], []
    for i in range(len(edges) - 1):
        m = idx == i
        if m.sum() == 0:
            continue
        outw.append(float(np.nanmedian(w[m])))
        outf.append(float(np.nanmedian(f[m])))
        oute.append(float(np.sqrt(np.nansum(e[m] ** 2))) / max(1, m.sum()))
    return np.asarray(outw), np.asarray(outf), np.asarray(oute)


# ---------------------------------------------------------------------------
# Feature table / line table
# ---------------------------------------------------------------------------

def _row_scalar(row, col):
    """Read a scalar from a PAHFIT features row, including (val, min, max)."""
    try:
        v = row[col]
    except Exception:
        return float("nan")
    try:
        if np.ma.is_masked(v):
            return float("nan")
    except Exception:
        pass
    try:
        return float(v["val"])
    except Exception:
        try:
            return float(v)
        except Exception:
            return float("nan")


def _submodel(model, name):
    """Return a fitted astropy submodel by feature name, or None."""
    try:
        m = model.fitter.model
    except Exception:
        return None
    try:
        return m[str(name)]
    except Exception:
        return None


def _component(model, name, lam):
    comp = _submodel(model, name)
    if comp is None:
        return np.zeros_like(np.asarray(lam, float))
    try:
        return np.asarray(comp(np.asarray(lam, float)), float)
    except Exception:
        return np.zeros_like(np.asarray(lam, float))


def _attenuation(model, lam):
    """Evaluate the product of all multiplicative (attenuation) components."""
    lam = np.asarray(lam, float)
    out = np.ones_like(lam)
    try:
        comps = list(model.fitter.multiplicative_components)
    except Exception:
        return out
    for c in comps:
        name = str(getattr(c, "name", ""))
        comp = _submodel(model, name)
        if comp is None:
            comp = c
        try:
            out = out * np.asarray(comp(lam), float)
        except Exception:
            pass
    return out


def _scale_features_inplace(model, factor):
    """Scale additive feature amplitudes/powers by ``factor``.

    PAHFIT's line/dust-feature powers and the starlight/dust-continuum
    amplitudes are linear in the input flux.  Temperatures, wavelengths,
    widths and the multiplicative attenuation are not.  This helper is used
    only for the optional internal fit normalization and for writing the
    historical-unit ECSV; it does not change the physical model.
    """
    if not np.isfinite(factor) or factor == 1.0:
        return model
    ft = model.features
    for i, row in enumerate(ft):
        kind = str(row["kind"])
        if kind in ("line", "dust_feature"):
            cols = ("power",)
        elif kind in ("starlight", "dust_continuum"):
            cols = ("tau",)
        else:
            continue
        for col in cols:
            try:
                v = float(ft[col]["val"][i])
                if np.isfinite(v):
                    ft[col]["val"][i] = v * float(factor)
            except Exception:
                pass
    return model


def _scaled_model_copy(model, factor):
    out = copy.deepcopy(model)
    return _scale_features_inplace(out, factor)


def _param_component_map(model):
    """Map global compound-model parameter names to (feature, local, index)."""
    m = model.fitter.model
    names = list(m.param_names)
    out = {}
    k = 0
    try:
        for i, sn in enumerate(m.submodel_names):
            comp = m[str(sn)]
            for local in comp.param_names:
                if k >= len(names):
                    break
                out[names[k]] = (str(sn), str(local), i)
                k += 1
    except Exception:
        k = 0
    if k != len(names):
        # Fallback for astropy versions that name compound parameters
        # ``<local>_<submodel index>`` rather than in sequential order.
        out = {}
        for n in names:
            hit = None
            for i, sn in enumerate(m.submodel_names):
                suffix = f"_{i}"
                if str(n).endswith(suffix):
                    hit = (str(sn), str(n)[: -len(suffix)], i)
                    break
            out[n] = hit or (str(n), str(n), 0)
    return out


def _feature_geometry(row, kind, rest_min, rest_max):
    """Return (rest wavelength, fwhm, reference wavelength) for one feature."""
    wl = _row_scalar(row, "wavelength")
    fwhm = _row_scalar(row, "fwhm")
    if kind == "dust_continuum":
        ref = 20.0
        if not np.isfinite(wl) or wl <= 0:
            wl = ref
    elif kind == "starlight":
        ref = 5.0
        if np.isfinite(rest_min):
            ref = max(ref, float(rest_min))
        if not np.isfinite(wl) or wl <= 0:
            wl = ref
    else:
        ref = wl
    if kind in ("line", "dust_feature") and (not np.isfinite(fwhm) or fwhm <= 0):
        fwhm = 0.1 * max(wl, 1e-3)
    return float(wl), float(fwhm), float(ref)


def compute_feature_records(model, spec, z, flux_scale=1.0):
    """Build the unified gas-line / PAH / continuum table from the fit."""
    ft = model.features
    enabled = set(str(x) for x in getattr(model, "enabled_features", []))
    lam_obs = spec.spectral_axis.to_value(u.micron)
    rest_min = float(np.nanmin(lam_obs) / (1.0 + z))
    rest_max = float(np.nanmax(lam_obs) / (1.0 + z))
    att_names = [str(c.name) for c in getattr(model.fitter, "multiplicative_components", [])]
    records = []
    for row in ft:
        name = str(row["name"])
        kind = str(row["kind"])
        group = str(row["group"])
        included = name in enabled
        wl, fwhm, ref = _feature_geometry(row, kind, rest_min, rest_max)
        rec = {
            "name": name,
            "group": group,
            "kind": kind,
            "included_in_fit": bool(included),
            "rest_wavelength_um": wl if np.isfinite(wl) else float("nan"),
            "observed_wavelength_um": (wl * (1.0 + z)) if np.isfinite(wl) else float("nan"),
            "fwhm_um": fwhm if np.isfinite(fwhm) else float("nan"),
            "quantity": "",
            "unit": "",
            "flux_observed": float("nan"),
            "flux_intrinsic": float("nan"),
            "flux_peak_observed": float("nan"),
            "flux_peak_intrinsic": float("nan"),
            "ew_um": float("nan"),
            "temperature_K": _row_scalar(row, "temperature"),
            "tau": _row_scalar(row, "tau"),
            "tau_sil": float("nan"),
            "attenuation_at_feature": float("nan"),
            "notes": "",
            "snr": float("nan"),
            "spec_index": None,
            "at_bound": False,
        }
        if not included:
            rec["notes"] = "outside fitted wavelength range"
            records.append(rec)
            continue

        if kind in ("line", "dust_feature"):
            half = max(8.0 * abs(fwhm), 1e-4 * max(abs(wl), 1e-3))
            lo = max(wl - half, 1e-4)
            hi = wl + half
            grid = np.linspace(lo, hi, 401)
            comp = _component(model, name, grid)
            att = _attenuation(model, grid)
            obs = comp * att
            rec["quantity"] = "integrated_intensity"
            rec["unit"] = "MJy/sr um"
            rec["flux_observed"] = _trapz(obs, grid)
            rec["flux_intrinsic"] = _trapz(comp, grid)
            rec["flux_peak_intrinsic"] = float(np.nanmax(comp)) if np.isfinite(comp).any() else float("nan")
            rec["flux_peak_observed"] = rec["flux_peak_intrinsic"] / (1.0 + z)
            rec["attenuation_at_feature"] = float(_attenuation(model, np.array([wl]))[0])
            rec["notes"] = "integrated feature intensity; observed = S07-attenuated"
            # Equivalent width uses the observed continuum at the feature.
            cont = np.zeros_like(grid)
            for cname in [str(r["name"]) for r in ft
                          if str(r["kind"]) in ("dust_continuum", "starlight")]:
                cont = cont + _component(model, cname, grid)
            cont_obs = cont * att
            good = np.isfinite(obs) & np.isfinite(cont_obs) & (cont_obs > 0)
            if good.sum() > 2:
                rec["ew_um"] = _trapz(obs[good] / cont_obs[good], grid[good])
        elif kind == "dust_continuum":
            lamref = np.array([ref], float)
            comp = _component(model, name, lamref)
            att = _attenuation(model, lamref)
            rec["quantity"] = f"flux_density_{ref:g}um"
            rec["unit"] = "MJy/sr"
            rec["flux_intrinsic"] = float(comp[0])
            rec["flux_observed"] = float(comp[0] * att[0]) / (1.0 + z)
            rec["flux_peak_intrinsic"] = rec["flux_intrinsic"]
            rec["flux_peak_observed"] = rec["flux_observed"]
            rec["attenuation_at_feature"] = float(att[0])
            rec["notes"] = f"flux density at rest {ref:g} um; not an integrated flux"
        elif kind == "starlight":
            lamref = np.array([ref], float)
            comp = _component(model, name, lamref)
            att = _attenuation(model, lamref)
            rec["quantity"] = f"flux_density_{ref:g}um"
            rec["unit"] = "MJy/sr"
            rec["flux_intrinsic"] = float(comp[0])
            rec["flux_observed"] = float(comp[0] * att[0]) / (1.0 + z)
            rec["flux_peak_intrinsic"] = rec["flux_intrinsic"]
            rec["flux_peak_observed"] = rec["flux_observed"]
            rec["attenuation_at_feature"] = float(att[0])
            rec["notes"] = f"stellar continuum flux density at rest {ref:g} um"
        elif kind in ("attenuation", "absorption"):
            comp = _submodel(model, name)
            val = float("nan")
            if comp is not None:
                for attr in ("tau_sil", "tau"):
                    if hasattr(comp, attr):
                        try:
                            val = float(getattr(comp, attr).value)
                            break
                        except Exception:
                            pass
            rec["quantity"] = "tau_sil" if kind == "attenuation" else "tau"
            rec["unit"] = ""
            rec["flux_observed"] = val
            rec["flux_intrinsic"] = val
            rec["tau_sil"] = val if kind == "attenuation" else float("nan")
            rec["notes"] = "multiplicative attenuation parameter"
        else:
            rec["notes"] = f"unsupported feature kind: {kind}"
        if np.isfinite(flux_scale) and flux_scale != 1.0:
            for key in ("flux_observed", "flux_intrinsic",
                        "flux_peak_observed", "flux_peak_intrinsic"):
                if np.isfinite(rec[key]):
                    rec[key] = float(rec[key]) * float(flux_scale)
        records.append(rec)
    return records


# ---------------------------------------------------------------------------
# Linearized covariance and Monte Carlo
# ---------------------------------------------------------------------------

def _param_bounds(model, name):
    try:
        return tuple(model.fitter.model.bounds.get(name, (None, None)))
    except Exception:
        return (None, None)


def _at_bound(value, lo, hi):
    if lo is not None and (value == lo or (value != 0 and abs(value - lo) <= 1e-10 * abs(value))):
        return True
    if hi is not None and (value == hi or (value != 0 and abs(value - hi) <= 1e-10 * abs(value))):
        return True
    return False


def _free_parameters(model):
    m = model.fitter.model
    try:
        fixed = dict(m.fixed)
    except Exception:
        fixed = {}
    pmap = _param_component_map(model)
    all_free = [n for n in m.param_names if not fixed.get(n, False)]
    free, at_bound = [], []
    for n in all_free:
        p = float(getattr(m, n).value)
        lo, hi = _param_bounds(model, n)
        if _at_bound(p, lo, hi):
            at_bound.append((n, p))
        else:
            free.append(n)
    return free, at_bound, pmap


def _param_scales(model, free, pmap):
    m = model.fitter.model
    groups: dict[str, list[float]] = {}
    for n in free:
        _, local, _ = pmap.get(n, (None, str(n), 0))
        p = float(getattr(m, n).value)
        if p != 0 and np.isfinite(p):
            groups.setdefault(local, []).append(abs(p))
    med = {k: float(np.median(v)) for k, v in groups.items() if v}
    scales = []
    for n in free:
        _, local, _ = pmap.get(n, (None, str(n), 0))
        p = float(getattr(m, n).value)
        if local in ("amplitude", "power"):
            s = max(abs(p), med.get(local, 1.0) * 1e-3, 1e-12)
        elif local == "temperature":
            s = max(abs(p), 1.0)
        elif local in ("mean", "x_0", "wavelength"):
            s = max(abs(p), 1e-4)
        elif local in ("stddev", "fwhm"):
            s = max(abs(p), 1e-6)
        elif local in ("tau_sil", "tau"):
            s = max(abs(p), 1e-4)
        else:
            s = max(abs(p), 1e-6)
        scales.append(s)
    return np.asarray(scales, float)


def _step(model, name, p0, scale):
    lo, hi = _param_bounds(model, name)
    h = 1e-3 * abs(scale)
    if h == 0:
        h = 1e-9
    if lo is not None and p0 - h < lo:
        h = max(p0 - lo, 1e-12 * abs(scale))
    if hi is not None and p0 + h > hi:
        h = max(hi - p0, 1e-12 * abs(scale))
    return max(h, 1e-30)


def _set_param(model, name, value):
    setattr(model.fitter.model, str(name), float(value))


def _model_jacobian(model, free, scales, lam_rest, sigma_rest):
    m = model.fitter.model
    jac = np.zeros((len(lam_rest), len(free)), float)
    for j, name in enumerate(free):
        p0 = float(getattr(m, name).value)
        h = _step(model, name, p0, scales[j])
        lo, hi = _param_bounds(model, name)
        central = True
        if lo is not None and p0 - h < lo:
            central = False
        if hi is not None and p0 + h > hi:
            central = False
        if central:
            _set_param(model, name, p0 + h)
            yp = np.asarray(m(lam_rest), float)
            _set_param(model, name, p0 - h)
            ym = np.asarray(m(lam_rest), float)
            _set_param(model, name, p0)
            jac[:, j] = (yp - ym) / (2.0 * h)
        else:
            _set_param(model, name, p0)
            y0 = np.asarray(m(lam_rest), float)
            direction = 1.0
            if hi is not None and p0 + h > hi:
                direction = -1.0
            _set_param(model, name, p0 + direction * h)
            y1 = np.asarray(m(lam_rest), float)
            _set_param(model, name, p0)
            jac[:, j] = direction * (y1 - y0) / h
    return jac * scales / np.asarray(sigma_rest, float)[:, None]


def _covariance_from_jacobian(jw, scales, rcond):
    if jw.size == 0 or not np.isfinite(jw).all():
        return None
    _, s, vt = np.linalg.svd(jw, full_matrices=False)
    if s.size == 0 or not np.isfinite(s[0]) or s[0] <= 0:
        return None
    rank = int(np.sum(s > float(rcond) * s[0]))
    if rank < 1:
        return None
    cu = (vt[:rank].T / s[:rank] ** 2) @ vt[:rank]
    cp = scales[:, None] * cu * scales[None, :]
    cond = float(s[0] / s[rank - 1]) if rank > 0 else float("inf")
    return {"cu": cu, "cp": cp, "singular_values": s, "rank": rank,
            "condition": cond, "rcond": float(rcond)}


def _quantity_specs(model, records, z):
    """Precompute the wavelength grids needed for feature-flux evaluation."""
    specs = []
    for idx, rec in enumerate(records):
        if not rec["included_in_fit"]:
            continue
        name, kind = rec["name"], rec["kind"]
        if kind in ("line", "dust_feature"):
            wl = rec["rest_wavelength_um"]
            fwhm = rec["fwhm_um"]
            half = max(8.0 * abs(fwhm), 1e-4 * max(abs(wl), 1e-3))
            grid = np.linspace(max(wl - half, 1e-4), wl + half, 401)
            specs.append({"record": idx, "name": name, "kind": kind,
                          "mode": "integrated", "grid": grid,
                          "ref": wl, "unit": "MJy/sr um",
                          "quantity": "integrated_intensity"})
        elif kind in ("dust_continuum", "starlight"):
            ref = 20.0 if kind == "dust_continuum" else max(5.0, float(rec["rest_wavelength_um"]))
            specs.append({"record": idx, "name": name, "kind": kind,
                          "mode": "flux_density", "grid": np.array([ref], float),
                          "ref": ref, "unit": "MJy/sr",
                          "quantity": f"flux_density_{ref:g}um"})
        elif kind in ("attenuation", "absorption"):
            specs.append({"record": idx, "name": name, "kind": kind,
                          "mode": "scalar", "grid": None, "ref": None,
                          "unit": "", "quantity": "tau_sil" if kind == "attenuation" else "tau"})
    return specs


def _quantities_for_model(model, specs, z):
    obs, intr = [], []
    for sp in specs:
        if sp["mode"] == "integrated":
            grid = sp["grid"]
            comp = _component(model, sp["name"], grid)
            att = _attenuation(model, grid)
            obs.append(_trapz(comp * att, grid))
            intr.append(_trapz(comp, grid))
        elif sp["mode"] == "flux_density":
            lam = np.asarray(sp["grid"], float)
            comp = _component(model, sp["name"], lam)[0]
            att = _attenuation(model, lam)[0]
            obs.append(float(comp * att) / (1.0 + z))
            intr.append(float(comp))
        else:
            comp = _submodel(model, sp["name"])
            val = float("nan")
            if comp is not None:
                for attr in ("tau_sil", "tau"):
                    if hasattr(comp, attr):
                        try:
                            val = float(getattr(comp, attr).value)
                            break
                        except Exception:
                            pass
            obs.append(val)
            intr.append(val)
    return np.asarray(obs, float), np.asarray(intr, float)


def _feature_gradients(model, specs, free, scales, z):
    q0o, q0i = _quantities_for_model(model, specs, z)
    go = np.zeros((len(specs), len(free)), float)
    gi = np.zeros((len(specs), len(free)), float)
    m = model.fitter.model
    for j, name in enumerate(free):
        p0 = float(getattr(m, name).value)
        h = _step(model, name, p0, scales[j])
        lo, hi = _param_bounds(model, name)
        central = True
        if lo is not None and p0 - h < lo:
            central = False
        if hi is not None and p0 + h > hi:
            central = False
        if central:
            _set_param(model, name, p0 + h)
            qpo, qpi = _quantities_for_model(model, specs, z)
            _set_param(model, name, p0 - h)
            qmo, qmi = _quantities_for_model(model, specs, z)
            _set_param(model, name, p0)
            go[:, j] = (qpo - qmo) / (2.0 * h)
            gi[:, j] = (qpi - qmi) / (2.0 * h)
        else:
            direction = 1.0
            if hi is not None and p0 + h > hi:
                direction = -1.0
            _set_param(model, name, p0)
            q0o2, q0i2 = _quantities_for_model(model, specs, z)
            _set_param(model, name, p0 + direction * h)
            q1o, q1i = _quantities_for_model(model, specs, z)
            _set_param(model, name, p0)
            go[:, j] = direction * (q1o - q0o2) / h
            gi[:, j] = direction * (q1i - q0i2) / h
    return q0o, q0i, go * scales[None, :], gi * scales[None, :]


def _draw_covariance_samples(model, free, scales, cu, n_samples, rng):
    if n_samples <= 0 or len(free) == 0:
        return np.zeros((0, len(free))), 0
    cu = (cu + cu.T) / 2.0
    evals, evecs = np.linalg.eigh(cu)
    evals = np.clip(evals, 0.0, None)
    if np.all(evals <= 0):
        return np.zeros((n_samples, len(free))), 0
    chol = evecs * np.sqrt(evals)[None, :]
    u = rng.normal(size=(n_samples, len(free))) @ chol.T
    clipped = 0
    m = model.fitter.model
    p0 = np.array([float(getattr(m, n).value) for n in free], float)
    for i in range(n_samples):
        for j, n in enumerate(free):
            lo, hi = _param_bounds(model, n)
            val = p0[j] + scales[j] * u[i, j]
            v2 = val
            if lo is not None:
                v2 = max(v2, lo)
            if hi is not None:
                v2 = min(v2, hi)
            if v2 != val:
                clipped += 1
            u[i, j] = (v2 - p0[j]) / scales[j] if scales[j] != 0 else 0.0
    return u, clipped


def _apply_samples(model, free, p0, scales, u):
    for j, n in enumerate(free):
        _set_param(model, n, p0[j] + scales[j] * u[j])


def run_covariance_mc(model, spec, z, records, specs, n_samples, rcond, rng,
                      chi2_red=float("nan"), flux_scale=1.0):
    free, at_bound, pmap = _free_parameters(model)
    if not free:
        return None
    scales = _param_scales(model, free, pmap)
    lam_rest = spec.spectral_axis.to_value(u.micron) / (1.0 + z)
    sigma = np.asarray(spec.uncertainty.array, float) * (1.0 + z)
    good = np.isfinite(lam_rest) & np.isfinite(sigma) & (sigma > 0)
    if good.sum() <= len(free):
        return None
    jw = _model_jacobian(model, free, scales, lam_rest[good], sigma[good])
    cov = _covariance_from_jacobian(jw, scales, rcond)
    if cov is None:
        return None
    q0o, q0i, go, gi = _feature_gradients(model, specs, free, scales, z)
    err_o = np.sqrt(np.clip(np.einsum("ij,jk,ik->i", go, cov["cu"], go), 0, None))
    err_i = np.sqrt(np.clip(np.einsum("ij,jk,ik->i", gi, cov["cu"], gi), 0, None))

    draws, clipped = _draw_covariance_samples(model, free, scales, cov["cu"], n_samples, rng)
    m = model.fitter.model
    p0 = np.array([float(getattr(m, n).value) for n in free], float)
    samples_o = np.full((n_samples, len(specs)), np.nan, float)
    samples_i = np.full((n_samples, len(specs)), np.nan, float)
    n_nonphysical = 0
    for i in range(n_samples):
        _apply_samples(model, free, p0, scales, draws[i])
        so, si = _quantities_for_model(model, specs, z)
        samples_o[i] = so
        samples_i[i] = si
        if np.any(np.isfinite(si) & (si < 0)):
            n_nonphysical += 1
    _apply_samples(model, free, p0, scales, np.zeros(len(free)))
    err_sample_o = np.nanstd(samples_o, axis=0, ddof=1) if n_samples > 1 else np.zeros(len(specs))
    err_sample_i = np.nanstd(samples_i, axis=0, ddof=1) if n_samples > 1 else np.zeros(len(specs))
    q16_o = np.nanpercentile(samples_o, 15.87, axis=0) if n_samples > 1 else q0o
    q84_o = np.nanpercentile(samples_o, 84.13, axis=0) if n_samples > 1 else q0o
    if np.isfinite(flux_scale) and flux_scale != 1.0:
        err_o = err_o * float(flux_scale)
        err_i = err_i * float(flux_scale)
        err_sample_o = err_sample_o * float(flux_scale)
        err_sample_i = err_sample_i * float(flux_scale)
        samples_o = samples_o * float(flux_scale)
        samples_i = samples_i * float(flux_scale)
        q0o = q0o * float(flux_scale)
        q0i = q0i * float(flux_scale)
        q16_o = q16_o * float(flux_scale)
        q84_o = q84_o * float(flux_scale)
    return {
        "method": "covariance",
        "free": free,
        "at_bound": at_bound,
        "n_free": len(free),
        "n_free_all": len(free) + len(at_bound),
        "n_at_bound": len(at_bound),
        "n_data": int(good.sum()),
        "scales": scales,
        "cov": cov,
        "q0o": q0o,
        "q0i": q0i,
        "err_o": err_o,
        "err_i": err_i,
        "samples_o": samples_o,
        "samples_i": samples_i,
        "err_sample_o": err_sample_o,
        "err_sample_i": err_sample_i,
        "q16_o": q16_o,
        "q84_o": q84_o,
        "n_nonphysical": n_nonphysical,
        "n_clipped": clipped,
        "chi2_red": chi2_red,
    }


def run_bootstrap_mc(model, spec, z, specs, n_samples, seed, maxiter, mode,
                     flux_scale=1.0):
    rng = np.random.default_rng(seed)
    y = np.asarray(spec.flux.value, float)
    sigma = np.asarray(spec.uncertainty.array, float)
    lam_obs = spec.spectral_axis.to_value(u.micron)
    lam_rest = lam_obs / (1.0 + z)
    try:
        pred_obs = np.asarray(model.fitter.model(lam_rest), float) / (1.0 + z)
    except Exception:
        pred_obs = np.full_like(y, np.nan)
    resid = y - pred_obs
    base = copy.deepcopy(model)
    flux_unit = spec.flux.unit
    samples_o = np.full((n_samples, len(specs)), np.nan, float)
    samples_i = np.full((n_samples, len(specs)), np.nan, float)
    status = []
    nfev = []
    runtime = []
    for i in range(n_samples):
        t0 = time.time()
        mb = copy.deepcopy(base)
        mb.features.meta["instrument"] = spec.meta.get("instrument", "")
        if mode == "residual":
            good = np.isfinite(resid) & np.isfinite(sigma) & (sigma > 0)
            if good.sum() > 2:
                yb = pred_obs + rng.choice(resid[good], size=len(resid), replace=True)
            else:
                yb = y + rng.normal(0.0, sigma)
        else:
            yb = y + rng.normal(0.0, sigma)
        sb = Spectrum1D(spectral_axis=lam_obs * u.micron,
                        flux=np.asarray(yb, float) * flux_unit,
                        uncertainty=StdDevUncertainty(np.asarray(sigma, float) * flux_unit))
        sb.meta["instrument"] = spec.meta.get("instrument", "")
        st = "ok"
        try:
            mb.fit(sb, redshift=z, maxiter=maxiter, verbose=False)
            so, si = _quantities_for_model(mb, specs, z)
            samples_o[i] = so
            samples_i[i] = si
        except Exception as exc:  # noqa: BLE001
            st = f"fit_failed:{type(exc).__name__}"
        status.append(st)
        try:
            nfev.append(int(mb.fitter.fit_info.get("nfev", 0)))
        except Exception:
            nfev.append(0)
        runtime.append(time.time() - t0)
    n_ok = int(sum(s == "ok" for s in status))
    err_o = np.nanstd(samples_o, axis=0, ddof=1) if n_ok > 1 else np.full(len(specs), np.nan)
    err_i = np.nanstd(samples_i, axis=0, ddof=1) if n_ok > 1 else np.full(len(specs), np.nan)
    q16 = np.nanpercentile(samples_o, 15.87, axis=0) if n_ok > 1 else np.full(len(specs), np.nan)
    q84 = np.nanpercentile(samples_o, 84.13, axis=0) if n_ok > 1 else np.full(len(specs), np.nan)
    if np.isfinite(flux_scale) and flux_scale != 1.0:
        samples_o = samples_o * float(flux_scale)
        samples_i = samples_i * float(flux_scale)
        err_o = err_o * float(flux_scale)
        err_i = err_i * float(flux_scale)
        q16 = q16 * float(flux_scale)
        q84 = q84 * float(flux_scale)
    return {
        "method": "bootstrap",
        "samples_o": samples_o,
        "samples_i": samples_i,
        "err_o": err_o,
        "err_i": err_i,
        "err_sample_o": err_o,
        "err_sample_i": err_i,
        "q16_o": q16,
        "q84_o": q84,
        "status": status,
        "nfev": nfev,
        "runtime": runtime,
        "n_ok": n_ok,
        "n_failed": int(n_samples - n_ok),
        "bootstrap_mode": mode,
    }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def _fmt(v):
    try:
        return f"{float(v):.10g}"
    except Exception:
        return ""


def write_lines_csv(path: Path, records):
    cols = [
        "category", "name", "group", "kind", "rest_wavelength_um",
        "observed_wavelength_um", "fwhm_um", "included_in_fit", "quantity",
        "unit", "flux_observed", "flux_intrinsic", "flux_peak_observed",
        "flux_peak_intrinsic", "ew_um", "temperature_K", "tau", "tau_sil",
        "attenuation_at_feature", "snr", "notes",
    ]
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in records:
            kind = r["kind"]
            if kind == "line":
                cat = "gas_line"
            elif kind == "dust_feature":
                cat = "pah_feature"
            elif kind == "dust_continuum":
                cat = "dust_continuum"
            elif kind == "starlight":
                cat = "starlight"
            elif kind == "attenuation":
                cat = "attenuation"
            elif kind == "absorption":
                cat = "absorption"
            else:
                cat = kind
            w.writerow({
                "category": cat,
                "name": r["name"],
                "group": r["group"],
                "kind": kind,
                "rest_wavelength_um": _fmt(r["rest_wavelength_um"]),
                "observed_wavelength_um": _fmt(r["observed_wavelength_um"]),
                "fwhm_um": _fmt(r["fwhm_um"]),
                "included_in_fit": str(bool(r["included_in_fit"])).lower(),
                "quantity": r["quantity"],
                "unit": r["unit"],
                "flux_observed": _fmt(r["flux_observed"]),
                "flux_intrinsic": _fmt(r["flux_intrinsic"]),
                "flux_peak_observed": _fmt(r["flux_peak_observed"]),
                "flux_peak_intrinsic": _fmt(r["flux_peak_intrinsic"]),
                "ew_um": _fmt(r["ew_um"]),
                "temperature_K": _fmt(r["temperature_K"]),
                "tau": _fmt(r["tau"]),
                "tau_sil": _fmt(r["tau_sil"]),
                "attenuation_at_feature": _fmt(r["attenuation_at_feature"]),
                "snr": _fmt(r["snr"]),
                "notes": r["notes"],
            })


def write_uncertainties_csv(path: Path, records, specs, mc, method, n_samples,
                            scale_chi2=None):
    cols = [
        "feature", "group", "kind", "quantity", "unit", "rest_wavelength_um",
        "flux", "err", "err_delta", "err_low", "err_high", "flux_intrinsic",
        "err_intrinsic", "method", "n_samples", "included_in_fit", "status",
    ]
    by_record = {sp["record"]: k for k, sp in enumerate(specs)}
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for idx, r in enumerate(records):
            k = by_record.get(idx)
            status = "ok"
            flux = r["flux_observed"]
            flux_i = r["flux_intrinsic"]
            err = err_d = err_lo = err_hi = err_i = float("nan")
            if not r["included_in_fit"]:
                status = "excluded_from_fit"
            elif k is None:
                status = "no_quantity"
            else:
                err = float(mc["err_o"][k]) if k < len(mc["err_o"]) else float("nan")
                err_i = float(mc["err_i"][k]) if k < len(mc["err_i"]) else float("nan")
                if method == "covariance":
                    err_d = err
                else:
                    err_d = float("nan")
                try:
                    q16 = float(mc["q16_o"][k])
                    q84 = float(mc["q84_o"][k])
                    if np.isfinite(q16) and np.isfinite(q84):
                        err_lo = flux - q16
                        err_hi = q84 - flux
                except Exception:
                    pass
                if not np.isfinite(err):
                    status = "mc_unavailable"
                elif err == 0 and (not np.isfinite(flux) or flux == 0):
                    status = "at_bound_or_zero"
                elif (method == "covariance"
                      and mc.get("cov", {}).get("rank", 0) < mc.get("n_free", 0)
                      and np.isfinite(flux) and flux != 0
                      and err <= 1e-6 * abs(flux)):
                    status = "covariance_rank_deficient"
                    err = float("nan")
                    err_d = float("nan")
                    err_i = float("nan")
                    err_lo = float("nan")
                    err_hi = float("nan")
            if scale_chi2 is not None and np.isfinite(err) and np.isfinite(scale_chi2):
                err_d = err * np.sqrt(scale_chi2)
            w.writerow({
                "feature": r["name"],
                "group": r["group"],
                "kind": r["kind"],
                "quantity": r["quantity"],
                "unit": r["unit"],
                "rest_wavelength_um": _fmt(r["rest_wavelength_um"]),
                "flux": _fmt(flux),
                "err": _fmt(err),
                "err_delta": _fmt(err_d),
                "err_low": _fmt(err_lo),
                "err_high": _fmt(err_hi),
                "flux_intrinsic": _fmt(flux_i),
                "err_intrinsic": _fmt(err_i),
                "method": method,
                "n_samples": int(n_samples),
                "included_in_fit": str(bool(r["included_in_fit"])).lower(),
                "status": status,
            })


def write_samples_csv(path: Path, records, specs, mc, method):
    cols = ["sample"] + [sp["name"] for sp in specs]
    if method == "bootstrap":
        cols.append("status")
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        samples = mc["samples_o"]
        for i in range(samples.shape[0]):
            row = [i] + [_fmt(v) for v in samples[i]]
            if method == "bootstrap":
                row.append(mc["status"][i] if i < len(mc.get("status", [])) else "")
            w.writerow(row)


def _select_top(records, specs, mc, n=8):
    vals = []
    for k, sp in enumerate(specs):
        idx = sp["record"]
        flux = records[idx]["flux_observed"]
        err = mc["err_o"][k] if k < len(mc["err_o"]) else float("nan")
        if np.isfinite(flux) and np.isfinite(err) and err > 0 and flux != 0:
            vals.append((abs(flux) / err, k, sp, flux, err))
    vals.sort(reverse=True, key=lambda x: x[0])
    return vals[:n]


def plot_uncertainties(path: Path, records, specs, mc, method, n_samples,
                       runtime, seed, title_extra=""):
    top = _select_top(records, specs, mc, n=8)
    fig = plt.figure(figsize=(15, 15))
    gs = GridSpec(4, 3, figure=fig, height_ratios=[1.0, 1.0, 1.0, 1.25])
    ax_rel = fig.add_subplot(gs[0, :2])
    ax_fe = fig.add_subplot(gs[0, 2])
    hist_axes = [fig.add_subplot(gs[1, i]) for i in range(3)] + \
                [fig.add_subplot(gs[2, i]) for i in range(3)]
    ax_corr = fig.add_subplot(gs[3, :2])
    ax_trace = fig.add_subplot(gs[3, 2])

    colors = {"line": "#d62728", "dust_feature": "#1f77b4",
              "dust_continuum": "#ff7f0e", "starlight": "#2ca02c",
              "attenuation": "#7f7f7f", "absorption": "#8c564b"}
    for k, sp in enumerate(specs):
        idx = sp["record"]
        r = records[idx]
        flux = r["flux_observed"]
        err = mc["err_o"][k] if k < len(mc["err_o"]) else float("nan")
        if not (np.isfinite(flux) and np.isfinite(err) and flux != 0 and err > 0):
            continue
        ax_rel.errorbar(r["rest_wavelength_um"], err / abs(flux), yerr=None,
                        fmt="o", ms=5, color=colors.get(r["kind"], "k"), alpha=0.8)
        if abs(flux) / err > 20:
            ax_rel.annotate(r["name"], (r["rest_wavelength_um"], err / abs(flux)),
                            fontsize=6, rotation=30, alpha=0.7)
    ax_rel.set_xscale("log")
    ax_rel.set_yscale("log")
    ax_rel.set_xlabel("rest wavelength (um)")
    ax_rel.set_ylabel("1-sigma / |flux|")
    ax_rel.set_title("Relative uncertainty of fitted features")
    ax_rel.grid(alpha=0.25)
    for kind, col in colors.items():
        ax_rel.plot([], [], "o", color=col, label=kind)
    ax_rel.legend(fontsize=7, ncol=3, loc="best")

    for _, _, sp, flux, err in top[:15]:
        r = records[sp["record"]]
        ax_fe.errorbar(abs(flux), err, xerr=None, fmt="o", ms=5,
                       color=colors.get(r["kind"], "k"))
        ax_fe.annotate(r["name"], (abs(flux), err), fontsize=6,
                       xytext=(3, 2), textcoords="offset points")
    ax_fe.set_xscale("log")
    ax_fe.set_yscale("log")
    ax_fe.set_xlabel("|flux| (native unit)")
    ax_fe.set_ylabel("1-sigma")
    ax_fe.set_title("Flux vs uncertainty (top S/N)")
    ax_fe.grid(alpha=0.25)

    for ax, item in zip(hist_axes, top[:6]):
        _, k, sp, flux, err = item
        r = records[sp["record"]]
        vals = mc["samples_o"][:, k]
        vals = vals[np.isfinite(vals)]
        if vals.size == 0:
            ax.text(0.5, 0.5, "no samples", ha="center", va="center",
                    transform=ax.transAxes)
            ax.set_axis_off()
            continue
        if np.isfinite(flux) and flux != 0:
            vals = vals / flux
            ref, lo, hi = 1.0, mc["q16_o"][k] / flux, mc["q84_o"][k] / flux
            ax.set_xlabel("flux / best fit", fontsize=7)
        else:
            ref, lo, hi = flux, mc["q16_o"][k], mc["q84_o"][k]
        nbin = min(30, max(8, vals.size // 3))
        lo = float(np.nanmin(vals))
        hi = float(np.nanmax(vals))
        span = hi - lo
        center = max(abs(lo), abs(hi), 1.0)
        pad = max(span * 1e-3, center * 1e-12, 1e-30)
        if span <= 1e-12 * center:
            nbin = 10
        edges = np.linspace(lo - pad, hi + pad, nbin + 1)
        ax.hist(vals, bins=edges,
                color=colors.get(r["kind"], "0.5"), alpha=0.75)
        ax.axvline(ref, color="k", lw=1.2)
        ax.axvline(lo, color="k", lw=0.8, ls="--")
        ax.axvline(hi, color="k", lw=0.8, ls="--")
        ax.set_title(f"{r['name']}  ({r['quantity']})", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.2)
    for ax in hist_axes[len(top[:6]):]:
        ax.set_axis_off()

    if len(top) >= 2:
        idxs = [x[1] for x in top]
        data = np.asarray(mc["samples_o"])[:, idxs]
        mask = np.all(np.isfinite(data), axis=0)
        data = data[:, mask]
        labels = [records[specs[k]["record"]]["name"] for k in idxs if
                  np.all(np.isfinite(np.asarray(mc["samples_o"])[:, k]))]
        if data.shape[1] >= 2:
            corr = np.corrcoef(data, rowvar=False)
            corr = np.nan_to_num(corr, nan=0.0)
            im = ax_corr.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
            ax_corr.set_xticks(range(len(labels)))
            ax_corr.set_yticks(range(len(labels)))
            ax_corr.set_xticklabels(labels, rotation=60, ha="right", fontsize=7)
            ax_corr.set_yticklabels(labels, fontsize=7)
            ax_corr.set_title("Feature-flux correlation (MC samples)")
            fig.colorbar(im, ax=ax_corr, fraction=0.046, pad=0.04)
        else:
            ax_corr.text(0.5, 0.5, "insufficient finite samples",
                         ha="center", va="center", transform=ax_corr.transAxes)
            ax_corr.set_axis_off()
    else:
        ax_corr.text(0.5, 0.5, "insufficient features", ha="center",
                     va="center", transform=ax_corr.transAxes)
        ax_corr.set_axis_off()

    if method == "bootstrap" and top:
        for _, k, sp, flux, err in top[:6]:
            r = records[sp["record"]]
            vals = np.asarray(mc["samples_o"])[:, k]
            if np.isfinite(flux) and flux != 0:
                vals = vals / flux - 1.0
                ax_trace.plot(vals, lw=1.0, label=r["name"])
            else:
                ax_trace.plot(vals, lw=1.0, label=r["name"])
        ax_trace.axhline(0.0, color="k", lw=0.8, ls="--")
        ax_trace.set_xlabel("realization")
        ax_trace.set_ylabel("relative deviation from best fit")
        ax_trace.set_title("Bootstrap trace (top features)")
        ax_trace.legend(fontsize=6, ncol=2)
        ax_trace.grid(alpha=0.25)
    else:
        ax_trace.text(0.5, 0.55, "Linearized covariance mode",
                      ha="center", va="center", transform=ax_trace.transAxes,
                      fontsize=10)
        ax_trace.text(0.5, 0.42, f"rank {mc['cov']['rank']}/{mc['n_free']}  "
                      f"rcond {mc['cov']['rcond']:g}",
                      ha="center", va="center", transform=ax_trace.transAxes,
                      fontsize=8)
        ax_trace.text(0.5, 0.30, f"N = {n_samples}  seed = {seed}",
                      ha="center", va="center", transform=ax_trace.transAxes,
                      fontsize=8)
        ax_trace.set_axis_off()

    method_label = ("covariance-linearized" if method == "covariance"
                    else f"full-refit bootstrap ({mc.get('bootstrap_mode', '')})")
    fig.suptitle(
        f"PAHFIT Monte Carlo uncertainties: {method_label}\n"
        f"N={n_samples}, runtime={runtime:.1f} s, seed={seed}"
        + (f", {title_extra}" if title_extra else ""),
        fontsize=12,
    )
    fig.text(0.01, 0.005,
             "Flux units follow the input spectrum (MJy/sr); integrated "
             "intensities are MJy/sr um. observed = S07-attenuated model; "
             "intrinsic = attenuation removed.",
             fontsize=7, color="0.35")
    fig.tight_layout(rect=(0, 0.02, 1, 0.94))
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser(cfg: dict):
    inp = cfg.get("input", {}) if isinstance(cfg, dict) else {}
    fit = cfg.get("fit", {}) if isinstance(cfg, dict) else {}
    mc = cfg.get("monte_carlo", {}) if isinstance(cfg, dict) else {}
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default=None,
                   help="JSON config file, or a name under configs/pahfit_mir/")
    p.add_argument("--input", type=Path, default=Path("/app/input"))
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--z", type=float, required=True)
    p.add_argument("--maxiter", type=int, default=int(fit.get("maxiter", 1000)))
    p.add_argument("--fit-passes", type=int, default=int(fit.get("passes", 1)),
                   help="number of sequential PAHFIT fits (warm-start after the first)")
    p.add_argument("--segment", choices=["both", "short", "long"],
                   default=inp.get("segment", "both"))
    p.add_argument("--no-guess", action="store_true",
                   default=bool(fit.get("no_guess", False)))
    p.add_argument("--spectrum", default=None, help="PAHFIT-packaged spectrum name/path")
    p.add_argument("--instrument", default=_instrument_default(cfg),
                   help="PAHFIT instrument name; otherwise infer/leave unset")
    p.add_argument("--s1d", action="store_true",
                   default=bool(inp.get("s1d", False)),
                   help="input dir contains *_s1d.fits")
    p.add_argument("--tbl", action="store_true",
                   default=bool(inp.get("tbl", False)),
                   help="input is a Spitzer IRS .tbl table")
    p.add_argument("--init-from", default=fit.get("init_from"),
                   help="warm-start from a previous PAHFIT ECSV model")
    p.add_argument("--smooth-um", type=float, default=inp.get("smooth_um"),
                   help="median-bin width in micron before fitting (MIRI high-res)")
    p.add_argument("--aperture-arcsec2", type=float,
                   default=float(inp.get("aperture_arcsec2", 0.04)),
                   help="effective aperture for Jy -> MJy/sr (MIRI x1d)")
    p.add_argument("--min-wave", type=float, default=float(inp.get("min_wave", 5.0)))
    p.add_argument("--max-wave", type=float, default=float(inp.get("max_wave", 38.0)))
    p.add_argument("--normalize-fit", action=argparse.BooleanOptionalAction,
                   default=fit.get("normalize", None),
                   help="divide the input by its median before fitting; "
                        "auto-enabled for MC runs to keep PAHFIT's least "
                        "squares well scaled")

    p.add_argument("--mc", action="store_true",
                   help="enable Monte Carlo using the config sample count")
    p.add_argument("--mc-samples", type=int, default=None,
                   help="number of MC realizations (0 disables; default 0)")
    p.add_argument("--mc-method", choices=["auto", "covariance", "bootstrap"],
                   default=mc.get("method", "auto"))
    p.add_argument("--mc-seed", type=int, default=int(mc.get("seed", 12345)))
    p.add_argument("--mc-maxiter", type=int, default=int(mc.get("maxiter", 500)),
                   help="maxiter for each bootstrap refit")
    p.add_argument("--mc-rcond", type=float, default=float(mc.get("rcond", 1e-10)),
                   help="relative singular-value cutoff for covariance truncation")
    p.add_argument("--mc-bootstrap-mode", choices=["parametric", "residual"],
                   default=mc.get("bootstrap_mode", "parametric"))
    p.add_argument("--mc-scale", choices=["none", "chi2"],
                   default=mc.get("scale", "none"),
                   help="optionally rescale covariance errors by sqrt(chi2_red)")
    p.add_argument("--mc-save-samples", action=argparse.BooleanOptionalAction,
                   default=bool(mc.get("save_samples", True)))
    return p


def main(argv=None):
    t_start = time.time()
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config", default=None)
    known, _ = pre.parse_known_args(argv)
    cfg_path, cfg = resolve_config(known.config)
    p = build_parser(cfg)
    args = p.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)

    mc_cfg = cfg.get("monte_carlo", {}) if isinstance(cfg, dict) else {}
    if args.mc_samples is None:
        if args.mc or bool(mc_cfg.get("enabled", False)):
            args.mc_samples = int(mc_cfg.get("samples", 100))
        else:
            args.mc_samples = 0
    args.mc_samples = max(0, int(args.mc_samples))
    if getattr(args, "normalize_fit", None) is None:
        # PAHFIT's Levenberg-Marquardt fit can stall when the native
        # intensity scale is very large (e.g. Jy converted to MJy/sr).
        # Normalizing is a numerical device only; all saved fluxes are
        # multiplied back to the native unit below.
        args.normalize_fit = bool(args.mc_samples > 0)
    if args.mc_samples > 0 and args.fit_passes < 2:
        args.fit_passes = 2
        print("[pahfit] MC enabled: using 2 sequential fit passes for a converged "
              "reference model", flush=True)
    if not (0 < args.mc_rcond < 1):
        raise SystemExit("--mc-rcond must be between 0 and 1")

    flux_unit = "MJy/sr"
    if args.spectrum:
        from pahfit.helpers import read_spectrum
        spec = read_spectrum(args.spectrum)
        if args.instrument:
            parts = [x.strip() for x in args.instrument.split(",") if x.strip()]
            spec.meta["instrument"] = parts[0] if len(parts) == 1 else parts
        w = spec.spectral_axis.to_value(u.micron)
        flux_unit = str(spec.flux.unit)
        print(f"[pahfit] packaged spectrum {args.spectrum}: {len(w)} pixels, "
              f"{w.min():.2f}-{w.max():.2f} um, unit={flux_unit}")
    else:
        waves, fluxes, errs = [], [], []
        unit = None
        if args.tbl:
            files = sorted(args.input.glob("*.tbl"))
            if not files:
                files = [args.input]
        elif args.s1d:
            files = sorted(args.input.glob("*_s1d.fits"))
        else:
            pat = {"both": "*_x1d.fits", "short": "*mirifushort_x1d.fits",
                   "long": "*mirifulong_x1d.fits"}[args.segment]
            files = sorted(args.input.glob(pat))
        if not files:
            raise SystemExit(f"no input spectra found under {args.input}")
        for f in files:
            if f.suffix == ".tbl":
                w, fl, er, dq, uu, order = read_irs_tbl(f)
                # Spitzer IRS tables are point-source calibrated Jy.  PAHFIT
                # requires intensity, so divide by the slit solid angle.
                arcsec2_sr = (np.pi / 180.0 / 3600.0) ** 2
                # The IRS table is point-source calibrated, not per-slit
                # surface brightness.  Applying different SL/LL slit areas
                # inserts an 8.6x step at 14.2 um.  Use one common aperture
                # solid angle so the SED is continuous; PAHFIT then fits the
                # shape and relative features.
                omega = 1.0 * arcsec2_sr
                fl = fl * 1e6 / omega
                er = er * 1e6 / omega
                uu = "MJy/sr"
            elif args.s1d:
                w, fl, er, dq, uu = read_s1d(f)
            else:
                w, fl, er, dq, uu = read_x1d(f)
            if uu == "Jy":
                omega = args.aperture_arcsec2 * (np.pi / 180.0 / 3600.0) ** 2
                fl = fl * 1e6 / omega
                er = er * 1e6 / omega
                uu = "MJy/sr"
            good = (np.isfinite(w) & np.isfinite(fl) & np.isfinite(er) & (er > 0)
                    & (dq == 0) & (w >= args.min_wave) & (w <= args.max_wave))
            waves.append(w[good]); fluxes.append(fl[good]); errs.append(er[good])
            unit = unit or uu
            print(f"[pahfit] {f.name}: {good.sum()} good pixels, "
                  f"{w[good].min():.2f}-{w[good].max():.2f} um, unit={uu}, "
                  f"median flux={np.nanmedian(fl[good]):.6g}, "
                  f"median err={np.nanmedian(er[good]):.6g}")
        w = np.concatenate(waves); fl = np.concatenate(fluxes); er = np.concatenate(errs)
        order = np.argsort(w); w, fl, er = w[order], fl[order], er[order]
        # Remove exact/near duplicates from overlapping IRS orders or MRS segments.
        keep = np.ones(len(w), dtype=bool)
        for i in range(1, len(w)):
            if abs(w[i] - w[i - 1]) < 1e-5:
                keep[i] = False
        w, fl, er = w[keep], fl[keep], er[keep]
        w, fl, er = bin_spectrum(w, fl, er, args.smooth_um)
        flux_unit = unit or "MJy/sr"
        spec = Spectrum1D(spectral_axis=w * u.micron,
                          flux=fl * u.Unit(flux_unit),
                          uncertainty=StdDevUncertainty(er * u.Unit(flux_unit)))
        if args.instrument:
            parts = [x.strip() for x in args.instrument.split(",") if x.strip()]
            spec.meta["instrument"] = parts[0] if len(parts) == 1 else parts
        elif args.s1d or any("miri" in f.name.lower() for f in files):
            spec.meta["instrument"] = MIRI_ALL
        if "instrument" not in spec.meta:
            raise SystemExit("PAHFIT needs --instrument for non-MIRI input")
        print(f"[pahfit] combined {len(w)} pixels, {w.min():.2f}-{w.max():.2f} um, "
              f"z={args.z}, bin={args.smooth_um}, unit={flux_unit}, "
              f"median flux={np.nanmedian(fl):.6g}, "
              f"median err={np.nanmedian(er):.6g}")

    fit_scale = 1.0
    fit_spec = spec
    if args.normalize_fit:
        med = float(np.nanmedian(np.abs(spec.flux.value)))
        if np.isfinite(med) and med > 0:
            fit_scale = med
            fit_spec = Spectrum1D(
                spectral_axis=spec.spectral_axis,
                flux=spec.flux / fit_scale,
                uncertainty=StdDevUncertainty(
                    np.asarray(spec.uncertainty.array, float) / fit_scale
                    * spec.flux.unit
                ),
            )
            fit_spec.meta.update(spec.meta)
            print(f"[pahfit] internal fit normalization: flux/{fit_scale:.6g}; "
                  f"saved fluxes are multiplied back to the native unit",
                  flush=True)

    pack = Path(pahfit.__file__).parent / "packs" / "science" / "classic.yaml"
    init_from = args.init_from
    if init_from:
        p_init = Path(init_from).expanduser()
        if not p_init.is_absolute():
            p_init = args.output / p_init
        if p_init.exists():
            init_from = str(p_init)
        else:
            print(f"[pahfit] warm-start file not found: {p_init}; "
                  f"starting from the science pack", flush=True)
            init_from = None
    if init_from:
        model = Model.from_saved(init_from)
        if args.normalize_fit and fit_scale != 1.0:
            _scale_features_inplace(model, 1.0 / fit_scale)
        # ECSV metadata has the instrument fields swapped; the observed
        # spectrum metadata remains authoritative for the fit.
        model.features.meta["instrument"] = fit_spec.meta.get("instrument", "")
        print(f"[pahfit] warm-starting from {init_from}")
    else:
        model = Model.from_yaml(str(pack))
    status = "ok"
    try:
        if not args.no_guess and not init_from:
            model.guess(fit_spec, redshift=args.z)
    except Exception as exc:  # noqa: BLE001
        status = f"guess_failed:{type(exc).__name__}"
        print(f"[pahfit] guess failed: {exc}")

    pass_chi2 = []
    passes_done = 0
    for ipass in range(max(1, int(args.fit_passes))):
        t_pass = time.time()
        try:
            model.fit(fit_spec, redshift=args.z, maxiter=args.maxiter, verbose=False)
            passes_done += 1
            try:
                lam_rest = fit_spec.spectral_axis.to_value(u.micron) / (1.0 + args.z)
                pred = np.asarray(model.fitter.model(lam_rest), float)
                y_rest = np.asarray(fit_spec.flux.value, float) * (1.0 + args.z)
                sig_rest = np.asarray(fit_spec.uncertainty.array, float) * (1.0 + args.z)
                good = np.isfinite(pred) & np.isfinite(y_rest) & np.isfinite(sig_rest) & (sig_rest > 0)
                chi2 = float(np.sum(((y_rest[good] - pred[good]) / sig_rest[good]) ** 2))
                pass_chi2.append(chi2)
            except Exception:
                pass_chi2.append(float("nan"))
            print(f"[pahfit] fit pass {ipass + 1}/{args.fit_passes}: "
                  f"chi2={pass_chi2[-1]:.6g}  ({time.time() - t_pass:.2f} s)", flush=True)
        except Exception as exc:  # noqa: BLE001
            status = f"fit_failed:{type(exc).__name__}"
            print(f"[pahfit] fit pass {ipass + 1} failed: {exc}", flush=True)
            break
    out_model = _scaled_model_copy(model, fit_scale)
    out_model.save(str(args.output / "pahfit_output.ecsv"), overwrite=True)
    out_model.features.write(str(args.output / "pahfit_features.csv"),
                             format="ascii.csv", overwrite=True)

    plot_status = "ok"
    try:
        plot_model = _scaled_model_copy(model, fit_scale)
        try:
            plot_model._set_up_fitter(spec.meta.get("instrument"),
                                      args.z, use_instrument_fwhm=False)
        except Exception:
            pass
        fig = default_layout_plot(spec, plot_model, 2.0)
        fig.savefig(args.output / "pahfit_fit.png", dpi=140, bbox_inches="tight")
        fig.savefig(args.output / "pahfit_fit.pdf", bbox_inches="tight")
    except Exception as exc:  # noqa: BLE001
        plot_status = f"fallback:{type(exc).__name__}"
        print(f"[pahfit] default plot failed ({exc}); using fallback plot")
        fig, ax = plt.subplots(figsize=(11, 5))
        ax.plot(np.asarray(w), np.asarray(spec.flux.value), color="0.3", lw=0.8)
        ax.set_xlabel("observed wavelength (um)")
        ax.set_ylabel(f"flux ({flux_unit})")
        ax.set_title("PAHFIT fit (fallback plot; fit itself succeeded)")
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(args.output / "pahfit_fit.png", dpi=140, bbox_inches="tight")
        fig.savefig(args.output / "pahfit_fit.pdf", bbox_inches="tight")

    # Unified feature/line table (always produced; no extra fit cost).
    records = compute_feature_records(model, fit_spec, args.z,
                                      flux_scale=fit_scale)
    specs = _quantity_specs(model, records, args.z)

    rms_rel = float("nan")
    chi2_best = float("nan")
    n_data = 0
    n_free_all = 0
    n_free = 0
    try:
        lam = fit_spec.spectral_axis.to_value(u.micron) / (1.0 + args.z)
        # PAHFIT converts the observed spectrum to the rest frame by (1+z);
        # the model is evaluated on that rest-frame grid.  Compare like with
        # like (the previous code compared observed flux to rest-frame model).
        pred = np.asarray(model.fitter.model(lam), float) / (1.0 + args.z)
        y = np.asarray(fit_spec.flux.value, float)
        if pred.shape == y.shape:
            rms_rel = float(np.sqrt(np.nanmean((y - pred) ** 2))
                            / max(np.nanmedian(np.abs(y)), 1e-30))
        y_rest = np.asarray(fit_spec.flux.value, float) * (1.0 + args.z)
        sig_rest = np.asarray(fit_spec.uncertainty.array, float) * (1.0 + args.z)
        pred_rest = np.asarray(model.fitter.model(lam), float)
        good = np.isfinite(pred_rest) & np.isfinite(y_rest) & np.isfinite(sig_rest) & (sig_rest > 0)
        n_data = int(good.sum())
        chi2_best = float(np.sum(((y_rest[good] - pred_rest[good]) / sig_rest[good]) ** 2))
        try:
            mfit = model.fitter.model
            n_free_all = int(sum(1 for v in dict(mfit.fixed).values() if not v))
            n_free = n_free_all
        except Exception:
            pass
        # Number of free parameters after dropping bound parameters, used for
        # the covariance and the reduced chi-square below.
        try:
            free_tmp, at_tmp, _ = _free_parameters(model)
            n_free = len(free_tmp)
            n_at_bound = len(at_tmp)
        except Exception:
            n_at_bound = 0
    except Exception:
        n_at_bound = 0
    dof = max(1, n_data - max(n_free, 0))
    chi2_red = chi2_best / dof if np.isfinite(chi2_best) else float("nan")

    # Monte Carlo uncertainty estimation (opt-in).
    mc_summary = {
        "enabled": bool(args.mc_samples > 0),
        "requested_method": args.mc_method,
        "method": None,
        "n_samples": int(args.mc_samples),
        "seed": int(args.mc_seed),
        "runtime_s": 0.0,
        "fit_passes": int(passes_done),
    }
    mc = None
    method = None
    mc_runtime = 0.0
    if args.mc_samples > 0 and passes_done > 0:
        t_mc = time.time()
        rng = np.random.default_rng(args.mc_seed)
        cov = None
        fallback = None
        if args.mc_method in ("auto", "covariance"):
            try:
                cov = run_covariance_mc(
                    model, fit_spec, args.z, records, specs, args.mc_samples,
                    args.mc_rcond, rng, chi2_red=chi2_red,
                    flux_scale=fit_scale,
                )
            except Exception as exc:  # noqa: BLE001
                cov = None
                fallback = f"covariance_failed:{type(exc).__name__}"
                print(f"[pahfit] covariance MC failed: {exc}", flush=True)
                traceback.print_exc()
            if cov is not None and args.mc_method == "auto":
                min_rank = max(2, int(0.8 * max(1, cov["n_free"])))
                if (cov["cov"]["rank"] < min_rank
                        or cov["cov"]["condition"] > 1e6):
                    fallback = (f"covariance_ill_conditioned_rank_"
                                f"{cov['cov']['rank']}_of_{cov['n_free']}_"
                                f"cond_{cov['cov']['condition']:.3g}")
                    cov = None
        if cov is not None:
            mc = cov
            method = "covariance"
        elif args.mc_samples > 0:
            method = "bootstrap"
            if fallback is None:
                fallback = ("covariance_unavailable" if args.mc_method != "bootstrap"
                            else None)
            print(f"[pahfit] using full-refit bootstrap "
                  f"({args.mc_samples} realizations, mode={args.mc_bootstrap_mode})",
                  flush=True)
            mc = run_bootstrap_mc(
                model, fit_spec, args.z, specs, args.mc_samples, args.mc_seed,
                args.mc_maxiter, args.mc_bootstrap_mode,
                flux_scale=fit_scale,
            )
        mc_runtime = time.time() - t_mc
        mc_summary.update({
            "method": method,
            "runtime_s": float(mc_runtime),
            "fallback_reason": fallback,
            "n_samples_ok": int(mc.get("n_ok", args.mc_samples)) if method == "bootstrap" else int(args.mc_samples),
        })
        if method == "covariance":
            mc_summary["covariance"] = {
                "rank": int(mc["cov"]["rank"]),
                "n_free": int(mc["n_free"]),
                "n_free_all": int(mc["n_free_all"]),
                "n_at_bound": int(mc["n_at_bound"]),
                "n_data": int(mc["n_data"]),
                "rcond": float(mc["cov"]["rcond"]),
                "condition_number": float(mc["cov"]["condition"]),
                "n_clipped_draws": int(mc["n_clipped"]),
                "n_nonphysical_draws": int(mc["n_nonphysical"]),
                "rank_deficient": bool(mc["cov"]["rank"] < mc["n_free"]),
                "covariance_scale": "absolute (no chi2/dof rescaling)",
                "chi2_red": float(chi2_red) if np.isfinite(chi2_red) else None,
                "scale": args.mc_scale,
            }
            # Attach errors to records for the line table.
            by_record = {sp["record"]: k for k, sp in enumerate(specs)}
            for idx, rec in enumerate(records):
                k = by_record.get(idx)
                if k is None:
                    continue
                _e = float(mc["err_o"][k]) if k < len(mc["err_o"]) else float("nan")
                _f = float(rec["flux_observed"])
                if (mc["cov"]["rank"] < mc["n_free"] and np.isfinite(_f)
                        and _f != 0 and np.isfinite(_e)
                        and _e <= 1e-6 * abs(_f)):
                    rec["snr"] = float("nan")
                else:
                    rec["snr"] = _f / _e if _e and np.isfinite(_e) else float("nan")
        else:
            mc_summary["bootstrap"] = {
                "mode": str(mc.get("bootstrap_mode", args.mc_bootstrap_mode)),
                "n_ok": int(mc.get("n_ok", 0)),
                "n_failed": int(mc.get("n_failed", 0)),
                "median_nfev": float(np.nanmedian(mc.get("nfev", [np.nan]))),
                "median_runtime_s": float(np.nanmedian(mc.get("runtime", [np.nan]))),
            }
            by_record = {sp["record"]: k for k, sp in enumerate(specs)}
            for idx, rec in enumerate(records):
                k = by_record.get(idx)
                if k is None:
                    continue
                rec["snr"] = (float(rec["flux_observed"]) / float(mc["err_o"][k])
                              if mc["err_o"][k] and np.isfinite(mc["err_o"][k]) else float("nan"))
        write_uncertainties_csv(
            args.output / "pahfit_uncertainties.csv", records, specs, mc,
            method, args.mc_samples,
            scale_chi2=chi2_red if args.mc_scale == "chi2" else None,
        )
        if args.mc_save_samples:
            write_samples_csv(args.output / "pahfit_mc_samples.csv", records,
                              specs, mc, method)
        try:
            plot_uncertainties(
                args.output / "pahfit_uncertainty.png", records, specs, mc,
                method, args.mc_samples, mc_runtime, args.mc_seed,
                title_extra=f"chi2_red={chi2_red:.2f}" if np.isfinite(chi2_red) else "",
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[pahfit] uncertainty plot failed: {exc}", flush=True)
            mc_summary["plot_error"] = f"{type(exc).__name__}: {exc}"
    elif args.mc_samples > 0:
        mc_summary["status"] = "skipped_fit_failed"

    # The always-on line table gets S/N values when MC is available.
    write_lines_csv(args.output / "pahfit_lines.csv", records)

    unstable = bool((np.isfinite(rms_rel) and rms_rel > 0.5) or status != "ok")
    summary = {
        "z": args.z, "instrument": str(spec.meta.get("instrument", "")),
        "n_pixels": int(len(w)), "flux_unit": flux_unit, "segment": args.segment,
        "smooth_um": args.smooth_um, "status": status, "plot_status": plot_status,
        "wave_min_um": float(np.min(w)), "wave_max_um": float(np.max(w)),
        "n_features": int(len(model.features)), "rms_rel": rms_rel,
        "unstable": unstable,
        "normalize_fit": bool(args.normalize_fit),
        "fit_flux_scale": float(fit_scale),
        "fit_passes_requested": int(args.fit_passes),
        "fit_passes_completed": int(passes_done),
        "fit_pass_chi2": [float(x) for x in pass_chi2],
        "chi2": float(chi2_best) if np.isfinite(chi2_best) else None,
        "dof": int(dof),
        "chi2_red": float(chi2_red) if np.isfinite(chi2_red) else None,
        "n_free_parameters": int(n_free),
        "n_free_parameters_all": int(n_free_all),
        "n_at_bound_parameters": int(n_at_bound),
        "mc": mc_summary,
        "config_file": str(cfg_path) if cfg_path else None,
        "config_name": str(cfg.get("name", "cli")) if isinstance(cfg, dict) else "cli",
        "runtime_s": float(time.time() - t_start),
    }
    try:
        fi = model.fitter.fit_info
        summary["fit_info"] = {
            "nfev": int(fi.get("nfev", 0)),
            "ierr": int(fi.get("ierr", 0)),
            "message": str(fi.get("message", "")),
            "status": str(fi.get("status", "")),
        }
    except Exception:
        pass
    (args.output / "pahfit_summary.json").write_text(
        json.dumps(summary, indent=2, default=float)
    )

    # Effective configuration, for provenance and reproducibility.
    effective = {
        "config_file": str(cfg_path) if cfg_path else None,
        "config_name": str(cfg.get("name", "cli")) if isinstance(cfg, dict) else "cli",
        "input": {
            "mode": ("spectrum" if args.spectrum else
                     "tbl" if args.tbl else "s1d" if args.s1d else "x1d"),
            "instrument": args.instrument,
            "segment": args.segment,
            "s1d": bool(args.s1d),
            "tbl": bool(args.tbl),
            "aperture_arcsec2": float(args.aperture_arcsec2),
            "min_wave_um": float(args.min_wave),
            "max_wave_um": float(args.max_wave),
        },
        "preprocess": {"smooth_um": args.smooth_um},
        "fit": {
            "maxiter": int(args.maxiter),
            "passes": int(args.fit_passes),
            "no_guess": bool(args.no_guess),
            "init_from": args.init_from,
            "normalize": bool(args.normalize_fit),
            "flux_scale": float(fit_scale),
        },
        "monte_carlo": {
            "enabled": bool(args.mc_samples > 0),
            "samples": int(args.mc_samples),
            "method": args.mc_method,
            "seed": int(args.mc_seed),
            "rcond": float(args.mc_rcond),
            "maxiter": int(args.mc_maxiter),
            "bootstrap_mode": args.mc_bootstrap_mode,
            "scale": args.mc_scale,
            "save_samples": bool(args.mc_save_samples),
        },
        "metadata": {
            "z": float(args.z),
            "wave_min_um": float(np.min(w)),
            "wave_max_um": float(np.max(w)),
            "n_pixels": int(len(w)),
            "flux_unit": flux_unit,
        },
    }
    (args.output / "effective_config.json").write_text(
        json.dumps(effective, indent=2, default=float)
    )

    print(f"[pahfit] done status={status} rms_rel={rms_rel:.3f} unstable={unstable} "
          f"-> {args.output}")
    if args.mc_samples > 0:
        print(f"[pahfit] MC method={method} N={args.mc_samples} "
              f"runtime={mc_runtime:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
