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


ARCSEC2_SR = (np.pi / 180.0 / 3600.0) ** 2


def _fits_col_unit(hdu, col: str, default: str | None = None) -> str | None:
    """Return the FITS table column unit, falling back to BUNIT."""
    unit = None
    try:
        unit = hdu.columns[col].unit
    except Exception:
        unit = None
    if not unit:
        unit = hdu.header.get("BUNIT")
    if not unit:
        unit = default
    return str(unit).strip() if unit else default


def _first_col(names: dict, candidates: tuple[str, ...]) -> str | None:
    for cand in candidates:
        if cand in names:
            return names[cand]
    return None


def read_s1d(path: Path):
    """Read a PAHFIT/MIRI ``s1d`` table and preserve its real unit.

    The official PAHFIT VV114 example stores flux in ``MJy`` (a flux
    density), not ``MJy/sr``.  Older versions of this driver hard-coded
    ``MJy/sr`` and therefore silently mislabelled the absolute scale.
    """
    with fits.open(path, memmap=False) as h:
        d = h[1].data
        names = {c.lower(): c for c in d.columns.names}
        wc = _first_col(names, ("wavelength", "wave", "lambda"))
        fc = _first_col(names, ("flux", "flux_density", "surf_bright"))
        ec = _first_col(names, ("uncertainty", "error", "flux_error", "stdev"))
        dc = _first_col(names, ("dq", "bit-flag", "bit_flag", "flag"))
        if wc is None or fc is None or ec is None:
            raise SystemExit(f"cannot identify wavelength/flux/error columns in {path}")
        w = np.asarray(d[wc], float)
        fl = np.asarray(d[fc], float)
        er = np.asarray(d[ec], float)
        dq = np.asarray(d[dc], float) if dc is not None else np.zeros(len(w))
        unit = _fits_col_unit(h[1], fc, "MJy/sr")
    return w, fl, er, dq, unit


def read_x1d(path: Path):
    with fits.open(path, memmap=False) as h:
        d = h["EXTRACT1D"].data
        names = {c.lower(): c for c in d.columns.names}
        w = np.asarray(d[names["wavelength"]], float)
        if "flux" in names:
            fl = np.asarray(d[names["flux"]], float)
            ec = _first_col(names, ("flux_error", "error"))
            er = np.asarray(d[ec], float)
            unit = _fits_col_unit(h["EXTRACT1D"], names["flux"], "Jy")
        else:
            fl = np.asarray(d[names["surf_bright"]], float)
            ec = _first_col(names, ("sb_error", "error"))
            er = np.asarray(d[ec], float)
            unit = _fits_col_unit(h["EXTRACT1D"], names["surf_bright"], "MJy/sr")
        dc = _first_col(names, ("dq", "bit-flag", "flag"))
        dq = np.asarray(d[dc], float) if dc is not None else np.zeros(len(w))
        return w, fl, er, dq, unit


def read_irs_tbl(path: Path):
    try:
        t = Table.read(path, format="ascii.ipac")
    except Exception:
        t = Table.read(path, format="ascii")
    names = {c.lower(): c for c in t.colnames}
    wc = _first_col(names, ("wavelength", "wave", "lambda"))
    fc = _first_col(names, ("flux_density", "flux", "surf_bright"))
    ec = _first_col(names, ("error", "flux_density_err", "stdev", "uncertainty"))
    if wc is None or fc is None or ec is None:
        raise SystemExit(f"cannot identify wavelength/flux/error columns in {path}")
    w = np.asarray(t[wc], float)
    fl = np.asarray(t[fc], float)
    er = np.asarray(t[ec], float)
    dc = _first_col(names, ("bit-flag", "bit_flag", "flag"))
    good = np.ones(len(w), dtype=bool)
    if dc is not None:
        good = np.asarray(t[dc]) == 0
    oc = _first_col(names, ("order",))
    order = np.asarray(t[oc], int) if oc is not None else np.zeros(len(w), int)
    try:
        unit = str(t[fc].unit) if t[fc].unit is not None else "Jy"
    except Exception:
        unit = "Jy"
    return w, fl, er, (~good).astype(float), unit, order


def _to_mjy_sr(fl, er, unit: str | None, aperture_arcsec2: float,
               label: str = "") -> tuple[np.ndarray, np.ndarray, str, float]:
    """Convert a supported input flux unit to MJy/sr.

    ``Jy`` and ``MJy`` are flux densities.  They are divided by the
    requested aperture solid angle.  ``MJy/sr`` is already an intensity.
    The historical code used ``1 Jy = 1e6 MJy`` (a factor 1e12 error), so
    this helper deliberately goes through astropy units.
    """
    if not np.isfinite(aperture_arcsec2) or aperture_arcsec2 <= 0:
        raise SystemExit(f"aperture must be positive, got {aperture_arcsec2}")
    text = str(unit or "MJy/sr").strip()
    try:
        uu = u.Unit(text)
    except Exception as exc:
        raise SystemExit(f"cannot parse flux unit {text!r} for {label}: {exc}") from exc
    if uu.is_equivalent(u.MJy / u.sr):
        scale = float((1.0 * uu).to(u.MJy / u.sr).value)
        return (np.asarray(fl, float) * scale, np.asarray(er, float) * scale,
                "MJy/sr", scale)
    if uu.is_equivalent(u.Jy):
        omega = float(aperture_arcsec2) * ARCSEC2_SR
        # 1 Jy = 1e-6 MJy; astropy handles mJy/uJy as well.
        scale = float((1.0 * uu).to(u.MJy).value) / omega
        return (np.asarray(fl, float) * scale, np.asarray(er, float) * scale,
                "MJy/sr", scale)
    raise SystemExit(
        f"unsupported flux unit {text!r} for {label}; "
        "expected MJy/sr, Jy or MJy"
    )


def _coverage_info(w) -> dict:
    """Describe wavelength coverage gaps in a sorted spectrum."""
    w = np.asarray(w, float)
    if len(w) < 2:
        return {"gaps": [], "max_gap_um": 0.0, "gap_total_um": 0.0}
    sw = np.sort(w)
    dw = np.diff(sw)
    pos = dw[dw > 0]
    med = float(np.median(pos)) if len(pos) else 0.0
    thresh = max(5.0 * med, 0.25)
    gaps = []
    for a, b, d in zip(sw[:-1], sw[1:], dw):
        if d > thresh:
            gaps.append({"start_um": float(a), "end_um": float(b),
                         "width_um": float(d)})
    return {"gaps": gaps,
            "max_gap_um": float(max((g["width_um"] for g in gaps), default=0.0)),
            "gap_total_um": float(sum(g["width_um"] for g in gaps))}


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


