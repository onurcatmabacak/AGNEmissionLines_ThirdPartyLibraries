#!/usr/bin/env python3
"""PAHFIT 2.0 fit for JWST/MIRI MRS short+long x1d spectra."""
from __future__ import annotations
import argparse, glob, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import astropy.units as u
from astropy.io import fits
from astropy.nddata import StdDevUncertainty
from specutils import Spectrum1D
import pahfit
from pahfit.model import Model
from pahfit.scripts.plot_pahfit import default_layout_plot


def read_s1d(path):
    with fits.open(path, memmap=False) as h:
        d = h[1].data
        return (np.asarray(d["wavelength"], float), np.asarray(d["flux"], float),
                np.asarray(d["uncertainty"], float), np.zeros(len(d)))


def read_x1d(path):
    with fits.open(path, memmap=False) as h:
        d = h["EXTRACT1D"].data
        return (np.asarray(d["WAVELENGTH"], float), np.asarray(d["SURF_BRIGHT"], float),
                np.asarray(d["SB_ERROR"], float),
                np.asarray(d["DQ"], float) if "DQ" in d.columns.names else np.zeros(len(d)))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=Path("/app/input"))
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--z", type=float, required=True)
    p.add_argument("--maxiter", type=int, default=1000)
    p.add_argument("--segment", choices=["both", "short", "long"], default="both")
    p.add_argument("--no-guess", action="store_true")
    p.add_argument("--spectrum", default=None, help="PAHFIT-packaged spectrum name/path")
    p.add_argument("--instrument", default=None, help="e.g. jwst.miri.mrs.ch1.C")
    p.add_argument("--s1d", action="store_true", help="input dir contains *_s1d.fits (PAHFIT MIRI example)")
    args = p.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)

    if args.spectrum:
        from pahfit.helpers import read_spectrum
        spec = read_spectrum(args.spectrum)
        spec.meta["instrument"] = args.instrument or "jwst.miri.mrs.ch1.C"
        w = spec.spectral_axis.to_value(u.micron)
        print(f"[pahfit] packaged spectrum {args.spectrum}: {len(w)} pixels, "
              f"{w.min():.2f}-{w.max():.2f} um, instrument={spec.meta['instrument']}")
    else:
        waves, fluxes, errs = [], [], []
        pat = "*_s1d.fits" if args.s1d else {"both": "*_x1d.fits", "short": "*mirifushort_x1d.fits",
               "long": "*mirifulong_x1d.fits"}[args.segment]
        for f in sorted(args.input.glob(pat)):
            w, fl, er, dq = read_s1d(f) if args.s1d else read_x1d(f)
            good = (np.isfinite(w) & np.isfinite(fl) & np.isfinite(er) & (er > 0)
                    & (dq == 0) & (w >= 5.0) & (w <= 28.0))
            waves.append(w[good]); fluxes.append(fl[good]); errs.append(er[good])
            print(f"[pahfit] {f.name}: {good.sum()} good pixels, {w[good].min():.2f}-{w[good].max():.2f} um")
        if not waves:
            raise SystemExit("no x1d spectra found")
        w = np.concatenate(waves); fl = np.concatenate(fluxes); er = np.concatenate(errs)
        order = np.argsort(w); w, fl, er = w[order], fl[order], er[order]
        spec = Spectrum1D(spectral_axis=w * u.micron,
                          flux=fl * u.MJy / u.sr,
                          uncertainty=StdDevUncertainty(er * u.MJy / u.sr))
        from pahfit import instrument as pahfit_instrument
        spec.meta["instrument"] = [n for n in pahfit_instrument.instruments()
                                   if str(n).startswith("jwst.miri.mrs.")]
        print(f"[pahfit] combined {len(w)} pixels, {w.min():.2f}-{w.max():.2f} um, z={args.z}")

    pack = Path(pahfit.__file__).parent / "packs" / "science" / "classic.yaml"
    model = Model.from_yaml(str(pack))
    if not args.no_guess:
        model.guess(spec, redshift=args.z)
    model.fit(spec, redshift=args.z, maxiter=args.maxiter)
    model.save(str(args.output / "pahfit_output.ecsv"), overwrite=True)
    model.features.write(str(args.output / "pahfit_features.csv"), format="ascii.csv", overwrite=True)

    fig = default_layout_plot(spec, model, 2.0)
    fig.savefig(args.output / "pahfit_fit.png", dpi=140, bbox_inches="tight")
    fig.savefig(args.output / "pahfit_fit.pdf", bbox_inches="tight")
    summary = {"z": args.z, "instrument": str(spec.meta["instrument"]), "n_pixels": int(len(w)), "flux_unit": "MJy/sr", "segment": args.segment,
               "wave_min_um": float(w.min()), "wave_max_um": float(w.max()),
               "n_features": int(len(model.features))}
    try:
        summary["fit_info"] = {k: float(v) for k, v in dict(model.fit_info).items()
                               if isinstance(v, (int, float, np.floating))}
    except Exception:
        pass
    (args.output / "pahfit_summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(f"[pahfit] done -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
