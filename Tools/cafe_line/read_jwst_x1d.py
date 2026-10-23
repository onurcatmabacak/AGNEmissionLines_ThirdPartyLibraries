#!/usr/bin/env python3
"""Adapter: JWST/MIRI MRS ``x1d`` FITS -> CAFE 3-column text spectrum.

CAFE (``specmod.read_spec``) accepts a plain text table with columns

    wave_um   flux_Jy   flux_unc_Jy

This module reads the canonical ``EXTRACT1D`` table of JWST/MIRI ``x1d``
products, keeps the real pipeline uncertainties, applies an optional
fractional error floor, removes blanked (DQ != 0) rows, and combines the
short/long detector files into one ascending spectrum.  It also records the
contiguous wavelength segments so the fitter can mask features that fall in
the zeroed detector gaps instead of silently interpolating across them.

The adapter is deliberately conservative:

* ``DQ == 0`` is required by default (``--dq-policy good``).  In the PDS 456
  x1d files the DQ=1 rows are exactly the blanked rows with FLUX=0 and
  FLUX_ERROR=0, i.e. the MRS sub-bands that were not extracted.
* Non-finite values, non-positive errors and duplicated wavelengths are
  removed.
* A fractional error floor (default 1 per cent) is applied because the
  pipeline per-pixel errors are formal statistical errors only and because
  CAFE v1.0.1's ``ErrSpec`` option is not implemented in the released code.
* Binning is optional and off by default.  CAFE derives the line widths from
  the instrument resolving power, so binning the data more coarsely than the
  instrument biases narrow-line fluxes; only use ``--bin-kms`` with care.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import astropy.units as u
from astropy.io import fits

C_KMS = 2.99792458e5


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_table_hdu(hdul: fits.HDUList):
    if "EXTRACT1D" in hdul:
        return hdul["EXTRACT1D"]
    for hdu in hdul:
        if getattr(hdu, "columns", None) is not None and "WAVELENGTH" in hdu.columns.names:
            return hdu
    raise KeyError("no EXTRACT1D/WAVELENGTH table extension in FITS file")


def _column_unit(col, default: str) -> u.Unit:
    unit = getattr(col, "unit", None)
    if unit is None:
        return u.Unit(default)
    try:
        return u.Unit(unit)
    except Exception:
        return u.Unit(default)


def read_x1d(path: Path, dq_policy: str = "good",
             sb_aperture_arcsec2: float | None = None) -> dict:
    """Read one JWST x1d file and return wave/flux/error arrays in um/Jy."""
    path = Path(path)
    with fits.open(path, memmap=False) as hdul:
        hdu = _find_table_hdu(hdul)
        data = hdu.data
        names = list(data.columns.names)
        upper = {n.upper(): n for n in names}

        if "WAVELENGTH" not in upper:
            raise KeyError(f"{path}: no WAVELENGTH column")
        wcol = data[upper["WAVELENGTH"]]
        wunit = _column_unit(wcol, "um")
        wave = np.asarray(wcol, dtype=float)
        try:
            wave = (wave * wunit).to_value(u.um)
        except Exception as exc:
            raise ValueError(f"{path}: cannot convert wavelength unit {wunit} to um") from exc

        if "FLUX" in upper and "FLUX_ERROR" in upper:
            fcol = data[upper["FLUX"]]
            ecol = data[upper["FLUX_ERROR"]]
            funit = _column_unit(fcol, "Jy")
            eunit = _column_unit(ecol, funit)
            flux = (np.asarray(fcol, dtype=float) * funit).to_value(u.Jy)
            err = (np.asarray(ecol, dtype=float) * eunit).to_value(u.Jy)
            flux_kind = "FLUX"
        elif "SURF_BRIGHT" in upper and "SB_ERROR" in upper:
            if not sb_aperture_arcsec2 or sb_aperture_arcsec2 <= 0:
                raise ValueError(
                    f"{path}: only SURF_BRIGHT is present; pass "
                    "--sb-aperture-arcsec2 to convert MJy/sr to Jy"
                )
            fcol = data[upper["SURF_BRIGHT"]]
            ecol = data[upper["SB_ERROR"]]
            funit = _column_unit(fcol, "MJy/sr")
            eunit = _column_unit(ecol, funit)
            omega_sr = float(sb_aperture_arcsec2) * (np.pi / 180.0 / 3600.0) ** 2
            # 1 MJy/sr = 1e6 Jy/sr
            flux = (np.asarray(fcol, dtype=float) * funit).to_value(u.MJy / u.sr) \
                * omega_sr * 1e6
            err = (np.asarray(ecol, dtype=float) * eunit).to_value(u.MJy / u.sr) \
                * omega_sr * 1e6
            flux_kind = "SURF_BRIGHT"
        else:
            raise KeyError(
                f"{path}: neither FLUX/FLUX_ERROR nor SURF_BRIGHT/SB_ERROR "
                "columns are present"
            )

        if "DQ" in upper:
            dq = np.asarray(data[upper["DQ"]], dtype=int)
        else:
            dq = np.zeros(len(wave), dtype=int)
        npix = np.asarray(data[upper["NPIXELS"]], dtype=float) \
            if "NPIXELS" in upper else np.full(len(wave), np.nan)

        header = hdul[0].header
        meta = {
            "path": str(path.resolve()),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "flux_kind": flux_kind,
            "n_rows": int(len(wave)),
            "dq_counts": {int(k): int(v) for k, v in zip(*np.unique(dq, return_counts=True))},
            "n_pixels_median": float(np.nanmedian(npix)) if np.any(np.isfinite(npix)) else None,
            "hdu": hdu.name,
            "header": {
                key: header.get(key)
                for key in ("TARGNAME", "INSTRUME", "DETECTOR", "BAND", "CHANNEL",
                            "SRCTYPE", "DATE-OBS", "PROGRAM", "OBSERVTN",
                            "SLIT_RA", "SLIT_DEC", "EXTR_X", "EXTR_Y")
                if header.get(key) is not None
            },
        }

    finite = np.isfinite(wave) & np.isfinite(flux) & np.isfinite(err)
    positive = err > 0
    nonzero = ~((flux == 0) & (err == 0))
    if dq_policy == "good":
        use = finite & positive & nonzero & (dq == 0)
    elif dq_policy == "all":
        # DQ=1 rows in the PDS 456 x1d products are blanked (flux=0, err=0),
        # so this still removes them; it merely permits other non-zero DQ flags.
        use = finite & positive & nonzero
    else:
        raise ValueError(f"unknown dq_policy: {dq_policy}")

    meta["n_used"] = int(use.sum())
    meta["n_rejected_dq"] = int((finite & positive & nonzero & (dq != 0)).sum())
    meta["n_rejected_nonfinite"] = int((~finite).sum())
    meta["n_rejected_zero_error"] = int((~(positive & nonzero)).sum())
    if use.sum() == 0:
        raise ValueError(f"{path}: no usable rows after DQ/finite/error cuts")

    return {"wave": wave[use], "flux": flux[use], "err": err[use],
            "dq": dq[use], "meta": meta}


def _combine_duplicates(wave: np.ndarray, flux: np.ndarray, err: np.ndarray,
                        tol: float = 1e-6):
    """Inverse-variance combine samples closer than ``tol`` micron."""
    order = np.argsort(wave)
    wave, flux, err = wave[order], flux[order], err[order]
    groups = []
    start = 0
    for i in range(1, len(wave) + 1):
        if i == len(wave) or (wave[i] - wave[i - 1]) > tol:
            groups.append((start, i))
            start = i
    if len(groups) == len(wave):
        return wave, flux, err, 0
    ww, ff, ee = [], [], []
    for a, b in groups:
        wgt = 1.0 / err[a:b] ** 2
        ww.append(np.sum(wave[a:b] * wgt) / np.sum(wgt))
        ff.append(np.sum(flux[a:b] * wgt) / np.sum(wgt))
        ee.append(np.sqrt(1.0 / np.sum(wgt)))
    return np.asarray(ww), np.asarray(ff), np.asarray(ee), int(len(wave) - len(ww))


def find_segments(wave: np.ndarray, gap_factor: float = 10.0,
                  min_gap_um: float = 0.01):
    """Return index pairs ``(start, stop)`` of contiguous wavelength blocks."""
    if len(wave) < 2:
        return [(0, len(wave))]
    dx = np.diff(wave)
    med = float(np.nanmedian(dx))
    threshold = max(gap_factor * med, min_gap_um)
    breaks = np.where(dx > threshold)[0]
    edges = [0] + [int(b) + 1 for b in breaks] + [len(wave)]
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)
            if edges[i + 1] > edges[i]]


def _trim_edges(wave, flux, err, segments, edge_trim: int):
    if edge_trim <= 0:
        return wave, flux, err, segments
    keep = np.zeros(len(wave), dtype=bool)
    new_segments = []
    for a, b in segments:
        aa, bb = a + edge_trim, b - edge_trim
        if bb - aa >= 3:
            keep[aa:bb] = True
            new_segments.append((int(aa), int(bb)))
        else:
            new_segments.append((int(a), int(b)))
            keep[a:b] = True
    return wave[keep], flux[keep], err[keep], new_segments


def _log_bin(wave, flux, err, bin_kms: float):
    """Inverse-variance bin in constant-velocity (log-wavelength) bins."""
    if bin_kms <= 0:
        return wave, flux, err, 0
    dln = float(bin_kms) / C_KMS
    idx = np.floor(np.log(wave) / dln).astype(np.int64)
    # Do not merge across large gaps: include the segment id in the key.
    seg = np.zeros(len(wave), dtype=np.int64)
    for j, (a, b) in enumerate(find_segments(wave)):
        seg[a:b] = j
    key = idx.astype(np.int64) * 1000 + seg
    order = np.argsort(key)
    key, wave, flux, err = key[order], wave[order], flux[order], err[order]
    ww, ff, ee = [], [], []
    start = 0
    for i in range(1, len(key) + 1):
        if i == len(key) or key[i] != key[start]:
            wgt = 1.0 / err[start:i] ** 2
            ww.append(np.sum(wave[start:i] * wgt) / np.sum(wgt))
            ff.append(np.sum(flux[start:i] * wgt) / np.sum(wgt))
            ee.append(np.sqrt(1.0 / np.sum(wgt)))
            start = i
    return (np.asarray(ww), np.asarray(ff), np.asarray(ee),
            int(len(wave) - len(ww)))


def build_spectrum(inputs, z: float, segment: str = "both",
                   dq_policy: str = "good", min_wave: float | None = None,
                   max_wave: float | None = None, error_floor: float = 0.01,
                   bin_kms: float = 0.0, edge_trim: int = 2,
                   gap_factor: float = 10.0, duplicate_tol_um: float = 1e-6,
                   sb_aperture_arcsec2: float | None = None) -> dict:
    """Read and combine one or more x1d files into a CAFE-ready spectrum."""
    paths = [Path(p) for p in inputs]
    if len(paths) == 1 and paths[0].is_dir():
        paths = sorted(paths[0].glob("*_x1d.fits"))
    if segment == "short":
        paths = [p for p in paths if "mirifushort" in p.name.lower()]
    elif segment == "long":
        paths = [p for p in paths if "mirifulong" in p.name.lower()]
    elif segment != "both":
        raise ValueError(f"unknown segment: {segment}")
    paths = [p for p in paths if p.is_file()]
    if not paths:
        raise FileNotFoundError(
            f"no *_x1d.fits inputs found (segment={segment}, inputs={inputs})"
        )

    parts = [read_x1d(p, dq_policy=dq_policy,
                      sb_aperture_arcsec2=sb_aperture_arcsec2) for p in paths]
    wave = np.concatenate([p["wave"] for p in parts])
    flux = np.concatenate([p["flux"] for p in parts])
    err = np.concatenate([p["err"] for p in parts])
    wave, flux, err, n_duplicates = _combine_duplicates(wave, flux, err,
                                                        tol=duplicate_tol_um)

    if min_wave is not None:
        m = wave >= float(min_wave)
        wave, flux, err = wave[m], flux[m], err[m]
    if max_wave is not None:
        m = wave <= float(max_wave)
        wave, flux, err = wave[m], flux[m], err[m]
    if len(wave) < 10:
        raise ValueError("fewer than 10 usable spectral samples after trimming")

    segments_before = find_segments(wave, gap_factor=gap_factor)
    wave, flux, err, segments = _trim_edges(wave, flux, err, segments_before,
                                            edge_trim=edge_trim)
    n_binned = 0
    if bin_kms and bin_kms > 0:
        wave, flux, err, n_binned = _log_bin(wave, flux, err, bin_kms)
        segments = find_segments(wave, gap_factor=gap_factor)

    # Error floor (CAFE v1.0.1's ErrSpec is present in the .cafe file but is
    # not applied anywhere in the released code).
    floor = np.maximum(np.abs(flux) * float(error_floor), 0.0) \
        if error_floor and error_floor > 0 else np.zeros_like(err)
    err_floored = np.maximum(err, floor)
    n_floor = int((err_floored > err).sum())

    good = np.isfinite(wave) & np.isfinite(flux) & np.isfinite(err_floored) \
        & (err_floored > 0)
    wave, flux, err = wave[good], flux[good], err_floored[good]
    segments = find_segments(wave, gap_factor=gap_factor)

    meta = {
        "inputs": [p["meta"] for p in parts],
        "z": float(z),
        "segment": segment,
        "dq_policy": dq_policy,
        "min_wave_um": float(np.min(wave)),
        "max_wave_um": float(np.max(wave)),
        "n_pixels": int(len(wave)),
        "n_duplicates_combined": int(n_duplicates),
        "n_binned": int(n_binned),
        "n_error_floor_applied": int(n_floor),
        "error_floor": float(error_floor),
        "bin_kms": float(bin_kms),
        "edge_trim": int(edge_trim),
        "gap_factor": float(gap_factor),
        "segments_um": [
            {"start": float(wave[a]), "stop": float(wave[b - 1]), "n": int(b - a)}
            for a, b in segments
        ],
        "segments_index": [[int(a), int(b)] for a, b in segments],
        "median_error_jy": float(np.median(err)),
        "median_flux_jy": float(np.median(flux)),
        "median_snr": float(np.median(flux / err)),
    }
    return {"wave": wave, "flux": flux, "err": err,
            "segments": segments, "meta": meta}


def write_cafe_text(path: Path, wave, flux, err, header: str | None = None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if header is None:
        header = ("CAFE input: observed wavelength [um], flux density [Jy], "
                  "1-sigma uncertainty [Jy]")
    np.savetxt(path, np.column_stack([wave, flux, err]), fmt="%.10g",
               header=header)
    return path


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", nargs="+", required=True,
                   help="x1d FITS file(s) or a directory containing *_x1d.fits")
    p.add_argument("--output", required=True, type=Path,
                   help="output 3-column text spectrum")
    p.add_argument("--z", required=True, type=float)
    p.add_argument("--segment", choices=["both", "short", "long"], default="both")
    p.add_argument("--dq-policy", choices=["good", "all"], default="good")
    p.add_argument("--min-wave", type=float, default=None)
    p.add_argument("--max-wave", type=float, default=None)
    p.add_argument("--error-floor", type=float, default=0.01,
                   help="fractional error floor: err=max(err, floor*|flux|)")
    p.add_argument("--bin-kms", type=float, default=0.0,
                   help="optional constant-velocity binning (0 = keep native)")
    p.add_argument("--edge-trim", type=int, default=2,
                   help="pixels removed at each contiguous-segment edge")
    p.add_argument("--gap-factor", type=float, default=10.0)
    p.add_argument("--sb-aperture-arcsec2", type=float, default=None)
    p.add_argument("--meta-json", type=Path, default=None)
    args = p.parse_args(argv)

    spec = build_spectrum(
        args.input, z=args.z, segment=args.segment, dq_policy=args.dq_policy,
        min_wave=args.min_wave, max_wave=args.max_wave,
        error_floor=args.error_floor, bin_kms=args.bin_kms,
        edge_trim=args.edge_trim, gap_factor=args.gap_factor,
        sb_aperture_arcsec2=args.sb_aperture_arcsec2,
    )
    write_cafe_text(args.output, spec["wave"], spec["flux"], spec["err"],
                    header=(f"CAFE input from JWST x1d; z={args.z}; "
                            f"segment={args.segment}; dq={args.dq_policy}; "
                            "columns: wave_um flux_Jy flux_unc_Jy"))
    if args.meta_json:
        args.meta_json.parent.mkdir(parents=True, exist_ok=True)
        args.meta_json.write_text(json.dumps(spec["meta"], indent=2,
                                             default=float) + "\n")
    print(f"[read_jwst_x1d] wrote {args.output} "
          f"({len(spec['wave'])} pixels, "
          f"{spec['meta']['min_wave_um']:.3f}-{spec['meta']['max_wave_um']:.3f} um, "
          f"{len(spec['meta']['segments_um'])} segments)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
