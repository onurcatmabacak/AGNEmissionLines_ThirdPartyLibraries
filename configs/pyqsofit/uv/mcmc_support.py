"""Production helpers for PyQSOFit's emcee MCMC.

PyQSOFit delegates sampling to :meth:`lmfit.Minimizer.emcee`.  lmfit 1.3.2
builds its default walker start as

    p0 = (1 + 1e-4 * N(0, 1)) * param.value

for every free parameter.  If a maximum-likelihood estimate sits exactly on a
bound -- the common case for an undetected emission line whose amplitude is
bounded below by zero -- the corresponding p0 column is identically zero.
``emcee.EnsembleSampler`` then rejects the state with

    ValueError: Initial state has a large condition number

This module fixes only the initial state.  It keeps the model, the priors and
the likelihood untouched, and jitters every free parameter around its MLE with
a bounds-aware, strictly positive scale.  Zero-valued amplitudes are started
just above zero using the largest fitted amplitude in the same line complex as
the reference scale; this leaves the posterior free to return to the boundary.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterable

import numpy as np

_TINY = 1e-12
_DEFAULT_NWALKERS = 100


@dataclass
class WalkerInit:
    """Description of one free parameter's walker initialization."""

    name: str
    mle: float
    center: float
    sigma: float
    lower: float | None
    upper: float | None
    touched_bound: bool


def free_parameter_names(params: Any) -> list[str]:
    """Return free parameter names in lmfit's own insertion order.

    lmfit's ``emcee`` implementation sets ``vary=False`` for every parameter
    with an expression before collecting ``result.var_names``.  Mirror that
    here so the ``pos`` array has exactly the sampler dimension.
    """

    names: list[str] = []
    for name in params:
        par = params[name]
        if par.vary and par.expr is None:
            names.append(name)
    return names


def _finite(value: float | None) -> bool:
    return value is not None and np.isfinite(value)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if np.isfinite(out) else default


def _clean_float(value: Any) -> float | None:
    """Return a JSON-safe float (None for NaN/inf)."""

    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if np.isfinite(out) else None


def _parameter_sigma(
    name: str,
    par: Any,
    center: float,
    span: float | None,
    scale_ref: float,
    rng: np.random.Generator,
) -> float:
    """Choose a strictly positive, bounds-aware jitter for one parameter."""

    value = _as_float(getattr(par, "value", 0.0))
    stderr = _as_float(getattr(par, "stderr", None), 0.0)
    lower = getattr(par, "min", None)
    upper = getattr(par, "max", None)
    lo = _as_float(lower, -np.inf) if _finite(lower) else -np.inf
    hi = _as_float(upper, np.inf) if _finite(upper) else np.inf
    bounded = np.isfinite(lo) and np.isfinite(hi)

    is_scale = name.endswith("_scale")
    is_offset = any(key in name for key in ("dwave", "shift", "center"))
    is_sigma = name.endswith("_sigma")

    # A small positive width is enough to make the columns independent.  Bias
    # it upward when lmfit provides a sane covariance error and the parameter
    # is not pinned at a bound.
    base = max(abs(center) * 1e-3, _TINY)
    if stderr > 0 and stderr < 1e3 * max(abs(center), 1.0):
        base = max(base, 0.25 * stderr)
    if bounded and span and span > 0:
        base = min(base, 0.05 * span)
        base = max(base, 1e-8 * span)

    if abs(center) <= _TINY or (bounded and abs(center - lo) <= 1e-10 * max(span or 1.0, 1.0)):
        # Parameter is sitting on (or effectively at) its lower bound.
        if is_scale:
            # Undetected lines: start at 0.1% of the strongest amplitude in
            # the complex, which is small compared with any detected line but
            # still numerically independent.
            base = max(0.1 * scale_ref * 1e-2, 1e-6)
        elif is_offset:
            base = max(1e-4 * (span if bounded and span else 1.0), 1e-8)
        elif is_sigma:
            base = max(1e-4 * (span if bounded and span else abs(center) or 1.0), 1e-8)
        else:
            base = max(1e-4 * (span if bounded and span else 1.0), 1e-8)

    # Protect against an absurd stderr from a singular covariance matrix.
    if bounded and span:
        base = min(base, 0.2 * span)
    elif not bounded:
        base = min(base, 0.1 * max(abs(center), 1.0))
    return float(max(base, 1e-10))


