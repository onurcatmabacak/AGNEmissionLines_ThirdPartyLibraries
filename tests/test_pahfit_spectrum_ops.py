import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Tools" / "pahfit_mir"))

from spectrum_ops import apply_error_floor, trim_near_gaps  # noqa: E402


def test_error_floor_zero_is_noop():
    flux = np.array([1.0, -2.0, 0.0])
    err = np.array([0.1, 0.2, 0.3])
    out = apply_error_floor(flux, err, 0.0)
    assert np.allclose(out, err)
    assert out is not err


def test_error_floor_adds_relative_quadrature():
    flux = np.array([10.0, -10.0])
    err = np.array([1.0, 1.0])
    out = apply_error_floor(flux, err, 0.1)
    assert np.allclose(out, np.sqrt(1.0 + 1.0))
    assert np.all(out >= 0.1 * np.abs(flux))


def test_error_floor_rejects_negative_and_mismatched():
    with pytest.raises(ValueError):
        apply_error_floor([1.0], [0.1], -0.1)
    with pytest.raises(ValueError):
        apply_error_floor([1.0, 2.0], [0.1], 0.1)


def test_trim_near_gaps_removes_edges_and_keeps_interior():
    w = np.array([9.0, 9.95, 10.0, 10.05, 11.0, 12.0, 12.05, 13.0])
    gaps = [{"start_um": 10.0, "end_um": 12.0}]
    keep = trim_near_gaps(w, gaps, 0.1)
    assert keep.tolist() == [True, False, False, False, True, False, False, True]


def test_trim_near_gaps_zero_is_noop_and_negative_rejected():
    w = np.array([9.0, 10.0, 11.0])
    assert trim_near_gaps(w, [{"start_um": 10.0, "end_um": 12.0}], 0.0).all()
    with pytest.raises(ValueError):
        trim_near_gaps(w, [], -0.1)
