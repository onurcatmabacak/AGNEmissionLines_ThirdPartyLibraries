#!/usr/bin/env python3
"""CASA 6 `specfit` on a spectral-line FITS cube.

`casatasks.specfit` fits a polynomial baseline plus N Gaussians to the spectrum
in a box of a CASA image, using the same task the ALMA/VLA community uses.  This
adapter converts the cube with `importfits`, runs `specfit`, and writes the
components in the repository line-table convention so the result can be compared
against `radio_line` (pyspeckit) and `submm_line` (McFine) on identical data.

`specfit` returns a plain dict; the Gaussian parameters live under ``gs`` as
``amp``/``center``/``fwhm``/``integral`` plus ``*Err`` arrays in the cube's own
spectral unit (``xUnit`` is ``km/s`` for a VRAD cube, ``Hz`` for a FREQ cube).
Velocities are derived with ``nu_obs = nu_rest / (1 + z)``.
"""
from __future__ import annotations

import argparse
import csv
import os
import json
import sys
from pathlib import Path

import numpy as np

C_KMS = 299792.458
FWHM_TO_SIGMA = 2.0 * np.sqrt(2.0 * np.log(2.0))


def log(msg: str) -> None:
    print(f"[casa_specfit] {msg}", flush=True)


def find_cube(path: Path) -> Path:
    """A FITS cube: a file, or the largest *.fits file under a directory."""
    if path.is_file():
        return path
    cands = sorted(
        (p for p in path.rglob("*.fits*") if p.is_file()),
        key=lambda p: p.stat().st_size,
        reverse=True,
    )
    if not cands:
        raise SystemExit(f"no FITS file under {path}")
    return cands[0]


def read_axes(src: Path):
    """Return (shape, xunit_kind, rest_freq_ghz, nchan) for the cube."""
    from astropy.io import fits

    with fits.open(src, memmap=True) as hdul:
        # Real ALMA cubes carry a Stokes axis, so accept ndim >= 3 and let
        # squeeze() drop the singleton ones (a view on the memmap, not a copy).
        hdu = next(
            (h for h in hdul if h.data is not None and np.asarray(h.data).ndim >= 3),
            None,
        )
        if hdu is None:
            raise SystemExit("no spectral cube found (need >= 3 dims)")
        hdr = hdu.header
        if np.squeeze(np.asarray(hdu.data)).ndim != 3:
            raise SystemExit(f"expected 3 dims after squeeze, got {np.squeeze(np.asarray(hdu.data)).shape}")
        rest = hdr.get("RESTFRQ") or hdr.get("RESTFREQ")
        rest_ghz = float(rest) / 1e9 if rest else None
        return tuple(hdu.data.shape), rest_ghz


