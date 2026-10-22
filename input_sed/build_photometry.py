#!/usr/bin/env python3
"""Build the CIGALE photometry table for the five z>0.5 eFEDS QSOs.

The eFEDS SPALL catalogue provides SDSS AB magnitudes (u,g,r,i,z; the u
value is a -9.99999 sentinel in every object) and WISE Vega magnitudes
(W1-W4), but no magnitude-error columns.  We therefore adopt nominal
errors: 0.05 mag for SDSS and 0.125 mag for WISE (the latter is a
conservative choice because the WISE photometry has no quoted error in
SPALL).  Fluxes are written in mJy with the filter names used by CIGALE.

Usage:
    python3 input_sed/build_photometry.py [--out input_sed/photometry.txt]
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from astropy.io import fits

SDSS_AB_ZERO_JY = 3631.0
# WISE Vega zero points in Jy (W1-W4), from the WISE explanatory supplement.
WISE_ZERO_JY = (309.54, 171.79, 31.67, 8.363)
SDSS_NAMES = ("sloan.sdss.g", "sloan.sdss.r", "sloan.sdss.i", "sloan.sdss.z")
WISE_NAMES = ("wise.W1", "wise.W2", "wise.W3", "wise.W4")


def mag_to_mjy(mag: float, zero_jy: float) -> float:
    return zero_jy * 10.0 ** (-0.4 * mag) * 1000.0


def err_mjy(flux_mjy: float, err_mag: float) -> float:
    return flux_mjy * err_mag * np.log(10.0) / 2.5


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="input_zgt05")
    ap.add_argument("--out", default="input_sed/photometry.txt")
    ap.add_argument("--sdss-err-mag", type=float, default=0.05)
    ap.add_argument("--wise-err-mag", type=float, default=0.125)
    args = ap.parse_args()

    rows = []
    for path in sorted(Path(args.dir).glob("*.fits")):
        with fits.open(path) as hdul:
            sp = hdul["SPALL"].data
            za = hdul["ZALL"].data
            mags = np.asarray(sp["MAG"][0], dtype=float)
            wmag = np.asarray(sp["WISE_MAG"][0], dtype=float)
            redshift = float(np.asarray(za["Z"]).ravel()[0])
            obj_id = str(np.asarray(sp["CATALOGID"]).ravel()[0]).strip()

        # MAG = [u,g,r,i,z]; u is the -9.99999 sentinel in this dataset.
        sdss_flux = [mag_to_mjy(float(mags[i]), SDSS_AB_ZERO_JY)
                     for i in range(1, 5)]
        sdss_err = [err_mjy(f, args.sdss_err_mag) for f in sdss_flux]
        wise_flux = [mag_to_mjy(float(wmag[i]), WISE_ZERO_JY[i])
                     for i in range(4)]
        wise_err = [err_mjy(f, args.wise_err_mag) for f in wise_flux]

        rows.append([obj_id, f"{redshift:.8f}"]
                    + [f"{v:.12g}" for v in sdss_flux + wise_flux]
                    + [f"{v:.12g}" for v in sdss_err + wise_err])

    header = ["id", "redshift"] + list(SDSS_NAMES) + list(WISE_NAMES) \
        + [n + "_err" for n in SDSS_NAMES + WISE_NAMES]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        fh.write("# " + " ".join(header) + "\n")
        writer = csv.writer(fh, delimiter=" ")
        writer.writerows(rows)
    print(f"wrote {len(rows)} objects to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
