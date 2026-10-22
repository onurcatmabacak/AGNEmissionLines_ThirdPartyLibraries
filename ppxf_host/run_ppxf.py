#!/usr/bin/env python3
"""pPXF host-AGN decomposition for rest-frame optical QSO spectra.

Input: the prepared PyQSOFit ``spectrum.fits`` (HDU0 flux, HDU1 wavelength in A,
HDU2 error, header ``z``).  Output: pPXF model/host/residual table, a FITS cube,
a fit figure and a JSON summary (chi2, sigma, host fraction).
"""
from __future__ import annotations

import argparse
import glob
import json
import math
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.io import fits

from ppxf.ppxf import ppxf
from ppxf import ppxf_util

C_KMS = 299792.458

# Rest-frame emission features masked before the stellar fit (A).
EMISSION = [1215.67, 1240.14, 1396.76, 1402.06, 1549.06, 1640.42, 1908.73,
            2798.75, 3727.0, 3869.0, 4340.0, 4862.68, 4960.30, 5008.24,
            6549.85, 6585.28, 6564.61, 6718.29, 6732.67]


def read_spectrum(path: Path):
    with fits.open(path, memmap=False) as h:
        flux = np.asarray(h[0].data, float).ravel()
        wave = np.asarray(h[1].data, float).ravel()
        err = np.asarray(h[2].data, float).ravel() if len(h) > 2 else 0.02 * np.abs(flux)
        z = float(h[0].header.get("z", 0.0))
    return wave, flux, err, z


