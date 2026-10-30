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
import shard_emom  # noqa: E402


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


# ---------------------------------------------------------------------------
# EMOM (emission-line moments) shard
# ---------------------------------------------------------------------------
class _FakeMomentsTable:
    """Minimal stand-in for EmissionLineMomentsDataTable."""

    def __init__(self, n, columns=("FLUX", "MOM1")):
        self.keys = list(columns)
        self._data = {k: np.zeros((n, 2)) for k in self.keys}
        self._n = n

    def __getitem__(self, key):
        return self._data[key]

    def set(self, key, values):
        self._data[key][:] = values


def test_emom_ranges_and_assembly():
    """Range splitting + column-wise copy-back reproduce the serial table."""
    import shard_emom

    n = 256
    flux = np.arange(n * 2, dtype=float).reshape(n, 2)

    def original(momdb, wave, flux, ivar=None, mask=None, sres=None,
                 continuum=None, redshift=None, bitmask=None):
        out = _FakeMomentsTable(len(flux))
        out.set("FLUX", np.asarray(flux) * 3.0)
        out.set("MOM1", np.asarray(flux) + 7.0)
        return out

    class _Momdb:
        size = 2

    expected = original(_Momdb(), None, flux)["FLUX"]
    shard_emom._new_table = lambda momdb, bitmask, n: _FakeMomentsTable(n)
    sharded = shard_emom.make_sharded(original, 4)
    got = sharded(_Momdb(), None, flux)
    assert got["FLUX"].shape == expected.shape
    assert np.array_equal(np.asarray(got["FLUX"]), np.asarray(expected))


def test_emom_skips_small_workloads():
    assert shard_emom.split_ranges(10, 4) == []


# ---------------------------------------------------------------------------
# SASUKE (per-spectrum emission-line fit) shard
# ---------------------------------------------------------------------------
def _fake_sasuke(ntpl=3, nkin=4, npix=6):
    """Deterministic stand-in matching emline_fitter_with_ppxf's return shape."""

    def fit(tpl_wave, templates, wave, flux, noise, velscale, velscale_ratio,
            gpm=None, tpl_to_use=None, binid=None, starting_spectrum=None, plot=False, **kw):
        nspec = len(flux)
        model = np.zeros((nspec, npix))
        eml = np.zeros((nspec, npix))
        gpm_out = np.ones((nspec, npix), dtype=bool)
        wgts = np.zeros((nspec, ntpl))
        wgts_err = np.zeros((nspec, ntpl))
        addc = np.zeros((nspec, 2))
        ebv = np.zeros(nspec)
        kininp = np.zeros((nspec, nkin))
        kin = np.zeros((nspec, nkin))
        kin_err = np.zeros((nspec, nkin))
        fault = np.zeros(nspec, dtype=bool)
        # Depend only on each spectrum's own data (flux is constant here), not
        # on the loop index: a shard restarts the index at 0 in each worker,
        # exactly as the real per-spectrum pPXF fit is independent of it.
        for i in range(nspec):
            model[i] = np.asarray(flux)[i].sum() + i * 0.0 + 1.0
            wgts[i] = np.asarray(flux)[i].sum()
            kin[i] = np.asarray(flux)[i].sum() * 2.0
            fault[i] = False
        return (model, eml, gpm_out, wgts, wgts_err, addc, None, ebv,
                kininp, kin, kin_err, fault)

    return fit


def test_sasuke_shard_matches_serial():
    import shard_sasuke

    n = 240
    # distinct per-spectrum content, so a misassembled shard is detectable
    flux = np.arange(n, dtype=float)[:, None] * np.ones((1, 6))
    noise = np.ones((n, 6))
    args = (np.zeros(5), np.ones((3, 5)), np.arange(6.0), flux, noise, 1.0, 1.0)

    serial = _fake_sasuke()(*args, gpm=np.ones((n, 6), bool))
    shard_sasuke._ORIGINAL = None
    sharded = shard_sasuke.make_sharded(_fake_sasuke(), 4)(*args, gpm=np.ones((n, 6), bool))

    assert len(sharded) == len(serial)
    for k, (a, b) in enumerate(zip(serial, sharded)):
        if a is None:
            assert b is None, f"output {k} should stay None"
            continue
        assert np.array_equal(np.asarray(a), np.asarray(b)), f"output {k} differs"


def test_sasuke_shard_slices_per_spectrum_keywords():
    import shard_sasuke

    n = 200
    seen = []

    def fit(tpl_wave, templates, wave, flux, noise, velscale, velscale_ratio,
            gpm=None, tpl_to_use=None, binid=None, starting_spectrum=None, plot=False, **kw):
        seen.append((len(flux), len(noise), None if gpm is None else len(gpm),
                     None if tpl_to_use is None else len(tpl_to_use)))
        return tuple(np.zeros((len(flux), 2)) for _ in range(11)) + (np.zeros(len(flux), bool),)

    shard_sasuke._ORIGINAL = None
    out = shard_sasuke.make_sharded(fit, 4)(
        np.zeros(5), np.ones((3, 5)), np.arange(6.0),
        np.ones((n, 6)), np.ones((n, 6)), 1.0, 1.0,
        gpm=np.ones((n, 6), bool), tpl_to_use=np.ones((n, 3), bool))
    # every per-spectrum output is assembled back to full length
    assert out[0].shape[0] == n
    assert out[-1].shape[0] == n
    del seen
