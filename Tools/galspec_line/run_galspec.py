#!/usr/bin/env python3
"""GalSpec line fits for optical AGN/QSO spectra.

Two model modes are supported:

  full (production, configs/galspec_line/default)
      Global rest-frame 2280-6460 A model: normalised polynomial continuum,
      park2022 Fe II, narrow NLR lines, [O III] core/wing, broad Balmer,
      broad Mg II, all available Balmer lines through H12, and the available
      forbidden lines.  The full model is sampled with emcee.

  reduced (legacy, configs/galspec_line/reduced)
      The original 4720-5150 A H-beta/[O III] window with a local linear
      continuum and Fe II.  Auxiliary [O II]/[Ne III]/[S II] windows are
      fitted separately with LSQ covariance.  This path is kept for
      reproducibility and is not the production recipe.

GalSpec's Astropy models (Line_Gaussian, IronTemplate_new) and fitters
(TRFLSQFitter, MCMC_Fit, Dynesty_Fit) do the scientific work.  This adapter
only handles SDSS I/O, the rest-frame conversion, initial guesses, line-flux
integration, standardised output and cross-tool comparison.

Flux convention
---------------
SDSS COADD FLUX is in 1e-17 erg s-1 cm-2 A-1 (observed frame).  When converting
to rest-frame wavelengths, F_lambda_rest = F_lambda_obs * (1+z), the same
cosmological correction used by PyQSOFit and GANDALF in this repository.  All
internal modelling is in 1e-17 erg s-1 cm-2 A-1 (rest frame); output tables give
both 1e-17 and cgs values.
"""
from __future__ import annotations

import argparse
import copy
import json
import logging
import math
import os
import sys
import time
import traceback
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from astropy.io import fits  # noqa: E402
from astropy.modeling import fitting, models  # noqa: E402

try:
    from PyAstronomy import pyasl
except Exception:  # pragma: no cover
    pyasl = None

try:
    import extinction
except Exception:  # pragma: no cover
    extinction = None

try:
    import corner
except Exception:  # pragma: no cover
    corner = None

import galspec  # noqa: E402

LS_KM = 299792.458
SQRT2PI = math.sqrt(2.0 * math.pi)
FWHM_PER_SIGMA = 2.3548200450309493
FLUX_UNIT_1E17 = 1e-17

LOG = logging.getLogger("galspec_line")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
class TieSigma:
    """Tie ``sigma`` to another model's ``sigma``."""

    def __init__(self, ref_name: str):
        self.ref_name = ref_name

    def __call__(self, model):
        return model[self.ref_name].sigma


class TieDV:
    """Tie ``dv`` to another model's ``dv``."""

    def __init__(self, ref_name: str):
        self.ref_name = ref_name

    def __call__(self, model):
        return model[self.ref_name].dv


class TieAmplitudeRatio:
    """Tie ``amplitude`` to ``model[ref].amplitude / ratio``."""

    def __init__(self, ref_name: str, ratio: float):
        self.ref_name = ref_name
        self.ratio = float(ratio)

    def __call__(self, model):
        return model[self.ref_name].amplitude / self.ratio


def jsonable(value):
    """Recursively convert numpy scalars/arrays and non-finite floats to JSON."""
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return [jsonable(v) for v in value.tolist()]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, Path):
        return str(value)
    return value


def write_json(path: Path, payload: dict):
    path.write_text(json.dumps(jsonable(payload), indent=2, sort_keys=False) + "\n")


def set_tied_values(model):
    """Refresh every tied parameter from its reference parameter."""
    # Two passes are enough for the shallow tie chains used here.
    for _ in range(2):
        for name in model.param_names:
            param = getattr(model, name)
            if param.tied:
                param.value = param.tied(model)


def gaussian_flux(amplitude, sigma, wavec):
    """Analytic integral of a velocity-Gaussian line profile."""
    return float(amplitude) * float(sigma) * SQRT2PI * float(wavec) / LS_KM


def line_component_name(line_name: str, label: str) -> str:
    return f"{line_name}_{label}"


def as_float(value, default=None):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------
def _find_table_hdu(hdul):
    for hdu in hdul:
        columns = getattr(hdu, "columns", None)
        if columns is None:
            continue
        names = {c.lower() for c in columns.names}
        if "flux" in names and ("loglam" in names or "wl" in names):
            return hdu
    return None


def _column(data, *names):
    columns = {c.lower(): c for c in data.columns.names}
    for name in names:
        if name.lower() in columns:
            return np.asarray(data[columns[name.lower()]], dtype=float)
    return None


def _header_float(*headers, keys=("Z", "z", "REDSHIFT")):
    for header in headers:
        if header is None:
            continue
        for key in keys:
            if key in header:
                try:
                    return float(header[key])
                except (TypeError, ValueError):
                    pass
    return None


def find_input(input_path: Path) -> Path:
    input_path = Path(input_path)
    if input_path.is_file():
        return input_path
    if not input_path.is_dir():
        raise FileNotFoundError(f"input path does not exist: {input_path}")
    candidates = []
    for pattern in ("spectrum.fits", "raw/spec-*.fits", "raw/*.fits", "*.fits"):
        candidates.extend(sorted(input_path.glob(pattern)))
    # de-duplicate while preserving order
    seen = set()
    unique = []
    for p in candidates:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    if not unique:
        raise FileNotFoundError(f"no FITS spectrum found under {input_path}")
    return unique[0]


def read_spectrum(path: Path, z_override, cfg: dict) -> dict:
    """Read a raw SDSS COADD table or a prepared PyQSOFit-style FITS."""
    with fits.open(path, memmap=False) as hdul:
        hdr0 = hdul[0].header
        table_hdu = _find_table_hdu(hdul)
        if table_hdu is not None:
            data = table_hdu.data
            flux = _column(data, "flux")
            loglam = _column(data, "loglam")
            wl = _column(data, "wl")
            if flux is None:
                raise ValueError(f"{path}: table has no FLUX column")
            if loglam is not None:
                wave_obs = 10.0 ** loglam
            elif wl is not None:
                wave_obs = wl
            else:
                raise ValueError(f"{path}: table has no LOGLAM/WL column")
            ivar = _column(data, "ivar")
            stdev = _column(data, "stdev")
            if ivar is None and stdev is not None:
                ivar = 1.0 / np.square(stdev)
            if ivar is None:
                ivar = np.ones_like(flux)
            and_mask = _column(data, "and_mask")
            wresl = _column(data, "wresl")
            z = None
            ebv = None
            try:
                spall = hdul["SPALL"].data
                z = float(spall["Z"][0])
                if "SFD_EBV" in spall.columns.names:
                    ebv = float(spall["SFD_EBV"][0])
            except (KeyError, IndexError, TypeError, ValueError):
                pass
            if z is None:
                z = _header_float(hdr0)
            if ebv is None:
                ebv = as_float(hdr0.get("EBV", hdr0.get("SFD_EBV")), None)
            flux_scale = 1.0  # SDSS COADD is already 1e-17 cgs
            input_layout = "sdss_coadd_table"
        else:
            if len(hdul) < 2 or hdul[0].data is None:
                raise ValueError(f"{path}: not an SDSS COADD table and no image flux")
            flux = np.asarray(hdul[0].data, dtype=float).ravel()
            wave_hdu = None
            for hdu in hdul[1:]:
                if hdu.data is not None and np.asarray(hdu.data).size == flux.size:
                    wave_hdu = hdu
                    break
            if wave_hdu is None:
                raise ValueError(f"{path}: cannot find a wavelength array")
            wave_obs = np.asarray(wave_hdu.data, dtype=float).ravel()
            err_hdu = None
            for hdu in hdul[1:]:
                if hdu is wave_hdu:
                    continue
                if hdu.data is not None and np.asarray(hdu.data).size == flux.size:
                    err_hdu = hdu
                    break
            if err_hdu is None:
                err = np.full_like(flux, np.nan)
                ivar = np.zeros_like(flux)
            else:
                err = np.asarray(err_hdu.data, dtype=float).ravel()
                ivar = 1.0 / np.square(np.where(err > 0, err, np.nan))
            and_mask = None
            wresl = None
            fwhm_header = as_float(hdr0.get("fwhm", hdr0.get("FWHM")), None)
            if fwhm_header and fwhm_header > 0:
                wresl = np.full_like(flux, fwhm_header)
            z = _header_float(hdr0)
            ebv = as_float(hdr0.get("EBV", hdr0.get("SFD_EBV")), None)
            # cgs input is ~1e-16; SDSS 1e-17 input is ~1e1.
            finite = np.isfinite(flux)
            median_abs = float(np.nanmedian(np.abs(flux[finite]))) if finite.any() else 0.0
            flux_scale = 1e17 if median_abs < 1e-6 else 1.0
            input_layout = "prepared_image"

    z = z if z is not None else as_float(z_override)
    if z is None:
        cfg_z = cfg.get("input", {}).get("redshift", "auto")
        z = as_float(cfg_z)
    if z is None:
        raise ValueError(
            "cannot determine redshift; pass --z or set input.redshift in the config"
        )

    flux = np.asarray(flux, dtype=float)
    wave_obs = np.asarray(wave_obs, dtype=float)
    ivar = np.asarray(ivar, dtype=float)

    good = np.isfinite(wave_obs) & np.isfinite(flux) & np.isfinite(ivar) & (ivar > 0)
    if cfg.get("input", {}).get("mask_and_mask", True) and and_mask is not None:
        good &= np.asarray(and_mask) == 0
    wmin = cfg.get("input", {}).get("min_wavelength_angstrom")
    wmax = cfg.get("input", {}).get("max_wavelength_angstrom")
    if wmin is not None:
        good &= wave_obs >= float(wmin)
    if wmax is not None:
        good &= wave_obs <= float(wmax)

    if good.sum() < 20:
        raise ValueError(f"{path}: only {int(good.sum())} usable pixels")
    wave_obs = wave_obs[good]
    flux = flux[good] * flux_scale
    err = (1.0 / np.sqrt(ivar[good])) * flux_scale
    if wresl is not None:
        wresl = np.asarray(wresl, dtype=float)[good]
    else:
        wresl = None

    # Optional Galactic extinction correction in the observed frame.
    if cfg.get("input", {}).get("deredden", False) and ebv and extinction is not None:
        a_lambda = extinction.ccm89(wave_obs, 3.1 * float(ebv), 3.1)
        corr = 10.0 ** (0.4 * a_lambda)
        flux *= corr
        err *= corr

    # GalSpec's optical line database is in air wavelengths.  SDSS LOGLAM is
    # vacuum, so convert observed vacuum -> air before de-redshifting.
    if cfg.get("input", {}).get("vacuum_to_air", True) and pyasl is not None:
        try:
            wave_air = np.asarray(pyasl.vactoair2(wave_obs), dtype=float)
        except Exception:
            wave_air = wave_obs.copy()
    else:
        wave_air = wave_obs.copy()

    rest = wave_air / (1.0 + z)
    rest_flux_correction = bool(cfg.get("input", {}).get("rest_frame_flux_correction", True))
    factor = (1.0 + z) if rest_flux_correction else 1.0
    flux_rest = flux * factor
    err_rest = err * factor

    # Optional rest-frame trim.  The reduced-window config leaves these null;
    # the full-continuum config uses them to exclude the noisy SDSS edges.
    rest_min = cfg.get("input", {}).get("rest_min_wavelength_angstrom")
    rest_max = cfg.get("input", {}).get("rest_max_wavelength_angstrom")
    if rest_min is not None or rest_max is not None:
        rest_good = np.ones_like(rest, dtype=bool)
        if rest_min is not None:
            rest_good &= rest >= float(rest_min)
        if rest_max is not None:
            rest_good &= rest <= float(rest_max)
        if rest_good.sum() < 20:
            raise ValueError(f"{path}: only {int(rest_good.sum())} pixels after rest-frame trim")
        rest = rest[rest_good]
        flux_rest = flux_rest[rest_good]
        err_rest = err_rest[rest_good]
        if wresl is not None:
            wresl = np.asarray(wresl, dtype=float)[rest_good]

    order = np.argsort(rest)
    rest = rest[order]
    flux_rest = flux_rest[order]
    err_rest = err_rest[order]
    if wresl is not None:
        wresl = np.asarray(wresl, dtype=float)[order]

    return {
        "path": str(path),
        "layout": input_layout,
        "z": float(z),
        "ebv": None if ebv is None else float(ebv),
        "wave_rest_air": rest,
        "flux_1e17": flux_rest,
        "err_1e17": err_rest,
        "wresl_obs": wresl,
        "flux_scale_input_to_1e17": float(flux_scale),
        "rest_frame_flux_correction": rest_flux_correction,
        "n_pix_raw": int(len(wave_obs)),
        "n_pix_used": int(len(rest)),
        "wave_rest_min": float(np.nanmin(rest)),
        "wave_rest_max": float(np.nanmax(rest)),
        "deredden": bool(cfg.get("input", {}).get("deredden", False) and ebv and extinction is not None),
    }


