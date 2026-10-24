#!/usr/bin/env python3
"""Full-continuum + emission-line GalSpec model.

This module is the production path for ``model_mode = "full"``.  It fits the
entire usable rest-frame SDSS spectrum with one global model:

* a normalised polynomial continuum (default degree 4 over 2280-6460 A);
* GalSpec's park2022 Fe II template (4000-5600 A);
* narrow forbidden and Balmer lines sharing one NLR kinematic component;
* a separate [O III] core kinematic component (the NLR core is often
  blueshifted relative to the Balmer lines);
* a broad Balmer component (H-beta, H-gamma, H-delta);
* broad Mg II 2796/2804;
* [O III] 5007/4959 core + broad wing and [O III] 4363;
* [O II] 3726/3729, [Ne III] 3869/3967, [Ne V] 3426, He II 4686,
  [S II] 4068/4076, [O I] 6300/6363 and [S III] 6312;
* the available Balmer series H-beta through H12 (higher orders tied to
  H-epsilon by Case-B ratios), plus H-alpha/N II/S II coverage rows when the
  spectrum does not reach them.

The global model is fitted with a trust-region least-squares start and then
sampled with ``galspec.MCMC_Fit`` (emcee).  Every saved posterior sample is a
sample of the *same* full model; this is not a reduced line-window fit.
"""
from __future__ import annotations

import copy
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402
import numpy as np  # noqa: E402
from astropy.modeling import models  # noqa: E402

try:
    import corner
except Exception:  # pragma: no cover
    corner = None

import galspec  # noqa: E402
import run_galspec as gr  # noqa: E402

LOG = gr.LOG
LS_KM = gr.LS_KM
FWHM_PER_SIGMA = gr.FWHM_PER_SIGMA
FLUX_UNIT_1E17 = gr.FLUX_UNIT_1E17


# ---------------------------------------------------------------------------
# Continuum
# ---------------------------------------------------------------------------
class NormalizedPolynomial1D(models.Polynomial1D):
    """Polynomial in ``(wave - x0) / xscale`` (well conditioned for spectra)."""

    def __init__(self, degree, x0=4350.0, xscale=1200.0, **kwargs):
        self.x0 = float(x0)
        self.xscale = float(xscale)
        super().__init__(degree=int(degree), **kwargs)

    def evaluate(self, x, *coeffs):
        xn = (np.asarray(x, dtype=float) - self.x0) / self.xscale
        return np.polynomial.polynomial.polyval(xn, coeffs)


def polynomial_degree(cfg):
    return int(cfg.get("continuum", {}).get("polynomial_degree", 4))


def continuum_param_names(degree):
    # The continuum is the first submodel in both the continuum-only and the
    # full compound model, so its free names are c0_0 ... cN_0.
    return [f"c{i}_0" for i in range(degree + 1)]


def build_continuum_model(cfg, x, y):
    degree = polynomial_degree(cfg)
    x0 = float(cfg.get("continuum", {}).get("polynomial_x0", 4350.0))
    xscale = float(cfg.get("continuum", {}).get("polynomial_xscale", 1200.0))
    xn = (np.asarray(x, dtype=float) - x0) / xscale
    coeffs = np.polyfit(xn, np.asarray(y, dtype=float), degree)[::-1]
    kwargs = {f"c{i}": float(coeffs[i]) for i in range(degree + 1)}
    model = NormalizedPolynomial1D(
        degree=degree, x0=x0, xscale=xscale, name="continuum", **kwargs
    )
    fe_cfg = cfg.get("continuum", {}).get("feii", {})
    if fe_cfg.get("enabled", False):
        model = model + galspec.IronTemplate_new(
            amplitude=float(fe_cfg.get("amplitude0", 10.0)),
            sigma=float(fe_cfg.get("sigma0", 1500.0)),
            dv=float(fe_cfg.get("dv0", 0.0)),
            z=0.0,
            template_name=str(fe_cfg.get("template", "park2022")),
            name="FeII",
            fixed={"z": True},
            bounds={
                "amplitude": tuple(fe_cfg.get("amplitude_bounds", [0.0, 120.0])),
                "sigma": tuple(fe_cfg.get("sigma_bounds", [500.0, 5000.0])),
                "dv": tuple(fe_cfg.get("dv_bounds", [-2000.0, 2000.0])),
            },
        )
    gr.set_tied_values(model)
    return model


def apply_continuum_values(full_model, fitted):
    """Copy continuum and Fe II parameter values from a fitted sub-model."""
    for sub in ("continuum", "FeII"):
        if sub not in fitted.submodel_names or sub not in full_model.submodel_names:
            continue
        fit_idx = list(fitted.submodel_names).index(sub)
        full_idx = list(full_model.submodel_names).index(sub)
        for pname in fitted[sub].param_names:
            source = f"{pname}_{fit_idx}"
            target = f"{pname}_{full_idx}"
            if hasattr(fitted, source) and hasattr(full_model, target):
                setattr(full_model, target, getattr(fitted, source).value)
    gr.set_tied_values(full_model)


def set_continuum_bounds(model, degree):
    """Broad polynomial bounds around the current (LSQ) solution."""
    for i, name in enumerate(continuum_param_names(degree)):
        if not hasattr(model, name):
            continue
        value = float(getattr(model, name).value)
        if i == 0:
            if value > 0:
                low, high = max(1.0, 0.35 * value), 2.5 * value
            else:
                low, high = -500.0, 500.0
        else:
            width = max(50.0, 0.75 * abs(value))
            low, high = value - width, value + width
        getattr(model, name).bounds = (low, high)


# ---------------------------------------------------------------------------
# Full model
# ---------------------------------------------------------------------------
def line_free_mask(x, line_specs):
    mask = np.ones_like(x, dtype=bool)
    for spec in line_specs:
        lo, hi = [float(v) for v in spec["profile_window"]]
        mask &= ~((x >= lo - 10.0) & (x <= hi + 10.0))
    return mask


