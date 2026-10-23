#!/usr/bin/env python3
"""S3Fit simultaneous spectrum + photometric-SED / emission-line fit.

This is the production adapter between the repository's canonical inputs

    inputs/<source>_z_<z>/raw/spec-*.fits
    inputs/<source>_z_<z>/photometry/photometry.txt

and S3Fit 2.2.6 (``pip install s3fit==2.2.6``).

S3Fit's statistical error estimate is a set of Monte-Carlo mock spectra
(``num_mocks``), not an MCMC.  Each mock is drawn from the observed spectrum
and its errors, refitted, and the spread of the fitted quantities is reported.
The original-data fit is loop 0; mock loops are 1..N.

The QSO mode deliberately has no stellar SSP component: the model is
AGN powerlaw + Fe II + Balmer continuum + SKIRTOR torus + NLR/BLR emission
lines.  S3Fit does not require an SSP library when the ``stellar`` model is
omitted; this is verified by the absence of the ``stellar`` key in the
effective model configuration and by a successful fit.

Outputs (inside ``--out``)
--------------------------
s3fit_lines.csv                  per-component line fluxes/FWHM/velocity
s3fit_fit.png                    data, total model, components, residuals, SED
s3fit_mc.png                     Monte-Carlo flux/FWHM distributions
s3fit_output.npz                 compact spectra, SED, and MC arrays
model_config.json                effective S3Fit model configuration
fit_config.effective.json        effective fitting controls
run.json                         provenance, chi2, runtimes, detections
s3fit.log                        full S3Fit log
pyqsofit_comparison.csv          optional comparison with pyqsofit_uv outputs
s3fit_output.pkl.gz              native pickle only when compact/requested
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import time
import traceback
from pathlib import Path

import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")

# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

C_KMS = 299792.458
FLUX_UNIT_CGS = "erg s-1 cm-2 angstrom-1"
MJY_TO_CGS = 1e-26  # erg s-1 cm-2 Hz-1
LOG10 = math.log(10.0)


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


class Logger:
    """Tee a small textual log to stdout and to run.log."""

    def __init__(self, path: Path):
        self.path = path
        self.lines: list[str] = []
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, msg: str = "") -> None:
        line = f"[{now()}] {msg}" if msg else ""
        print(line, flush=True)
        self.lines.append(line)
        with self.path.open("a") as fh:
            fh.write(line + "\n")


def load_json(path: Path):
    with Path(path).open() as fh:
        return json.load(fh)


def json_sanitize(obj):
    """Recursively make an object strict-JSON safe (NaN/Inf -> null)."""
    if isinstance(obj, dict):
        return {str(k): json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_sanitize(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [json_sanitize(v) for v in obj.tolist()]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return v if math.isfinite(v) else None
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, Path):
        return str(obj)
    return obj


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(json_sanitize(obj), fh, indent=2, sort_keys=False, allow_nan=False)
        fh.write("\n")


def json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    return str(obj)


def finite(value, default=None):
    try:
        v = float(value)
        return v if math.isfinite(v) else default
    except Exception:
        return default


def mad_std(values) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 2:
        return float("nan")
    med = np.median(values)
    return float(1.4826 * np.median(np.abs(values - med)))


def pct(values, q) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan")
    return float(np.percentile(values, q))


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text)).strip("_") or "value"


def decode_strings(arr) -> list[str]:
    return [str(x) for x in np.asarray(arr).tolist()]


# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------

DEFAULT_SPECTRUM_GLOBS = (
    "raw/spec-*.fits",
    "raw/*.fits",
    "spectrum.fits",
    "*.fits",
)


def find_spectrum(input_dir: Path, explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.exists():
            p = input_dir / explicit
        if not p.exists():
            raise FileNotFoundError(f"spectrum not found: {explicit}")
        return p
    for pattern in DEFAULT_SPECTRUM_GLOBS:
        hits = sorted(input_dir.glob(pattern))
        hits = [h for h in hits if h.is_file()]
        if hits:
            return hits[0]
    raise FileNotFoundError(f"no FITS spectrum found under {input_dir}")


def find_photometry(input_dir: Path, explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        if not p.exists():
            p = input_dir / explicit
        return p if p.exists() else None
    for name in ("photometry/photometry.txt", "photometry.txt"):
        p = input_dir / name
        if p.exists():
            return p
    return None


def resolve_model_config(config_path: Path, config_dir: Path, model_root: Path) -> dict:
    """Load model_config.json and inline/abspath its referenced JSON/files.

    S3Fit 2.2.6's flat model registry is used here: each model entry has
    ``enable``, ``config`` and optional ``file``/``use_pyneb`` keys.  A nested
    ``mods`` wrapper (newer S3Fit) is accepted and flattened, because the
    pinned 2.2.6 FitFrame only normalises the flat format.
    """
    model_cfg = load_json(config_path)
    if "mods" in model_cfg:
        mods = dict(model_cfg["mods"])
    else:
        mods = {k: v for k, v in model_cfg.items()
                if k not in ("root_info", "info", "mods")}

    for mod_name, mod in mods.items():
        cfg = mod.get("config")
        if isinstance(cfg, str):
            cfg_path = config_dir / cfg
            if not cfg_path.exists():
                # a config entry may be a path relative to the model root
                cfg_path = model_root / cfg
            mod["config"] = load_json(cfg_path)
        elif isinstance(cfg, dict):
            pass
        else:
            raise ValueError(f"model '{mod_name}' has no usable 'config' entry")

        fname = mod.get("file")
        if isinstance(fname, str):
            p = Path(fname)
            if not p.is_absolute():
                p = model_root / p
            if not p.exists():
                raise FileNotFoundError(f"model '{mod_name}' file not found: {p}")
            mod["file"] = str(p)
    return mods


def load_fit_config(config_path: Path | None, defaults: dict) -> tuple[dict, Path | None]:
    if config_path is None:
        return dict(defaults), None
    p = Path(config_path)
    if p.is_dir():
        fit_path = p / "fit_config.json"
        cfg = load_json(fit_path) if fit_path.exists() else {}
        return {**defaults, **cfg}, p
    cfg = load_json(p)
    if "fit_config" in cfg:
        cfg = cfg["fit_config"]
    return {**defaults, **cfg}, p.parent


# ---------------------------------------------------------------------------
# input readers
# ---------------------------------------------------------------------------

def _table_hdu(hdul):
    for name in ("COADD", "SPECTRUM", "SPEC"):
        if name in hdul:
            return hdul[name]
    for hdu in hdul:
        cols = getattr(hdu, "columns", None)
        if cols is None or hdu.data is None:
            continue
        names = {c.lower() for c in cols.names}
        if {"flux", "loglam"} <= names or {"flux", "wl"} <= names or {"flux", "wave"} <= names:
            return hdu
    raise ValueError("could not locate a spectrum table (need FLUX and LOGLAM/WL)")


def _col(table, *names):
    cols = {c.lower(): c for c in table.columns.names}
    for name in names:
        if name.lower() in cols:
            return np.asarray(table[cols[name.lower()]], dtype=float)
    return None


def read_spectrum(path: Path, z_cli: float | None) -> dict:
    from astropy.io import fits

    with fits.open(path, memmap=False) as hdul:
        hdr0 = hdul[0].header
        tab = _table_hdu(hdul)
        data = tab.data

        flux = _col(data, "FLUX", "FLUXCAL")
        if flux is None:
            raise ValueError(f"{path}: no FLUX column")
        loglam = _col(data, "LOGLAM")
        wl = _col(data, "WL", "WAVE")
        if loglam is not None:
            wave = 10.0 ** loglam
            dloglam = float(np.median(np.diff(loglam)))
        elif wl is not None:
            wave = wl
            dloglam = float(np.median(np.diff(np.log(wl))))
        else:
            raise ValueError(f"{path}: no LOGLAM/WL column")

        ivar = _col(data, "IVAR", "IVARIANCE")
        if ivar is None:
            stdev = _col(data, "STDEV", "ERROR", "ERR")
            if stdev is None:
                raise ValueError(f"{path}: no IVAR/STDEV column")
            ivar = 1.0 / np.square(np.clip(stdev, 1e-30, None))
        wdisp = _col(data, "WDISP", "WRESL")
        and_mask = _col(data, "AND_MASK")
        or_mask = _col(data, "OR_MASK")

        # redshift: SPALL first, then source.json / CLI elsewhere
        z = None
        try:
            if "SPALL" in hdul:
                z = float(np.asarray(hdul["SPALL"].data["Z"]).ravel()[0])
        except Exception:
            z = None
        if z is None:
            for key in ("Z", "REDSHIFT", "z"):
                if key in hdr0:
                    try:
                        z = float(hdr0[key])
                        break
                    except Exception:
                        pass

        bunit = str(tab.header.get("BUNIT", hdr0.get("BUNIT", ""))).upper()
        scale = 1.0
        m = re.search(r"1E([+-]?\d+)", bunit.replace(" ", ""))
        if m:
            scale = 10.0 ** int(m.group(1))
        elif "1E-17" in bunit:
            scale = 1e-17
        elif scale == 1.0 and np.nanmedian(np.abs(flux)) > 1.0:
            # SDSS-style 1e-17 fluxes with a missing/unhelpful BUNIT
            scale = 1e-17

    # SDSS COADD is vacuum; default S3Fit would otherwise apply air->vac.
    return {
        "path": str(path),
        "wave": wave,
        "flux": flux,
        "ivar": ivar,
        "wdisp": wdisp,
        "and_mask": and_mask,
        "or_mask": or_mask,
        "dloglam": dloglam,
        "flux_scale": scale,
        "z": z,
    }


def resolution_from_wdisp(wdisp, dloglam: float) -> np.ndarray:
    if wdisp is None:
        return np.full(1, 2000.0)
    w = np.asarray(wdisp, dtype=float)
    good = np.isfinite(w) & (w > 0)
    med = float(np.median(w[good])) if good.any() else 1.0
    w = np.where(good, w, med)
    # SDSS WDISP is the 1-sigma resolution width in pixels; one pixel is
    # dlog10(lambda) = 1e-4, so dln(lambda) = ln(10)*dloglam.
    dln = LOG10 * dloglam
    R = 1.0 / (2.354820045 * w * dln)
    return np.clip(R, 300.0, 20000.0)


def read_photometry(path: Path) -> dict[str, tuple[float, float, float]]:
    """Read the repository's one-row CIGALE photometry table (mJy)."""
    text = Path(path).read_text().splitlines()
    if not text:
        return {}
    header = text[0].split()
    if len(text) < 2:
        return {}
    row = text[1].split()
    if len(row) != len(header):
        # tolerate comma-separated files as well
        header = [h.strip() for h in text[0].split(",")]
        row = [r.strip() for r in text[1].split(",")]
    rec = dict(zip(header, row))

    aliases = {
        "sloan.sdss.g": "SDSS_gp",
        "sloan.sdss.r": "SDSS_rp",
        "sloan.sdss.i": "SDSS_ip",
        "sloan.sdss.z": "SDSS_zp",
        "SDSS_g": "SDSS_gp",
        "SDSS_r": "SDSS_rp",
        "SDSS_i": "SDSS_ip",
        "SDSS_z": "SDSS_zp",
        "SDSS_gp": "SDSS_gp",
        "SDSS_rp": "SDSS_rp",
        "SDSS_ip": "SDSS_ip",
        "SDSS_zp": "SDSS_zp",
        "wise.W1": "WISE_1",
        "wise.W2": "WISE_2",
        "wise.W3": "WISE_3",
        "wise.W4": "WISE_4",
        "WISE_W1": "WISE_1",
        "WISE_W2": "WISE_2",
        "WISE_W3": "WISE_3",
        "WISE_W4": "WISE_4",
        "WISE_1": "WISE_1",
        "WISE_2": "WISE_2",
        "WISE_3": "WISE_3",
        "WISE_4": "WISE_4",
    }
    out = {}
    for col, s3name in aliases.items():
        if col not in rec:
            continue
        f = finite(rec.get(col))
        e = finite(rec.get(col + "_err", rec.get(col.replace(".", "_") + "_err")))
        if f is not None and e is not None and f > 0 and e > 0:
            out[s3name] = (float(f), float(e), str(col))
    return out


