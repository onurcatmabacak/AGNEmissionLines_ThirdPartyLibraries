#!/usr/bin/env python3
"""Spatially resolved spectral-line fitting on a 3-D cube.

Every other tool in this repository fits one spectrum extracted from one box of a
cube.  This one fits the cube: per-spaxel continuum removal, moment maps, an
aperture spectrum with Gaussian components, and line-ratio maps.  That is the
difference between "line flux" and "kinematics", and it is what the JBST MIRI MRS
and ALMA products in ``inputs/`` were bought for.

Input is any FITS cube with a celestial + spectral WCS, including JWST ``s3d``
files whose spectral axis is a ``-TAB`` table (astropy needs ``fobj=hdul`` for
those).  Intensity is expected in surface-brightness units (``MJy/sr`` for MIRI);
line fluxes are converted to W/m^2 using the spaxel solid angle, so the maps and
the ratios are physically meaningful.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

C_KMS = 299792.458
C_UM_PER_S = 2.99792458e14       # speed of light in um/s
JY_WM2 = 1e-26                   # 1 Jy in W m^-2 Hz^-1


def log(msg: str) -> None:
    print(f"[cube_lines] {msg}", flush=True)


def load_cube(path: Path):
    """Return (data, err, dq, wcs, rest-free wavelength array in um)."""
    from astropy.io import fits
    from astropy.wcs import WCS

    # JWST s3d stores the science array as unsigned int with BSCALE/BZERO, which
    # astropy refuses to memory-map.  Detect that from the header (cheap) instead
    # of catching the error after the array is touched.
    # (MIRI s3d puts the BZERO on the int16 DQ extension, not on SCI, so every
    # image HDU has to be checked.)
    with fits.open(path, memmap=True) as probe:
        scaled = any(
            ("BSCALE" in h.header) or ("BZERO" in h.header) or ("BLANK" in h.header)
            for h in probe if getattr(h, "is_image", False)
        )
    hdul = fits.open(path, memmap=not scaled)
    sci = hdul["SCI"] if "SCI" in hdul else hdul[0]
    data = np.asarray(sci.data, dtype=np.float64)
    err = np.asarray(hdul["ERR"].data, dtype=np.float64) if "ERR" in hdul else None
    dq = np.asarray(hdul["DQ"].data) if "DQ" in hdul else None
    # ALMA products carry a Stokes axis (1, nchan, ny, nx); drop singleton axes
    # before the moment analysis.  The WCS keeps its original dimensionality,
    # which is fine because we only use .spectral and .celestial.
    if data.ndim != 3:
        data = np.squeeze(data)
        if err is not None:
            err = np.squeeze(err)
        if dq is not None:
            dq = np.squeeze(dq)
    if data.ndim != 3:
        raise SystemExit(f"expected a 3-D cube, got shape {data.shape}")
    try:
        wcs = WCS(sci.header, fobj=hdul)      # -TAB needs the HDUList
    except Exception:
        wcs = WCS(sci.header)
    wave = wcs.spectral.pixel_to_world(np.arange(data.shape[0]))
    wave = np.asarray([w.to_value("um") for w in np.atleast_1d(wave)], dtype=float)
    return data, err, dq, wcs, wave, sci.header


def spaxel_scale_sr(wcs) -> float:
    """Solid angle of one spaxel in sr (small-angle approximation).

    Takes the already-built WCS: rebuilding one from the header fails on cubes
    with a -TAB spectral axis (MIRI s3d), which need the WCS-TABLE HDU.
    """
    w = wcs.celestial
    cd = np.abs(np.linalg.det(w.pixel_scale_matrix))
    return float(cd * (np.pi / 180.0) ** 2)


def continuum_model(wave, spec, line_um, half_kms, order=1, win=None):
    """Fit a low-order continuum in the line-free windows around a line.

    ``win`` is (lo, hi) in km/s; it must lie *inside* the extraction band, since
    the band is what we extract.  Defaults to the outer 55-100 % of the band.
    """
    v = C_KMS * (wave - line_um) / line_um
    lo, hi = win if win else (0.55 * half_kms, half_kms)
    mask = (np.abs(v) >= lo) & (np.abs(v) <= hi)
    if mask.sum() < order + 2:
        return np.zeros_like(spec), np.zeros_like(spec, dtype=bool)
    good = mask & np.isfinite(spec)
    if good.sum() < order + 2:
        return np.zeros_like(spec), good
    coef = np.polyfit(v[good], spec[good], order)
    return np.polyval(coef, v), good


def fit_component(v, flux, err, v0_guess, w_lo, w_hi, snr_min, polarity="emission"):
    """Multi-start Gaussian fit on one aperture spectrum."""
    import scipy.optimize as opt

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from line_snr import snr_row

    good = np.isfinite(flux) & np.isfinite(err) & (err > 0)
    if good.sum() < 8:
        log(f"  fit skipped: only {int(good.sum())} usable channels")
        return None
    v, flux, err = v[good], flux[good], err[good]
    amp0 = float(np.nanmax(flux))
    starts = []
    for w0 in (w_lo * 2, np.sqrt(w_lo * w_hi), w_hi * 0.5):
        for dv in (-0.5 * w0, 0.0, 0.5 * w0):
            starts.append([amp0, v0_guess + dv, w0 / 2.3548])

    def model(vv, a, c, s):
        return a * np.exp(-0.5 * ((vv - c) / s) ** 2)

    best, errs = None, "none"
    for p0 in starts:
        try:
            p, cov = opt.curve_fit(model, v, flux, p0=p0, sigma=err, absolute_sigma=True,
                                   bounds=([0.0 if polarity == "emission" else -np.inf,
                                            v0_guess - 4 * w_hi, w_lo / 4],
                                           [np.inf if polarity == "emission" else 0.0,
                                            v0_guess + 4 * w_hi, w_hi * 2]),
                                   maxfev=20000)
        except Exception as exc:
            errs = str(exc)[:80]
            continue
        resid = flux - model(v, *p)
        chi2 = float(np.nansum((resid / err) ** 2))
        if best is None or chi2 < best[0]:
            best = (chi2, p, cov, resid, v, flux)
    if best is None:
        log(f"  fit failed on all {len(starts)} starts (last error: {errs})")
        return None
    chi2, p, cov, resid, v, flux = best
    dof = max(len(v) - 3, 1)
    perr = np.sqrt(np.diag(cov)) if cov is not None and np.all(np.diag(cov) >= 0) else np.full(3, np.nan)
    at_bound = bool(abs(abs(p[2]) - w_hi / 2.3548) < 1e-3 * w_hi)
    row = {
        "centre_kms": float(p[1]),
        "fwhm_kms": float(abs(p[2]) * 2.3548),
        "amplitude": float(p[0]),
        "amplitude_err": float(perr[0]),
        "chi2nu": chi2 / dof,
    }
    row.update(snr_row(peak=p[0], sigma_peak=perr[0], model=model(v, *p),
                       vel_kms=v, resid=resid, snr_min=snr_min, at_bound=at_bound))
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--z", type=float, default=None)
    ap.add_argument("--source-key", default=None)
    ap.add_argument("--plot", action="store_true")
    args = ap.parse_args(argv)

    cfg = json.loads(args.config.read_text()) if args.config and args.config.exists() else {}
    z = float(args.z if args.z is not None else cfg.get("redshift", 0.0))
    lines = cfg.get("lines", [])
    if not lines:
        raise SystemExit("config needs a 'lines' list of {name, rest_um}")
    half = float(cfg.get("half_width_kms", 900.0))
    snr_min = float(cfg.get("snr_min", 3.0))
    ap_radius = int(cfg.get("aperture_radius_px", 1))
    polarity = str(cfg.get("polarity", "emission")).lower()
    order = int(cfg.get("continuum_order", 1))
    cw = cfg.get("continuum_window_kms")
    cont_win = (float(cw[0]), float(cw[1])) if cw else None

    outdir = args.output
    outdir.mkdir(parents=True, exist_ok=True)
    data, err, dq, wcs, wave, header = load_cube(args.input)
    omega = spaxel_scale_sr(wcs)
    log(f"cube {data.shape}, {wave.min():.3f}-{wave.max():.3f} um, BUNIT={header.get('BUNIT')}, "
        f"spaxel solid angle {omega:.3e} sr, z={z}")

    if dq is not None:
        bad = dq != 0
        data = np.where(bad, np.nan, data)
        if err is not None:
            err = np.where(bad, np.nan, err)
    if err is None:
        err = np.full_like(data, np.nan)

    # Optional crop: ALMA cubes are 2646x2646 spaxels, of which only a small
    # region carries the line; cropping keeps the moment maps meaningful and
    # the run fast.
    crop = cfg.get("crop")
    if crop:
        cy, cx = (int(v) for v in crop["centre_yx"])
        size = int(crop["size"])
        h = size // 2
        ys, ye = max(0, cy - h), min(data.shape[1], cy + h)
        xs, xe = max(0, cx - h), min(data.shape[2], cx + h)
        data, err = data[:, ys:ye, xs:xe], err[:, ys:ye, xs:xe]
        log(f"cropped to y[{ys}:{ye}] x[{xs}:{xe}] -> {data.shape}")

    dlam = float(np.median(np.abs(np.diff(wave))))
    rows, maps = [], {}
    for line in lines:
        name = line["name"]
        # accept either a wavelength or a rest frequency (mm/sub-mm are usually
        # quoted in GHz)
        # lambda[um] = c[um/s] / nu[Hz]
        rest_um = (float(line["rest_um"]) if "rest_um" in line
                   else C_UM_PER_S / (float(line["rest_ghz"]) * 1e9))
        obs_um = rest_um * (1.0 + z)
        band = np.abs(C_KMS * (wave - obs_um) / obs_um) <= half
        if band.sum() < 8:
            log(f"{name}: not covered ({obs_um:.3f} um)")
            rows.append({"line": name, "status": "not_covered", "rest_um": rest_um, "obs_um": obs_um})
            continue

        sub = data[band]
        v = C_KMS * (wave[band] - obs_um) / obs_um
        # per-spaxel continuum
        flat = sub.reshape(sub.shape[0], -1)
        # Continuum for every spaxel at once: the line-free mask is common, so a
        # single pseudo-inverse replaces a per-spaxel loop (ALMA cubes have
        # millions of spaxels).
        vv = C_KMS * (wave[band] - obs_um) / obs_um
        lo, hi = cont_win if cont_win else (0.55 * half, half)
        cmask = (np.abs(vv) >= lo) & (np.abs(vv) <= hi)
        if cmask.sum() >= order + 2:
            design = np.vstack([vv[cmask] ** k for k in range(order + 1)]).T
            pinv = np.linalg.pinv(design)
            coef = pinv @ flat[cmask]
            cont = np.vstack([vv ** k for k in range(order + 1)]).T @ coef
        else:
            cont = np.zeros_like(flat)
        subc = flat - cont
        # channel widths: MRS wavelength spacing is not uniform, so integrate
        # with the per-channel width rather than a single median step
        dlam_vec = np.gradient(wave[band])
        m0 = np.nansum(subc * dlam_vec[:, None], axis=0)
        w2 = np.nansum(subc * v[:, None] ** 2, axis=0)
        wsum = np.nansum(subc, axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            m1 = np.nansum(subc * v[:, None], axis=0) / wsum
            m2 = np.sqrt(np.maximum(w2 / wsum - m1 ** 2, 0.0))
        # noise from the continuum window (the only line-free part of the band,
        # so it must be the same mask the continuum fit used)
        rms_map = np.nanstd(np.where(cmask[:, None], subc, np.nan), axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            snr_map = np.nanmax(np.abs(subc), axis=0) / rms_map

        # flux in W/m^2.  Two conventions have to be told apart: surface
        # brightness (MJy/sr, MIRI) needs the spaxel solid angle, while ALMA
        # delivers Jy/beam per spaxel already.  Either way dnu = c dlam / lam^2.
        bunit = str(header.get("BUNIT", "")).lower().replace(" ", "")
        per_sr = "/sr" in bunit
        jy_scale = (1e6 * omega) if per_sr else 1.0          # -> Jy per spaxel
        conv = m0 * (jy_scale * JY_WM2) * (C_UM_PER_S / obs_um ** 2)
        flux_map = conv.reshape(sub.shape[1:])
        maps[f"{name}_flux"] = flux_map
        maps[f"{name}_vel"] = m1.reshape(sub.shape[1:])
        maps[f"{name}_disp"] = m2.reshape(sub.shape[1:])
        maps[f"{name}_snr"] = snr_map.reshape(sub.shape[1:])

        # aperture spectrum at the brightest spaxel
        # Pick the aperture by *signal-to-noise*, not raw flux: on a real cube the
        # highest integrated flux is usually a noise spike at the field edge.
        from scipy.ndimage import uniform_filter
        snr_cube = uniform_filter(np.nan_to_num(maps[f"{name}_snr"], nan=0.0), size=3)
        pick = (np.nanargmax(snr_cube) if polarity == "emission" else np.nanargmin(snr_cube))
        yx = np.unravel_index(pick, flux_map.shape)
        sl = tuple(slice(max(0, i - ap_radius), i + ap_radius + 1) for i in yx)
        yy, xx = np.indices(flux_map.shape)
        sel = (np.abs(yy - yx[0]) <= ap_radius) & (np.abs(xx - yx[1]) <= ap_radius)
        idx = np.flatnonzero(sel.ravel())
        spec = np.nanmean(flat[:, idx], axis=1)
        espe = np.nanmean(err[band].reshape(band.sum(), -1)[:, idx], axis=1)
        cont_ap, cmask = continuum_model(wave[band], spec, obs_um, half, order=order, win=cont_win)
        if not np.any(cmask):                     # no usable continuum window
            cont_ap = np.full_like(spec, np.nanmedian(spec[~band] if (~band).any() else spec))
        good_e = np.isfinite(espe) & (espe > 0)
        if good_e.sum() < 8:
            rms_e = float(np.nanstd(spec - cont_ap))
            espe = np.full_like(spec, rms_e)
        fit = fit_component(v, spec - cont_ap, espe, 0.0, 100.0, 2000.0, snr_min,
                            polarity=polarity)
        row = {"line": name, "status": "ok", "rest_um": rest_um, "obs_um": obs_um,
               "spaxel_y": int(yx[0]), "spaxel_x": int(yx[1]),
               "flux_wm2": float(np.nansum(flux_map[sl])),
               "n_spaxels_detected": int(np.count_nonzero(maps[f"{name}_snr"] >= snr_min))}
        if fit:
            row.update(fit)
        else:
            row["status"] = "fit_failed"
        rows.append(row)
        log(f"{name}: obs {obs_um:.3f} um, aperture spaxel {yx}, "
            f"flux {row.get('flux_wm2', float('nan')):.3e} W/m^2, "
            + (f"FWHM {fit['fwhm_kms']:.0f} km/s, snr_int {fit['snr_integrated']:.1f}"
               if fit else "fit failed"))

    # line ratios between every detected pair
    ratio_rows = []
    det = {r["line"]: r for r in rows if r.get("status") == "ok" and r.get("flux_wm2")}
    names = list(det)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = det[names[i]], det[names[j]]
            if b["flux_wm2"]:
                ratio_rows.append({"ratio": f"{names[i]}/{names[j]}",
                                   "value": a["flux_wm2"] / b["flux_wm2"]})

    cols = ["line", "status", "rest_um", "obs_um", "spaxel_y", "spaxel_x", "flux_wm2",
            "n_spaxels_detected", "centre_kms", "fwhm_kms", "amplitude", "amplitude_err",
            "chi2nu", "snr", "snr_integrated", "snr_rms", "width_at_bound", "detected"]
    with open(outdir / "cube_lines.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    if ratio_rows:
        with open(outdir / "cube_ratios.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["ratio", "value"])
            w.writeheader()
            w.writerows(ratio_rows)

    from astropy.io import fits as _fits
    hdus = [_fits.PrimaryHDU()]
    for key, arr in maps.items():
        hdus.append(_fits.ImageHDU(np.asarray(arr, dtype=np.float32), name=key[:8].upper()))
    _fits.HDUList(hdus).writeto(outdir / "cube_maps.fits", overwrite=True)

    (outdir / "run.json").write_text(json.dumps({
        "tool": "cube_lines",
        "status": "ok",
        "source_key": args.source_key or args.input.stem,
        "cube": str(args.input),
        "shape": list(data.shape),
        "wavelength_um": [float(wave.min()), float(wave.max())],
        "bunit": header.get("BUNIT"),
        "spaxel_solid_angle_sr": omega,
        "redshift": z,
        "lines": [l["name"] for l in lines],
        "n_spaxels_detected": {r["line"]: r.get("n_spaxels_detected") for r in rows},
    }, indent=2) + "\n")

    if args.plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            first = next((r for r in rows if r.get("status") == "ok"), None)
            if first:
                fig, axes = plt.subplots(1, 3, figsize=(12, 3.4))
                for ax, (key, title) in zip(axes, ((f"{first['line']}_flux", "flux"),
                                                   (f"{first['line']}_vel", "velocity km/s"),
                                                   (f"{first['line']}_disp", "dispersion km/s"))):
                    im = ax.imshow(maps[key], origin="lower")
                    ax.set_title(f"{first['line']} {title}", fontsize=9)
                    fig.colorbar(im, ax=ax, fraction=0.046)
                fig.tight_layout()
                fig.savefig(outdir / "cube_maps.png", dpi=140)
                fig.savefig(outdir / "cube_maps.pdf")
                plt.close(fig)
        except Exception as exc:
            log(f"plot skipped: {exc}")

    log(f"wrote {outdir/'cube_lines.csv'} and {outdir/'cube_maps.fits'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
