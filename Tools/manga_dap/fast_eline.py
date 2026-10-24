#!/usr/bin/env python3
"""Fast fixed-continuum SASUKE emission-line fit on official DAP bins.

The full MaNGA DAP emission-line model fits every HYB10 bin with a 65-template
MaStar-HC2 library, a 35-line database and a 14th-order multiplicative
polynomial.  On the 175-bin validation run this did not complete in more than
one hour (two attempts: ``ensemble=True`` and ``ensemble=False``; the latter
reached 39/175 spectra in 40 min).  The same official DAP ``Sasuke`` fitter is
used here on the **official DAP binned spectra** with the **official pPXF
stellar-continuum model** supplied as a fixed per-spectrum template.  This is
the standard DAP "fixed continuum" configuration, just with the continuum taken
from the completed DAP stellar-kinematics stage instead of being rebuilt from
65 templates inside every emission-line fit.  It keeps the full ELPMPL11 line
database and the DAP pixel mask/resolution, and it returns the same
``FLUX``/``FLUXERR``/``KIN``/``EW`` quantities that the DAP maps use.

The fit is embarrassingly parallel across bins; the runner uses one process per
CPU with single-threaded BLAS.  The result is merged into the partial MAPS
produced by the moments-only DAP run (see ``run_manga_dap.py --fast-eline``).
"""
from __future__ import annotations

import csv
import math
import multiprocessing as mp
import os
import time
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

C_KMS = 299792.458

_G = {}


# ---------------------------------------------------------------------------
# data loading
# ---------------------------------------------------------------------------
def find_binned_products(dap_root: Path, plate: int, ifu: int) -> tuple[Path, Path]:
    common = dap_root / "common" / str(plate) / str(ifu)
    bsp = common / f"manga-{plate}-{ifu}-SNRG-HYB10.fits.gz"
    cont = common / f"manga-{plate}-{ifu}-SNRG-HYB10-MILESHC.fits.gz"
    if not bsp.exists():
        hits = sorted(common.glob("*SNRG-HYB10.fits.gz"))
        if not hits:
            raise FileNotFoundError(f"no binned spectra in {common}")
        bsp = hits[0]
    if not cont.exists():
        hits = sorted(common.glob("*SNRG-HYB10-MILESHC.fits.gz"))
        if not hits:
            raise FileNotFoundError(f"no stellar continuum in {common}")
        cont = hits[0]
    return bsp, cont


def load_binned(bsp_path: Path, cont_path: Path) -> dict:
    with fits.open(bsp_path, memmap=False) as hdu:
        wave = hdu["WAVE"].data.astype(float)
        flux = hdu["FLUX"].data.T.astype(float)
        ivar = hdu["IVAR"].data.T.astype(float)
        mask = hdu["MASK"].data.T.astype(np.int32)
        sres = hdu["SPECRES"].data.T.astype(float)
        binid_map = hdu["BINID"].data.astype(np.int32)
        bins = hdu["BINS"].data.copy()
    with fits.open(cont_path, memmap=False) as hdu:
        cflux = hdu["FLUX"].data.T.astype(float)
        ckin = hdu["PAR"].data["KIN"].astype(float)
    if cflux.shape != flux.shape:
        raise ValueError("continuum and binned spectra shapes differ")
    if len(bins) != flux.shape[0]:
        raise ValueError("BINS table length does not match the number of spectra")
    ferr = np.full_like(flux, np.nan)
    # Mirror the DAP get_spectra_to_fit() masking: reject the binned-spectrum
    # flags that the survey emission-line fit ignores, plus the BADSKY
    # artifact mask used by the default plan.
    good = (ivar > 0) & np.isfinite(flux)
    try:
        from mangadap.proc.spatiallybinnedspectra import SpatiallyBinnedSpectraBitMask
        bm = SpatiallyBinnedSpectraBitMask()
        bad = bm.flagged(mask, flag=['DIDNOTUSE', 'FORESTAR', 'LOW_SPECCOV',
                                     'LOW_SNR', 'NONE_IN_STACK', 'IVARINVALID'])
        good &= ~bad
    except Exception:
        bad = np.zeros_like(mask, dtype=bool)
    try:
        from mangadap.par.artifactdb import ArtifactDB
        from mangadap.util.pixelmask import SpectralPixelMask
        pm = SpectralPixelMask(artdb=ArtifactDB.from_key('BADSKY'))
        badsky = pm.boolean(wave, nspec=1)[0]
        good &= ~badsky[None, :]
    except Exception:
        badsky = np.zeros_like(wave, dtype=bool)
    ferr[good] = 1.0 / np.sqrt(ivar[good])
    return {"wave": wave, "flux": flux, "ivar": ivar, "mask": mask,
            "sres": sres, "binid_map": binid_map, "bins": bins,
            "badsky": badsky,
            "cflux": cflux, "ckin": ckin, "ferr": ferr, "good": good,
            "bsp_path": str(bsp_path), "cont_path": str(cont_path)}


