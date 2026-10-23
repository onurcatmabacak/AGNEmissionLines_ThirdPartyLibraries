#!/usr/bin/env python3
"""Fetch real SDSS spectro-photometric and AllWISE magnitude errors.

The eFEDS ``SPALL`` table has no MAGERR columns, but it does carry
``SPECTROFLUX``/``SPECTROFLUX_IVAR`` for the five SDSS bands.  AllWISE provides
the W1-W4 magnitude errors through IRSA TAP.  The result is cached in
``inputs/catalogs/photometry_errors.json``; ``build_photometry.py`` uses it
when present and falls back to nominal errors otherwise.

Usage:
    .venv/bin/python pipeline/fetch_photometry_errors.py
"""
from __future__ import annotations

import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pipeline.io_layout import iter_sources, source_files  # noqa: E402

TAP = "https://irsa.ipac.caltech.edu/TAP/sync?"
SDSS_NAMES = ("sloan.sdss.g", "sloan.sdss.r", "sloan.sdss.i", "sloan.sdss.z")
WISE_NAMES = ("wise.W1", "wise.W2", "wise.W3", "wise.W4")


def allwise_errors(ra: float, dec: float) -> list[float]:
    q = ("select top 300 ra,dec,w1mpro,w1sigmpro,w2mpro,w2sigmpro,"
         "w3mpro,w3sigmpro,w4mpro,w4sigmpro from allwise_p3as_psd "
         f"where ra between {ra-0.05:.6f} and {ra+0.05:.6f} "
         f"and dec between {dec-0.05:.6f} and {dec+0.05:.6f}")
    url = TAP + urllib.parse.urlencode({"query": q, "format": "json"})
    with urllib.request.urlopen(url, timeout=120) as fh:
        d = json.load(fh)
    rows = d["VOTABLE"]["RESOURCE_ARRAY"][0]["TABLE"]["DATA"]["TABLEDATA"]
    best = None
    for row in rows:
        try:
            w = [float(row[i]) if row[i] not in ("", None) else 99.0
                 for i in (2, 4, 6, 8)]
            e = [float(row[i]) if row[i] not in ("", None) else np.nan
                 for i in (3, 5, 7, 9)]
            # WISE_MAG from SPALL is Vega; AllWISE w#mpro is Vega.
            # We do not know the target magnitudes here, so choose the source
            # closest to the catalogue position and require finite errors.
            dist = math.hypot(float(row[0]) - ra, float(row[1]) - dec)
            if np.isfinite(e).all() and (best is None or dist < best[0]):
                best = (dist, e, w)
        except Exception:
            continue
    if best is None:
        return [np.nan] * 4
    return best[1]


def main() -> int:
    cache = {}
    for src in iter_sources():
        if src.get("kind") != "sdss":
            continue
        spec = source_files(src, "spectrum")
        if not spec:
            continue
        with fits.open(spec[0], memmap=False) as h:
            sp = h["SPALL"].data
            sf = np.asarray(sp["SPECTROFLUX"][0], float)
            iv = np.asarray(sp["SPECTROFLUX_IVAR"][0], float)
            ra = float(np.asarray(sp["RA"][0]).ravel()[0])
            dec = float(np.asarray(sp["DEC"][0]).ravel()[0])
        # SPECTROFLUX = u,g,r,i,z; use relative errors for g,r,i,z.
        sdss = []
        for i in range(1, 5):
            frac = (1.0 / math.sqrt(iv[i]) / sf[i]) if (sf[i] > 0 and iv[i] > 0) else np.nan
            sdss.append(2.5 / math.log(10.0) * frac if np.isfinite(frac) else np.nan)
        wise = allwise_errors(ra, dec)
        cache[src["key"]] = {"sdss_magerr": sdss, "wise_magerr": wise,
                             "ra": ra, "dec": dec}
        print(src["key"], "SDSS", np.round(sdss, 4), "WISE", np.round(wise, 4))
    out = ROOT / "inputs" / "catalogs" / "photometry_errors.json"
    out.write_text(json.dumps(cache, indent=2) + "\n")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
