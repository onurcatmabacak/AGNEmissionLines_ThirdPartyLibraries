"""Spectrum ingestion and the canonical in-memory representation.

For the first slice the flux unit is ``1e-17 erg s-1 cm-2 A-1`` (the eFEDS/BOSS
COADD convention used by the optical pipeline).  Adapters record the native
unit and convert explicitly; the fitter never guesses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import warnings

import numpy as np

C_KMS = 299792.458


@dataclass
class Spectrum:
    wave_um: np.ndarray          # observed-frame vacuum wavelength, micron
    flux: np.ndarray             # 1e-17 erg s-1 cm-2 A-1
    error: np.ndarray            # same unit
    mask: np.ndarray             # True = good
    z: float
    z_err: float = np.nan
    band: str = "optical"
    instrument: str = ""
    object_id: str = ""
    flux_unit: str = "1e-17 erg s-1 cm-2 A-1"
    native_flux_unit: str = ""
    ra: float = np.nan
    dec: float = np.nan
    meta: dict = field(default_factory=dict)

    @property
    def wave_min(self) -> float:
        return float(np.nanmin(self.wave_um[self.mask])) if self.mask.any() else float(np.nanmin(self.wave_um))

    @property
    def wave_max(self) -> float:
        return float(np.nanmax(self.wave_um[self.mask])) if self.mask.any() else float(np.nanmax(self.wave_um))

    def rest_wave(self) -> np.ndarray:
        return self.wave_um / (1.0 + self.z)

    def at_rest(self, rest_um: float) -> float:
        return rest_um * (1.0 + self.z)


def _get_table(hdul):
    for name in ("COADD", "SPECTRUM", "FLUX"):
        if name in hdul:
            return hdul[name]
    for hdu in hdul:
        if getattr(hdu, "columns", None) is not None:
            names = {c.lower() for c in hdu.columns.names}
            if "flux" in names and ({"loglam", "wave", "wl"} & names):
                return hdu
    raise ValueError("no spectrum table (need FLUX + LOGLAM/WL)")


def _col(data, *names):
    for n in names:
        if n in data.columns.names:
            return np.asarray(data[n], dtype=float)
    return None


def read_sdss(path: str | Path, z_override: float | None = None,
              band: str | None = None) -> Spectrum:
    """Read an SDSS DR18 eFEDS/BOSS COADD (or a generic SDSS-style FITS)."""
    from astropy.io import fits

    path = Path(path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fits.open(path, memmap=False) as hdul:
            tab = _get_table(hdul)
            d = tab.data
            flux = _col(d, "FLUX", "flux")
            loglam = _col(d, "LOGLAM", "loglam")
            wl = _col(d, "WAVE", "wave", "WL", "wl")
            ivar = _col(d, "IVAR", "ivar")
            ormask = _col(d, "OR_MASK", "OR_MASK")
            if flux is None:
                raise ValueError("no FLUX column")
            if loglam is not None:
                wave_um = 10.0 ** loglam / 1e4          # Angstrom -> micron
            elif wl is not None:
                # assume Angstrom if the median is > 10, else micron
                wave_um = np.asarray(wl, float)
                if np.nanmedian(wave_um) > 10.0:
                    wave_um = wave_um / 1e4
            else:
                raise ValueError("no LOGLAM/WL column")

            if ivar is not None:
                good_ivar = np.isfinite(ivar) & (ivar > 0)
                err = np.full_like(flux, np.nan)
                err[good_ivar] = 1.0 / np.sqrt(ivar[good_ivar])
            else:
                err = np.full_like(flux, np.nan)
                good_ivar = np.ones_like(flux, dtype=bool)

            # ivar/finite masking by default; OR_MASK is retained as metadata
            # (the optical pipeline also ignores it: it flags ~50 % of pixels).
            mask = np.isfinite(flux) & np.isfinite(err) & good_ivar & (err > 0)
            ormask_frac = float(np.mean(ormask != 0)) if ormask is not None else 0.0

            z = np.nan
            zerr = np.nan
            objclass = ""
            subclass = ""
            instrument = str(tab.header.get("INSTRUME", "") or "")
            ra = tab.header.get("PLUG_RA", np.nan)
            dec = tab.header.get("PLUG_DEC", np.nan)
            if "ZALL" in hdul and hdul["ZALL"].data is not None and len(hdul["ZALL"].data):
                zt = hdul["ZALL"].data
                z = float(zt["Z"][0])
                zerr = float(zt["Z_ERR"][0]) if "Z_ERR" in zt.columns.names else np.nan
                instrument = instrument or str(zt["OBJTYPE"][0] if "OBJTYPE" in zt.columns.names else "")
                objclass = str(zt["CLASS"][0]).strip() if "CLASS" in zt.columns.names else ""
                subclass = str(zt["SUBCLASS"][0]).strip() if "SUBCLASS" in zt.columns.names else ""
            if not np.isfinite(z):
                for key in ("Z", "REDSHIFT", "z"):
                    if key in tab.header:
                        z = float(tab.header[key])
                        break
            if not np.isfinite(z):
                for key in ("Z", "REDSHIFT"):
                    if key in hdul[0].header:
                        z = float(hdul[0].header[key])
                        break
            if z_override is not None:
                z = float(z_override)
            if not np.isfinite(z):
                z = 0.0

            objid = ""
            if "SPALL" in hdul and hdul["SPALL"].data is not None and len(hdul["SPALL"].data):
                sp = hdul["SPALL"].data
                if "OBJID" in sp.columns.names:
                    obj = np.atleast_1d(sp["OBJID"][0]).ravel()[0]
                    objid = str(int(obj))
            if objid in ("", "0"):
                objid = path.stem

    if band is None:
        band = _infer_band(wave_um, mask, instrument)
    return Spectrum(wave_um=np.asarray(wave_um, float), flux=np.asarray(flux, float) * 1.0,
                    error=np.asarray(err, float), mask=mask, z=z, z_err=zerr,
                    band=band, instrument=instrument, object_id=objid or path.stem,
                    native_flux_unit=str(tab.header.get("BUNIT", "")),
                    ra=ra, dec=dec,
                    meta={"path": str(path), "source": "SDSS DR18",
                          "ormask_frac": ormask_frac, "class": objclass,
                          "subclass": subclass})


def _infer_band(wave_um, mask, instrument: str) -> str:
    inst = (instrument or "").upper()
    if "APOGEE" in inst or "NIRSPEC" in inst or "NIRISS" in inst:
        return "nir"
    if "MIRI" in inst or "IRS" in inst or "MIPS" in inst:
        return "mir"
    if "PACS" in inst or "SPIRE" in inst or "ALMA" in inst or "GREAT" in inst or "FIFI" in inst:
        return "fir"
    w = wave_um[mask] if mask.any() else wave_um
    med = float(np.nanmedian(w))
    if med < 1.0:
        return "optical"
    if med < 5.0:
        return "nir"
    if med < 30.0:
        return "mir"
    return "fir"



def read_jwst_x1d(path: str | Path, z_override: float | None = None,
                  band: str | None = None) -> Spectrum:
    """JWST/NIRSpec (and NIRISS/MIRI) x1d EXTRACT1D table -> Spectrum.

    FLUX is in Jy; convert to the pipeline's 1e-17 erg s-1 cm-2 A-1.
    """
    from astropy.io import fits
    path = Path(path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fits.open(path, memmap=False) as hdul:
            tab = hdul["EXTRACT1D"]
            d = tab.data
            wave_um = np.asarray(d["WAVELENGTH"], float)
            flux_jy = np.asarray(d["FLUX"], float)
            err_jy = np.asarray(d["FLUX_ERROR"], float)
            dq = np.asarray(d["DQ"], float) if "DQ" in d.columns.names else np.zeros_like(wave_um)
            lam_a = wave_um * 1e4
            # Jy -> erg s-1 cm-2 A-1  (f_lambda = f_nu * c / lambda^2)
            conv = 1e-23 * 2.99792458e18 / np.where(lam_a > 0, lam_a ** 2, np.nan)
            flux = flux_jy * conv / 1e-17
            err = err_jy * conv / 1e-17
            hdr = hdul[0].header
            z = hdr.get("Z", hdr.get("REDSHIFT", np.nan))
            if not np.isfinite(z):
                z = 0.0
            if z_override is not None:
                z = float(z_override)
            target = str(hdr.get("TARGNAME", "") or path.stem).replace(" ", "_")
            inst = str(hdr.get("INSTRUME", "NIRSPEC"))
            objid = target
            ra = hdr.get("RA_REF", np.nan)
            dec = hdr.get("DEC_REF", np.nan)
    mask = np.isfinite(wave_um) & np.isfinite(flux) & np.isfinite(err) & (err > 0) & (dq == 0)
    if band is None:
        band = _infer_band(wave_um, mask, inst)
    return Spectrum(wave_um=wave_um, flux=flux, error=err, mask=mask, z=float(z),
                    z_err=float(hdr.get("Z_ERR", np.nan)) if "hdr" in locals() else np.nan,
                    band=band, instrument=inst, object_id=objid,
                    flux_unit="1e-17 erg s-1 cm-2 A-1", native_flux_unit="Jy",
                    ra=ra, dec=dec,
                    meta={"path": str(path), "source": "JWST x1d", "target": target,
                          "dq_flagged": int(np.sum(dq != 0))})


def read_spectrum(path: str | Path, **kw) -> Spectrum:
    """Adapter dispatch: JWST x1d if EXTRACT1D is present, else SDSS-style."""
    from astropy.io import fits
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fits.open(path, memmap=False) as hdul:
            names = [h.name for h in hdul]
    if "EXTRACT1D" in names:
        return read_jwst_x1d(path, **kw)
    return read_sdss(path, **kw)


def zline_table(path: str | Path):
    """SDSS ZLINE measurements (validation only)."""
    from astropy.io import fits
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fits.open(path, memmap=False) as hdul:
            if "ZLINE" not in hdul:
                return {}
            d = hdul["ZLINE"].data
            out = {}
            for i in range(len(d)):
                name = str(d["LINENAME"][i]).strip()
                out[name] = {
                    "wave": float(d["LINEWAVE"][i]),
                    "z": float(d["LINEZ"][i]),
                    "sigma_kms": float(d["LINESIGMA"][i]),
                    "area": float(d["LINEAREA"][i]),
                    "area_err": float(d["LINEAREA_ERR"][i]),
                    "ew": float(d["LINEEW"][i]),
                }
            return out