def load_templates(template_dir: Path, wave_rest: np.ndarray):
    files = sorted(glob.glob(str(template_dir / "*.fits")))
    if not files:
        raise SystemExit(f"no templates in {template_dir}")
    tmpl = []
    for f in files:
        with fits.open(f, memmap=False) as h:
            y = np.asarray(h[0].data, float).ravel()
            hdr = h[0].header
        x = hdr.get("CRVAL1", 1680.2) + hdr.get("CDELT1", 0.9) * np.arange(y.size)
        # interpolate onto the spectrum's rest-frame grid, then normalise
        yi = np.interp(wave_rest, x, y, left=np.nan, right=np.nan)
        if not np.isfinite(yi).any():
            continue
        good = np.isfinite(yi)
        yi[~good] = np.interp(wave_rest[~good], wave_rest[good], yi[good])
        yi = np.clip(yi, 0, None)
        med = np.median(yi[yi > 0]) if np.any(yi > 0) else 1.0
        tmpl.append(yi / med)
    if not tmpl:
        raise SystemExit("no usable templates")
    return np.array(tmpl).T  # (npix, ntemp)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path, help="prepared spectrum.fits")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--templates", type=Path, default=Path("/app/templates/eMILES"))
    p.add_argument("--degree", type=int, default=10)
    args = p.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)

    wave, flux, err, z = read_spectrum(args.input)
    wave_rest = wave / (1.0 + z)
    flux_rest = flux * (1.0 + z)
    err_rest = err * (1.0 + z)

    # mask emission lines and bad pixels (rest frame, +/- 2000 km/s)
    mask = np.isfinite(wave_rest) & np.isfinite(flux_rest) & np.isfinite(err_rest) & (err_rest > 0)
    for lam in EMISSION:
        d = lam * 2000.0 / C_KMS
        mask &= ~((wave_rest > lam - d) & (wave_rest < lam + d))
    if mask.sum() < 200:
        raise SystemExit(f"only {mask.sum()} good continuum pixels")
    # rebin to a common log grid
    w0, w1 = float(wave_rest[mask].min()), float(wave_rest[mask].max())
    log_flux, log_wave, velscale = ppxf_util.log_rebin([w0, w1], flux_rest, velscale=None)
    log_err, _, _ = ppxf_util.log_rebin([w0, w1], err_rest, velscale=velscale)
    # templates on the spectrum's rest grid, then the same log grid
    tmpl_lin = load_templates(args.templates, wave_rest)
    tmpl_log = []
    for j in range(tmpl_lin.shape[1]):
        ly, _, _ = ppxf_util.log_rebin([w0, w1], tmpl_lin[:, j], velscale=velscale)
        if ly.size == log_flux.size:
            tmpl_log.append(ly)
    templates = np.array(tmpl_log).T
    # pPXF fit: stellar templates + additive polynomial (AGN continuum)
    # map the rest-frame mask onto the log grid and pass it as goodpixels
    goodpix = np.where(np.interp(np.exp(log_wave), wave_rest, mask.astype(float)) > 0.5)[0]
    pp = ppxf(templates, log_flux, log_err, velscale, start=[100.0, 100.0],
              goodpixels=goodpix, degree=5, mdegree=-1, quiet=True)
    weights = pp.weights
    stellar = templates.dot(weights)
    poly = pp.apoly if pp.apoly is not None else np.zeros_like(stellar)
    total = pp.bestfit
    resid = log_flux - total
    # host fraction in an adaptive rest-frame window (4-5k, else 3-4k, else 2-3k)
    wave_log = np.exp(log_wave)
    if wave_log.max() > 5000:
        lo, hi = 4000.0, 5000.0
    elif wave_log.max() > 4000:
        lo, hi = 3000.0, 4000.0
    else:
        lo, hi = 2000.0, 3000.0
    win = (wave_log > lo) & (wave_log < hi)
    denom = np.nansum(total[win])
    host_frac = float(np.nansum(stellar[win]) / denom) if (win.sum() and np.isfinite(denom) and denom != 0) else float("nan")
    npoly = 0 if pp.polyweights is None else len(pp.polyweights)
    chi2 = float(np.sum((resid / log_err) ** 2) / max(1, log_flux.size - npoly - 2))

    out = args.output
    np.savetxt(out / "ppxf_model.csv",
               np.column_stack([wave_log, log_flux, total, stellar, poly, resid]),
               delimiter=",", header="wave_rest_A,flux,model,stellar,agn_poly,residual", comments="")
    hdu = fits.HDUList([
        fits.PrimaryHDU(),
        fits.BinTableHDU.from_columns([
            fits.Column(name="wave", format="D", array=wave_log),
            fits.Column(name="flux", format="D", array=log_flux),
            fits.Column(name="model", format="D", array=total),
            fits.Column(name="stellar", format="D", array=stellar),
            fits.Column(name="agn_poly", format="D", array=poly),
            fits.Column(name="residual", format="D", array=resid),
        ]),
    ])
    hdu.writeto(out / "ppxf_result.fits", overwrite=True)
    summary = {"z": z, "chi2_red": chi2,
               "n_templates": int(templates.shape[1]),
               "host_fraction": host_frac,
               "host_window_A": [lo, hi],
               "degree": 5, "velscale_kms": float(velscale)}
    try:
        summary["sigma_kms"] = float(pp.sol[1])
    except Exception:
        summary["sigma_kms"] = float("nan")
    (out / "ppxf_summary.json").write_text(json.dumps(summary, indent=2, default=float))

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True,
                                 gridspec_kw={"height_ratios": [3, 1]})
    a1.plot(wave_log, log_flux, color="0.25", lw=0.8, label="observed")
    a1.plot(wave_log, total, color="C3", lw=1.2, label="pPXF total")
    a1.plot(wave_log, stellar, color="C0", lw=1.2, label="stellar host")
    a1.plot(wave_log, poly, color="C1", lw=1.0, ls="--", label="AGN polynomial")
    a1.set_ylabel("flux (1e-17)")
    a1.set_title(f"pPXF host decomposition  z={z:.4f}  chi2_red={chi2:.2f}  host(4-5k)={host_frac:.3f}")
    a1.legend(fontsize=8, frameon=False)
    a2.plot(wave_log, resid, color="0.3", lw=0.7)
    a2.axhline(0, color="k", lw=0.5)
    a2.set_xlabel("rest wavelength (A)")
    a2.set_ylabel("residual")
    fig.tight_layout()
    fig.savefig(out / "ppxf_fit.png", dpi=140, bbox_inches="tight")
    fig.savefig(out / "ppxf_fit.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"[ppxf] z={z:.4f} chi2_red={chi2:.2f} host_frac={host_frac:.3f} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
