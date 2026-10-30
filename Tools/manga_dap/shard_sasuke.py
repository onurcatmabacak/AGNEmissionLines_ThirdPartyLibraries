#!/usr/bin/env python3
"""Shard the SASUKE per-spectrum emission-line fit across processes.

The third long serial stage of the DAP is `mangadap.contrib.xjmc
.emline_fitter_with_ppxf`, which runs one pPXF emission-line fit per spectrum:

    for i in range(starting_spectrum, nspec):
        ... pp = ppxf.ppxf(...) ...
        # writes model[i], tpl_wgts[i], kin[i], fault[i], ...

Every iteration writes only index ``i`` of a set of preallocated output
arrays, and the inputs (``templates``, ``wave``, ``flux`` ...) are read-only,
so the loop shards exactly the same way as the pPXF and EMOM stages:

1. split ``starting_spectrum..nspec`` into contiguous ranges;
2. in each forked worker call the **original** function on the sliced spectra
   (``flux[lo:hi]``, ``noise[lo:hi]``, ``gpm[lo:hi]``, ``tpl_to_use[lo:hi]``,
   ``binid[lo:hi]``, ``flux_binned/noise_binned/gpm_binned`` when per-spectrum,
   ``x_binned/y_binned/x/y``) with ``starting_spectrum=0``;
3. copy each returned array's rows/columns back into the full-size outputs at
   ``[lo:hi]`` and OR the ``fault`` flags.

The fit code is never reimplemented.

Slicing is done positionally: the first six positional arguments of
``emline_fitter_with_ppxf`` are ``(tpl_wave, templates, wave, flux, noise,
velscale)``, so only ``flux`` and ``noise`` are per-spectrum there; the rest
of the per-spectrum arrays arrive as keywords.
"""
from __future__ import annotations

import os

import numpy as np

_ORIGINAL = None
_CALL = None

# Positional arguments that are per-spectrum (index in the signature).
_POS_SPECTRA = {3: "flux", 4: "noise"}
# Keyword arguments that are per-spectrum when they are arrays.
_KW_SPECTRA = ("gpm", "tpl_to_use", "binid", "flux_binned", "noise_binned",
               "gpm_binned", "x_binned", "y_binned", "x", "y")


def split_ranges(n, workers, min_per_worker=32):
    from shard_ppxf import split_ranges as _split
    return _split(n, workers, min_per_worker=min_per_worker)


def _slice(value, lo, hi):
    if value is None:
        return None
    arr = np.asarray(value)
    if arr.ndim == 0:
        return value
    if arr.shape[0] < hi and arr.shape[0] != hi - lo:
        # Not per-spectrum (e.g. a template axis) — leave untouched.
        return value
    return value[lo:hi]


def _worker(bounds):
    lo, hi = bounds
    args, kwargs = list(_CALL["args"]), dict(_CALL["kwargs"])
    nspec = _CALL["nspec"]
    for pos, name in _POS_SPECTRA.items():
        if pos < len(args) and args[pos] is not None:
            arr = np.asarray(args[pos])
            if arr.shape[0] == nspec:
                args[pos] = arr[lo:hi]
    for name in _KW_SPECTRA:
        if name in kwargs and kwargs[name] is not None:
            arr = np.asarray(kwargs[name])
            if arr.ndim and arr.shape[0] == nspec:
                kwargs[name] = arr[lo:hi]
    kwargs["starting_spectrum"] = 0
    return _ORIGINAL(*args, **kwargs)


def make_sharded(original, workers):
    """Return a replacement for ``emline_fitter_with_ppxf``."""

    def sharded(tpl_wave, templates, wave, flux, noise, velscale, velscale_ratio,
                *args, **kwargs):
        nspec = np.asarray(flux).shape[0]
        ranges = split_ranges(nspec, workers)
        if not ranges or kwargs.get("plot"):
            return original(tpl_wave, templates, wave, flux, noise, velscale,
                            velscale_ratio, *args, **kwargs)

        global _ORIGINAL, _CALL
        _ORIGINAL = original
        _CALL = dict(nspec=nspec,
                     args=(tpl_wave, templates, wave, flux, noise, velscale, velscale_ratio) + args,
                     kwargs=kwargs)

        import multiprocessing as mp

        ctx = mp.get_context("fork")
        with ctx.Pool(processes=len(ranges)) as pool:
            parts = pool.map(_worker, ranges)

        # Return signature (mangadap.contrib.xjmc.emline_fitter_with_ppxf):
        #   model, eml_model, model_gpm            -> shape (nspec, npix)
        #   tpl_wgts, tpl_wgts_err                 -> shape (nspec, ntpl)
        #   addcoef, multcoef                      -> (nspec, k) or None
        #   ebv                                    -> (nspec,) or None
        #   kininp, kin, kin_err                   -> (nspec, nkin)
        #   fault                                  -> (nspec,) bool
        n_out = len(parts[0])
        full = [None] * n_out
        for (lo, hi), part in zip(ranges, parts):
            width = hi - lo
            for k, value in enumerate(part):
                if value is None:
                    continue
                arr = np.asarray(value)
                if arr.shape[0] != width:
                    # not a per-spectrum array; identical in every worker
                    full[k] = value
                    continue
                if full[k] is None:
                    dtype = bool if k == n_out - 1 else arr.dtype
                    full[k] = np.zeros((nspec,) + arr.shape[1:], dtype=dtype)
                full[k][lo:hi] = arr
        print(f"Fitting spectrum: {nspec}/{nspec} (sharded over {len(ranges)} processes)",
              flush=True)
        return tuple(full)

    return sharded


def install(workers: int | None = None) -> bool:
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

    import mangadap.contrib.xjmc as xjmc

    _ORIGINAL = xjmc.emline_fitter_with_ppxf
    xjmc.emline_fitter_with_ppxf = make_sharded(_ORIGINAL, workers)

    # `mangadap/proc/sasuke.py` does `from ..contrib.xjmc import
    # emline_fitter_with_ppxf`, which binds the name at *its* import time.
    # Importing sasuke here and rebinding is enough because sitecustomize runs
    # before the DAP CLI; the guard keeps it safe if sasuke were already loaded.
    try:
        import mangadap.proc.sasuke as sasuke
        sasuke.emline_fitter_with_ppxf = xjmc.emline_fitter_with_ppxf
    except Exception as exc:  # noqa: BLE001
        print(f"[mangadap-shard] sasuke rebind failed: {exc}")
    print(f"[mangadap-shard] SASUKE emission-line fits sharded over {workers} processes")
    return True