def _component_value(model, name: str, attr: str, default=float("nan")) -> float:
    """Read a fitted astropy submodel attribute (authoritative, unscaled)."""
    comp = _submodel(model, name)
    if comp is None:
        return float(default)
    try:
        value = getattr(comp, attr)
        try:
            return float(value.value)
        except Exception:
            return float(value)
    except Exception:
        return float(default)


def _feature_power(model, name: str, kind: str) -> float:
    """Integrated feature power in PAHFIT's internal intensity-power unit."""
    if kind in ("line", "dust_feature"):
        return _component_value(model, name, "power")
    if kind in ("dust_continuum", "starlight"):
        return _component_value(model, name, "amplitude")
    if kind == "attenuation":
        return _component_value(model, name, "tau_sil")
    if kind == "absorption":
        return _component_value(model, name, "tau")
    return float("nan")


def _feature_flux(model, name: str, kind: str, wl: float, fwhm: float,
                  z: float, compute_ew: bool = True):
    """Physical flux of one fitted feature.

    PAHFIT's fittable components return F_nu in MJy/sr.  The line table
    reports PAHFIT's integrated line power (the frequency integral, MJy/sr
    THz).  This is the quantity that preserves physical line ratios; the old
    ``∫F_nu dλ`` convention biased every ratio by ``(λ2/λ1)^2``.
    """
    out = {
        "flux_observed": float("nan"), "flux_intrinsic": float("nan"),
        "flux_peak_observed": float("nan"), "flux_peak_intrinsic": float("nan"),
        "ew_um": float("nan"), "attenuation_at_feature": float("nan"),
    }
    if kind in ("line", "dust_feature"):
        # PAHFIT's ``power`` is the integrated line power over frequency.
        # The old table copied ∫F_nu dλ instead; that is not a physical line
        # flux and every line ratio was biased by (λ2/λ1)^2.  Use the
        # PAHFIT power (intrinsic) multiplied by the attenuation at the line
        # for the observed value.  Ratios are now independent of λ².
        fwhm = fwhm if np.isfinite(fwhm) and fwhm > 0 else 0.1 * max(wl, 1e-3)
        half = max(8.0 * abs(fwhm), 1e-4 * max(abs(wl), 1e-3))
        grid = np.linspace(max(wl - half, 1e-4), wl + half, 401)
        comp = _component(model, name, grid)
        att = _attenuation(model, grid)
        power = _feature_power(model, name, kind)
        out["flux_intrinsic"] = float(power)
        out["flux_observed"] = float(power) * float(_attenuation(model, np.array([wl]))[0])
        if np.isfinite(comp).any():
            out["flux_peak_intrinsic"] = float(np.nanmax(comp))
            out["flux_peak_observed"] = float(np.nanmax(comp * att)) / (1.0 + z)
            if compute_ew:
                cont = np.zeros_like(grid)
                for cname in [str(r["name"]) for r in model.features
                              if str(r["kind"]) in ("dust_continuum", "starlight")]:
                    cont = cont + _component(model, cname, grid)
                cont_obs = cont * att
                good = np.isfinite(comp) & np.isfinite(cont_obs) & (cont_obs > 0)
                if good.sum() > 2:
                    out["ew_um"] = _trapz((comp * att)[good] / cont_obs[good], grid[good])
        out["attenuation_at_feature"] = float(_attenuation(model, np.array([wl]))[0])
    elif kind in ("dust_continuum", "starlight"):
        lam = np.array([wl], float)
        comp = _component(model, name, lam)
        att = _attenuation(model, lam)
        out["flux_intrinsic"] = float(comp[0])
        out["flux_observed"] = float(comp[0] * att[0]) / (1.0 + z)
        out["flux_peak_intrinsic"] = out["flux_intrinsic"]
        out["flux_peak_observed"] = out["flux_observed"]
        out["attenuation_at_feature"] = float(att[0])
    return out