# ---------------------------------------------------------------------------
# Model construction
# ---------------------------------------------------------------------------
def continuum_start(x, y, sidebands):
    mask = np.zeros_like(x, dtype=bool)
    for lo, hi in sidebands:
        mask |= (x >= float(lo)) & (x <= float(hi))
    if mask.sum() < 5:
        span = float(np.nanmax(x) - np.nanmin(x))
        lo = float(np.nanmin(x))
        mask = ((x >= lo) & (x <= lo + 0.1 * span)) | (
            (x >= lo + 0.9 * span) & (x <= lo + span)
        )
    if mask.sum() < 2:
        mask = np.isfinite(y)
    slope, intercept = np.polyfit(x[mask], y[mask], 1)
    side_cont = slope * x + intercept
    return float(slope), float(intercept), side_cont


def effective_errors(err, side_cont, cfg):
    floor_cfg = cfg.get("errors", {})
    floor = float(floor_cfg.get("floor_frac_of_continuum", 0.0)) * np.maximum(side_cont, 0.0)
    floor += float(floor_cfg.get("floor_abs", 0.0))
    out = np.sqrt(np.square(err) + np.square(floor))
    return np.maximum(out, float(floor_cfg.get("min_error", 1e-6)))


def make_continuum(slope, intercept, cfg, name="continuum"):
    model_type = str(cfg.get("continuum", {}).get("main_model", "linear")).lower()
    slope_pad = float(cfg.get("continuum", {}).get("slope_pad", 0.05))
    inter_pad = float(cfg.get("continuum", {}).get("intercept_pad", 50.0))
    if model_type in ("linear", "lin"):
        return models.Linear1D(
            slope=slope,
            intercept=intercept,
            name=name,
            bounds={
                "slope": (slope - slope_pad, slope + slope_pad),
                "intercept": (intercept - inter_pad, intercept + inter_pad),
            },
        )
    if model_type in ("powerlaw", "power_law", "pl"):
        x0 = float(cfg.get("continuum", {}).get("powerlaw_x0", 5000.0))
        alpha0 = float(cfg.get("continuum", {}).get("powerlaw_alpha0", -1.0))
        return models.PowerLaw1D(
            amplitude=float(intercept),
            x_0=x0,
            alpha=alpha0,
            name=name,
            fixed={"x_0": True},
            bounds={"amplitude": (0.0, max(2.0 * intercept, 1.0)), "alpha": (-5.0, 5.0)},
        )
    raise ValueError(f"unknown continuum model: {model_type}")


def initial_peak(x, y, cont_side, wavec, half_width=20.0):
    mask = (x >= wavec - half_width) & (x <= wavec + half_width)
    if mask.sum() == 0:
        return 0.1
    return max(float(np.max(y[mask] - cont_side[mask])), 0.1)


def build_main_model(cfg, x, y):
    sidebands = cfg.get("continuum", {}).get("sidebands", [[4720.0, 4780.0], [5110.0, 5150.0]])
    slope, intercept, cont_side = continuum_start(x, y, sidebands)
    model = make_continuum(slope, intercept, cfg)

    line_specs = []
    created = {}
    for line in cfg["main_window"]["lines"]:
        line_name = str(line["name"])
        wavec = float(line["wave"])
        tie_to = line.get("tie_to")
        comp_names = []
        comp_labels = []
        for comp in line.get("components", []):
            label = str(comp["label"])
            full_name = line_component_name(line_name, label)
            comp_labels.append(label)
            if tie_to:
                ref_name = line_component_name(str(tie_to), label)
                ref = created[ref_name]
                sigma0 = float(comp.get("sigma0", ref.sigma.value))
                sigma_bounds = tuple(comp.get("sigma_bounds", ref.bounds["sigma"]))
                amp_bounds = tuple(comp.get("amplitude_bounds", ref.bounds["amplitude"]))
                dv_bounds = tuple(comp.get("dv_bounds", ref.bounds["dv"]))
                component = galspec.Line_Gaussian(
                    amplitude=0.1,
                    dv=0.0,
                    sigma=sigma0,
                    wavec=wavec,
                    name=full_name,
                    bounds={
                        "amplitude": amp_bounds,
                        "sigma": sigma_bounds,
                        "dv": dv_bounds,
                    },
                )
                component.amplitude.tied = TieAmplitudeRatio(
                    ref_name, float(line.get("amplitude_ratio", 1.0))
                )
                component.dv.tied = TieDV(ref_name)
                component.sigma.tied = TieSigma(ref_name)
            else:
                if "amp0" in comp:
                    amp0 = float(comp["amp0"])
                else:
                    peak = initial_peak(
                        x, y, cont_side, wavec, float(comp.get("init_half_width", 20.0))
                    )
                    amp0 = peak * float(comp.get("amp0_frac", 1.0))
                component = galspec.Line_Gaussian(
                    amplitude=max(amp0, 0.05),
                    dv=float(comp.get("dv0", 0.0)),
                    sigma=float(comp.get("sigma0", 300.0)),
                    wavec=wavec,
                    name=full_name,
                    bounds={
                        "amplitude": tuple(comp.get("amplitude_bounds", [0.0, 300.0])),
                        "sigma": tuple(comp.get("sigma_bounds", [80.0, 4000.0])),
                        "dv": tuple(comp.get("dv_bounds", [-1500.0, 1500.0])),
                    },
                )
            model = model + component
            created[full_name] = component
            comp_names.append(full_name)
        line_specs.append(
            {
                "name": line_name,
                "wave": wavec,
                "components": comp_names,
                "component_labels": comp_labels,
                "profile_window": [float(v) for v in line.get("profile_window", [wavec - 50, wavec + 50])],
                "total": bool(line.get("total", True)),
                "kind": "main",
                "tie_to": tie_to,
            }
        )
    fe_cfg = cfg.get("continuum", {}).get("feii", {})
    if fe_cfg.get("enabled", False):
        # Keep the Fe II template last: its parameter ordering matters for the
        # finite-difference trust-region path, and this matches the validated
        # GalSpec prototype ordering.
        model = model + galspec.IronTemplate_new(
            amplitude=float(fe_cfg.get("amplitude0", 10.0)),
            sigma=float(fe_cfg.get("sigma0", 1500.0)),
            dv=float(fe_cfg.get("dv0", 0.0)),
            z=0.0,
            template_name=str(fe_cfg.get("template", "park2022")),
            name="FeII",
            bounds={
                "amplitude": tuple(fe_cfg.get("amplitude_bounds", [0.0, 300.0])),
                "sigma": tuple(fe_cfg.get("sigma_bounds", [400.0, 4000.0])),
                "dv": tuple(fe_cfg.get("dv_bounds", [-2000.0, 2000.0])),
            },
        )
    set_tied_values(model)
    return model, x, y, cont_side, line_specs