def safe_initial_state(
    params: Any,
    nwalkers: int = _DEFAULT_NWALKERS,
    seed: int | None = None,
) -> tuple[np.ndarray, list[WalkerInit]]:
    """Build a linearly independent walker state around the MLE.

    Returns
    -------
    pos : ndarray, shape (nwalkers, nvarys)
    report : list[WalkerInit]
    """

    names = free_parameter_names(params)
    if not names:
        raise ValueError("cannot initialise emcee: no free parameters")
    if nwalkers <= 2 * len(names):
        raise ValueError(
            f"nwalkers={nwalkers} must exceed 2*nvarys={2 * len(names)}"
        )

    rng = np.random.default_rng(seed)
    scale_values = [
        abs(_as_float(params[name].value))
        for name in names
        if name.endswith("_scale") and abs(_as_float(params[name].value)) > 0
    ]
    scale_ref = max(scale_values) if scale_values else 1.0

    columns: list[np.ndarray] = []
    report: list[WalkerInit] = []
    for name in names:
        par = params[name]
        value = _as_float(par.value)
        lower = getattr(par, "min", None)
        upper = getattr(par, "max", None)
        lo = _as_float(lower, -np.inf) if _finite(lower) else -np.inf
        hi = _as_float(upper, np.inf) if _finite(upper) else np.inf
        span = (hi - lo) if np.isfinite(lo) and np.isfinite(hi) else None

        # Centre the walkers inside the allowed region.  A parameter exactly
        # on a bound is moved a hair inward so that no walker starts outside
        # the uniform prior.
        if span is not None:
            margin = max(1e-10 * span, 1e-12)
            center = float(np.clip(value, lo + margin, hi - margin))
        else:
            center = value

        sigma = _parameter_sigma(name, par, center, span, scale_ref, rng)
        draw = center + sigma * rng.standard_normal(nwalkers)

        if span is not None:
            margin = max(1e-10 * span, 1e-12)
            draw = np.clip(draw, lo + margin, hi - margin)
        if not np.all(np.isfinite(draw)):
            raise FloatingPointError(f"non-finite initial walkers for {name}")
        if float(np.ptp(draw)) == 0.0:
            draw = center + sigma * np.linspace(-1.0, 1.0, nwalkers)
        columns.append(draw)
        touched = False
        if span is not None:
            touched = bool(abs(value - lo) < 1e-10 * max(span, 1.0) or abs(value - hi) < 1e-10 * max(span, 1.0))
        report.append(
            WalkerInit(
                name=name,
                mle=value,
                center=center,
                sigma=sigma,
                lower=lo if np.isfinite(lo) else None,
                upper=hi if np.isfinite(hi) else None,
                touched_bound=touched,
            )
        )

    pos = np.column_stack(columns)
    if pos.shape != (nwalkers, len(names)):
        raise RuntimeError(f"bad walker state shape {pos.shape}")

    # emcee's own test: every column must vary and the centred/normalised
    # state must have a modest condition number.  Fail loudly if we did not
    # actually solve the problem.
    centered = pos - pos.mean(axis=0, keepdims=True)
    colmax = np.max(np.abs(centered), axis=0)
    if np.any(colmax == 0):
        bad = [names[i] for i in np.flatnonzero(colmax == 0)]
        raise RuntimeError(f"walker state has constant columns: {bad}")
    normalized = centered / colmax
    normalized /= np.sqrt(np.sum(normalized**2, axis=0, keepdims=True))
    cond = float(np.linalg.cond(normalized.astype(float)))
    if not np.isfinite(cond) or cond > 1e8:
        raise RuntimeError(f"walker state condition number too large: {cond:.3g}")
    return pos, report


def _complex_label(var_names: Iterable[str]) -> str:
    names = list(var_names)
    continuum_roots = ("PL_norm", "Fe_uv", "Fe_op", "conti_a", "Blamer", "Balmer")
    if any(name.startswith(continuum_roots) for name in names):
        return "continuum"
    for root in ("MgII", "CIII", "CIV", "Lya", "SiIV", "Ha", "Hb", "OIII", "HeII", "NII", "SII"):
        if any(name.startswith(root) for name in names):
            return root
    return names[0].split("_")[0] if names else "unknown"


