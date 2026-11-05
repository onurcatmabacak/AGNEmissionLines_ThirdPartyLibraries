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
    """JWST/NIRSpec or MIRI x1d EXTRACT1D table -> Spectrum.

    NIRSpec x1d uses FLUX/FLUX_ERROR in Jy.  MIRI x1d uses
    SURF_BRIGHT/SB_ERROR in MJy/sr.  The native unit is retained in the
    Spectrum; the generic fitter does not assume a physical unit.
    """
    from astropy.io import fits
    path = Path(path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fits.open(path, memmap=False) as hdul:
            tab = hdul["EXTRACT1D"]
            d = tab.data
            names = set(d.columns.names)
            wave_um = np.asarray(d["WAVELENGTH"], float)
            if "FLUX" in names:
                native = np.asarray(d["FLUX"], float)
                native_err = np.asarray(d["FLUX_ERROR"], float)
                native_unit = "Jy"
                lam_a = wave_um * 1e4
                conv = 1e-23 * 2.99792458e18 / np.where(lam_a > 0, lam_a ** 2, np.nan)
                flux = native * conv / 1e-17
                err = native_err * conv / 1e-17
                flux_unit = "1e-17 erg s-1 cm-2 A-1"
            elif "SURF_BRIGHT" in names:
                native = np.asarray(d["SURF_BRIGHT"], float)
                native_err = np.asarray(d["SB_ERROR"], float)
                native_unit = str(tab.header.get("TUNIT2", "MJy/sr"))
                flux, err = native, native_err
                flux_unit = native_unit
            else:
                raise ValueError(f"EXTRACT1D has neither FLUX nor SURF_BRIGHT: {sorted(names)}")
            dq = np.asarray(d["DQ"], float) if "DQ" in names else np.zeros_like(wave_um)
            hdr = hdul[0].header
            z = hdr.get("Z", hdr.get("REDSHIFT", np.nan))
            if not np.isfinite(z):
                z = 0.0
            if z_override is not None:
                z = float(z_override)
            target = str(hdr.get("TARGNAME", "") or path.stem).replace(" ", "_")
            inst = str(hdr.get("INSTRUME", "NIRSPEC"))
            ra = hdr.get("RA_REF", np.nan)
            dec = hdr.get("DEC_REF", np.nan)
    mask = np.isfinite(wave_um) & np.isfinite(flux) & np.isfinite(err) & (err > 0) & (dq == 0)
    if band is None:
        band = _infer_band(wave_um, mask, inst)
    return Spectrum(wave_um=wave_um, flux=flux, error=err, mask=mask, z=float(z),
                    z_err=float(hdr.get("Z_ERR", np.nan)),
                    band=band, instrument=inst, object_id=target,
                    flux_unit=flux_unit, native_flux_unit=native_unit,
                    ra=ra, dec=dec,
                    meta={"path": str(path), "source": "JWST x1d", "target": target,
                          "dq_flagged": int(np.sum(dq != 0))})


def _robust_scalar_error(y: np.ndarray) -> float:
    """Noise estimate for spectra without an error column."""
    y = np.asarray(y, float)
    d = np.diff(y[np.isfinite(y)])
    if d.size < 5:
        return float("nan")
    mad = np.nanmedian(np.abs(d - np.nanmedian(d)))
    val = 1.4826 * mad / np.sqrt(2.0)
    return float(val) if np.isfinite(val) and val > 0 else float("nan")


def read_hifi_hpdp(path: str | Path, z_override: float | None = None,
                   band: str | None = None) -> Spectrum:
    """Herschel/HIFI HPDP spectrum (flux [K], wave [GHz]) -> Spectrum.

    The HPDP products store antenna temperature in K and frequency in GHz.  We
    retain that native unit and fit the line shape; absolute line fluxes require
    the HIFI beam/Jy-K calibration, which is deliberately not invented here.
    """
    from astropy.io import fits
    path = Path(path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fits.open(path, memmap=False) as hdul:
            tab = None
            for hdu in hdul:
                if getattr(hdu, "columns", None) is not None:
                    names = {c.lower() for c in hdu.columns.names}
                    if {"flux", "wave"} <= names:
                        tab = hdu
                        break
            if tab is None:
                raise ValueError("HIFI FITS has no FLUX/WAVE table")
            d = tab.data
            cols = {c.lower(): c for c in d.columns.names}
            flux_k = np.asarray(d[cols["flux"]], float)
            freq_ghz = np.asarray(d[cols["wave"]], float)
            hdr = hdul[0].header
            obj = str(hdr.get("OBJECT", path.stem)).strip().replace(" ", "_")
            inst = str(hdr.get("INSTRUME", "HIFI"))
            ra = hdr.get("RA", np.nan)
            dec = hdr.get("DEC", np.nan)
    wave_um = 299792.458 / np.where(freq_ghz > 0, freq_ghz, np.nan)
    noise = _robust_scalar_error(flux_k)
    err = np.full_like(flux_k, noise if np.isfinite(noise) else np.nan)
    mask = np.isfinite(wave_um) & np.isfinite(flux_k) & np.isfinite(err) & (err > 0)
    z = 0.0 if z_override is None else float(z_override)
    return Spectrum(wave_um=wave_um, flux=flux_k, error=err, mask=mask, z=z,
                    band=band or "fir", instrument=inst, object_id=obj,
                    flux_unit="K (antenna temperature)", native_flux_unit="K",
                    ra=ra, dec=dec,
                    meta={"path": str(path), "source": "Herschel/HIFI HPDP",
                          "noise_estimate_K": noise})


def read_s1d(path: str | Path, z_override: float | None = None,
             band: str | None = None) -> Spectrum:
    """PAHFIT/MIRI MRS s1d table (wavelength, flux, uncertainty)."""
    from astropy.io import fits
    path = Path(path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fits.open(path, memmap=False) as hdul:
            tab = hdul[1] if len(hdul) > 1 else hdul[0]
            d = tab.data
            cols = {c.lower(): c for c in d.columns.names}
            w = np.asarray(d[cols["wavelength"]], float)
            f = np.asarray(d[cols["flux"]], float)
            e = np.asarray(d[cols.get("uncertainty", "error")], float)
            hdr = hdul[0].header
            obj = str(hdr.get("OBJECT", path.stem)).strip().replace(" ", "_")
            ra = hdr.get("RA", np.nan)
            dec = hdr.get("DEC", np.nan)
    # PAHFIT s1d wavelengths are microns.
    mask = np.isfinite(w) & np.isfinite(f) & np.isfinite(e) & (e > 0)
    z = 0.0 if z_override is None else float(z_override)
    return Spectrum(wave_um=w, flux=f, error=e, mask=mask, z=z,
                    band=band or "mir", instrument="MIRI MRS (s1d)",
                    object_id=obj, flux_unit="MJy/sr", native_flux_unit="MJy/sr",
                    ra=ra, dec=dec,
                    meta={"path": str(path), "source": "PAHFIT s1d"})


def read_pacs(path: str | Path, z_override: float | None = None,
             band: str | None = None) -> Spectrum:
    """Herschel/PACS HPDP extracted spectrum (wave [um], flux [Jy])."""
    from astropy.io import fits
    path = Path(path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fits.open(path, memmap=False) as hdul:
            tab = hdul["spectra"] if "spectra" in hdul else hdul[1]
            d = tab.data
            cols = {c.lower(): c for c in d.columns.names}
            w = np.asarray(d[cols["wave"]], float)
            fcol = None
            for c in ("pointSourceScaledFlux&", "pointSourceScaledFlux",
                      "pointSourceFlux&", "pointSourceFlux", "centralFlux"):
                if c.lower() in cols:
                    fcol = cols[c.lower()]
                    break
            if fcol is None:
                raise ValueError("PACS spectrum has no point-source flux column")
            ecol = None
            for c in ("pointSourceScaledError&", "pointSourceScaledError",
                      "pointSourceError&", "pointSourceError", "centralError"):
                if c.lower() in cols:
                    ecol = cols[c.lower()]
                    break
            f = np.asarray(d[fcol], float)
            e = np.asarray(d[ecol], float) if ecol else np.full_like(f, np.nan)
            hdr = hdul[0].header
            obj = str(hdr.get("OBJECT", path.stem)).strip().replace(" ", "_")
            ra = hdr.get("RA", np.nan)
            dec = hdr.get("DEC", np.nan)
    mask = np.isfinite(w) & np.isfinite(f) & np.isfinite(e) & (e > 0)
    z = 0.0 if z_override is None else float(z_override)
    return Spectrum(wave_um=w, flux=f, error=e, mask=mask, z=z,
                    band=band or "fir", instrument="PACS",
                    object_id=obj, flux_unit="Jy", native_flux_unit="Jy",
                    ra=ra, dec=dec,
                    meta={"path": str(path), "source": "Herschel/PACS HPDP"})


def read_spitzer_irs_tbl(path: str | Path, z_override: float | None = None,
                          band: str | None = None) -> Spectrum:
    """Spitzer IRS Enhanced IPAC table -> Spectrum (Jy -> cgs f_lambda)."""
    from astropy.table import Table
    path = Path(path)
    try:
        t = Table.read(path, format="ascii.ipac")
    except Exception:
        t = Table.read(path, format="ascii")
    names = {c.lower(): c for c in t.colnames}
    w = np.asarray(t[names["wavelength"]], float)
    fjy = np.asarray(t[names["flux_density"]], float)
    ejy = np.asarray(t[names.get("error", "flux_density_err")], float)
    if "bit-flag" in names:
        good = np.asarray(t[names["bit-flag"]]) == 0
    else:
        good = np.ones_like(w, dtype=bool)
    lam_a = w * 1e4
    conv = 1e-23 * 2.99792458e18 / np.where(lam_a > 0, lam_a ** 2, np.nan)
    flux = fjy * conv / 1e-17
    err = ejy * conv / 1e-17
    mask = good & np.isfinite(w) & np.isfinite(flux) & np.isfinite(err) & (err > 0)
    obj = str(t.meta.get("OBJECT", path.stem)).strip(" '\"")
    z = 0.0 if z_override is None else float(z_override)
    return Spectrum(wave_um=w, flux=flux, error=err, mask=mask, z=z,
                    band=band or "mir", instrument="Spitzer IRS",
                    object_id=obj, flux_unit="1e-17 erg s-1 cm-2 A-1",
                    native_flux_unit="Jy",
                    meta={"path": str(path), "source": "Spitzer IRS Enhanced"})



def read_hst(path: str | Path, z_override: float | None = None,
             band: str | None = None) -> Spectrum:
    """HST/STIS x1d or HASP cspec (WAVELENGTH [A], FLUX/ERROR [cgs/A])."""
    from astropy.io import fits
    path = Path(path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fits.open(path, memmap=False) as hdul:
            tab = None
            for hdu in hdul:
                if getattr(hdu, "columns", None) is None:
                    continue
                names = {c.upper() for c in hdu.columns.names}
                if {"WAVELENGTH", "FLUX", "ERROR"} <= names:
                    tab = hdu
                    break
            if tab is None:
                raise ValueError("HST FITS has no WAVELENGTH/FLUX/ERROR table")
            d = tab.data
            cols = {c.upper(): c for c in d.columns.names}
            wave_a = np.asarray(d[cols["WAVELENGTH"]], float).ravel()
            flux = np.asarray(d[cols["FLUX"]], float).ravel()
            err = np.abs(np.asarray(d[cols["ERROR"]], float).ravel())
            hdr = hdul[0].header
            z = hdr.get("Z", hdr.get("REDSHIFT", np.nan))
            if not np.isfinite(z):
                z = 0.0
            if z_override is not None:
                z = float(z_override)
            obj = str(hdr.get("TARGNAME", path.stem)).strip().replace(" ", "_")
            ra = hdr.get("TARG_RA", hdr.get("RA", np.nan))
            dec = hdr.get("TARG_DEC", hdr.get("DEC", np.nan))
    wave_um = wave_a / 1e4
    flux_1e17 = flux / 1e-17
    err_1e17 = err / 1e-17
    mask = (np.isfinite(wave_um) & np.isfinite(flux_1e17) & np.isfinite(err_1e17)
            & (err_1e17 > 0))
    return Spectrum(wave_um=wave_um, flux=flux_1e17, error=err_1e17,
                    mask=mask, z=float(z), band=band or "optical",
                    instrument="HST/STIS", object_id=obj,
                    flux_unit="1e-17 erg s-1 cm-2 A-1",
                    native_flux_unit="erg s-1 cm-2 A-1",
                    ra=ra, dec=dec,
                    meta={"path": str(path), "source": "HST/STIS x1d or HASP cspec"})


def read_xshooter(path: str | Path, z_override: float | None = None,
                  band: str | None = None) -> Spectrum:
    """ESO X-SHOOTER reduced SFLX spectrum (WAVE [nm], FLUX/ERR [cgs/A])."""
    from astropy.io import fits
    path = Path(path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fits.open(path, memmap=False) as hdul:
            tab = None
            for hdu in hdul:
                if getattr(hdu, "columns", None) is not None:
                    names = {c.upper() for c in hdu.columns.names}
                    if {"WAVE", "FLUX", "ERR"} <= names:
                        tab = hdu
                        break
            if tab is None:
                raise ValueError("X-SHOOTER FITS has no WAVE/FLUX/ERR table")
            d = tab.data
            cols = {c.upper(): c for c in d.columns.names}
            wave_nm = np.asarray(d[cols["WAVE"]], float).ravel()
            flux = np.asarray(d[cols["FLUX"]], float).ravel()
            err = np.asarray(d[cols["ERR"]], float).ravel()
            qual = np.asarray(d[cols["QUAL"]], int).ravel() if "QUAL" in cols else np.zeros_like(flux, dtype=int)
            hdr = hdul[0].header
            z = hdr.get("Z", hdr.get("REDSHIFT", np.nan))
            if not np.isfinite(z):
                z = 0.0
            if z_override is not None:
                z = float(z_override)
            obj = str(hdr.get("OBJECT", path.stem)).strip().replace(" ", "_")
            ra = hdr.get("RA", np.nan)
            dec = hdr.get("DEC", np.nan)
    wave_um = wave_nm / 1000.0
    flux_1e17 = flux / 1e-17
    err_1e17 = np.abs(err) / 1e-17
    mask = (np.isfinite(wave_um) & np.isfinite(flux_1e17) & np.isfinite(err_1e17)
            & (err_1e17 > 0) & (qual == 0))
    return Spectrum(wave_um=wave_um, flux=flux_1e17, error=err_1e17,
                    mask=mask, z=float(z), band=band or "optical",
                    instrument="XSHOOTER", object_id=obj,
                    flux_unit="1e-17 erg s-1 cm-2 A-1",
                    native_flux_unit="erg s-1 cm-2 A-1",
                    ra=ra, dec=dec,
                    meta={"path": str(path), "source": "ESO X-SHOOTER SFLX",
                          "quality_flagged": int(np.sum(qual != 0))})


def read_spectrum(path: str | Path, **kw) -> Spectrum:
    """Adapter dispatch for all supported spectra."""
    from astropy.io import fits
    path = Path(path)
    if path.suffix.lower() in (".tbl", ".dat"):
        return read_spitzer_irs_tbl(path, **kw)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fits.open(path, memmap=False) as hdul:
            names = [h.name for h in hdul]
            if "EXTRACT1D" in names:
                return read_jwst_x1d(path, **kw)
            # PACS HPDP: WAVE [um] + pointSource*/centralFlux [Jy]
            for hdu in hdul:
                if getattr(hdu, "columns", None) is None:
                    continue
                cols = {c.lower() for c in hdu.columns.names}
                if "wave" in cols and any(c.startswith(("pointsourcescaledflux", "pointsourceflux", "centralflux"))
                                           for c in cols):
                    return read_pacs(path, **kw)
                hdr = hdul[0].header
                if {"flux", "wave"} <= cols and str(hdr.get("WAVEUNIT", "")).upper() == "GHZ":
                    return read_hifi_hpdp(path, **kw)
                if {"wavelength", "flux"} <= cols and "uncertainty" in cols:
                    return read_s1d(path, **kw)
                if {"wave", "flux", "err"} <= cols:
                    return read_xshooter(path, **kw)
                if {"wavelength", "flux", "error"} <= cols:
                    return read_hst(path, **kw)
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