def build_aux_model(aux_cfg, x, y):
    sidebands = aux_cfg.get("sidebands")
    if not sidebands:
        lo, hi = [float(v) for v in aux_cfg["rest"]]
        span = hi - lo
        sidebands = [[lo, lo + 0.1 * span], [hi - 0.1 * span, hi]]
    slope, intercept, cont_side = continuum_start(x, y, sidebands)
    pad = float(aux_cfg.get("slope_pad", 0.05))
    model = models.Linear1D(
        slope=slope,
        intercept=intercept,
        name="continuum",
        bounds={
            "slope": (slope - pad, slope + pad),
            "intercept": (intercept - 50.0, intercept + 50.0),
        },
    )
    label = str(aux_cfg.get("component_label", "narrow"))
    created = {}
    line_specs = []
    for line in aux_cfg["lines"]:
        name = str(line["name"])
        wavec = float(line["wave"])
        full_name = line_component_name(name, label)
        peak = initial_peak(x, y, cont_side, wavec, float(line.get("init_half_width", 15.0)))
        component = galspec.Line_Gaussian(
            amplitude=max(peak * float(line.get("amp0_frac", 1.0)), 0.05),
            dv=0.0,
            sigma=float(line.get("sigma0", 300.0)),
            wavec=wavec,
            name=full_name,
            bounds={
                "amplitude": tuple(line.get("amplitude_bounds", [0.0, 300.0])),
                "sigma": tuple(line.get("sigma_bounds", [80.0, 900.0])),
                "dv": tuple(line.get("dv_bounds", [-1000.0, 1000.0])),
            },
        )
        ref = line.get("kinematic_ref")
        if ref:
            component.dv.tied = TieDV(str(ref))
            component.sigma.tied = TieSigma(str(ref))
        model = model + component
        created[full_name] = component
        line_specs.append(
            {
                "name": name,
                "wave": wavec,
                "components": [full_name],
                "component_labels": [label],
                "profile_window": [wavec - 45.0, wavec + 45.0],
                "total": False,
                "kind": "auxiliary",
                "tie_to": ref,
            }
        )
    set_tied_values(model)
    return model, x, y, cont_side, line_specs


# ---------------------------------------------------------------------------
# Metrics and fitting
# ---------------------------------------------------------------------------
def _crossing(grid, values, level, start, direction):
    j = start
    n = len(grid)
    if direction < 0:
        while j > 0 and values[j] > level:
            j -= 1
        if j == 0:
            return float(grid[0])
        f0, f1 = values[j], values[j + 1]
        g0, g1 = grid[j], grid[j + 1]
    else:
        while j < n - 1 and values[j] > level:
            j += 1
        if j == n - 1:
            return float(grid[-1])
        f0, f1 = values[j - 1], values[j]
        g0, g1 = grid[j - 1], grid[j]
    if f1 == f0:
        return float(g1)
    return float(g0 + (level - f0) * (g1 - g0) / (f1 - f0))


def total_profile_metrics(model, components, wavec, window, step=0.4):
    lo, hi = float(window[0]), float(window[1])
    grid = np.arange(lo, hi + step, step)
    if grid.size < 5:
        grid = np.linspace(lo, hi, 64)
    profile = np.zeros_like(grid)
    for name in components:
        profile += model[name](grid)
    imax = int(np.argmax(profile))
    fmax = float(profile[imax])
    if not np.isfinite(fmax) or fmax <= 0:
        return {"flux": float(np.nansum([0.0])), "fwhm": np.nan, "velocity": np.nan, "peak_wave": np.nan}
    half = 0.5 * fmax
    left = _crossing(grid, profile, half, imax, -1)
    right = _crossing(grid, profile, half, imax, +1)
    peak_wave = float(grid[imax])
    return {
        "flux": float(np.nansum([gaussian_flux(model[c].amplitude.value, model[c].sigma.value, model[c].wavec.value) for c in components])),
        "fwhm": float((right - left) / peak_wave * LS_KM),
        "velocity": float((peak_wave - wavec) / wavec * LS_KM),
        "peak_wave": peak_wave,
    }


def compute_metrics(model, line_specs):
    """Return {line|component: {flux, fwhm, velocity}}."""
    result = {}
    for spec in line_specs:
        comp_flux = 0.0
        for name in spec["components"]:
            sub = model[name]
            flux = gaussian_flux(sub.amplitude.value, sub.sigma.value, sub.wavec.value)
            comp_flux += flux
            result[f"{spec['name']}|{name.rsplit('_', 1)[-1]}"] = {
                "flux": float(flux),
                "fwhm": float(FWHM_PER_SIGMA * sub.sigma.value),
                "velocity": float(sub.dv.value),
                "peak_wave": float(sub.wavec.value + sub.dv.value / LS_KM * sub.wavec.value),
            }
        if spec.get("total", True):
            total = total_profile_metrics(
                model,
                spec["components"],
                spec["wave"],
                spec["profile_window"],
            )
            total["flux"] = float(comp_flux)
            result[f"{spec['name']}|total"] = total
    return result


def covariance_errors(model, free_names, cov, line_specs, metric_keys):
    """Propagate the LSQ parameter covariance to each derived line metric."""
    if cov is None:
        return {}
    cov = np.asarray(cov, dtype=float)
    if cov.ndim != 2 or cov.shape[0] != len(free_names) or cov.shape[1] != len(free_names):
        return {}
    base = compute_metrics(model, line_specs)
    grads = {key: {metric: [] for metric in ("flux", "fwhm", "velocity")} for key in metric_keys}
    for j, name in enumerate(free_names):
        param = getattr(model, name)
        value = float(param.value)
        step = max(abs(value) * 1e-4, 1e-5)
        low, high = param.bounds
        if low is not None:
            step = min(step, max((value - float(low)) * 0.5, 1e-6))
        if high is not None:
            step = min(step, max((float(high) - value) * 0.5, 1e-6))
        plus = copy.deepcopy(model)
        minus = copy.deepcopy(model)
        setattr(plus, name, value + step)
        setattr(minus, name, value - step)
        set_tied_values(plus)
        set_tied_values(minus)
        m_plus = compute_metrics(plus, line_specs)
        m_minus = compute_metrics(minus, line_specs)
        for key in metric_keys:
            for metric in ("flux", "fwhm", "velocity"):
                vp = m_plus.get(key, {}).get(metric, np.nan)
                vm = m_minus.get(key, {}).get(metric, np.nan)
                if not (np.isfinite(vp) and np.isfinite(vm)):
                    grads[key][metric].append(0.0)
                else:
                    grads[key][metric].append((vp - vm) / (2.0 * step))
    errors = {}
    for key in metric_keys:
        errors[key] = {}
        for metric in ("flux", "fwhm", "velocity"):
            g = np.asarray(grads[key][metric], dtype=float)
            if not np.all(np.isfinite(g)):
                errors[key][metric] = float("nan")
                continue
            var = float(g @ cov @ g)
            errors[key][metric] = float(math.sqrt(var)) if var >= 0 else float("nan")
    return errors


def make_lsq_fitter(cfg):
    name = str(cfg.get("fitter", {}).get("name", "trf")).lower()
    if name in ("trf", "least_squares"):
        return fitting.TRFLSQFitter()
    if name in ("levmar", "lm"):
        return fitting.LevMarLSQFitter()
    if name in ("dogbox",):
        return fitting.DogBoxLSQFitter()
    raise ValueError(f"unknown fitter: {name}")


def fit_lsq(model, x, y, err, cfg):
    fitter = make_lsq_fitter(cfg)
    kwargs = {"maxiter": int(cfg.get("fitter", {}).get("maxiter", 5000))}
    # astropy's TRF wrapper does not expose scipy's robust loss; keep the
    # config key for documentation but do not pass it through.
    t0 = time.perf_counter()
    fitted = fitter(model, x, y, weights=1.0 / err, **kwargs)
    elapsed = time.perf_counter() - t0
    set_tied_values(fitted)
    info = getattr(fitter, "fit_info", {}) or {}
    # Use unweighted residuals; fit_quality applies the same sigma vector that
    # was passed to the fitter.  astropy's fit_info['fun'] is fitter-internal
    # and is not guaranteed to be unweighted.
    residuals = np.asarray(y - fitted(x), dtype=float)
    return fitted, info, elapsed, residuals


def fit_quality(y, residuals, err_raw, err_eff, n_free):
    chi2_raw = float(np.sum(np.square(residuals / err_raw)))
    chi2_eff = float(np.sum(np.square(residuals / err_eff)))
    dof = int(len(y) - n_free)
    return {
        "chi2_raw": chi2_raw,
        "chi2_floor": chi2_eff,
        "dof": dof,
        "chi2nu_raw": chi2_raw / dof if dof > 0 else float("nan"),
        "chi2nu_floor": chi2_eff / dof if dof > 0 else float("nan"),
        "rms_1e17": float(np.std(residuals)),
        "rms_over_median_error": float(np.std(residuals) / np.median(err_raw)),
        "n_free": int(n_free),
        "n_pixels": int(len(y)),
    }


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------
def run_mcmc(model, x, y, err, cfg, line_specs, seed):
    mcfg = cfg.get("mcmc", {})
    nwalkers = int(mcfg.get("nwalkers", 48))
    nsteps = int(mcfg.get("nsteps", 4000))
    nburn = int(mcfg.get("nburn", 1500))
    ndim = len(galspec.get_free_params(model))
    nwalkers = max(nwalkers, 2 * ndim + 2)
    # MCMC_Fit creates its own emcee EnsembleSampler without an rstate; seed
    # numpy's global generator so repeated runs with the same --seed match.
    np.random.seed(int(seed))
    mcmc = galspec.MCMC_Fit(
        model,
        x,
        y,
        err,
        nwalkers=nwalkers,
        nsteps=nsteps,
        nburn=nburn,
        initial_frac=float(mcfg.get("initial_jitter_frac", 0.03)),
    )
    rng = np.random.default_rng(int(seed))
    theta0 = np.asarray(mcmc.theta_initial, dtype=float)
    low = np.asarray(
        [
            getattr(mcmc.model, name).bounds[0]
            if getattr(mcmc.model, name).bounds[0] is not None
            else theta0[i] - 1.0
            for i, name in enumerate(mcmc.param_names)
        ],
        dtype=float,
    )
    high = np.asarray(
        [
            getattr(mcmc.model, name).bounds[1]
            if getattr(mcmc.model, name).bounds[1] is not None
            else theta0[i] + 1.0
            for i, name in enumerate(mcmc.param_names)
        ],
        dtype=float,
    )
    span = high - low
    scale = float(mcfg.get("initial_jitter_frac", 0.03)) * span
    scale = np.maximum(scale, 1e-8)
    pos = theta0 + scale * rng.standard_normal((nwalkers, ndim))
    pos = np.clip(pos, low + 1e-8 * span, high - 1e-8 * span)
    mcmc.pos = pos

    t0 = time.perf_counter()
    mcmc.fit(progress=bool(mcfg.get("progress", False)))
    elapsed = time.perf_counter() - t0

    flat = np.asarray(mcmc.flat_samples, dtype=float)
    log_prob = np.asarray(mcmc.log_prob, dtype=float)
    if flat.size == 0:
        raise RuntimeError("emcee returned an empty chain")
    best_index = int(np.argmax(log_prob))
    theta_map = flat[best_index].copy()
    mcmc.set_model_params(theta_map)

    acceptance = float(np.mean(mcmc.sampler.acceptance_fraction))
    tau = None
    tau_max = None
    tau_status = "not_estimated"
    try:
        tau = np.asarray(mcmc.sampler.get_autocorr_time(tol=0), dtype=float)
        tau_max = float(np.nanmax(tau))
        tau_status = "ok"
    except Exception as exc:  # emcee.autocorr.AutocorrError
        tau_status = f"{type(exc).__name__}: {exc}"

    n_derived = min(int(mcfg.get("max_samples_for_derived", 2000)), len(flat))
    indices = np.linspace(0, len(flat) - 1, n_derived, dtype=int)
    arrays = {}
    for i in indices:
        mcmc.set_model_params(flat[i])
        metrics = compute_metrics(mcmc.model, line_specs)
        for key, values in metrics.items():
            for metric in ("flux", "fwhm", "velocity", "peak_wave"):
                arrays.setdefault(f"{key}|{metric}", []).append(values.get(metric, np.nan))
    mcmc.set_model_params(theta_map)
    posterior = {key: np.asarray(values, dtype=float) for key, values in arrays.items()}

    saved_n = min(int(cfg.get("output", {}).get("max_mcmc_samples_saved", 2000)), len(flat))
    saved_idx = np.linspace(0, len(flat) - 1, saved_n, dtype=int)
    return {
        "method": "emcee_mcmc",
        "mcmc": mcmc,
        "theta_map": theta_map,
        "flat_samples_saved": flat[saved_idx],
        "log_prob_saved": log_prob[saved_idx],
        "param_names": list(mcmc.param_names),
        "posterior": posterior,
        "acceptance_fraction": acceptance,
        "autocorr_tau": tau,
        "tau_max": tau_max,
        "tau_status": tau_status,
        "nsteps": nsteps,
        "nburn": nburn,
        "nwalkers": nwalkers,
        "ndim": ndim,
        "n_samples_discarded": int(len(flat)),
        "n_samples_derived": n_derived,
        "runtime_sec": elapsed,
        "model_after_map": mcmc.model,
    }