def compute_feature_records(model, spec, z, flux_scale=1.0):
    """Build the unified gas-line / PAH / continuum table from the fit."""
    ft = model.features
    enabled = set(str(x) for x in getattr(model, "enabled_features", []))
    coverage = spec.meta.get("coverage", {}) or {}
    lam_obs = spec.spectral_axis.to_value(u.micron)
    rest_min = float(np.nanmin(lam_obs) / (1.0 + z))
    rest_max = float(np.nanmax(lam_obs) / (1.0 + z))
    try:
        free, at_bound, pmap = _free_parameters(model)
        at_bound_features = {pmap.get(n, (None, None, 0))[0] for n, _ in at_bound}
    except Exception:
        free, at_bound, pmap = [], [], {}
        at_bound_features = set()
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
            "reference_wavelength_um": ref if np.isfinite(ref) else float("nan"),
            "observed_wavelength_um": (wl * (1.0 + z)) if np.isfinite(wl) else float("nan"),
            "fwhm_um": fwhm if np.isfinite(fwhm) else float("nan"),
            "quantity": "",
            "unit": "",
            "flux_observed": float("nan"),
            "flux_intrinsic": float("nan"),
            "flux_peak_observed": float("nan"),
            "flux_peak_intrinsic": float("nan"),
            "ew_um": float("nan"),
            "temperature_K": _component_value(model, name, "temperature"),
            "tau": _component_value(model, name, "amplitude"),
            "tau_sil": float("nan"),
            "attenuation_at_feature": float("nan"),
            "notes": "",
            "snr": float("nan"),
            "spec_index": None,
            "at_bound": bool(name in at_bound_features),
            "extrapolated": False,
            "status": "ok",
        }
        if not included:
            rec["notes"] = "outside fitted wavelength range"
            rec["status"] = "excluded_from_fit"
            records.append(rec)
            continue

        if kind in ("line", "dust_feature"):
            values = _feature_flux(model, name, kind, wl, fwhm, z)
            rec["quantity"] = "integrated_line_power"
            rec["unit"] = "MJy/sr THz"
            rec["notes"] = ("PAHFIT integrated line power (frequency integral); "
                            "observed = S07-attenuated, intrinsic = unattenuated; "
                            "not ∫F_nu dlambda")
        elif kind in ("dust_continuum", "starlight"):
            values = _feature_flux(model, name, kind, ref, fwhm, z)
            rec["quantity"] = f"flux_density_{ref:g}um"
            rec["unit"] = "MJy/sr"
            rec["extrapolated"] = bool(ref < rest_min or ref > rest_max)
            label = "dust continuum" if kind == "dust_continuum" else "stellar continuum"
            rec["notes"] = f"{label} flux density at rest {ref:g} um; not an integrated flux"
            if rec["extrapolated"]:
                rec["notes"] += "; reference wavelength outside fitted range (extrapolated)"
        elif kind in ("attenuation", "absorption"):
            val = _feature_power(model, name, kind)
            values = {"flux_observed": val, "flux_intrinsic": val,
                      "flux_peak_observed": val, "flux_peak_intrinsic": val,
                      "ew_um": float("nan"), "attenuation_at_feature": float("nan")}
            rec["quantity"] = "tau_sil" if kind == "attenuation" else "tau"
            rec["unit"] = ""
            rec["tau_sil"] = val if kind == "attenuation" else float("nan")
            rec["notes"] = "multiplicative attenuation parameter"
        else:
            values = {}
            rec["notes"] = f"unsupported feature kind: {kind}"
            rec["status"] = "unsupported"
        rec.update({k: v for k, v in values.items() if k in rec})
        if rec["included_in_fit"] and rec["kind"] in ("line", "dust_feature"):
            wobs = rec.get("observed_wavelength_um", float("nan"))
            for gap in coverage.get("gaps", []):
                if (gap.get("width_um", 0.0) > 0.5 and
                        gap.get("start_um", np.inf) <= wobs <= gap.get("end_um", -np.inf)):
                    rec["status"] = "coverage_gap"
                    rec["notes"] = (rec["notes"] +
                                    "; observed wavelength lies in a coverage gap "
                                    "(unconstrained)").strip("; ")
                    break
        if rec["at_bound"]:
            rec["status"] = "at_bound"
        if rec["extrapolated"] and rec["status"] == "ok":
            rec["status"] = "extrapolated"
        if (np.isfinite(rec["flux_intrinsic"]) and rec["kind"] in
                ("line", "dust_feature", "dust_continuum", "starlight")
                and rec["flux_intrinsic"] == 0):
            rec["status"] = "zero_flux"
        # Gap coverage is the dominant caveat: re-assert it after the
        # at-bound/zero-flux status assignment.
        if rec["included_in_fit"] and rec["kind"] in ("line", "dust_feature"):
            wobs = rec.get("observed_wavelength_um", float("nan"))
            for gap in coverage.get("gaps", []):
                if (gap.get("width_um", 0.0) > 0.5 and
                        gap.get("start_um", np.inf) <= wobs <= gap.get("end_um", -np.inf)):
                    rec["status"] = "coverage_gap"
                    if "coverage gap" not in rec["notes"]:
                        rec["notes"] = (rec["notes"] +
                                        "; observed wavelength lies in a coverage "
                                        "gap (unconstrained)").strip("; ")
                    break
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
            wl = float(rec["rest_wavelength_um"])
            fwhm = float(rec["fwhm_um"])
            specs.append({"record": idx, "name": name, "kind": kind,
                          "mode": "integrated", "wl": wl, "fwhm": fwhm,
                          "ref": wl, "unit": "MJy/sr THz",
                          "quantity": "integrated_line_power"})
        elif kind in ("dust_continuum", "starlight"):
            ref = float(rec["reference_wavelength_um"])
            specs.append({"record": idx, "name": name, "kind": kind,
                          "mode": "flux_density", "wl": ref, "fwhm": float(rec["fwhm_um"]),
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
        if sp["mode"] in ("integrated", "flux_density"):
            values = _feature_flux(model, sp["name"], sp["kind"],
                                   float(sp["wl"]), float(sp["fwhm"]), z,
                                   compute_ew=False)
            obs.append(values["flux_observed"])
            intr.append(values["flux_intrinsic"])
        else:
            val = _feature_power(model, sp["name"], sp["kind"])
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
    ierrs = []
    chi2s = []
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
        ierr = 0
        nf = 0
        chi2b = float("nan")
        try:
            mb.fit(sb, redshift=z, maxiter=maxiter, verbose=False)
            try:
                fi = mb.fitter.fit_info
                ierr = int(fi.get("ierr", 0))
                nf = int(fi.get("nfev", 0))
            except Exception:
                ierr, nf = 0, 0
            pred_b = np.asarray(mb.fitter.model(lam_rest), float)
            y_rest_b = y * (1.0 + z)
            sig_rest_b = sigma * (1.0 + z)
            good_b = (np.isfinite(pred_b) & np.isfinite(y_rest_b)
                      & np.isfinite(sig_rest_b) & (sig_rest_b > 0))
            if good_b.any():
                chi2b = float(np.sum(((y_rest_b[good_b] - pred_b[good_b])
                                      / sig_rest_b[good_b]) ** 2))
            if ierr not in (1, 2, 3, 4):
                st = f"fit_not_converged:ierr={ierr}"
            elif not np.isfinite(chi2b):
                st = "fit_failed:nonfinite_chi2"
            else:
                so, si = _quantities_for_model(mb, specs, z)
                samples_o[i] = so
                samples_i[i] = si
        except Exception as exc:  # noqa: BLE001
            st = f"fit_failed:{type(exc).__name__}"
            try:
                ierr = int(mb.fitter.fit_info.get("ierr", 0))
            except Exception:
                ierr = 0
        status.append(st)
        ierrs.append(ierr)
        chi2s.append(chi2b)
        nfev.append(int(nf))
        runtime.append(time.time() - t0)
    n_ok = int(sum(s == "ok" for s in status))
    err_o = np.nanstd(samples_o, axis=0, ddof=1) if n_ok > 1 else np.full(len(specs), np.nan)
    err_i = np.nanstd(samples_i, axis=0, ddof=1) if n_ok > 1 else np.full(len(specs), np.nan)
    q16 = np.nanpercentile(samples_o, 15.87, axis=0) if n_ok > 1 else np.full(len(specs), np.nan)
    q84 = np.nanpercentile(samples_o, 84.13, axis=0) if n_ok > 1 else np.full(len(specs), np.nan)
    frozen = np.zeros(len(specs), dtype=bool)
    if n_ok > 1:
        med = np.nanmedian(samples_o, axis=0)
        for k in range(len(specs)):
            if not np.isfinite(med[k]):
                continue
            vals = samples_o[:, k]
            vals = vals[np.isfinite(vals)]
            if vals.size < 3:
                continue
            rel = np.nanstd(vals, ddof=1) / max(abs(med[k]), 1e-300)
            n_unique = len(np.unique(np.round(vals, 12)))
            if (abs(med[k]) > 0 and rel < 1e-6) or (n_unique < max(3, n_ok // 2)):
                frozen[k] = True
    n_frozen = int(np.sum(frozen))
    err_o_raw = err_o.copy()
    if np.isfinite(flux_scale) and flux_scale != 1.0:
        samples_o = samples_o * float(flux_scale)
        samples_i = samples_i * float(flux_scale)
        err_o = err_o * float(flux_scale)
        err_i = err_i * float(flux_scale)
        q16 = q16 * float(flux_scale)
        q84 = q84 * float(flux_scale)
        err_o_raw = err_o_raw * float(flux_scale)
    err_o = np.where(frozen, np.nan, err_o)
    err_i = np.where(frozen, np.nan, err_i)
    return {
        "method": "bootstrap",
        "samples_o": samples_o,
        "samples_i": samples_i,
        "err_o": err_o,
        "err_i": err_i,
        "err_o_raw": err_o_raw,
        "err_sample_o": err_o,
        "err_sample_i": err_i,
        "q16_o": q16,
        "q84_o": q84,
        "frozen": frozen,
        "n_frozen": n_frozen,
        "status": status,
        "nfev": nfev,
        "ierr": ierrs,
        "chi2": chi2s,
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
        "reference_wavelength_um", "observed_wavelength_um", "fwhm_um",
        "included_in_fit", "at_bound", "extrapolated", "quantity", "unit",
        "flux_observed", "flux_intrinsic", "flux_peak_observed",
        "flux_peak_intrinsic", "ew_um", "temperature_K", "tau", "tau_sil",
        "attenuation_at_feature", "snr", "status", "notes",
    ]
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
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
                "reference_wavelength_um": _fmt(r.get("reference_wavelength_um", float("nan"))),
                "observed_wavelength_um": _fmt(r["observed_wavelength_um"]),
                "fwhm_um": _fmt(r["fwhm_um"]),
                "included_in_fit": str(bool(r["included_in_fit"])).lower(),
                "at_bound": str(bool(r.get("at_bound", False))).lower(),
                "extrapolated": str(bool(r.get("extrapolated", False))).lower(),
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
                "status": r.get("status", "ok"),
                "notes": r["notes"],
            })


def write_uncertainties_csv(path: Path, records, specs, mc, method, n_samples,
                            scale_chi2=None):
    cols = [
        "feature", "group", "kind", "quantity", "unit", "rest_wavelength_um",
        "flux", "err", "err_delta", "err_low", "err_high", "flux_intrinsic",
        "err_intrinsic", "method", "n_samples", "included_in_fit", "reliable",
        "status",
    ]
    by_record = {sp["record"]: k for k, sp in enumerate(specs)}
    frozen = mc.get("frozen")
    err_delta_all = mc.get("err_delta_o")
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for idx, r in enumerate(records):
            k = by_record.get(idx)
            status = "ok"
            reliable = True
            flux = r["flux_observed"]
            flux_i = r["flux_intrinsic"]
            err = err_d = err_lo = err_hi = err_i = float("nan")
            if not r["included_in_fit"]:
                status = "excluded_from_fit"
                reliable = False
            elif k is None:
                status = "no_quantity"
                reliable = False
            else:
                err = float(mc["err_o"][k]) if k < len(mc["err_o"]) else float("nan")
                err_i = float(mc["err_i"][k]) if k < len(mc["err_i"]) else float("nan")
                if err_delta_all is not None and k < len(err_delta_all):
                    err_d = float(err_delta_all[k])
                if method == "covariance":
                    err_d = err
                try:
                    q16 = float(mc["q16_o"][k])
                    q84 = float(mc["q84_o"][k])
                    if np.isfinite(q16) and np.isfinite(q84):
                        err_lo = flux - q16
                        err_hi = q84 - flux
                except Exception:
                    pass
                if frozen is not None and k < len(frozen) and bool(frozen[k]):
                    reliable = False
                    err_i = float("nan")
                    err_lo = float("nan")
                    err_hi = float("nan")
                    use_delta = (np.isfinite(err_d)
                                 and np.isfinite(flux) and flux != 0
                                 and abs(err_d) <= 10.0 * abs(flux))
                    if use_delta:
                        err = err_d
                        status = "bootstrap_frozen_covariance_fallback"
                    else:
                        err = float("nan")
                        status = "bootstrap_frozen_unconstrained"
                elif not np.isfinite(err):
                    status = "mc_unavailable"
                    reliable = False
                elif err == 0 and (not np.isfinite(flux) or flux == 0):
                    status = "at_bound_or_zero"
                    reliable = False
                elif (method == "covariance"
                      and mc.get("cov", {}).get("rank", 0) < mc.get("n_free", 0)):
                    status = "covariance_rank_deficient"
                    reliable = False
                if r.get("status") == "coverage_gap":
                    status = "coverage_gap"
                    reliable = False
                    err = err_d = err_lo = err_hi = err_i = float("nan")
                if r.get("at_bound"):
                    status = "at_bound" if status == "ok" else status
                    reliable = False
            scale = float(np.sqrt(scale_chi2)) if (
                scale_chi2 is not None and np.isfinite(scale_chi2)
                and scale_chi2 > 0) else 1.0
            if scale != 1.0:
                err = err * scale if np.isfinite(err) else err
                err_d = err_d * scale if np.isfinite(err_d) else err_d
                err_lo = err_lo * scale if np.isfinite(err_lo) else err_lo
                err_hi = err_hi * scale if np.isfinite(err_hi) else err_hi
                err_i = err_i * scale if np.isfinite(err_i) else err_i
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
                "reliable": str(bool(reliable)).lower(),
                "status": status,
            })


