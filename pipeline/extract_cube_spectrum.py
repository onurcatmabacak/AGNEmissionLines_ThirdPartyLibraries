#!/usr/bin/env python3
"""Extract a 1-D spectrum from a spectral-line cube.

Radio and sub-mm line fitters (``radio_line``, ``submm_line``, CASA ``specfit``)
want a spectrum, while ALMA/VLA products are cubes.  This script integrates a
box around the brightest pixel of the channel-averaged map (or a given pixel)
and writes a 1-D FITS spectrum with a proper FREQ axis plus an error spectrum
estimated from the line-free channels.

    python pipeline/extract_cube_spectrum.py <cube.fits[.gz]> <out.fits> \
        [--box 5] [--x X] [--y Y] [--unit Jy]

The output header carries CTYPE1=FREQ (GHz), CRVAL1/CDELT1, RESTFRQ and BUNIT so
the downstream adapters can convert to velocity without extra arguments.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


def log(msg: str) -> None:
    print(f"[extract_cube] {msg}", flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cube", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--box", type=int, default=5, help="box width in pixels (odd)")
    ap.add_argument("--x", type=int, default=None, help="pixel x (0-based); default = brightest")
    ap.add_argument("--y", type=int, default=None, help="pixel y (0-based); default = brightest")
    ap.add_argument("--unit", default="Jy", help="BUNIT written to the output header")
    ap.add_argument("--error-frac", type=float, default=0.15,
                    help="fraction of channels at each end used for the noise estimate")
    args = ap.parse_args(argv)

    from astropy.io import fits

    with fits.open(args.cube) as hdul:
        hdu = next(h for h in hdul if h.data is not None and np.asarray(h.data).ndim >= 3)
        data = np.asarray(hdu.data, dtype=float)
        hdr = hdu.header
    cube = np.squeeze(data)
    if cube.ndim == 4:                       # drop a Stokes axis
        cube = cube[0]
    if cube.ndim != 3:
        raise SystemExit(f"expected a 3-D cube, got shape {cube.shape}")
    nchan, ny, nx = cube.shape

    c3 = str(hdr.get("CTYPE3", "")).upper()
    v0, dv = float(hdr.get("CRVAL3")), float(hdr.get("CDELT3", 1.0))
    rest = float(hdr.get("RESTFRQ", 0.0) or 0.0)
    if "VELO" in c3 or "VRAD" in c3 or "VOPT" in c3:
        # velocity axis: CRVAL3/CDELT3 in m/s for ALMA products, km/s otherwise
        scale = 1e-3 if abs(dv) > 50 and abs(v0) > 50 else 1.0     # -> km/s
        v = (v0 + dv * np.arange(nchan)) * scale
        if rest <= 0:
            raise SystemExit("velocity axis without RESTFRQ: cannot convert to frequency")
        nu = rest * (1.0 - v / 299792.458) / 1e9                  # GHz
    else:
        nu = (v0 + dv * np.arange(nchan)) / 1e9                   # GHz from Hz

    mean_map = np.nanmean(cube, axis=0)
    if args.x is None or args.y is None:
        peak = np.unravel_index(np.nanargmax(mean_map), mean_map.shape)
        y, x = int(peak[0]), int(peak[1])
    else:
        x, y = int(args.x), int(args.y)
    half = max(0, (max(1, args.box) - 1) // 2)
    y0, y1 = max(0, y - half), min(ny, y + half + 1)
    x0, x1 = max(0, x - half), min(nx, x + half + 1)
    sub = cube[:, y0:y1, x0:x1]
    area = (y1 - y0) * (x1 - x0)
    log(f"cube {cube.shape} -> box x[{x0}:{x1}] y[{y0}:{y1}] ({area} pixels) "
        f"around ({x},{y}), {nchan} channels {nu.min():.4f}-{nu.max():.4f} GHz")

    # Mean over the box preserves the intensity scale (Jy/beam); summing would
    # need the beam area to mean anything physical.
    spec = np.nanmean(sub.reshape(nchan, -1), axis=1)

    # Noise from the line-free ends of the band.
    edge = max(3, int(args.error_frac * nchan))
    line_free = np.concatenate([spec[:edge], spec[-edge:]])
    sigma = float(np.nanstd(line_free))
    if not np.isfinite(sigma) or sigma <= 0:
        sigma = float(np.nanstd(spec)) or 1.0
    err = np.full(nchan, sigma)

    out_hdu = fits.PrimaryHDU(spec.astype(np.float32))
    out_hdu.header.update({
        "CTYPE1": "FREQ-GHz", "CRVAL1": nu[0], "CDELT1": nu[1] - nu[0],
        "CUNIT1": "GHz", "BUNIT": args.unit,
        "OBJECT": str(hdr.get("OBJECT", "")),
        "RESTFRQ": rest / 1e9 if rest > 1e6 else rest,
        "SRCRA": hdr.get("CRVAL1", 0.0), "SRCDEC": hdr.get("CRVAL2", 0.0),
        "PIXBOX": area, "NOISE": sigma,
    })
    err_hdu = fits.ImageHDU(err.astype(np.float32), name="ERR")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList([out_hdu, err_hdu]).writeto(args.out, overwrite=True)
    log(f"wrote {args.out}: peak {np.nanmax(spec):.4g} {args.unit}, "
        f"noise {sigma:.4g}, S/N {np.nanmax(spec) / sigma:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
