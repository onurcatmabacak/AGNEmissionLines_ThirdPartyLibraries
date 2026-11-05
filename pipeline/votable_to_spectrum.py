#!/usr/bin/env python3
"""Convert a published spectral-line VOTable into the 1-D FITS our fitters read.

Radio and millimetre archives routinely publish *calibrated* line spectra as
VOTables with a velocity column and an optical-depth or flux column (CSIRO's Data
Access Portal for ATCA/ASKAP products, for example).  Those are the cheapest way
to obtain real radio-band data, because the calibration is already done - but
``radio_line`` expects a FITS spectrum with a spectral axis and an error column.

Two conventions are handled explicitly, because getting them wrong silently
inverts the physics:

* ``--flux-is opacity`` - the archive stores *normalised absorption*, i.e. 1.0 is
  no absorption.  Optical depth is ``tau = -ln(opacity)`` and
  ``sigma_tau = sigma_opacity / opacity``.
* ``--flux-is value`` - the column already is the quantity to fit.

The spectral axis is written as frequency in GHz, ``nu = rest / (1 + v/c)``, with
``RESTFRQ`` set so that downstream velocity conversion reproduces the original
velocity axis.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

C_KMS = 299792.458


def log(msg: str) -> None:
    print(f"[votable_to_spectrum] {msg}", flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path, help="VOTable with a velocity column")
    ap.add_argument("output", type=Path, help="output 1-D FITS")
    ap.add_argument("--velocity-column", default="velocity")
    ap.add_argument("--flux-column", default="opacity")
    ap.add_argument("--error-column", default="sigma_opacity")
    ap.add_argument("--flux-is", choices=["opacity", "value"], default="opacity")
    ap.add_argument("--velocity-unit", choices=["auto", "m/s", "km/s"], default="auto")
    ap.add_argument("--rest-ghz", type=float, default=1.420405751)
    ap.add_argument("--bunit", default="optical depth")
    ap.add_argument("--source-name", default=None)
    ap.add_argument("--provenance", default=None)
    args = ap.parse_args(argv)

    from astropy.io import fits
    from astropy.table import Table

    tab = Table.read(args.input)
    for col in (args.velocity_column, args.flux_column, args.error_column):
        if col not in tab.colnames:
            raise SystemExit(f"column {col!r} not in {tab.colnames}")

    v = np.asarray(tab[args.velocity_column], dtype=float)
    raw = np.asarray(tab[args.flux_column], dtype=float)
    raw_err = np.asarray(tab[args.error_column], dtype=float)

    if args.velocity_unit == "auto":
        unit = str(tab[args.velocity_column].unit or "").lower()
        scale = 1e-3 if ("m / s" in unit or unit == "m/s") else 1.0
    else:
        scale = 1e-3 if args.velocity_unit == "m/s" else 1.0
    v_kms = v * scale
    log(f"{len(v_kms)} channels, v {v_kms.min():.1f}..{v_kms.max():.1f} km/s "
        f"(unit scale {scale:g})")

    if args.flux_is == "opacity":
        # 1.0 = no absorption, so tau = -ln(opacity)
        good = raw > 0
        flux = np.full_like(raw, np.nan)
        flux[good] = -np.log(raw[good])
        err = np.full_like(raw, np.nan)
        err[good] = raw_err[good] / raw[good]
        log(f"converted opacity -> tau: peak {np.nanmax(flux):.3f}")
    else:
        flux, err = raw, raw_err

    rest_ghz = float(args.rest_ghz)
    nu = rest_ghz / (1.0 + v_kms / C_KMS)          # GHz
    order = np.argsort(nu)
    nu, flux, err = nu[order], flux[order], err[order]

    hdu = fits.PrimaryHDU(np.vstack([flux, err]).astype(np.float32))
    h = hdu.header
    h["CTYPE1"] = ("FREQ", "spectral axis")
    h["CUNIT1"] = ("GHz", "")
    h["CRPIX1"] = (1.0, "reference pixel")
    h["CRVAL1"] = (float(nu[0]), "GHz at reference pixel")
    h["CDELT1"] = (float(np.median(np.diff(nu))), "GHz per channel")
    h["RESTFRQ"] = (rest_ghz * 1e9, "Hz")
    h["BUNIT"] = (args.bunit, "")
    h["NAXIS2"] = 2
    h["EXTNAME"] = ("FLUX+ERR", "")
    h["SRCNAME"] = (args.source_name or args.input.stem, "")
    if args.provenance:
        h["PROV"] = (args.provenance[:70], "data provenance")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    hdu.writeto(args.output, overwrite=True)
    log(f"wrote {args.output} ({nu.min():.6f}-{nu.max():.6f} GHz, "
        f"rest {rest_ghz} GHz, peak {np.nanmax(flux):.3f} {args.bunit})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
