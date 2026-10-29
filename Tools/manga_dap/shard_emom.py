#!/usr/bin/env python3
"""Shard the MaNGA DAP emission-line-moments (EMOM) stage across processes.

`EmissionLineMoments.measure_moments` is a static method with the same
data-parallel shape as the pPXF stage — except that it preallocates one
`EmissionLineMomentsDataTable` and fills ``measurements[column][i, :]`` in a
``for i in range(nspec)`` loop.  So an exact shard means:

1. split ``0..nspec`` into contiguous ranges;
2. in each forked worker, call the **original** static method on the sliced
   inputs (``flux[lo:hi]``, ``ivar[lo:hi]``, ``mask[lo:hi]``, ``sres[lo:hi]``,
   ``continuum[lo:hi]``, ``redshift[lo:hi]``), yielding a small table;
3. copy every column of every partial table back into the full-size table at
   ``[lo:hi]``.

The measurement code itself is never reimplemented, so the numbers are the
upstream numbers; fork shares the read-only inputs instead of pickling them.

Enable with ``MANGADAP_SHARD_WORKERS=<n>`` — the shard installer patches both
the pPXF stage (`shard_ppxf`) and this one.
"""
from __future__ import annotations

import os

import numpy as np

_ORIGINAL = None
_CALL = None


def split_ranges(n, workers, min_per_worker=32):
    """Contiguous, balanced ranges; ``[]`` when sharding is not worthwhile."""
    from shard_ppxf import split_ranges as _split
    return _split(n, workers, min_per_worker=min_per_worker)


def _column_keys(table):
    return list(getattr(table, "keys", None) or [])


def _measure_chunk(bounds):
    lo, hi = bounds
    kwargs = dict(_CALL)
    for name in ("flux", "ivar", "mask", "sres", "continuum", "redshift"):
        value = kwargs.get(name)
        if value is not None:
            kwargs[name] = value[lo:hi]
    return _ORIGINAL(kwargs.pop("momdb"), kwargs.pop("wave"), **kwargs)


def make_sharded(original, workers):
    """Return a replacement for the static ``measure_moments``."""

    def sharded(momdb, wave, flux, ivar=None, mask=None, sres=None,
                continuum=None, redshift=None, bitmask=None):
        nspec = np.asarray(flux).shape[0]
        ranges = split_ranges(nspec, workers)
        if not ranges:
            return original(momdb, wave, flux, ivar=ivar, mask=mask, sres=sres,
                            continuum=continuum, redshift=redshift, bitmask=bitmask)

        global _CALL, _ORIGINAL
        _ORIGINAL = original
        _CALL = dict(momdb=momdb, wave=wave, flux=flux, ivar=ivar, mask=mask,
                     sres=sres, continuum=continuum, redshift=redshift,
                     bitmask=bitmask)
        import multiprocessing as mp

        ctx = mp.get_context("fork")
        with ctx.Pool(processes=len(ranges)) as pool:
            parts = pool.map(_measure_chunk, ranges)

        # Take the shape/type of a real partial table so the return type is
        # identical to the serial path, then copy column by column.
        full = _new_table(momdb, bitmask, nspec)
        keys = _column_keys(parts[0]) if parts else []
        for (lo, hi), part in zip(ranges, parts):
            for key in keys:
                full[key][lo:hi] = np.asarray(part[key])
        print(f"Measuring emission-line moments in spectrum: {nspec}/{nspec} "
              f"(sharded over {len(ranges)} processes)", flush=True)
        return full

    return sharded


def _new_table(momdb, bitmask, nspec):
    """Allocate an empty full-size moments table (the shard's target)."""
    from mangadap.proc.emissionlinemoments import EmissionLineMomentsDataTable
    return EmissionLineMomentsDataTable(neml=momdb.size, bitmask=bitmask, shape=nspec)


def install(workers: int | None = None) -> bool:
    """Monkeypatch ``EmissionLineMoments.measure_moments``."""
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

    from mangadap.proc.emissionlinemoments import EmissionLineMoments

    _ORIGINAL = EmissionLineMoments.measure_moments
    # It is a staticmethod; keep it callable both ways.
    replacement = make_sharded(_ORIGINAL, workers)
    EmissionLineMoments.measure_moments = staticmethod(replacement)
    print(f"[mangadap-shard] emission-line moments sharded over {workers} processes")
    return True
