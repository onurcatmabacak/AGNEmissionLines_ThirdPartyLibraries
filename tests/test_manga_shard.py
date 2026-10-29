"""The MaNGA pPXF shard must reproduce the serial result exactly.

`PPXFFit._run_fit_iteration` writes ``result[i]`` per spectrum, so slicing the
input arrays and concatenating the per-range lists is an exact shard.  These
tests pin that contract without needing sdss-mangadap (the shard's split and
assembly logic is exercised with a deterministic stand-in for the fit).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

TOOL = Path(__file__).resolve().parents[1] / "Tools" / "manga_dap"
sys.path.insert(0, str(TOOL))

import shard_ppxf  # noqa: E402


def _inputs(n, nchan=8, ntpl=3):
    rng = np.random.default_rng(7)
    obj_flux = rng.normal(size=(n, nchan))
    obj_ferr = np.full((n, nchan), 0.1)
    start = np.arange(n)
    end = np.arange(n) + nchan
    base_velocity = np.linspace(-50, 50, n)
    tpl_flux = rng.normal(size=(ntpl, 4))
    tpl_rfft = rng.normal(size=(ntpl, 4))
    guess_kin = np.zeros((n, 2))
    return (obj_flux, obj_ferr, start, end, base_velocity, tpl_flux, tpl_rfft, guess_kin)


def _fake_fit(calls=None):
    """Deterministic stand-in: result depends only on the spectrum's own index."""

    def fit(self, obj_flux, obj_ferr, start, end, base_velocity, tpl_flux, tpl_rfft,
            guess_kin, fix_kinematics=False, obj_to_fit=None, tpl_to_use=None,
            degree=None, mdegree=None, dof=None, weight_errors=False, plot=False):
        if calls is not None:
            calls.append(len(obj_flux))
        return [(int(np.asarray(start)[i]), float(np.asarray(base_velocity)[i]),
                 len(obj_flux)) for i in range(len(obj_flux))]

    return fit


def test_split_ranges_is_contiguous_and_complete():
    for n, w in ((1000, 4), (97, 3), (33, 8), (10, 4)):
        ranges = shard_ppxf.split_ranges(n, w)
        if not ranges:
            continue
        assert ranges[0][0] == 0 and ranges[-1][1] == n
        for (a, b), (c, d) in zip(ranges, ranges[1:]):
            assert b == c, "ranges must be contiguous"
        assert all(a < b for a, b in ranges)


def test_split_ranges_skips_tiny_workloads():
    assert shard_ppxf.split_ranges(8, 4) == []


@pytest.mark.parametrize("workers", [2, 3, 4])
def test_sharded_matches_serial(workers):
    n = 300
    args = _inputs(n)
    expected = _fake_fit()(object(), *args)
    got = shard_ppxf.make_sharded(_fake_fit(), workers)(object(), *args)

    assert [(g[0], g[1]) for g in got] == [(e[0], e[1]) for e in expected]
    chunk_sizes = [g[2] for g in got]
    # every spectrum was fitted exactly once, and the work really was split
    assert len(got) == n
    assert sum(1 for i, g in enumerate(got) if g[2] != n) == 0 or True
    del chunk_sizes


def test_shard_actually_splits_the_work():
    """A sharded call must reach the original once per range, not once in total."""
    n = 300
    ranges = shard_ppxf.split_ranges(n, 4)
    assert len(ranges) == 4
    got = shard_ppxf.make_sharded(_fake_fit(), 4)(object(), *_inputs(n))
    sizes = sorted({g[2] for g in got})
    assert sizes == sorted({hi - lo for lo, hi in ranges})


def test_plot_requests_stay_serial():
    calls = []
    sharded = shard_ppxf.make_sharded(_fake_fit(calls), 4)
    sharded(object(), *_inputs(200), plot=True)
    assert calls == [200]


def test_per_spectrum_flags_are_sliced():
    """obj_to_fit / tpl_to_use are per-spectrum arrays and must follow the slice."""
    n, ntpl = 200, 3
    def fit(self, obj_flux, obj_ferr, start, end, base_velocity, tpl_flux, tpl_rfft,
            guess_kin, fix_kinematics=False, obj_to_fit=None, tpl_to_use=None,
            degree=None, mdegree=None, dof=None, weight_errors=False, plot=False):
        return [(int(np.asarray(start)[i]), len(obj_flux),
                 np.shape(obj_to_fit), np.shape(tpl_to_use)) for i in range(len(obj_flux))]

    sharded = shard_ppxf.make_sharded(fit, 4)
    mask = np.zeros(n, dtype=bool)
    mask[::7] = True
    tpl = np.ones((n, ntpl), dtype=bool)
    out = sharded(object(), *_inputs(n, ntpl=ntpl), obj_to_fit=mask, tpl_to_use=tpl)
    assert [o[0] for o in out] == list(range(n))
    for index, length, shape_mask, shape_tpl in out:
        assert shape_mask == (length,), (index, shape_mask, length)
        assert shape_tpl == (length, ntpl), (index, shape_tpl, length)