# ---------------------------------------------------------------------------
# output extraction
# ---------------------------------------------------------------------------

def loop_times(log_lines: list[str]) -> dict:
    out = []
    for msg in log_lines:
        m = re.search(r"Loop\s+(\d+)/(\d+)\s+ends,\s+chi_sq\s*=\s*([0-9.eE+-]+)\s+([0-9.]+)s", msg)
        if m:
            out.append({"loop": int(m.group(1)), "n_loops": int(m.group(2)),
                        "chi_sq": float(m.group(3)), "seconds": float(m.group(4))})
    original = out[0]["seconds"] if out else None
    mc = sum(x["seconds"] for x in out[1:]) if len(out) > 1 else 0.0 if out else None
    return {
        "loops": out,
        "original_fit_seconds": original,
        "mc_fit_seconds": mc,
    }


def good_loop_mask(ff) -> np.ndarray:
    """Return loops usable for MC statistics, always keeping loop 0."""
    n = ff.num_loops
    mask = np.zeros(n, dtype=bool)
    try:
        mask = np.asarray(ff.fit_quality_l, dtype=bool).copy()
    except Exception:
        pass
    if not mask.any():
        chi = None
        for step in ("joint_fit_3", "joint_fit_2"):
            if step in ff.output_S:
                chi = np.asarray(ff.output_S[step]["chi_sq_l"], dtype=float)
                break
        if chi is not None:
            mask = np.isfinite(chi) & (chi > 0)
    if mask.size and not mask[0]:
        mask[0] = True
    return mask


