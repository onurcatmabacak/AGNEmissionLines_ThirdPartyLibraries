#!/usr/bin/env python3
"""Fetch SDSS DR18 eFEDS (SPIDERS/eROSITA) spectra into a global dataset folder.

The raw spectra live on the SDSS SAS as ``lite`` (coadded, ~0.5 MB/object) or
``full`` (per-exposure, ~5 MB/object) FITS files.  The catalog
``spAll-v6_0_4-eFEDS.fits`` (16 548 rows) maps a target to its spectrum path:

    spectra/<full|lite>/00000p/<MJD>/spec-00000-<MJD>-<CATALOGID:011d>.fits

This script downloads the catalog (once) and a reproducible subset of spectra
into ``$AGN_DATA_DIR`` (default ``~/agn_data``), flat, so every tool can reach
them easily.

Examples
--------
    # 10 good QSOs with S/N > 8
    python pipeline/fetch_efeds.py --n 10 --class QSO --min-sn 8

    # Everything with a specific subclass (careful, can be large)
    python pipeline/fetch_efeds.py --subclass BROADLINE --n 25
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.request
from pathlib import Path

import numpy as np

SAS = "https://dr18.sdss.org/sas/dr18/spectro/boss/redux/eFEDS"
CATALOG_NAME = "spAll-v6_0_4-eFEDS.fits"
DEFAULT_DATA_DIR = Path(os.environ.get("AGN_DATA_DIR", Path.home() / "agn_data"))


def data_dir() -> Path:
    return Path(os.environ.get("AGN_DATA_DIR", DEFAULT_DATA_DIR))


def catalog_path() -> Path:
    return data_dir() / "catalogs" / "efeds" / CATALOG_NAME


def spectra_dir() -> Path:
    return data_dir() / "efeds"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(dest)


def ensure_catalog(force: bool = False) -> Path:
    path = catalog_path()
    if force or not path.exists():
        print(f"Downloading catalog -> {path}")
        _download(f"{SAS}/{CATALOG_NAME}", path)
    return path


def spectrum_path(row, kind: str = "lite") -> Path:
    mjd = int(row["MJD"])
    catid = int(row["CATALOGID"])
    name = f"spec-00000-{mjd:05d}-{catid:011d}.fits"
    return spectra_dir() / name


def spectrum_url(row, kind: str = "lite") -> str:
    mjd = int(row["MJD"])
    catid = int(row["CATALOGID"])
    name = f"spec-00000-{mjd:05d}-{catid:011d}.fits"
    return f"{SAS}/spectra/{kind}/00000p/{mjd:05d}/{name}"


def select(cat, args) -> "object":
    """Apply selection cuts, returning a view of the catalog table."""
    mask = np.ones(len(cat), dtype=bool)
    if args.program:
        mask &= np.isin(np.char.strip(cat["PROGRAMNAME"].astype(str)), args.program)
    if args.zwarning:
        mask &= cat["ZWARNING"] == 0
    if args.min_sn is not None:
        sn = cat["SN_MEDIAN_ALL"]
        mask &= np.isfinite(sn) & (sn >= args.min_sn)
    if args.classes:
        mask &= np.isin(np.char.strip(cat["CLASS"].astype(str)), args.classes)
    if args.subclass:
        sub = np.char.strip(cat["SUBCLASS"].astype(str))
        mask &= np.isin(sub, args.subclass)
    z = cat["Z"]
    if args.z_min is not None:
        mask &= z >= args.z_min
    if args.z_max is not None:
        mask &= z <= args.z_max
    sel = cat[mask]
    # Deterministic order: highest S/N first (stable across runs).
    order = np.argsort(-np.asarray(sel["SN_MEDIAN_ALL"], dtype=float))
    return sel[order]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--n", type=int, default=10, help="number of spectra to download (default 10)")
    p.add_argument("--kind", choices=["lite", "full"], default="lite")
    p.add_argument("--class", dest="classes", nargs="+", default=["QSO"], help="CLASS values to keep")
    p.add_argument("--subclass", nargs="+", default=None, help="SUBCLASS values to keep")
    p.add_argument("--program", nargs="+", default=None, help="PROGRAMNAME values to keep")
    p.add_argument("--min-sn", type=float, default=None, help="minimum SN_MEDIAN_ALL")
    p.add_argument("--z-min", type=float, default=None)
    p.add_argument("--z-max", type=float, default=None)
    p.add_argument("--no-zwarning", dest="zwarning", action="store_false", default=True,
                   help="exclude objects with ZWARNING != 0")
    p.add_argument("--force-catalog", action="store_true")
    p.add_argument("--list-only", action="store_true", help="print the selection, do not download")
    args = p.parse_args(argv)

    from astropy.table import Table

    cat = Table.read(ensure_catalog(force=args.force_catalog), hdu=1)
    sel = select(cat, args)
    if args.n:
        sel = sel[: args.n]

    print(f"Selected {len(sel)} targets (from {len(cat)}).")
    for row in sel:
        sc = np.asarray(row["SN_MEDIAN"], dtype=float)
        print(
            f"  CATALOGID={int(row['CATALOGID']):>11d} MJD={int(row['MJD'])} "
            f"CLASS={str(row['CLASS']).strip():<8s} SUBCLASS={str(row['SUBCLASS']).strip():<12s} "
            f"z={float(row['Z']):.4f} SN={float(row['SN_MEDIAN_ALL']):5.1f} "
            f"sn_arms={np.array2string(sc, precision=1)}"
        )

    if args.list_only:
        return 0

    dest = spectra_dir()
    dest.mkdir(parents=True, exist_ok=True)
    ok = 0
    for row in sel:
        path = spectrum_path(row, args.kind)
        if path.exists():
            print(f"[skip] {path.name} (exists)")
            ok += 1
            continue
        url = spectrum_url(row, args.kind)
        try:
            print(f"[get ] {path.name}")
            _download(url, path)
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"[fail] {path.name}: {exc}", file=sys.stderr)
    print(f"Done. {ok}/{len(sel)} spectra in {dest}")
    return 0 if ok == len(sel) else 1


if __name__ == "__main__":
    raise SystemExit(main())
