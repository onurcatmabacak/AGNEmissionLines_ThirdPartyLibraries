#!/usr/bin/env python3
"""Convert raw eFEDS/SDSS spectra into the exact FITS layout each tool expects.

The six fitting tools disagree about how a spectrum should be stored.  This module
reads one raw spectrum (SDSS DR18 eFEDS ``lite``/``full`` FITS, or a classic SDSS
``spPlate``-style FITS) and emits a per-tool copy in that tool's native format:

    tool          file                                   flux unit      wavelength
    ------------  -------------------------------------  -------------  -------------
    sculptor      spectrum.fits                         1e-17 erg/...  loglam table
    pyqsofit      spectrum.fits                          erg/... (cgs)  HDU1 image
    badass        my_sdss.fits                           erg/... (cgs)  loglam table
    fantasy_agn   my_sdss.fits                           erg/... (cgs)  loglam table
    gelato        my_sdss.fits + my_sdss.json            erg/... (cgs)  loglam table
    gleam         spec1d.sdss.sdss.fiber1.1.fits        1e-17 erg/...  linear wl

The unit conventions above were reverse-engineered from the FITS files already in
this repository (see ``pipeline/README.md``), so the tools keep behaving the same
way they did for the original single-object analysis.

Usage
-----
    python pipeline/prepare_inputs.py --fits FILE_OR_DIR --out work
    python pipeline/prepare_inputs.py --fits ~/agn_data/efeds --out work --select 3
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import astropy.units as u
from astropy.io import fits

# eFEDS COADD flux is calibrated in 1e-17 erg cm-2 s-1 A-1 (SDSS convention).
EFEDS_FLUX_UNIT_CGS = 1e-17

def _get_table_hdu(hdul):
    """Return the HDU holding the spectrum (COADD for eFEDS, else the first table)."""
    try:
        return hdul["COADD"]
    except KeyError:
        pass
    for hdu in hdul:
        if getattr(hdu, "columns", None) is not None and hdu.data is not None:
            names = {c.lower() for c in hdu.columns.names}
            if {"flux", "loglam"} <= names or {"flux", "wl"} <= names:
                return hdu
    raise ValueError("Could not locate a spectrum HDU (need FLUX + LOGLAM/WL)")


def _col(table, *names):
    cols = {c.lower(): c for c in table.columns.names}
    for n in names:
        if n.lower() in cols:
            return np.asarray(table[cols[n.lower()]], dtype=np.float64)
    return None


def read_spectrum(path: Path) -> dict:
    """Read a raw spectrum, returning arrays and metadata in a tool-neutral dict."""
    with fits.open(path, memmap=False) as hdul:
        hdr0 = hdul[0].header
        tab = _get_table_hdu(hdul)
        data = tab.data

        flux = _col(data, "FLUX", "flux")
        loglam = _col(data, "LOGLAM", "loglam")
        wl = _col(data, "WL", "wl")
        if flux is None:
            raise ValueError(f"{path}: no FLUX column")
        if loglam is not None:
            wave = 10.0 ** loglam
        elif wl is not None:
            wave = wl
        else:
            raise ValueError(f"{path}: no LOGLAM/WL column")

        ivar = _col(data, "IVAR", "ivar")
        if ivar is None:
            stdev = _col(data, "STDEV", "stdev")
            ivar = 1.0 / np.square(stdev) if stdev is not None else np.ones_like(flux)
        wdisp = _col(data, "WDISP", "wdisp")
        if wdisp is None:
            wdisp = np.full_like(flux, np.median(np.diff(wave)))

        # Redshift + object metadata: prefer the SPALL catalog HDU, then headers.
        z = ra = dec = mjd = fiberid = plateid = catalogid = None
        try:
            spall = hdul["SPALL"].data
            z = float(spall["Z"][0])
            ra = float(spall["PLUG_RA"][0])
            dec = float(spall["PLUG_DEC"][0])
            mjd = int(spall["MJD"][0])
            fiberid = int(spall["FIBERID"][0])
            catalogid = int(spall["CATALOGID"][0])
        except (KeyError, IndexError, ValueError):
            pass

        def hget(*keys, default=None):
            for k in keys:
                if k in hdr0:
                    return hdr0[k]
            return default

        if z is None:
            z = float(hget("Z", "z", "REDSHIFT", default=0.0))
        if ra is None:
            ra = float(hget("PLUG_RA", "RA", default=0.0))
        if dec is None:
            dec = float(hget("PLUG_DEC", "DEC", default=0.0))
        if mjd is None:
            mjd = int(hget("MJD", "MJD-OBS", default=0))
        if fiberid is None:
            fiberid = int(hget("FIBERID", default=0))
        if plateid is None:
            plateid = int(hget("PLATEID", "PLATE", default=0))
        if catalogid is None:
            catalogid = int(hget("CATALOGID", default=0))

    return {
        "path": str(path),
        "wave": wave,
        "flux_1e17": flux,               # eFEDS/SDSS native 1e-17 units
        "ivar": ivar,
        "wdisp": wdisp,
        "z": z,
        "ra": ra,
        "dec": dec,
        "mjd": mjd,
        "fiberid": fiberid,
        "plateid": plateid,
        "catalogid": catalogid,
        "n_pix": int(flux.size),
    }


def _base_header(spec: dict, flux_note: str) -> fits.Header:
    h = fits.Header()
    h["PLUG_RA"] = spec["ra"]
    h["PLUG_DEC"] = spec["dec"]
    h["MJD"] = spec["mjd"]
    h["PLATEID"] = spec["plateid"]
    h["FIBERID"] = spec["fiberid"]
    h["CATID"] = spec["catalogid"]
    h["Z"] = spec["z"]
    h["BUNIT"] = flux_note
    h["COMMENT"] = f"Prepared by prepare_inputs.py from {Path(spec['path']).name}"
    return h


def write_sculptor(spec: dict, out: Path) -> Path:
    """SCULPTOR: SDSS-style table, flux already in 1e-17 units, header Z."""
    hdr = _base_header(spec, "1e-17 erg s-1 cm-2 Ang-1")
    cols = [
        fits.Column(name="flux", format="D", array=spec["flux_1e17"]),
        fits.Column(name="loglam", format="D", array=np.log10(spec["wave"])),
        fits.Column(name="ivar", format="D", array=spec["ivar"]),
    ]
    hdul = fits.HDUList([fits.PrimaryHDU(header=hdr), fits.BinTableHDU.from_columns(cols)])
    hdul.writeto(out, overwrite=True)
    return out


def write_pyqsofit(spec: dict, out: Path, fwhm: float = 2.5, ebv: float = 0.0) -> Path:
    """PyQSOFit: flux in HDU0 (absolute cgs), wavelength in HDU1; header z/fwhm/ebv."""
    hdr = _base_header(spec, "erg s-1 cm-2 Ang-1")
    hdr["z"] = spec["z"]
    hdr["fwhm"] = fwhm
    hdr["ebv"] = ebv
    flux_cgs = spec["flux_1e17"] * EFEDS_FLUX_UNIT_CGS
    hdul = fits.HDUList(
        [
            fits.PrimaryHDU(data=flux_cgs.astype(np.float64), header=hdr),
            fits.ImageHDU(data=spec["wave"].astype(np.float64), name="WAVELENGTH"),
        ]
    )
    hdul.writeto(out, overwrite=True)
    return out


def write_sdss_like(spec: dict, out: Path) -> Path:
    """BADASS3 / fantasy_agn / GELATO: flux/loglam/ivar/wdisp table + z table."""
    hdr = _base_header(spec, "erg s-1 cm-2 Ang-1")
    flux_cgs = spec["flux_1e17"] * EFEDS_FLUX_UNIT_CGS
    cols = [
        fits.Column(name="flux", format="E", array=flux_cgs.astype(np.float32)),
        fits.Column(name="loglam", format="E", array=np.log10(spec["wave"]).astype(np.float32)),
        fits.Column(name="ivar", format="E", array=spec["ivar"].astype(np.float32)),
        fits.Column(name="wdisp", format="E", array=spec["wdisp"].astype(np.float32)),
    ]
    zcol = fits.Column(name="z", format="E", array=np.array([spec["z"]], dtype=np.float32))
    hdul = fits.HDUList(
        [
            fits.PrimaryHDU(header=hdr),
            fits.BinTableHDU.from_columns(cols),
            fits.BinTableHDU.from_columns([zcol]),
        ]
    )
    hdul.writeto(out, overwrite=True)
    return out


def write_gleam(spec: dict, out: Path) -> Path:
    """GLEAM: linear wavelength, flux in 1e-17 units, HDU2 column 'redshift'.

    GLEAM reads the wavelength/flux units from the FITS column TUNIT, so both
    columns are written as astropy Quantities (matching the reference file).
    """
    hdr = _base_header(spec, "1e-17 erg s-1 cm-2 Ang-1")
    cols = [
        fits.Column(name="flux", format="E", unit="erg / (s cm2 Angstrom)", array=spec["flux_1e17"].astype(np.float32)),
        fits.Column(name="wl", format="E", unit="Angstrom", array=spec["wave"].astype(np.float32)),
        # GLEAM's reference SDSS file uses a constant unit error and constant
        # dispersion; the instrument resolution is set in gleamconfig.yaml.
        fits.Column(name="stdev", format="E", array=np.ones_like(spec["wave"], dtype=np.float32)),
        fits.Column(name="wdisp", format="E", array=np.full_like(spec["wave"], 1e-4, dtype=np.float32)),
    ]
    zcol = fits.Column(name="redshift", format="E", array=np.array([spec["z"]], dtype=np.float32))
    hdul = fits.HDUList(
        [
            fits.PrimaryHDU(header=hdr),
            fits.BinTableHDU.from_columns(cols),
            fits.BinTableHDU.from_columns([zcol]),
        ]
    )
    hdul.writeto(out, overwrite=True)
    return out


def gleam_meta(spec: dict) -> str:
    return "# Sample    Setup    Pointing    SourceNumber    Redshift\n" \
           f"sdss       sdss     fiber1      1               {spec['z']:.6f}\n"


def gelato_json(template: Path, spec: dict) -> str:
    """Load the project's GELATO JSON template and inject the object redshift."""
    import json as _json

    cfg = _json.loads(template.read_text())
    cfg["OutFolder"] = "/app/output"
    return _json.dumps(cfg, indent=4)


