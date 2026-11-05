#!/usr/bin/env python3
"""Build the per-source CIGALE photometry tables from the eFEDS SPALL spectra.

The eFEDS SPALL catalogue provides SDSS AB magnitudes (u,g,r,i,z; the u value
is a -9.99999 sentinel in every object) and WISE Vega magnitudes (W1-W4), but
no MAGERR columns.  Real errors are taken from SPECTROFLUX_IVAR (SDSS) and a
matched AllWISE source; the cache is
`inputs/catalogs/photometry_errors.json`.  Nominal 0.05/0.125 mag errors are
only fallbacks.  Fluxes are written in mJy with CIGALE filter names.

Usage:
    .venv/bin/python pipeline/build_photometry.py
    .venv/bin/python pipeline/build_photometry.py --dir inputs --out-root inputs
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pipeline.io_layout import source_key  # noqa: E402

SDSS_AB_ZERO_JY = 3631.0
WISE_ZERO_JY = (309.54, 171.79, 31.67, 8.363)
SDSS_NAMES = ("sloan.sdss.g", "sloan.sdss.r", "sloan.sdss.i", "sloan.sdss.z")
WISE_NAMES = ("wise.W1", "wise.W2", "wise.W3", "wise.W4")


def mag_to_mjy(mag: float, zero_jy: float) -> float:
    return zero_jy * 10.0 ** (-0.4 * mag) * 1000.0


def err_mjy(flux_mjy: float, err_mag: float) -> float:
    return flux_mjy * err_mag * np.log(10.0) / 2.5


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="inputs")
    ap.add_argument("--out-root", default="inputs")
    ap.add_argument("--sdss-err-mag", type=float, default=0.05)
    ap.add_argument("--wise-err-mag", type=float, default=0.125)
    ap.add_argument("--error-cache", default="inputs/catalogs/photometry_errors.json")
    args = ap.parse_args()

    cache = {}
    if Path(args.error_cache).exists():
        cache = json.loads(Path(args.error_cache).read_text())
    paths = sorted(Path(args.dir).glob("*/raw/spec-*.fits"))
    if not paths:
        paths = sorted(Path(args.dir).rglob("*.fits"))
    rows = []
    for path in paths:
        with fits.open(path) as hdul:
            if "SPALL" not in hdul:
                continue
            sp = hdul["SPALL"].data
            za = hdul["ZALL"].data
            mags = np.asarray(sp["MAG"][0], dtype=float)
            wmag = np.asarray(sp["WISE_MAG"][0], dtype=float)
            z = float(np.asarray(za["Z"]).ravel()[0])
            obj_id = str(np.asarray(sp["CATALOGID"]).ravel()[0]).strip()
        # MAG = [u,g,r,i,z]; u is the -9.99999 sentinel in this dataset.
        sdss_flux = [mag_to_mjy(float(mags[i]), SDSS_AB_ZERO_JY) for i in range(1, 5)]
        wise_flux = [mag_to_mjy(float(wmag[i]), WISE_ZERO_JY[i]) for i in range(4)]
        sdss_id = path.stem.split("-")[-1]
        key = source_key(sdss_id, z)
        ec = cache.get(key, {})
        sdss_magerr = ec.get("sdss_magerr", [np.nan] * 4)
        wise_magerr = ec.get("wise_magerr", [np.nan] * 4)
        sdss_err = [err_mjy(f, sdss_magerr[i] if np.isfinite(sdss_magerr[i]) else args.sdss_err_mag)
                    for i, f in enumerate(sdss_flux)]
        wise_err = [err_mjy(f, wise_magerr[i] if np.isfinite(wise_magerr[i]) else args.wise_err_mag)
                    for i, f in enumerate(wise_flux)]
        row = [obj_id, f"{z:.8f}"] + [f"{v:.12g}" for v in sdss_flux + wise_flux] \
            + [f"{v:.12g}" for v in sdss_err + wise_err]
        rows.append(row)
        out = Path(args.out_root) / key / "photometry" / "photometry.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        header = ["id", "redshift"] + list(SDSS_NAMES) + list(WISE_NAMES) \
            + [n + "_err" for n in SDSS_NAMES + WISE_NAMES]
        with out.open("w", newline="") as fh:
            fh.write(" ".join(header) + "\n")
            csv.writer(fh, delimiter=" ").writerow(row)

    header = ["id", "redshift"] + list(SDSS_NAMES) + list(WISE_NAMES) \
        + [n + "_err" for n in SDSS_NAMES + WISE_NAMES]
    cat = Path(args.out_root) / "catalogs" / "photometry.txt"
    cat.parent.mkdir(parents=True, exist_ok=True)
    with cat.open("w", newline="") as fh:
        fh.write(" ".join(header) + "\n")
        csv.writer(fh, delimiter=" ").writerows(rows)
    print(f"wrote {len(rows)} per-source catalogues and {cat}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
