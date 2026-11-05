"""The shared signal-to-noise definition must behave predictably.

This guards the reconciliation described in pipeline/line_snr.py: every tool now
reports the same three statistics, so their definitions have to be pinned down by
tests rather than by whatever each adapter happened to compute.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))

from line_snr import integrated_snr, noise_correlation, snr_row  # noqa: E402


def _gauss(vel, amp=1.0, centre=0.0, sigma=5.0):
    return amp * np.exp(-0.5 * ((vel - centre) / sigma) ** 2)


def test_white_noise_has_unit_correlation():
    rng = np.random.default_rng(0)
    assert noise_correlation(rng.normal(size=4000)) == pytest.approx(1.0, abs=0.05)


def test_oversampled_noise_inflates_the_correlation_factor():
    rng = np.random.default_rng(1)
    white = rng.normal(size=4000)
    # smooth over 4 channels: neighbouring samples become correlated
    smooth = np.convolve(white, np.ones(4) / 4.0, mode="same")
    assert noise_correlation(smooth) > 2.0


def test_integrated_snr_recovers_the_textbook_value_for_white_noise():
    rng = np.random.default_rng(2)
    vel = np.arange(0.0, 200.0, 1.0)
    model = _gauss(vel, amp=1.0, sigma=5.0)
    resid = rng.normal(scale=0.1, size=vel.size)
    n_eff = np.count_nonzero(model >= 0.5 * model.max())
    integral = np.trapezoid(model, vel) if hasattr(np, "trapezoid") else np.trapz(model, vel)
    expected = integral / (0.1 * 1.0 * np.sqrt(n_eff * 1.0))
    assert integrated_snr(model, vel, resid) == pytest.approx(expected, rel=0.35)


def test_snr_is_independent_of_velocity_direction():
    rng = np.random.default_rng(3)
    vel = np.arange(0.0, 200.0, 1.0)
    model = _gauss(vel, sigma=5.0)
    resid = rng.normal(scale=0.1, size=vel.size)
    forward = integrated_snr(model, vel, resid)
    backward = integrated_snr(model[::-1], vel[::-1], resid[::-1])
    assert forward == pytest.approx(backward, rel=1e-9)
    assert forward > 0


def test_a_width_pinned_at_a_bound_is_never_a_detection():
    rng = np.random.default_rng(4)
    vel = np.arange(0.0, 200.0, 1.0)
    model = _gauss(vel, amp=1.0, sigma=5.0)
    resid = rng.normal(scale=0.01, size=vel.size)
    free = snr_row(peak=1.0, sigma_peak=0.02, model=model, vel_kms=vel,
                   resid=resid, snr_min=3.0, at_bound=False)
    pinned = snr_row(peak=1.0, sigma_peak=0.02, model=model, vel_kms=vel,
                     resid=resid, snr_min=3.0, at_bound=True)
    assert free["detected"] is True and pinned["detected"] is False


def test_a_broad_line_is_not_rejected_for_a_low_per_channel_snr():
    rng = np.random.default_rng(5)
    vel = np.arange(0.0, 400.0, 1.0)
    model = _gauss(vel, amp=0.1, sigma=40.0)
    resid = rng.normal(scale=0.05, size=vel.size)
    row = snr_row(peak=0.1, sigma_peak=None, model=model, vel_kms=vel,
                  resid=resid, snr_min=3.0, at_bound=False)
    assert row["snr_rms"] < 3.0          # per channel it looks marginal ...
    assert row["snr_integrated"] > 3.0   # ... but the integrated line is solid
    assert row["detected"] is True