def build_full_model(cfg, x, y, continuum_model=None):
    """Build the global continuum + Fe II + line model."""
    degree = polynomial_degree(cfg)
    x0 = float(cfg.get("continuum", {}).get("polynomial_x0", 4350.0))
    xscale = float(cfg.get("continuum", {}).get("polynomial_xscale", 1200.0))
    if continuum_model is None:
        continuum_model = build_continuum_model(cfg, x, y)

    # Extract polynomial coefficients and build the full model's continuum.
    coeffs = []
    for i in range(degree + 1):
        name = f"c{i}_0"
        if hasattr(continuum_model, name):
            coeffs.append(float(getattr(continuum_model, name).value))
        else:
            coeffs.append(0.0)
    model = NormalizedPolynomial1D(
        degree=degree,
        x0=x0,
        xscale=xscale,
        name="continuum",
        **{f"c{i}": coeffs[i] for i in range(degree + 1)},
    )

    line_specs = []
    kin_refs = {}
    created = {}
    for line in cfg["lines"]:
        line_name = str(line["name"])
        wavec = float(line["wave"])
        comp_names = []
        labels = []
        for comp in line.get("components", []):
            label = str(comp["label"])
            full_name = gr.line_component_name(line_name, label)
            kind = str(comp.get("kind", "narrow"))
            if kind not in cfg["kinematics"]:
                raise ValueError(f"line {line_name}: unknown kinematic group {kind}")
            kin = cfg["kinematics"][kind]
            amp_bounds = tuple(comp.get("amplitude_bounds", [0.0, 300.0]))
            if kind in kin_refs:
                ref_name = kin_refs[kind]
                component = galspec.Line_Gaussian(
                    amplitude=1.0,
                    dv=float(kin.get("dv0", 0.0)),
                    sigma=float(kin.get("sigma0", 300.0)),
                    wavec=wavec,
                    name=full_name,
                    bounds={
                        "amplitude": amp_bounds,
                        "sigma": tuple(kin.get("sigma_bounds", [80.0, 6000.0])),
                        "dv": tuple(kin.get("dv_bounds", [-2000.0, 2000.0])),
                    },
                )
                component.sigma.tied = gr.TieSigma(ref_name)
                component.dv.tied = gr.TieDV(ref_name)
            else:
                ref_name = full_name
                component = galspec.Line_Gaussian(
                    amplitude=max(float(comp.get("amp0", 1.0)), 0.05),
                    dv=float(kin.get("dv0", 0.0)),
                    sigma=float(kin.get("sigma0", 300.0)),
                    wavec=wavec,
                    name=full_name,
                    bounds={
                        "amplitude": amp_bounds,
                        "sigma": tuple(kin.get("sigma_bounds", [80.0, 6000.0])),
                        "dv": tuple(kin.get("dv_bounds", [-2000.0, 2000.0])),
                    },
                )
                kin_refs[kind] = full_name
            tie_amp = comp.get("tie_amplitude_to")
            if tie_amp:
                if str(tie_amp) not in created:
                    raise ValueError(
                        f"line {line_name}: amplitude tie reference {tie_amp} "
                        "must appear earlier in the line list"
                    )
                component.amplitude.tied = gr.TieAmplitudeRatio(
                    str(tie_amp), float(comp.get("amplitude_ratio", 1.0))
                )
            model = model + component
            created[full_name] = component
            comp_names.append(full_name)
            labels.append(label)
        line_specs.append(
            {
                "name": line_name,
                "wave": wavec,
                "components": comp_names,
                "component_labels": labels,
                "profile_window": [
                    float(v)
                    for v in line.get(
                        "profile_window", [wavec - 30.0, wavec + 30.0]
                    )
                ],
                "total": bool(line.get("total", True)),
                "kind": "full",
                "groups": [str(c.get("kind", "narrow")) for c in line.get("components", [])],
            }
        )
    fe_cfg = cfg.get("continuum", {}).get("feii", {})
    if fe_cfg.get("enabled", False):
        model = model + galspec.IronTemplate_new(
            amplitude=float(fe_cfg.get("amplitude0", 10.0)),
            sigma=float(fe_cfg.get("sigma0", 1500.0)),
            dv=float(fe_cfg.get("dv0", 0.0)),
            z=0.0,
            template_name=str(fe_cfg.get("template", "park2022")),
            name="FeII",
            fixed={"z": True},
            bounds={
                "amplitude": tuple(fe_cfg.get("amplitude_bounds", [0.0, 120.0])),
                "sigma": tuple(fe_cfg.get("sigma_bounds", [500.0, 5000.0])),
                "dv": tuple(fe_cfg.get("dv_bounds", [-2000.0, 2000.0])),
            },
        )
    gr.set_tied_values(model)
    return model, line_specs


# ---------------------------------------------------------------------------
# Least-squares start
# ---------------------------------------------------------------------------
def _fix_submodels(model, submodels, fixed):
    """Fix/release every non-tied parameter of the named submodels."""
    names = []
    for sub in submodels:
        if sub not in model.submodel_names:
            continue
        idx = list(model.submodel_names).index(sub)
        for pname in model[sub].param_names:
            compound = f"{pname}_{idx}"
            if not hasattr(model, compound):
                continue
            param = getattr(model, compound)
            if not param.tied and (not fixed or not param.fixed):
                param.fixed = bool(fixed)
                names.append(compound)
    return names


def fit_full_model(cfg, x, y, err, line_specs):
    """Continuum-only robust start followed by a full-model TRF fit."""
    degree = polynomial_degree(cfg)
    mask = line_free_mask(x, line_specs)
    if int(mask.sum()) < 100:
        mask = np.isfinite(y)
    cont_model = build_continuum_model(cfg, x[mask], y[mask])
    cont_fit, cont_info, cont_sec, _ = gr.fit_lsq(
        cont_model, x[mask], y[mask], err[mask], cfg
    )
    gr.set_tied_values(cont_fit)
    LOG.info(
        "continuum start: %d line-free pixels, %.2f s, chi2/nu=%.3f",
        int(mask.sum()),
        cont_sec,
        _chi2nu(y[mask], cont_fit(x[mask]), err[mask], len(cont_fit.param_names)),
    )

    full, _ = build_full_model(cfg, x, y, continuum_model=cont_fit)
    apply_continuum_values(full, cont_fit)
    # Fit the full model in two stages.  First hold the global continuum and
    # Fe II fixed and solve for the lines; this prevents the polynomial from
    # absorbing broad Mg II/Balmer wings.  Then release everything for a joint
    # refinement.  A failed LSQ start is not fatal: the MCMC can still start
    # from the continuum solution and the configured line guesses.
    full_fit = full
    full_info = {}
    full_sec = 0.0
    fixed_names = _fix_submodels(full, ("continuum", "FeII"), True)
    try:
        t0 = time.perf_counter()
        line_only, line_info, line_sec, _ = gr.fit_lsq(full, x, y, err, cfg)
        full_sec += line_sec
        gr.set_tied_values(line_only)
        if np.all(np.isfinite(line_only(x))):
            full_fit = line_only
            full_info = line_info
        LOG.info("line-only LSQ start (continuum fixed): %.2f s", line_sec)
    except Exception as exc:  # noqa: BLE001
        LOG.warning("line-only LSQ start failed (%s); continuing", exc)
        full_info = {"message": f"line-only LSQ failed: {type(exc).__name__}: {exc}"}
        full_sec = time.perf_counter() - t0
    for name in fixed_names:
        getattr(full_fit, name).fixed = False
    try:
        t0 = time.perf_counter()
        candidate, info, sec, _ = gr.fit_lsq(full_fit, x, y, err, cfg)
        full_sec += sec
        gr.set_tied_values(candidate)
        if np.all(np.isfinite(candidate(x))):
            full_fit = candidate
            full_info = info
        LOG.info("joint full LSQ start: %.2f s", sec)
    except Exception as exc:  # noqa: BLE001
        LOG.warning("joint full LSQ start failed (%s); keeping line-only solution", exc)
        full_info = {"message": f"joint full LSQ failed: {type(exc).__name__}: {exc}"}


    # Anchor the final model to the line-free continuum solution.  The joint
    # stage refines the lines with the continuum free; restoring continuum and
    # Fe II afterwards prevents broad lines from absorbing the continuum.
    apply_continuum_values(full_fit, cont_fit)
    set_continuum_bounds(full_fit, degree)
    gr.set_tied_values(full_fit)
    residuals = y - full_fit(x)
    n_free = len(galspec.get_free_params(full_fit))
    quality = gr.fit_quality(y, residuals, err, err, n_free)
    quality["lsq_success"] = bool(full_fit is not full)
    quality["lsq_message"] = str(full_info.get("message", ""))
    return full_fit, quality, cont_sec, full_sec, mask


def _chi2nu(y, model, err, n_free):
    dof = max(1, len(y) - n_free)
    return float(np.sum(((y - model) / np.maximum(err, 1e-12)) ** 2) / dof)


# ---------------------------------------------------------------------------
# Line metrics
# ---------------------------------------------------------------------------
def _gaussian_profile(grid, wavec, amplitude, sigma, dv):
    v = (np.asarray(grid, dtype=float) - wavec) / wavec * LS_KM
    return amplitude * np.exp(-0.5 * ((v - dv) / sigma) ** 2)