def run_nested(model, x, y, err, cfg, line_specs, seed):
    ncfg = cfg.get("nested", {})
    fitter = galspec.Dynesty_Fit(
        model,
        x,
        y,
        err,
        nlive=int(ncfg.get("nlive", 200)),
        sample_method=str(ncfg.get("sample_method", "rwalk")),
        bound=str(ncfg.get("bound", "multi")),
        n_processes=int(ncfg.get("n_processes", 1)),
        rstate=np.random.default_rng(int(seed)),
    )
    t0 = time.perf_counter()
    samples, _, param_names = fitter.fit(progress=False, dlogz=float(ncfg.get("dlogz", 0.5)))
    elapsed = time.perf_counter() - t0
    samples = np.asarray(samples, dtype=float)
    if samples.size == 0:
        raise RuntimeError("dynesty returned no equally weighted samples")
    fitter.get_best_fit()
    theta_map = np.asarray(fitter.theta_best, dtype=float)
    fitter.set_model_params(theta_map)
    n_derived = min(int(cfg.get("mcmc", {}).get("max_samples_for_derived", 2000)), len(samples))
    indices = np.linspace(0, len(samples) - 1, n_derived, dtype=int)
    arrays = {}
    for i in indices:
        fitter.set_model_params(samples[i])
        metrics = compute_metrics(fitter.model, line_specs)
        for key, values in metrics.items():
            for metric in ("flux", "fwhm", "velocity", "peak_wave"):
                arrays.setdefault(f"{key}|{metric}", []).append(values.get(metric, np.nan))
    fitter.set_model_params(theta_map)
    posterior = {key: np.asarray(values, dtype=float) for key, values in arrays.items()}
    saved_n = min(int(cfg.get("output", {}).get("max_mcmc_samples_saved", 2000)), len(samples))
    saved_idx = np.linspace(0, len(samples) - 1, saved_n, dtype=int)
    return {
        "method": "dynesty_nested",
        "mcmc": None,
        "fitter": fitter,
        "theta_map": theta_map,
        "flat_samples_saved": samples[saved_idx],
        "log_prob_saved": None,
        "param_names": list(param_names),
        "posterior": posterior,
        "acceptance_fraction": None,
        "autocorr_tau": None,
        "tau_max": None,
        "tau_status": "not_applicable",
        "nsteps": None,
        "nburn": None,
        "nwalkers": None,
        "ndim": len(param_names),
        "n_samples_discarded": int(len(samples)),
        "n_samples_derived": n_derived,
        "runtime_sec": elapsed,
        "log_evidence": float(fitter.log_evidence),
        "log_evidence_err": float(fitter.log_evidence_err),
        "ncall": int(fitter.ncall),
        "model_after_map": fitter.model,
    }


def posterior_summary(samples):
    samples = np.asarray(samples, dtype=float)
    finite = samples[np.isfinite(samples)]
    if finite.size == 0:
        return {"median": float("nan"), "p16": float("nan"), "p84": float("nan"), "err": float("nan")}
    p16, p50, p84 = np.percentile(finite, [16, 50, 84])
    return {
        "median": float(p50),
        "p16": float(p16),
        "p84": float(p84),
        "err": float(0.5 * (p84 - p16)),
    }


# ---------------------------------------------------------------------------
# Line table
# ---------------------------------------------------------------------------
def instrument_fwhm_kms(spectrum, wavec, cfg):
    inst_cfg = cfg.get("instrument", {})
    if inst_cfg.get("resolution_source") == "wresl" and spectrum.get("wresl_obs") is not None:
        wresl = np.asarray(spectrum["wresl_obs"], dtype=float)
        z = spectrum["z"]
        wave_grid = spectrum["wave_rest_air"]
        # WRESL is an observed-frame FWHM in Angstrom.  Convert to rest-frame
        # Angstrom at the line, then to km/s.
        wresl_rest = wresl / (1.0 + z)
        value = float(np.interp(wavec, wave_grid, wresl_rest))
        return max(value / wavec * LS_KM, 0.0)
    return float(inst_cfg.get("default_fwhm_kms", 0.0))


def intrinsic_fwhm(fwhm, inst, cfg):
    if not cfg.get("instrument", {}).get("subtract_from_fwhm", True):
        return fwhm
    if not np.isfinite(fwhm) or not np.isfinite(inst) or inst <= 0:
        return fwhm
    value = fwhm * fwhm - inst * inst
    return float(math.sqrt(value)) if value > 0 else 0.0


def make_line_row(
    line,
    component,
    wavec,
    flux,
    flux_err,
    fwhm,
    fwhm_err,
    velocity,
    velocity_err,
    snr_min,
    status,
    method,
    window,
    notes,
    inst_fwhm=0.0,
    cfg=None,
):
    flux = float(flux) if np.isfinite(flux) else float("nan")
    flux_err = float(flux_err) if np.isfinite(flux_err) else float("nan")
    snr = flux / flux_err if np.isfinite(flux) and np.isfinite(flux_err) and flux_err > 0 else float("nan")
    detected = bool(np.isfinite(snr) and snr >= snr_min and flux > 0)
    if status == "ok" and not detected:
        status = "weak" if np.isfinite(snr) and snr > 1 else "not_detected"
    return {
        "line": line,
        "component": component,
        "lambda_rest": float(wavec),
        "flux": flux * FLUX_UNIT_1E17,
        "flux_err": flux_err * FLUX_UNIT_1E17,
        "flux_1e17": flux,
        "flux_err_1e17": flux_err,
        "fwhm_kms": float(fwhm) if np.isfinite(fwhm) else float("nan"),
        "fwhm_err_kms": float(fwhm_err) if np.isfinite(fwhm_err) else float("nan"),
        "fwhm_intrinsic_kms": intrinsic_fwhm(fwhm, inst_fwhm, cfg or {}),
        "velocity_kms": float(velocity) if np.isfinite(velocity) else float("nan"),
        "velocity_err_kms": float(velocity_err) if np.isfinite(velocity_err) else float("nan"),
        "snr": float(snr) if np.isfinite(snr) else float("nan"),
        "detected": detected,
        "status": status,
        "method": method,
        "window_A": f"{float(window[0]):.1f}-{float(window[1]):.1f}",
        "notes": notes,
    }


def rows_from_sampling(sampling, line_specs, spectrum, cfg, snr_min, method_label):
    posterior = sampling["posterior"]
    rows = []
    for spec in line_specs:
        wavec = spec["wave"]
        inst = instrument_fwhm_kms(spectrum, wavec, cfg)
        labels = spec["component_labels"]
        components = spec["components"]
        for label, full_name in zip(labels, components):
            key = f"{spec['name']}|{label}"
            f = posterior_summary(posterior.get(f"{key}|flux", []))
            w = posterior_summary(posterior.get(f"{key}|fwhm", []))
            v = posterior_summary(posterior.get(f"{key}|velocity", []))
            rows.append(
                make_line_row(
                    spec["name"],
                    label,
                    wavec,
                    f["median"],
                    f["err"],
                    w["median"],
                    w["err"],
                    v["median"],
                    v["err"],
                    snr_min,
                    "ok",
                    method_label,
                    spec["profile_window"],
                    f"GalSpec {method_label}; Gaussian velocity width; air rest wavelength",
                    inst,
                    cfg,
                )
            )
        if spec.get("total", True):
            key = f"{spec['name']}|total"
            f = posterior_summary(posterior.get(f"{key}|flux", []))
            w = posterior_summary(posterior.get(f"{key}|fwhm", []))
            v = posterior_summary(posterior.get(f"{key}|velocity", []))
            rows.append(
                make_line_row(
                    spec["name"],
                    "total",
                    wavec,
                    f["median"],
                    f["err"],
                    w["median"],
                    w["err"],
                    v["median"],
                    v["err"],
                    snr_min,
                    "ok",
                    method_label,
                    spec["profile_window"],
                    "sum of all components; FWHM/velocity measured from the summed profile; air rest wavelength",
                    inst,
                    cfg,
                )
            )
    return rows