def pick_box(src: Path, half: int) -> str:
    """Box around the brightest pixel of the channel-mean map."""
    from astropy.io import fits

    with fits.open(src, memmap=True) as hdul:
        hdu = next(
            h for h in hdul if h.data is not None and np.asarray(h.data).ndim >= 3
        )
        data = np.squeeze(hdu.data)
        nchan = data.shape[0]
        # Collapse in chunks so a multi-GB cube never lands fully in memory.
        acc = np.zeros(data.shape[1:], dtype=np.float64)
        step = max(1, int(2e7 // max(1, data[0].size)))
        for i in range(0, nchan, step):
            acc += np.nanmean(data[i:i + step], axis=0)
        y, x = np.unravel_index(np.nanargmax(acc), acc.shape)
    return f"{max(0, x - half)},{max(0, y - half)},{x + half},{y + half}", int(x), int(y)


def velocity_kms(center: float, xunit: str, rest_ghz: float | None, z: float) -> float | None:
    """Convert specfit's centre to a velocity in km/s."""
    unit = (xunit or "").strip().lower()
    if unit in ("km/s", "km s-1", "kms"):
        return float(center)
    if rest_ghz is None:
        return None
    # specfit reports the spectral axis in Hz for FREQ cubes; accept GHz too.
    freq_ghz = float(center) / 1e9 if abs(float(center)) > 1e6 else float(center)
    nu_rest_obs = rest_ghz / (1.0 + z)
    return float(C_KMS * (nu_rest_obs - freq_ghz) / freq_ghz)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=Path("/app/input"))
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("/app/config/config.json"))
    ap.add_argument("--ncomp", type=int, default=None)
    ap.add_argument("--z", type=float, default=None)
    ap.add_argument("--source-key", default=None)
    args = ap.parse_args(argv)

    cfg = json.loads(args.config.read_text()) if args.config.exists() else {}
    ncomp = int(args.ncomp or cfg.get("n_components", 1))
    z = float(args.z if args.z is not None else cfg.get("redshift", 0.0))
    poly = int(cfg.get("baseline_order", 0))
    outdir = args.output
    outdir.mkdir(parents=True, exist_ok=True)

    src = find_cube(args.input)
    log(f"cube: {src}")
    shape, rest_ghz = read_axes(src)
    log(f"shape {shape}, rest {rest_ghz} GHz, z={z}")

    ensure_measures()
    from casatasks import importfits, specfit

    # specfit works on a CASA image, not a FITS file.  Write it to scratch, not
    # the output dir: importfits of a real ALMA cube produces a multi-GB image
    # directory that must not end up in a committed product.
    work = Path(os.environ.get("CASA_WORK", "/tmp/casa_work"))
    work.mkdir(parents=True, exist_ok=True)
    imname = str(work / "cube.im")
    if not Path(imname).exists():
        importfits(fitsimage=str(src), imagename=imname, overwrite=True)

    box = cfg.get("box")
    if not box:
        box, x, y = pick_box(src, int(cfg.get("box_half_width", 1)))
        log(f"peak pixel x={x} y={y}, box={box}")
    else:
        log(f"box from config: {box}")

    res = specfit(
        imagename=imname,
        box=box,
        poly=poly,
        ngauss=ncomp,
        estimates="",
        multifit=False,
        wantreturn=True,
        logresults=True,
        logfile=str(outdir / "casa_specfit.log"),
    )

    xunit = str(np.asarray(res["xUnit"]).ravel()[0]) if "xUnit" in res else ""
    yunit = str(np.asarray(res["yUnit"]).ravel()[0]) if "yUnit" in res else ""
    converged = bool(np.all(res.get("converged", [[[True]]])))
    succeeded = bool(np.all(res.get("succeeded", [[[True]]])))
    gs = res.get("gs", {})
    log(f"xUnit={xunit} yUnit={yunit} converged={converged} succeeded={succeeded}")

    rows = []
    amp = np.atleast_1d(np.asarray(gs.get("amp", []), dtype=float).ravel()) if "amp" in gs else []
    centre = np.atleast_1d(np.asarray(gs.get("center", []), dtype=float).ravel()) if "center" in gs else []
    fwhm = np.atleast_1d(np.asarray(gs.get("fwhm", []), dtype=float).ravel()) if "fwhm" in gs else []
    integ = np.atleast_1d(np.asarray(gs.get("integral", []), dtype=float).ravel()) if "integral" in gs else []
    ampe = np.atleast_1d(np.asarray(gs.get("ampErr", np.zeros_like(amp)), dtype=float).ravel())
    cente = np.atleast_1d(np.asarray(gs.get("centerErr", np.zeros_like(centre)), dtype=float).ravel())
    fwhme = np.atleast_1d(np.asarray(gs.get("fwhmErr", np.zeros_like(fwhm)), dtype=float).ravel())
    inte = np.atleast_1d(np.asarray(gs.get("integralErr", np.zeros_like(integ)), dtype=float).ravel())

    from line_snr import snr_row

    for i in range(len(amp)):
        vel = velocity_kms(centre[i], xunit, rest_ghz, z)
        _c = abs(float(centre[i]))
        freq_centre_ghz = _c / 1e9 if _c > 1e6 else _c
        width_kms = float(fwhm[i]) if xunit.strip().lower().startswith("km") else None
        # specfit works in the cube's own spectral unit; for the integrated S/N
        # we need a km/s grid, so build one from the fitted parameters.
        if width_kms is None and vel is not None and rest_ghz:
            nu_rest_obs = rest_ghz / (1.0 + z)
            width_kms = abs(float(fwhm[i])) * C_KMS / abs(freq_centre_ghz or nu_rest_obs)
        npts = 64
        if width_kms and width_kms > 0:
            vel_grid = np.linspace(vel - 3 * width_kms, vel + 3 * width_kms, npts)
            sig = width_kms / FWHM_TO_SIGMA
            single = float(amp[i]) * np.exp(-0.5 * ((vel_grid - vel) / sig) ** 2)
        else:
            vel_grid, single = None, None
        row = {
            "line": cfg.get("line", "casa"),
            "component": f"c{i + 1}",
            "centre": float(centre[i]),
            "centre_err": float(cente[i]),
            "x_unit": xunit,
            "velocity_kms": "" if vel is None else float(vel),
            "fwhm_kms": "" if width_kms is None else width_kms,
            "fwhm": float(fwhm[i]),
            "fwhm_err": float(fwhme[i]),
            "amplitude": float(amp[i]),
            "amplitude_err": float(ampe[i]),
            "integral": float(integ[i]),
            "integral_err": float(inte[i]),
        }
        # specfit reports no residual spectrum, so rms is not available; the
        # primary peak statistic (amp / ampErr) and the integrated significance
        # from CASA's own integral error are what this tool can supply.
        row.update(snr_row(peak=float(amp[i]),
                           sigma_peak=float(ampe[i]) if ampe[i] > 0 else float("nan"),
                           model=single, vel_kms=vel_grid,
                           resid=None,
                           snr_min=float(cfg.get("snr_min", 3.0)),
                           at_bound=False,
                           # specfit keeps no residual spectrum, so the rms-based
                           # integrated S/N is unavailable; CASA's own
                           # integral/integralErr is the same quantity from its
                           # covariance, and it is what the other tools'
                           # snr_integrated is compared against.
                           snr_integrated_override=(float(abs(integ[i]) / inte[i])
                                                    if inte[i] > 0 else None)))
        rows.append(row)

    cols = ["line", "component", "centre", "centre_err", "x_unit", "velocity_kms",
            "fwhm_kms", "fwhm", "fwhm_err", "amplitude", "amplitude_err",
            "integral", "integral_err", "snr", "snr_integrated", "snr_rms",
            "width_at_bound", "detected"]
    with open(outdir / "casa_lines.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    (outdir / "run.json").write_text(json.dumps({
        "tool": "casa_specfit",
        "status": "ok" if (converged and succeeded) else "not_converged",
        "source_key": args.source_key or src.stem,
        "cube": str(src),
        "shape": list(shape),
        "box": box,
        "n_components": ncomp,
        "baseline_order": poly,
        "redshift": z,
        "rest_frequency_ghz": rest_ghz,
        "x_unit": xunit,
        "y_unit": yunit,
        "converged": converged,
        "succeeded": succeeded,
        "casa_version": _casa_version(),
    }, indent=2) + "\n")
    log(f"wrote {len(rows)} component(s) to {outdir / 'casa_lines.csv'}")
    return 0 if (converged and succeeded) else 1


def ensure_measures() -> None:
    """Expose the baked-in measures tables to a non-root HOME.

    The image installs casarundata under /opt/casa/data, but the runner drops to
    the calling uid (``--user``) with HOME pointing at writable scratch, and CASA
    looks for ~/.casa/data.  Symlink it rather than copying 350 MB.
    """
    baked = Path("/opt/casa/data")
    if not baked.is_dir():
        return
    target = Path(os.path.expanduser("~")) / ".casa" / "data"
    if target.exists() or target.is_symlink():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.symlink_to(baked)
    except OSError:
        pass


def _casa_version() -> str:
    try:
        import casatools

        return str(casatools.version_string())
    except Exception:
        return "unknown"


if __name__ == "__main__":
    sys.exit(main())
