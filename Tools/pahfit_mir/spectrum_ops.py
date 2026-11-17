"""Small, dependency-free spectrum operations used by the PAHFIT runner.

Keeping these here (instead of inside ``run_pahfit.py``) lets the unit tests
exercise them without importing the PAHFIT stack or the JWST calibration data.
"""
from __future__ import annotations

import numpy as np


def apply_error_floor(flux, error, fraction: float):
    """Return errors with a relative floor added in quadrature.

    ``fraction`` is the floor as a fraction of ``|flux|``; 0 disables it.
    The result is ``sqrt(error**2 + (fraction * |flux|)**2)``, so a channel
    with a tiny quoted error cannot dominate the fit.
    """
    fraction = float(fraction)
    if not np.isfinite(fraction) or fraction < 0:
        raise ValueError("error-floor fraction must be finite and >= 0")
    f = np.asarray(flux, dtype=float)
    e = np.asarray(error, dtype=float)
    if f.shape != e.shape:
        raise ValueError("flux and error must have the same shape")
    if fraction == 0.0:
        return e.copy()
    return np.sqrt(e * e + (fraction * np.abs(f)) ** 2)