def rows_from_lsq(model, line_specs, metrics, errors, spectrum, cfg, snr_min, method_label, notes_prefix):
    rows = []
    for spec in line_specs:
        wavec = spec["wave"]
        inst = instrument_fwhm_kms(spectrum, wavec, cfg)
        for label, full_name in zip(spec["component_labels"], spec["components"]):
            key = f"{spec['name']}|{label}"
            m = metrics.get(key, {})
            e = errors.get(key, {})
            rows.append(
                make_line_row(
                    spec["name"],
                    label,
                    wavec,
                    m.get("flux", np.nan),
                    e.get("flux", np.nan),
                    m.get("fwhm", np.nan),
                    e.get("fwhm", np.nan),
                    m.get("velocity", np.nan),
                    e.get("velocity", np.nan),
                    snr_min,
                    "ok",
                    method_label,
                    spec["profile_window"],
                    notes_prefix,
                    inst,
                    cfg,
                )
            )
        if spec.get("total", True):
            key = f"{spec['name']}|total"
            m = metrics.get(key, {})
            e = errors.get(key, {})
            rows.append(
                make_line_row(
                    spec["name"],
                    "total",
                    wavec,
                    m.get("flux", np.nan),
                    e.get("flux", np.nan),
                    m.get("fwhm", np.nan),
                    e.get("fwhm", np.nan),
                    m.get("velocity", np.nan),
                    e.get("velocity", np.nan),
                    snr_min,
                    "ok",
                    method_label,
                    spec["profile_window"],
                    "sum of all components; FWHM/velocity measured from the summed profile",
                    inst,
                    cfg,
                )
            )
    return rows


# ---------------------------------------------------------------------------
# Cross-tool comparison
# ---------------------------------------------------------------------------
def _read_csv_rows(path: Path):
    if not path.exists():
        return None
    try:
        import pandas as pd

        return pd.read_csv(path)
    except Exception as exc:
        LOG.warning("could not read %s: %s", path, exc)
        return None


def _num(value):
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _reference_runtime(tool_dir: Path):
    run_json = tool_dir / "run.json"
    if not run_json.exists():
        return None
    try:
        data = json.loads(run_json.read_text())
    except Exception:
        return None
    for key in ("total_runtime_seconds", "runtime_seconds"):
        value = _num(data.get(key))
        if value is not None:
            return value
    runtime = data.get("runtime")
    if isinstance(runtime, dict):
        for key in ("total_sec", "original_fit_sec", "wall_sec"):
            value = _num(runtime.get(key))
            if value is not None:
                return value
    return None


def build_comparison(outdir: Path, rows, cfg, reference_root: Path | None = None):
    """Compare our H-beta/[O III] 5007 fluxes with the sibling tool outputs."""
    parent = Path(reference_root) if reference_root is not None else outdir.parent
    ours = {}
    for row in rows:
        if row["line"] in ("Hbeta", "OIII_5007") and row["component"] in ("narrow", "wing", "broad", "total"):
            component = row["component"]
            if row["line"] == "OIII_5007" and component == "wing":
                component = "broad"  # cross-tool alias for the [O III] wing
            ours[(row["line"], component)] = _num(row["flux_1e17"])
    comparisons = []

    def add(line, component, tool, ref_component, ref_flux, note):
        ref_flux = _num(ref_flux)
        gs = ours.get((line, component))
        ratio = None
        if gs is not None and ref_flux not in (None, 0.0):
            ratio = gs / ref_flux
        comparisons.append(
            {
                "line": line,
                "component": component,
                "galspec_flux_1e17": gs,
                "reference_tool": tool,
                "reference_component": ref_component,
                "reference_flux_1e17": ref_flux,
                "ratio_galspec_over_reference": ratio,
                "reference_runtime_sec": _reference_runtime(parent / tool),
                "note": note,
            }
        )

    # PyQSOFit (pyqsofit_uv)
    pyq_dir = parent / "pyqsofit_uv"
    pyq = _read_csv_rows(pyq_dir / "pyqsofit_lines.csv")
    if pyq is not None:
        def pyq_val(line, comp):
            m = (pyq["line"] == line) & (pyq["component"] == comp)
            if not m.any():
                return None
            return _num(pyq.loc[m, "area_1e17"].iloc[0])

        hb_br = pyq_val("Hb_br", "broad")
        hb_na = pyq_val("Hb_na", "narrow")
        o3_br = pyq_val("OIII5007w", "broad")
        o3_na = pyq_val("OIII5007c", "narrow")
        if hb_br is not None and hb_na is not None:
            add("Hbeta", "total", "pyqsofit_uv", "Hb_br+Hb_na", hb_br + hb_na, "sum of PyQSOFit broad+narrow H-beta areas")
        if hb_na is not None:
            add("Hbeta", "narrow", "pyqsofit_uv", "Hb_na", hb_na, "PyQSOFit narrow H-beta")
        if hb_br is not None:
            add("Hbeta", "broad", "pyqsofit_uv", "Hb_br", hb_br, "PyQSOFit broad H-beta")
        if o3_br is not None and o3_na is not None:
            add("OIII_5007", "total", "pyqsofit_uv", "OIII5007c+OIII5007w", o3_br + o3_na, "sum of PyQSOFit core+wing [O III] 5007")
        if o3_na is not None:
            add("OIII_5007", "narrow", "pyqsofit_uv", "OIII5007c", o3_na, "PyQSOFit core [O III] 5007")
        if o3_br is not None:
            add("OIII_5007", "broad", "pyqsofit_uv", "OIII5007w", o3_br, "PyQSOFit wing [O III] 5007")

    # GANDALF
    gand_dir = parent / "gandalf_line"
    gand = _read_csv_rows(gand_dir / "gandalf_lines.csv")
    if gand is not None:
        def gand_val(line, comp):
            m = (gand["line"] == line) & (gand["component"] == comp)
            if not m.any():
                return None
            return _num(gand.loc[m, "flux_1e17"].iloc[0])

        add("Hbeta", "total", "gandalf_line", "Hbeta total", gand_val("Hbeta", "total"), "GANDALF total H-beta")
        add("Hbeta", "narrow", "gandalf_line", "Hbeta narrow", gand_val("Hbeta", "narrow"), "GANDALF narrow H-beta")
        add("Hbeta", "broad", "gandalf_line", "Hbeta broad", gand_val("Hbeta", "broad"), "GANDALF broad H-beta")
        add("OIII_5007", "narrow", "gandalf_line", "[OIII]5007 narrow", gand_val("[OIII]5007", "narrow"), "GANDALF only reports the narrow [O III] 5007 component")
        add("OIII_5007", "total", "gandalf_line", "[OIII]5007 narrow", gand_val("[OIII]5007", "narrow"), "GANDALF has no broad [O III] 5007 component")

    # S3Fit
    s3_dir = parent / "s3fit_line"
    s3 = _read_csv_rows(s3_dir / "s3fit_lines.csv")
    if s3 is not None:
        def s3_val(line, comp):
            m = (s3["line"] == line) & (s3["component"] == comp)
            if not m.any():
                return None
            return _num(s3.loc[m, "flux_1e17"].iloc[0])

        add("Hbeta", "total", "s3fit_line", "total H-beta", s3_val("H-beta", "total"), "S3Fit total H-beta")
        add("Hbeta", "narrow", "s3fit_line", "NLR H-beta", s3_val("H-beta", "NLR"), "S3Fit NLR H-beta")
        add("Hbeta", "broad", "s3fit_line", "BLR H-beta", s3_val("H-beta", "BLR"), "S3Fit BLR H-beta")
        add("OIII_5007", "total", "s3fit_line", "total [O III] 5008", s3_val("[O III]:5008", "total"), "S3Fit total [O III] 5008")
        add("OIII_5007", "narrow", "s3fit_line", "NLR [O III] 5008", s3_val("[O III]:5008", "NLR"), "S3Fit NLR [O III] 5008")
    return comparisons


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
def plot_fit(outdir: Path, spectrum, main_model, main_specs, main_cont_side, aux_results, cfg):
    x = spectrum["wave_rest_air"]
    y = spectrum["flux_1e17"]
    err = spectrum["err_1e17"]
    z = spectrum["z"]
    feii_name = "FeII" if "FeII" in main_model.submodel_names else None

    fig = plt.figure(figsize=(15, 13))
    gs = fig.add_gridspec(5, 1, height_ratios=[1.1, 1.2, 0.55, 1.15, 1.15], hspace=0.55)
    ax0 = fig.add_subplot(gs[0])
    ax1 = fig.add_subplot(gs[1])
    ax2 = fig.add_subplot(gs[2], sharex=ax1)
    ax3 = fig.add_subplot(gs[3])
    ax4 = fig.add_subplot(gs[4])

    # full spectrum
    ax0.plot(x, y, color="0.15", lw=0.6, label="SDSS data")
    mask_main = (x >= cfg["main_window"]["rest"][0]) & (x <= cfg["main_window"]["rest"][1])
    ax0.plot(x[mask_main], main_model(x[mask_main]), color="C3", lw=1.2, label="GalSpec main-window model")
    for aux in aux_results:
        spec = aux.get("spectrum_slice")
        if spec is None or aux.get("model") is None:
            continue
        ax0.plot(spec["x"], aux["model"](spec["x"]), color="C0", lw=1.0)
    for lo, hi in [cfg["main_window"]["rest"]] + [a["rest"] for a in cfg.get("aux_windows", [])]:
        ax0.axvspan(lo, hi, color="C1", alpha=0.12)
    ax0.set_xlim(max(0, np.nanmin(x) - 20), np.nanmax(x) + 20)
    ax0.set_ylabel(r"$F_\lambda$ (10$^{-17}$ erg s$^{-1}$ cm$^{-2}$ $\AA^{-1}$)")
    ax0.set_title(f"GalSpec reduced line fit  z={z:.5f}  (rest-frame air wavelengths)")
    ax0.legend(loc="upper right", fontsize=8)
    ax0.grid(alpha=0.25)

    # main window
    main_mask = mask_main
    xm = x[main_mask]
    ym = y[main_mask]
    em = err[main_mask]
    model_m = main_model(xm)
    ax1.plot(xm, ym, "k.", ms=3, label="data")
    ax1.plot(xm, model_m, "r-", lw=1.4, label="total model")
    cont = main_model["continuum"](xm)
    pseudo = cont.copy()
    if feii_name:
        feii = main_model[feii_name](xm)
        pseudo += feii
        ax1.plot(xm, feii, "b--", lw=0.9, alpha=0.8, label="Fe II template")
    ax1.plot(xm, pseudo, "b:", lw=1.2, label="continuum + Fe II")
    colors = ["C2", "C4", "C5", "C6"]
    for i, spec in enumerate(main_specs):
        if not spec.get("total", True):
            continue
        prof = np.zeros_like(xm)
        for name in spec["components"]:
            prof += main_model[name](xm)
        ax1.plot(xm, prof, color=colors[i % len(colors)], lw=1.0, label=f"{spec['name']} (total)")
    ax1.set_ylabel(r"$F_\lambda$ (10$^{-17}$)")
    ax1.legend(loc="upper right", fontsize=7, ncol=3)
    ax1.grid(alpha=0.25)
    ax1.set_title("H-beta + [O III] 4959,5007 window")

    residual = (ym - model_m) / np.maximum(em, 1e-9)
    ax2.plot(xm, residual, "k.", ms=3)
    ax2.axhline(0, color="r", lw=0.8)
    ax2.axhline(3, color="0.6", lw=0.7, ls="--")
    ax2.axhline(-3, color="0.6", lw=0.7, ls="--")
    ax2.set_ylabel("resid / $\\sigma$")
    ax2.set_xlabel(r"rest wavelength (air, $\AA$)")
    ax2.grid(alpha=0.25)

    # component zooms
    for ax, target in [(ax3, "Hbeta"), (ax4, "OIII_5007")]:
        spec = next((s for s in main_specs if s["name"] == target), None)
        if spec is None:
            continue
        lo, hi = spec["profile_window"]
        mm = (x >= lo) & (x <= hi)
        ax.plot(x[mm], y[mm], "k.", ms=3, label="data")
        ax.plot(x[mm], main_model(x[mm]), "r-", lw=1.3, label="total model")
        ax.plot(x[mm], pseudo[mm] if np.array_equal(xm, x[mm]) else (main_model["continuum"](x[mm]) + (main_model[feii_name](x[mm]) if feii_name else 0.0)), "b:", lw=1.0, label="pseudo-continuum")
        for j, (label, name) in enumerate(zip(spec["component_labels"], spec["components"])):
            ax.plot(x[mm], main_model[name](x[mm]), color=colors[j % len(colors)], lw=1.1, label=f"{label} component")
        ax.set_title(f"{target} decomposition")
        ax.set_ylabel(r"$F_\lambda$ (10$^{-17}$)")
        ax.set_xlabel(r"rest wavelength (air, $\AA$)")
        ax.legend(fontsize=7, loc="upper right")
        ax.grid(alpha=0.25)

    fig.subplots_adjust(top=0.94, bottom=0.06, left=0.07, right=0.98, hspace=0.55)
    fig.suptitle("GalSpec: Astropy line models + Fe II template + emcee posterior", y=0.995, fontsize=13)
    fig.savefig(outdir / "galspec_fit.png", dpi=int(cfg.get("output", {}).get("dpi", 150)), bbox_inches="tight")
    if cfg.get("output", {}).get("save_pdf", True):
        fig.savefig(outdir / "galspec_fit.pdf", bbox_inches="tight")
    plt.close(fig)