def extract_lines(ff, step: str, z: float, logger: Logger) -> tuple[list[dict], dict]:
    """Build per-component and total line rows from S3Fit's line frame."""
    line_mod = ff.model_dict["line"]["spec_mod"]
    out = line_mod.extract_results(
        step=step, if_print_results=False, if_return_results=True
    )
    scale = float(ff.spec_flux_scale)
    names = decode_strings(line_mod.linename_n)
    rest = {name: float(w) for name, w in zip(names, line_mod.linerest_n)}
    comps = list(line_mod.cframe.comp_name_c)
    good = good_loop_mask(ff)

    def stats(arr, comp_name):
        arr = np.asarray(arr, dtype=float)
        mc = arr[1:][good[1:]] if arr.size > 1 else np.asarray([])
        mc = mc[np.isfinite(mc)]
        return {
            "flux": float(arr[0]) * scale if arr.size else float("nan"),
            "err": float(np.std(mc, ddof=1)) * scale if mc.size >= 2 else 0.0,
            "mc_mean": float(np.mean(mc)) * scale if mc.size else float("nan"),
            "p16": pct(mc, 16) * scale,
            "p84": pct(mc, 84) * scale,
            "n_mc": int(mc.size),
        }

    rows: list[dict] = []
    for comp in comps:
        values = out[comp]["value_Vl"]
        fwhm_arr = np.asarray(values.get("fwhm", [np.nan]), dtype=float)
        voff_arr = np.asarray(values.get("voff", [np.nan]), dtype=float)
        av_arr = np.asarray(values.get("Av", [np.nan]), dtype=float)
        den_arr = np.asarray(values.get("log_e_den", [np.nan]), dtype=float)
        for line in names:
            s = stats(values[line], comp)
            fwhm_mc = fwhm_arr[1:][good[1:]] if fwhm_arr.size > 1 else np.asarray([])
            voff_mc = voff_arr[1:][good[1:]] if voff_arr.size > 1 else np.asarray([])
            snr = s["flux"] / s["err"] if s["err"] and np.isfinite(s["err"]) else float("nan")
            rows.append({
                "component": comp,
                "line": line,
                "rest_wavelength_angstrom": rest.get(line, float("nan")),
                "flux_erg_s_cm2": s["flux"],
                "flux_err_erg_s_cm2": s["err"],
                "flux_1e17": s["flux"] / 1e-17,
                "flux_err_1e17": s["err"] / 1e-17,
                "fwhm_kms": float(fwhm_arr[0]) if fwhm_arr.size else float("nan"),
                "fwhm_err_kms": float(np.std(fwhm_mc, ddof=1)) if fwhm_mc.size >= 2 else 0.0,
                "velocity_kms": float(voff_arr[0]) if voff_arr.size else float("nan"),
                "velocity_err_kms": float(np.std(voff_mc, ddof=1)) if voff_mc.size >= 2 else 0.0,
                "av": float(av_arr[0]) if av_arr.size else float("nan"),
                "log_e_den": float(den_arr[0]) if den_arr.size else float("nan"),
                "mc_mean_flux_erg_s_cm2": s["mc_mean"],
                "mc_p16_flux_erg_s_cm2": s["p16"],
                "mc_p84_flux_erg_s_cm2": s["p84"],
                "snr": snr,
                "n_mc": s["n_mc"],
                "detected": bool(np.isfinite(snr) and snr >= 3.0),
            })
        logger(f"  {comp}: {int(line_mod.mask_free_cn[comps.index(comp)].sum())} free lines, "
               f"FWHM={fwhm_arr[0]:.1f} km/s, voff={voff_arr[0]:.1f} km/s")

    for line in names:
        s = stats(out["tot"]["value_Vl"][line], "tot")
        snr = s["flux"] / s["err"] if s["err"] and np.isfinite(s["err"]) else float("nan")
        rows.append({
            "component": "total",
            "line": line,
            "rest_wavelength_angstrom": rest.get(line, float("nan")),
            "flux_erg_s_cm2": s["flux"],
            "flux_err_erg_s_cm2": s["err"],
            "flux_1e17": s["flux"] / 1e-17,
            "flux_err_1e17": s["err"] / 1e-17,
            "fwhm_kms": float("nan"),
            "fwhm_err_kms": float("nan"),
            "velocity_kms": float("nan"),
            "velocity_err_kms": float("nan"),
            "av": float("nan"),
            "log_e_den": float("nan"),
            "mc_mean_flux_erg_s_cm2": s["mc_mean"],
            "mc_p16_flux_erg_s_cm2": s["p16"],
            "mc_p84_flux_erg_s_cm2": s["p84"],
            "snr": snr,
            "n_mc": s["n_mc"],
            "detected": bool(np.isfinite(snr) and snr >= 3.0),
        })

    rows.sort(key=lambda r: (r["rest_wavelength_angstrom"], r["component"]))
    return rows, out


def write_lines_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "component", "line", "rest_wavelength_angstrom",
        "flux_erg_s_cm2", "flux_err_erg_s_cm2", "flux_1e17", "flux_err_1e17",
        "fwhm_kms", "fwhm_err_kms", "velocity_kms", "velocity_err_kms",
        "av", "log_e_den", "mc_mean_flux_erg_s_cm2",
        "mc_p16_flux_erg_s_cm2", "mc_p84_flux_erg_s_cm2",
        "snr", "n_mc", "detected",
    ]
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


# ---------------------------------------------------------------------------
# plots
# ---------------------------------------------------------------------------

def _flux_cgs(arr, scale):
    return np.asarray(arr, dtype=float) * float(scale)


