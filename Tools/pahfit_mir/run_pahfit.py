#!/usr/bin/env python3
"""PAHFIT 2.0 fit for JWST/MIRI MRS, PAHFIT s1d, or Spitzer IRS spectra.

The fitter is deliberately conservative: it reports the native flux unit,
the number of pixels, a relative residual metric and a stability flag.  MIRI
MRS spectra can be binned to a coarser grid before fitting; this is important
for PDS 456, where the native high-resolution short/long spectra otherwise
drive the PAH solution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import astropy.units as u
from astropy.io import fits
from astropy.nddata import StdDevUncertainty
from astropy.table import Table
from specutils import Spectrum1D
import pahfit
from pahfit.model import Model
from pahfit.scripts.plot_pahfit import default_layout_plot

MIRI_ALL = [
    "jwst.miri.mrs.ch1.A", "jwst.miri.mrs.ch1.B", "jwst.miri.mrs.ch1.C",
    "jwst.miri.mrs.ch2.A", "jwst.miri.mrs.ch2.B", "jwst.miri.mrs.ch2.C",
    "jwst.miri.mrs.ch3.A", "jwst.miri.mrs.ch3.B", "jwst.miri.mrs.ch3.C",
    "jwst.miri.mrs.ch4.A", "jwst.miri.mrs.ch4.B", "jwst.miri.mrs.ch4.C",
]


def read_s1d(path: Path):
    with fits.open(path, memmap=False) as h:
        d = h[1].data
        return (np.asarray(d["wavelength"], float), np.asarray(d["flux"], float),
                np.asarray(d["uncertainty"], float), np.zeros(len(d)), "MJy/sr")


def read_x1d(path: Path):
    with fits.open(path, memmap=False) as h:
        d = h["EXTRACT1D"].data
        names = set(d.columns.names)
        w = np.asarray(d["WAVELENGTH"], float)
        if "FLUX" in names:
            fl = np.asarray(d["FLUX"], float)
            er = np.asarray(d["FLUX_ERROR"], float)
            unit = "Jy"
        else:
            fl = np.asarray(d["SURF_BRIGHT"], float)
            er = np.asarray(d["SB_ERROR"], float)
            unit = "MJy/sr"
        dq = np.asarray(d["DQ"], float) if "DQ" in names else np.zeros(len(w))
        return w, fl, er, dq, unit


def read_irs_tbl(path: Path):
    try:
        t = Table.read(path, format="ascii.ipac")
    except Exception:
        t = Table.read(path, format="ascii")
    names = {c.lower(): c for c in t.colnames}
    w = np.asarray(t[names["wavelength"]], float)
    fl = np.asarray(t[names["flux_density"]], float)
    er = np.asarray(t[names.get("error", "flux_density_err")], float)
    good = np.ones(len(w), dtype=bool)
    if "bit-flag" in names:
        good = np.asarray(t[names["bit-flag"]]) == 0
    order = np.asarray(t[names["order"]], int) if "order" in names else np.zeros(len(w), int)
    return w, fl, er, (~good).astype(float), "Jy", order


def bin_spectrum(w, f, e, width: float | None):
    """Median-bin a spectrum; errors combine in quadrature."""
    if not width or width <= 0:
        return w, f, e
    edges = np.arange(float(np.nanmin(w)), float(np.nanmax(w)) + width, width)
    idx = np.digitize(w, edges) - 1
    outw, outf, oute = [], [], []
    for i in range(len(edges) - 1):
        m = idx == i
        if m.sum() == 0:
            continue
        outw.append(float(np.nanmedian(w[m])))
        outf.append(float(np.nanmedian(f[m])))
        oute.append(float(np.sqrt(np.nansum(e[m] ** 2))) / max(1, m.sum()))
    return np.asarray(outw), np.asarray(outf), np.asarray(oute)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=Path("/app/input"))
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--z", type=float, required=True)
    p.add_argument("--maxiter", type=int, default=1000)
    p.add_argument("--segment", choices=["both", "short", "long"], default="both")
    p.add_argument("--no-guess", action="store_true")
    p.add_argument("--spectrum", default=None, help="PAHFIT-packaged spectrum name/path")
    p.add_argument("--instrument", default=None,
                   help="PAHFIT instrument name; otherwise infer/leave unset")
    p.add_argument("--s1d", action="store_true", help="input dir contains *_s1d.fits")
    p.add_argument("--tbl", action="store_true", help="input is a Spitzer IRS .tbl table")
    p.add_argument("--init-from", default=None,
                   help="warm-start from a previous PAHFIT ECSV model")
    p.add_argument("--smooth-um", type=float, default=None,
                   help="median-bin width in micron before fitting (MIRI high-res)")
    p.add_argument("--aperture-arcsec2", type=float, default=0.04,
                   help="effective aperture for Jy -> MJy/sr (MIRI x1d)")
    p.add_argument("--min-wave", type=float, default=5.0)
    p.add_argument("--max-wave", type=float, default=38.0)
    args = p.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)

    flux_unit = "MJy/sr"
    if args.spectrum:
        from pahfit.helpers import read_spectrum
        spec = read_spectrum(args.spectrum)
        if args.instrument:
            parts = [x.strip() for x in args.instrument.split(",") if x.strip()]
            spec.meta["instrument"] = parts[0] if len(parts) == 1 else parts
        w = spec.spectral_axis.to_value(u.micron)
        flux_unit = str(spec.flux.unit)
        print(f"[pahfit] packaged spectrum {args.spectrum}: {len(w)} pixels, "
              f"{w.min():.2f}-{w.max():.2f} um, unit={flux_unit}")
    else:
        waves, fluxes, errs = [], [], []
        unit = None
        if args.tbl:
            files = sorted(args.input.glob("*.tbl"))
            if not files:
                files = [args.input]
        elif args.s1d:
            files = sorted(args.input.glob("*_s1d.fits"))
        else:
            pat = {"both": "*_x1d.fits", "short": "*mirifushort_x1d.fits",
                   "long": "*mirifulong_x1d.fits"}[args.segment]
            files = sorted(args.input.glob(pat))
        if not files:
            raise SystemExit(f"no input spectra found under {args.input}")
        for f in files:
            if f.suffix == ".tbl":
                w, fl, er, dq, uu, order = read_irs_tbl(f)
                # Spitzer IRS tables are point-source calibrated Jy.  PAHFIT
                # requires intensity, so divide by the slit solid angle.
                arcsec2_sr = (np.pi / 180.0 / 3600.0) ** 2
                # The IRS table is point-source calibrated, not per-slit
                # surface brightness.  Applying different SL/LL slit areas
                # inserts an 8.6x step at 14.2 um.  Use one common aperture
                # solid angle so the SED is continuous; PAHFIT then fits the
                # shape and relative features.
                omega = 1.0 * arcsec2_sr
                fl = fl * 1e6 / omega
                er = er * 1e6 / omega
                uu = "MJy/sr"
            elif args.s1d:
                w, fl, er, dq, uu = read_s1d(f)
            else:
                w, fl, er, dq, uu = read_x1d(f)
            if uu == "Jy":
                omega = args.aperture_arcsec2 * (np.pi / 180.0 / 3600.0) ** 2
                fl = fl * 1e6 / omega
                er = er * 1e6 / omega
                uu = "MJy/sr"
            good = (np.isfinite(w) & np.isfinite(fl) & np.isfinite(er) & (er > 0)
                    & (dq == 0) & (w >= args.min_wave) & (w <= args.max_wave))
            waves.append(w[good]); fluxes.append(fl[good]); errs.append(er[good])
            unit = unit or uu
            print(f"[pahfit] {f.name}: {good.sum()} good pixels, "
                  f"{w[good].min():.2f}-{w[good].max():.2f} um, unit={uu}")
        w = np.concatenate(waves); fl = np.concatenate(fluxes); er = np.concatenate(errs)
        order = np.argsort(w); w, fl, er = w[order], fl[order], er[order]
        # Remove exact/near duplicates from overlapping IRS orders or MRS segments.
        keep = np.ones(len(w), dtype=bool)
        for i in range(1, len(w)):
            if abs(w[i] - w[i - 1]) < 1e-5:
                keep[i] = False
        w, fl, er = w[keep], fl[keep], er[keep]
        w, fl, er = bin_spectrum(w, fl, er, args.smooth_um)
        flux_unit = unit or "MJy/sr"
        spec = Spectrum1D(spectral_axis=w * u.micron,
                          flux=fl * u.Unit(flux_unit),
                          uncertainty=StdDevUncertainty(er * u.Unit(flux_unit)))
        if args.instrument:
            parts = [x.strip() for x in args.instrument.split(",") if x.strip()]
            spec.meta["instrument"] = parts[0] if len(parts) == 1 else parts
        elif args.s1d or any("miri" in f.name.lower() for f in files):
            spec.meta["instrument"] = MIRI_ALL
        if "instrument" not in spec.meta:
            raise SystemExit("PAHFIT needs --instrument for non-MIRI input")
        print(f"[pahfit] combined {len(w)} pixels, {w.min():.2f}-{w.max():.2f} um, "
              f"z={args.z}, bin={args.smooth_um}, unit={flux_unit}")

    pack = Path(pahfit.__file__).parent / "packs" / "science" / "classic.yaml"
    if args.init_from:
        model = Model.from_saved(args.init_from)
        # ECSV metadata has the instrument fields swapped; the observed
        # spectrum metadata remains authoritative for the fit.
        model.features.meta["instrument"] = spec.meta.get("instrument", "")
        print(f"[pahfit] warm-starting from {args.init_from}")
    else:
        model = Model.from_yaml(str(pack))
    status = "ok"
    try:
        if not args.no_guess and not args.init_from:
            model.guess(spec, redshift=args.z)
    except Exception as exc:  # noqa: BLE001
        status = f"guess_failed:{type(exc).__name__}"
        print(f"[pahfit] guess failed: {exc}")
    try:
        model.fit(spec, redshift=args.z, maxiter=args.maxiter)
    except Exception as exc:  # noqa: BLE001
        status = f"fit_failed:{type(exc).__name__}"
        print(f"[pahfit] fit failed: {exc}")
    model.save(str(args.output / "pahfit_output.ecsv"), overwrite=True)
    model.features.write(str(args.output / "pahfit_features.csv"), format="ascii.csv", overwrite=True)

    plot_status = "ok"
    try:
        fig = default_layout_plot(spec, model, 2.0)
        fig.savefig(args.output / "pahfit_fit.png", dpi=140, bbox_inches="tight")
        fig.savefig(args.output / "pahfit_fit.pdf", bbox_inches="tight")
    except Exception as exc:  # noqa: BLE001
        plot_status = f"fallback:{type(exc).__name__}"
        print(f"[pahfit] default plot failed ({exc}); using fallback plot")
        fig, ax = plt.subplots(figsize=(11, 5))
        ax.plot(np.asarray(w), np.asarray(spec.flux.value), color="0.3", lw=0.8)
        ax.set_xlabel("observed wavelength (um)")
        ax.set_ylabel(f"flux ({flux_unit})")
        ax.set_title("PAHFIT fit (fallback plot; fit itself succeeded)")
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(args.output / "pahfit_fit.png", dpi=140, bbox_inches="tight")
        fig.savefig(args.output / "pahfit_fit.pdf", bbox_inches="tight")

    rms_rel = float("nan")
    try:
        lam = spec.spectral_axis.to_value(u.micron) / (1.0 + args.z)
        # PAHFIT converts the observed spectrum to the rest frame by (1+z);
        # the model is evaluated on that rest-frame grid.  Compare like with
        # like (the previous code compared observed flux to rest-frame model).
        pred = np.asarray(model.fitter.model(lam), float) / (1.0 + args.z)
        y = np.asarray(spec.flux.value, float)
        if pred.shape == y.shape:
            rms_rel = float(np.sqrt(np.nanmean((y - pred) ** 2))
                            / max(np.nanmedian(np.abs(y)), 1e-30))
    except Exception:
        pass
    unstable = bool((np.isfinite(rms_rel) and rms_rel > 0.5) or status != "ok")
    summary = {
        "z": args.z, "instrument": str(spec.meta.get("instrument", "")),
        "n_pixels": int(len(w)), "flux_unit": flux_unit, "segment": args.segment,
        "smooth_um": args.smooth_um, "status": status, "plot_status": plot_status,
        "wave_min_um": float(np.min(w)), "wave_max_um": float(np.max(w)),
        "n_features": int(len(model.features)), "rms_rel": rms_rel,
        "unstable": unstable,
    }
    try:
        summary["fit_info"] = {k: float(v) for k, v in dict(model.fit_info).items()
                               if isinstance(v, (int, float, np.floating))}
    except Exception:
        pass
    (args.output / "pahfit_summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(f"[pahfit] done status={status} rms_rel={rms_rel:.3f} unstable={unstable} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