GLEAM_STATIC = ("line_table.fits", "Sky_bands.fits", "gleamconfig.yaml")


def stage_gleam_static(obj_dir: Path, source_dir: Path) -> None:
    """Copy GLEAM's static config/line tables next to the prepared spectrum."""
    dest = obj_dir / "inputs" / "gleam"
    for name in GLEAM_STATIC:
        src = source_dir / name
        if src.exists():
            shutil.copy2(src, dest / name)


def prepare_one(src: Path, runs: Path, *, fwhm: float = 2.5, ebv: float = 0.0,
                templates: dict | None = None, gleam_static: Path | None = None) -> dict:
    """Prepare all tool inputs for a single raw spectrum; return metadata.

    Layout created::

        runs/<tag>/inputs/<tool>/...     prepared native inputs
        runs/<tag>/outputs/<tool>/       empty, filled by the tool run
        runs/<tag>/manifest.json
    """
    spec = read_spectrum(src)
    tag = f"{spec['catalogid']:011d}" if spec["catalogid"] else src.stem
    obj_dir = runs / tag
    all_tools = ("sculptor", "pyqsofit", "badass", "fantasy_agn", "gelato", "gleam")
    for t in all_tools:
        (obj_dir / "inputs" / t).mkdir(parents=True, exist_ok=True)
        (obj_dir / "outputs" / t).mkdir(parents=True, exist_ok=True)
    inputs = {}

    def mk(tool):
        return obj_dir / "inputs" / tool

    inputs["sculptor"] = str(write_sculptor(spec, mk("sculptor") / "spectrum.fits"))
    inputs["pyqsofit"] = str(write_pyqsofit(spec, mk("pyqsofit") / "spectrum.fits", fwhm=fwhm, ebv=ebv))
    for tool in ("badass", "fantasy_agn", "gelato"):
        inputs[tool] = str(write_sdss_like(spec, mk(tool) / "my_sdss.fits"))
    inputs["gleam"] = str(write_gleam(spec, mk("gleam") / "spec1d.sdss.sdss.fiber1.1.fits"))

    # gleam needs the object redshift in meta.dat next to the spectrum
    (obj_dir / "inputs" / "gleam" / "meta.dat").write_text(gleam_meta(spec))
    if gleam_static is not None:
        stage_gleam_static(obj_dir, gleam_static)

    # gelato needs its JSON template copied next to the FITS
    if templates and templates.get("gelato_json"):
        j = gelato_json(Path(templates["gelato_json"]), spec)
        (obj_dir / "inputs" / "gelato" / "my_sdss.json").write_text(j)

    manifest = {
        "source": str(src),
        "tag": tag,
        "catalogid": spec["catalogid"],
        "z": spec["z"],
        "ra": spec["ra"],
        "dec": spec["dec"],
        "mjd": spec["mjd"],
        "fiberid": spec["fiberid"],
        "n_pix": spec["n_pix"],
        "wave_min": float(np.min(spec["wave"])),
        "wave_max": float(np.max(spec["wave"])),
        "inputs": inputs,
        "outputs": {t: str(obj_dir / "outputs" / t) for t in all_tools},
    }
    obj_dir.mkdir(parents=True, exist_ok=True)
    (obj_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def discover(fits_arg: Path) -> list[Path]:
    if fits_arg.is_dir():
        return sorted(fits_arg.glob("*.fits"))
    return [fits_arg]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fits", required=True, type=Path, help="a .fits file or a directory of them")
    p.add_argument("--out", type=Path, default=Path("runs"), help="runs directory (default: runs)")
    p.add_argument("--select", type=int, default=None, help="only prepare the first N spectra")
    p.add_argument("--fwhm", type=float, default=2.5, help="PyQSOFit header fwhm (Angstrom)")
    p.add_argument("--ebv", type=float, default=0.0, help="PyQSOFit header ebv")
    p.add_argument("--gelato-json", type=Path, default=Path("Gelato/my_sdss.json"),
                   help="GELATO JSON template to copy per object")
    p.add_argument("--gleam-static", type=Path, default=Path("Gleam"),
                   help="directory holding GLEAM's line_table.fits/Sky_bands.fits/gleamconfig.yaml")
    args = p.parse_args(argv)

    files = discover(args.fits)
    if args.select:
        files = files[: args.select]
    if not files:
        print(f"No .fits files found in {args.fits}")
        return 1

    templates = {"gelato_json": str(args.gelato_json)} if args.gelato_json.exists() else {}
    gleam_static = args.gleam_static if args.gleam_static.exists() else None
    for src in files:
        m = prepare_one(src, args.out, fwhm=args.fwhm, ebv=args.ebv, templates=templates,
                        gleam_static=gleam_static)
        print(f"[prepared] {m['tag']}  z={m['z']:.4f}  npix={m['n_pix']}  -> {args.out / m['tag']}")
    print(f"Prepared {len(files)} object(s) under {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
