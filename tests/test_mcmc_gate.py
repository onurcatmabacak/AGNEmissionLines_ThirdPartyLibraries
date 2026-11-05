"""Convergence-gate tests, including the 1-D acceptance-band correction."""

import numpy as np

from configs.pyqsofit.uv.mcmc_support import acceptance_band, summarize_runs


def _fake_run(nvarys, acceptance=0.806, tau=27.0, nsteps=12900, label="fake"):
    nwalkers = 100
    return {
        "label": label,
        "nvarys": nvarys,
        "nwalkers": nwalkers,
        "acceptance_fraction": np.full(nwalkers, acceptance),
        "tau": np.full(nvarys, tau),
        "ess": np.full(nvarys, nwalkers * nsteps / tau),
        "nsteps_retained": nsteps,
        "seconds": 1.0,
    }


def test_one_dimensional_high_acceptance_is_not_a_failure():
    # [N II] has one free parameter; emcee's 1-D random walk accepts far more
    # than the multi-dimensional 0.20-0.50 guideline while mixing well.
    assert acceptance_band(1) == (0.05, 0.95)
    summary = summarize_runs([_fake_run(1)])["fake"]
    assert summary["acceptance_ok"] is True
    assert summary["converged"] is True


def test_multidimensional_high_acceptance_still_fails():
    summary = summarize_runs([_fake_run(9)])["fake"]
    assert summary["acceptance_ok"] is False
    assert summary["converged"] is False


def test_one_dimensional_extreme_acceptance_still_fails():
    summary = summarize_runs([_fake_run(1, acceptance=0.99)])["fake"]
    assert summary["acceptance_ok"] is False
    assert summary["converged"] is False