def write_samples_csv(path: Path, records, specs, mc, method):
    cols = ["sample"] + [sp["name"] for sp in specs]
    if method == "bootstrap":
        cols.append("status")
    with path.open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
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
        rec = records[idx]
        if rec.get("status") == "coverage_gap":
            continue
        flux = rec["flux_observed"]
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
        if r.get("status") == "coverage_gap":
            continue
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
    elif method == "bootstrap":
        ax_trace.text(0.5, 0.55, "Bootstrap samples are frozen",
                      ha="center", va="center", transform=ax_trace.transAxes,
                      fontsize=10)
        ax_trace.text(0.5, 0.42, f"N = {n_samples}, no finite feature errors",
                      ha="center", va="center", transform=ax_trace.transAxes,
                      fontsize=8)
        ax_trace.set_axis_off()
    else:
        cov_info = mc.get("cov", {})
        ax_trace.text(0.5, 0.55, "Linearized covariance mode",
                      ha="center", va="center", transform=ax_trace.transAxes,
                      fontsize=10)
        ax_trace.text(0.5, 0.42, f"rank {cov_info.get('rank', 0)}/{mc.get('n_free', 0)}  "
                      f"rcond {cov_info.get('rcond', float('nan')):g}",
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
             "line powers are MJy/sr THz. observed = S07-attenuated model; "
             "intrinsic = attenuation removed.",
             fontsize=7, color="0.35")
    fig.tight_layout(rect=(0, 0.02, 1, 0.94))
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _subset_spectrum(spec, mask):
    mask = np.asarray(mask, dtype=bool)
    out = Spectrum1D(
        spectral_axis=spec.spectral_axis[mask],
        flux=spec.flux[mask],
        uncertainty=StdDevUncertainty(
            np.asarray(spec.uncertainty.array, float)[mask] * spec.flux.unit),
    )
    out.meta.update(spec.meta)
    return out


