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


def trim_near_gaps(wavelength, gaps, trim_um: float):
    """Boolean mask that drops samples within ``trim_um`` of a coverage gap.

    ``gaps`` is the list produced by ``_coverage_info`` (``start_um`` /
    ``end_um``).  The mask is True for samples that should be kept.
    """
    trim_um = float(trim_um)
    if not np.isfinite(trim_um) or trim_um < 0:
        raise ValueError("gap trim must be finite and >= 0")
    w = np.asarray(wavelength, dtype=float)
    keep = np.ones(w.shape, dtype=bool)
    if trim_um == 0.0:
        return keep
    for gap in gaps or ():
        start = float(gap["start_um"])
        end = float(gap["end_um"])
        keep &= ~((np.abs(w - start) <= trim_um) | (np.abs(w - end) <= trim_um))
    return keep