def line_metrics(model, spec):
    """Analytic component fluxes/widths and summed-profile totals."""
    wavec = float(spec["wave"])
    result = {}
    total_flux = 0.0
    components = []
    for label, name in zip(spec["component_labels"], spec["components"]):
        param = model[name]
        amp = float(param.amplitude.value)
        sigma = float(param.sigma.value)
        dv = float(param.dv.value)
        flux = gr.gaussian_flux(amp, sigma, wavec)
        result[label] = {
            "flux": flux,
            "fwhm": FWHM_PER_SIGMA * sigma,
            "velocity": dv,
            "peak_wave": wavec * (1.0 + dv / LS_KM),
            "amplitude": amp,
            "sigma": sigma,
        }
        total_flux += flux
        components.append((amp, sigma, dv))
    if spec.get("total", True) and components:
        max_sigma = max(c[1] for c in components)
        lo, hi = [float(v) for v in spec["profile_window"]]
        half = max((hi - lo) / 2.0, 5.0 * max_sigma * wavec / LS_KM)
        grid = np.linspace(wavec - half, wavec + half, 801)
        profile = np.zeros_like(grid)
        for amp, sigma, dv in components:
            profile += _gaussian_profile(grid, wavec, amp, sigma, dv)
        peak = float(np.max(profile))
        if peak > 0:
            above = np.where(profile >= 0.5 * peak)[0]
            fwhm_wave = grid[above[-1]] - grid[above[0]]
            fwhm = fwhm_wave / wavec * LS_KM
            imax = int(np.argmax(profile))
            velocity = (grid[imax] - wavec) / wavec * LS_KM
            peak_wave = float(grid[imax])
        else:
            fwhm, velocity, peak_wave = 0.0, 0.0, wavec
        result["total"] = {
            "flux": total_flux,
            "fwhm": fwhm,
            "velocity": velocity,
            "peak_wave": peak_wave,
            "amplitude": peak,
            "sigma": float("nan"),
        }
    return result


def metrics_for_specs(model, line_specs):
    out = {}
    for spec in line_specs:
        metrics = line_metrics(model, spec)
        for label, values in metrics.items():
            out[f"{spec['name']}|{label}"] = values
    return out


# ---------------------------------------------------------------------------
# MCMC
# ---------------------------------------------------------------------------
def run_full_mcmc(model, x, y, err, cfg, line_specs, seed):
    mcfg = cfg.get("mcmc", {})
    nwalkers = int(mcfg.get("nwalkers", 80))
    nsteps = int(mcfg.get("nsteps", 4000))
    nburn = int(mcfg.get("nburn", 1200))
    ndim = len(galspec.get_free_params(model))
    if ndim < 2:
        raise RuntimeError("full model has too few free parameters")
    nwalkers = max(nwalkers, 2 * ndim + 2)
    np.random.seed(int(seed))
    mcmc = galspec.MCMC_Fit(
        model,
        x,
        y,
        err,
        nwalkers=nwalkers,
        nsteps=nsteps,
        nburn=nburn,
        initial_frac=float(mcfg.get("initial_jitter_frac", 0.02)),
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
    scale = float(mcfg.get("initial_jitter_frac", 0.02)) * span
    scale = np.maximum(scale, 1e-8)
    pos = theta0 + scale * rng.standard_normal((nwalkers, ndim))
    pos = np.clip(pos, low + 1e-8 * span, high - 1e-8 * span)
    mcmc.pos = pos

    # Custom prior: the usual parameter bounds plus a positivity constraint on
    # the global continuum.  The continuum is the first submodel and its
    # coefficients are the first ndeg+1 free parameters.
    degree = polynomial_degree(cfg)
    cont_idx = [
        mcmc.param_map[f"continuum.{pname}"][0]
        for pname in [f"c{i}" for i in range(degree + 1)]
        if f"continuum.{pname}" in mcmc.param_map
    ]
    x0 = float(cfg.get("continuum", {}).get("polynomial_x0", 4350.0))
    xscale = float(cfg.get("continuum", {}).get("polynomial_xscale", 1200.0))
    xn_grid = (np.linspace(float(np.min(x)), float(np.max(x)), 256) - x0) / xscale

    def log_prior(theta):
        for i, name in enumerate(mcmc.param_names):
            lo, hi = getattr(mcmc.model, name).bounds
            if lo is not None and theta[i] < lo:
                return -np.inf
            if hi is not None and theta[i] > hi:
                return -np.inf
        if cont_idx:
            cont = np.polynomial.polynomial.polyval(
                xn_grid, np.asarray(theta, dtype=float)[cont_idx]
            )
            if not np.all(np.isfinite(cont)) or np.any(cont <= 0.0):
                return -np.inf
        return 0.0

    mcmc.log_prior_func = log_prior
    ncores = int(mcfg.get("ncores", 0) or 0)
    t0 = time.perf_counter()
    if ncores > 1:
        # emcee walkers are independent; GalSpec's fit_ncores wraps a
        # multiprocess pool.  step_initial=0 selects a single production phase.
        mcmc.step_initial = 0
        mcmc.fit_ncores(ncores=ncores)
        chain = np.asarray(mcmc.sampler.get_chain(discard=nburn), dtype=float)
        flat = chain.reshape(-1, ndim)
        log_prob = np.asarray(
            mcmc.sampler.get_log_prob(discard=nburn), dtype=float
        ).reshape(-1)
        mcmc.flat_samples = flat
        mcmc.log_prob = log_prob
    else:
        mcmc.fit(progress=bool(mcfg.get("progress", False)))
        flat = np.asarray(mcmc.flat_samples, dtype=float)
        log_prob = np.asarray(mcmc.log_prob, dtype=float)
        chain = np.asarray(mcmc.sampler.get_chain(discard=nburn), dtype=float)
    elapsed = time.perf_counter() - t0
    if flat.size == 0:
        raise RuntimeError("emcee returned an empty chain")
    theta_map = flat[int(np.argmax(log_prob))].copy()
    mcmc.set_model_params(theta_map)

    acceptance = float(np.mean(mcmc.sampler.acceptance_fraction))
    tau = None
    tau_max = None
    tau_status = "not_estimated"
    tol = float(mcfg.get("autocorr_tol", 0.0))
    for attempt_tol in (tol, 1.0, 5.0):
        try:
            tau = np.asarray(
                mcmc.sampler.get_autocorr_time(
                    discard=nburn, tol=attempt_tol, quiet=True
                ),
                dtype=float,
            )
            tau_max = float(np.nanmax(tau))
            tau_status = f"ok (tol={attempt_tol})"
            break
        except Exception as exc:  # noqa: BLE001
            tau_status = f"{type(exc).__name__}: {exc}"

    n_steps_kept = int(chain.shape[0]) if chain.ndim == 3 else int(nsteps - nburn)
    ess = (
        float(n_steps_kept * nwalkers / tau_max)
        if tau_max and np.isfinite(tau_max) and tau_max > 0
        else None
    )
    return {
        "method": "emcee_mcmc_full",
        "mcmc": mcmc,
        "chain": chain,
        "theta_map": theta_map,
        "flat_samples": flat,
        "log_prob": log_prob,
        "param_names": list(mcmc.param_names),
        "acceptance_fraction": acceptance,
        "autocorr_tau": tau,
        "tau_max": tau_max,
        "tau_status": tau_status,
        "nsteps": nsteps,
        "nburn": nburn,
        "nwalkers": nwalkers,
        "ndim": ndim,
        "n_samples_total": int(len(flat)),
        "n_steps_kept": n_steps_kept,
        "effective_sample_size": ess,
        "runtime_sec": elapsed,
        "model_after_map": mcmc.model,
    }


def derive_posterior(sampling, line_specs, n_samples):
    flat = sampling["flat_samples"]
    n_samples = min(int(n_samples), len(flat))
    indices = np.linspace(0, len(flat) - 1, n_samples, dtype=int)
    arrays = {}
    model = sampling["mcmc"].model
    for i in indices:
        sampling["mcmc"].set_model_params(flat[i])
        metrics = metrics_for_specs(model, line_specs)
        for key, values in metrics.items():
            for metric in ("flux", "fwhm", "velocity", "peak_wave", "amplitude", "sigma"):
                arrays.setdefault(f"{key}|{metric}", []).append(values.get(metric, np.nan))
    sampling["mcmc"].set_model_params(sampling["theta_map"])
    sampling["posterior"] = {
        key: np.asarray(values, dtype=float) for key, values in arrays.items()
    }
    sampling["n_samples_derived"] = int(n_samples)
    return sampling["posterior"]


# ---------------------------------------------------------------------------
# Rows
# ---------------------------------------------------------------------------
def rows_from_full_sampling(sampling, line_specs, spectrum, cfg, snr_min):
    posterior = sampling["posterior"]
    rows = []
    method = "emcee_mcmc_full"
    for spec in line_specs:
        wavec = float(spec["wave"])
        inst = gr.instrument_fwhm_kms(spectrum, wavec, cfg)
        for label in spec["component_labels"]:
            key = f"{spec['name']}|{label}"
            f = gr.posterior_summary(posterior.get(f"{key}|flux", []))
            w = gr.posterior_summary(posterior.get(f"{key}|fwhm", []))
            v = gr.posterior_summary(posterior.get(f"{key}|velocity", []))
            rows.append(
                gr.make_line_row(
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
                    method,
                    spec["profile_window"],
                    "full-continuum GalSpec model; Gaussian velocity width; air rest wavelength",
                    inst,
                    cfg,
                )
            )
        if spec.get("total", True):
            key = f"{spec['name']}|total"
            f = gr.posterior_summary(posterior.get(f"{key}|flux", []))
            w = gr.posterior_summary(posterior.get(f"{key}|fwhm", []))
            v = gr.posterior_summary(posterior.get(f"{key}|velocity", []))
            rows.append(
                gr.make_line_row(
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
                    method,
                    spec["profile_window"],
                    "sum of all components; FWHM/velocity measured from the summed profile; air rest wavelength",
                    inst,
                    cfg,
                )
            )
    return rows


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
def _plot_model_decomposition(ax, model, x, y, err, specs, lo, hi):
    mask = (x >= lo) & (x <= hi)
    xm, ym, em = x[mask], y[mask], err[mask]
    ax.plot(xm, ym, "k.", ms=2.5, label="data")
    ax.plot(xm, model(xm), "r-", lw=1.3, label="total model")
    pseudo = model["continuum"](xm)
    if "FeII" in model.submodel_names:
        pseudo = pseudo + model["FeII"](xm)
    ax.plot(xm, pseudo, "b:", lw=1.1, label="continuum + Fe II")
    colors = ["C2", "C4", "C5", "C6", "C7", "C8", "C9"]
    for i, spec in enumerate(specs):
        if not ((spec["wave"] >= lo - 20) and (spec["wave"] <= hi + 20)):
            continue
        if not spec.get("total", True):
            continue
        prof = np.zeros_like(xm)
        for name in spec["components"]:
            prof += model[name](xm)
        ax.plot(
            xm,
            prof,
            color=colors[i % len(colors)],
            lw=1.0,
            alpha=0.9,
            label=f"{spec['name']} (total)",
        )
    ax.set_xlim(lo, hi)
    ax.grid(alpha=0.25)
    ax.set_ylabel(r"$F_\lambda$ (10$^{-17}$)")
    if ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=7, loc="upper right", ncol=2)


