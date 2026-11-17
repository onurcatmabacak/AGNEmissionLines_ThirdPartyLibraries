"""The rebin step must preserve flux and propagate errors correctly."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _write(path, wave, flux, err):
    from astropy.io import fits
    cols = [fits.Column(name="WAVELENGTH", format="D", array=wave),
            fits.Column(name="FLUX", format="D", array=flux),
            fits.Column(name="ERROR", format="D", array=err)]
    fits.HDUList([fits.PrimaryHDU(), fits.BinTableHDU.from_columns(cols)]).writeto(path)


def test_flux_is_preserved_and_errors_shrink(tmp_path):
    from astropy.io import fits

    rng = np.random.default_rng(0)
    wave = np.arange(1500.0, 1700.0, 0.1)          # 2000 samples at 0.1 A
    true = 1e-13 + 0.0 * wave
    err = np.full_like(wave, 1e-15)
    flux = true + rng.normal(scale=err)
    src = tmp_path / "in.fits"
    dst = tmp_path / "out.fits"
    _write(src, wave, flux, err)

    subprocess.run([sys.executable, str(ROOT / "pipeline/rebin_spectrum.py"),
                    str(src), str(dst), "--step-A", "10"], check=True,
                   capture_output=True)
    with fits.open(dst) as h:
        d = h[1].data
        w = np.asarray(d["WAVELENGTH"], float)
        f = np.asarray(d["FLUX"], float)
        e = np.asarray(d["ERROR"], float)

    assert w.size == pytest.approx(20, abs=1)       # 200 A / 10 A
    # inverse-variance weighted mean of a constant is the constant
    assert np.allclose(f, 1e-13, rtol=5e-3)
    # 100 samples per bin -> error shrinks by 10
    assert np.allclose(e, 1e-15 / 10.0, rtol=1e-6)


def test_bad_samples_are_dropped(tmp_path):
    from astropy.io import fits
    wave = np.arange(1500.0, 1600.0, 1.0)
    flux = np.ones_like(wave) * 1e-14
    err = np.ones_like(wave) * 1e-15
    flux[10] = np.nan
    err[20] = 0.0
    src, dst = tmp_path / "a.fits", tmp_path / "b.fits"
    _write(src, wave, flux, err)
    subprocess.run([sys.executable, str(ROOT / "pipeline/rebin_spectrum.py"),
                    str(src), str(dst), "--step-A", "5"], check=True, capture_output=True)
    with fits.open(dst) as h:
        f = np.asarray(h[1].data["FLUX"], float)
    assert np.all(np.isfinite(f)) and np.all(f > 0)