def install_safe_emcee(
    module: Any,
    *,
    nwalkers: int = _DEFAULT_NWALKERS,
    seed: int | None = None,
    progress: bool = False,
) -> list[dict[str, Any]]:
    """Patch ``module.minimize`` so every emcee call gets a safe ``pos``.

    ``module`` is the ``pyqsofit.PyQSOFit`` module object.  The original
    ``lmfit.minimize`` is still used for the actual optimisation/sampling; the
    wrapper only supplies ``pos`` and records diagnostics.

    Returns a mutable list that is filled with one dictionary per MCMC run.
    """

    runs: list[dict[str, Any]] = []
    original = module.minimize
    if getattr(module, "_safe_emcee_installed", False):
        existing = getattr(module, "_safe_emcee_runs", None)
        if existing is not None:
            return existing
    module._safe_emcee_installed = True
    module._safe_emcee_runs = runs

    def wrapped(fcn, params=None, method=None, **kwargs):
        if method != "emcee":
            if method is None:
                return original(fcn, params=params, **kwargs)
            return original(fcn, params=params, method=method, **kwargs)

        run_seed = kwargs.pop("seed", seed)
        run_nwalkers = int(kwargs.pop("nwalkers", nwalkers))
        run_nwalkers = max(run_nwalkers, 2 * len(free_parameter_names(params)) + 2)
        if kwargs.get("pos") is None:
            pos, init_report = safe_initial_state(params, run_nwalkers, run_seed)
            kwargs["pos"] = pos
        else:
            init_report = []
        kwargs["nwalkers"] = run_nwalkers
        kwargs.setdefault("progress", progress)

        mle = {name: _as_float(params[name].value) for name in free_parameter_names(params)}
        # Snapshot the complete parameter set (including fixed and expression
        # parameters) so the derived quantities can be recomputed from every
        # posterior draw.  PyQSOFit's own gauss_result_all stores expression
        # parameters at their MLE, which is not a posterior sample.
        param_template = []
        for name in params:
            par = params[name]
            param_template.append({
                "name": name,
                "value": _as_float(par.value),
                "min": par.min,
                "max": par.max,
                "vary": bool(par.vary),
                "expr": par.expr,
            })
        all_names = list(params.keys())
        ln_lambda_0s = None
        call_args = kwargs.get("args")
        if call_args is not None and len(call_args) >= 4:
            candidate = call_args[3]
            if isinstance(candidate, (list, tuple, np.ndarray)) and len(candidate) == len(all_names) // 3:
                ln_lambda_0s = [float(item) for item in candidate]
        t0 = time.time()
        result = original(fcn, params=params, method=method, **kwargs)
        elapsed = time.time() - t0

        names = list(result.var_names)
        if len(names) != kwargs["pos"].shape[1]:
            raise RuntimeError(
                "safe emcee initialization dimension mismatch: "
                f"{len(names)} vs {kwargs['pos'].shape[1]}"
            )
        chain = np.asarray(result.chain, dtype=float)
        lnprob = np.asarray(result.lnprob, dtype=float)
        tau = None
        try:
            import emcee

            tau = np.atleast_1d(
                emcee.autocorr.integrated_time(chain, quiet=True)
            ).astype(float)
        except Exception:
            tau = None
        if tau is None:
            acor = getattr(result, "acor", None)
            if acor is not None:
                tau = np.atleast_1d(np.asarray(acor, dtype=float))
        acceptance = np.atleast_1d(np.asarray(result.acceptance_fraction, dtype=float))
        nsteps = int(chain.shape[0])
        ess = None
        if tau is not None:
            ess = np.full_like(tau, np.nan, dtype=float)
            good = np.isfinite(tau) & (tau > 0)
            if np.any(good):
                ess[good] = chain.shape[1] * nsteps / tau[good]

        label = _complex_label(names)
        used = {run["label"] for run in runs}
        if label in used:
            k = 2
            while f"{label}_{k}" in used:
                k += 1
            label = f"{label}_{k}"

        runs.append(
            {
                "label": label,
                "var_names": names,
                "all_names": all_names,
                "param_template": param_template,
                "ln_lambda_0s": ln_lambda_0s,
                "mle": mle,
                "chain": chain,
                "lnprob": lnprob,
                "acceptance_fraction": acceptance,
                "tau": tau,
                "ess": ess,
                "nwalkers": int(chain.shape[1]),
                "nvarys": int(chain.shape[2]),
                "nsteps_retained": nsteps,
                "seconds": elapsed,
                "init": [asdict(item) for item in init_report],
            }
        )
        return result

    module.minimize = wrapped
    return runs


def summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Compact, JSON-serialisable convergence summary."""

    out: dict[str, Any] = {}
    for run in runs:
        tau = run.get("tau")
        ess = run.get("ess")
        acceptance = np.asarray(run["acceptance_fraction"], dtype=float)
        tau_max = _clean_float(np.nanmax(tau)) if tau is not None and np.any(np.isfinite(tau)) else None
        ess_min = _clean_float(np.nanmin(ess)) if ess is not None and np.any(np.isfinite(ess)) else None
        nsteps = int(run["nsteps_retained"])
        converged = bool(
            np.isfinite(acceptance).all()
            and 0.2 <= float(np.nanmean(acceptance)) <= 0.5
            and tau_max is not None
            and nsteps >= 50.0 * tau_max
            and ess_min is not None and ess_min >= 500.0
        )
        out[run["label"]] = {
            "nvarys": int(run["nvarys"]),
            "nwalkers": int(run["nwalkers"]),
            "nsteps_retained": nsteps,
            "acceptance_mean": _clean_float(np.nanmean(acceptance)),
            "acceptance_std": _clean_float(np.nanstd(acceptance)),
            "acceptance_min": _clean_float(np.nanmin(acceptance)),
            "acceptance_max": _clean_float(np.nanmax(acceptance)),
            "tau_mean": _clean_float(np.nanmean(tau)) if tau is not None else None,
            "tau_max": tau_max,
            "ess_min": ess_min,
            "ess_median": _clean_float(np.nanmedian(ess)) if ess is not None else None,
            "steps_per_tau": _clean_float(nsteps / tau_max) if tau_max else None,
            "converged": converged,
            "seconds": float(run["seconds"]),
        }
    return out


def write_npz(
    runs: list[dict[str, Any]],
    path: str,
    extra: dict[str, np.ndarray] | None = None,
) -> None:
    """Persist every posterior chain plus its diagnostics in one npz."""

    payload: dict[str, Any] = {
        "labels": np.array([run["label"] for run in runs], dtype=str),
        "created_unix": np.array(time.time()),
    }
    if extra:
        for key, val in extra.items():
            arr = np.asarray(val)
            if arr.dtype == object:
                arr = np.asarray(val, dtype=str)
            payload[key] = arr
    for run in runs:
        label = run["label"]
        payload[f"{label}__chain"] = run["chain"]
        payload[f"{label}__lnprob"] = run["lnprob"]
        payload[f"{label}__names"] = np.array(run["var_names"], dtype=str)
        payload[f"{label}__acceptance"] = run["acceptance_fraction"]
        if run.get("tau") is not None:
            payload[f"{label}__tau"] = run["tau"]
        if run.get("ess") is not None:
            payload[f"{label}__ess"] = run["ess"]
        payload[f"{label}__mle"] = np.array(
            [run["mle"][name] for name in run["var_names"]], dtype=float
        )
        payload[f"{label}__init_sigma"] = np.array(
            [item["sigma"] for item in run["init"]], dtype=float
        )
    np.savez_compressed(path, **payload)


def write_run_json(
    runs: list[dict[str, Any]],
    path: str,
    *,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = summarize_runs(runs)
    payload = {
        "status": "success" if runs else "no_mcmc_runs",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **(meta or {}),
        "runs": summary,
        "total_seconds": float(sum(item["seconds"] for item in runs)),
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    return payload


def write_effective_config(path: str, config: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def mcmc_env_config() -> dict[str, Any]:
    """Environment-derived effective MCMC configuration."""

    def _int(name: str, default: int) -> int:
        try:
            return int(os.environ.get(name, default))
        except ValueError:
            return default

    return {
        "MCMC": os.environ.get("PYQSOFIT_MCMC", "0") == "1",
        "MC": os.environ.get("PYQSOFIT_MC", "0") == "1",
        "nsamp": _int("PYQSOFIT_NSAMP", 50),
        "nburn": _int("PYQSOFIT_NBURN", 20),
        "nthin": _int("PYQSOFIT_NTHIN", 10),
        "nwalkers": _int("PYQSOFIT_NWALKERS", _DEFAULT_NWALKERS),
        "seed": _int("PYQSOFIT_MCMC_SEED", 20240517),
        "err_floor": float(os.environ.get("PYQSOFIT_ERR_FLOOR", "0") or 0),
        "host": os.environ.get("PYQSOFIT_HOST", "0") == "1",
        "z": os.environ.get("PYQSOFIT_Z"),
    }


def _flatten(run: dict[str, Any], max_points: int = 6000, seed: int = 0) -> np.ndarray:
    flat = run["chain"].reshape((-1, run["nvarys"]))
    if flat.shape[0] > max_points:
        rng = np.random.default_rng(seed)
        idx = rng.choice(flat.shape[0], size=max_points, replace=False)
        flat = flat[np.sort(idx)]
    return flat


def save_corner_pdf(
    runs: list[dict[str, Any]],
    path: str,
    *,
    max_points: int = 6000,
) -> None:
    """One corner page per line complex (full posterior)."""

    import corner
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(path) as pdf:
        for run in runs:
            flat = _flatten(run, max_points=max_points)
            fig = corner.corner(
                flat,
                labels=run["var_names"],
                quantiles=[0.16, 0.5, 0.84],
                show_titles=True,
                title_fmt=".3g",
                title_kwargs={"fontsize": 8},
                label_kwargs={"fontsize": 7},
            )
            fig.suptitle(
                f"PyQSOFit emcee posterior: {run['label']} "
                f"({run['nvarys']} free parameters, "
                f"acc={np.nanmean(run['acceptance_fraction']):.2f})",
                fontsize=11,
            )
            pdf.savefig(fig)
            plt.close(fig)


def save_corner_png(
    run: dict[str, Any],
    path: str,
    *,
    max_points: int = 6000,
) -> None:
    import corner
    import matplotlib.pyplot as plt

    flat = _flatten(run, max_points=max_points)
    fig = corner.corner(
        flat,
        labels=run["var_names"],
        quantiles=[0.16, 0.5, 0.84],
        show_titles=True,
        title_fmt=".3g",
        title_kwargs={"fontsize": 8},
        label_kwargs={"fontsize": 7},
    )
    fig.suptitle(
        f"PyQSOFit emcee posterior: {run['label']} "
        f"({run['nvarys']} free parameters, "
        f"acc={np.nanmean(run['acceptance_fraction']):.2f})",
        fontsize=11,
    )
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_trace_pdf(
    runs: list[dict[str, Any]],
    path: str,
) -> None:
    """One trace page per line complex: median and 16/84 band per parameter."""

    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(path) as pdf:
        for run in runs:
            chain = run["chain"]
            names = run["var_names"]
            n = len(names)
            ncols = min(4, n)
            nrows = int(np.ceil(n / ncols))
            fig, axes = plt.subplots(
                nrows, ncols, figsize=(3.2 * ncols, 2.1 * nrows),
                squeeze=False, sharex=True,
            )
            steps = np.arange(chain.shape[0])
            for i, name in enumerate(names):
                ax = axes.flat[i]
                med = np.median(chain[:, :, i], axis=1)
                lo = np.percentile(chain[:, :, i], 16, axis=1)
                hi = np.percentile(chain[:, :, i], 84, axis=1)
                ax.fill_between(steps, lo, hi, color="C0", alpha=0.25, lw=0)
                ax.plot(steps, med, color="C0", lw=0.8)
                ax.set_title(name, fontsize=7)
                ax.tick_params(labelsize=6)
            for ax in axes.flat[n:]:
                ax.set_visible(False)
            fig.suptitle(
                f"PyQSOFit emcee trace: {run['label']} "
                f"({run['nsteps_retained']} retained steps x {run['nwalkers']} walkers)",
                fontsize=10,
            )
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)


def save_trace_png(run: dict[str, Any], path: str) -> None:
    import matplotlib.pyplot as plt

    chain = run["chain"]
    names = run["var_names"]
    n = len(names)
    ncols = min(4, n)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(3.2 * ncols, 2.1 * nrows),
        squeeze=False, sharex=True,
    )
    steps = np.arange(chain.shape[0])
    for i, name in enumerate(names):
        ax = axes.flat[i]
        med = np.median(chain[:, :, i], axis=1)
        lo = np.percentile(chain[:, :, i], 16, axis=1)
        hi = np.percentile(chain[:, :, i], 84, axis=1)
        ax.fill_between(steps, lo, hi, color="C0", alpha=0.25, lw=0)
        ax.plot(steps, med, color="C0", lw=0.8)
        ax.set_title(name, fontsize=7)
        ax.tick_params(labelsize=6)
    for ax in axes.flat[n:]:
        ax.set_visible(False)
    fig.suptitle(
        f"PyQSOFit emcee trace: {run['label']} "
        f"({run['nsteps_retained']} retained steps x {run['nwalkers']} walkers)",
        fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_line_corner(
    samples: dict[str, np.ndarray],
    path: str,
) -> None:
    """Corner plot of posterior line fluxes (1e-17 erg/s/cm2)."""

    import corner
    import matplotlib.pyplot as plt

    labels = []
    values = []
    for key, sample in samples.items():
        val = np.asarray(sample, dtype=float)
        val = val[np.isfinite(val)]
        if val.size and float(np.ptp(val)) > 0.0:
            labels.append(key)
            values.append(val)
    if len(labels) < 2:
        return
    n = min(len(val) for val in values)
    if n == 0:
        return
    matrix = np.column_stack([val[:n] for val in values])
    fig = corner.corner(
        matrix,
        labels=labels,
        quantiles=[0.16, 0.5, 0.84],
        show_titles=True,
        title_fmt=".1f",
        title_kwargs={"fontsize": 8},
        label_kwargs={"fontsize": 8},
    )
    fig.suptitle("PyQSOFit emcee posterior line fluxes (1e-17 erg/s/cm2)", fontsize=11)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def reconstruct_parameter_samples(
    run: dict[str, Any],
    indices: np.ndarray,
) -> np.ndarray:
    """Recompute all parameters (including expressions) at selected draws."""

    import lmfit

    params = lmfit.Parameters()
    for item in run["param_template"]:
        params.add(
            item["name"],
            value=item["value"],
            min=item["min"],
            max=item["max"],
            vary=False if item["expr"] else item["vary"],
            expr=item["expr"],
        )
    chain = run["chain"].reshape((-1, run["nvarys"]))
    free_names = run["var_names"]
    all_names = run["all_names"]
    out = np.empty((len(indices), len(all_names)), dtype=float)
    for row, index in enumerate(indices):
        for col, name in enumerate(free_names):
            params[name].value = float(chain[int(index), col])
        params.update_constraints()
        values = params.valuesdict()
        out[row] = [float(values[name]) for name in all_names]
    return out


def corrected_line_samples(
    qso: Any,
    runs: list[dict[str, Any]],
    indices: np.ndarray,
) -> np.ndarray:
    """Build a gauss_result_all-compatible matrix from the actual chains.

    ``PyQSOFit.fit_lines`` appends the MCMC ``samples`` array after filling
    fixed and expression parameters with their MLE values.  For tied lines
    such as [O III] 5007 (``3.03 * OIII4959``) that makes the derived flux
    constant in the supposed posterior.  This function evaluates the lmfit
    expressions on every requested draw and returns the matrix in the same
    column order as ``gauss_result_name`` (three values per Gaussian).
    """

    line_runs = [run for run in runs if run.get("label") != "continuum"]
    names = list(qso.gauss_result_name)
    ncols = len(names) // 2
    out = np.full((len(indices), ncols), np.nan, dtype=float)
    out_offset = 0
    name_offset = 0
    for run in line_runs:
        all_names = run["all_names"]
        ngauss = len(all_names) // 3
        block_cols = 3 * ngauss
        expected = [all_names[3 * j] for j in range(ngauss)]
        found = None
        for start in range(name_offset, len(names) - 6 * ngauss + 1, 6):
            if all(names[start + 6 * j] == expected[j] for j in range(ngauss)):
                found = start
                break
        if found is None:
            raise RuntimeError(
                f"could not locate {run['label']} block in gauss_result_name; "
                f"expected={expected[:4]} all_names={all_names[:6]} "
                f"gauss_names={names[:12]} n_names={len(names)} ngauss={ngauss}"
            )
        values = reconstruct_parameter_samples(run, indices)
        block = np.empty((len(indices), block_cols), dtype=float)
        block[:, 0::3] = values[:, 0::3]
        ln0 = run.get("ln_lambda_0s")
        if ln0 is None:
            raise RuntimeError(f"missing ln_lambda_0s for {run['label']}")
        block[:, 1::3] = values[:, 1::3] + np.asarray(ln0, dtype=float)[None, :]
        block[:, 2::3] = values[:, 2::3]
        out[:, out_offset:out_offset + block_cols] = block
        out_offset += block_cols
        name_offset = found + 6 * ngauss
    if out_offset != ncols:
        raise RuntimeError(
            f"reconstructed {out_offset} columns but gauss_result_all has {ncols}"
        )
    return out
