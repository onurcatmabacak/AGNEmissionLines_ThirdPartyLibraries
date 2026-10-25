from pathlib import Path
import tempfile

import numpy as np
from astropy.io import fits

from pipeline.prepare_inputs import read_spectrum, write_pyqsofit


def test_hst_pds456_reader():
    p = Path("inputs/PDS456_z_0.1840/raw/hst_8264_stis_pds456_sg140l-sg230l_o58s_cspec.fits")
    s = read_spectrum(p)
    assert s["n_pix"] == 1899
    assert 1130 < s["wave"][0] < 1150
    assert 3130 < s["wave"][-1] < 3150
    assert s["good"].all()
    assert np.isfinite(s["flux_1e17"]).all()
    assert np.nanmedian(s["flux_1e17"] / (1.0 / np.sqrt(s["ivar"]))) > 5


def test_hst_3c120_reader_and_error_conversion():
    p = Path("inputs/3C120_z_0.0330/raw/hst_8700_stis_3c120d0_g430l-g750l_o62o_cspec.fits")
    s = read_spectrum(p)
    assert s["n_pix"] == 1425
    assert 2990 < s["wave"][0] < 3000
    assert 10240 < s["wave"][-1] < 10250
    assert (~s["good"]).sum() == 8
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "spectrum.fits"
        s["z"] = 0.033
        write_pyqsofit(s, out)
        h = fits.open(out)
        assert h[0].header["z"] == 0.033
        assert h[0].data.shape == (1425,)
        assert h[1].data.shape == (1425,)
        assert h[2].data.shape == (1425,)
        # prepared PyQSOFit error is in cgs, not 1e-17 units
        assert 1e-18 < np.nanmedian(h[2].data[h[2].data > 0]) < 1e-15


def test_classic_spspec_reader():
    p = Path("inputs/spSpec-51908-0277-120_z_0.0859/raw/spSpec-51908-0277-120.fit")
    if not p.exists():
        import pytest
        pytest.skip("legacy GANDALF input not present")
    s = read_spectrum(p)
    assert s["n_pix"] > 1000
    assert s["z"] > 0.08
    assert s["good"].any()
