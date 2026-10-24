#!/usr/bin/env python3
"""Run the official SDSS MaNGA Data Analysis Pipeline on a real LOGCUBE.

Production entry point for ``Tools/manga_dap``.  It does four things:

1. Builds the official DAP datacube object from the DRP LOGCUBE and passes the
   NSA metadata (z, effective radius, ellipticity, position angle) exactly as
   the survey DAP does.
2. Runs the complete ``mangadap.survey.manga_dap.manga_dap`` workflow:
   reduction assessments, HYB10 binning, pPXF stellar kinematics, emission-line
   moments, SASUKE Gaussian emission-line fits, and spectral indices.
3. Extracts compact, documented science tables and pedagogical figures from
   the resulting MAPS and model LOGCUBE.
4. Writes ``run.json``, ``effective_config.json`` and ``provenance.md`` with
   input hashes, exact package/template versions and every limitation.

The published DAP MAPS is **not** used as an input to the DAP.  It is copied to
the output only by the separate comparison step (``compare_maps.py``).

The code deliberately does not call ``EmissionLineFit`` on a single row-stacked
spectrum and call that "the DAP".  The DAP is run through its public survey
workflow on the datacube, with all stages enabled.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import gzip
import importlib.metadata as md
import io
import json
import math
import os
import platform
import resource
import shutil
import sys
import time
import traceback
import warnings
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# The DAP reads these at import time.  Set them before importing mangadap.
os.environ.setdefault("MANGADRP_VER", "v3_1_1")
os.environ.setdefault("MANGADAP_VER", "4.5.0")
os.environ.setdefault("MANGA_SPECTRO_REDUX", "/app/redux")
os.environ.setdefault("MANGA_SPECTRO_ANALYSIS", "/app/output/dap")
os.environ.setdefault("MANGACORE_VER", "v1_9_1")
os.environ.setdefault("MANGACORE_DIR", "/app/manga/core/v1_9_1")

import numpy as np
import matplotlib

matplotlib.use("Agg")
from astropy.io import fits
from astropy.wcs import WCS

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from manga_maps import (  # noqa: E402
    KEY_LINES, LINE_KEYS, CLASS_NAMES, bpt_fractions, classify_bpt, get_line_names,
    jsonable, key_fluxes, line_arrays, line_ew, line_kinematics, load_maps,
    md5_file, plot_bpt, plot_maps, plot_spectrum_fit, sha256_file, summary_stats,
    stellar_arrays, write_csv, write_json,
)

C_KMS = 299792.458
DAPTYPE_DEFAULT = "HYB10-MILESHC-MASTARHC2"
PLATE_DEFAULT = 9193
IFU_DEFAULT = 12701


# ---------------------------------------------------------------------------
# generic helpers
# ---------------------------------------------------------------------------
def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def package_version(name: str) -> str:
    try:
        return md.version(name)
    except Exception:
        return "unknown"


def collect_versions() -> dict:
    names = ["sdss-mangadap", "numpy", "scipy", "astropy", "matplotlib", "ppxf",
             "cvxopt", "vorbin", "pydl", "shapely", "configobj", "requests"]
    out = {name: package_version(name) for name in names}
    out["python"] = platform.python_version()
    out["platform"] = platform.platform()
    out["machine"] = platform.machine()
    try:
        import mangadap
        out["mangadap_module_version"] = getattr(mangadap, "__version__", "unknown")
    except Exception:
        out["mangadap_module_version"] = "unknown"
    # The wheel ships its exact SCM commit in scm_version.json.
    try:
        scm = Path(md.distribution("sdss-mangadap")._path) / "scm_version.json"
        if scm.exists():
            out["upstream_scm"] = json.loads(scm.read_text())
    except Exception:
        pass
    return out


def file_record(path: Path, include_hash: bool = True) -> dict:
    path = Path(path)
    rec = {"path": path.name, "size_bytes": path.stat().st_size if path.exists() else None}
    if path.exists() and include_hash:
        rec["sha256"] = sha256_file(path)
    return rec


def parse_plan(plan_path: Path) -> dict:
    import tomllib
    with plan_path.open("rb") as fh:
        return tomllib.load(fh)


def find_input_cube(input_dir: Path, explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"cube not found: {path}")
        return path
    candidates = sorted(input_dir.glob("manga-*-LOGCUBE.fits.gz"))
    if not candidates:
        candidates = sorted((input_dir / "raw").glob("manga-*-LOGCUBE.fits.gz"))
    if not candidates:
        candidates = sorted(input_dir.glob("**/*LOGCUBE*.fits*"))
    if not candidates:
        raise FileNotFoundError(f"no LOGCUBE FITS file in {input_dir} or {input_dir / 'raw'}")
    if len(candidates) > 1:
        raise ValueError(f"multiple LOGCUBE files in {input_dir}: {[p.name for p in candidates]}")
    return candidates[0]


def find_model_cube(dap_method_dir: Path, plate: int, ifu: int, daptype: str) -> Path | None:
    expected = dap_method_dir / f"manga-{plate}-{ifu}-LOGCUBE-{daptype}.fits.gz"
    if expected.exists():
        return expected
    hits = sorted(dap_method_dir.glob(f"*LOGCUBE*{daptype}*.fits*"))
    return hits[0] if hits else None


def find_maps(dap_method_dir: Path, plate: int, ifu: int, daptype: str) -> Path | None:
    expected = dap_method_dir / f"manga-{plate}-{ifu}-MAPS-{daptype}.fits.gz"
    if expected.exists():
        return expected
    hits = sorted(dap_method_dir.glob(f"*MAPS*{daptype}*.fits*"))
    return hits[0] if hits else None


def dap_data_manifest() -> dict:
    """Record every DAP template/DB file actually used, with hashes."""
    from mangadap.config.defaults import dap_data_root
    root = Path(dap_data_root())
    groups = {
        "MILESHC_templates": root / "spectral_templates" / "miles_cluster",
        "MASTARHC2_templates": root / "spectral_templates" / "mastarhc_v2",
        "line_database": root / "emission_lines",
        "artifact_masks": root / "artifacts",
        "maskbits": root / "sdss",
    }
    manifest = {"dap_data_root": str(root), "groups": {}}
    for label, directory in groups.items():
        files = []
        if directory.exists():
            for path in sorted(directory.glob("*")):
                if not path.is_file():
                    continue
                if label == "line_database" and path.name not in ("elpmpl11.par", "elpscmsk.par"):
                    continue
                if label == "artifact_masks" and path.name != "badsky.par":
                    continue
                if label == "maskbits" and path.name != "sdssMaskbits.par":
                    continue
                files.append({
                    "name": path.name,
                    "size_bytes": path.stat().st_size,
                    "md5": md5_file(path),
                    "sha256": sha256_file(path),
                })
        manifest["groups"][label] = {
            "directory": str(directory.relative_to(root.parent)) if directory.exists() else str(directory),
            "n_files": len(files),
            "files": files,
        }
    return manifest


# ---------------------------------------------------------------------------
# DAP run
# ---------------------------------------------------------------------------
def run_official_dap(cube_path: Path, out: Path, config: dict, plan_path: Path,
                     verbose: int = 1, disable_eline_fits: bool = False) -> dict:
    from mangadap.datacube.manga import MaNGADataCube
    from mangadap.config.manga import MaNGAAnalysisPlan
    from mangadap.survey.manga_dap import manga_dap
    from mangadap import __version__ as mangadap_version

    meta = config["metadata"]
    cube = MaNGADataCube(
        str(cube_path),
        z=float(meta["z"]),
        vdisp=float(meta.get("vdisp_kms_initial", 100.0)),
        ell=float(meta["ell"]),
        pa=float(meta["pa_deg"]),
        reff=float(meta["reff_arcsec"]),
    )
    # The official DAP uses the row-stacked spectra to compute the spatial
    # covariance matrix used by the Voronoi binning.  The LOGRSS is in the same
    # input directory; load it explicitly so the full covariance path is
    # exercised instead of silently falling back to covar_mode='none'.
    rss_loaded = False
    rss_note = ""
    try:
        cube.load_rss()
        rss_loaded = cube.rss is not None
        print(f"  LOGRSS loaded  : {rss_loaded} (covariance input)")
    except Exception as exc:  # noqa: BLE001
        rss_note = f"LOGRSS not loaded: {exc}"
        warnings.warn(rss_note)

    dap_root = out / "dap"
    dap_root.mkdir(parents=True, exist_ok=True)
    plan = MaNGAAnalysisPlan.from_toml(str(plan_path), cube=cube,
                                       analysis_path=str(dap_root))
    if disable_eline_fits:
        # AnalysisPlan._validate() fills a missing eline_fits block with an
        # empty dict, which instantiates the *default* EmissionLineModel.
        # Explicitly set it to None so the moments-only Stage A really skips
        # the expensive Gaussian fit.
        for plan_key in plan.keys():
            plan.elfit[plan_key] = None
    log_path = out / "logs" / "manga_dap.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"MaNGA DAP {mangadap_version}: {cube_path.name}")
    print(f"  plate/ifu       : {cube.plate}/{cube.ifudesign}")
    print(f"  z (NSA)         : {cube.meta['z']:.7f}")
    print(f"  Reff/ell/PA     : {cube.meta['reff']:.3f} arcsec, "
          f"{cube.meta['ell']:.3f}, {cube.meta['pa']:.3f} deg")
    print(f"  DAPTYPE/plan    : {config['dap']['daptype']}")
    print(f"  output          : {dap_root}")

    caught = []
    t0 = time.perf_counter()
    status = None
    error = None
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            status = manga_dap(cube, plan, log=str(log_path), verbose=verbose)
    except Exception:
        error = traceback.format_exc()
    elapsed = time.perf_counter() - t0

    warning_counts = Counter(
        f"{w.category.__name__}: {str(w.message)[:180]}" for w in caught
    )
    warning_summary = [{"message": msg, "count": n}
                       for msg, n in warning_counts.most_common(30)]

    method_dir = dap_root / config["dap"]["daptype"] / str(cube.plate) / str(cube.ifudesign)
    maps_path = find_maps(method_dir, cube.plate, cube.ifudesign, config["dap"]["daptype"])
    model_path = find_model_cube(method_dir, cube.plate, cube.ifudesign, config["dap"]["daptype"])
    return {
        "cube": cube,
        "plan": plan,
        "dap_root": dap_root,
        "method_dir": method_dir,
        "maps_path": maps_path,
        "model_path": model_path,
        "log_path": log_path,
        "status_code": status,
        "error": error,
        "runtime_seconds": elapsed,
        "warnings": warning_summary,
        "warning_count": len(caught),
        "mangadap_version": mangadap_version,
        "dap_meta": {
            "z": cube.meta["z"],
            "vel_kms": cube.meta.get("vel"),
            "vdisp_initial_kms": cube.meta["vdisp"],
            "ell": cube.meta["ell"],
            "pa_deg": cube.meta["pa"],
            "reff_arcsec": cube.meta["reff"],
            "ebv_galactic": cube.meta.get("ebv"),
            "drpcrit": cube.meta.get("drpcrit"),
            "plate": cube.plate,
            "ifudesign": cube.ifudesign,
            "drpver": cube.drpver,
            "name": cube.name,
            "rss_loaded": rss_loaded,
            "rss_note": rss_note,
            "can_compute_covariance": bool(getattr(cube, "can_compute_covariance", False)),
        },
    }


# ---------------------------------------------------------------------------
# science tables
# ---------------------------------------------------------------------------
def _fmt(value):
    if value is None:
        return ""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    return "" if (math.isnan(value) or math.isinf(value)) else value


def _snr(flux, err):
    return np.where(np.isfinite(flux) & np.isfinite(err) & (err > 0), flux / err, np.nan)


def build_line_tables(maps: dict, out: Path, daptype: str):
    """Write the compact per-spaxel table, the long table and a line summary."""
    f = key_fluxes(maps)
    sv, sve, ss, sse = stellar_arrays(maps)
    ny, nx = maps["gflux"].shape[1:]
    # Precompute kinematics and EWs once for each key line; the per-spaxel loop
    # below is then pure table assembly.
    kin = {key: line_kinematics(maps, key) for key in
           ("ha", "hb", "oiii_5007", "nii_6584", "sii_6716", "sii_6731")}
    ews = {key: line_ew(maps, key) for key in
           ("ha", "hb", "oiii_5007", "nii_6584", "sii_6716", "sii_6731")}
    summary_kin = {key: line_kinematics(maps, key) for key in LINE_KEYS}
    summary_ew = {key: line_ew(maps, key) for key in LINE_KEYS}
    rows = []
    for iy in range(ny):
        for ix in range(nx):
            row = {
                "spaxel_index": iy * nx + ix,
                "row": iy,
                "col": ix,
                "ra_deg": _fmt(maps["ra"][iy, ix]),
                "dec_deg": _fmt(maps["dec"][iy, ix]),
                "x_arcsec": _fmt(maps["skycoo"][0][iy, ix]),
                "y_arcsec": _fmt(maps["skycoo"][1][iy, ix]),
                "binid": int(maps["binid"][0][iy, ix]),
            }
            for key, prefix in (("ha", "ha"), ("hb", "hb"),
                                ("oiii_5007", "oiii_5007"),
                                ("nii_6584", "nii_6584"),
                                ("sii_6716", "sii_6716"),
                                ("sii_6731", "sii_6731"),
                                ("sii_total", "sii_total")):
                flux = f[key][iy, ix]
                err = f[f"{key}_err"][iy, ix]
                if key != "sii_total":
                    vel, verr, sig, serr = (arr[iy, ix] for arr in kin[key])
                    ew, ewerr, _ = (arr[iy, ix] for arr in ews[key])
                else:
                    vel = verr = sig = serr = ew = ewerr = np.nan
                row[f"{prefix}_flux"] = _fmt(flux)
                row[f"{prefix}_flux_err"] = _fmt(err)
                row[f"{prefix}_snr"] = _fmt(_snr(flux, err))
                row[f"{prefix}_vel"] = _fmt(vel)
                row[f"{prefix}_vel_err"] = _fmt(verr)
                row[f"{prefix}_sigma"] = _fmt(sig)
                row[f"{prefix}_sigma_err"] = _fmt(serr)
                row[f"{prefix}_ew"] = _fmt(ew)
            for key in ("o3_hb", "n2_ha", "s2_ha", "oi_ha", "ha_hb"):
                row[key] = _fmt(f[key][iy, ix])
                row[f"{key}_err"] = _fmt(f[f"{key}_err"][iy, ix])
            row["bpt_class"] = f["bpt_class"][iy, ix]
            row["seyfert_liner_s2"] = f["seyfert_liner_s2"][iy, ix]
            row["seyfert_liner_oi"] = f["seyfert_liner_oi"][iy, ix]
            row["stellar_vel"] = _fmt(sv[iy, ix])
            row["stellar_vel_err"] = _fmt(sve[iy, ix])
            row["stellar_sigma"] = _fmt(ss[iy, ix])
            row["stellar_sigma_err"] = _fmt(sse[iy, ix])
            row["spx_snr"] = _fmt(maps["spx_snr"][iy, ix])
            rows.append(row)
    write_csv(out / "manga_lines.csv", rows)
    print(f"  wrote manga_lines.csv ({len(rows)} spaxels)")

    # Long table for all 35 DAP channels.  Compressed because it is a
    # documentation/inspection product, not the compact science table.
    long_rows = []
    for iy in range(ny):
        for ix in range(nx):
            base = {"spaxel_index": iy * nx + ix, "row": iy, "col": ix,
                    "ra_deg": _fmt(maps["ra"][iy, ix]),
                    "dec_deg": _fmt(maps["dec"][iy, ix]),
                    "binid": int(maps["binid"][0][iy, ix])}
            for ich, name in enumerate(maps["line_names"]):
                flux = maps["gflux"][ich, iy, ix]
                ivar = maps["gflux_ivar"][ich, iy, ix]
                mask = maps["gflux_mask"][ich, iy, ix]
                if not (mask == 0 and ivar > 0 and np.isfinite(flux)):
                    continue
                err = 1.0 / math.sqrt(float(ivar))
                ew = maps["gew"][ich, iy, ix]
                ewivar = maps["gew_ivar"][ich, iy, ix]
                ewerr = 1.0 / math.sqrt(float(ewivar)) if ewivar > 0 else np.nan
                vel = maps["gvel"][ich, iy, ix]
                velivar = maps["gvel_ivar"][ich, iy, ix]
                verr = 1.0 / math.sqrt(float(velivar)) if velivar > 0 else np.nan
                sig = maps["gsigma"][ich, iy, ix]
                sigivar = maps["gsigma_ivar"][ich, iy, ix]
                serr = 1.0 / math.sqrt(float(sigivar)) if sigivar > 0 else np.nan
                long_rows.append({**base, "channel": f"C{ich + 1:02d}",
                                  "dap_name": name,
                                  "restwave_vac_A": _restwave(name),
                                  "flux": _fmt(flux), "flux_err": _fmt(err),
                                  "snr": _fmt(flux / err if err > 0 else np.nan),
                                  "vel": _fmt(vel), "vel_err": _fmt(verr),
                                  "sigma": _fmt(sig), "sigma_err": _fmt(serr),
                                  "ew": _fmt(ew), "ew_err": _fmt(ewerr)})
    long_path = out / "manga_lines_all.csv.gz"
    with gzip.open(long_path, "wt", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(long_rows[0].keys()) if long_rows else
                                ["spaxel_index"])
        writer.writeheader()
        writer.writerows(long_rows)
    print(f"  wrote {long_path.name} ({len(long_rows)} line-spaxel measurements)")

    # Line summary.  Flux sums are sums of the per-spaxel model values and are
    # not aperture-corrected; they are a compact census, not a photometric
    # total.  The median is more robust to the reconstructed spaxel grid.
    summary = []
    for key, label, rest in (
        ("ha", "H-alpha 6564", 6564.608), ("hb", "H-beta 4862", 4862.683),
        ("oiii_5007", "[O III] 5007", 5008.240), ("nii_6584", "[N II] 6584", 6585.270),
        ("sii_6716", "[S II] 6716", 6718.295), ("sii_6731", "[S II] 6731", 6732.674),
        ("sii_total", "[S II] 6716+6731", None), ("oi_6300", "[O I] 6300", 6302.046),
        ("oi_6364", "[O I] 6364", 6365.536)):
        flux = f[key]
        err = f[f"{key}_err"]
        good = np.isfinite(flux) & np.isfinite(err) & (flux != 0)
        snr = _snr(flux, err)
        snr3 = good & (snr >= 3)
        if key in LINE_KEYS:
            vel, verr, sig, serr = summary_kin[key]
            ew, ewerr, _ = summary_ew[key]
        else:
            vel = verr = sig = serr = ew = ewerr = np.full(flux.shape, np.nan)
        summary.append({
            "line": label,
            "dap_name": LINE_KEYS.get(key, "SII-6718+SII-6732"),
            "restwave_vac_A": rest if rest is not None else "",
            "n_spaxels": int(np.sum(good)),
            "n_snr_ge_3": int(np.sum(snr3)),
            "median_flux_1e17": _fmt(np.nanmedian(flux[good]) if np.any(good) else np.nan),
            "median_flux_err_1e17": _fmt(np.nanmedian(err[good]) if np.any(good) else np.nan),
            "median_snr": _fmt(np.nanmedian(snr[good]) if np.any(good) else np.nan),
            "sum_flux_1e17": _fmt(np.nansum(flux[good])),
            "sum_flux_err_1e17": _fmt(np.sqrt(np.nansum(err[good] ** 2))),
            "median_ew_A": _fmt(np.nanmedian(ew[good]) if np.any(good) else np.nan),
            "median_vel_kms": _fmt(np.nanmedian(vel[good]) if np.any(good) else np.nan),
            "vel_scatter_kms": _fmt(1.4826 * np.nanmedian(np.abs(vel[good] - np.nanmedian(vel[good])))
                                    if np.any(good) else np.nan),
            "median_sigma_kms": _fmt(np.nanmedian(sig[good]) if np.any(good) else np.nan),
        })
    write_csv(out / "line_summary.csv", summary)
    print("  wrote line_summary.csv")
    return f, sv, sve, ss, sse, summary


def _restwave(name: str) -> float | str:
    table = {
        "OII-3727": 3727.092, "OII-3729": 3729.875, "H12-3751": 3751.2174,
        "H11-3771": 3771.7012, "Hthe-3798": 3798.9757, "Heta-3836": 3836.4720,
        "NeIII-3869": 3869.86, "HeI-3889": 3889.749, "Hzet-3890": 3890.1506,
        "NeIII-3968": 3968.59, "Heps-3971": 3971.1951, "Hdel-4102": 4102.8922,
        "Hgam-4341": 4341.6837, "HeII-4687": 4687.015, "Hb-4862": 4862.683,
        "OIII-4960": 4960.295, "OIII-5008": 5008.240, "NI-5199": 5199.349,
        "NI-5201": 5201.705, "HeI-5877": 5877.252, "OI-6302": 6302.046,
        "OI-6365": 6365.536, "NII-6549": 6549.86, "Ha-6564": 6564.608,
        "NII-6585": 6585.27, "SII-6718": 6718.295, "SII-6732": 6732.674,
        "HeI-7067": 7067.657, "ArIII-7137": 7137.76, "ArIII-7753": 7753.24,
        "Peta-9017": 9017.384, "SIII-9071": 9071.1, "Pzet-9231": 9231.546,
        "SIII-9533": 9533.2, "Peps-9548": 9548.588,
    }
    return table.get(name, "")


def maps_statistics(maps: dict, f: dict) -> dict:
    sv, sve, ss, sse = stellar_arrays(maps)
    gv, gve, gs, gse = line_kinematics(maps, "ha")
    binid = maps["binid"][0]
    good_bins = binid >= 0
    n_bins = int(len(np.unique(binid[good_bins]))) if np.any(good_bins) else 0
    ha = f["ha"]
    good_ha = np.isfinite(ha) & (ha != 0)
    # Brightest H-alpha spaxel, useful for the pedagogical spectrum.
    if np.any(good_ha):
        idx = int(np.nanargmax(np.where(good_ha, ha, np.nan)))
        iy, ix = np.unravel_index(idx, ha.shape)
    else:
        iy = ix = ha.shape[0] // 2
    central = {
        "row": int(iy), "col": int(ix),
        "ra_deg": float(maps["ra"][iy, ix]), "dec_deg": float(maps["dec"][iy, ix]),
        "x_arcsec": float(maps["skycoo"][0][iy, ix]),
        "y_arcsec": float(maps["skycoo"][1][iy, ix]),
        "ha_flux_1e17": float(ha[iy, ix]) if np.isfinite(ha[iy, ix]) else None,
        "ha_snr": float(ha[iy, ix] / f["ha_err"][iy, ix])
        if np.isfinite(f["ha_err"][iy, ix]) and f["ha_err"][iy, ix] > 0 else None,
        "bpt_class": str(f["bpt_class"][iy, ix]),
    }
    return {
        "n_spaxels_total": int(ha.size),
        "n_bins": n_bins,
        "n_spaxels_valid_ha": int(np.sum(good_ha)),
        "n_spaxels_snr3_ha": int(np.sum(good_ha & (_snr(ha, f["ha_err"]) >= 3))),
        "bpt": bpt_fractions(f["bpt_class"]),
        "bpt_s2_subclass": {
            "seyfert": int(np.sum(f["seyfert_liner_s2"] == "seyfert")),
            "liner": int(np.sum(f["seyfert_liner_s2"] == "liner")),
            "unclassified": int(np.sum(f["seyfert_liner_s2"] == "")),
        },
        "stellar_velocity_kms": summary_stats(sv),
        "stellar_sigma_kms": summary_stats(ss),
        "gas_velocity_ha_kms": summary_stats(gv),
        "gas_sigma_ha_kms": summary_stats(gs),
        "spx_snr": summary_stats(maps["spx_snr"]),
        "brightest_ha_spaxel": central,
        "key_flux_sum_1e17": {k: float(np.nansum(f[k][np.isfinite(f[k])]))
                              for k in KEY_LINES},
    }


def extract_central_spectrum(cube_path: Path, model_path: Path | None,
                             maps: dict, row: int, col: int, out: Path,
                             model_arrays: dict | None = None,
                             observed_arrays: dict | None = None) -> dict:
    if observed_arrays is not None:
        wave = np.asarray(observed_arrays["obs_wave"], dtype=float)
        flux = np.asarray(observed_arrays["obs_flux"], dtype=float)
        err = np.asarray(observed_arrays["obs_ferr"], dtype=float)
        good = np.asarray(observed_arrays["obs_good"], dtype=bool)
    else:
        with fits.open(cube_path, memmap=False) as hdu:
            wave = hdu["WAVE"].data.astype(float)
            flux = hdu["FLUX"].data[:, row, col].astype(float)
            ivar = hdu["IVAR"].data[:, row, col].astype(float)
            mask = hdu["MASK"].data[:, row, col].astype(np.int32)
        err = np.full_like(flux, np.nan)
        good = (ivar > 0) & np.isfinite(flux)
        err[good] = 1.0 / np.sqrt(ivar[good])
    spectra = {"wave": wave, "flux": flux, "error": err, "good": good,
               "model": np.full_like(flux, np.nan),
               "emline": np.full_like(flux, np.nan),
               "stellar": np.full_like(flux, np.nan),
               "row": row, "col": col}
    note = "Brightest H-alpha spaxel"
    if model_arrays is not None:
        wave_model = model_arrays.get("model_wave")
        if wave_model is not None and np.asarray(wave_model).shape == wave.shape:
            wave = np.asarray(wave_model, dtype=float)
        spectra["model"] = np.asarray(model_arrays["model_flux"], dtype=float)
        spectra["emline"] = np.asarray(model_arrays["model_eml_flux"], dtype=float)
        spectra["stellar"] = spectra["model"] - spectra["emline"]
        note = ("Brightest H-alpha spaxel; official SASUKE fixed-continuum fit "
                "on its HYB10 bin")
    elif model_path is not None and Path(model_path).exists():
        with fits.open(model_path, memmap=False) as hdu:
            if "WAVE" in hdu:
                wave_model = hdu["WAVE"].data.astype(float)
                if wave_model.shape == wave.shape and np.allclose(wave_model, wave, rtol=1e-6):
                    wave = wave_model
            for ext in ("MODEL", "EMLINE", "STELLAR"):
                if ext in hdu:
                    spectra[ext.lower()] = hdu[ext].data[:, row, col].astype(float)
        note = "Brightest H-alpha spaxel; model/emline/stellar from the DAP model LOGCUBE"
    # Save a compact FITS table.
    cols = [fits.Column(name="wave", format="D", unit="Angstrom", array=spectra["wave"]),
            fits.Column(name="flux", format="D", unit="1e-17 erg/s/cm2/A/spaxel",
                        array=spectra["flux"]),
            fits.Column(name="error", format="D", unit="1e-17 erg/s/cm2/A/spaxel",
                        array=spectra["error"]),
            fits.Column(name="model", format="D", unit="1e-17 erg/s/cm2/A/spaxel",
                        array=spectra["model"]),
            fits.Column(name="emline", format="D", unit="1e-17 erg/s/cm2/A/spaxel",
                        array=spectra["emline"]),
            fits.Column(name="stellar", format="D", unit="1e-17 erg/s/cm2/A/spaxel",
                        array=spectra["stellar"]),
            fits.Column(name="good", format="L", array=spectra["good"])]
    hdu = fits.BinTableHDU.from_columns(cols)
    hdu.header["ROW"] = (row, "spaxel row in the 74x74 DAP grid")
    hdu.header["COL"] = (col, "spaxel column in the 74x74 DAP grid")
    hdu.header["RA"] = (float(maps["ra"][row, col]), "RA J2000 (deg)")
    hdu.header["DEC"] = (float(maps["dec"][row, col]), "Dec J2000 (deg)")
    hdu.header["FLUXUNIT"] = "1e-17 erg/s/cm2/A/spaxel"
    hdu.header["NOTE"] = note
    hdu.writeto(out, overwrite=True)
    return spectra


def write_key_maps(maps: dict, out: Path, title: str):
    f = key_fluxes(maps)
    sv, sve, ss, sse = stellar_arrays(maps)
    wcs = WCS(maps["linehdr"], naxis=2)
    wcs_header = wcs.to_header(relax=True)
    products = [
        ("HA_GFLUX", f["ha"], "1e-17 erg/s/cm2/spaxel", "H-alpha Gaussian flux"),
        ("HA_GFLUX_ERR", f["ha_err"], "1e-17 erg/s/cm2/spaxel", "H-alpha formal error"),
        ("HB_GFLUX", f["hb"], "1e-17 erg/s/cm2/spaxel", "H-beta Gaussian flux"),
        ("HB_GFLUX_ERR", f["hb_err"], "1e-17 erg/s/cm2/spaxel", "H-beta formal error"),
        ("OIII_5007_GFLUX", f["oiii_5007"], "1e-17 erg/s/cm2/spaxel", "[O III] 5007 flux"),
        ("OIII_5007_GFLUX_ERR", f["oiii_5007_err"], "1e-17 erg/s/cm2/spaxel", "[O III] 5007 error"),
        ("NII_6584_GFLUX", f["nii_6584"], "1e-17 erg/s/cm2/spaxel", "[N II] 6584 flux"),
        ("NII_6584_GFLUX_ERR", f["nii_6584_err"], "1e-17 erg/s/cm2/spaxel", "[N II] 6584 error"),
        ("SII_TOTAL_GFLUX", f["sii_total"], "1e-17 erg/s/cm2/spaxel", "[S II] 6716+6731 flux"),
        ("SII_TOTAL_GFLUX_ERR", f["sii_total_err"], "1e-17 erg/s/cm2/spaxel", "[S II] total error"),
        ("HA_HB", f["ha_hb"], "ratio", "H-alpha/H-beta (observed)"),
        ("O3_HB", f["o3_hb"], "ratio", "[O III] 5007/H-beta"),
        ("N2_HA", f["n2_ha"], "ratio", "[N II] 6584/H-alpha"),
        ("S2_HA", f["s2_ha"], "ratio", "[S II]/H-alpha"),
        ("BPT_CODE", f["bpt_code"].astype(np.int16), "code", "0 unclassified, 1 SF, 2 composite, 3 Seyfert, 4 LINER, 5 AGN unclassified"),
        ("STELLAR_VEL", sv, "km/s", "pPXF stellar velocity"),
        ("STELLAR_VEL_ERR", sve, "km/s", "stellar velocity formal error"),
        ("STELLAR_SIGMA", ss, "km/s", "pPXF stellar velocity dispersion"),
        ("STELLAR_SIGMA_ERR", sse, "km/s", "stellar sigma formal error"),
        ("SPX_SNR", maps["spx_snr"], "S/N", "continuum S/N per spaxel"),
        ("BINID", maps["binid"][0], "index", "adopted HYB10 bin ID (-1 = no bin)"),
    ]
    hdus = [fits.PrimaryHDU()]
    pri = hdus[0].header
    pri["TITLE"] = (title, "product")
    pri["DAPTYPE"] = (maps["prihdr"].get("DAPTYPE", ""), "DAP analysis type")
    pri["VERSDAP"] = (maps["prihdr"].get("VERSDAP", ""), "DAP version")
    pri["VERSDRP3"] = (maps["prihdr"].get("VERSDRP3", ""), "DRP version")
    pri["PLATEIFU"] = (maps["prihdr"].get("PLATEIFU", ""), "MaNGA plate-ifu")
    pri["BUNIT"] = ("mixed", "see individual EXTNAME/BUNIT")
    for name, data, unit, desc in products:
        hdr = wcs_header.copy()
        hdr["BUNIT"] = (unit, "data unit")
        hdr["DESCR"] = (desc, "product description")
        hdus.append(fits.ImageHDU(data=np.asarray(data, dtype=np.float32),
                                 header=hdr, name=name))
    fits.HDUList(hdus).writeto(out, overwrite=True)


def write_provenance(path: Path, source: dict, config: dict, versions: dict,
                     inputs: dict, products: dict, run: dict, stats: dict,
                     comparison_note: str = ""):
    lines = [
        f"# MaNGA DAP provenance — {source['name']} ({source['plateifu']})",
        "",
        "This note documents a **real run of the official SDSS MaNGA Data Analysis",
        "Pipeline** (`sdss-mangadap` 4.5.0) on the public DR17 LOGCUBE of NGC 1194.",
        "The published DAP MAPS (v3_1_1/3.1.0) is an independent reference",
        "product; it was not used as an input to this run.",
        "",
        "## Inputs",
        "",
        "| role | file | size (bytes) | SHA-256 | source |",
        "|---|---|---:|---|---|",
    ]
    for role, rec in inputs.items():
        lines.append(f"| `{role}` | `{rec['path']}` | {rec['size_bytes']} | "
                     f"`{rec.get('sha256', '')}` | {rec.get('url', '')} |")
    lines += [
        "",
        "The LOGCUBE is the datacube consumed by the DAP.  LOGRSS is loaded by",
        "the official MaNGA datacube object to compute the spatial covariance",
        "matrix used by the Voronoi binning; it is not fit as a spectrum.  Both",
        "DRP files are downloaded unmodified by",
        "`inputs/NGC1194_z_0.0136/download.sh` and are intentionally not committed",
        "because they exceed GitHub's 100 MB per-file limit.  The 10.8 MB published",
        "MAPS *is* committed because it is the comparison reference.",
        "",
        "## Software",
        "",
        f"- `sdss-mangadap` **{versions.get('sdss-mangadap', '')}** "
        f"(upstream commit `{versions.get('upstream_scm', {}).get('node', '')}`)",
        f"- numpy {versions.get('numpy', '')}, scipy {versions.get('scipy', '')}, "
        f"astropy {versions.get('astropy', '')}, ppxf {versions.get('ppxf', '')}",
        f"- cvxopt {versions.get('cvxopt', '')}, vorbin {versions.get('vorbin', '')}, "
        f"pydl {versions.get('pydl', '')}",
        f"- Python {versions.get('python', '')} on {versions.get('platform', '')}",
        "",
        "## Configuration",
        "",
        f"- DAPTYPE: `{config['dap']['daptype']}`",
        f"- analysis plan: `{run.get('plan_path', 'configs/manga_dap/default/plan_moments.toml')}`",
        f"- binning: `{config['binning']['key']}`, Voronoi target S/N = {config['binning']['target_snr']}",
        f"- stellar continuum: `{config['continuum']['key']}` + pPXF, "
        f"MILES-HC templates",
        f"- emission lines: `{config['emission_line_fit']['key']}` + SASUKE, "
        f"line database `{config['line_database']['key']}` ({config['line_database']['n_channels']} channels)",
        f"- templates: `{config['emission_line_fit']['template_library']}`; "
        f"exact file hashes are in `effective_config.json`",
        f"- uncertainty: {config['uncertainty']['mode']}; no MCMC",
        "",
        "## Run",
        "",
        f"- started: {run.get('started_utc', '')}",
        f"- finished: {run.get('finished_utc', '')}",
        f"- wall time: {run.get('runtime_seconds', 0):.1f} s",
        f"- status: **{run.get('status', '')}**",
        f"- DAP status code: {run.get('dap_status_code')}",
        f"- warnings captured: {run.get('warning_count', 0)}",
        "",
    ]
    if run.get("error"):
        lines += ["The DAP raised an exception; the exact traceback is in `run.json`.", "",
                  "```text", run["error"].strip()[:4000], "```", ""]
    if config.get("fast_eline", {}).get("enabled"):
        lines += [
            "## Production mode (important)",
            "",
            "The **full** 65-template MaStar-HC2 `EmissionLineModel` did not complete on",
            "this 8-core host: two attempts (`ensemble=True` and `ensemble=False`) ran for",
            "60 and 40 minutes; the latter reached 39/175 binned spectra.  This is a",
            "runtime/memory limitation of the full DAP emission-line stage, not a data",
            "failure.  The production run therefore uses:",
            "",
            "1. Stage A: the official DAP `manga_dap()` workflow with the Gaussian",
            "   `eline_fits` block removed.  This completed the reduction assessment,",
            "   HYB10 Voronoi binning, pPXF stellar kinematics, `EMOM` emission-line",
            "   moments and spectral indices, and wrote a MAPS file.",
            "2. Stage B: the official DAP `Sasuke` Gaussian fitter on the same 175 official",
            "   DAP binned spectra, with the official pPXF stellar-continuum model supplied",
            "   as a fixed per-spectrum template.  The full `ELPMPL11` 35-line database,",
            "   DAP pixel mask and spectral resolution are retained.  `ensemble=False` and",
            "   `mdegree=14`; the fit is parallelised across bins.",
            "",
            "The merged MAPS has the same extension names as the survey product.  The",
            "published DAP MAPS (v3_1_1/3.1.0) remains the independent reference and was",
            "not used as an input to either stage.",
            "",
        ]
    lines += [
        "## Products",
        "",
        "| file | contents |",
        "|---|---|",
    ]
    for name, desc in products.items():
        lines.append(f"| `{name}` | {desc} |")
    lines += [
        "",
        "## Measurement summary",
        "",
        f"- bins: {stats.get('n_bins')}",
        f"- spaxels with a valid H-alpha Gaussian flux: {stats.get('n_spaxels_valid_ha')}",
        f"- BPT classes: {stats.get('bpt')}",
        f"- brightest H-alpha spaxel: row {stats.get('brightest_ha_spaxel', {}).get('row')}, "
        f"col {stats.get('brightest_ha_spaxel', {}).get('col')}, "
        f"BPT `{stats.get('brightest_ha_spaxel', {}).get('bpt_class')}`",
        "",
        "## Comparison to the published MAPS",
        "",
        comparison_note or ("The comparison is produced by `Tools/manga_dap/compare_maps.py` "
                            "and stored under `comparison/`."),
        "",
        "## Limitations",
        "",
    ]
    for limitation in config.get("limitations", []):
        lines.append(f"- {limitation}")
    lines += [
        "",
        "## Reproduction",
        "",
        "```bash",
        "bash Pipelines/build_images.sh manga_dap",
        "bash inputs/NGC1194_z_0.0136/download.sh",
        "bash Pipelines/run_manga_dap_docker.sh \\",
        "  inputs/NGC1194_z_0.0136 \\",
        "  outputs/NGC1194_z_0.0136/manga_dap \\",
        "  --reference inputs/NGC1194_z_0.0136/raw/manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz",
        "```",
        "",
        "The runner mounts the input directory read-only, mounts the config",
        "directory read-only, and writes only under the requested output directory.",
        "",
    ]
    path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="/app/input")
    parser.add_argument("--cube", default=None, help="explicit LOGCUBE path")
    parser.add_argument("--out", default="/app/output")
    parser.add_argument("--config", default="/app/config")
    parser.add_argument("--reference", default=None,
                        help="published MAPS used only for provenance/comparison")
    parser.add_argument("--source-key", default=None)
    parser.add_argument("--skip-dap", action="store_true",
                        help="post-process an existing fits/manga_dap_maps.fits.gz")
    parser.add_argument("--fast-eline", action="store_true",
                        help="run the official SASUKE fit on the 175 DAP bins with the "
                             "pPXF continuum fixed, instead of the full 65-template "
                             "EmissionLineModel (which did not complete; see README)")
    parser.add_argument("--fast-nproc", type=int, default=None,
                        help="processes for the fast SASUKE fit (default MANGA_DAP_NPROC or 8)")
    parser.add_argument("--fast-mdegree", type=int, default=None,
                        help="multiplicative polynomial order for the fast SASUKE fit")
    parser.add_argument("--stage-a-only", action="store_true",
                        help="run the official moments-only DAP stages and stop")
    parser.add_argument("--fast-only", action="store_true",
                        help="run the fast SASUKE stage against an existing Stage-A output")
    parser.add_argument("--keep-intermediate", action="store_true")
    parser.add_argument("--verbose", type=int, default=1)
    args = parser.parse_args(argv)

    started = utc_now()
    t_start = time.perf_counter()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)
    (out / "fits").mkdir(exist_ok=True)
    config_dir = Path(args.config)
    config = json.loads((config_dir / "config.json").read_text())
    if args.fast_eline or args.fast_only:
        plan_name = config["dap"].get("plan_file_moments", "plan_moments.toml")
    else:
        plan_name = config["dap"]["plan_file"]
    plan_path = config_dir / plan_name
    source = config["source"]
    source_key = args.source_key or source["key"]
    daptype = config["dap"]["daptype"]
    plate = int(source.get("plate", PLATE_DEFAULT))
    ifu = int(source.get("ifu_design", IFU_DEFAULT))

    versions = collect_versions()
    print(json.dumps(versions, indent=2))

    input_dir = Path(args.input_dir).resolve()
    cube_path = find_input_cube(input_dir, args.cube)
    rss_path = input_dir / f"manga-{plate}-{ifu}-LOGRSS.fits.gz"
    if not rss_path.exists():
        rss_path = input_dir / "raw" / f"manga-{plate}-{ifu}-LOGRSS.fits.gz"
    inputs = {
        "manga_cube": {**file_record(cube_path), "url": source.get("urls", {}).get("manga_cube", "")},
        "manga_rss": ({**file_record(rss_path), "url": source.get("urls", {}).get("manga_rss", "")}
                      if rss_path.exists() else {"path": rss_path.name, "status": "not_present"}),
        "reference_maps": ({"path": Path(args.reference).name,
                            "size_bytes": Path(args.reference).stat().st_size,
                            "sha256": sha256_file(Path(args.reference)),
                            "url": source.get("urls", {}).get("manga_maps_reference", "")}
                           if args.reference and Path(args.reference).exists()
                           else {"status": "not_provided"}),
    }

    run_info = {
        "tool": "manga_dap",
        "source_key": source_key,
        "status": "running",
        "started_utc": started,
        "versions": versions,
        "inputs": inputs,
        "config": config,
        "plate": plate,
        "ifu_design": ifu,
        "daptype": daptype,
        "host": {
            "cpu_count": os.cpu_count(),
            "memory_total_kb": _mem_total_kb(),
            "image": os.environ.get("MANGA_DAP_IMAGE", ""),
            "image_size_bytes": int(os.environ.get("MANGA_DAP_IMAGE_SIZE", "0") or 0),
            "repo_commit": os.environ.get("MANGA_DAP_REPO_COMMIT", ""),
        },
    }

    dap = None
    maps_path = None
    if args.fast_only:
        stage_a_path = out / "stage_a.json"
        if not stage_a_path.exists():
            raise FileNotFoundError(f"--fast-only requires {stage_a_path} (run --stage-a-only first)")
        stage_a = json.loads(stage_a_path.read_text())
        dap = {
            "status_code": stage_a.get("dap_status_code"),
            "error": stage_a.get("dap_error"),
            "runtime_seconds": stage_a.get("runtime_seconds", 0.0),
            "warning_count": stage_a.get("warning_count", 0),
            "warnings": stage_a.get("warnings", []),
            "dap_meta": stage_a.get("dap_meta", {}),
            "dap_root": out / "dap",
            "method_dir": Path(stage_a["method_dir"]) if stage_a.get("method_dir") else None,
            "model_path": Path(stage_a["model_path"]) if stage_a.get("model_path") else None,
            "maps_path": out / "fits" / "manga_dap_moments_maps.fits.gz",
            "log_path": Path(stage_a["log_path"]) if stage_a.get("log_path") else None,
        }
        import fast_eline
        fast_meta = fast_eline.run_fast_eline(
            dap["dap_root"], plate, ifu, config, out,
            nproc=args.fast_nproc, mdegree=args.fast_mdegree)
        dap["fast_eline"] = fast_meta
        dap["runtime_seconds"] = float(dap.get("runtime_seconds") or 0.0) + \
            float(fast_meta.get("runtime_seconds") or 0.0)
        maps_path = out / "fits" / "manga_dap_maps.fits.gz"
        print(f"fast SASUKE MAPS written to {maps_path}")
    elif args.skip_dap:
        maps_path = out / "fits" / "manga_dap_maps.fits.gz"
        if not maps_path.exists():
            raise FileNotFoundError(f"--skip-dap requested but {maps_path} does not exist")
        dap = {"status_code": None, "error": None, "runtime_seconds": 0.0,
               "warning_count": 0, "warnings": [], "dap_meta": {},
               "model_path": out / "fits" / "manga_dap_model_cube.fits.gz",
               "maps_path": maps_path}
        print(f"skipping DAP; using {maps_path}")
    else:
        dap = run_official_dap(cube_path, out, config, plan_path, verbose=args.verbose,
                               disable_eline_fits=args.fast_eline)
        if dap["maps_path"] is None:
            dap["error"] = (dap.get("error") or "") + \
                "\nDAP completed without producing a MAPS file."
        elif args.fast_eline:
            # Stage A produced the moments-only MAPS.  Keep it, then fill the
            # Gaussian-line extensions with the official Sasuke fit on the
            # official DAP binned spectra and fixed pPXF continuum.
            shutil.copy2(dap["maps_path"], out / "fits" / "manga_dap_moments_maps.fits.gz")
            print(f"moments-only MAPS copied to {out / 'fits' / 'manga_dap_moments_maps.fits.gz'}")
            write_json(out / "stage_a.json", {
                "status": "ok", "runtime_seconds": dap.get("runtime_seconds"),
                "dap_status_code": dap.get("status_code"), "dap_error": dap.get("error"),
                "warning_count": dap.get("warning_count", 0),
                "warnings": dap.get("warnings", []), "dap_meta": dap.get("dap_meta", {}),
                "dap_root": str(dap.get("dap_root")),
                "method_dir": str(dap.get("method_dir")) if dap.get("method_dir") else None,
                "model_path": str(dap.get("model_path")) if dap.get("model_path") else None,
                "log_path": str(dap.get("log_path")) if dap.get("log_path") else None,
            })
            if args.stage_a_only:
                print("stage A complete; stopping before the fast SASUKE fit")
                return 0
            import fast_eline
            fast_meta = fast_eline.run_fast_eline(
                dap["dap_root"], plate, ifu, config, out,
                nproc=args.fast_nproc, mdegree=args.fast_mdegree)
            dap["fast_eline"] = fast_meta
            dap["model_path"] = None
            maps_path = out / "fits" / "manga_dap_maps.fits.gz"
            print(f"fast SASUKE MAPS written to {maps_path}")
        else:
            shutil.copy2(dap["maps_path"], out / "fits" / "manga_dap_maps.fits.gz")
            maps_path = out / "fits" / "manga_dap_maps.fits.gz"
            print(f"MAPS copied to {maps_path}")

    # Scientific post-processing.
    f = None
    stats = {}
    if maps_path is not None and Path(maps_path).exists():
        maps = load_maps(maps_path)
        f, sv, sve, ss, sse, summary = build_line_tables(maps, out, daptype)
        stats = maps_statistics(maps, f)
        write_json(out / "maps_stats.json", stats)
        plot_maps(maps, out / "figures" / "manga_dap_maps.png",
                  title_prefix=f"MaNGA DAP {versions['sdss-mangadap']}")
        plot_bpt(maps, out / "figures" / "manga_dap_bpt.png")
        write_key_maps(maps, out / "fits" / "manga_dap_key_maps.fits.gz",
                       f"MaNGA DAP key maps for {source['plateifu']}")
        # Central/brightest spectrum and fit figure.
        bright = stats["brightest_ha_spaxel"]
        model_path = dap.get("model_path")
        fast_arrays = None
        if dap.get("fast_eline"):
            import fast_eline
            bin_id = int(maps["binid"][0][bright["row"], bright["col"]])
            fast_arrays = fast_eline.central_model(
                Path(dap["fast_eline"]["bsp"]), Path(dap["fast_eline"]["continuum"]),
                bin_id, config)
            if not fast_arrays.get("ok"):
                print(f"fast central re-fit failed: {fast_arrays.get('error')}")
                fast_arrays = None
        spectra = extract_central_spectrum(cube_path, model_path, maps,
                                           bright["row"], bright["col"],
                                           out / "fits" / "manga_dap_central_spectra.fits",
                                           model_arrays=fast_arrays,
                                           observed_arrays=fast_arrays)
        if np.any(np.isfinite(spectra["model"])):
            plot_spectrum_fit(
                spectra, out / "figures" / "manga_dap_spectrum_fit.png",
                title=(f"MaNGA DAP fit at the brightest H-alpha spaxel "
                       f"(row {bright['row']}, col {bright['col']})"))
        else:
            print("model LOGCUBE not available; skipping spectrum fit figure")
        # Keep small DAP reference products; the full model cube is huge and is
        # removed after the central spectrum has been extracted.
        _collect_dap_reference_products(dap.get("method_dir"), out / "fits")
        if not args.keep_intermediate:
            _clean_intermediate(dap.get("dap_root"), dap.get("model_path"), out)
    else:
        stats = {"status": "no_maps"}
        print("ERROR: no MAPS product; science tables were not written")

    finished = utc_now()
    elapsed = time.perf_counter() - t_start
    fast_meta = dap.get("fast_eline")
    fast_failed = bool(fast_meta and fast_meta.get("n_fail", 0) >= fast_meta.get("n_bins", 1))
    status = "ok" if (maps_path is not None and Path(maps_path).exists()
                      and not (dap.get("error")) and not fast_failed) else "failed"
    run_info.update({
        "status": status,
        "dap_mode": ("official DAP moments stage + official SASUKE fixed-continuum fit"
                     if fast_meta else "official DAP full EmissionLineModel"),
        "fast_eline": fast_meta,
        "stages_completed": (
            ["reduction_assessment", "HYB10_binning", "ppxf_stellar_kinematics",
             "emission_line_moments", "spectral_indices", "sasuke_gaussian_fit_fixed_continuum"]
            if fast_meta else
            ["reduction_assessment", "HYB10_binning", "ppxf_stellar_kinematics",
             "emission_line_moments", "sasuke_gaussian_fit", "spectral_indices"]),
        "full_dap_attempt": config.get("dap", {}).get("full_attempt"),
        "finished_utc": finished,
        "runtime_seconds": elapsed,
        "dap_runtime_seconds": dap.get("runtime_seconds", 0.0),
        "dap_status_code": dap.get("status_code"),
        "dap_error": dap.get("error"),
        "warning_count": dap.get("warning_count", 0),
        "warnings": dap.get("warnings", []),
        "dap_meta": dap.get("dap_meta", {}),
        "dap_products": {
            "maps": str(maps_path) if maps_path else None,
            "model_cube": str(dap.get("model_path")) if dap.get("model_path") else None,
            "dap_method_dir": str(dap.get("method_dir")) if dap.get("method_dir") else None,
            "dap_log": str(dap.get("log_path")) if dap.get("log_path") else None,
        },
        "stats": stats,
        "outputs": _output_manifest(out),
    })
    write_json(out / "run.json", run_info)

    effective = {
        "tool": "manga_dap",
        "variant": config.get("variant", "default"),
        "source": source,
        "versions": versions,
        "configuration": config,
        "effective_plan": parse_plan(plan_path),
        "plan_path": str(plan_path),
        "fast_eline": config.get("fast_eline"),
        "production_mode": config["dap"].get("production_mode"),
        "dap_data_manifest": dap_data_manifest(),
        "dap_metadata_used": dap.get("dap_meta", {}),
        "uncertainty": config["uncertainty"],
        "products": run_info["dap_products"],
        "input_hashes": inputs,
        "limitations": config.get("limitations", []),
    }
    write_json(out / "effective_config.json", effective)

    products_md = {
        "manga_lines.csv": "compact per-spaxel table for the six key lines, ratios, BPT class and stellar kinematics",
        "manga_lines_all.csv.gz": "long table of every valid DAP channel measurement (35 channels)",
        "line_summary.csv": "per-line census: counts, medians, sums, EWs and kinematics",
        "fast_eline_bins.csv": "official SASUKE fit result for each of the 175 HYB10 bins",
        "fits/manga_dap_moments_maps.fits.gz": "Stage-A official DAP MAPS with stellar kinematics and emission-line moments (empty Gaussian extensions)",
        "logs/full_dap_attempt_summary.txt": "exact evidence for the full 65-template EmissionLineModel runtime blocker",
        "maps_stats.json": "global BPT fractions, kinematic summaries and bin/spaxel counts",
        "fits/manga_dap_maps.fits.gz": "full DAP MAPS produced by this run",
        "fits/manga_dap_key_maps.fits.gz": "compact subset of key line, BPT and kinematic maps",
        "fits/manga_dap_central_spectra.fits": "observed and DAP model spectra at the brightest H-alpha spaxel",
        "figures/manga_dap_maps.png": "pedagogical 3x3 maps of line flux, kinematics and S/N",
        "figures/manga_dap_bpt.png": "N2-BPT diagram and spatial ionization-class map",
        "figures/manga_dap_spectrum_fit.png": "H-beta/[O III] and H-alpha/[N II]/[S II] data-model fit",
        "run.json": "versions, input hashes, DAP status, warnings, runtime and product manifest",
        "effective_config.json": "exact plan, metadata, template/DB hashes and uncertainty settings",
        "provenance.md": "human-readable provenance, reproduction command and limitations",
    }
    comparison_note = ""
    if args.reference and Path(args.reference).exists() and maps_path is not None:
        comparison_note = (
            "The independent comparison to the published MAPS is produced by "
            "`Tools/manga_dap/compare_maps.py`; its summary is in "
            "`comparison/comparison_summary.json` and `comparison/comparison_notes.md`."
        )
    write_provenance(out / "provenance.md", source, config, versions, inputs,
                     products_md, run_info, stats, comparison_note)
    print(f"status={status} runtime={elapsed:.1f}s out={out}")
    return 0 if status == "ok" else 1


def _mem_total_kb() -> int | None:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1])
    except Exception:
        pass
    return None


def _output_manifest(root: Path) -> list[dict]:
    out = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "manga_dap_maps.fits.gz" and path.stat().st_size > 50 * 1024 * 1024:
            continue
        rel = path.relative_to(root)
        out.append({"path": str(rel), "size_bytes": path.stat().st_size})
    return out


def _collect_dap_reference_products(method_dir: Path | None, fits_dir: Path):
    """Copy small, scientifically useful DAP reference products."""
    if method_dir is None or not Path(method_dir).exists():
        return
    method_dir = Path(method_dir)
    candidates = []
    for pattern in ("*EMLINE*.fits.gz", "*LOGRSS*.fits.gz", "*STELLARCONT*.fits.gz"):
        candidates += sorted((method_dir / "ref").glob(pattern))
    for path in candidates:
        if path.stat().st_size > 60 * 1024 * 1024:
            continue
        target = fits_dir / f"dap_ref_{path.name}"
        if not target.exists():
            shutil.copy2(path, target)
            print(f"  kept DAP reference product {target.name} "
                  f"({target.stat().st_size / 1e6:.1f} MB)")


def _clean_intermediate(dap_root: Path | None, model_path: Path | None, out: Path):
    """Remove the multi-hundred-MB model cube while keeping the run log."""
    if model_path is not None and Path(model_path).exists():
        size = Path(model_path).stat().st_size
        Path(model_path).unlink()
        print(f"  removed intermediate model cube ({size / 1e6:.0f} MB)")
    # Keep the DAP log; remove the rest of the bulky tree.
    if dap_root is not None and Path(dap_root).exists():
        for child in sorted(Path(dap_root).iterdir()):
            if child.name == "logs":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        print(f"  cleaned intermediate DAP tree under {dap_root}")


if __name__ == "__main__":
    raise SystemExit(main())
