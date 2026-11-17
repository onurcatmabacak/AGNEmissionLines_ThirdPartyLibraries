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


def block_bootstrap_indices(n: int, block_length: int, rng):
    """Indices for a block bootstrap of length ``n``.

    Contiguous blocks of ``block_length`` samples are drawn with replacement
    from ``0..n-1`` and concatenated/truncated to length ``n``.  A block
    length >= n degenerates to one block, which is *not* a bootstrap; callers
    should keep the block shorter than the series.
    """
    n = int(n)
    block_length = int(block_length)
    if n < 1:
        raise ValueError("n must be >= 1")
    if block_length < 1:
        raise ValueError("block_length must be >= 1")
    block_length = min(block_length, n)
    n_blocks = int(np.ceil(n / block_length))
    starts = rng.integers(0, max(1, n - block_length + 1), size=n_blocks)
    out = np.concatenate([np.arange(s, s + block_length) for s in starts])
    return out[:n]