def _param_index(sampling, submodel, parameter):
    mcmc = sampling.get("mcmc")
    if mcmc is not None:
        key = f"{submodel}.{parameter}"
        if key in mcmc.param_map:
            return int(mcmc.param_map[key][0])
    names = sampling["param_names"]
    for i, name in enumerate(names):
        if name.startswith(parameter) and str(i) in name:
            pass
    # Fallback: match the astropy free-parameter order through the model.
    model = sampling.get("model_after_map")
    if model is not None:
        try:
            free = galspec.get_free_params(model)
            return free.index(f"{parameter}_{list(model.submodel_names).index(submodel)}")
        except Exception:
            return None
    return None


def plot_uncertainty(outdir: Path, sampling, rows, cfg, spectrum, main_specs):
    posterior = sampling["posterior"]
    fig, axes = plt.subplots(2, 1, figsize=(13, 10), gridspec_kw={"height_ratios": [1.0, 1.0]})

    # Trace of the physically interesting parameters.
    ax = axes[0]
    if sampling.get("mcmc") is not None:
        chain = sampling["mcmc"].sampler.get_chain()
        selected = []
        for sub, par in [
            ("Hbeta_narrow", "amplitude"),
            ("Hbeta_broad", "amplitude"),
            ("OIII_5007_narrow", "amplitude"),
            ("OIII_5007_wing", "amplitude"),
            ("Hbeta_narrow", "sigma"),
            ("Hbeta_broad", "sigma"),
        ]:
            idx = _param_index(sampling, sub, par)
            if idx is not None and idx not in [s[0] for s in selected]:
                selected.append((idx, f"{sub}.{par}"))
        for idx, label in selected:
            ax.plot(chain[:, :, idx], color=None, alpha=0.18, lw=0.4)
            ax.plot(np.median(chain[:, :, idx], axis=1), color="k", lw=1.0, label=label)
        ax.set_xlabel("step")
        ax.set_ylabel("parameter")
        ax.set_title("emcee trace (thin lines: walkers; black: median)")
        ax.legend(fontsize=7, ncol=2, loc="upper right")
    else:
        ax.text(0.5, 0.5, "trace unavailable for nested sampling", ha="center", va="center")
        ax.set_axis_off()
    ax.grid(alpha=0.25)

    # Posterior line-flux distributions.
    ax = axes[1]
    plot_items = [
        ("Hbeta|narrow|flux", "H-beta narrow", "C0"),
        ("Hbeta|broad|flux", "H-beta broad", "C1"),
        ("Hbeta|total|flux", "H-beta total", "C3"),
        ("OIII_5007|narrow|flux", "O III 5007 narrow", "C2"),
        ("OIII_5007|wing|flux", "O III 5007 wing", "C4"),
        ("OIII_5007|total|flux", "O III 5007 total", "C5"),
    ]
    for key, label, color in plot_items:
        values = posterior.get(key)
        if values is None or not np.any(np.isfinite(values)):
            continue
        values = values[np.isfinite(values)] * FLUX_UNIT_1E17
        ax.hist(values, bins=40, histtype="step", lw=1.3, color=color, label=f"{label}: {np.median(values):.3g}")
    ax.set_xlabel(r"line flux (erg s$^{-1}$ cm$^{-2}$)")
    ax.set_ylabel("posterior samples")
    ax.set_title("Posterior line fluxes (16th/50th/84th percentiles in table)")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(outdir / "galspec_uncertainty.png", dpi=int(cfg.get("output", {}).get("dpi", 150)), bbox_inches="tight")
    if cfg.get("output", {}).get("save_pdf", True):
        fig.savefig(outdir / "galspec_uncertainty.pdf", bbox_inches="tight")
    plt.close(fig)

    # Corner plot of selected physical parameters.
    if corner is None or sampling.get("flat_samples_saved") is None:
        return
    samples = np.asarray(sampling["flat_samples_saved"], dtype=float)
    if samples.ndim != 2 or samples.shape[0] < 10:
        return
    selected = []
    for sub, par in [
        ("Hbeta_narrow", "amplitude"),
        ("Hbeta_broad", "amplitude"),
        ("Hbeta_narrow", "sigma"),
        ("Hbeta_broad", "sigma"),
        ("OIII_5007_narrow", "amplitude"),
        ("OIII_5007_narrow", "sigma"),
        ("OIII_5007_wing", "amplitude"),
        ("OIII_5007_wing", "sigma"),
    ]:
        idx = _param_index(sampling, sub, par)
        if idx is not None and idx < samples.shape[1]:
            selected.append((idx, f"{sub}.{par}"))
    if len(selected) < 2:
        return
    cols = [s[0] for s in selected]
    truths = np.asarray(sampling["theta_map"], dtype=float)[cols]
    fig = corner.corner(
        samples[:, cols],
        labels=[s[1] for s in selected],
        truths=truths,
        quantiles=[0.16, 0.5, 0.84],
        show_titles=True,
        title_fmt=".3g",
    )
    fig.suptitle("GalSpec emcee posterior (selected parameters)", y=0.995)
    fig.savefig(outdir / "galspec_corner.png", dpi=int(cfg.get("output", {}).get("dpi", 150)), bbox_inches="tight")
    if cfg.get("output", {}).get("save_pdf", True):
        fig.savefig(outdir / "galspec_corner.pdf", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------
def run(args):
    started = time.perf_counter()
    config_path = Path(args.config)
    if config_path.is_dir():
        config_path = config_path / "config.json"
    cfg = json.loads(config_path.read_text())

    # CLI overrides
    if args.sampler:
        if args.sampler == "lsq":
            cfg.setdefault("mcmc", {})["enabled"] = False
        elif args.sampler == "mcmc":
            cfg.setdefault("mcmc", {})["enabled"] = True
        elif args.sampler == "nested":
            cfg.setdefault("nested", {})["enabled"] = True
            cfg.setdefault("mcmc", {})["enabled"] = False
    if args.mcmc_steps is not None:
        cfg.setdefault("mcmc", {})["nsteps"] = int(args.mcmc_steps)
        if args.mcmc_steps > 1000:
            cfg["mcmc"]["nburn"] = min(int(cfg["mcmc"].get("nburn", 1500)), int(0.4 * args.mcmc_steps))
    if args.nwalkers is not None:
        cfg.setdefault("mcmc", {})["nwalkers"] = int(args.nwalkers)
    if args.nburn is not None:
        cfg.setdefault("mcmc", {})["nburn"] = int(args.nburn)
    if args.seed is not None:
        cfg.setdefault("mcmc", {})["seed"] = int(args.seed)
        cfg.setdefault("nested", {})["seed"] = int(args.seed)

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    log_handler = logging.FileHandler(outdir / "galspec.log", mode="w")
    log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOG.addHandler(log_handler)
    LOG.setLevel(logging.INFO)
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in LOG.handlers):
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        LOG.addHandler(stream)

    LOG.info("GalSpec version %s; input=%s; config=%s", galspec.__version__, args.input, config_path)
    if str(cfg.get("model_mode", "reduced")).lower() == "full":
        from galspec_full import run_full

        return run_full(args, cfg, config_path)
    input_path = find_input(Path(args.input))
    LOG.info("spectrum: %s", input_path)

    read_start = time.perf_counter()
    spectrum = read_spectrum(input_path, args.z, cfg)
    read_sec = time.perf_counter() - read_start
    x = spectrum["wave_rest_air"]
    y = spectrum["flux_1e17"]
    err = spectrum["err_1e17"]
    LOG.info(
        "z=%.8f  rest=%.2f-%.2f A  n=%d  median S/N=%.1f",
        spectrum["z"],
        spectrum["wave_rest_min"],
        spectrum["wave_rest_max"],
        len(x),
        float(np.nanmedian(y / np.maximum(err, 1e-12))),
    )

    main_lo, main_hi = [float(v) for v in cfg["main_window"]["rest"]]
    main_mask = (x >= main_lo) & (x <= main_hi) & np.isfinite(y) & (err > 0)
    if main_mask.sum() < 30:
        raise ValueError(
            f"main window {main_lo}-{main_hi} A has only {int(main_mask.sum())} usable pixels; "
            f"spectrum covers {spectrum['wave_rest_min']:.1f}-{spectrum['wave_rest_max']:.1f} A"
        )
    xm = x[main_mask]
    ym = y[main_mask]
    em = err[main_mask]

    main_model, xm, ym, main_cont_side, main_specs = build_main_model(cfg, xm, ym)
    em_eff = effective_errors(em, main_cont_side, cfg)
    LOG.info(
        "main model: %d pixels, %d free parameters, floor median=%.4f",
        len(xm),
        len(galspec.get_free_params(main_model)),
        float(np.median(em_eff - em)),
    )

    lsq_model, lsq_info, lsq_sec, lsq_residuals = fit_lsq(main_model, xm, ym, em_eff, cfg)
    n_free = len(galspec.get_free_params(lsq_model))
    main_quality = fit_quality(ym, lsq_residuals, em, em_eff, n_free)
    main_quality["lsq_success"] = bool(lsq_info.get("success", True))
    main_quality["lsq_message"] = str(lsq_info.get("message", ""))
    LOG.info(
        "LSQ: success=%s chi2nu(raw)=%.3f chi2nu(floor)=%.3f rms=%.3f (%.2f s)",
        main_quality["lsq_success"],
        main_quality["chi2nu_raw"],
        main_quality["chi2nu_floor"],
        main_quality["rms_1e17"],
        lsq_sec,
    )

    # Main-window sampling.
    if cfg.get("nested", {}).get("enabled", False):
        sampling = run_nested(lsq_model, xm, ym, em_eff, cfg, main_specs, cfg["nested"].get("seed", 42))
        method_label = "dynesty_nested"
    elif cfg.get("mcmc", {}).get("enabled", True):
        sampling = run_mcmc(lsq_model, xm, ym, em_eff, cfg, main_specs, cfg["mcmc"].get("seed", 42))
        method_label = "emcee_mcmc"
    else:
        metrics = compute_metrics(lsq_model, main_specs)
        cov = lsq_info.get("param_cov")
        free_names = galspec.get_free_params(lsq_model)
        errors = covariance_errors(lsq_model, free_names, cov, main_specs, list(metrics.keys()))
        sampling = {
            "method": "lsq_covariance",
            "mcmc": None,
            "theta_map": np.asarray([getattr(lsq_model, n).value for n in free_names]),
            "flat_samples_saved": None,
            "log_prob_saved": None,
            "param_names": free_names,
            "posterior": None,
            "acceptance_fraction": None,
            "autocorr_tau": None,
            "tau_max": None,
            "tau_status": "not_applicable",
            "nsteps": None,
            "nburn": None,
            "nwalkers": None,
            "ndim": len(free_names),
            "n_samples_discarded": 0,
            "n_samples_derived": 0,
            "runtime_sec": 0.0,
            "model_after_map": lsq_model,
            "_metrics": metrics,
            "_errors": errors,
        }
        method_label = "lsq_covariance"

    if sampling["method"] == "lsq_covariance":
        rows = rows_from_lsq(
            lsq_model,
            main_specs,
            sampling["_metrics"],
            sampling["_errors"],
            spectrum,
            cfg,
            float(cfg.get("detection", {}).get("snr_min", 3.0)),
            method_label,
            "LSQ covariance error; reduced window model",
        )
    else:
        rows = rows_from_sampling(
            sampling,
            main_specs,
            spectrum,
            cfg,
            float(cfg.get("detection", {}).get("snr_min", 3.0)),
            method_label,
        )
    LOG.info("main-window sampling: %s, %.1f s", sampling["method"], sampling["runtime_sec"])

    # Auxiliary windows.
    aux_sec = 0.0
    aux_records = []
    aux_rows = []
    aux_plot = []
    for aux_cfg in cfg.get("aux_windows", []):
        lo, hi = [float(v) for v in aux_cfg["rest"]]
        mask = (x >= lo) & (x <= hi) & np.isfinite(y) & (err > 0)
        if mask.sum() < 30:
            LOG.warning("aux window %s has only %d pixels; skipped", aux_cfg["name"], int(mask.sum()))
            aux_records.append({"name": aux_cfg["name"], "status": "not_covered", "n_pixels": int(mask.sum())})
            continue
        xa, ya, ea = x[mask], y[mask], err[mask]
        aux_model, xa, ya, aux_cont, aux_specs = build_aux_model(aux_cfg, xa, ya)
        ea_eff = effective_errors(ea, aux_cont, cfg)
        t0 = time.perf_counter()
        aux_fit, aux_info, aux_fit_sec, aux_res = fit_lsq(aux_model, xa, ya, ea_eff, cfg)
        aux_sec += time.perf_counter() - t0
        aux_nfree = len(galspec.get_free_params(aux_fit))
        aux_quality = fit_quality(ya, aux_res, ea, ea_eff, aux_nfree)
        metrics = compute_metrics(aux_fit, aux_specs)
        cov = aux_info.get("param_cov")
        free_names = galspec.get_free_params(aux_fit)
        errors = covariance_errors(aux_fit, free_names, cov, aux_specs, list(metrics.keys()))
        aux_rows.extend(
            rows_from_lsq(
                aux_fit,
                aux_specs,
                metrics,
                errors,
                spectrum,
                cfg,
                float(cfg.get("detection", {}).get("snr_min", 3.0)),
                "lsq_covariance",
                f"auxiliary window {aux_cfg['name']}; single Gaussian per line; linear continuum",
            )
        )
        aux_records.append(
            {
                "name": aux_cfg["name"],
                "status": "ok",
                "rest": [lo, hi],
                "n_pixels": int(mask.sum()),
                "n_free": int(aux_nfree),
                "fit_sec": float(aux_fit_sec),
                "quality": aux_quality,
                "free_parameters": [
                    {
                        "name": name,
                        "value": float(getattr(aux_fit, name).value),
                    }
                    for name in free_names
                ],
            }
        )
        aux_plot.append(
            {
                "name": aux_cfg["name"],
                "rest": [lo, hi],
                "model": aux_fit,
                "spectrum_slice": {"x": xa, "y": ya, "err": ea},
                "quality": aux_quality,
            }
        )
        LOG.info(
            "aux %s: chi2nu(floor)=%.2f rms=%.2f (%.2f s)",
            aux_cfg["name"],
            aux_quality["chi2nu_floor"],
            aux_quality["rms_1e17"],
            aux_fit_sec,
        )

    # Explicit coverage rows for the H-alpha/[N II]/[S II] region.
    coverage_rows = []
    for line in cfg.get("coverage_lines", []):
        wave = float(line["wave"])
        covered = spectrum["wave_rest_min"] <= wave <= spectrum["wave_rest_max"]
        status = "not_covered" if not covered else "not_fitted"
        coverage_rows.append(
            make_line_row(
                str(line["name"]),
                str(line.get("component", "narrow")),
                wave,
                float("nan"),
                float("nan"),
                float("nan"),
                float("nan"),
                float("nan"),
                float("nan"),
                float(cfg.get("detection", {}).get("snr_min", 3.0)),
                status,
                "none",
                [wave - 10.0, wave + 10.0],
                (
                    "outside the rest-frame coverage of this spectrum"
                    if not covered
                    else "covered but not included in the reduced model"
                ),
                0.0,
                cfg,
            )
        )

    all_rows = rows + aux_rows + coverage_rows

    reference_root = Path(args.reference_dir) if args.reference_dir else outdir.parent
    comparison = build_comparison(outdir, all_rows, cfg, reference_root)

    # Outputs.
    write_start = time.perf_counter()
    import pandas as pd

    lines_path = outdir / "galspec_lines.csv"
    pd.DataFrame(all_rows).to_csv(lines_path, index=False)
    if comparison:
        pd.DataFrame(comparison).to_csv(outdir / "galspec_comparison.csv", index=False)

    effective_config = copy.deepcopy(cfg)
    effective_config["_effective"] = {
        "input_path": str(input_path),
        "output_path": str(outdir),
        "object": args.object,
        "config_path": str(config_path),
        "sampler": sampling["method"],
        "z": spectrum["z"],
    }
    write_json(outdir / "config.effective.json", effective_config)

    # Model CSV over the main window.
    model_m = sampling["model_after_map"](xm) if sampling["method"] != "lsq_covariance" else lsq_model(xm)
    feii_name = "FeII" if "FeII" in sampling["model_after_map"].submodel_names else None
    cont = sampling["model_after_map"]["continuum"](xm)
    pseudo = cont.copy()
    if feii_name:
        pseudo += sampling["model_after_map"][feii_name](xm)
    model_table = {
        "wave_rest_air": xm,
        "flux_1e17": ym,
        "err_1e17": em,
        "model_1e17": model_m,
        "continuum_1e17": cont,
        "feii_1e17": sampling["model_after_map"][feii_name](xm) if feii_name else np.zeros_like(xm),
        "pseudo_continuum_1e17": pseudo,
        "residual_1e17": ym - model_m,
        "residual_over_err": (ym - model_m) / np.maximum(em, 1e-12),
    }
    for spec in main_specs:
        prof = np.zeros_like(xm)
        for name in spec["components"]:
            prof += sampling["model_after_map"][name](xm)
        model_table[f"line_{spec['name']}_1e17"] = prof
    pd.DataFrame(model_table).to_csv(outdir / "galspec_model.csv", index=False)

    # MCMC samples.
    if sampling.get("flat_samples_saved") is not None:
        payload = {
            "samples": np.asarray(sampling["flat_samples_saved"], dtype=np.float32),
            "log_prob": (
                np.asarray(sampling["log_prob_saved"], dtype=np.float32)
                if sampling.get("log_prob_saved") is not None
                else np.array([], dtype=np.float32)
            ),
            "param_names": np.asarray(sampling["param_names"], dtype="U64"),
            "theta_map": np.asarray(sampling["theta_map"], dtype=np.float32),
            "sampler": np.asarray([sampling["method"]], dtype="U32"),
        }
        for key, values in sampling["posterior"].items():
            safe = key.replace("|", "__")
            payload[f"posterior__{safe}"] = np.asarray(values, dtype=np.float32)
        np.savez_compressed(outdir / "galspec_mcmc.npz", **payload)

    # Figures.
    plot_start = time.perf_counter()
    plot_fit(outdir, spectrum, sampling["model_after_map"], main_specs, main_cont_side, aux_plot, cfg)
    if sampling.get("posterior") is not None:
        plot_uncertainty(outdir, sampling, all_rows, cfg, spectrum, main_specs)
    plot_sec = time.perf_counter() - plot_start
    write_sec = time.perf_counter() - write_start - plot_sec

    # Free-parameter table.
    free_names = galspec.get_free_params(sampling["model_after_map"])
    cov = lsq_info.get("param_cov")
    param_rows = []
    for i, name in enumerate(free_names):
        param = getattr(sampling["model_after_map"], name)
        err_value = None
        if cov is not None and np.asarray(cov).ndim == 2 and i < np.asarray(cov).shape[0]:
            v = float(np.asarray(cov)[i, i])
            err_value = math.sqrt(v) if v >= 0 else None
        param_rows.append(
            {
                "name": name,
                "lsq_value": float(getattr(lsq_model, name).value),
                "map_value": float(param.value),
                "map_lower": float(param.bounds[0]) if param.bounds[0] is not None else None,
                "map_upper": float(param.bounds[1]) if param.bounds[1] is not None else None,
                "lsq_cov_sigma": err_value,
            }
        )

    runtime = {
        "total_sec": float(time.perf_counter() - started),
        "read_sec": float(read_sec),
        "lsq_main_sec": float(lsq_sec),
        "sampling_main_sec": float(sampling["runtime_sec"]),
        "aux_sec": float(aux_sec),
        "plot_sec": float(plot_sec),
        "write_sec": float(write_sec),
    }
    limitations = [
        "Reduced-window model, not a full-spectrum continuum/host decomposition: linear local continuum + park2022 Fe II + H-beta/[O III] 4959,5007 components in 4720-5150 A rest frame.",
        "H-alpha 6563, [N II] 6548/6583 and [S II] 6716/6731 are outside the SDSS rest-frame coverage of this z=0.5874 QSO (rest ~2246-6509 A); they are reported as not_covered, not fitted.",
        "The H-beta narrow/broad and [O III] core/wing labels are empirical. Their flux split depends on the adopted Gaussian decomposition and is not directly interchangeable with other tools' narrow/broad definitions.",
        "Fe II is represented by GalSpec's park2022 empirical template; no Balmer pseudo-continuum, host galaxy or full QSO principal-component continuum is included.",
        "Line fluxes are integrated Gaussian areas from the GalSpec model, in rest-frame 1e-17 erg s-1 cm-2 A-1 times (1+z); the (1+z) factor matches PyQSOFit and GANDALF.",
        "Wavelengths are air rest-frame wavelengths. SDSS LOGLAM (vacuum) is converted with PyAstronomy vactoair2 before de-redshifting.",
        "Intrinsic FWHM subtracts the SDSS WRESL resolution in quadrature; the observed FWHM is also stored.",
        "Auxiliary [O II], [Ne III] and [S II] lines use a single Gaussian per line and linear covariance errors; they are not sampled with emcee.",
    ]
    if sampling["method"] == "emcee_mcmc":
        limitations.append(
            f"emcee chain: {sampling['nsteps']} steps, {sampling['nburn']} burn-in, {sampling['nwalkers']} walkers; "
            f"tau_status={sampling['tau_status']}. A short chain is a demonstration of the posterior machinery, not a fully converged production posterior."
        )
    if sampling["method"] == "dynesty_nested":
        limitations.append("dynesty nested sampling was used; evidence errors are reported in run.json.")
    if sampling["method"] == "lsq_covariance":
        limitations.append("LSQ covariance only; no MCMC/nested posterior was run.")

    galspec_commit = os.environ.get(
        "GALSPEC_COMMIT", "18e4effd796a1d51615ca2340bb927278eb18bbf"
    )
    run_json = {
        "tool": "galspec_line",
        "galspec_version": str(galspec.__version__),
        "galspec_upstream": {
            "repo": "https://github.com/jyshangguan/GalSpec",
            "commit": galspec_commit,
        },
        "image": os.environ.get("GALSPEC_IMAGE", "galspec_line"),
        "object": args.object,
        "input": {
            "path": spectrum["path"],
            "layout": spectrum["layout"],
            "z": spectrum["z"],
            "ebv": spectrum["ebv"],
            "n_pix_raw": spectrum["n_pix_raw"],
            "n_pix_used": spectrum["n_pix_used"],
            "rest_min_A": spectrum["wave_rest_min"],
            "rest_max_A": spectrum["wave_rest_max"],
            "flux_scale_input_to_1e17": spectrum["flux_scale_input_to_1e17"],
            "vacuum_to_air": True,
            "rest_frame_flux_correction": spectrum["rest_frame_flux_correction"],
            "deredden": spectrum["deredden"],
        },
        "frame": {
            "wavelength": "air rest-frame",
            "flux_internal": "1e-17 erg s-1 cm-2 A-1 (rest frame)",
            "flux_table": "both 1e-17 and cgs erg s-1 cm-2",
        },
        "model": {
            "scope": "reduced line-window fit",
            "main_window_A": [main_lo, main_hi],
            "continuum": cfg.get("continuum", {}).get("main_model", "linear"),
            "feii": cfg.get("continuum", {}).get("feii", {}),
            "lines": [
                {
                    "name": s["name"],
                    "wave_A": s["wave"],
                    "components": s["component_labels"],
                    "tie_to": s.get("tie_to"),
                }
                for s in main_specs
            ],
            "aux_windows": cfg.get("aux_windows", []),
            "fitter": cfg.get("fitter", {}),
            "error_floor": cfg.get("errors", {}),
        },
        "fit": {
            "main": main_quality,
            "lsq_free_parameters": param_rows,
            "aux": aux_records,
        },
        "sampling": {
            "method": sampling["method"],
            "nsteps": sampling.get("nsteps"),
            "nburn": sampling.get("nburn"),
            "nwalkers": sampling.get("nwalkers"),
            "ndim": sampling.get("ndim"),
            "acceptance_fraction": sampling.get("acceptance_fraction"),
            "tau_max": sampling.get("tau_max"),
            "tau_status": sampling.get("tau_status"),
            "nsteps_over_tau_max": (
                float(sampling["nsteps"] / sampling["tau_max"])
                if sampling.get("nsteps") and sampling.get("tau_max")
                else None
            ),
            "n_samples_discarded": sampling.get("n_samples_discarded"),
            "n_samples_derived": sampling.get("n_samples_derived"),
            "log_evidence": sampling.get("log_evidence"),
            "log_evidence_err": sampling.get("log_evidence_err"),
            "ncall": sampling.get("ncall"),
        },
        "mcmc": {
            "saved_samples": (
                int(np.asarray(sampling["flat_samples_saved"]).shape[0])
                if sampling.get("flat_samples_saved") is not None
                else 0
            ),
            "saved_parameters": sampling.get("param_names"),
            "theta_map": np.asarray(sampling.get("theta_map", [])).tolist(),
            "file": "galspec_mcmc.npz" if sampling.get("flat_samples_saved") is not None else None,
        },
        "line_measurements": all_rows,
        "comparison": comparison,
        "runtime": runtime,
        "reference_runtimes": {
            "pyqsofit_uv": _reference_runtime(reference_root / "pyqsofit_uv"),
            "gandalf_line": _reference_runtime(reference_root / "gandalf_line"),
            "s3fit_line": _reference_runtime(reference_root / "s3fit_line"),
        },
        "limitations": limitations,
        "files": sorted([p.name for p in outdir.iterdir() if p.is_file()] + ["run.json"]),
    }
    write_json(outdir / "run.json", run_json)

    LOG.info("wrote %s", outdir)
    LOG.info(
        "H-beta total=%.2f  1e-17; [O III] 5007 total=%.2f  1e-17",
        next((r["flux_1e17"] for r in all_rows if r["line"] == "Hbeta" and r["component"] == "total"), float("nan")),
        next((r["flux_1e17"] for r in all_rows if r["line"] == "OIII_5007" and r["component"] == "total"), float("nan")),
    )
    LOG.info("total runtime %.1f s", runtime["total_sec"])
    return 0


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True, help="input directory or FITS spectrum")
    p.add_argument("--output", required=True, help="output directory")
    p.add_argument("--config", default="/app/config", help="config directory or JSON file")
    p.add_argument("--object", default=None, help="object/source key for provenance")
    p.add_argument("--reference-dir", default=None,
                   help="directory containing sibling pyqsofit_uv/gandalf_line/s3fit_line outputs")
    p.add_argument("--z", type=float, default=None, help="override systemic redshift")
    p.add_argument("--sampler", choices=("mcmc", "nested", "lsq"), default=None,
                   help="override config sampling mode")
    p.add_argument("--mcmc-steps", type=int, default=None, help="override emcee steps")
    p.add_argument("--nwalkers", type=int, default=None, help="override emcee walkers")
    p.add_argument("--nburn", type=int, default=None, help="override emcee burn-in")
    p.add_argument("--seed", type=int, default=None, help="override random seed")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        return run(args)
    except Exception as exc:  # noqa: BLE001
        LOG.error("GalSpec fit failed: %s", exc)
        LOG.error("%s", traceback.format_exc())
        outdir = Path(args.output)
        outdir.mkdir(parents=True, exist_ok=True)
        write_json(
            outdir / "run_error.json",
            {
                "tool": "galspec_line",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "input": args.input,
                "config": args.config,
            },
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