def _relative_residual_mask(model, spec, z, nmad):
    """Robust relative-residual clip (used for unflagged cosmic rays)."""
    lam = spec.spectral_axis.to_value(u.micron) / (1.0 + z)
    y = np.asarray(spec.flux.value, float)
    try:
        pred = np.asarray(model.fitter.model(lam), float) / (1.0 + z)
    except Exception:
        return np.ones(len(y), dtype=bool)
    good = np.isfinite(y) & np.isfinite(pred) & (y != 0)
    if good.sum() < 10:
        return good
    scale = np.maximum(np.abs(y), 1e-3 * np.nanmedian(np.abs(y[good])))
    rel = np.full(len(y), np.nan)
    rel[good] = (y[good] - pred[good]) / scale[good]
    med = float(np.nanmedian(rel[good]))
    mad = 1.4826 * float(np.nanmedian(np.abs(rel[good] - med)))
    if not np.isfinite(mad) or mad <= 0:
        return good
    mask = good & (np.abs(rel - med) <= float(nmad) * mad)
    return mask


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
                   help="effective aperture (arcsec^2) for flux-density -> MJy/sr "
                        "(MIRI x1d and MIRI s1d tables)")
    p.add_argument("--tbl-aperture-arcsec2", type=float,
                   default=float(inp.get("tbl_aperture_arcsec2", 1.0)),
                   help="common aperture (arcsec^2) for Spitzer IRS .tbl Jy data")
    p.add_argument("--min-wave", type=float, default=float(inp.get("min_wave", 5.0)))
    p.add_argument("--max-wave", type=float, default=float(inp.get("max_wave", 38.0)))
    p.add_argument("--normalize-fit", action=argparse.BooleanOptionalAction,
                   default=fit.get("normalize", None),
                   help="divide the input by its median before fitting; "
                        "auto-enabled for MC runs to keep PAHFIT's least "
                        "squares well scaled")
    p.add_argument("--clip-nmad", type=float, default=float(fit.get("clip_nmad", 0.0)),
                   help="optional robust outlier rejection: clip points whose "
                        "relative residual is > NMAD robust standard deviations "
                        "(0 disables; applied after the first fit)")
    p.add_argument("--clip-iterations", type=int,
                   default=int(fit.get("clip_iterations", 1)),
                   help="number of clip/refit iterations when --clip-nmad > 0")

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
    input_stats = []
    coverage = {"gaps": [], "max_gap_um": 0.0, "gap_total_um": 0.0}
    n_input = 0
    n_duplicates = 0
    if args.spectrum:
        from pahfit.helpers import read_spectrum
        spec = read_spectrum(args.spectrum)
        if not spec.flux.unit.is_equivalent(u.MJy / u.sr):
            fl, er, _, _ = _to_mjy_sr(
                spec.flux.value, spec.uncertainty.array,
                str(spec.flux.unit), args.aperture_arcsec2, args.spectrum)
            spec = Spectrum1D(spectral_axis=spec.spectral_axis,
                              flux=fl * u.MJy / u.sr,
                              uncertainty=StdDevUncertainty(er * u.MJy / u.sr))
        if args.instrument:
            parts = [x.strip() for x in args.instrument.split(",") if x.strip()]
            spec.meta["instrument"] = parts[0] if len(parts) == 1 else parts
        w = spec.spectral_axis.to_value(u.micron)
        flux_unit = str(spec.flux.unit)
        n_input = int(len(w))
        print(f"[pahfit] packaged spectrum {args.spectrum}: {len(w)} pixels, "
              f"{w.min():.2f}-{w.max():.2f} um, unit={flux_unit}")
    else:
        waves, fluxes, errs = [], [], []
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
                aperture = args.tbl_aperture_arcsec2
            elif args.s1d:
                w, fl, er, dq, uu = read_s1d(f)
                aperture = args.aperture_arcsec2
            else:
                w, fl, er, dq, uu = read_x1d(f)
                aperture = args.aperture_arcsec2
            unit_in = str(uu)
            fl, er, uu, conv = _to_mjy_sr(fl, er, uu, aperture, f.name)
            good = (np.isfinite(w) & np.isfinite(fl) & np.isfinite(er) & (er > 0)
                    & (dq == 0) & (w >= args.min_wave) & (w <= args.max_wave))
            n_total = int(len(w))
            n_flagged = int(np.sum(dq != 0))
            n_input += n_total
            input_stats.append({
                "file": f.name,
                "n_total": n_total,
                "n_good": int(good.sum()),
                "n_flagged": n_flagged,
                "unit_in": unit_in,
                "conversion_to_MJy_sr": float(conv),
                "aperture_arcsec2": float(aperture),
                "wave_min_um": float(np.nanmin(w[good])) if good.any() else None,
                "wave_max_um": float(np.nanmax(w[good])) if good.any() else None,
            })
            waves.append(w[good]); fluxes.append(fl[good]); errs.append(er[good])
            if good.any():
                print(f"[pahfit] {f.name}: {good.sum()}/{n_total} good pixels, "
                      f"{w[good].min():.2f}-{w[good].max():.2f} um, "
                      f"in={input_stats[-1]['unit_in']}, out=MJy/sr, "
                      f"median flux={np.nanmedian(fl[good]):.6g}, "
                      f"median err={np.nanmedian(er[good]):.6g}")
            else:
                print(f"[pahfit] {f.name}: no good pixels after masking")
        w = np.concatenate(waves); fl = np.concatenate(fluxes); er = np.concatenate(errs)
        order = np.argsort(w); w, fl, er = w[order], fl[order], er[order]
        # Remove exact/near duplicates from overlapping IRS orders or MRS segments.
        keep = np.ones(len(w), dtype=bool)
        for i in range(1, len(w)):
            if abs(w[i] - w[i - 1]) < 1e-5:
                keep[i] = False
        n_duplicates = int(len(w) - keep.sum())
        w, fl, er = w[keep], fl[keep], er[keep]
        w, fl, er = bin_spectrum(w, fl, er, args.smooth_um)
        coverage = _coverage_info(w)
        flux_unit = "MJy/sr"
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
        spec.meta["input_stats"] = input_stats
        spec.meta["coverage"] = coverage
        print(f"[pahfit] combined {len(w)} pixels, {w.min():.2f}-{w.max():.2f} um, "
              f"z={args.z}, bin={args.smooth_um}, unit={flux_unit}, "
              f"median flux={np.nanmedian(fl):.6g}, "
              f"median err={np.nanmedian(er):.6g}")
        if coverage["gaps"]:
            print("[pahfit] coverage gaps: " + "; ".join(
                f"{g['start_um']:.3f}-{g['end_um']:.3f} um "
                f"({g['width_um']:.3f})" for g in coverage["gaps"]), flush=True)

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
    clip_refits = 0
    fit_info_last = {}
    fit_converged = True

    def _fit_once(spec_fit):
        nonlocal passes_done, status, fit_info_last, fit_converged
        t_pass = time.time()
        try:
            model.fit(spec_fit, redshift=args.z, maxiter=args.maxiter, verbose=False)
            passes_done += 1
            try:
                fi = model.fitter.fit_info
                fit_info_last = {
                    "nfev": int(fi.get("nfev", 0)),
                    "ierr": int(fi.get("ierr", 0)),
                    "message": str(fi.get("message", "")),
                }
            except Exception:
                fit_info_last = {}
            ierr = int(fit_info_last.get("ierr", 0))
            if ierr not in (1, 2, 3, 4):
                fit_converged = False
                status = f"fit_not_converged:ierr={ierr}"
            try:
                lam_rest = spec_fit.spectral_axis.to_value(u.micron) / (1.0 + args.z)
                pred = np.asarray(model.fitter.model(lam_rest), float)
                y_rest = np.asarray(spec_fit.flux.value, float) * (1.0 + args.z)
                sig_rest = np.asarray(spec_fit.uncertainty.array, float) * (1.0 + args.z)
                good = (np.isfinite(pred) & np.isfinite(y_rest)
                        & np.isfinite(sig_rest) & (sig_rest > 0))
                chi2 = float(np.sum(((y_rest[good] - pred[good])
                                     / sig_rest[good]) ** 2))
                pass_chi2.append(chi2)
            except Exception:
                pass_chi2.append(float("nan"))
            print(f"[pahfit] fit pass {passes_done}: chi2={pass_chi2[-1]:.6g} "
                  f"ierr={fit_info_last.get('ierr', '?')} "
                  f"({time.time() - t_pass:.2f} s)", flush=True)
        except Exception as exc:  # noqa: BLE001
            status = f"fit_failed:{type(exc).__name__}"
            fit_converged = False
            print(f"[pahfit] fit pass {passes_done + 1} failed: {exc}", flush=True)
            raise

    for ipass in range(max(1, int(args.fit_passes))):
        try:
            _fit_once(fit_spec)
        except Exception:
            break

    # Optional robust clipping of unflagged cosmic rays / hot pixels.
    n_clipped = 0
    if args.clip_nmad and args.clip_nmad > 0 and passes_done > 0:
        n_par = 0
        try:
            n_par = int(len(model.fitter.model.param_names))
        except Exception:
            pass
        for iclip in range(max(0, int(args.clip_iterations))):
            n_before = int(len(fit_spec.spectral_axis))
            mask = _relative_residual_mask(
                model, fit_spec, args.z, args.clip_nmad)
            n_new = int(mask.sum())
            if n_new == n_before:
                break
            if n_new < max(10, n_par + 5):
                print(f"[pahfit] clipping would leave only {n_new} pixels; "
                      f"stopping robust clip", flush=True)
                break
            fit_spec = _subset_spectrum(fit_spec, mask)
            n_clipped += n_before - n_new
            print(f"[pahfit] robust clip {iclip + 1}: kept {n_new} pixels "
                  f"(clipped {n_before - n_new}; total {n_clipped})",
                  flush=True)
            try:
                _fit_once(fit_spec)
                clip_refits += 1
            except Exception:
                break

    # PAHFIT 2.0 stores instrument and redshift in swapped metadata slots
    # inside Model.fit().  Write authoritative values for downstream users.
    model.features.meta["instrument"] = fit_spec.meta.get("instrument", "")
    model.features.meta["redshift"] = float(args.z)

    out_model = _scaled_model_copy(model, fit_scale)
    out_model.features.meta["instrument"] = fit_spec.meta.get("instrument", "")
    out_model.features.meta["redshift"] = float(args.z)
    out_model.save(str(args.output / "pahfit_output.ecsv"), overwrite=True)
    out_model.features.write(str(args.output / "pahfit_features.csv"),
                             format="ascii.csv", overwrite=True)

    plot_status = "ok"
    try:
        plot_model = _scaled_model_copy(model, fit_scale)
        try:
            plot_model._set_up_fitter(spec.meta.get("instrument"),
                                      args.z, lam=w, use_instrument_fwhm=True)
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
    rms_rel_all = float("nan")
    chi2_best = float("nan")
    n_data = 0
    n_free_all = 0
    n_free = 0
    n_at_bound = 0
    try:
        lam = fit_spec.spectral_axis.to_value(u.micron) / (1.0 + args.z)
        pred = np.asarray(model.fitter.model(lam), float) / (1.0 + args.z)
        y = np.asarray(fit_spec.flux.value, float)
        if pred.shape == y.shape:
            rms_rel = float(np.sqrt(np.nanmean((y - pred) ** 2))
                            / max(np.nanmedian(np.abs(y)), 1e-30))
        # Same metric on all input pixels (including clipped outliers).
        try:
            lam_all = spec.spectral_axis.to_value(u.micron) / (1.0 + args.z)
            pred_all = (np.asarray(model.fitter.model(lam_all), float)
                        * float(fit_scale) / (1.0 + args.z))
            y_all = np.asarray(spec.flux.value, float)
            if pred_all.shape == y_all.shape:
                rms_rel_all = float(np.sqrt(np.nanmean((y_all - pred_all) ** 2))
                                    / max(np.nanmedian(np.abs(y_all)), 1e-30))
        except Exception:
            pass
        y_rest = np.asarray(fit_spec.flux.value, float) * (1.0 + args.z)
        sig_rest = np.asarray(fit_spec.uncertainty.array, float) * (1.0 + args.z)
        pred_rest = np.asarray(model.fitter.model(lam), float)
        good = (np.isfinite(pred_rest) & np.isfinite(y_rest)
                & np.isfinite(sig_rest) & (sig_rest > 0))
        n_data = int(good.sum())
        chi2_best = float(np.sum(((y_rest[good] - pred_rest[good])
                                  / sig_rest[good]) ** 2))
        try:
            mfit = model.fitter.model
            n_free_all = int(sum(1 for v in dict(mfit.fixed).values() if not v))
            n_free = n_free_all
        except Exception:
            pass
        try:
            free_tmp, at_tmp, _ = _free_parameters(model)
            n_free = len(free_tmp)
            n_at_bound = len(at_tmp)
        except Exception:
            n_at_bound = 0
    except Exception:
        pass
    # Use all optimized parameters in the dof, including those resting on a
    # physical bound: they are still parameters selected by the fit.
    dof = max(1, n_data - max(n_free_all, 0))
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
        probe = None
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
                # Require a full-rank covariance in auto mode.  A rank of
                # 0.8*n_free is not enough: the missing directions still
                # produce meaningless zero/underestimated feature errors.
                if (cov["cov"]["rank"] < cov["n_free"]
                        or cov["cov"]["condition"] > 1e6
                        or cov["n_data"] <= cov["n_free"] + 2):
                    fallback = (f"covariance_ill_conditioned_rank_"
                                f"{cov['cov']['rank']}_of_{cov['n_free']}_"
                                f"cond_{cov['cov']['condition']:.3g}_"
                                f"ndata_{cov['n_data']}")
                    probe = cov
                    cov = None
            elif cov is not None:
                probe = cov
        elif args.mc_method == "bootstrap":
            # A cheap covariance probe supplies delta-method errors and the
            # rank/condition diagnostics even when bootstrap is requested.
            try:
                probe = run_covariance_mc(
                    model, fit_spec, args.z, records, specs, 0,
                    args.mc_rcond, rng, chi2_red=chi2_red,
                    flux_scale=fit_scale,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[pahfit] covariance probe failed: {exc}", flush=True)
                probe = None
        if cov is not None:
            mc = cov
            method = "covariance"
        elif args.mc_samples > 0:
            method = "bootstrap"
            if fallback is None and args.mc_method != "bootstrap":
                fallback = "covariance_unavailable"
            print(f"[pahfit] using full-refit bootstrap "
                  f"({args.mc_samples} realizations, mode={args.mc_bootstrap_mode})",
                  flush=True)
            mc = run_bootstrap_mc(
                model, fit_spec, args.z, specs, args.mc_samples, args.mc_seed,
                args.mc_maxiter, args.mc_bootstrap_mode,
                flux_scale=fit_scale,
            )
            if probe is not None and "err_o" in probe:
                mc["err_delta_o"] = np.asarray(probe["err_o"], float)
                mc["err_delta_i"] = np.asarray(probe["err_i"], float)
        mc_runtime = time.time() - t_mc
        mc_summary.update({
            "method": method,
            "runtime_s": float(mc_runtime),
            "fallback_reason": fallback,
            "n_samples_ok": (int(mc.get("n_ok", args.mc_samples))
                             if method == "bootstrap" else int(args.mc_samples)),
        })
        if probe is not None:
            mc_summary["covariance_probe"] = {
                "rank": int(probe["cov"]["rank"]),
                "n_free": int(probe["n_free"]),
                "n_at_bound": int(probe["n_at_bound"]),
                "n_data": int(probe["n_data"]),
                "condition_number": float(probe["cov"]["condition"]),
                "rank_deficient": bool(probe["cov"]["rank"] < probe["n_free"]),
            }
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
                "reliable": bool(mc["cov"]["rank"] >= mc["n_free"]),
            }
            err_scale = (float(np.sqrt(chi2_red))
                         if args.mc_scale == "chi2" and np.isfinite(chi2_red)
                         and chi2_red > 0 else 1.0)
            by_record = {sp["record"]: k for k, sp in enumerate(specs)}
            for idx, rec in enumerate(records):
                k = by_record.get(idx)
                if k is None:
                    continue
                _e = float(mc["err_o"][k]) if k < len(mc["err_o"]) else float("nan")
                _e *= err_scale
                _f = float(rec["flux_observed"])
                if mc["cov"]["rank"] < mc["n_free"]:
                    # A truncated covariance has missing directions; a formal
                    # S/N would be meaningless even if the diagonal is finite.
                    rec["snr"] = float("nan")
                else:
                    rec["snr"] = (_f / _e if np.isfinite(_e) and _e > 0
                                  else float("nan"))
        else:
            mc_summary["bootstrap"] = {
                "mode": str(mc.get("bootstrap_mode", args.mc_bootstrap_mode)),
                "n_ok": int(mc.get("n_ok", 0)),
                "n_failed": int(mc.get("n_failed", 0)),
                "n_not_converged": int(sum(
                    1 for x in mc.get("ierr", []) if int(x) not in (1, 2, 3, 4))),
                "n_frozen_features": int(mc.get("n_frozen", 0)),
                "median_nfev": float(np.nanmedian(mc.get("nfev", [np.nan]))),
                "median_chi2": float(np.nanmedian(mc.get("chi2", [np.nan]))),
                "median_runtime_s": float(np.nanmedian(mc.get("runtime", [np.nan]))),
            }
            by_record = {sp["record"]: k for k, sp in enumerate(specs)}
            for idx, rec in enumerate(records):
                k = by_record.get(idx)
                if k is None:
                    continue
                _e = float(mc["err_o"][k]) if k < len(mc["err_o"]) else float("nan")
                rec["snr"] = (float(rec["flux_observed"]) / _e
                              if np.isfinite(_e) and _e > 0 else float("nan"))
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

    for rec in records:
        if rec.get("status") == "coverage_gap":
            rec["snr"] = float("nan")

    # The always-on line table gets S/N values when MC is available.
    write_lines_csv(args.output / "pahfit_lines.csv", records)

    gap_feature_names = sorted({r["name"] for r in records
                                if r.get("status") == "coverage_gap"})
    n_features_enabled = 0
    try:
        n_features_enabled = int(len(model.enabled_features))
    except Exception:
        n_features_enabled = int(len(model.features))
    at_bound_fraction = (float(n_at_bound) / float(max(n_free_all, 1)))
    quality_flags = []
    if passes_done == 0 or status.startswith("fit_failed"):
        quality_flags.append("fit_failed")
    if not fit_converged:
        quality_flags.append("fit_not_converged")
    if np.isfinite(rms_rel) and rms_rel > 0.5:
        quality_flags.append("large_rms")
    if np.isfinite(chi2_red) and chi2_red > 10:
        quality_flags.append("formal_chi2_mismatch")
    if at_bound_fraction > 0.5:
        quality_flags.append("many_parameters_at_bound")
    if n_data <= max(n_free_all, 1) + 5:
        quality_flags.append("few_degrees_of_freedom")
    if coverage.get("max_gap_um", 0.0) > 0.5:
        quality_flags.append("coverage_gap")
    if gap_feature_names:
        quality_flags.append("features_in_coverage_gaps")
    if n_clipped > 0:
        quality_flags.append("outliers_clipped")
    if method == "covariance" and "covariance" in mc_summary:
        if mc_summary["covariance"].get("rank_deficient"):
            quality_flags.append("covariance_rank_deficient")
    if method == "bootstrap" and "bootstrap" in mc_summary:
        if mc_summary["bootstrap"].get("n_frozen_features", 0) > 0:
            quality_flags.append("bootstrap_frozen_features")
        if (mc_summary["bootstrap"].get("n_failed", 0) > 0
                or mc_summary["bootstrap"].get("n_not_converged", 0) > 0):
            quality_flags.append("mc_fit_failures")
    if args.mc_samples > 0 and method is None:
        quality_flags.append("mc_unavailable")

    if passes_done == 0 or status.startswith("fit_failed"):
        fit_quality = "failed"
    elif (not fit_converged) or (np.isfinite(rms_rel) and rms_rel > 0.5):
        fit_quality = "unstable"
    elif (np.isfinite(chi2_red) and chi2_red > 10) or at_bound_fraction > 0.5 \
            or coverage.get("max_gap_um", 0.0) > 0.5:
        fit_quality = "systematics_limited"
    else:
        fit_quality = "good"
    unstable = bool(fit_quality in ("failed", "unstable"))
    flagged = bool(unstable or quality_flags)

    summary = {
        "z": args.z, "instrument": str(spec.meta.get("instrument", "")),
        "n_pixels": int(len(fit_spec.spectral_axis)),
        "n_binned_pixels": int(len(w)),
        "n_input_pixels": int(n_input),
        "n_duplicates_removed": int(n_duplicates),
        "n_clipped": int(n_clipped),
        "flux_unit": flux_unit, "segment": args.segment,
        "smooth_um": args.smooth_um, "status": status, "plot_status": plot_status,
        "fit_converged": bool(fit_converged),
        "fit_quality": fit_quality,
        "quality_flags": quality_flags,
        "unstable": unstable,
        "flagged": flagged,
        "wave_min_um": float(np.min(spec.spectral_axis.value)),
        "wave_max_um": float(np.max(spec.spectral_axis.value)),
        "fit_wave_min_um": float(np.min(fit_spec.spectral_axis.value)),
        "fit_wave_max_um": float(np.max(fit_spec.spectral_axis.value)),
        "coverage": coverage,
        "features_in_coverage_gaps": gap_feature_names,
        "n_features_in_coverage_gaps": int(len(gap_feature_names)),
        "input_stats": input_stats,
        "n_features": int(n_features_enabled),
        "n_features_table": int(len(model.features)),
        "rms_rel": rms_rel,
        "rms_rel_all_input": rms_rel_all,
        "normalize_fit": bool(args.normalize_fit),
        "clip_nmad": float(args.clip_nmad),
        "clip_iterations": int(args.clip_iterations),
        "clip_refits": int(clip_refits),
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
        "at_bound_fraction": at_bound_fraction,
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
        summary["fit_info"] = fit_info_last
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
            "tbl_aperture_arcsec2": float(args.tbl_aperture_arcsec2),
            "min_wave_um": float(args.min_wave),
            "max_wave_um": float(args.max_wave),
            "files": input_stats,
            "coverage": coverage,
        },
        "preprocess": {"smooth_um": args.smooth_um,
                       "clip_nmad": float(args.clip_nmad),
                       "clip_iterations": int(args.clip_iterations),
                       "n_clipped": int(n_clipped)},
        "fit": {
            "maxiter": int(args.maxiter),
            "passes": int(args.fit_passes),
            "no_guess": bool(args.no_guess),
            "init_from": args.init_from,
            "normalize": bool(args.normalize_fit),
            "flux_scale": float(fit_scale),
            "converged": bool(fit_converged),
            "ierr": int(fit_info_last.get("ierr", 0)),
            "quality": fit_quality,
            "quality_flags": quality_flags,
            "chi2_red": float(chi2_red) if np.isfinite(chi2_red) else None,
            "dof": int(dof),
        },
        "monte_carlo": {
            "enabled": bool(args.mc_samples > 0),
            "samples": int(args.mc_samples),
            "method": args.mc_method,
            "resolved_method": method,
            "seed": int(args.mc_seed),
            "rcond": float(args.mc_rcond),
            "maxiter": int(args.mc_maxiter),
            "bootstrap_mode": args.mc_bootstrap_mode,
            "scale": args.mc_scale,
            "save_samples": bool(args.mc_save_samples),
            "fallback_reason": mc_summary.get("fallback_reason"),
        },
        "metadata": {
            "z": float(args.z),
            "wave_min_um": float(np.min(spec.spectral_axis.value)),
            "wave_max_um": float(np.max(spec.spectral_axis.value)),
            "n_pixels": int(len(fit_spec.spectral_axis)),
            "n_input_pixels": int(n_input),
            "flux_unit": "MJy/sr",
        },
    }
    (args.output / "effective_config.json").write_text(
        json.dumps(effective, indent=2, default=float)
    )

    print(f"[pahfit] done status={status} rms_rel={rms_rel:.3f} "
          f"chi2_red={chi2_red:.1f} quality={fit_quality} "
          f"flagged={flagged} -> {args.output}")
    if quality_flags:
        print("[pahfit] quality flags: " + ", ".join(quality_flags), flush=True)
    if args.mc_samples > 0:
        print(f"[pahfit] MC method={method} N={args.mc_samples} "
              f"runtime={mc_runtime:.1f}s")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