def make_fit_figure(path: Path, ff, step: str, z: float, lines: list[dict],
                    mode: str, logger: Logger) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    scale = float(ff.spec_flux_scale)
    out = ff.output_mc
    wave_rest = ff.spec["wave_w"] / (1.0 + z)
    data = _flux_cgs(ff.spec["flux_w"], scale)
    ferr = _flux_cgs(ff.spec["ferr_w"], scale)
    model = _flux_cgs(out["tot"]["fmod"]["spec_lw"][0], scale)
    resid = _flux_cgs(out["tot"]["fres"]["spec_lw"][0], scale)

    have_phot = bool(getattr(ff, "have_phot", False))
    if have_phot:
        fig = plt.figure(figsize=(13, 10))
        gs = GridSpec(3, 1, height_ratios=[2.3, 1.0, 1.7], hspace=0.05)
        ax = fig.add_subplot(gs[0])
        axr = fig.add_subplot(gs[1], sharex=ax)
        axs = fig.add_subplot(gs[2])
    else:
        fig = plt.figure(figsize=(13, 8))
        gs = GridSpec(2, 1, height_ratios=[2.5, 1.0], hspace=0.05)
        ax = fig.add_subplot(gs[0])
        axr = fig.add_subplot(gs[1], sharex=ax)
        axs = None

    ax.plot(wave_rest, data, color="0.35", lw=1.0, label="observed spectrum", zorder=2)
    ax.fill_between(wave_rest, data - 3 * ferr, data + 3 * ferr,
                    color="0.7", alpha=0.25, lw=0, label=r"$\pm3\sigma$")
    ax.plot(wave_rest, model, color="C1", lw=1.8, label="total model", zorder=4)

    styles = {
        "agn": ("C4", "--", 1.2),
        "torus": ("C8", "-.", 1.2),
        "line": ("C2", "-", 1.2),
    }
    for mod, (color, ls, lw) in styles.items():
        if mod not in out:
            continue
        if "tot" in out[mod] and "spec_lw" in out[mod]["tot"]:
            ax.plot(wave_rest, _flux_cgs(out[mod]["tot"]["spec_lw"][0], scale),
                    color=color, ls=ls, lw=lw, label=f"{mod} total", zorder=3)
        if mod == "line":
            for comp in out[mod]:
                if comp == "tot":
                    continue
                ax.plot(wave_rest, _flux_cgs(out[mod][comp]["spec_lw"][0], scale),
                        color=color, lw=0.8, alpha=0.75, label=f"line:{comp}", zorder=3)
        if mod == "agn":
            for comp in out[mod]:
                if comp == "tot":
                    continue
                ax.plot(wave_rest, _flux_cgs(out[mod][comp]["spec_lw"][0], scale),
                        color=color, lw=0.7, alpha=0.55, label=f"agn:{comp}", zorder=3)

    # mark the fitted optical lines
    for row in lines:
        if row["component"] != "total" or not np.isfinite(row["flux_erg_s_cm2"]):
            continue
        if not row["detected"]:
            continue
        ax.axvline(row["rest_wavelength_angstrom"], color="0.6", lw=0.35, alpha=0.35, zorder=1)

    ax.set_ylabel(r"$F_\lambda$ (erg s$^{-1}$ cm$^{-2}$ $\AA^{-1}$)")
    ax.legend(ncol=4, fontsize=6.5, loc="upper right")
    ax.set_title(f"S3Fit {mode} fit   z={z:.5f}   "
                 fr"$\chi^2_\nu$={ff.output_S[step]['chi_sq_l'][0]:.3f}")
    ax.set_xlim(max(2000, np.nanmin(wave_rest)), min(7500, np.nanmax(wave_rest)))
    ax.tick_params(labelbottom=False)

    axr.plot(wave_rest, resid / np.where(ferr > 0, ferr, np.nan),
             color="C0", lw=0.7)
    axr.axhline(0, color="k", lw=0.5)
    for y in (-3, 3):
        axr.axhline(y, color="C3", lw=0.5, ls="--", alpha=0.7)
    axr.set_ylabel(r"residual/$\sigma$")
    axr.set_xlabel(r"rest wavelength ($\AA$)")

    if axs is not None:
        sed_wave = np.asarray(ff.sed["wave_w"], dtype=float)
        sed_rest_um = sed_wave / (1.0 + z) / 1e4
        sed_tot = _flux_cgs(out["tot"]["fmod"]["sed_lw"][0], scale)
        axs.plot(sed_rest_um, sed_wave * sed_tot, color="C1", lw=1.8, label="total SED")
        for mod, (color, ls, lw) in styles.items():
            if mod in out and "tot" in out[mod] and "sed_lw" in out[mod]["tot"]:
                axs.plot(sed_rest_um, sed_wave * _flux_cgs(out[mod]["tot"]["sed_lw"][0], scale),
                         color=color, ls=ls, lw=lw, label=f"{mod} SED")
        pw = np.asarray(ff.phot["wave_b"], dtype=float)
        pf = _flux_cgs(ff.phot["flux_b"], scale)
        pe = _flux_cgs(ff.phot["ferr_b"], scale)
        axs.errorbar(pw / (1.0 + z) / 1e4, pw * pf, yerr=pw * pe,
                     fmt="o", ms=5, color="k", capsize=2, label="photometry", zorder=5)
        axs.set_xscale("log")
        axs.set_yscale("log")
        axs.set_xlabel(r"rest wavelength ($\mu$m)")
        axs.set_ylabel(r"$\lambda F_\lambda$ (erg s$^{-1}$ cm$^{-2}$ s$^{-1}$)")
        axs.legend(ncol=5, fontsize=6.5)

    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger(f"wrote {path}")


