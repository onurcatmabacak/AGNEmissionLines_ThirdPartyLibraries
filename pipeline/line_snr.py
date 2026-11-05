"""One documented signal-to-noise definition for the line-fitting tools.

Until now every adapter invented its own detection statistic:

* ``radio_line``  used ``peak / rms`` of the residuals,
* ``submm_line``  used ``max|model| / rms``,
* ``casa_specfit`` used ``amplitude / amplitude_err`` from the CASA covariance.

On the same NGC 1275 HCN 3-2 spectrum those gave 2.9, 2.0 and 6.0 for what is
one and the same fit, so "detected" was not comparable across tools.  This
module fixes the meaning of the columns.

``snr_integrated`` (primary)
    Significance of the integrated line flux,
    ``|integral| / (rms * dv * sqrt(N_eff * k))``, where ``N_eff`` is the number
    of channels above half the model peak and ``k`` is the noise correlation
    factor measured from the residual autocorrelation.  ``k`` matters: ALMA and
    GBT cubes are usually regridded to channels much finer than the spectral
    resolution, so neighbouring channels are correlated and the naive
    ``sqrt(N)`` overestimates a detection by ``sqrt(k)`` (2-3x here).

``snr``
    Peak significance ``peak / sigma_peak`` from the fit covariance.  Free of
    channel-correlation assumptions, but sensitive to parameters pinned at a
    bound.  Not available for McFine, whose peak is a derived quantity.

``snr_rms``
    The old per-channel ``peak / rms``.  Kept for traceability only: for a
    *resolved* line it is intrinsically small (the flux is spread over many
    channels), so it must not be used to reject a broad detection.

``detected`` is ``snr_integrated >= snr_min`` (falling back to ``snr`` when the
integrated value cannot be computed), and is always False when the fitted width
sits on a prior bound - a fit pinned at a bound is not a measurement.
"""
from __future__ import annotations

import numpy as np

# numpy renamed trapz -> trapezoid in 2.0; the containers and the host venv do
# not agree on the major version, so support both.
_trapz = getattr(np, "trapezoid", None) or np.trapz


def noise_correlation(resid: np.ndarray, max_lag: int = 200) -> float:
    """Correlation factor ``k = 1 + 2*sum(rho_lag)`` of the residual noise.

    Integrates the autocorrelation until its first non-positive lag.  ``k = 1``
    for white noise, larger when the channels are oversampled.
    """
    r = np.asarray(resid, dtype=float)
    r = r[np.isfinite(r)]
    if r.size < 8:
        return 1.0
    r = r - np.mean(r)
    var = float(np.dot(r, r) / r.size)
    if var <= 0:
        return 1.0
    acf = np.correlate(r, r, mode="full")[r.size - 1:] / (var * r.size)
    total = 0.0
    for lag in range(1, min(max_lag, acf.size)):
        if acf[lag] <= 0:
            break
        total += float(acf[lag])
    return max(1.0, 1.0 + 2.0 * total)


def integrated_snr(model: np.ndarray, vel: np.ndarray, resid: np.ndarray) -> float:
    """Significance of the integrated flux of a fitted model profile.

    ``model`` is the baseline-subtracted fitted model on the data grid, ``vel``
    the same grid in km/s, ``resid`` the fit residuals in the same flux unit.
    """
    model = np.asarray(model, dtype=float)
    vel = np.asarray(vel, dtype=float)
    resid = np.asarray(resid, dtype=float)
    if model.size < 2 or resid.size < 2:
        return float("nan")
    rms = float(np.nanstd(resid))
    if not np.isfinite(rms) or rms <= 0:
        return float("nan")
    dv = float(np.median(np.abs(np.diff(vel))))
    if not np.isfinite(dv) or dv <= 0:
        return float("nan")
    peak = float(np.nanmax(np.abs(model)))
    if not np.isfinite(peak) or peak <= 0:
        return 0.0
    n_eff = max(int(np.count_nonzero(np.abs(model) >= 0.5 * peak)), 1)
    k = noise_correlation(resid)
    # the velocity grid can run either way (a frequency axis gives a descending
    # velocity axis), so take the magnitude
    integral = float(abs(_trapz(np.abs(model), vel)))
    return float(integral / (rms * dv * np.sqrt(n_eff * k)))


def peak_sigma(peak_func, theta, covar, rel_step: float = 1e-4) -> float:
    """Propagate a parameter covariance onto a derived peak value."""
    theta = np.asarray(theta, dtype=float)
    covar = np.asarray(covar, dtype=float)
    if theta.size == 0 or covar.shape != (theta.size, theta.size):
        return float("nan")
    if not np.all(np.isfinite(covar)):
        return float("nan")
    jac = np.zeros(theta.size, dtype=float)
    for i in range(theta.size):
        step = rel_step * max(abs(theta[i]), 1e-8)
        up, dn = theta.copy(), theta.copy()
        up[i] += step
        dn[i] -= step
        jac[i] = (float(peak_func(up)) - float(peak_func(dn))) / (2.0 * step)
    var = float(jac @ covar @ jac)
    return float(np.sqrt(var)) if var > 0 else float("nan")


def snr_row(peak: float, sigma_peak: float | None, model: np.ndarray | None,
            vel_kms: np.ndarray | None, resid: np.ndarray | None,
            snr_min: float, at_bound: bool = False,
            snr_integrated_override: float | None = None) -> dict:
    """The S/N columns, computed and interpreted the same way for every tool."""
    peak = abs(float(peak))
    snr = (float(peak / sigma_peak)
           if sigma_peak and np.isfinite(sigma_peak) and sigma_peak > 0 else float("nan"))
    rms = float(np.nanstd(resid)) if resid is not None and np.size(resid) > 1 else float("nan")
    snr_rms = float(peak / rms) if np.isfinite(rms) and rms > 0 else float("nan")
    if snr_integrated_override is not None:
        snr_int = float(snr_integrated_override)
    elif model is not None and vel_kms is not None and resid is not None:
        snr_int = integrated_snr(model, vel_kms, resid)
    else:
        snr_int = float("nan")

    primary = snr_int if np.isfinite(snr_int) else snr
    ok = bool(np.isfinite(primary) and primary >= snr_min and not at_bound)
    return {
        "snr": snr,
        "snr_integrated": snr_int,
        "snr_rms": snr_rms,
        "width_at_bound": bool(at_bound),
        "detected": ok,
    }
