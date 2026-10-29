#!/usr/bin/env python3
"""Shard the MaNGA DAP pPXF stage across processes — exactly, by slicing.

`sdss-mangadap` 4.5.0 has no parallel entry point: `PPXFFit._run_fit_iteration`
walks the spectra with ``for i in range(nspec)`` and writes ``result[i]``.  Each
iteration touches only its own ``i`` — the shared inputs (``tpl_flux``,
``tpl_rfft``, `self`) are read-only — so the loop is *data-parallel*.

That makes an exact shard possible without reimplementing the fit:

1. split ``0..nspec`` into contiguous ranges;
2. in each forked worker, call the **original** method with the sliced arrays
   (``obj_flux[lo:hi]``, ``obj_ferr[lo:hi]``, ``start[lo:hi]``, ...);
3. concatenate the per-range result lists in index order.

Because every fit is executed by the unmodified upstream code with the same
inputs, the output objects are the same; only wall-clock changes.  Workers are
forked, so the template arrays are shared copy-on-write instead of pickled.

Enable with ``MANGADAP_SHARD_WORKERS=<n>`` (the image ships a ``sitecustomize``
that calls :func:`install`).  ``MANGADAP_SHARD=0`` disables it; ``plot=True``
and single-spectrum calls always run serially.
"""
from __future__ import annotations

import os
import sys

import numpy as np

_STATE = None
_ORIGINAL = None


def _chunk(bounds):
    """Fit the spectra in ``[lo, hi)`` with the unmodified upstream method."""
    lo, hi = bounds
    self, positional, keywords = _STATE
    obj_flux, obj_ferr, start, end, base_velocity, tpl_flux, tpl_rfft, guess_kin = positional
    kw = dict(keywords)
    for name in ("obj_to_fit", "tpl_to_use"):
        value = kw.get(name)
        if value is not None:
            kw[name] = value[lo:hi]
    return _ORIGINAL(
        self,
        obj_flux[lo:hi], obj_ferr[lo:hi], start[lo:hi], end[lo:hi],
        base_velocity[lo:hi], tpl_flux, tpl_rfft, guess_kin[lo:hi], **kw,
    )


def split_ranges(n, workers, min_per_worker=16):
    """Contiguous, balanced ranges; ``[]`` when the shard is not worthwhile."""
    if workers <= 1 or n < 2 * min_per_worker:
        return []
    workers = min(workers, max(1, n // min_per_worker))
    step = n / float(workers)
    return [(int(round(i * step)), int(round((i + 1) * step))) for i in range(workers)]


def make_sharded(original, workers):
    """Return a drop-in replacement for ``PPXFFit._run_fit_iteration``."""

    def sharded(self, obj_flux, obj_ferr, start, end, base_velocity, tpl_flux,
                tpl_rfft, guess_kin, fix_kinematics=False, obj_to_fit=None,
                tpl_to_use=None, degree=None, mdegree=None, dof=None,
                weight_errors=False, plot=False):
        nspec = obj_flux.shape[0]
        ranges = [] if plot else split_ranges(nspec, workers)
        if not ranges:
            return original(
                self, obj_flux, obj_ferr, start, end, base_velocity, tpl_flux,
                tpl_rfft, guess_kin, fix_kinematics=fix_kinematics,
                obj_to_fit=obj_to_fit, tpl_to_use=tpl_to_use, degree=degree,
                mdegree=mdegree, dof=dof, weight_errors=weight_errors, plot=plot,
            )
        global _STATE
        _STATE = (
            self,
            (obj_flux, obj_ferr, start, end, base_velocity, tpl_flux, tpl_rfft, guess_kin),
            dict(fix_kinematics=fix_kinematics, obj_to_fit=obj_to_fit,
                 tpl_to_use=tpl_to_use, degree=degree, mdegree=mdegree, dof=dof,
                 weight_errors=weight_errors, plot=False),
        )
        # Patch the worker's view of the original too (fork inherits it).
        global _ORIGINAL
        _ORIGINAL = original
        import multiprocessing as mp

        ctx = mp.get_context("fork")
        with ctx.Pool(processes=len(ranges)) as pool:
            parts = pool.map(_chunk, ranges)
        # Upstream builds `numpy.empty(nspec, dtype=object)`; downstream code
        # indexes and masks it, so return the same container type.
        out = np.empty(nspec, dtype=object)
        for (lo, hi), part in zip(ranges, parts):
            out[lo:hi] = part
        _STATE = None
        print(f"Running pPXF fit on spectrum: {nspec}/{nspec} "
              f"(sharded over {len(ranges)} processes)", flush=True)
        return out

    return sharded


def install(workers: int | None = None) -> bool:
    """Monkeypatch ``PPXFFit._run_fit_iteration``.  Returns True if installed."""
    global _ORIGINAL
    if _ORIGINAL is not None:
        return True
    if workers is None:
        try:
            workers = int(os.environ.get("MANGADAP_SHARD_WORKERS", "0"))
        except ValueError:
            workers = 0
    if workers <= 1 or os.environ.get("MANGADAP_SHARD", "1") == "0":
        return False

    from mangadap.proc.ppxffit import PPXFFit

    _ORIGINAL = PPXFFit._run_fit_iteration
    sharded = make_sharded(_ORIGINAL, workers)
    PPXFFit._run_fit_iteration = sharded
    print(f"[mangadap-shard] pPXF stage sharded over {workers} processes", file=sys.stderr)
    return True
