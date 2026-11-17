#!/usr/bin/env python3
"""Rebin a high-resolution 1-D spectrum onto a coarser constant-dispersion grid.

HST/STIS echelle products have ~46,000 pixels (R ~ 45,000), while the SDSS-era
line fitters in this repository were built for ~4,000 pixels (R ~ 2,000) and
become impractically slow on them - PyQSOFit takes minutes, QSOFITMORE did not
finish in 45 minutes on Mrk 509.  This rebins in wavelength with inverse-variance
weighting, so the result is a statistically correct coarser spectrum rather than a
decimation.

    python pipeline/rebin_spectrum.py in.fits out.fits --step-A 1.0

Input layout: HDU1 with WAVELENGTH, FLUX, ERROR columns (STIS/``cspec`` and the
``prepare_inputs`` layout both match).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


def log(msg: str) -> None:
    print(f"[rebin_spectrum] {msg}", flush=True)


def main(argv=None) -> int:
    from astropy.io import fits

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--step-A", type=float, default=1.0, help="output bin width in Angstrom")
    ap.add_argument("--min-snr", type=float, default=0.0, help="drop samples below this S/N")
    args = ap.parse_args(argv)

    with fits.open(args.input) as h:
        hdu = h[1] if len(h) > 1 else h[0]
        d = hdu.data
        wave = np.asarray(d["WAVELENGTH"], float)
        flux = np.asarray(d["FLUX"], float)
        err = np.asarray(d["ERROR"], float)

    good = np.isfinite(wave) & np.isfinite(flux) & np.isfinite(err) & (err > 0)
    if args.min_snr > 0:
        good &= (np.abs(flux) / err) >= args.min_snr
    wave, flux, err = wave[good], flux[good], err[good]
    order = np.argsort(wave)
    wave, flux, err = wave[order], flux[order], err[order]

    edges = np.arange(wave.min(), wave.max() + args.step_A, args.step_A)
    idx = np.digitize(wave, edges) - 1
    ok = (idx >= 0) & (idx < edges.size - 1)
    idx, flux, err = idx[ok], flux[ok], err[ok]

    n = edges.size - 1
    wsum = np.bincount(idx, weights=1.0 / err ** 2, minlength=n)
    fsum = np.bincount(idx, weights=flux / err ** 2, minlength=n)
    out_flux = np.divide(fsum, wsum, out=np.zeros(n), where=wsum > 0)
    out_err = np.where(wsum > 0, 1.0 / np.sqrt(np.where(wsum > 0, wsum, 1)), 0.0)
    centre = 0.5 * (edges[:-1] + edges[1:])
    keep = wsum > 0

    out = fits.BinTableHDU.from_columns([
        fits.Column(name="WAVELENGTH", format="D", array=centre[keep]),
        fits.Column(name="FLUX", format="D", array=out_flux[keep]),
        fits.Column(name="ERROR", format="D", array=out_err[keep]),
    ])
    out.header["REBIN"] = (f"{args.step_A} A inverse-variance", "rebin_spectrum.py")
    fits.HDUList([fits.PrimaryHDU(), out]).writeto(args.output, overwrite=True)
    log(f"{wave.size} -> {keep.sum()} bins at {args.step_A} A "
        f"({centre[keep].min():.1f}-{centre[keep].max():.1f} A) -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
