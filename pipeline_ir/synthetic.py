"""Synthetic IR line spectra for exercising the router/fitter end to end."""
from __future__ import annotations

import numpy as np

from .lines import BY_NAME
from .spectrum import Spectrum, C_KMS


BAND_RANGE = {"optical": (0.36, 1.04), "nir": (1.0, 5.0), "mir": (5.0, 30.0), "fir": (30.0, 300.0)}


def make_spectrum(z: float, band: str, lines: dict[str, tuple[float, float]],
                  snr: float = 20.0, R: float = 2000.0, seed: int = 1) -> Spectrum:
    """lines: name -> (flux_1e17, fwhm_kms).  Flux is the integrated line flux."""
    lo, hi = BAND_RANGE[band]
    n = int(np.log(hi / lo) / np.log(1 + 1.0 / R)) + 2
    wave = lo * (hi / lo) ** (np.arange(n) / (n - 1))
    rng = np.random.default_rng(seed)
    cont = np.ones_like(wave)
    flux = cont.copy()
    for name, (f, fwhm) in lines.items():
        ln = BY_NAME[name]
        c = ln.rest_um * (1 + z)
        s = c * fwhm / 2.354820045 / C_KMS
        amp = f / (s * np.sqrt(2 * np.pi) * 1e4)  # y is per A, x is um
        flux += amp * np.exp(-0.5 * ((wave - c) / s) ** 2)
    err = np.full_like(wave, 1.0 / snr)
    flux = flux + rng.normal(0, err)
    return Spectrum(wave_um=wave, flux=flux, error=err, mask=np.ones_like(wave, bool),
                    z=z, band=band, instrument=f"synthetic_{band}",
                    object_id=f"synthetic_{band}_z{z:.2f}", native_flux_unit="1e-17")