def plot_full_fit(outdir: Path, spectrum, model, line_specs, cfg, quality):
    x = spectrum["wave_rest_air"]
    y = spectrum["flux_1e17"]
    err = spectrum["err_1e17"]
    z = spectrum["z"]
    fig = plt.figure(figsize=(16, 21))
    gs = GridSpec(
        8,
        1,
        figure=fig,
        height_ratios=[1.25, 0.55, 1.0, 1.0, 1.0, 1.05, 1.0, 1.0],
        hspace=0.55,
    )
    ax0 = fig.add_subplot(gs[0])
    ax0.plot(x, y, color="0.15", lw=0.55, label="SDSS data")
    ax0.plot(x, model(x), color="C3", lw=1.0, label="full GalSpec model")
    pseudo = model["continuum"](x)
    if "FeII" in model.submodel_names:
        pseudo = pseudo + model["FeII"](x)
    ax0.plot(x, pseudo, color="C0", lw=0.9, ls=":", label="continuum + Fe II")
    ax0.set_xlim(float(np.min(x)), float(np.max(x)))
    ax0.set_ylabel(r"$F_\lambda$ (10$^{-17}$ erg s$^{-1}$ cm$^{-2}$ $\AA^{-1}$)")
    ax0.set_title(
        f"GalSpec full-continuum + emission-line model  z={z:.5f}  "
        f"rest {x.min():.0f}-{x.max():.0f} A  "
        f"chi2/nu={quality['chi2nu_floor']:.2f}"
    )
    ax0.legend(loc="upper right", fontsize=8, ncol=3)
    ax0.grid(alpha=0.25)

    axr = fig.add_subplot(gs[1])
    resid = (y - model(x)) / np.maximum(err, 1e-9)
    axr.plot(x, resid, "k.", ms=2)
    axr.axhline(0, color="r", lw=0.8)
    axr.axhline(3, color="0.6", lw=0.7, ls="--")
    axr.axhline(-3, color="0.6", lw=0.7, ls="--")
    axr.set_xlim(float(np.min(x)), float(np.max(x)))
    axr.set_ylabel(r"resid / $\sigma$")
    axr.grid(alpha=0.25)

    zooms = [
        (2730.0, 2870.0, "Mg II 2796/2804"),
        (3690.0, 4170.0, "[O II] 3726/3729, [Ne III], Balmer series"),
        (4280.0, 4420.0, "H-gamma + [O III] 4363"),
        (4780.0, 5090.0, "H-beta + [O III] 4959/5007"),
        (6240.0, 6420.0, "[O I] 6300/6363 + [S III] 6312"),
    ]
    for spec_ax, (lo, hi, title) in zip(
        [fig.add_subplot(gs[i]) for i in range(2, 7)], zooms
    ):
        _plot_model_decomposition(spec_ax, model, x, y, err, line_specs, lo, hi)
        spec_ax.set_title(title)
    for spec_ax in [fig.add_subplot(gs[7])]:
        # H-gamma/H-delta detail with the narrow Balmer series
        _plot_model_decomposition(spec_ax, model, x, y, err, line_specs, 4050.0, 4160.0)
        spec_ax.set_title("H-delta + [S II] 4068/4076")
    fig.subplots_adjust(top=0.965, bottom=0.04, left=0.07, right=0.985, hspace=0.55)
    fig.suptitle(
        "GalSpec: global polynomial continuum + park2022 Fe II + full line model + emcee",
        y=0.995,
        fontsize=14,
    )
    fig.savefig(
        outdir / "galspec_fit.png",
        dpi=int(cfg.get("output", {}).get("dpi", 150)),
        bbox_inches="tight",
    )
    if cfg.get("output", {}).get("save_pdf", True):
        fig.savefig(outdir / "galspec_fit.pdf", bbox_inches="tight")
    plt.close(fig)


def _robust_scale(values):
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return 1.0
    mad = np.median(np.abs(finite - np.median(finite)))
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale <= 0:
        scale = float(np.std(finite))
    return max(float(scale), 1e-12)


def _param_index(sampling, full_name):
    mcmc = sampling.get("mcmc")
    if mcmc is not None and full_name in mcmc.param_map:
        return int(mcmc.param_map[full_name][0])
    return None