# ---------------------------------------------------------------------------
# worker
# ---------------------------------------------------------------------------
def _worker_init():
    # Nothing to do: fork inherits the _G payload.  Kept as an initializer hook
    # so the pool is explicit about its setup.
    return None


def _fit_one(index: int, return_model: bool = False) -> dict:
    from mangadap.proc.sasuke import Sasuke
    from mangadap.proc.emissionlinemodel import EmissionLineModelBitMask

    g = _G
    wave = g["wave"]
    flux = g["flux"][index]
    ferr = g["ferr"][index]
    good = g["good"][index]
    if not np.any(good):
        return {"index": index, "ok": False, "error": "no good pixels"}
    obj_flux = np.ma.array(flux[None, :], mask=~good[None, :])
    obj_ferr = np.ma.array(ferr[None, :], mask=~good[None, :])
    ckin = g["ckin"][index:index + 1]
    try:
        sasuke = Sasuke(EmissionLineModelBitMask())
        # The pPXF continuum model is in the observed frame.  Shift its
        # wavelength vector back to the rest frame and give Sasuke the fitted
        # stellar cz; Sasuke then shifts the template forward by the same
        # amount.  This one-to-one mapping is what makes the fixed-continuum
        # fit equivalent to the survey continuum subtraction.
        z_star = float(ckin[0, 0] / C_KMS)
        tpl_wave = wave / (1.0 + z_star)
        tpl_sres = np.interp(tpl_wave, wave, np.asarray(g["sres"][index], dtype=float))
        out = sasuke.fit(
            g["emldb"], wave, obj_flux, obj_ferr=obj_ferr,
            obj_mask=~good[None, :],
            obj_sres=g["sres"][index],
            guess_redshift=ckin[:, 0] / C_KMS,
            guess_dispersion=ckin[:, 1],
            reject_boxcar=int(g["reject_boxcar"]),
            stpl_wave=tpl_wave,
            stpl_flux=g["cflux"][index:index + 1],
            stpl_sres=tpl_sres,
            stpl_to_use=np.ones((1, 1), dtype=bool),
            stellar_kinematics=ckin,
            etpl_sinst_mode="offset",
            etpl_sinst_min=10.0,
            velscale_ratio=1,
            degree=-1,
            mdegree=int(g["mdegree"]),
            ppxf_faults="flag",
            quiet=True,
            ensemble=False,
        )
        model_wave, model_flux, model_eml_flux, model_mask, fitpar, emlpar = out
        fl = np.asarray(emlpar["FLUX"][0], dtype=float)
        fe = np.asarray(emlpar["FLUXERR"][0], dtype=float)
        kin = np.asarray(emlpar["KIN"][0], dtype=float)
        kine = np.asarray(emlpar["KINERR"][0], dtype=float)
        emask = np.asarray(emlpar["MASK"][0], dtype=np.int32).copy()
        # Use all finite positive measurements in the science maps.  The
        # original SASUKE quality mask is retained separately so a user can
        # reject NEAR_BOUND/FITFAILED flags if desired.
        ok = np.isfinite(fl) & np.isfinite(fe) & (fe > 0)
        # The DAP measures EWs separately from the Gaussian fit because it can
        # use the observed spectrum and the local sidebands.  Use the official
        # helper with the NSA redshift (not the fitted cz).
        from mangadap.proc.spectralfitting import EmissionLineFit
        from mangadap.proc.emissionlinemodel import EmissionLineModelBitMask
        try:
            EmissionLineFit.measure_equivalent_width(
                wave, np.ma.array(flux[None, :], mask=~good[None, :]),
                g["emldb"], emlpar,
                redshift=np.array([ckin[0, 0] / C_KMS]),
                bitmask=EmissionLineModelBitMask(), checkdb=False)
        except Exception:
            pass
        ew = np.asarray(emlpar["EW"][0], dtype=float)
        ewe = np.asarray(emlpar["EWERR"][0], dtype=float)
        # The kinematics are fitted as cz relative to the input guess; convert
        # to the DAP MAPS velocity zero point (relative to the NSA systemic z).
        kin[:, 0] -= g.get("sys_cz", 0.0)
        ok_ew = ok & np.isfinite(ew) & np.isfinite(ewe) & (ewe > 0)
        out = {
            "index": index, "ok": True, "error": "",
            "flux": fl.astype(np.float32), "fluxerr": fe.astype(np.float32),
            "kin": kin.astype(np.float32), "kinerr": kine.astype(np.float32),
            "ew": ew.astype(np.float32), "ewerr": ewe.astype(np.float32),
            "mask": np.where(ok, 0, 1).astype(np.int16),
            "sasuke_mask": emask.astype(np.int16),
            "ewmask": np.where(ok_ew, 0, 1).astype(np.int16),
        }
        if return_model:
            out["model_wave"] = np.asarray(model_wave, dtype=float)
            out["model_flux"] = np.asarray(model_flux[0], dtype=float)
            out["model_eml_flux"] = np.asarray(model_eml_flux[0], dtype=float)
            out["model_mask"] = np.asarray(model_mask[0], dtype=np.int32)
        return out
    except Exception as exc:  # noqa: BLE001
        return {"index": index, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _run_pool(nproc: int, nbin: int):
    if nproc <= 1:
        return [_fit_one(i) for i in range(nbin)]
    ctx = mp.get_context("fork")
    with ctx.Pool(processes=nproc, initializer=_worker_init) as pool:
        results = []
        t0 = time.perf_counter()
        for k, res in enumerate(pool.imap_unordered(_fit_one, range(nbin), chunksize=1), 1):
            results.append(res)
            if k % 10 == 0 or k == nbin:
                print(f"    fast SASUKE: {k}/{nbin} bins "
                      f"({time.perf_counter() - t0:.0f} s)", flush=True)
    results.sort(key=lambda r: r["index"])
    return results


# ---------------------------------------------------------------------------
# map construction
# ---------------------------------------------------------------------------
def _base_header(partial_maps: Path) -> tuple[fits.Header, list[str], fits.PrimaryHDU, list]:
    with fits.open(partial_maps, memmap=False) as hdul:
        pri = hdul[0].copy()
        hdr = hdul["EMLINE_GFLUX"].header.copy() if "EMLINE_GFLUX" in hdul else hdul["EMLINE_SFLUX"].header.copy()
        names = []
        for i in range(1, 200):
            key = f"C{i:02d}"
            if key not in hdr:
                break
            names.append(str(hdr[key]).strip())
        keep = []
        for hdu in hdul[1:]:
            if hdu.name in _DROP:
                continue
            keep.append(hdu.copy())
    for key in ("NAXIS", "NAXIS1", "NAXIS2", "NAXIS3", "EXTNAME", "BUNIT",
                "ERRDATA", "QUALDATA", "CHECKSUM", "DATASUM"):
        hdr.pop(key, None)
    return hdr, names, pri, keep


_DROP = {
    "EMLINE_GFLUX", "EMLINE_GFLUX_IVAR", "EMLINE_GFLUX_MASK",
    "EMLINE_GEW", "EMLINE_GEW_CNT", "EMLINE_GEW_IVAR", "EMLINE_GEW_MASK",
    "EMLINE_GVEL", "EMLINE_GVEL_IVAR", "EMLINE_GVEL_MASK",
    "EMLINE_GSIGMA", "EMLINE_GSIGMA_IVAR", "EMLINE_GSIGMA_MASK",
    "EMLINE_INSTSIGMA", "EMLINE_TPLSIGMA", "EMLINE_GA", "EMLINE_GANR",
    "EMLINE_FOM", "EMLINE_LFOM",
}


def _wcs_header(hdr: fits.Header) -> fits.Header:
    """Return a 3D map header with the WCS from the partial MAPS."""
    out = WCS(hdr, naxis=3).to_header(relax=True)
    return out


def build_maps(partial_maps: Path, binned: dict, results: list[dict],
               out_maps: Path, metadata: dict) -> dict:
    nbin = len(results)
    neml = int(_G["emldb"].size)
    shape = (neml,) + binned["binid_map"].shape
    gflux = np.full(shape, np.nan, dtype=np.float32)
    gflux_ivar = np.zeros(shape, dtype=np.float32)
    gflux_mask = np.ones(shape, dtype=np.int16)
    gew = np.full(shape, np.nan, dtype=np.float32)
    gew_ivar = np.zeros(shape, dtype=np.float32)
    gew_mask = np.ones(shape, dtype=np.int16)
    gvel = np.full(shape, np.nan, dtype=np.float32)
    gvel_ivar = np.zeros(shape, dtype=np.float32)
    gvel_mask = np.ones(shape, dtype=np.int16)
    gsig = np.full(shape, np.nan, dtype=np.float32)
    gsig_ivar = np.zeros(shape, dtype=np.float32)
    gsig_mask = np.ones(shape, dtype=np.int16)
    sasuke_mask = np.zeros(shape, dtype=np.int16)
    binid_map = binned["binid_map"]
    bin_ids = binned["bins"]["BINID"].astype(int)
    nfail = 0
    for res in results:
        i = res["index"]
        if not res["ok"]:
            nfail += 1
            continue
        sel = binid_map == bin_ids[i]
        if not np.any(sel):
            nfail += 1
            continue
        fl = res["flux"]
        fe = res["fluxerr"]
        ok = res["mask"] == 0
        gflux[:, sel] = fl[:, None]
        gflux_ivar[:, sel] = np.where(ok, 1.0 / np.square(fe), 0.0)[:, None]
        gflux_mask[:, sel] = np.where(ok, 0, 1)[:, None]
        gew[:, sel] = res["ew"][:, None]
        gew_ivar[:, sel] = np.divide(1.0, np.square(res["ewerr"]),
                                     out=np.zeros_like(res["ewerr"]),
                                     where=ok & (res["ewerr"] > 0))[:, None]
        ew_ok = res.get("ewmask", np.where(ok, 0, 1)) == 0
        gew_mask[:, sel] = np.where(ew_ok, 0, 1)[:, None]
        for arr, ivar, mask, vals, errs in (
                (gvel, gvel_ivar, gvel_mask, res["kin"][:, 0], res["kinerr"][:, 0]),
                (gsig, gsig_ivar, gsig_mask, res["kin"][:, 1], res["kinerr"][:, 1])):
            arr[:, sel] = vals[:, None]
            ivar[:, sel] = np.divide(1.0, np.square(errs), out=np.zeros_like(errs),
                                     where=ok & (errs > 0))[:, None]
            mask[:, sel] = np.where(ok, 0, 1)[:, None]
        sasuke_mask[:, sel] = res.get("sasuke_mask", np.zeros(neml, dtype=np.int16))[:, None]

    hdr, names, pri, keep = _base_header(partial_maps)
    if len(names) != neml:
        raise ValueError(f"line-name count mismatch: MAPS={len(names)}, fit={neml}")
    wcs = _wcs_header(hdr)
    # Update primary provenance.
    pri.header["DAPMODE"] = ("FASTCONT", "Fixed-continuum SASUKE fit on DAP bins")
    pri.header["DAPPIPE"] = ("sdss-mangadap 4.5.0 Sasuke; fixed pPXF continuum",
                             "emission-line fit mode")
    pri.header["DAPNOTE"] = (metadata.get("note", ""), "fast-mode note")
    pri.header["BINFIT"] = (int(nbin), "number of DAP bins fitted")
    pri.header["BINFAIL"] = (int(nfail), "number of bins without a valid fit")
    pri.header["MDFIT"] = (int(_G["mdegree"]), "pPXF multiplicative polynomial order")
    pri.header["ENSEMBLE"] = ("F", "Sasuke ensemble mode (one spectrum per fit)")
    pri.header["ELINES"] = (int(neml), "number of emission-line channels")

    def hdu(name, data, unit, desc, extra=None):
        h = wcs.copy()
        h["BUNIT"] = (unit, "data unit")
        h["DESCR"] = (desc, "product description")
        # The per-channel line labels are required by the DAP MAPS data model.
        for i, line_name in enumerate(names, 1):
            h[f"C{i:02d}"] = (line_name, f"Data in channel {i}")
        if extra:
            for k, v in extra.items():
                h[k] = v
        return fits.ImageHDU(data=data, header=h, name=name)

    new = [
        hdu("EMLINE_GFLUX", gflux, "1E-17 erg/s/cm^2/spaxel",
            "SASUKE Gaussian line flux",
            {"ERRDATA": "EMLINE_GFLUX_IVAR", "QUALDATA": "EMLINE_GFLUX_MASK"}),
        hdu("EMLINE_GFLUX_IVAR", gflux_ivar, "(1E-17 erg/s/cm^2/spaxel)^-2",
            "inverse variance of EMLINE_GFLUX",
            {"ERRDATA": "EMLINE_GFLUX"}),
        hdu("EMLINE_GFLUX_MASK", gflux_mask, "", "0 = valid, 1 = no fit",
            {"QUALDATA": "EMLINE_GFLUX"}),
        hdu("EMLINE_GEW", gew, "ang", "SASUKE Gaussian equivalent width",
            {"ERRDATA": "EMLINE_GEW_IVAR", "QUALDATA": "EMLINE_GEW_MASK"}),
        hdu("EMLINE_GEW_IVAR", gew_ivar, "ang^-2", "inverse variance of EMLINE_GEW",
            {"ERRDATA": "EMLINE_GEW"}),
        hdu("EMLINE_GEW_MASK", gew_mask, "", "0 = valid, 1 = no fit",
            {"QUALDATA": "EMLINE_GEW"}),
        hdu("EMLINE_GVEL", gvel, "km/s", "SASUKE Gaussian line velocity",
            {"ERRDATA": "EMLINE_GVEL_IVAR", "QUALDATA": "EMLINE_GVEL_MASK"}),
        hdu("EMLINE_GVEL_IVAR", gvel_ivar, "(km/s)^-2", "inverse variance of EMLINE_GVEL",
            {"ERRDATA": "EMLINE_GVEL"}),
        hdu("EMLINE_GVEL_MASK", gvel_mask, "", "0 = valid, 1 = no fit",
            {"QUALDATA": "EMLINE_GVEL"}),
        hdu("EMLINE_GSIGMA", gsig, "km/s", "SASUKE Gaussian line velocity dispersion",
            {"ERRDATA": "EMLINE_GSIGMA_IVAR", "QUALDATA": "EMLINE_GSIGMA_MASK"}),
        hdu("EMLINE_GSIGMA_IVAR", gsig_ivar, "(km/s)^-2", "inverse variance of EMLINE_GSIGMA",
            {"ERRDATA": "EMLINE_GSIGMA"}),
        hdu("EMLINE_GSIGMA_MASK", gsig_mask, "", "0 = valid, 1 = no fit",
            {"QUALDATA": "EMLINE_GSIGMA"}),
        hdu("SASUKE_MASK", sasuke_mask, "", "original SASUKE fit quality bitmask"),
    ]
    hdul = fits.HDUList([pri, *keep, *new])
    hdul.writeto(out_maps, overwrite=True)
    return {"n_bins": nbin, "n_fail": nfail, "n_lines": neml,
            "maps": str(out_maps), "names": names}


def run_fast_eline(dap_root: Path, plate: int, ifu: int, config: dict,
                   out: Path, nproc: int | None = None,
                   mdegree: int | None = None) -> dict:
    from mangadap.par.emissionlinedb import EmissionLineDB

    t0 = time.perf_counter()
    bsp_path, cont_path = find_binned_products(dap_root, plate, ifu)
    binned = load_binned(bsp_path, cont_path)
    nbin = binned["flux"].shape[0]
    emldb = EmissionLineDB.from_key(config["emission_line_fit"]["line_database"])
    nproc = int(nproc or os.environ.get("MANGA_DAP_NPROC", min(8, os.cpu_count() or 1)))
    mdegree = int(mdegree if mdegree is not None else
                  config.get("fast_eline", {}).get("mdegree", 14))
    _G.clear()
    _G.update({"wave": binned["wave"], "flux": binned["flux"], "ferr": binned["ferr"],
               "good": binned["good"], "sres": binned["sres"], "cflux": binned["cflux"],
               "ckin": binned["ckin"], "emldb": emldb, "mdegree": mdegree,
               "sys_cz": C_KMS * float(config["metadata"]["z"]),
               "reject_boxcar": config["emission_line_fit"].get("reject_boxcar", 101)})
    print(f"  fast fixed-continuum SASUKE: {nbin} bins, {nproc} processes, "
          f"mdegree={mdegree}, lines={emldb.size}")
    results = _run_pool(nproc, nbin)
    elapsed = time.perf_counter() - t0
    nfail = sum(not r["ok"] for r in results)
    print(f"  fast SASUKE done: {nbin} bins, {nfail} failures, {elapsed:.1f} s")

    # Per-bin table.
    rows = []
    names = list(emldb.data["name"])
    key = {name: i for i, name in enumerate(names)}
    for res in results:
        i = res["index"]
        row = {"bin_index": i, "binid": int(binned["bins"]["BINID"][i]),
               "nspax": int(binned["bins"]["NBIN"][i]),
               "snr": float(binned["bins"]["SNR"][i]),
               "ok": res["ok"], "error": res.get("error", "")}
        if res["ok"]:
            for line in ("Ha", "Hb", "OIII", "NII", "SII"):
                if line in key:
                    j = key[line]
                    row[f"{line}_flux"] = float(res["flux"][j])
                    row[f"{line}_fluxerr"] = float(res["fluxerr"][j])
                    row[f"{line}_vel"] = float(res["kin"][j, 0])
                    row[f"{line}_sigma"] = float(res["kin"][j, 1])
        rows.append(row)
    with (out / "fast_eline_bins.csv").open("w", newline="") as fh:
        fields = ["bin_index", "binid", "nspax", "snr", "ok", "error",
                  "Ha_flux", "Ha_fluxerr", "Ha_vel", "Ha_sigma",
                  "Hb_flux", "Hb_fluxerr", "Hb_vel", "Hb_sigma",
                  "OIII_flux", "OIII_fluxerr", "OIII_vel", "OIII_sigma",
                  "NII_flux", "NII_fluxerr", "NII_vel", "NII_sigma",
                  "SII_flux", "SII_fluxerr", "SII_vel", "SII_sigma"]
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    partial = dap_root / config["dap"]["daptype"] / str(plate) / str(ifu) / \
        f"manga-{plate}-{ifu}-MAPS-{config['dap']['daptype']}.fits.gz"
    # The partial MAPS is the moments-only product; locate it robustly.
    if not partial.exists():
        hits = sorted((dap_root / config["dap"]["daptype"] / str(plate) / str(ifu)).glob("*MAPS*.fits.gz"))
        if not hits:
            raise FileNotFoundError("moments-only MAPS not found")
        partial = hits[0]
    meta = build_maps(partial, binned, results, out / "fits" / "manga_dap_maps.fits.gz",
                      {"note": config.get("fast_eline", {}).get(
                          "note", "Official Sasuke fit on official DAP bins with fixed pPXF continuum")})
    meta.update({"runtime_seconds": elapsed, "nproc": nproc, "mdegree": mdegree,
                 "bsp": str(bsp_path), "continuum": str(cont_path),
                 "n_fail": nfail, "partial_maps": str(partial)})
    return meta


def central_model(bsp_path: Path, cont_path: Path, bin_id: int,
                  config: dict) -> dict:
    """Re-fit one bin and return the model spectra for a pedagogical figure."""
    from mangadap.par.emissionlinedb import EmissionLineDB
    binned = load_binned(Path(bsp_path), Path(cont_path))
    idx = int(np.where(binned["bins"]["BINID"].astype(int) == bin_id)[0][0])
    _G.clear()
    _G.update({"wave": binned["wave"], "flux": binned["flux"], "ferr": binned["ferr"],
               "good": binned["good"], "sres": binned["sres"], "cflux": binned["cflux"],
               "ckin": binned["ckin"],
               "emldb": EmissionLineDB.from_key(config["emission_line_fit"]["line_database"]),
               "mdegree": int(config.get("fast_eline", {}).get("mdegree", 14)),
               "sys_cz": C_KMS * float(config["metadata"]["z"]),
               "reject_boxcar": config["emission_line_fit"].get("reject_boxcar", 101)})
    res = _fit_one(idx, return_model=True)
    res["bin_index"] = idx
    res["binid"] = int(binned["bins"]["BINID"][idx])
    res["nspax"] = int(binned["bins"]["NBIN"][idx])
    # The binned spectrum is the actual data fitted by the DAP, and it has
    # already been corrected for Galactic extinction.  The raw LOGCUBE spectrum
    # is not dereddened, so use the binned spectrum for the pedagogical fit
    # figure to keep data and model on the same photometric scale.
    res["obs_wave"] = binned["wave"]
    res["obs_flux"] = binned["flux"][idx]
    res["obs_ferr"] = binned["ferr"][idx]
    res["obs_good"] = binned["good"][idx]
    return res
