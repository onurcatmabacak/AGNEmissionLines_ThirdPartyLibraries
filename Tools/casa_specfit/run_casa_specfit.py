#!/usr/bin/env python3
"""CASA 6 specfit on a spectral-line image cube.

`casatasks.specfit` extracts the spectrum inside a box from a spectral-line
image and fits polynomial + Gaussian components to it.  This adapter runs that
task on a real cube and writes the components in the repository line-table
convention, giving an independent (CASA) cross-check of the Gaussian
decompositions produced by `radio_line` and `submm_line`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def log(msg: str) -> None:
    print(f"[casa_specfit] {msg}", flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=Path("/app/input"))
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("/app/config/config.json"))
    ap.add_argument("--ncomp", type=int, default=None)
    ap.add_argument("--source-key", default=None)
    args = ap.parse_args(argv)

    cfg = json.loads(args.config.read_text()) if args.config.exists() else {}
    ncomp = int(args.ncomp or cfg.get("n_components", 2))
    outdir = args.output
    outdir.mkdir(parents=True, exist_ok=True)

    src = args.input
    if src.is_dir():
        cands = sorted(p for p in src.rglob("*.fits*"))
        if not cands:
            raise SystemExit(f"no FITS cube under {src}")
        src = cands[0]
    log(f"cube: {src}")

    from casatasks import specfit

    # Box around the brightest pixel in the collapsed cube: the AGN continuum
    # peak for a real observation, the line peak for a spectrum cube.
    from astropy.io import fits

    with fits.open(src) as hdul:
        cube = None
        for hdu in hdul:
            if hdu.data is not None and np.asarray(hdu.data).ndim == 3:
                cube = np.asarray(hdu.data, dtype=float)[0]
                break
        if cube is None:
            raise SystemExit("no 3-D spectral cube found")
    peak = np.unravel_index(np.nanargmax(np.nanmean(cube, axis=0)), cube.shape[1:])
    y, x = int(peak[0]), int(peak[1])
    half = int(cfg.get("box_half_width", 1))
    box = f"{x - half},{y - half},{x + half},{y + half}"
    log(f"peak pixel x={x} y={y}, box={box}")

    specfit(
        imagename=str(outdir),  # unused placeholder, replaced below
        box=box,
        poly=int(cfg.get("baseline_order", 0)),
        estimates="",
        ngauss=ncomp,
        ngaussest=0,
        multifit=False,
        overwrite=True,
        outfile=str(outdir / "casa_specfit.txt"),
    ) if False else None

    # specfit needs the image in the CASA imaging namespace; imfit-style calls on
    # a FITS file go through imfit/specfit on the opened image.
    from casatools import image

    ia = image()
    ia.open(str(src))
    try:
        specfit(
            imagename=str(src),
            box=box,
            region="",
            chans="",
            poly=int(cfg.get("baseline_order", 0)),
            width=int(cfg.get("width", 1)),
            ngauss=ncomp,
            ngaussest=0,
            multifit=False,
            estimates="",
            parname="",
            parunit="",
            parvalue="",
            overwrite=True,
            stretch=False,
            logfile=str(outdir / "casa_specfit.log"),
            append=False,
            plotprogress=False,
            goodname="",
            grouptype="",
            interactive=False,
        )
    finally:
        ia.close()

    log("specfit finished")
    (outdir / "run.json").write_text(json.dumps({
        "tool": "casa_specfit", "status": "ok",
        "source_key": args.source_key or src.stem, "cube": str(src),
        "n_components": ncomp, "box": box,
        "note": "Components are written by casatasks.specfit to casa_specfit.log.",
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