def plot_full_uncertainty(outdir: Path, sampling, cfg):
    chain = sampling.get("chain")
    saved = sampling.get("saved_samples")
    fig, axes = plt.subplots(
        2, 1, figsize=(14, 13), gridspec_kw={"height_ratios": [1.15, 1.0]}
    )
    ax = axes[0]
    selected = [
        ("Hbeta_narrow.amplitude", "H-beta narrow amp"),
        ("Hbeta_broad.amplitude", "H-beta broad amp"),
        ("OIII_5007_narrow.amplitude", "[O III] core amp"),
        ("OIII_5007_wing.amplitude", "[O III] wing amp"),
        ("Hbeta_broad.sigma", "H-beta broad sigma"),
        ("OIII_5007_narrow.sigma", "[O III] core sigma"),
        ("FeII.amplitude", "Fe II amp"),
        ("MgII_2796_broad.amplitude", "Mg II broad amp"),
    ]
    used = []
    for j, (full_name, label) in enumerate(selected):
        idx = _param_index(sampling, full_name)
        if idx is None:
            continue
        if chain is not None:
            vals = np.asarray(chain[:, :, idx], dtype=float)
            xvals = np.arange(vals.shape[0])
            ax.plot(xvals, (vals - np.median(vals)) / _robust_scale(vals) + 4.0 * j,
                    color="C0", alpha=0.10, lw=0.35)
            ax.plot(xvals, (np.median(vals, axis=1) - np.median(vals)) / _robust_scale(vals) + 4.0 * j,
                    color="k", lw=1.0)
        elif saved is not None and idx < saved.shape[1]:
            vals = np.asarray(saved[:, idx], dtype=float)
            xvals = np.arange(len(vals))
            ax.plot(xvals, (vals - np.median(vals)) / _robust_scale(vals) + 4.0 * j,
                    color="C0", alpha=0.8, lw=0.6)
        else:
            continue
        used.append((j, label))
    if used:
        ax.set_yticks([4.0 * j for j, _ in used])
        ax.set_yticklabels([label for _, label in used], fontsize=8)
        ax.set_xlabel(
            "step after burn-in" if chain is not None else "saved posterior sample (thinned)"
        )
        ax.set_ylabel("normalised trace + offset")
        ax.set_title(
            "emcee trace, normalised per parameter "
            "(blue: walkers/samples; black: median)"
        )
    else:
        ax.text(0.5, 0.5, "trace unavailable (LSQ debug or empty chain)", ha="center", va="center")
    ax.grid(alpha=0.25)

    ax = axes[1]
    items = [
        ("Hbeta|narrow|flux", "H-beta narrow", "C0"),
        ("Hbeta|broad|flux", "H-beta broad", "C1"),
        ("Hbeta|total|flux", "H-beta total", "C3"),
        ("OIII_5007|narrow|flux", "[O III] core", "C2"),
        ("OIII_5007|wing|flux", "[O III] wing", "C4"),
        ("OIII_5007|total|flux", "[O III] total", "C5"),
        ("MgII_2796|broad|flux", "Mg II broad", "C6"),
        ("OII_3726|narrow|flux", "[O II] 3726", "C7"),
        ("NeIII_3869|narrow|flux", "[Ne III] 3869", "C8"),
    ]
    for key, label, color in items:
        values = sampling["posterior"].get(key)
        if values is None or not np.any(np.isfinite(values)):
            continue
        values = values[np.isfinite(values)] * FLUX_UNIT_1E17
        ax.hist(
            values,
            bins=45,
            histtype="step",
            lw=1.3,
            color=color,
            label=f"{label}: {np.median(values):.3g}",
        )
    ax.set_xlabel(r"line flux (erg s$^{-1}$ cm$^{-2}$)")
    ax.set_ylabel("posterior samples")
    ax.set_title("Posterior line fluxes (16th/50th/84th percentiles in table)")
    ax.legend(fontsize=7, loc="upper right", ncol=2)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(
        outdir / "galspec_uncertainty.png",
        dpi=int(cfg.get("output", {}).get("dpi", 150)),
        bbox_inches="tight",
    )
    if cfg.get("output", {}).get("save_pdf", True):
        fig.savefig(outdir / "galspec_uncertainty.pdf", bbox_inches="tight")
    plt.close(fig)

    if corner is None:
        return
    saved = np.asarray(sampling.get("saved_samples", []), dtype=float)
    if saved.ndim != 2 or saved.shape[0] < 10:
        return
    corner_items = [
        ("Hbeta_narrow.amplitude", "Hbeta_n amp"),
        ("Hbeta_narrow.sigma", "Hbeta_n sigma"),
        ("Hbeta_broad.amplitude", "Hbeta_b amp"),
        ("Hbeta_broad.sigma", "Hbeta_b sigma"),
        ("OIII_5007_narrow.amplitude", "OIII_n amp"),
        ("OIII_5007_narrow.sigma", "OIII_n sigma"),
        ("OIII_5007_wing.amplitude", "OIII_w amp"),
        ("OIII_5007_wing.sigma", "OIII_w sigma"),
        ("FeII.amplitude", "FeII amp"),
        ("MgII_2796_broad.amplitude", "MgII_b amp"),
        ("continuum.c0", "cont c0"),
        ("continuum.c1", "cont c1"),
    ]
    cols, labels = [], []
    for full_name, label in corner_items:
        idx = _param_index(sampling, full_name)
        if idx is not None and idx < saved.shape[1]:
            cols.append(idx)
            labels.append(label)
    if len(cols) < 2:
        return
    truths = np.asarray(sampling["theta_map"], dtype=float)[cols]
    fig = corner.corner(
        saved[:, cols],
        labels=labels,
        truths=truths,
        quantiles=[0.16, 0.5, 0.84],
        show_titles=True,
        title_fmt=".3g",
    )
    fig.suptitle("GalSpec full-model emcee posterior (selected parameters)", y=0.995)
    fig.savefig(
        outdir / "galspec_corner.png",
        dpi=int(cfg.get("output", {}).get("dpi", 150)),
        bbox_inches="tight",
    )
    if cfg.get("output", {}).get("save_pdf", True):
        fig.savefig(outdir / "galspec_corner.pdf", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------
def _add_comparison_block(comparisons, ours, tool, rows, mapping, runtime):
    def val(line, comp):
        m = (rows["line"] == line) & (rows["component"] == comp)
        if not m.any():
            return None
        col = "flux_1e17" if "flux_1e17" in rows.columns else "area_1e17"
        return gr._num(rows.loc[m, col].iloc[0])

    for line, component, ref_line, ref_comp, note in mapping:
        ref_flux = val(ref_line, ref_comp)
        gs = ours.get((line, component))
        ratio = gs / ref_flux if gs is not None and ref_flux not in (None, 0.0) else None
        comparisons.append(
            {
                "line": line,
                "component": component,
                "galspec_flux_1e17": gs,
                "reference_tool": tool,
                "reference_component": ref_comp,
                "reference_flux_1e17": ref_flux,
                "ratio_galspec_over_reference": ratio,
                "reference_runtime_sec": runtime,
                "note": note,
            }
        )


def extended_comparison(outdir: Path, rows, cfg, reference_root: Path | None = None):
    comparisons = gr.build_comparison(outdir, rows, cfg, reference_root)
    parent = Path(reference_root) if reference_root is not None else outdir.parent
    ours = {}
    for row in rows:
        if row["line"] in ("Hbeta", "OIII_5007") and row["component"] in (
            "narrow",
            "wing",
            "broad",
            "total",
        ):
            comp = row["component"]
            if row["line"] == "OIII_5007" and comp == "wing":
                comp = "broad"
            ours[(row["line"], comp)] = gr._num(row["flux_1e17"])

    # PyQSOFitSpec (skew-normal, kapteyn least squares)
    p = parent / "pyqsofitspec_line" / "pyqsofitspec_lines.csv"
    rows_p = gr._read_csv_rows(p)
    if rows_p is not None:
        runtime = gr._reference_runtime(parent / "pyqsofitspec_line")
        mapping = [
            ("Hbeta", "narrow", "Hb_na", "narrow", "PyQSOFitSpec narrow H-beta"),
            ("Hbeta", "broad", "Hb_br", "broad", "PyQSOFitSpec broad H-beta"),
            ("OIII_5007", "narrow", "OIII5007c", "narrow", "PyQSOFitSpec [O III] 5007 core"),
            ("OIII_5007", "broad", "OIII5007w", "broad", "PyQSOFitSpec [O III] 5007 wing"),
        ]
        _add_comparison_block(comparisons, ours, "pyqsofitspec_line", rows_p, mapping, runtime)
        # Total PyQSOFitSpec H-beta is the sum of its broad and narrow rows.
        hb_b = None
        hb_n = None
        m = (rows_p["line"] == "Hb_br") & (rows_p["component"] == "broad")
        if m.any():
            hb_b = gr._num(rows_p.loc[m, "flux_1e17"].iloc[0])
        m = (rows_p["line"] == "Hb_na") & (rows_p["component"] == "narrow")
        if m.any():
            hb_n = gr._num(rows_p.loc[m, "flux_1e17"].iloc[0])
        if hb_b is not None and hb_n is not None:
            gs = ours.get(("Hbeta", "total"))
            comparisons.append(
                {
                    "line": "Hbeta",
                    "component": "total",
                    "galspec_flux_1e17": gs,
                    "reference_tool": "pyqsofitspec_line",
                    "reference_component": "Hb_br+Hb_na",
                    "reference_flux_1e17": hb_b + hb_n,
                    "ratio_galspec_over_reference": gs / (hb_b + hb_n),
                    "reference_runtime_sec": runtime,
                    "note": "sum of PyQSOFitSpec broad+narrow H-beta",
                }
            )

    # QGfit
    p = parent / "qgfit" / "qgfit_lines.csv"
    rows_q = gr._read_csv_rows(p)
    if rows_q is not None:
        runtime = gr._reference_runtime(parent / "qgfit")
        mapping = [
            ("Hbeta", "total", "Hbeta", "total", "QGfit total H-beta"),
            ("Hbeta", "narrow", "Hbeta", "narrow", "QGfit narrow H-beta"),
            ("Hbeta", "broad", "Hbeta", "broad", "QGfit broad H-beta"),
            ("OIII_5007", "total", "OIII5007", "total", "QGfit total [O III] 5007"),
            ("OIII_5007", "narrow", "OIII5007", "narrow", "QGfit narrow [O III] 5007"),
            ("OIII_5007", "total", "OIII5007", "narrow", "QGfit has one [O III] component; narrow flux used as total"),
        ]
        _add_comparison_block(comparisons, ours, "qgfit", rows_q, mapping, runtime)

    # SHEAP (optional extra)
    p = parent / "sheap_line" / "sheap_lines.csv"
    rows_s = gr._read_csv_rows(p)
    if rows_s is not None:
        runtime = gr._reference_runtime(parent / "sheap_line")
        mapping = [
            ("Hbeta", "total", "Hbeta", "total", "SHEAP total H-beta"),
            ("Hbeta", "narrow", "Hbeta", "narrow", "SHEAP narrow H-beta"),
            ("Hbeta", "broad", "Hbeta", "broad", "SHEAP broad H-beta"),
            ("OIII_5007", "total", "OIII5007", "total", "SHEAP total [O III] 5007"),
            ("OIII_5007", "narrow", "OIII5007", "total", "SHEAP only reports one [O III] component"),
        ]
        _add_comparison_block(comparisons, ours, "sheap_line", rows_s, mapping, runtime)
    return comparisons


# ---------------------------------------------------------------------------
# Main full run
# ---------------------------------------------------------------------------
def run_full(args, cfg, config_path):
    started = time.perf_counter()
    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    if cfg.get("model_mode") != "full":
        raise ValueError("run_full called for a non-full model_mode")

    input_path = gr.find_input(Path(args.input))
    LOG.info("spectrum: %s", input_path)
    read_start = time.perf_counter()
    spectrum = gr.read_spectrum(input_path, args.z, cfg)
    read_sec = time.perf_counter() - read_start
    x = spectrum["wave_rest_air"]
    y = spectrum["flux_1e17"]
    err = spectrum["err_1e17"]
    good = np.isfinite(x) & np.isfinite(y) & np.isfinite(err) & (err > 0)
    if int(good.sum()) < 100:
        raise ValueError("fewer than 100 usable pixels in the full model")
    x, y, err = x[good], y[good], err[good]
    spectrum["wave_rest_air"] = x
    spectrum["flux_1e17"] = y
    spectrum["err_1e17"] = err
    spectrum["n_pix_used"] = int(len(x))
    spectrum["wave_rest_min"] = float(np.min(x))
    spectrum["wave_rest_max"] = float(np.max(x))
    LOG.info(
        "z=%.8f  full rest=%.2f-%.2f A  n=%d  median S/N=%.1f",
        spectrum["z"],
        spectrum["wave_rest_min"],
        spectrum["wave_rest_max"],
        len(x),
        float(np.nanmedian(y / np.maximum(err, 1e-12))),
    )

    # Build line specifications once so the continuum fit can mask line windows.
    _, line_specs = build_full_model(cfg, x, y)

    lsq_start = time.perf_counter()
    model, lsq_quality, cont_sec, full_sec, line_mask = fit_full_model(
        cfg, x, y, err, line_specs
    )
    lsq_total_sec = time.perf_counter() - lsq_start
    # Effective error floor uses the fitted global continuum, not a local
    # sideband; this keeps the floor uniform in relative-flux terms.
    cont = model["continuum"](x)
    err_eff = gr.effective_errors(err, np.maximum(cont, 0.0), cfg)
    residuals = y - model(x)
    n_free = len(galspec.get_free_params(model))
    quality = gr.fit_quality(y, residuals, err, err_eff, n_free)
    quality["lsq_success"] = bool(lsq_quality.get("lsq_success", True))
    quality["lsq_message"] = lsq_quality.get("lsq_message", "")
    LOG.info(
        "full LSQ: success=%s chi2nu(raw)=%.3f chi2nu(floor)=%.3f rms=%.3f (%.2f s)",
        quality["lsq_success"],
        quality["chi2nu_raw"],
        quality["chi2nu_floor"],
        quality["rms_1e17"],
        lsq_total_sec,
    )

    if cfg.get("mcmc", {}).get("enabled", True):
        sampling = run_full_mcmc(
            model, x, y, err_eff, cfg, line_specs, cfg["mcmc"].get("seed", 42)
        )
        method_label = "emcee_mcmc_full"
        LOG.info(
            "full-model emcee: %d walkers x %d steps (burn %d), acceptance=%.3f, "
            "tau_max=%s, %.1f s",
            sampling["nwalkers"],
            sampling["nsteps"],
            sampling["nburn"],
            sampling["acceptance_fraction"],
            "n/a" if sampling["tau_max"] is None else f"{sampling['tau_max']:.1f}",
            sampling["runtime_sec"],
        )
    else:
        # Explicit debug path only; the production recipe uses emcee.
        metrics = metrics_for_specs(model, line_specs)
        sampling = {
            "method": "lsq_full",
            "mcmc": None,
            "chain": None,
            "theta_map": np.asarray(
                [getattr(model, n).value for n in galspec.get_free_params(model)]
            ),
            "flat_samples": None,
            "log_prob": None,
            "param_names": galspec.get_free_params(model),
            "posterior": None,
            "acceptance_fraction": None,
            "autocorr_tau": None,
            "tau_max": None,
            "tau_status": "not_applicable",
            "nsteps": None,
            "nburn": None,
            "nwalkers": None,
            "ndim": n_free,
            "n_samples_total": 0,
            "n_steps_kept": 0,
            "effective_sample_size": None,
            "runtime_sec": 0.0,
            "model_after_map": model,
            "_metrics": metrics,
        }
        method_label = "lsq_full"

    n_derived = int(cfg.get("mcmc", {}).get("max_samples_for_derived", 4000))
    if sampling["method"].startswith("emcee"):
        derive_posterior(sampling, line_specs, n_derived)
        rows = rows_from_full_sampling(
            sampling,
            line_specs,
            spectrum,
            cfg,
            float(cfg.get("detection", {}).get("snr_min", 3.0)),
        )
    else:
        # LSQ debug rows use the same posterior-free metric path with symmetric
        # zero errors; this path is never labelled MCMC.
        posterior = {}
        for key, values in sampling["_metrics"].items():
            posterior[f"{key}|flux"] = np.array([values["flux"]])
            posterior[f"{key}|fwhm"] = np.array([values["fwhm"]])
            posterior[f"{key}|velocity"] = np.array([values["velocity"]])
        sampling["posterior"] = posterior
        sampling["n_samples_derived"] = 0
        rows = []
        for spec in line_specs:
            for label in spec["component_labels"]:
                metrics = sampling["_metrics"].get(f"{spec['name']}|{label}")
                if metrics is None:
                    continue
                rows.append(
                    gr.make_line_row(
                        spec["name"],
                        label,
                        spec["wave"],
                        metrics["flux"],
                        float("nan"),
                        metrics["fwhm"],
                        float("nan"),
                        metrics["velocity"],
                        float("nan"),
                        float(cfg.get("detection", {}).get("snr_min", 3.0)),
                        "ok",
                        method_label,
                        spec["profile_window"],
                        "LSQ full model (debug only); no posterior",
                        gr.instrument_fwhm_kms(spectrum, spec["wave"], cfg),
                        cfg,
                    )
                )
            if spec.get("total", True):
                metrics = sampling["_metrics"].get(f"{spec['name']}|total")
                if metrics is not None:
                    rows.append(
                        gr.make_line_row(
                            spec["name"],
                            "total",
                            spec["wave"],
                            metrics["flux"],
                            float("nan"),
                            metrics["fwhm"],
                            float("nan"),
                            metrics["velocity"],
                            float("nan"),
                            float(cfg.get("detection", {}).get("snr_min", 3.0)),
                            "ok",
                            method_label,
                            spec["profile_window"],
                            "LSQ full model (debug only); no posterior",
                            gr.instrument_fwhm_kms(spectrum, spec["wave"], cfg),
                            cfg,
                        )
                    )

    # Coverage rows for H-alpha/[N II]/[S II] outside the SDSS rest range.
    coverage_rows = []
    for line in cfg.get("coverage_lines", []):
        wave = float(line["wave"])
        covered = spectrum["wave_rest_min"] <= wave <= spectrum["wave_rest_max"]
        status = "not_covered" if not covered else "not_fitted"
        coverage_rows.append(
            gr.make_line_row(
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
                    else "covered but outside the fitted full-model line list"
                ),
                0.0,
                cfg,
            )
        )
    all_rows = rows + coverage_rows

    reference_root = Path(args.reference_dir) if args.reference_dir else outdir.parent
    comparison = extended_comparison(outdir, all_rows, cfg, reference_root)

    # Save samples and derived posterior.
    write_start = time.perf_counter()
    saved_samples = np.zeros((0, 0), dtype=float)
    thin = 1
    if sampling.get("flat_samples") is not None:
        flat = np.asarray(sampling["flat_samples"], dtype=float)
        max_saved = int(
            cfg.get("mcmc", {}).get(
                "max_mcmc_samples_saved",
                cfg.get("output", {}).get("max_mcmc_samples_saved", 40000),
            )
        )
        # Save a real posterior, not a handful of interpolated points.  The
        # chain is thinned just enough to fit the cap; tau/ESS are reported
        # separately so the saved samples are not mistaken for independent
        # draws.  A 40k cap keeps the corner plot and npz portable.
        thin = max(1, int(np.ceil(len(flat) / max(1, max_saved))))
        saved_idx = np.arange(0, len(flat), thin, dtype=int)
        if len(saved_idx) > max_saved:
            keep = np.linspace(0, len(saved_idx) - 1, max_saved, dtype=int)
            saved_idx = saved_idx[keep]
        saved_samples = np.asarray(flat[saved_idx], dtype=np.float32)
        sampling["saved_samples"] = saved_samples
        sampling["thin"] = int(thin)
        payload = {
            "samples": saved_samples,
            "log_prob": np.asarray(sampling["log_prob"][saved_idx], dtype=np.float32),
            "param_names": np.asarray(sampling["param_names"], dtype="U64"),
            "theta_map": np.asarray(sampling["theta_map"], dtype=np.float32),
            "sampler": np.asarray([sampling["method"]], dtype="U32"),
            "thin": np.asarray([thin], dtype=np.int64),
            "n_total_postburn": np.asarray([len(flat)], dtype=np.int64),
            "acceptance_fraction": np.asarray([sampling["acceptance_fraction"]], dtype=np.float32),
            "tau": (
                np.asarray(sampling["autocorr_tau"], dtype=np.float32)
                if sampling.get("autocorr_tau") is not None
                else np.asarray([], dtype=np.float32)
            ),
            "tau_max": np.asarray(
                [sampling["tau_max"] if sampling.get("tau_max") is not None else np.nan],
                dtype=np.float32,
            ),
        }
        for key, values in (sampling.get("posterior") or {}).items():
            safe = key.replace("|", "__")
            payload[f"posterior__{safe}"] = np.asarray(values, dtype=np.float32)
        np.savez_compressed(outdir / "galspec_mcmc.npz", **payload)

    import pandas as pd

    pd.DataFrame(all_rows).to_csv(outdir / "galspec_lines.csv", index=False)
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
        "model_mode": "full",
    }
    gr.write_json(outdir / "config.effective.json", effective_config)

    # Full model decomposition table.
    xm = spectrum["wave_rest_air"]
    model_total = sampling["model_after_map"](xm)
    cont = sampling["model_after_map"]["continuum"](xm)
    feii = (
        sampling["model_after_map"]["FeII"](xm)
        if "FeII" in sampling["model_after_map"].submodel_names
        else np.zeros_like(xm)
    )
    model_table = {
        "wave_rest_air": xm,
        "flux_1e17": y,
        "err_1e17": err,
        "model_1e17": model_total,
        "continuum_1e17": cont,
        "feii_1e17": feii,
        "pseudo_continuum_1e17": cont + feii,
        "residual_1e17": y - model_total,
        "residual_over_err": (y - model_total) / np.maximum(err_eff, 1e-12),
    }
    for spec in line_specs:
        prof = np.zeros_like(xm)
        for name in spec["components"]:
            prof += sampling["model_after_map"][name](xm)
        model_table[f"line_{spec['name']}_1e17"] = prof
    pd.DataFrame(model_table).to_csv(outdir / "galspec_model.csv", index=False)

    plot_start = time.perf_counter()
    plot_full_fit(
        outdir,
        spectrum,
        sampling["model_after_map"],
        line_specs,
        cfg,
        quality,
    )
    if sampling.get("posterior") is not None:
        plot_full_uncertainty(outdir, sampling, cfg)
    plot_sec = time.perf_counter() - plot_start
    write_sec = time.perf_counter() - write_start - plot_sec

    runtime = {
        "total_sec": float(time.perf_counter() - started),
        "read_sec": float(read_sec),
        "continuum_start_sec": float(cont_sec),
        "full_lsq_sec": float(full_sec),
        "lsq_total_sec": float(lsq_total_sec),
        "sampling_main_sec": float(sampling.get("runtime_sec", 0.0)),
        "plot_sec": float(plot_sec),
        "write_sec": float(write_sec),
    }
    limitations = [
        "Full-continuum model: global normalised polynomial (degree %d) over %.0f-%.0f A rest frame plus park2022 Fe II and all fitted lines.  It is not a host-galaxy/stellar decomposition and does not use a QSO principal-component continuum."
        % (polynomial_degree(cfg), spectrum["wave_rest_min"], spectrum["wave_rest_max"]),
        "H-alpha 6563, [N II] 6548/6583 and red [S II] 6716/6731 are outside the SDSS rest-frame coverage of this z=0.5874 QSO; they are emitted as not_covered, not fitted.",
        "Fe II is the empirical park2022 template (rest 4000-5600 A); UV Fe II blends below 4000 A are absorbed by the polynomial continuum rather than modelled explicitly.",
        "The Balmer pseudo-continuum is not a separate model component: explicit Balmer lines H-beta through H12 are fitted, and the polynomial continuum represents the remaining UV/optical shape.  Broad high-order Balmer lines are blended with Fe II and are not separately resolved.",
        "Narrow Balmer/[O II]/[Ne III]/[S II]/[O I]/[S III]/He II/[Ne V] lines share one NLR sigma/dv; [O III] 4959/5007 core and wing have their own kinematic components.  The narrow/broad and core/wing splits are empirical and not directly interchangeable with other tools' definitions.",
        "Line fluxes are integrated Gaussian areas from the full model, in rest-frame 1e-17 erg s-1 cm-2 A-1 times (1+z); wavelengths are air rest-frame.  The (1+z) factor matches PyQSOFit and GANDALF.",
        "Intrinsic FWHM subtracts the SDSS WRESL resolution in quadrature; the observed FWHM is also stored.",
        "The emcee posterior is production-length but convergence is reported explicitly: tau_max, nsteps/tau_max and effective sample size are in run.json.  A chain with nsteps/tau_max < 50 is a usable posterior for a wide-line QSO but should not be described as asymptotically converged.",
        "The continuum is constrained by a polynomial, so absolute continuum systematics (flux calibration, slit losses, intrinsic QSO variability) are not included in the line-flux errors.",
        "The red [O I] 6300/[S III] 6312 region contains SDSS sky residuals; those weak lines are less reliable than H-beta/[O III].",
        "Mg II 2796/2804 is a broad doublet modelled without UV Fe II or a Balmer pseudo-continuum; its flux is model-dependent and lower than PyQSOFit's UV-inclusive value.",
    ]
    param_rows = []
    for name in galspec.get_free_params(sampling["model_after_map"]):
        param = getattr(sampling["model_after_map"], name)
        param_rows.append(
            {
                "name": name,
                "map_value": float(param.value),
                "lower_bound": float(param.bounds[0]) if param.bounds[0] is not None else None,
                "upper_bound": float(param.bounds[1]) if param.bounds[1] is not None else None,
            }
        )
    run_json = {
        "tool": "galspec_line",
        "galspec_version": galspec.__version__,
        "galspec_upstream": {
            "repo": "https://github.com/jyshangguan/GalSpec",
            "commit": "18e4effd796a1d51615ca2340bb927278eb18bbf",
        },
        "image": "galspec_line",
        "object": args.object,
        "model_mode": "full",
        "input": {
            "path": str(input_path),
            "layout": spectrum.get("layout"),
            "z": spectrum["z"],
            "ebv": spectrum.get("ebv"),
            "n_pix_raw": int(spectrum.get("n_pix_raw", 0)),
            "n_pix_used": int(spectrum.get("n_pix_used", len(x))),
            "rest_min_A": float(spectrum["wave_rest_min"]),
            "rest_max_A": float(spectrum["wave_rest_max"]),
            "flux_scale_input_to_1e17": float(spectrum.get("flux_scale_input_to_1e17", 1.0)),
            "vacuum_to_air": bool(cfg.get("input", {}).get("vacuum_to_air", True)),
            "rest_frame_flux_correction": bool(
                spectrum.get("rest_frame_flux_correction", True)
            ),
            "deredden": bool(spectrum.get("deredden", False)),
        },
        "frame": {
            "wavelength": "air rest-frame",
            "flux_internal": "1e-17 erg s-1 cm-2 A-1 (rest frame)",
            "flux_table": "both 1e-17 and cgs erg s-1 cm-2",
        },
        "model": {
            "scope": "full-continuum global model (2280-6460 A rest)",
            "continuum": {
                "type": "normalized polynomial",
                "degree": polynomial_degree(cfg),
                "x0": float(cfg.get("continuum", {}).get("polynomial_x0", 4350.0)),
                "xscale": float(cfg.get("continuum", {}).get("polynomial_xscale", 1200.0)),
            },
            "feii": cfg.get("continuum", {}).get("feii", {}),
            "kinematics": cfg.get("kinematics", {}),
            "lines": [
                {
                    "name": s["name"],
                    "wave_A": s["wave"],
                    "components": s["component_labels"],
                    "groups": s.get("groups", []),
                    "total": s["total"],
                }
                for s in line_specs
            ],
            "free_parameters": param_rows,
        },
        "fit": {
            "full": quality,
            "line_free_pixels": int(line_mask.sum()),
            "n_pixels": int(len(x)),
            "n_free": int(n_free),
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
            "n_steps_kept": sampling.get("n_steps_kept"),
            "n_samples_total": sampling.get("n_samples_total"),
            "effective_sample_size": sampling.get("effective_sample_size"),
            "saved_samples": int(len(saved_samples)),
            "saved_thin": int(thin),
            "n_samples_derived": sampling.get("n_samples_derived"),
        },
        "mcmc": {
            "saved_samples": int(len(saved_samples)),
            "saved_thin": int(thin),
            "saved_parameters": sampling.get("param_names"),
            "theta_map": np.asarray(sampling.get("theta_map", [])).tolist(),
            "file": "galspec_mcmc.npz",
        },
        "line_measurements": all_rows,
        "comparison": comparison,
        "runtime": runtime,
        "reference_runtimes": {
            "pyqsofit_uv": gr._reference_runtime(reference_root / "pyqsofit_uv"),
            "pyqsofitspec_line": gr._reference_runtime(reference_root / "pyqsofitspec_line"),
            "gandalf_line": gr._reference_runtime(reference_root / "gandalf_line"),
            "s3fit_line": gr._reference_runtime(reference_root / "s3fit_line"),
            "qgfit": gr._reference_runtime(reference_root / "qgfit"),
            "sheap_line": gr._reference_runtime(reference_root / "sheap_line"),
        },
        "limitations": limitations,
        "files": sorted({p.name for p in outdir.iterdir() if p.is_file()} | {"run.json"}),
    }
    gr.write_json(outdir / "run.json", run_json)
    LOG.info("wrote %s", outdir)
    LOG.info(
        "H-beta total=%.2f  1e-17; [O III] 5007 total=%.2f  1e-17",
        next(
            (
                r["flux_1e17"]
                for r in all_rows
                if r["line"] == "Hbeta" and r["component"] == "total"
            ),
            float("nan"),
        ),
        next(
            (
                r["flux_1e17"]
                for r in all_rows
                if r["line"] == "OIII_5007" and r["component"] == "total"
            ),
            float("nan"),
        ),
    )
    LOG.info("total runtime %.1f s", runtime["total_sec"])
    return 0
