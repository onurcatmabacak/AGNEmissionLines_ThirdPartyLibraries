#!/usr/bin/env python3
"""Native GANDALF v1.5 (GDL) emission-line fitting for optical QSO spectra.

This tool runs the public IDL GANDALF v1.5 source under GNU Data Language
(GDL), not under licensed IDL.  GANDALF performs a simultaneous fit of the
stellar continuum (BC03/Tremonti04 templates, convolved with a stellar LOSVD)
and Gaussian gas templates with tied multiplet kinematics.  The amplitudes are
solved linearly (BVLS) at each nonlinear step; MPFIT fits the Gaussian
velocities/dispersions and, with ``FOR_ERRORS=1``, returns formal covariance
errors.

Input
-----
Prepared ``spectrum.fits`` (HDU0 flux, HDU1 wavelength in A, HDU2 1-sigma
error, header ``z``) as written by ``pipeline/prepare_inputs.py``.  Raw SDSS
``spSpec`` files and SDSS COADD tables are also accepted.

Output
------
``gandalf_lines.csv``, ``gandalf_fit.png/pdf``, ``gandalf_uncertainty.png/pdf``,
``gandalf_fit.fits``, ``gandalf_input.fits``, ``gandalf_model.csv``,
``gandalf_lines_raw.csv``, ``gandalf_meta.txt``, ``gandalf_run.log``, and
``run.json``.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.io import fits

C_KMS = 299792.458
TOOL_ROOT = Path(__file__).resolve().parent
HA = 6562.80
HB = 4861.32
OIII = 5006.77
NII = 6583.34


# ---------------------------------------------------------------------------
# Input readers
# ---------------------------------------------------------------------------
def _header_z(hdr) -> float:
    for key in ("z", "Z", "REDSHIFT", "redshift"):
        if key in hdr:
            try:
                return float(hdr[key])
            except Exception:
                pass
    return float("nan")


def read_spectrum(path: Path) -> dict:
    """Read prepared spectrum.fits, raw SDSS spSpec, or SDSS COADD table."""
    with fits.open(path, memmap=False) as hdul:
        hdr0 = hdul[0].header
        z = _header_z(hdr0)
        meta = {"object": hdr0.get("OBJECT", hdr0.get("NAME", path.stem)),
                "z_header": z}

        # Preferred: prepared PyQSOFit-style file.
        if len(hdul) >= 3 and hdul[0].data is not None \
                and np.ndim(hdul[0].data) == 1 \
                and hdul[1].data is not None and np.ndim(hdul[1].data) == 1 \
                and hdul[2].data is not None and np.ndim(hdul[2].data) == 1 \
                and hdul[1].data.dtype.names is None \
                and hdul[2].data.dtype.names is None:
            d0 = np.asarray(hdul[0].data, float).ravel()
            d1 = np.asarray(hdul[1].data, float).ravel()
            d2 = np.asarray(hdul[2].data, float).ravel()
            if d0.size == d1.size == d2.size and d0.size > 10:
                return {"wave": d1, "flux": d0, "err": d2, "z": z, **meta}

        # Raw SDSS spSpec: primary is a (>=3, npix) array.
        d = hdul[0].data
        if d is not None and np.ndim(d) == 2 and np.shape(d)[0] >= 3:
            arr = np.asarray(d, float)
            crval = float(hdr0.get("CRVAL1", 3.5))
            cdelt = float(hdr0.get("CD1_1", hdr0.get("CDELT1", 1e-4)))
            wave = 10.0 ** (crval + cdelt * np.arange(arr.shape[1]))
            return {"wave": wave, "flux": arr[0], "err": np.abs(arr[2]),
                    "z": z, **meta}

        # SDSS COADD / generic table.
        for hdu in hdul:
            data = hdu.data
            if data is None or data.dtype.names is None:
                continue
            names = {n.lower(): n for n in data.dtype.names}
            if "flux" not in names:
                continue
            flux = np.asarray(data[names["flux"]], float)
            if "loglam" in names:
                wave = 10.0 ** np.asarray(data[names["loglam"]], float)
            elif "wl" in names:
                wave = np.asarray(data[names["wl"]], float)
            else:
                continue
            if "ivar" in names:
                ivar = np.asarray(data[names["ivar"]], float)
                err = 1.0 / np.sqrt(np.clip(ivar, 1e-30, None))
            elif "stdev" in names:
                err = np.abs(np.asarray(data[names["stdev"]], float))
            else:
                err = np.full_like(flux, np.nan)
            if not np.isfinite(z):
                z = _header_z(hdu.header)
            if not np.isfinite(z):
                for tname in ("SPALL", "ZALL"):
                    try:
                        t = hdul[tname].data
                        if t is not None and "Z" in t.dtype.names:
                            z = float(t["Z"][0])
                            break
                    except Exception:
                        pass
            return {"wave": wave, "flux": flux, "err": err, "z": z, **meta}

        # ZALL / SPALL table may hold the redshift for COADD files.
        for name in ("SPALL", "ZALL"):
            try:
                t = hdul[name].data
                if t is not None and "Z" in t.dtype.names:
                    z = float(t["Z"][0])
                    break
            except Exception:
                pass

    raise ValueError(f"{path}: could not find a spectrum (flux/wavelength/error)")


def _flux_scale(flux: np.ndarray, mode: str) -> float:
    if mode == "cgs":
        return 1e17
    if mode in ("1e-17", "1e17", "efeds"):
        return 1.0
    med = float(np.nanmedian(np.abs(flux))) if np.isfinite(flux).any() else 0.0
    return 1e17 if med < 1e-8 else 1.0


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
def load_template_rows(list_path: Path, template_dir: Path):
    rows = []
    if list_path.exists():
        for line in list_path.read_text().splitlines():
            s = line.strip()
            if not s or s.startswith("#") or s.upper().startswith("DIR"):
                continue
            parts = s.split()
            if len(parts) >= 2:
                rows.append((parts[0], parts[1]))
    if not rows and template_dir.exists():
        rows = [(p.stem, p.name) for p in sorted(template_dir.glob("*.fits"))]
    if not rows:
        raise FileNotFoundError(f"no templates in {list_path} / {template_dir}")
    return rows


# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------
def prepare_inputs(args, cfg, work: Path):
    spec = read_spectrum(Path(args.input))
    wave = np.asarray(spec["wave"], float).ravel()
    flux = np.asarray(spec["flux"], float).ravel()
    err = np.asarray(spec["err"], float).ravel()
    z = float(spec["z"])
    obj = os.environ.get("GANDALF_OBJECT") or spec.get("object")
    if not np.isfinite(z) or z < 0:
        raise ValueError(f"invalid redshift: {z}")

    good = np.isfinite(wave) & np.isfinite(flux) & np.isfinite(err) & (err > 0)
    if good.sum() < 100:
        raise ValueError(f"only {good.sum()} finite input pixels")
    order = np.argsort(wave[good])
    wave, flux, err = wave[good][order], flux[good][order], err[good][order]

    scale = _flux_scale(flux, str(cfg.get("input_flux_unit", "auto")))
    # Rest-frame flux density: F_lambda,rest = (1+z) F_lambda,obs.
    wave_r = wave / (1.0 + z)
    flux_r = flux * scale * (1.0 + z)
    err_r = err * scale * (1.0 + z)

    dlog = float(cfg["dlog"])
    lt0 = float(cfg["template_l0"])
    ltn = int(cfg["template_npix"])
    tmin = 10.0 ** lt0
    tmax = 10.0 ** (lt0 + (ltn - 1) * dlog)

    rest_min_obs = float(wave_r.min())
    rest_max_obs = float(wave_r.max())
    rest_min = max(tmin, rest_min_obs)
    rest_max = min(tmax, rest_max_obs)
    if cfg.get("rest_max_A") is not None:
        rest_max = min(rest_max, float(cfg["rest_max_A"]))

    # If H-alpha is at/just beyond the red edge, its blue wing can bias the
    # continuum and the [O I] region.  Truncate before H-alpha in that case.
    ha_cut = float(cfg.get("rest_max_when_ha_uncovered", 6200.0))
    if rest_max < HA + 50.0 and rest_max > ha_cut:
        rest_max = ha_cut

    if rest_max - rest_min < 200.0:
        raise ValueError(f"rest-frame coverage too small: {rest_min:.1f}-{rest_max:.1f} A")

    l0 = lt0 + math.ceil((math.log10(rest_min) - lt0) / dlog) * dlog
    l0 = max(l0, lt0)
    i0 = int(round((l0 - lt0) / dlog))
    n = int(math.floor((math.log10(rest_max) - l0) / dlog)) + 1
    n = max(n, 200)
    n = min(n, ltn - i0)
    n_temp = min(ltn - i0, n + int(cfg.get("template_pad", 200)))
    if n_temp < n:
        n_temp = n
    if n < 200:
        raise ValueError(f"grid too short: {n} pixels")

    wave_grid = 10.0 ** (l0 + np.arange(n) * dlog)
    fg = np.interp(wave_grid, wave_r, flux_r, left=np.nan, right=np.nan)
    var = np.interp(wave_grid, wave_r, err_r ** 2, left=np.nan, right=np.nan)
    eg = np.sqrt(np.clip(var, 0.0, None))
    good = np.isfinite(fg) & np.isfinite(eg) & (eg > 0)
    fg = np.where(good, fg, 0.0)
    eg = np.where(good, eg, 1e6)
    good_i = good.astype(np.int16)
    if good.sum() < 100:
        raise ValueError(f"only {good.sum()} good rest-frame pixels")

    tdir = Path(str(cfg["template_dir"]).format(tool_root=str(TOOL_ROOT)))
    tlist = Path(str(cfg["template_list"]).format(tool_root=str(TOOL_ROOT)))
    rows = load_template_rows(tlist, tdir)
    tmpl, names, used = [], [], []
    for name, fname in rows:
        path = tdir / fname
        if not path.exists():
            continue
        y = np.asarray(fits.getdata(path, ext=0), float).ravel()
        if y.size < i0 + n_temp:
            continue
        y = y[i0:i0 + n_temp]
        pos = y[y > 0]
        if pos.size == 0 or not np.isfinite(y).all():
            continue
        med = float(np.median(pos))
        if med <= 0:
            continue
        tmpl.append(y / med)
        names.append(name)
        used.append(fname)
    if len(tmpl) < 2:
        raise ValueError(f"only {len(tmpl)} usable templates")
    templates = np.array(tmpl, float).T
    if templates.shape[0] < n:
        raise ValueError("template grid shorter than galaxy grid")

    hdr = fits.Header()
    hdr["OBJECT"] = str(obj if obj else "target")[:60]
    hdr["Z"] = z
    hdr["L0GAL"] = l0
    hdr["DLGAL"] = dlog
    hdr["L0TEMPL"] = l0
    hdr["LOG10"] = 1
    hdr["INTDISP"] = float(cfg["int_disp_kms"])
    hdr["RESTMIN"] = 10.0 ** l0
    hdr["RESTMAX"] = 10.0 ** (l0 + (n - 1) * dlog)
    hdr["NPIXGAL"] = n
    hdr["NPIXTEMP"] = n_temp
    hdr["HISTORY"] = "gandalf_line: rest-frame log10 grid, flux in 1e-17 units"
    in_fits = work / "gandalf_input.fits"
    fits.HDUList([
        fits.PrimaryHDU(fg.astype(np.float64), header=hdr),
        fits.ImageHDU(eg.astype(np.float64), name="ERROR"),
        fits.ImageHDU(good_i, name="MASK"),
        fits.ImageHDU(templates.astype(np.float64), name="TEMPLATES"),
    ]).writeto(in_fits, overwrite=True)

    info = {
        "z": z, "wave_min": float(wave.min()), "wave_max": float(wave.max()),
        "wave_rest_min": rest_min_obs, "wave_rest_max": rest_max_obs,
        "rest_min": float(10.0 ** l0),
        "rest_max": float(10.0 ** (l0 + (n - 1) * dlog)),
        "l0": l0, "dlog": dlog, "n": n, "n_temp": n_temp,
        "i0": i0, "velscale_kms": C_KMS * dlog * math.log(10.0),
        "n_templates": len(names), "template_names": names,
        "template_files": used, "input_fits": str(in_fits),
        "n_good": int(good.sum()), "flux_scale": scale,
        "object": obj,
    }
    return in_fits, info, fg, eg, good_i, wave_grid


def write_run_setup(src: Path, dst: Path, z: float):
    """Copy the emission setup, converting observed sky wavelengths to rest."""
    out = []
    for line in src.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            out.append(line)
            continue
        parts = s.split()
        if len(parts) >= 9 and parts[0].lstrip("+-").isdigit():
            if parts[1] == "sky":
                parts[2] = f"{float(parts[2]) / (1.0 + z):.4f}"
            out.append("  ".join(parts))
        else:
            out.append(line)
    dst.write_text("\n".join(out) + "\n")


# ---------------------------------------------------------------------------
# GDL run
# ---------------------------------------------------------------------------
def write_gdl_batch(work: Path, in_fits: Path, setup: Path, cfg: dict):
    gdl_dir = TOOL_ROOT / "third_party" / "ppxf_idl_2018"
    gandalf_dir = TOOL_ROOT / "third_party" / "gandalf_v1.5"
    files = [
        gdl_dir / "cap_any.pro", gdl_dir / "cap_diff.pro",
        gdl_dir / "cap_range.pro", gdl_dir / "log_rebin.pro",
        gdl_dir / "ppxf_determine_goodpixels.pro",
        gdl_dir / "ppxf_emission_lines.pro", gdl_dir / "bvls.pro",
        gdl_dir / "ppxf.pro", gandalf_dir / "range.pro",
        gandalf_dir / "gandalf.pro", TOOL_ROOT / "gdl" / "mask_emission_lines.pro",
        TOOL_ROOT / "gdl" / "run_gandalf.pro",
    ]
    missing = [str(p) for p in files if not p.exists()]
    if missing:
        raise FileNotFoundError("missing GDL source: " + ", ".join(missing))
    lines = ["!PATH = '/usr/share/gnudatalanguage/astrolib:' + !PATH"]
    lines += [f".run {p}" for p in files]
    use_ppxf = 1 if cfg.get("use_ppxf", True) else 0
    call = (
        "gandalf_line_run, input='{}', output='{}', setup='{}', "
        "mdegree={}, degree={}, int_disp={}, "
        "ppxf_mask_sigma={}, gandalf_mask_sigma={}, use_ppxf={}, "
        "ppxf_degree={}, ppxf_mdegree={}, fixed_v={}, fixed_sigma={}, "
        "ppxf_sigma_min={}, ppxf_sigma_max={}, ppxf_v_max={}"
    ).format(
        in_fits, work, setup,
        int(cfg["mdegree"]), int(cfg["degree"]), float(cfg["int_disp_kms"]),
        float(cfg["ppxf_mask_sigma_kms"]), float(cfg["gandalf_mask_sigma_kms"]),
        use_ppxf, int(cfg["ppxf_degree"]), int(cfg["ppxf_mdegree"]),
        float(cfg["stellar_velocity_kms"]), float(cfg["stellar_sigma_kms"]),
        float(cfg["ppxf_sigma_min_kms"]), float(cfg["ppxf_sigma_max_kms"]),
        float(cfg["ppxf_v_max_kms"]),
    )
    lines += [call, "exit"]
    batch = work / "run_gandalf.gdl"
    batch.write_text("\n".join(lines) + "\n")
    return batch


def run_gdl(batch: Path, work: Path, timeout: int):
    exe = shutil.which("gdl")
    if not exe:
        raise RuntimeError("gdl executable not found in PATH")
    cmd = [exe, "-quiet", str(batch)]
    t0 = time.time()
    p = subprocess.run(cmd, cwd=str(work), capture_output=True, text=True,
                       timeout=timeout)
    runtime = time.time() - t0
    log = "$ " + " ".join(cmd) + "\n" + p.stdout + "\n" + p.stderr
    log = "\n".join(line.rstrip() for line in log.splitlines()) + "\n"
    (work / "gandalf_run.log").write_text(log)
    for marker in ("Execution halted", "Procedure not found", "Parser syntax error"):
        if marker in log:
            tail = "\n".join(log.splitlines()[-40:])
            raise RuntimeError(f"GDL failed ({marker}):\n{tail}")
    if p.returncode != 0:
        tail = "\n".join(log.splitlines()[-40:])
        raise RuntimeError(f"GDL exited {p.returncode}:\n{tail}")
    for f in ("gandalf_fit.fits", "gandalf_lines_raw.csv", "gandalf_meta.txt"):
        if not (work / f).exists():
            tail = "\n".join(log.splitlines()[-40:])
            raise RuntimeError(f"GDL did not produce {f}:\n{tail}")
    return runtime, log


def parse_meta(path: Path) -> dict:
    meta = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            meta[k.strip()] = v.strip()
    for k in ("ppxf_attempted", "ppxf_ok", "ppxf_npix", "ppxf_nz",
              "npix", "ntemp", "nlines", "ngood"):
        if k in meta:
            try:
                meta[k] = int(float(meta[k]))
            except Exception:
                pass
    for k in ("ppxf_v", "ppxf_sigma", "ppxf_chi2", "stellar_v",
              "stellar_sigma", "l0_gal", "lstep_gal", "velscale"):
        if k in meta:
            try:
                meta[k] = float(meta[k])
            except Exception:
                pass
    return meta


def parse_raw(path: Path) -> list[dict]:
    with path.open() as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# Line table
# ---------------------------------------------------------------------------
DISPLAY = {
    "OII3729": ("[OII]3729", "narrow"),
    "NeIII3869": ("[NeIII]3869", "narrow"),
    "NeIII3967": ("[NeIII]3967", "narrow"),
    "Hb": ("Hbeta", "narrow"),
    "Hb_br": ("Hbeta", "broad"),
    "OIII5007": ("[OIII]5007", "narrow"),
    "OI6300": ("[OI]6300", "narrow"),
    "Ha": ("Halpha", "narrow"),
    "Ha_br": ("Halpha", "broad"),
    "NII6584": ("[NII]6584", "narrow"),
    "SII6716": ("[SII]6716", "narrow"),
}


def _f(row, key, default=float("nan")):
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def build_line_rows(raw_rows, rest_min, rest_max, int_disp, snr_min):
    rows = []
    by_key = {}
    for r in raw_rows:
        name = r.get("name", "").strip()
        line, comp = DISPLAY.get(name, (name, "narrow"))
        flux = _f(r, "flux")
        eflux = _f(r, "eflux")
        ampl = _f(r, "ampl")
        eampl = _f(r, "eampl")
        method = "mpfit_covariance"
        if (not np.isfinite(eflux) or eflux <= 0) and np.isfinite(eampl) \
                and eampl > 0 and np.isfinite(ampl) and ampl != 0 \
                and np.isfinite(flux):
            eflux = eampl * abs(flux / ampl)
            method = "amplitude_error_scaled"
        snr = flux / eflux if (np.isfinite(eflux) and eflux > 0 and np.isfinite(flux)) else 0.0
        if not np.isfinite(flux) or flux <= 0:
            status = "not_detected"
        elif snr >= snr_min:
            status = "ok"
        else:
            status = "weak"
        sigma = _f(r, "sigma")
        esigma = _f(r, "esigma")
        fit_kind = r.get("fit_kind", "f").strip()
        kind = r.get("kind", "l").strip()
        notes = []
        if fit_kind[:1] in ("t", "v", "s"):
            notes.append(f"kinematics tied to line index {fit_kind[1:]}")
        if kind[:1] == "d":
            notes.append("multiplet satellite")
        if comp == "broad":
            notes.append("broad Gaussian component; empirical BLR proxy")
        if method == "amplitude_error_scaled":
            notes.append("flux error scaled from MPFIT amplitude error (tied kinematics)")
        row = {
            "line": line, "component": comp,
            "lambda_rest": _f(r, "lambda_rest"),
            "flux_1e17": flux, "flux_err_1e17": eflux,
            "flux_erg_s_cm2": flux * 1e-17, "flux_err_erg_s_cm2": eflux * 1e-17,
            "amplitude": ampl, "amplitude_err": eampl,
            "velocity_kms": _f(r, "vel"), "velocity_err_kms": _f(r, "evel"),
            "sigma_kms": sigma, "sigma_err_kms": esigma,
            "sigma_obs_kms": math.sqrt(sigma ** 2 + int_disp ** 2)
                             if np.isfinite(sigma) else float("nan"),
            "snr": snr,
            "detected": bool(status == "ok"),
            "status": status,
            "method": "gandalf_gdl",
            "notes": "; ".join(notes),
            "_fit_kind": fit_kind, "_kind": kind,
        }
        rows.append(row)
        by_key.setdefault((line, comp), row)

    required = [
        ("Hbeta", "narrow"), ("Hbeta", "broad"), ("Hbeta", "total"),
        ("[OIII]5007", "narrow"), ("Halpha", "narrow"), ("[NII]6584", "narrow"),
    ]
    out = []
    for line, comp in required:
        if (line, comp) in by_key:
            out.append(by_key[(line, comp)])
            continue
        if line == "Hbeta" and comp == "total":
            narrow = by_key.get(("Hbeta", "narrow"))
            broad = by_key.get(("Hbeta", "broad"))
            if narrow and broad and narrow["status"] != "not_covered" \
                    and broad["status"] != "not_covered":
                f = narrow["flux_1e17"] + broad["flux_1e17"]
                ef = math.sqrt(narrow["flux_err_1e17"] ** 2 + broad["flux_err_1e17"] ** 2)
                out.append({
                    "line": "Hbeta", "component": "total", "lambda_rest": HB,
                    "flux_1e17": f, "flux_err_1e17": ef,
                    "flux_erg_s_cm2": f * 1e-17, "flux_err_erg_s_cm2": ef * 1e-17,
                    "amplitude": float("nan"), "amplitude_err": float("nan"),
                    "velocity_kms": narrow["velocity_kms"],
                    "velocity_err_kms": float("nan"),
                    "sigma_kms": float("nan"), "sigma_err_kms": float("nan"),
                    "sigma_obs_kms": float("nan"), "snr": f / ef if ef > 0 else 0.0,
                    "detected": bool(f / ef >= snr_min) if ef > 0 else False,
                    "status": "ok" if ef > 0 and f / ef >= snr_min else "weak",
                    "method": "gandalf_gdl",
                    "notes": "narrow + broad; errors added in quadrature",
                    "_fit_kind": "", "_kind": "",
                })
                continue
        lam = {"Hbeta": HB, "[OIII]5007": OIII, "Halpha": HA,
               "[NII]6584": NII}.get(line, float("nan"))
        reason = f"outside rest-frame coverage ({rest_min:.0f}-{rest_max:.0f} A)"
        if line == "Hbeta" and comp == "broad":
            reason = "no independent broad H-beta component in the fit"
        out.append({
            "line": line, "component": comp, "lambda_rest": lam,
            "flux_1e17": float("nan"), "flux_err_1e17": float("nan"),
            "flux_erg_s_cm2": float("nan"), "flux_err_erg_s_cm2": float("nan"),
            "amplitude": float("nan"), "amplitude_err": float("nan"),
            "velocity_kms": float("nan"), "velocity_err_kms": float("nan"),
            "sigma_kms": float("nan"), "sigma_err_kms": float("nan"),
            "sigma_obs_kms": float("nan"), "snr": 0.0, "detected": False,
            "status": "not_covered", "method": "gandalf_gdl", "notes": reason,
            "_fit_kind": "", "_kind": "",
        })

    # Append remaining measured lines, and any broad H-alpha, in wavelength order.
    seen = {(r["line"], r["component"]) for r in out}
    extra = [r for r in rows if (r["line"], r["component"]) not in seen]
    extra.sort(key=lambda r: (r["lambda_rest"] if np.isfinite(r["lambda_rest"]) else 0.0,
                              r["component"]))
    out.extend(extra)
    for r in out:
        r.pop("_fit_kind", None)
        r.pop("_kind", None)
    return out


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def _finite(a):
    return np.asarray(a, float) if np.isfinite(a).any() else np.zeros_like(a, float)


def make_figures(out: Path, wave, galaxy, bestfit, emission, residual, err,
                 goodpix, rows, info, meta):
    stellar = bestfit - emission
    wave = np.asarray(wave, float)
    good = np.asarray(goodpix, int)
    resid_chi2 = float("nan")
    if good.size > 10:
        dof = max(1, good.size - (3 * max(1, len(rows)) + 4))
        resid_chi2 = float(np.nansum((residual[good] / err[good]) ** 2) / dof)
    has_ha = any(r["line"] == "Halpha" and r["status"] != "not_covered" for r in rows)

    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=False,
                             gridspec_kw={"height_ratios": [2.6, 2.6, 1.0]})
    ax, axz, axr = axes

    def draw(a, lo, hi):
        q = (wave >= lo) & (wave <= hi)
        a.plot(wave[q], galaxy[q], color="0.20", lw=0.8, label="observed")
        a.plot(wave[q], bestfit[q], color="C3", lw=1.1, label="GANDALF total")
        a.plot(wave[q], stellar[q], color="C0", lw=1.0, label="stellar continuum")
        a.plot(wave[q], emission[q], color="C1", lw=1.0, label="gas emission")
        for lam, lab in [(HB, r"H$\beta$"), (4958.83, "[O III] 4959"),
                         (OIII, "[O III] 5007"), (HA, r"H$\alpha$"),
                         (NII, "[N II] 6584")]:
            if lo <= lam <= hi:
                a.axvline(lam, color="0.55", lw=0.6, ls=":")
        a.set_ylabel(r"flux (10$^{-17}$ erg s$^{-1}$ cm$^{-2}$ A$^{-1}$)")

    draw(ax, float(info["rest_min"]), float(info["rest_max"]))
    ax.legend(fontsize=8, frameon=False, loc="upper right")
    title = (f"GANDALF v1.5 native (GDL)  z={info['z']:.4f}  "
             f"rest {info['rest_min']:.0f}-{info['rest_max']:.0f} A  "
             f"residual $\\chi^2_\\nu$={resid_chi2:.2f}")
    if not has_ha:
        title += "  |  Halpha/[N II] outside coverage"
    ax.set_title(title, fontsize=10)

    if has_ha:
        zlo, zhi = 6400.0, 6800.0
    else:
        zlo, zhi = 4750.0, 5150.0
    zlo = max(zlo, float(info["rest_min"]))
    zhi = min(zhi, float(info["rest_max"]))
    if zhi - zlo < 50:
        zlo, zhi = float(info["rest_min"]), float(info["rest_max"])
    draw(axz, zlo, zhi)
    axz.set_title(f"zoom: {zlo:.0f}-{zhi:.0f} A", fontsize=9)

    q = (wave >= float(info["rest_min"])) & (wave <= float(info["rest_max"]))
    axr.plot(wave[q], residual[q], color="0.25", lw=0.7)
    axr.axhline(0.0, color="k", lw=0.5)
    axr.set_xlabel("rest-frame wavelength (A)")
    axr.set_ylabel("residual")

    lines_txt = []
    for key in [("Hbeta", "narrow"), ("Hbeta", "broad"), ("Hbeta", "total"),
                ("[OIII]5007", "narrow"), ("Halpha", "narrow"), ("[NII]6584", "narrow")]:
        r = next((x for x in rows if x["line"] == key[0] and x["component"] == key[1]), None)
        if r is None:
            continue
        if r["status"] == "not_covered":
            lines_txt.append(f"{r['line']:<12s} {r['component']:<6s}  not covered")
        else:
            lines_txt.append(f"{r['line']:<12s} {r['component']:<6s}  "
                             f"{r['flux_1e17']:7.1f} +/- {r['flux_err_1e17']:5.1f}")
    ax.text(0.015, 0.97, "\n".join(lines_txt), transform=ax.transAxes,
            va="top", ha="left", fontsize=7.5, family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", alpha=0.9))
    fig.tight_layout()
    fig.savefig(out / "gandalf_fit.png", dpi=160, bbox_inches="tight")
    fig.savefig(out / "gandalf_fit.pdf", bbox_inches="tight")
    plt.close(fig)
    return resid_chi2

def make_uncertainty(out: Path, rows, info):
    sel = [r for r in rows if r["status"] in ("ok", "weak")
           and np.isfinite(r["flux_1e17"]) and np.isfinite(r["flux_err_1e17"])
           and r["flux_err_1e17"] > 0]
    if not sel:
        return
    labels = [f"{r['line']}\n{r['component']}" for r in sel]
    x = np.arange(len(sel))
    flux = np.array([r["flux_1e17"] for r in sel])
    eflux = np.array([r["flux_err_1e17"] for r in sel])
    sig = np.array([r["sigma_kms"] for r in sel])
    esig = np.array([r["sigma_err_kms"] for r in sel])
    snr = np.array([r["snr"] for r in sel])

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True,
                             gridspec_kw={"height_ratios": [2.0, 2.0, 1.3]})
    ax = axes[0]
    ax.errorbar(x, flux, yerr=eflux, fmt="o", color="C3", capsize=3, lw=1.0)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_ylabel(r"flux (10$^{-17}$ erg s$^{-1}$ cm$^{-2}$)")
    ax.set_title("GANDALF v1.5 FOR_ERRORS=1: MPFIT formal 1-sigma errors "
                 "(diagonal covariance; no MCMC)", fontsize=10)

    ax = axes[1]
    m = np.isfinite(sig) & np.isfinite(esig) & (esig > 0)
    if m.any():
        ax.errorbar(x[m], sig[m], yerr=esig[m], fmt="s", color="C0", capsize=3, lw=1.0)
    ax.set_ylabel(r"Gaussian $\sigma$ (km s$^{-1}$)")

    ax = axes[2]
    ax.bar(x, snr, color="C1", alpha=0.8)
    ax.axhline(float(info.get("detection_snr", 3.0)), color="C3", lw=0.8, ls="--")
    ax.set_ylabel("S/N")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7.5)
    fig.tight_layout()
    fig.savefig(out / "gandalf_uncertainty.png", dpi=160, bbox_inches="tight")
    fig.savefig(out / "gandalf_uncertainty.pdf", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def _limitations(rows, meta, cfg, info):
    lims = [
        "GANDALF v1.5 is an IDL code; this run uses GNU Data Language 1.0.4. "
        "GDL is IDL-compatible but not identical to licensed IDL.",
        "GANDALF uses MPFIT covariance (FOR_ERRORS=1), not MCMC.  Errors are "
        "formal 1-sigma and assume the model and noise are correct.",
        "Narrow H-beta is tied to [O III] 5007 kinematics; the broad H-beta "
        "component is an independent Gaussian and an empirical BLR proxy, not "
        "a physical broad-line profile.",
        "Line fluxes are integrated Gaussian fluxes.  No aperture correction "
        "or reddening correction is applied; GANDALF v1.5 forbids REDDENING "
        "together with MDEGREE>0.",
        "Stellar templates are BC03/Tremonti04 at SDSS resolution "
        "(int_disp=61.5 km/s); higher-resolution data must be degraded first.",
    ]
    ha = next((r for r in rows if r["line"] == "Halpha"), None)
    if ha is None or ha["status"] == "not_covered":
        lims.insert(2, "H-alpha and [N II] 6584 are outside the observed/rest-frame "
                       "coverage of this spectrum; they are reported as not_covered, "
                       "not as non-detections.")
    else:
        lims.insert(2, "H-alpha and [N II] 6584 are covered; the broad H-alpha "
                       "component is included only when GANDALF detects it.")
    if int(meta.get("ppxf_ok", 0)):
        lims.insert(3, "PPXF supplied the stellar kinematics used to convolve the "
                       "templates.")
    else:
        lims.insert(3, "PPXF could not constrain the stellar kinematics of this "
                       "AGN-dominated continuum; a fixed %.0f km/s stellar LOSVD was "
                       "used.  The gas fit is still native GANDALF." %
                       float(cfg["stellar_sigma_kms"]))
    return lims


def json_safe(obj):
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(float(obj)) else float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return json_safe(obj.tolist())
    return obj


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path,
                   help="prepared spectrum.fits (or raw SDSS spSpec/COADD)")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--config", type=Path,
                   default=Path("/app/config/config.json"))
    p.add_argument("--emission-setup", type=Path, default=None)
    p.add_argument("--keep-work", action="store_true")
    args = p.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)

    cfg = json.loads(args.config.read_text())
    cfg_dir = args.config.parent
    setup_src = args.emission_setup or (cfg_dir / cfg.get("emission_setup", "emission_lines_setup"))
    if not setup_src.exists():
        raise FileNotFoundError(f"emission setup not found: {setup_src}")

    total_t0 = time.time()
    work = Path(tempfile.mkdtemp(prefix="gandalf_line_"))
    try:
        in_fits, info, fg, eg, good_i, wave_grid = prepare_inputs(args, cfg, work)
        setup_run = work / "emission_lines_setup"
        write_run_setup(setup_src, setup_run, info["z"])
        batch = write_gdl_batch(work, in_fits, setup_run, cfg)
        runtime, log = run_gdl(batch, work, int(cfg.get("timeout_seconds", 1800)))

        meta = parse_meta(work / "gandalf_meta.txt")
        raw_rows = parse_raw(work / "gandalf_lines_raw.csv")
        rows = build_line_rows(raw_rows, info["rest_min"], info["rest_max"],
                               float(cfg["int_disp_kms"]),
                               float(cfg.get("detection_snr", 3.0)))

        with fits.open(work / "gandalf_fit.fits", memmap=False) as h:
            galaxy = np.asarray(h[0].data, float).ravel()
            bestfit = np.asarray(h[1].data, float).ravel()
            emission = np.asarray(h[2].data, float).ravel()
            residual = np.asarray(h[3].data, float).ravel()
            goodpix = np.asarray(h[4].data, int).ravel()
            weights = np.asarray(h[5].data, float).ravel()
            sol_star = np.asarray(h[6].data, float).ravel()
            sol = np.asarray(h[7].data, float).ravel()
            esol = np.asarray(h[8].data, float).ravel()
            em_templates = np.asarray(h[9].data, float)
            hdr = h[0].header
            l0 = float(hdr["L0GAL"])
            dlog = float(hdr["DLGAL"])
        wave = 10.0 ** (l0 + np.arange(galaxy.size) * dlog)
        nlines = len(raw_rows)
        if em_templates.ndim == 2 and em_templates.shape[0] == nlines \
                and em_templates.shape[1] == galaxy.size:
            em_templates = em_templates.T

        # Final CSV
        fields = ["line", "component", "lambda_rest", "flux_1e17",
                  "flux_err_1e17", "flux_erg_s_cm2", "flux_err_erg_s_cm2",
                  "amplitude", "amplitude_err", "velocity_kms",
                  "velocity_err_kms", "sigma_kms", "sigma_err_kms",
                  "sigma_obs_kms", "snr", "detected", "status", "method", "notes"]
        with (args.output / "gandalf_lines.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in fields})

        # Model table and FITS products
        np.savetxt(args.output / "gandalf_model.csv",
                   np.column_stack([wave, galaxy, bestfit, bestfit - emission,
                                    emission, residual, eg]),
                   delimiter=",", comments="",
                   header="wave_rest_A,flux,model,stellar,emission,residual,error")
        for name in ("gandalf_input.fits", "gandalf_fit.fits",
                     "gandalf_lines_raw.csv", "gandalf_meta.txt",
                     "gandalf_run.log"):
            shutil.copy2(work / name, args.output / name)
        shutil.copy2(batch, args.output / "gandalf_batch.gdl")

        resid_chi2 = make_figures(args.output, wave, galaxy, bestfit, emission,
                                  residual, eg, goodpix, rows, info, meta)
        make_uncertainty(args.output, rows, {**info, **cfg})

        # Run summary
        line_yield = {}
        for key in ("Hbeta", "OIII5007", "Halpha", "NII6584"):
            line = {"OIII5007": "[OIII]5007", "NII6584": "[NII]6584"}.get(key, key)
            prefer = "total" if key == "Hbeta" else "narrow"
            cand = [r for r in rows if r["line"] == line and r["component"] == prefer]
            if not cand:
                cand = [r for r in rows if r["line"] == line
                        and r["component"] in ("total", "narrow")]
            if cand:
                r = cand[0]
                line_yield[key] = {
                    "line": r["line"], "component": r["component"],
                    "status": r["status"], "flux_1e17": r["flux_1e17"],
                    "flux_err_1e17": r["flux_err_1e17"],
                    "sigma_kms": r["sigma_kms"],
                    "sigma_err_kms": r["sigma_err_kms"],
                }
            else:
                line_yield[key] = {"status": "not_covered"}

        try:
            _v = subprocess.run(["gdl", "--version"], capture_output=True,
                                text=True, timeout=20)
            gdl_version = (_v.stdout + " " + _v.stderr).strip()
        except Exception:
            gdl_version = "unknown"

        summary = {
            "tool": "gandalf_line",
            "method": "gandalf_gdl",
            "native_gandalf": True,
            "engine": {
                "gandalf": "v1.5 (Sarzi et al. 2006)",
                "interpreter": "GNU Data Language (GDL)",
                "gdl_version": gdl_version or "unknown",
                "libraries": ["gdl-astrolib", "gdl-mpfit", "IDL pPXF 2018-03-02", "BVLS"],
                "idl_license_required": False,
            },
            "input": str(args.input),
            "object": info.get("object"),
            "z": info["z"],
            "rest_frame": True,
            "rest_range_A": [info["rest_min"], info["rest_max"]],
            "input_coverage_A": [info["wave_min"], info["wave_max"]],
            "grid": {
                "l0": info["l0"], "dlog": info["dlog"], "npix": info["n"],
                "velscale_kms": info["velscale_kms"], "n_good": info["n_good"],
            },
            "templates": {
                "library": "BC03/Tremonti04 (GANDALF v1.5 SDSS example)",
                "n": info["n_templates"], "names": info["template_names"],
            },
            "fit_controls": {
                "int_disp_kms": cfg["int_disp_kms"],
                "mdegree": cfg["mdegree"], "degree": cfg["degree"],
                "ppxf_mask_sigma_kms": cfg["ppxf_mask_sigma_kms"],
                "gandalf_mask_sigma_kms": cfg["gandalf_mask_sigma_kms"],
                "use_ppxf": cfg["use_ppxf"], "reddening": None,
                "for_errors": True,
            },
            "ppxf": {
                "attempted": bool(meta.get("ppxf_attempted", 0)),
                "accepted": bool(meta.get("ppxf_ok", 0)),
                "message": meta.get("ppxf_message", ""),
                "n_good_pixels": meta.get("ppxf_npix"),
                "v_kms": meta.get("ppxf_v"),
                "sigma_kms": meta.get("ppxf_sigma"),
                "chi2": meta.get("ppxf_chi2"),
                "n_nonzero_templates": meta.get("ppxf_nz"),
            },
            "stellar_kinematics": {
                "source": "ppxf" if int(meta.get("ppxf_ok", 0)) else "fixed_fallback",
                "v_kms": meta.get("stellar_v"),
                "sigma_kms": meta.get("stellar_sigma"),
                "fixed_sigma_kms": float(cfg["stellar_sigma_kms"]),
                "note": ("PPXF constrained the stellar kinematics."
                         if int(meta.get("ppxf_ok", 0)) else
                         "PPXF did not pass the acceptance cuts for this AGN-dominated "
                         "continuum; a fixed %.0f km/s stellar LOSVD was used.  The gas "
                         "fit is still native GANDALF." % float(cfg["stellar_sigma_kms"])),
            },
            "line_measurements": [
                {k: v for k, v in r.items() if k in fields} for r in rows
            ],
            "line_yield": line_yield,
            "residual_chi2_nu": resid_chi2,
            "runtime_seconds": runtime,
            "total_runtime_seconds": time.time() - total_t0,
            "gdl_command": f"gdl -quiet {batch}",
            "outputs": sorted(p.name for p in args.output.iterdir()),
            "limitations": _limitations(rows, meta, cfg, info),
        }
        (args.output / "run.json").write_text(
            json.dumps(json_safe(summary), indent=2) + "\n")

        print(f"[gandalf_line] {info['object']} z={info['z']:.4f} "
              f"rest={info['rest_min']:.0f}-{info['rest_max']:.0f} A "
              f"runtime={runtime:.1f}s")
        for key in ("Hbeta", "OIII5007", "Halpha", "NII6584"):
            r = line_yield[key]
            if r.get("status") == "not_covered":
                print(f"  {key:<10s} not covered")
            else:
                sig = r.get("sigma_kms")
                sig_txt = (f"  sigma={sig:.1f} km/s"
                           if sig is not None and np.isfinite(float(sig)) else "")
                print(f"  {key:<10s} flux={r['flux_1e17']:.2f} +/- "
                      f"{r['flux_err_1e17']:.2f} (1e-17){sig_txt}  "
                      f"status={r['status']}")
        return 0
    finally:
        if args.keep_work:
            print(f"[gandalf_line] work kept at {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
