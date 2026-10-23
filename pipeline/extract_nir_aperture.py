#!/usr/bin/env python3
"""Extract a QSO-centred aperture from a JWST/NIRSpec s3d cube.

The MAST x1d product is a single pipeline extraction.  This script uses the
cube WCS and a requested aperture (default 3x3 spaxels) centred on the target
coordinates, returning an EXTRACT1D-compatible FITS table that the NIR/MIR
adapters can read.

Usage:
  .venv/bin/python pipeline/extract_nir_aperture.py \
      /path/s3d.fits 15.05425 28.0405 inputs/J0100.../derived/centered_x1d.fits
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from astropy.io import fits


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("cube", type=Path)
    p.add_argument("ra", type=float)
    p.add_argument("dec", type=float)
    p.add_argument("out", type=Path)
    p.add_argument("--radius", type=int, default=1, help="half-size in spaxels (1 => 3x3)")
    p.add_argument("--target", default="SDSS_J0100+2802")
    args = p.parse_args(argv)

    with fits.open(args.cube, memmap=False) as h:
        sci = np.asarray(h["SCI"].data, dtype=float)
        err = np.asarray(h["ERR"].data, dtype=float)
        dq = np.asarray(h["DQ"].data, dtype=float)
        hdr = h["SCI"].header
        phdr = h[0].header
    # cube axes are (wave, y, x)
    crpix1, crpix2, crpix3 = hdr["CRPIX1"], hdr["CRPIX2"], hdr["CRPIX3"]
    crval1, crval2, crval3 = hdr["CRVAL1"], hdr["CRVAL2"], hdr["CRVAL3"]
    cdelt1, cdelt2, cdelt3 = hdr["CDELT1"], hdr["CDELT2"], hdr["CDELT3"]
    x0 = int(round(crpix1 + (args.ra - crval1) / cdelt1)) - 1
    y0 = int(round(crpix2 + (args.dec - crval2) / cdelt2)) - 1
    r = int(args.radius)
    xs = slice(max(0, x0 - r), min(sci.shape[2], x0 + r + 1))
    ys = slice(max(0, y0 - r), min(sci.shape[1], y0 + r + 1))
    sub = sci[:, ys, xs]
    esub = err[:, ys, xs]
    dsub = dq[:, ys, xs]
    good = (dsub == 0) & np.isfinite(sub) & np.isfinite(esub) & (esub > 0)
    n = good.sum(axis=(1, 2))
    denom = np.maximum(n, 1)
    flux = np.where(n > 0, np.nansum(np.where(good, sub, 0.0), axis=(1, 2)) / denom, np.nan)
    ferr = np.where(n > 0, np.sqrt(np.nansum(np.where(good, esub ** 2, 0.0), axis=(1, 2))) / denom, np.nan)
    dqout = np.where(n == good.shape[1] * good.shape[2], 0, 1)
    wave = crval3 + (np.arange(sci.shape[0]) + 1 - crpix3) * cdelt3
    # MJy/sr is the cube unit; keep it explicit.
    cols = [
        fits.Column(name="WAVELENGTH", format="D", unit="um", array=wave),
        fits.Column(name="SURF_BRIGHT", format="D", unit="MJy/sr", array=flux),
        fits.Column(name="SB_ERROR", format="D", unit="MJy/sr", array=ferr),
        fits.Column(name="DQ", format="J", array=dqout.astype(np.int32)),
    ]
    h = fits.Header()
    h["TARGNAME"] = args.target
    h["INSTRUME"] = "NIRSPEC"
    h["Z"] = float(phdr.get("Z", 6.327))
    h["APER"] = f"{2*r+1}x{2*r+1} centred on QSO"
    h["RA_REF"] = args.ra
    h["DEC_REF"] = args.dec
    hdul = fits.HDUList([fits.PrimaryHDU(header=h), fits.BinTableHDU.from_columns(cols, name="EXTRACT1D")])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    hdul.writeto(args.out, overwrite=True)
    print(f"wrote {args.out}: {len(wave)} pixels, {n.min()}–{n.max()} good spaxels, "
          f"{wave.min():.3f}–{wave.max():.3f} um")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
