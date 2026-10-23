#!/usr/bin/env python3
"""PyQSOFitSpec production line-fitting driver.

Wraps the vendored PyQSOFitSpec package (upstream commit aa326ed) and reproduces
its *bootstrap* mode from ``main.py``:

    for each bootstrap iteration:
        flux_noise = [N(f, err) for f, err in zip(flux, err)]   # parametric bootstrap
        QSOFit(...).Fit(..., MC=False, n_trials=0)               # full continuum+line refit
    line value = mean over iterations, line error = std over iterations

Differences from upstream ``main.py`` (all applied here, not in the vendored
code):

* the emission-line table (``qsopar2.fits``) is generated from a JSON config
  instead of being hard-coded in ``main.py``, and covers the optical H-beta /
  [O III] complex in addition to Mg II;
* the per-line properties are fetched from the fitted Gaussian parameters with
  ``QSOFit.line_prop`` (the same routine upstream uses for
  ``_whole_br_*`` results), so the line *area* (flux) is available as well as
  FWHM/sigma/skew/EW/peak;
* the bootstrap mean/std is kept per line and per property, and the individual
  realisations are written out; a compact table, a fit figure, a bootstrap
  histogram grid and a corner plot are produced.

The fit itself is never replaced: continuum fitting, kmpfit line fitting,
skew-normal line model and the bootstrap refit all run inside PyQSOFitSpec.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

import numpy as np

# Package design constant: line_prop() classifies a Gaussian as broad when its
# log10(sigma) is > 0.0017 (sigma ~ 510 km/s); see PyQSOFitSpec.line_prop.
BROAD_LOG_SIGMA = 0.0017

PROP_NAMES = ("fwhm", "sigma", "skew", "ew", "peak", "area")
PROP_LABELS = {
    "fwhm": "FWHM (km/s)",
    "sigma": "sigma (km/s)",
    "skew": "skewness",
    "ew": "EW (A)",
    "peak": "peak (1e-17 erg/s/cm2/A)",
    "area": "flux (1e-17 erg/s/cm2)",
}

DEFAULT_CONFIG = {
    "linemodel": "skewnorm_model",
    "nboot_fit": 5,
    "seed": 20250101,
    "error_floor_frac": 0.0,
    "obs_wave_range": None,
    "flux_unit": "auto",
    "nsmooth": 1,
    "reject_badpix": False,
    "Fe_uv_op": True,
    "poly": True,
    "BC": False,
    "rej_abs": False,
    "decomposition_host": False,
    "save_fits": False,
    "plot_fit_figure": True,
    "line_table": [],
    "comparison": {
        "totals": {
            "MgII": ["MgII_br", "MgII_na"],
            "Hbeta": ["Hb_br", "Hb_na"],
            "OIII5007": ["OIII5007c", "OIII5007w"],
        },
        "corner": ["Hbeta", "OIII5007", "MgII"],
    },
}


class Tee:
    """Print to stdout and a log file at the same time."""

    def __init__(self, path: Path):
        self.terminal = sys.stdout
        self.log = path.open("w")

    def write(self, msg):
        self.terminal.write(msg)
        self.log.write(msg)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def close(self):
        self.log.close()


def deep_update(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_update(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: Path) -> dict:
    if path.is_dir():
        path = path / "config.json"
    if not path.is_file():
        raise FileNotFoundError(f"config not found: {path}")
    with path.open() as fh:
        user = json.load(fh)
    cfg = deep_update(DEFAULT_CONFIG, user)
    cfg["_config_path"] = str(path)
    return cfg


# --------------------------------------------------------------------------
# spectrum input
# --------------------------------------------------------------------------
def find_spectrum(input_path: Path) -> Path:
    if input_path.is_file():
        return input_path
    if not input_path.is_dir():
        raise FileNotFoundError(f"input path not found: {input_path}")
    preferred = input_path / "spectrum.fits"
    if preferred.is_file():
        return preferred
    candidates = sorted(input_path.glob("spec-*.fits"))
    if not candidates:
        candidates = sorted(input_path.glob("*.fits"))
    if not candidates:
        raise FileNotFoundError(f"no FITS spectrum in {input_path}")
    return candidates[0]


def read_spectrum(path: Path, flux_unit: str = "auto", z_override=None):
    """Read a spectrum and return (lam_obs [A], flux, err, z, meta).

    Flux/err are returned in units of 1e-17 erg/s/cm2/A, which is the unit
    PyQSOFit/PyQSOFitSpec expects (it is also the native SDSS COADD unit and
    the unit on the package's plot axes).

    Supported layouts:
      * PyQSOFit prepared layout (this repo's ``write_pyqsofit``): flux in
        HDU0, wavelength in HDU1, 1-sigma error in HDU2, absolute cgs flux;
      * SDSS COADD table: HDU1 columns LOGLAM/FLUX/IVAR, redshift in HDU2 or
        in the primary header.
    """
    from astropy.io import fits

    with fits.open(path) as hdul:
        hdr = hdul[0].header
        meta = {
            "file": str(path),
            "hdu0_bunit": hdr.get("BUNIT", ""),
            "hdu0_z": float(hdr["z"]) if "z" in hdr else None,
        }
        is_table = isinstance(hdul[1], (fits.BinTableHDU, fits.TableHDU))
        if is_table:
            table = hdul[1].data
            cols = {name.lower(): name for name in table.dtype.names}
            lam = 10.0 ** np.asarray(table[cols["loglam"]], dtype=float)
            flux = np.asarray(table[cols["flux"]], dtype=float)
            ivar = np.asarray(table[cols["ivar"]], dtype=float)
            with np.errstate(divide="ignore"):
                err = 1.0 / np.sqrt(np.clip(ivar, 1e-30, None))
            # ivar <= 0 marks a masked/junk pixel; make it fail the finite check
            # in clean_spectrum instead of giving it a ~infinite error.
            err = np.where(ivar > 0, err, np.inf)
            # SDSS writes the redshift in the SPALL/ZALL binary tables as "Z";
            # FITS column lookup is case-insensitive but columns.names is not.
            z = None
            for hdu in hdul[1:]:
                if hdu.data is None or not isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                    continue
                lower = [name.lower() for name in hdu.columns.names]
                if "z" in lower:
                    z = float(np.ravel(hdu.data["z"])[0])
                    break
            if z is None:
                z = hdr.get("z", hdr.get("Z", None))
            native_scale = 1.0  # SDSS COADD flux is already 1e-17 cgs
            meta["layout"] = "sdss_table"
        else:
            flux = np.asarray(hdul[0].data, dtype=float)
            lam = np.asarray(hdul[1].data, dtype=float)
            err = np.asarray(hdul[2].data, dtype=float)
            z = hdr.get("z", hdr.get("Z", None))
            bunit = str(hdr.get("BUNIT", "")).lower().replace(" ", "")
            if flux_unit == "auto":
                # The prepared files in this repo are absolute cgs; anything
                # labelled 1e-17 (or with no unit at all in an SDSS-like
                # product) is already in the native PyQSOFit unit.
                native = ("1e-17" in bunit) or ("10^-17" in bunit) or ("1e17" in bunit)
                native_scale = 1.0 if native else 1e17
            elif flux_unit in ("1e-17", "native", "sdss"):
                native_scale = 1.0
            elif flux_unit == "cgs":
                native_scale = 1e17
            else:
                raise ValueError(f"unknown flux_unit: {flux_unit}")
            meta["layout"] = "pyqsofit_image"
        # flux and err are multiplied by this to reach 1e-17 cgs units
        meta["unit_scale_to_1e17"] = native_scale

    flux = flux * native_scale
    err = err * native_scale
    if z_override is not None:
        z = float(z_override)
    if z is None:
        raise ValueError("no redshift in the input FITS; pass --z")
    meta["z"] = float(z)
    meta["n_pixels_raw"] = int(flux.size)
    return lam, flux, err, float(z), meta


def clean_spectrum(lam, flux, err, cfg):
    good = np.isfinite(lam) & np.isfinite(flux) & np.isfinite(err) & (err > 0)
    lo, hi = (cfg.get("obs_wave_range") or [None, None])
    if lo is not None:
        good &= lam >= float(lo)
    if hi is not None:
        good &= lam <= float(hi)
    lam, flux, err = lam[good], flux[good], err[good]
    floor = float(cfg.get("error_floor_frac") or 0.0)
    if floor > 0:
        err = np.sqrt(err ** 2 + (floor * flux) ** 2)
    order = np.argsort(lam)
    return lam[order], flux[order], err[order], int((~good).sum()), floor


# --------------------------------------------------------------------------
# line table (qsopar2.fits)
# --------------------------------------------------------------------------
LINE_COLUMNS = [
    ("lambda", "f4"),
    ("compname", "S20"),
    ("minwav", "f4"),
    ("maxwav", "f4"),
    ("linename", "S20"),
    ("ngauss", "f4"),
    ("sigval", "S20"),
    ("voff", "f4"),
    ("iniskw", "S20"),
    ("fvalue", "S20"),
]


def build_line_table(lines: list[dict], path: Path):
    """Write the PyQSOFitSpec ``qsopar2.fits`` line table.

    Column semantics (upstream main.py / PyQSOFitSpec._DoLineFit):
      lambda   vacuum rest wavelength of the line [A]
      compname name of the fitting complex (lines sharing it are fitted together)
      minwav/maxwav  rest-frame window of the complex [A]
      linename unique component name
      ngauss   number of Gaussians per component
      sigval   initial log10(sigma) or "[min, max]"; "OTHER*1.0" ties the width
               and the velocity shift to another component
      voff     half-width of the allowed velocity offset in log(lambda)
      iniskw   initial skewness of the skew-normal profile
      fvalue   initial amplitude, or "OTHER*ratio" for a fixed flux ratio
    """
    from astropy.io import fits

    if not lines:
        raise ValueError("config has an empty 'line_table'")
    needed = [name for name, _ in LINE_COLUMNS]
    rec = np.recarray(len(lines), dtype=[(name, dt) for name, dt in LINE_COLUMNS])
    for i, line in enumerate(lines):
        missing = [key for key in needed if key not in line]
        if missing:
            raise ValueError(f"line_table[{i}] missing {missing}")
        for name in needed:
            value = line[name]
            if np.dtype(dict(LINE_COLUMNS)[name]).kind == "S":
                value = str(value)
            rec[name][i] = value

    hdr = fits.Header()
    hdr["lambda"] = "Vacuum wavelength in Angstrom"
    hdr["compname"] = "Fitting complex"
    hdr["minwav"] = "Lower complex fitting range [A, rest frame]"
    hdr["maxwav"] = "Upper complex fitting range [A, rest frame]"
    hdr["ngauss"] = "Number of Gaussians per component"
    hdr["sigval"] = "Initial/bounded log10(sigma) or tie (OTHER*ratio)"
    hdr["voff"] = "Velocity offset limit in log(lambda)"
    hdr["iniskw"] = "Initial skewness"
    hdr["fvalue"] = "Amplitude or flux-ratio tie (OTHER*ratio)"
    fits.BinTableHDU(data=rec.view(fits.FITS_rec), header=hdr, name="data").writeto(
        path, overwrite=True
    )
    return path


# --------------------------------------------------------------------------
# fitting
# --------------------------------------------------------------------------
def import_package():
    import PyQSOFitSpec
    from PyQSOFitSpec import QSOFit

    return PyQSOFitSpec, QSOFit


def run_single_fit(QSOFit, lam, flux, err, z, cfg, path, name, fig_dir, plot):
    q = QSOFit(
        lam, flux, err, z,
        ra=-999.0, dec=-999.0, plateid=0, mjd=0, fiberid=0, path=str(path),
    )
    save_fits_name = bool(cfg.get("save_fits"))
    q.Fit(
        name=name,
        nsmooth=int(cfg.get("nsmooth", 1)),
        and_or_mask=False,
        deredden=False,
        reject_badpix=bool(cfg.get("reject_badpix", False)),
        wave_range=None,
        wave_mask=None,
        decomposition_host=bool(cfg.get("decomposition_host", False)),
        Mi=None,
        npca_gal=5,
        npca_qso=20,
        Fe_uv_op=bool(cfg.get("Fe_uv_op", True)),
        Fe_flux_range=None,
        poly=bool(cfg.get("poly", True)),
        BC=bool(cfg.get("BC", False)),
        rej_abs=bool(cfg.get("rej_abs", False)),
        initial_guess=None,
        MC=False,          # bootstrap supplies the uncertainty, not internal MC
        n_trials=0,
        linemodel=str(cfg.get("linemodel", "skewnorm_model")),
        linefit=True,
        save_result=False,
        plot_fig=bool(plot),
        save_fig=bool(plot),
        plot_line_name=True,
        plot_legend=True,
        dustmap_path=None,
        save_fig_path=str(fig_dir),
        save_fits_path=None,
        save_fits_name=save_fits_name,
    )
    return q


def fit_quality(q):
    """Status/chi2 of each fitted complex.

    ``QSOFit._DoLineFit`` only stores ``comp_result`` (values) without the
    matching names; the same entries are part of ``line_result`` /
    ``line_result_name`` (``<i>_line_status``, ``<i>_line_red_chi2``, ...), so
    read them from there.
    """
    status = {}
    names = [str(n) for n in np.atleast_1d(q.line_result_name)]
    values = np.atleast_1d(q.line_result)
    for i, name in enumerate(names):
        if name.endswith(("_line_status", "_line_red_chi2", "_line_min_chi2", "_ndof")):
            try:
                status[name] = float(values[i])
            except (TypeError, ValueError):
                status[name] = None
    return status


def extract_line_properties(q, cfg):
    """Per-component line properties from the converged kpmfit parameters.

    ``QSOFit._DoLineFit`` stores one 4-parameter block per Gaussian
    (scale, ln(center), ln(sigma), skewness) in ``gauss_result`` with names
    ``<linename>_<gauss index>_scale`` etc.  Properties are computed with
    ``QSOFit.line_prop`` (same code path as the package's own results), using
    the package's broad/narrow classification.
    """
    out = {}
    names = [str(n) for n in np.atleast_1d(q.gauss_result_name)]
    values = np.asarray(q.gauss_result, dtype=float)
    for line in cfg["line_table"]:
        lname = str(line["linename"])
        key = f"{lname}_1_scale"
        if key not in names:
            raise RuntimeError(f"fitted parameters for {lname} not found in gauss_result")
        idx = names.index(key)
        pp = np.asarray(values[idx: idx + 4], dtype=float)
        if not np.all(np.isfinite(pp)):
            out[lname] = {p: float("nan") for p in PROP_NAMES}
            continue
        linetype = "broad" if pp[2] > BROAD_LOG_SIGMA else "narrow"
        try:
            fwhm, sigma, skew, ew, peak, area = q.line_prop(
                float(line["lambda"]), pp, linetype
            )
        except Exception as exc:  # noqa: BLE001 - a failed component must not kill the run
            print(f"  [warn] line_prop failed for {lname}: {exc}")
            fwhm = sigma = skew = ew = peak = area = float("nan")
        out[lname] = {
            "fwhm": float(fwhm), "sigma": float(sigma), "skew": float(skew),
            "ew": float(ew), "peak": float(peak), "area": float(area),
            "linetype": linetype,
            "scale": float(pp[0]), "ln_center": float(pp[1]),
            "ln_sigma": float(pp[2]), "skew_par": float(pp[3]),
        }
    return out


# --------------------------------------------------------------------------
# aggregation / figures
# --------------------------------------------------------------------------
def bootstrap_summary(samples: dict, component_of: dict):
    """mean/std/median/p16/p84 per line and property (package uses mean/std)."""
    summary = {}
    for lname, rows in samples.items():
        summary[lname] = {}
        for prop in PROP_NAMES:
            values = np.array([row[prop] for row in rows], dtype=float)
            finite = values[np.isfinite(values)]
            if finite.size == 0:
                summary[lname][prop] = {
                    "mean": float("nan"), "std": float("nan"), "median": float("nan"),
                    "p16": float("nan"), "p84": float("nan"), "n": 0,
                }
                continue
            summary[lname][prop] = {
                "mean": float(np.mean(finite)),
                "std": float(np.std(finite)),
                "median": float(np.median(finite)),
                "p16": float(np.percentile(finite, 16)),
                "p84": float(np.percentile(finite, 84)),
                "n": int(finite.size),
            }
        summary[lname]["component"] = component_of.get(lname, "")
    return summary


def total_series(samples: dict, groups: dict, prop: str = "area") -> dict:
    """Sum named components per realisation (broad+narrow totals)."""
    totals = {}
    n = len(next(iter(samples.values())))
    for label, members in groups.items():
        series = []
        for i in range(n):
            value = 0.0
            ok = True
            for member in members:
                if member not in samples:
                    ok = False
                    break
                v = samples[member][i][prop]
                if not np.isfinite(v):
                    ok = False
                    break
                value += v
            series.append(value if ok else float("nan"))
        totals[label] = np.array(series, dtype=float)
    return totals


def write_csv(path: Path, rows: list[dict], fieldnames=None):
    if not rows:
        return
    fieldnames = fieldnames or list(rows[0].keys())
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sigval_bounds(line, table_by_name, depth=0):
    """Upper/lower log10(sigma) prior bounds encoded in a sigval string.

    ``sigval`` is either "[min, max]" or "OTHER*ratio" (width tied to another
    component); tied components inherit the referenced component's bounds.
    """
    sigval = str(line.get("sigval", ""))
    if sigval.startswith("["):
        parts = sigval.strip("[]").split(",")
        if len(parts) == 2:
            lo, hi = sorted(float(part) for part in parts)
            return lo, hi
        return None
    if "*" in sigval and depth < 4:
        ref = sigval.split("*")[0]
        target = table_by_name.get(ref)
        if target is not None:
            return sigval_bounds(target, table_by_name, depth + 1)
    return None


def line_note(line, samples, table_by_name):
    """Flag widths that are pinned by the prior rather than measured."""
    bounds = sigval_bounds(line, table_by_name)
    if bounds is None:
        return ""
    ln_sigmas = np.array([row.get("ln_sigma", np.nan) for row in samples], dtype=float)
    ln_sigmas = ln_sigmas[np.isfinite(ln_sigmas)]
    if ln_sigmas.size == 0:
        return ""
    mean = float(np.mean(ln_sigmas))
    lo, hi = bounds
    if abs(mean - hi) <= 0.02 * max(abs(hi), 1e-6):
        return "FWHM pinned at the prior upper bound; only the flux is measured"
    if abs(mean - lo) <= 0.02 * max(abs(lo), 1e-6):
        return "FWHM pinned at the prior lower bound; only the flux is measured"
    return ""


def is_stable(mean, p16, p84, rel_width=0.25):
    """False when the 16-84% interval is wide or the posterior is bimodal."""
    if not np.isfinite(mean) or not np.isfinite(p16) or not np.isfinite(p84) or mean == 0:
        return False
    return bool(abs(p84 - p16) / abs(mean) <= rel_width)


def fmt(value, digits=10):
    if value is None:
        return ""
    if isinstance(value, float) and not np.isfinite(value):
        return "nan"
    if isinstance(value, (float, np.floating)):
        return f"{value:.{digits}g}"
    return value


def make_bootstrap_figures(samples, groups, out_dir: Path, nboot: int,
                           corner_keys=None, display=None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    display = display or {}
    prop = "area"
    labels = list(groups.keys())
    ncols = 3
    nrows = int(np.ceil(len(labels) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.0 * ncols, 3.1 * nrows), squeeze=False)
    for ax, label in zip(axes.ravel(), labels):
        series = total_series(samples, {label: groups[label]}, prop)[label]
        series = series[np.isfinite(series)]
        if series.size:
            bins = int(min(30, max(4, series.size // 2)))
            ax.hist(series, bins=bins, color="C0", alpha=0.8, edgecolor="C0", linewidth=0.3)
            mean = float(np.mean(series))
            std = float(np.std(series))
            ax.axvline(mean, color="C3", lw=1.2, label=f"mean={mean:.1f}")
            ax.axvspan(mean - std, mean + std, color="C3", alpha=0.12, label=r"$\pm1\sigma$")
            ax.legend(fontsize=7)
        ax.set_title(display.get(label, label), fontsize=10)
        ax.set_xlabel("flux (1e-17 erg/s/cm2)")
        ax.set_ylabel("realisations")
        ax.tick_params(labelsize=8)
    for ax in axes.ravel()[len(labels):]:
        ax.axis("off")
    fig.suptitle(f"PyQSOFitSpec parametric bootstrap (nboot={nboot})", fontsize=12)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"pyqsofitspec_bootstrap.{ext}", dpi=140)
    plt.close(fig)

    corner_keys = corner_keys or labels
    corner_keys = [lab for lab in corner_keys if lab in groups]
    if len(corner_keys) < 2 or nboot < 4:
        return False
    series = total_series(samples, {lab: groups[lab] for lab in corner_keys})
    data = np.column_stack([series[lab] for lab in corner_keys])
    keep = np.all(np.isfinite(data), axis=1)
    data = data[keep]
    if data.shape[0] >= 4:
        try:
            import warnings
            import corner

            kwargs = dict(
                labels=[display.get(lab, lab) for lab in corner_keys],
                quantiles=[0.16, 0.5, 0.84],
                show_titles=True, title_kwargs={"fontsize": 9},
                label_kwargs={"fontsize": 11},
            )
            if data.shape[0] < 20:
                # Too few realisations for kernel-density contours; show the
                # individual draws instead of empty contour levels.
                kwargs.update(plot_density=False, plot_contours=False, no_fill_contours=True)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fig = corner.corner(data, **kwargs)
            for ext in ("png", "pdf"):
                fig.savefig(out_dir / f"pyqsofitspec_corner.{ext}", dpi=140, bbox_inches="tight")
            plt.close(fig)
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] corner plot skipped: {exc}")
    return False


def save_fit_figure(out_dir: Path, name: str):
    import matplotlib.pyplot as plt

    fignums = plt.get_fignums()
    saved = []
    for i, num in enumerate(fignums):
        fig = plt.figure(num)
        suffix = "" if i == 0 else f"_{i + 1}"
        png = out_dir / f"spec-{name}_fit{suffix}.png"
        fig.savefig(png, dpi=140, bbox_inches="tight")
        saved.append(png.name)
    plt.close("all")
    return saved


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input-dir", "--input", dest="input_dir", default="/app/input",
                   help="directory with spectrum.fits / spec-*.fits, or a FITS path")
    p.add_argument("--out", default="/app/output", help="output directory")
    p.add_argument("--config", default="/app/config", help="config directory or JSON file")
    p.add_argument("--z", type=float, default=None, help="override systemic redshift")
    p.add_argument("--nboot", type=int, default=None, help="override nboot_fit")
    p.add_argument("--seed", type=int, default=None, help="override random seed")
    p.add_argument("--name", default=None, help="object name used in figures/run.json")
    p.add_argument("--package-dir", default=os.environ.get("PYQSOFITSPEC_ROOT", "/app/pyqsofitspec"),
                   help="directory containing PyQSOFitSpec.py and the Fe II templates")
    p.add_argument("--flux-unit", default=None, choices=["auto", "cgs", "1e-17"],
                   help="override the input flux unit")
    p.add_argument("--input-host", default=os.environ.get("PYQSOFITSPEC_INPUT_HOST"),
                   help="host-side path of the input, recorded in run.json for provenance")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    log = Tee(out_dir / "run.log")
    sys.stdout = log
    t_start = time.time()
    try:
        return _main(args, out_dir, t_start)
    finally:
        sys.stdout = log.terminal
        log.close()


def _main(args, out_dir: Path, t_start: float):
    here = Path(__file__).resolve().parent
    default_cfg = here.parent / "configs" / "pyqsofitspec_line" / "default"
    cfg = load_config(Path(args.config) if args.config else default_cfg)
    if args.nboot is not None:
        cfg["nboot_fit"] = args.nboot
    if args.seed is not None:
        cfg["seed"] = args.seed
    if args.flux_unit is not None:
        cfg["flux_unit"] = args.flux_unit
    nboot = int(cfg["nboot_fit"])
    if nboot < 1:
        raise ValueError("nboot_fit must be >= 1; this tool only reports a real bootstrap")
    seed = int(cfg["seed"])

    package_dir = Path(args.package_dir).resolve()
    pkg, QSOFit = import_package()
    work = out_dir / ".work"
    work.mkdir(exist_ok=True)
    for fname in ("fe_uv.txt", "fe_optical.txt"):
        src = package_dir / fname
        if not src.is_file():
            raise FileNotFoundError(f"{src} not found (PyQSOFitSpec package dir)")
        shutil.copy2(src, work / fname)
    build_line_table(cfg["line_table"], work / "qsopar2.fits")

    spec_path = find_spectrum(Path(args.input_dir))
    lam, flux, err, z, meta = read_spectrum(spec_path, cfg.get("flux_unit", "auto"), args.z)
    lam, flux, err, n_removed, floor = clean_spectrum(lam, flux, err, cfg)
    if args.input_host:
        meta["host_input"] = str(args.input_host)
    name = args.name or Path(spec_path).stem.replace("spectrum", "") or "source"
    name = name.strip("-_") or "source"

    rest_lo = float(lam.min() / (1 + z))
    rest_hi = float(lam.max() / (1 + z))
    print("PyQSOFitSpec production driver")
    print(f"  package        : {pkg.__file__}")
    print(f"  spectrum       : {meta['file']} ({meta['layout']}, {flux.size} px used, {n_removed} masked)")
    print(f"  z              : {z:.8f}   rest coverage: {rest_lo:.0f}-{rest_hi:.0f} A")
    print(f"  line model     : {cfg['linemodel']}")
    print(f"  line table     : {len(cfg['line_table'])} components, "
          f"{work / 'qsopar2.fits'}")
    print(f"  bootstrap      : nboot={nboot}, seed={seed}, parametric (flux + N(0, err))")
    print(f"  error floor    : {floor:g} x flux (0 = calibrated errors only)")

    components = [str(line["linename"]) for line in cfg["line_table"]]
    table_by_name = {str(line["linename"]): line for line in cfg["line_table"]}
    component_of = {str(line["linename"]): str(line["compname"]) for line in cfg["line_table"]}
    rest_wave = {str(line["linename"]): float(line["lambda"]) for line in cfg["line_table"]}

    np.random.seed(seed)
    samples = {lname: [] for lname in components}
    iteration_info = []
    fig_files = []
    fit_status = None
    for nb in range(nboot):
        t0 = time.time()
        # Exactly the package's bootstrap step (main.py):
        #   flux_noise = [np.random.normal(f, fe) for f, fe in zip(flux, err)]
        flux_noise = np.array([np.random.normal(f, fe) for f, fe in zip(flux, err)])
        plot = bool(cfg.get("plot_fit_figure", True)) and nb == 0
        q = run_single_fit(QSOFit, lam, flux_noise, err, z, cfg, work, name, out_dir, plot)
        props = extract_line_properties(q, cfg)
        for lname in components:
            samples[lname].append(props[lname])
        if fit_status is None:
            fit_status = fit_quality(q)
        if plot:
            fig_files = save_fit_figure(out_dir, name)
        dt = time.time() - t0
        iteration_info.append({
            "iteration": nb,
            "wall_seconds": round(dt, 2),
            "figure": bool(plot),
            "area_1e17": {ln: round(props[ln]["area"], 6) for ln in components},
        })
        print(f"  [boot {nb + 1}/{nboot}] {dt:6.2f} s  " + "  ".join(
            f"{ln}={props[ln]['area']:.1f}" for ln in components))

    summary = bootstrap_summary(samples, component_of)
    groups = cfg["comparison"]["totals"]

    # ---- compact per-line table -----------------------------------------
    line_rows = []
    for lname in components:
        s = summary[lname]
        rows = samples[lname]
        lt = next((r.get("linetype", "") for r in rows if "linetype" in r), "")
        area = s["area"]
        snr = area["mean"] / area["std"] if area["std"] > 0 else float("nan")
        line_rows.append({
            "line": lname,
            "component": lt,
            "complex": component_of[lname],
            "rest_wavelength_angstrom": f"{rest_wave[lname]:.2f}",
            "flux_1e17": fmt(area["mean"]),
            "flux_err_1e17": fmt(area["std"]),
            "flux_p16_1e17": fmt(area["p16"]),
            "flux_p84_1e17": fmt(area["p84"]),
            "flux_erg_s_cm2": fmt(area["mean"] * 1e-17),
            "flux_err_erg_s_cm2": fmt(area["std"] * 1e-17),
            "fwhm_kms": fmt(s["fwhm"]["mean"], 8),
            "fwhm_err_kms": fmt(s["fwhm"]["std"], 8),
            "sigma_kms": fmt(s["sigma"]["mean"], 8),
            "sigma_err_kms": fmt(s["sigma"]["std"], 8),
            "skewness": fmt(s["skew"]["mean"], 6),
            "skewness_err": fmt(s["skew"]["std"], 6),
            "ew_angstrom": fmt(s["ew"]["mean"], 8),
            "ew_err_angstrom": fmt(s["ew"]["std"], 8),
            "peak_1e17": fmt(s["peak"]["mean"], 8),
            "peak_err_1e17": fmt(s["peak"]["std"], 8),
            "snr": fmt(snr, 6),
            "stable": is_stable(area["mean"], area["p16"], area["p84"]),
            "note": line_note(table_by_name[lname], rows, table_by_name),
            "nboot": area["n"],
        })
    write_csv(out_dir / "pyqsofitspec_lines.csv", line_rows)

    # ---- native-style package output (main.py column convention) --------
    # upstream main.py writes one row per spectrum with <line>_<prop>_<comp>
    # columns and mean/std over the bootstrap realisations.  Here <line> is the
    # component name (MgII_br, Hb_na, ...) and <comp> is broad/narrow as fitted.
    native = {"spectra": name}
    for lname in components:
        comp = "br" if samples[lname][0].get("linetype") == "broad" else "na"
        for prop in ("fwhm", "sigma", "skew", "ew", "peak", "area"):
            key = f"{lname}_{prop}_{comp}"
            native[key] = fmt(summary[lname][prop]["mean"])
            native[f"{key}_err"] = fmt(summary[lname][prop]["std"])
    write_csv(out_dir / "pyqsofitspec_out.csv", [native])

    # ---- per-realisation samples ----------------------------------------
    boot_rows = []
    for i in range(nboot):
        for lname in components:
            row = {"iteration": i, "line": lname,
                   "component": component_of[lname],
                   "rest_wavelength_angstrom": f"{rest_wave[lname]:.2f}"}
            for prop in PROP_NAMES:
                row[prop] = fmt(samples[lname][i][prop], 10)
            for key in ("scale", "ln_center", "ln_sigma", "skew_par"):
                row[key] = fmt(samples[lname][i].get(key), 10)
            boot_rows.append(row)
    write_csv(out_dir / "pyqsofitspec_bootstrap.csv", boot_rows)

    # ---- totals (broad+narrow) for cross-tool comparison ----------------
    total_rows = []
    for label, members in groups.items():
        series = total_series(samples, {label: members})[label]
        finite = series[np.isfinite(series)]
        mean = float(np.mean(finite)) if finite.size else float("nan")
        std = float(np.std(finite)) if finite.size else float("nan")
        total_rows.append({
            "total": label,
            "components": "+".join(members),
            "flux_1e17": fmt(mean),
            "flux_err_1e17": fmt(std),
            "flux_p16_1e17": fmt(np.percentile(finite, 16)) if finite.size else "nan",
            "flux_p84_1e17": fmt(np.percentile(finite, 84)) if finite.size else "nan",
            "flux_erg_s_cm2": fmt(mean * 1e-17),
            "flux_err_erg_s_cm2": fmt(std * 1e-17),
            "snr": fmt(mean / std, 6) if std > 0 else "nan",
            "stable": is_stable(mean, float(np.percentile(finite, 16)) if finite.size else np.nan,
                                float(np.percentile(finite, 84)) if finite.size else np.nan),
            "nboot": int(finite.size),
        })
    write_csv(out_dir / "pyqsofitspec_totals.csv", total_rows)

    corner_ok = make_bootstrap_figures(
        samples, groups, out_dir, nboot,
        corner_keys=cfg["comparison"].get("corner"),
        display=cfg["comparison"].get("labels", {}),
    )
    shutil.rmtree(work, ignore_errors=True)
    total_seconds = time.time() - t_start

    effective = {k: v for k, v in cfg.items() if not k.startswith("_")}
    effective.update({
        "_resolved": {
            "spectrum": meta["file"],
            "layout": meta["layout"],
            "z": z,
            "n_pixels": int(flux.size),
            "n_masked": int(n_removed),
            "error_floor_frac": floor,
            "rest_coverage_angstrom": [round(rest_lo, 1), round(rest_hi, 1)],
            "nboot_fit": nboot,
            "seed": seed,
            "package": str(pkg.__file__),
            "upstream_commit": "aa326ed0b13003b22588a0ad9c8a369d9a2de6dd",
        }
    })
    with (out_dir / "config.effective.json").open("w") as fh:
        json.dump(effective, fh, indent=2)

    run = {
        "tool": "pyqsofitspec_line",
        "tool_version": "PyQSOFitSpec @ aa326ed0b13003b22588a0ad9c8a369d9a2de6dd",
        "method": {
            "continuum": "Fe II (UV+optical) + Balmer continuum + power law + polynomial",
            "lines": cfg["linemodel"] + " (skew-normal) profiles, kmpfit least squares",
            "uncertainty": "parametric bootstrap: flux + N(0, sigma) refit, mean/std over nboot",
            "n_internal_mc_trials_per_fit": 0,
        },
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "astropy": __import__("astropy").__version__,
            "scipy": __import__("scipy").__version__,
            "matplotlib": __import__("matplotlib").__version__,
            "kapteyn": __import__("kapteyn").__version__,
        },
        "command": [sys.executable, str(Path(__file__).name)] + sys.argv[1:],
        "input": meta,
        "name": name,
        "redshift": z,
        "rest_coverage_angstrom": [round(rest_lo, 1), round(rest_hi, 1)],
        "nboot_fit": nboot,
        "seed": seed,
        "error_floor_frac": floor,
        "fit_quality": fit_status,
        "iterations": iteration_info,
        "runtime_seconds": round(total_seconds, 2),
        "runtime_per_iteration_seconds": [it["wall_seconds"] for it in iteration_info],
        "lines": line_rows,
        "totals": total_rows,
        "corner_plot": corner_ok,
        "files": {
            "lines_csv": "pyqsofitspec_lines.csv",
            "native_csv": "pyqsofitspec_out.csv",
            "totals_csv": "pyqsofitspec_totals.csv",
            "bootstrap_csv": "pyqsofitspec_bootstrap.csv",
            "bootstrap_png": "pyqsofitspec_bootstrap.png",
            "corner_png": "pyqsofitspec_corner.png" if corner_ok else None,
            "fit_figure": fig_files,
            "config_effective": "config.effective.json",
            "run_log": "run.log",
        },
        "caveats": [
            "Reported line values are bootstrap means; errors are the bootstrap "
            "standard deviation (upstream PyQSOFitSpec convention), not a "
            "covariance matrix.",
            f"Only {nboot} bootstrap realisations were run, so the uncertainties "
            "are themselves noisy at the ~1/sqrt(2*(nboot-1)) level.",
            "Ugriz-type flux calibration slippage and Fe II template systematics "
            "dominate over the statistical error; the bootstrap captures neither.",
            "PyQSOFitSpec fits a single skewed profile per listed component; the "
            "Mg II 2796/2804 doublet is a single blended component, and the "
            "[O III] 5007 total is core + broad wing.",
            "Component type (broad/narrow) is assigned by the fitted sigma "
            "(log10 sigma > 0.0017 -> broad), matching QSOFit.line_prop.",
        ],
    }
    pinned = [row["line"] for row in line_rows if row.get("note")]
    if pinned:
        run["caveats"].append(
            "FWHM pinned at a sigval prior bound for " + ", ".join(pinned) +
            ": only the flux is measured for those components (see the 'note' "
            "column of pyqsofitspec_lines.csv)."
        )
    unstable = [row["line"] for row in line_rows if not row.get("stable")]
    if unstable:
        run["caveats"].append(
            "unstable/multimodal components (16-84 interval > 25% of the mean): " +
            ", ".join(unstable) + "; use the summed totals in "
            "pyqsofitspec_totals.csv for line-ratio work."
        )
    with (out_dir / "run.json").open("w") as fh:
        json.dump(run, fh, indent=2)

    print("")
    print(f"Done in {total_seconds:.1f} s ({nboot} bootstrap fits). Outputs in {out_dir}")
    for row in total_rows:
        print(f"  {row['total']:<10} {row['flux_1e17']:>12} +/- {row['flux_err_1e17']:<12} "
              f"(1e-17 erg/s/cm2)  S/N={row['snr']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