def make_mc_figure(path: Path, ff, line_rows: list[dict], line_out: dict,
                   z: float, fit_cfg: dict, logger: Logger) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    good = good_loop_mask(ff)
    have_mc = bool(good[1:].any())
    line_mod = ff.model_dict["line"]["spec_mod"]
    valid = [str(x) for x in line_mod.linename_n]
    requested = [str(x) for x in fit_cfg.get("mc_plot_lines", ["H-beta", "[O III]:5008", "H-alpha"])]
    chosen = [x for x in requested if x in valid]
    for x in valid:
        if len(chosen) >= 3:
            break
        if x not in chosen:
            chosen.append(x)
    chosen = chosen[:3]
    comps = [str(x) for x in line_mod.cframe.comp_name_c]

    fig, axes = plt.subplots(2, 3, figsize=(13, 7.2))
    axes = np.atleast_2d(axes)
    scale = float(ff.spec_flux_scale)

    for j, line in enumerate(chosen):
        ax = axes[0, j]
        arr = np.asarray(line_out["tot"]["value_Vl"][line], dtype=float) * scale
        mc = arr[1:][good[1:]]
        mc = mc[np.isfinite(mc)]
        if mc.size:
            ax.hist(mc / 1e-17, bins=max(6, min(20, mc.size)), color="C0", alpha=0.7,
                    edgecolor="k", lw=0.4)
        ax.axvline(arr[0] / 1e-17, color="C3", lw=1.5, label="original")
        ax.set_title(line)
        ax.set_xlabel(r"integrated flux ($10^{-17}$ erg s$^{-1}$ cm$^{-2}$)")
        ax.set_ylabel("MC count")
        if mc.size:
            ax.text(0.97, 0.95, f"MC {np.mean(mc)/1e-17:.2f} $\\pm$ {np.std(mc, ddof=1)/1e-17:.2f}\n"
                                f"orig {arr[0]/1e-17:.2f}",
                    transform=ax.transAxes, ha="right", va="top", fontsize=7)
        ax.legend(fontsize=7, loc="upper left")

    # FWHM distributions for each line component
    for j, comp in enumerate(comps[:2]):
        ax = axes[1, j]
        fw = np.asarray(line_out[comp]["value_Vl"].get("fwhm", []), dtype=float)
        mc = fw[1:][good[1:]]
        mc = mc[np.isfinite(mc)]
        if mc.size:
            ax.hist(mc, bins=max(6, min(20, mc.size)), color="C2", alpha=0.7,
                    edgecolor="k", lw=0.4)
        if fw.size:
            ax.axvline(fw[0], color="C3", lw=1.5, label="original")
        ax.set_title(f"{comp} FWHM")
        ax.set_xlabel("FWHM (km s$^{-1}$)")
        ax.set_ylabel("MC count")
        if mc.size:
            ax.text(0.97, 0.95, f"MC {np.mean(mc):.0f} $\\pm$ {np.std(mc, ddof=1):.0f}\n"
                                f"orig {fw[0]:.0f}",
                    transform=ax.transAxes, ha="right", va="top", fontsize=7)
        ax.legend(fontsize=7, loc="upper left")

    ax = axes[1, 2]
    chi = np.asarray(ff.output_S["joint_fit_3" if getattr(ff, "have_phot", False) else "joint_fit_2"]["chi_sq_l"], dtype=float)
    mc = chi[1:][good[1:]]
    mc = mc[np.isfinite(mc)]
    if mc.size:
        ax.hist(mc, bins=max(6, min(20, mc.size)), color="C4", alpha=0.7,
                edgecolor="k", lw=0.4)
    ax.axvline(chi[0], color="C3", lw=1.5, label="original")
    ax.set_title(r"reduced $\chi^2_\nu$")
    ax.set_xlabel(r"$\chi^2_\nu$")
    ax.set_ylabel("MC count")
    if mc.size:
        ax.text(0.97, 0.95, f"MC {np.mean(mc):.3f} $\\pm$ {np.std(mc, ddof=1):.3f}\n"
                            f"orig {chi[0]:.3f}",
                transform=ax.transAxes, ha="right", va="top", fontsize=7)
    ax.legend(fontsize=7, loc="upper left")

    if not have_mc:
        fig.suptitle("No successful Monte-Carlo loops: histograms are empty", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger(f"wrote {path}")


# ---------------------------------------------------------------------------
# comparison with pyqsofit_uv
# ---------------------------------------------------------------------------

def read_pyqsofit_lines(path: Path) -> dict[tuple[str, str], dict]:
    out = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            key = (row["line"].strip(), row["component"].strip())
            out[key] = row
    return out


def compare_pyqsofit(pyq_dir: Path | None, line_rows: list[dict],
                     spec_calib_ratio: float, source: str, out_csv: Path) -> dict:
    if pyq_dir is None:
        return {"status": "unavailable", "reason": "no --pyqsofit-dir"}
    candidates = [
        pyq_dir / "pyqsofit_lines.csv",
        pyq_dir / "pyqsofit" / "pyqsofit_lines.csv",
        pyq_dir / "lines.csv",
    ]
    src = next((p for p in candidates if p.exists()), None)
    if src is None:
        return {"status": "unavailable", "reason": f"no pyqsofit_lines.csv under {pyq_dir}"}

    pyq = read_pyqsofit_lines(src)
    by_line_comp = {(r["line"], r["component"]): r for r in line_rows}
    mapping = {
        "H-beta": {"pyq_broad": "Hb_br", "pyq_narrow": "Hb_na", "s3_broad": "BLR", "s3_narrow": "NLR"},
        "OIII5007": {"pyq_broad": "OIII5007w", "pyq_narrow": "OIII5007c", "s3_broad": "BLR", "s3_narrow": "NLR"},
        "MgII": {"pyq_broad": "MgII_br", "pyq_narrow": "MgII_na", "s3_broad": "BLR", "s3_narrow": "NLR"},
        "CIII": {"pyq_broad": "CIII_br", "pyq_narrow": "CIII_na", "s3_broad": "BLR", "s3_narrow": "NLR"},
    }
    s3_line_map = {
        "H-beta": "H-beta",
        "OIII5007": "[O III]:5008",
        "MgII": "Mg II]:2804",
        "CIII": "C III]:1909",
    }

    rows = []
    for label, m in mapping.items():
        s3name = s3_line_map[label]
        total = by_line_comp.get((s3name, "total"))
        if total is None:
            continue
        pyq_b = pyq.get((m["pyq_broad"], "broad"))
        pyq_n = pyq.get((m["pyq_narrow"], "narrow"))
        pyq_total = None
        if pyq_b or pyq_n:
            pyq_total = sum(float(x["area_1e17"]) for x in (pyq_b, pyq_n) if x) * 1e-17
        if pyq_total is None or not np.isfinite(pyq_total) or pyq_total <= 0:
            continue

        def add(component_s3, component_pyq, s3row, pyqrow):
            if s3row is None or pyqrow is None:
                return
            s3flux = float(s3row["flux_erg_s_cm2"])
            pflux = float(pyqrow["area_1e17"]) * 1e-17
            if not np.isfinite(s3flux) or pflux <= 0:
                return
            raw = s3flux / spec_calib_ratio if spec_calib_ratio else s3flux
            rows.append({
                "source": source,
                "line": label,
                "component_s3fit": component_s3,
                "component_pyqsofit": component_pyq,
                "s3fit_flux_erg_s_cm2": s3flux,
                "s3fit_flux_err_erg_s_cm2": float(s3row.get("flux_err_erg_s_cm2") or 0),
                "pyqsofit_flux_erg_s_cm2": pflux,
                "ratio_fitted": s3flux / pflux,
                "ratio_rawspec": raw / pflux,
                "difference_rawspec_erg_s_cm2": raw - pflux,
                "spec_calib_ratio": spec_calib_ratio,
                "note": "ratio_rawspec = (S3Fit flux / spec_calib_ratio) / PyQSOFit; no silent normalization change",
            })

        add("total", "total", total, {"area_1e17": pyq_total / 1e-17})
        add(m["s3_broad"], "broad", by_line_comp.get((s3name, m["s3_broad"])), pyq_b)
        add(m["s3_narrow"], "narrow", by_line_comp.get((s3name, m["s3_narrow"])), pyq_n)

    fields = [
        "source", "line", "component_s3fit", "component_pyqsofit",
        "s3fit_flux_erg_s_cm2", "s3fit_flux_err_erg_s_cm2",
        "pyqsofit_flux_erg_s_cm2", "ratio_fitted", "ratio_rawspec",
        "difference_rawspec_erg_s_cm2", "spec_calib_ratio", "note",
    ]
    with out_csv.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

    summary = {
        "status": "ok",
        "reference": str(src),
        "spec_calib_ratio": spec_calib_ratio,
        "rows": len(rows),
        "totals_rawspec": {
            r["line"]: {
                "s3fit_flux_erg_s_cm2": r["s3fit_flux_erg_s_cm2"],
                "pyqsofit_flux_erg_s_cm2": r["pyqsofit_flux_erg_s_cm2"],
                "ratio_rawspec": r["ratio_rawspec"],
                "difference_rawspec_erg_s_cm2": r["difference_rawspec_erg_s_cm2"],
            }
            for r in rows if r["component_s3fit"] == "total"
        },
    }
    return summary


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input_dir", nargs="?", help="canonical source directory")
    ap.add_argument("output_dir", nargs="?", help="output directory")
    ap.add_argument("--input-dir", dest="input_dir_opt")
    ap.add_argument("--out", "--output-dir", dest="output_dir_opt")
    ap.add_argument("--config", default=os.environ.get("S3FIT_CONFIG", "/app/config"),
                    help="config directory (fit_config.json + model_config.json) or a JSON file")
    ap.add_argument("--model-root", default=os.environ.get("S3FIT_MODEL_ROOT", "/app/s3fit_line"),
                    help="root containing model_libraries/ and filters/")
    ap.add_argument("--z", type=float, default=None, help="override systemic redshift")
    ap.add_argument("--spectrum", default=None, help="override spectrum path")
    ap.add_argument("--photometry", default=None, help="override photometry path")
    ap.add_argument("--mode", choices=("spec+sed", "spec"), default=None)
    ap.add_argument("--n-mocks", type=int, default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--pyqsofit-dir", default=None,
                    help="directory holding pyqsofit_lines.csv (mounted at /app/reference)")
    ap.add_argument("--save-pickle", action="store_true",
                    help="write the native S3Fit pickle if it is compact")
    args = ap.parse_args(argv)

    input_dir = Path(args.input_dir_opt or args.input_dir or ".")
    output_dir = Path(args.output_dir_opt or args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log = Logger(output_dir / "run.log")

    source_meta = {}
    source_json = input_dir / "source.json"
    if source_json.exists():
        try:
            source_meta = load_json(source_json)
        except Exception:
            source_meta = {}
    source_key = str(source_meta.get("key") or source_meta.get("name") or input_dir.name)

    defaults = {
        "mode": "spec+sed", "n_mocks": 10, "seed": 42, "threads": 1,
        "spec_wave_medium": "vacuum",
        "spec_flux_unit": FLUX_UNIT_CGS,
        "phot_flux_unit": "mJy",
        "phot_trans_dir": "filters",
        "sed_wave_num": 3000,
        "spec_valid_range": None,
        "spec_invalid_range": None,
        "phot_calib_b": None,
        "fit_space": "log",
        "examine_result": True,
        "accept_chi_sq": 3.0,
        "nlfit_ntry_max": 3,
        "nllsq_max_nfev": 10000,
        "conv_nbin_max": 5,
        "if_run_init_annealing": True,
        "da_niter_max": 10,
        "perturb_scale": 0.02,
        "use_pyneb": False,
        "save_native_pickle": False,
        "native_pickle_max_mb": 25,
        "mc_plot_lines": ["H-beta", "[O III]:5008", "H-alpha"],
    }
    fit_cfg, config_dir = load_fit_config(Path(args.config) if args.config else None, defaults)
    if config_dir is None:
        config_dir = Path(args.config).parent if args.config else Path("/app/config")

    if args.n_mocks is not None:
        fit_cfg["n_mocks"] = args.n_mocks
    if args.seed is not None:
        fit_cfg["seed"] = args.seed
    if args.threads is not None:
        fit_cfg["threads"] = args.threads
    if args.mode is not None:
        fit_cfg["mode"] = args.mode
    if args.save_pickle:
        fit_cfg["save_native_pickle"] = True

    model_root = Path(args.model_root)
    model_cfg_path = config_dir / "model_config.json"
    if not model_cfg_path.exists() and Path(args.config).is_file():
        model_cfg_path = Path(args.config)
    model_config = resolve_model_config(model_cfg_path, config_dir, model_root)
    if "line" in model_config:
        model_config["line"]["use_pyneb"] = bool(fit_cfg.get("use_pyneb", False))

    log("=" * 78)
    log("S3Fit line fit")
    log(f"input_dir   = {input_dir}")
    log(f"output_dir  = {output_dir}")
    log(f"config      = {args.config}")
    log(f"model_root  = {model_root}")
    log(f"models      = {list(model_config)}")
    log(f"mode        = {fit_cfg['mode']}, n_mocks = {fit_cfg['n_mocks']}, "
        f"seed = {fit_cfg['seed']}, threads = {fit_cfg['threads']}")

    # ---- spectrum ----
    spec_path = find_spectrum(input_dir, args.spectrum)
    log(f"spectrum    = {spec_path}")
    spec = read_spectrum(spec_path, args.z)
    z = args.z if args.z is not None else spec["z"]
    if z is None:
        src_json = input_dir / "source.json"
        if src_json.exists():
            z = float(load_json(src_json).get("z"))
    if z is None:
        raise ValueError("systemic redshift not found in FITS/source.json; pass --z")
    z = float(z)
    log(f"redshift    = {z:.8f}")

    wave = np.asarray(spec["wave"], dtype=float)
    flux = np.asarray(spec["flux"], dtype=float) * spec["flux_scale"]
    ivar = np.asarray(spec["ivar"], dtype=float)
    good = np.isfinite(wave) & np.isfinite(flux) & np.isfinite(ivar) & (ivar > 0)
    if spec.get("and_mask") is not None:
        good &= np.asarray(spec["and_mask"]) == 0
    # S3Fit 2.2.6 has an index mismatch if NaN pixels are passed together with
    # a spec_valid_range; remove bad pixels before constructing FitFrame.
    n_bad = int((~good).sum())
    wave = wave[good]
    flux = flux[good]
    ferr = (1.0 / np.sqrt(ivar[good])) * spec["flux_scale"]
    R = resolution_from_wdisp(spec["wdisp"], spec["dloglam"])
    if R.size == 1:
        R = np.full_like(wave, R[0])
    elif R.size != wave.size:
        R = R[good]
    log(f"spectrum: {len(wave)} pixels, {n_bad} masked, "
        f"{wave.min():.1f}-{wave.max():.1f} A obs, R={np.nanmedian(R):.0f}")

    # ---- photometry ----
    phot_path = find_photometry(input_dir, args.photometry)
    phot = read_photometry(phot_path) if phot_path else {}
    mode = str(fit_cfg.get("mode", "spec+sed")).lower()
    if mode not in ("spec+sed", "spec"):
        raise ValueError(f"unknown mode: {mode}")
    if mode == "spec+sed" and len(phot) < 2:
        log("WARNING: fewer than 2 usable photometric bands; falling back to pure-spectrum mode")
        mode = "spec"
    phot_names = list(phot)
    phot_flux = np.array([phot[n][0] for n in phot_names], dtype=float)
    phot_ferr = np.array([phot[n][1] for n in phot_names], dtype=float)
    log(f"photometry  = {phot_path} ({len(phot_names)} bands: {phot_names})" if phot_path else "photometry  = none")

    # ---- run ----
    import s3fit
    from s3fit import FitFrame

    np.random.seed(int(fit_cfg["seed"]))
    kwargs = dict(
        spec_wave_w=wave, spec_flux_w=flux, spec_ferr_w=ferr,
        spec_R_inst_w=R,
        spec_valid_range=fit_cfg.get("spec_valid_range"),
        spec_invalid_range=fit_cfg.get("spec_invalid_range"),
        spec_wave_medium=fit_cfg.get("spec_wave_medium", "vacuum"),
        spec_flux_unit=fit_cfg.get("spec_flux_unit", FLUX_UNIT_CGS),
        v0_redshift=z,
        model_config=model_config,
        num_mocks=int(fit_cfg["n_mocks"]),
        if_use_multi_thread=bool(int(fit_cfg.get("threads", 1)) > 1),
        num_multi_thread=int(fit_cfg.get("threads", 1)),
        fit_space=fit_cfg.get("fit_space", "log"),
        if_examine_result=bool(fit_cfg.get("examine_result", True)),
        accept_chi_sq=float(fit_cfg.get("accept_chi_sq", 3.0)),
        nlfit_ntry_max=int(fit_cfg.get("nlfit_ntry_max", 3)),
        nllsq_max_nfev=int(fit_cfg.get("nllsq_max_nfev", 10000)),
        conv_nbin_max=int(fit_cfg.get("conv_nbin_max", 5)),
        if_run_init_annealing=bool(fit_cfg.get("if_run_init_annealing", True)),
        da_niter_max=int(fit_cfg.get("da_niter_max", 10)),
        perturb_scale=float(fit_cfg.get("perturb_scale", 0.02)),
        if_print_steps=True, if_plot_steps=False, if_plot_results=False,
        if_plot_icon=False,
        model_R_ratio=2,
        accept_fmod_SN=2,
        accept_absorption_SN=2,
    )
    if mode == "spec+sed":
        trans_dir = model_root / str(fit_cfg.get("phot_trans_dir", "filters"))
        kwargs.update(dict(
            phot_name_b=phot_names,
            phot_flux_b=phot_flux,
            phot_ferr_b=phot_ferr,
            phot_flux_unit=fit_cfg.get("phot_flux_unit", "mJy"),
            phot_trans_dir=str(trans_dir),
            sed_wave_num=int(fit_cfg["sed_wave_num"]) if fit_cfg.get("sed_wave_num") else None,
            phot_calib_b=fit_cfg.get("phot_calib_b"),
            inst_calib_ratio=0.1,
            if_rev_inst_calib_ratio=True,
        ))
    log(f"initializing FitFrame (mode={mode})")
    ff = FitFrame(**kwargs)
    log(f"FitFrame initialized; spec_flux_scale={ff.spec_flux_scale:.3e}; "
        f"models={list(ff.model_dict)}; have_phot={ff.have_phot}")
    if getattr(ff, "have_phot", False):
        ratio = float(getattr(ff, "spec_calib_ratio", 1.0))
        log(f"spectrum/photometry calibration ratio = {ratio:.6f} "
            "(spectrum multiplied by this; recorded in run.json)")
    else:
        ratio = 1.0

    t0 = time.time()
    fit_error = None
    try:
        ff.main_fit()
    except Exception as exc:  # noqa: BLE001
        fit_error = f"{type(exc).__name__}: {exc}"
        log(f"ERROR during main_fit: {fit_error}")
        log(traceback.format_exc())
        raise
    runtime = time.time() - t0
    log(f"main_fit finished in {runtime:.1f}s")

    step = "joint_fit_3" if getattr(ff, "have_phot", False) else "joint_fit_2"
    chi_l = np.asarray(ff.output_S[step]["chi_sq_l"], dtype=float)
    good_loops = good_loop_mask(ff)
    chi_mc = chi_l[1:][good_loops[1:]]
    chi_mc = chi_mc[np.isfinite(chi_mc)]
    chi2 = {
        "reduced_chi2_original": float(chi_l[0]),
        "reduced_chi2_mc_mean": float(np.mean(chi_mc)) if chi_mc.size else float("nan"),
        "reduced_chi2_mc_std": float(np.std(chi_mc, ddof=1)) if chi_mc.size >= 2 else float("nan"),
        "chi2_l": chi_l.tolist(),
        "n_good_loops": int(np.sum(good_loops)),
    }
    log(f"reduced chi2: original={chi2['reduced_chi2_original']:.3f}, "
        f"MC={chi2['reduced_chi2_mc_mean']:.3f} +/- {chi2['reduced_chi2_mc_std']:.3f}")

    # ---- extract lines / parameters ----
    line_rows, line_out = extract_lines(ff, step, z, log)
    write_lines_csv(output_dir / "s3fit_lines.csv", line_rows)

    # AGN/torus properties
    model_props = {}
    for mod in ("agn", "torus"):
        if mod not in ff.model_dict:
            continue
        try:
            mout = ff.model_dict[mod]["spec_mod"].extract_results(
                step=step, if_print_results=False, if_return_results=True)
            model_props[mod] = {
                comp: {k: float(np.asarray(v, dtype=float)[0])
                       for k, v in vals["value_Vl"].items()
                       if np.asarray(v).ndim == 1 and np.asarray(v).size >= 1
                       and np.isscalar(np.asarray(v, dtype=float)[0])}
                for comp, vals in mout.items()
            }
        except Exception as exc:  # noqa: BLE001
            log(f"WARNING: could not extract {mod} properties: {exc}")

    # ---- plots ----
    make_fit_figure(output_dir / "s3fit_fit.png", ff, step, z, line_rows, mode, log)
    make_mc_figure(output_dir / "s3fit_mc.png", ff, line_rows, line_out, z, fit_cfg, log)

    # ---- NPZ ----
    scale = float(ff.spec_flux_scale)
    npz = {
        "z": z,
        "spec_flux_scale": scale,
        "spec_wave_obs": ff.spec["wave_w"],
        "spec_wave_rest": ff.spec["wave_w"] / (1.0 + z),
        "spec_flux": _flux_cgs(ff.spec["flux_w"], scale),
        "spec_ferr": _flux_cgs(ff.spec["ferr_w"], scale),
        "spec_model": _flux_cgs(ff.output_mc["tot"]["fmod"]["spec_lw"], scale),
        "spec_resid": _flux_cgs(ff.output_mc["tot"]["fres"]["spec_lw"], scale),
        "mc_chi2": chi_l,
        "mc_good": good_loops,
        "spec_calib_ratio": ratio,
        "line_names": np.array([str(x) for x in ff.model_dict["line"]["spec_mod"].linename_n]),
        "line_comp_names": np.array([str(x) for x in ff.model_dict["line"]["spec_mod"].cframe.comp_name_c]),
    }
    if getattr(ff, "have_phot", False):
        npz.update({
            "sed_wave_obs": ff.sed["wave_w"],
            "sed_wave_rest": ff.sed["wave_w"] / (1.0 + z),
            "sed_model": _flux_cgs(ff.output_mc["tot"]["fmod"]["sed_lw"], scale),
            "phot_wave_obs": ff.phot["wave_b"],
            "phot_flux": _flux_cgs(ff.phot["flux_b"], scale),
            "phot_ferr": _flux_cgs(ff.phot["ferr_b"], scale),
            "phot_model": _flux_cgs(ff.output_mc["tot"]["fmod"]["phot_lb"], scale),
            "phot_names": np.array(phot_names),
        })
    for mod in ff.output_mc:
        if "tot" in ff.output_mc[mod] and "spec_lw" in ff.output_mc[mod]["tot"]:
            npz[f"{safe_name(mod)}_spec"] = _flux_cgs(ff.output_mc[mod]["tot"]["spec_lw"], scale)
            if getattr(ff, "have_phot", False) and "sed_lw" in ff.output_mc[mod]["tot"]:
                npz[f"{safe_name(mod)}_sed"] = _flux_cgs(ff.output_mc[mod]["tot"]["sed_lw"], scale)
        for comp in ff.output_mc[mod]:
            if comp == "tot":
                continue
            if "spec_lw" in ff.output_mc[mod][comp]:
                npz[f"{safe_name(mod)}_{safe_name(comp)}_spec"] = _flux_cgs(
                    ff.output_mc[mod][comp]["spec_lw"], scale)
    # MC line arrays
    comps = [str(x) for x in ff.model_dict["line"]["spec_mod"].cframe.comp_name_c]
    lnames = [str(x) for x in ff.model_dict["line"]["spec_mod"].linename_n]
    mc_flux = np.full((ff.num_loops, len(comps), len(lnames)), np.nan)
    for i, comp in enumerate(comps):
        for j, line in enumerate(lnames):
            mc_flux[:, i, j] = np.asarray(line_out[comp]["value_Vl"][line], dtype=float) * scale
    npz["mc_line_flux"] = mc_flux
    np.savez_compressed(output_dir / "s3fit_output.npz", **npz)
    log(f"wrote {output_dir / 's3fit_output.npz'} ({os.path.getsize(output_dir / 's3fit_output.npz')/1e6:.2f} MB)")

    # ---- native pickle (optional) ----
    pickle_info = {"saved": False, "reason": "disabled by config"}
    if bool(fit_cfg.get("save_native_pickle", False)):
        pkl = output_dir / "s3fit_output.pkl.gz"
        try:
            ff.save_to_file(str(pkl))
            mb = pkl.stat().st_size / 1e6
            if mb <= float(fit_cfg.get("native_pickle_max_mb", 25)):
                pickle_info = {"saved": True, "file": pkl.name, "mb": mb}
                log(f"wrote native pickle {pkl.name} ({mb:.1f} MB)")
            else:
                pkl.unlink()
                pickle_info = {"saved": False, "reason": f"too large ({mb:.1f} MB > "
                               f"{fit_cfg.get('native_pickle_max_mb', 25)} MB); compact NPZ kept"}
                log(f"removed native pickle ({mb:.1f} MB > limit)")
        except Exception as exc:  # noqa: BLE001
            pickle_info = {"saved": False, "reason": f"{type(exc).__name__}: {exc}"}
            log(f"WARNING: native pickle failed: {pickle_info['reason']}")

    # ---- comparison ----
    pyq_dir = Path(args.pyqsofit_dir) if args.pyqsofit_dir else None
    if pyq_dir is None:
        default_ref = Path("/app/reference")
        pyq_dir = default_ref if default_ref.exists() else None
    comp_summary = compare_pyqsofit(pyq_dir, line_rows, ratio,
                                    source=source_key, out_csv=output_dir / "pyqsofit_comparison.csv")
    log(f"PyQSOFit comparison: {comp_summary.get('status')}")

    # ---- logs / configs / run.json ----
    s3fit_log = output_dir / "s3fit.log"
    with s3fit_log.open("w") as fh:
        fh.write("\n".join(str(x) for x in getattr(ff, "log_message", [])))
        fh.write("\n")
    log(f"wrote {s3fit_log} ({len(getattr(ff, 'log_message', []))} lines)")

    dump_json(output_dir / "model_config.json", model_config)
    dump_json(output_dir / "fit_config.effective.json", fit_cfg)

    times = loop_times(getattr(ff, "log_message", []))
    detections = [r for r in line_rows if r["component"] == "total" and r["detected"]]
    run = {
        "tool": "s3fit_line",
        "s3fit_version": getattr(s3fit, "__version__", "unknown"),
        "source": source_key,
        "source_name": source_meta.get("name"),
        "z": z,
        "mode_requested": str(fit_cfg.get("mode", "spec+sed")),
        "mode_used": mode,
        "have_photometry": bool(getattr(ff, "have_phot", False)),
        "input": {
            "source_dir": str(input_dir),
            "spectrum": str(spec_path),
            "photometry": str(phot_path) if phot_path else None,
            "photometry_bands": phot_names,
            "n_spec_pixels": int(len(wave)),
            "n_spec_masked": n_bad,
            "wave_min_obs_angstrom": float(np.nanmin(wave)),
            "wave_max_obs_angstrom": float(np.nanmax(wave)),
            "wave_min_rest_angstrom": float(np.nanmin(wave) / (1 + z)),
            "wave_max_rest_angstrom": float(np.nanmax(wave) / (1 + z)),
            "resolution_median": float(np.nanmedian(R)),
            "flux_unit_input": "erg s-1 cm-2 angstrom-1 (SDSS 1e-17 scaled)",
            "photometry_unit_input": "mJy",
        },
        "scope": {
            "pure_spectrum_only": bool(mode == "spec"),
            "joint_spectrum_sed": bool(mode == "spec+sed" and getattr(ff, "have_phot", False)),
            "torus_configured": bool(model_config.get("torus", {}).get("enable", False)),
            "torus_used": "torus" in str(getattr(ff, "rev_mod_type", "")).split("+"),
            "stellar_ssp_used": "stellar" in ff.model_dict,
            "dual_annealing": bool(fit_cfg.get("if_run_init_annealing", True)),
            "nlfit_ntry_max": int(fit_cfg.get("nlfit_ntry_max", 3)),
            "accept_chi_sq": float(fit_cfg.get("accept_chi_sq", 3.0)),
            "line_list_note": "H-alpha/[N II]/[S II] removed from the fast line list because they are outside the SDSS coverage of both validation targets",
        },
        "fit": {
            "n_mocks": int(fit_cfg["n_mocks"]),
            "n_loops": int(ff.num_loops),
            "seed": int(fit_cfg["seed"]),
            "threads": int(fit_cfg["threads"]),
            "fit_space": str(fit_cfg.get("fit_space", "log")),
            "examine_result": bool(fit_cfg.get("examine_result", True)),
            "accept_chi_sq": float(fit_cfg.get("accept_chi_sq", 3.0)),
            "if_run_init_annealing": bool(fit_cfg.get("if_run_init_annealing", True)),
            "use_pyneb": bool(fit_cfg.get("use_pyneb", False)),
            "spec_flux_scale": scale,
            "spec_calib_ratio": ratio,
            "spec_valid_range": fit_cfg.get("spec_valid_range"),
            "phot_calib_b": fit_cfg.get("phot_calib_b"),
        },
        "model": {
            "models": list(ff.model_dict),
            "models_used": str(getattr(ff, "rev_mod_type", "")).split("+"),
            "torus_enabled": bool(model_config.get("torus", {}).get("enable", False)),
            "stellar_ssp_used": "stellar" in ff.model_dict,
            "no_stellar_ssp_reason": "QSO mode: AGN powerlaw + Fe II + Balmer continuum + SKIRTOR torus + lines; no host/SSP term",
            "line_components": [str(x) for x in ff.model_dict["line"]["spec_mod"].cframe.comp_name_c],
            "line_names": [str(x) for x in ff.model_dict["line"]["spec_mod"].linename_n],
            "agn_components": [str(x) for x in ff.model_dict["agn"]["spec_mod"].cframe.comp_name_c] if "agn" in ff.model_dict else [],
            "torus_components": [str(x) for x in ff.model_dict["torus"]["spec_mod"].cframe.comp_name_c] if "torus" in ff.model_dict else [],
            "model_properties": model_props,
        },
        "chi2": chi2,
        "runtime": {
            "total_sec": runtime,
            "original_fit_sec": times["original_fit_seconds"],
            "mc_fit_sec": times["mc_fit_seconds"],
            "loop_times": times["loops"],
        },
        "line_detections": detections,
        "line_summary": {
            "n_rows": len(line_rows),
            "n_total_lines": len([r for r in line_rows if r["component"] == "total"]),
            "n_detected_total": len(detections),
        },
        "pyqsofit_comparison": comp_summary,
        "native_pickle": pickle_info,
        "files": {
            "lines_csv": "s3fit_lines.csv",
            "fit_png": "s3fit_fit.png",
            "mc_png": "s3fit_mc.png",
            "npz": "s3fit_output.npz",
            "model_config": "model_config.json",
            "fit_config": "fit_config.effective.json",
            "s3fit_log": "s3fit.log",
            "run_log": "run.log",
            "pyqsofit_comparison": "pyqsofit_comparison.csv" if comp_summary.get("status") == "ok" else None,
        },
        "command": [sys.executable] + sys.argv,
        "fit_error": fit_error,
    }
    dump_json(output_dir / "run.json", run)
    log("wrote run.json")
    log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
