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
from astropy.wcs import WCS


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("cube", type=Path)
    p.add_argument("ra", type=float)
    p.add_argument("dec", type=float)
    p.add_argument("out", type=Path)
    p.add_argument("--radius", type=float, default=3.0, help="aperture radius in spaxels")
    p.add_argument("--psf", action="store_true", help="Gaussian PSF weighting instead of a hard aperture")
    p.add_argument("--psf-sigma", type=float, default=1.0, help="PSF sigma in spaxels")
    p.add_argument("--centroid", choices=["auto", "target"], default="auto")
    p.add_argument("--background", action="store_true", help="subtract an outer annulus")
    p.add_argument("--target", default="SDSS_J0100+2802")
    args = p.parse_args(argv)

    with fits.open(args.cube, memmap=False) as h:
        sci = np.asarray(h["SCI"].data, dtype=float)
        err = np.asarray(h["ERR"].data, dtype=float)
        dq = np.asarray(h["DQ"].data, dtype=float)
        hdr = h["SCI"].header
        phdr = h[0].header
    # cube axes are (wave, y, x); use the celestial WCS (PC/SIP), not the
    # hand CRVAL/CDELT formula, which ignored PC1_1=-1 and decentred the QSO.
    wcs = WCS(hdr).celestial
    try:
        tx, ty = wcs.all_world2pix([[args.ra, args.dec]], 0)[0]
    except Exception:
        tx = hdr["CRPIX1"] + (args.ra - hdr["CRVAL1"]) / hdr["CDELT1"] - 1
        ty = hdr["CRPIX2"] + (args.dec - hdr["CRVAL2"]) / hdr["CDELT2"] - 1
    if args.centroid == "auto":
        # Flux-weighted centroid in a 9x9 box around the WCS target.  The
        # companion at x~22 is outside this box.
        xlo, xhi = int(round(tx)) - 4, int(round(tx)) + 5
        ylo, yhi = int(round(ty)) - 4, int(round(ty)) + 5
        med = np.nanmedian(sci[:, max(0, ylo):yhi, max(0, xlo):xhi], axis=0)
        wy, wx = np.mgrid[max(0, ylo):yhi, max(0, xlo):xhi]
        wgt = np.clip(np.nan_to_num(med), 0, None)
        if np.nansum(wgt) > 0:
            ty = float(np.nansum(wy * wgt) / np.nansum(wgt))
            tx = float(np.nansum(wx * wgt) / np.nansum(wgt))
    # wavelength grid from the spectral WCS
    wave = hdr["CRVAL3"] + (np.arange(sci.shape[0]) + 1 - hdr["CRPIX3"]) * hdr["CDELT3"]
    yy, xx = np.mgrid[0:sci.shape[1], 0:sci.shape[2]]
    rr = np.sqrt((xx - tx) ** 2 + (yy - ty) ** 2)
    if args.psf:
        wgt = np.exp(-0.5 * (rr / args.psf_sigma) ** 2)
    else:
        wgt = (rr <= args.radius).astype(float)
    sub = sci * wgt[None, :, :]
    esub = err * wgt[None, :, :]
    dsub = dq
    bkg = np.zeros(sci.shape[0], float)
    if args.background:
        bm = (rr > args.radius) & (rr <= args.radius + 3.0)
        bkg = np.nanmedian(sci[:, bm], axis=1)
        bkg[~np.isfinite(bkg)] = 0.0
    good = (dsub == 0) & np.isfinite(sub) & np.isfinite(esub) & (esub > 0)
    wsum = np.nansum(np.where(good, wgt[None, :, :], 0.0), axis=(1, 2))
    flux = np.where(wsum > 0, np.nansum(np.where(good, sub, 0.0), axis=(1, 2)) / wsum - bkg, np.nan)
    ferr = np.where(wsum > 0, np.sqrt(np.nansum(np.where(good, esub ** 2, 0.0), axis=(1, 2))) / wsum, np.nan)
    dqout = np.where(wsum > 0, 0, 1)
    # MJy/sr is the cube unit; keep it explicit.
    cols = [
        fits.Column(name="WAVELENGTH", format="D", unit="um", array=wave),
        fits.Column(name="SURF_BRIGHT", format="D", unit="MJy/sr", array=flux),
        fits.Column(name="SB_ERROR", format="D", unit="MJy/sr", array=ferr),
        fits.Column(name="DQ", format="J", array=dqout.astype(np.int32)),
        fits.Column(name="BACKGROUND", format="D", unit="MJy/sr", array=bkg),
    ]
    h = fits.Header()
    h["TARGNAME"] = args.target
    h["INSTRUME"] = "NIRSPEC"
    h["Z"] = float(phdr.get("Z", 6.327))
    h["APER"] = f"r={args.radius} psf={args.psf} centred=({tx:.2f},{ty:.2f})"
    h["RA_REF"] = args.ra
    h["DEC_REF"] = args.dec
    hdul = fits.HDUList([fits.PrimaryHDU(header=h), fits.BinTableHDU.from_columns(cols, name="EXTRACT1D")])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    hdul.writeto(args.out, overwrite=True)
    print(f"wrote {args.out}: {len(wave)} pixels, {int(np.sum(np.isfinite(flux)))} finite, "
          f"{wave.min():.3f}–{wave.max():.3f} um")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
