"""Shared test fixtures.

The repository no longer ships `inputs/` (raw third-party observations) or the
bulk of `outputs/`; see `docs/RESULTS.md`.  Tests that need a specific spectrum
or a committed product have to skip instead of fail on a fresh clone, and
`DATA_SHIPPED` is the single switch they consult.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# A conftest.py inside tests/ makes pytest put tests/ on sys.path instead of the
# repository root, so `import pipeline...` in the test modules needs this.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def data_shipped() -> bool:
    """True when this checkout has real input data (or a committed catalogue)."""
    inputs = ROOT / "inputs"
    has_inputs = inputs.is_dir() and any(inputs.glob("*/*/*.fits*"))
    has_catalog = (ROOT / "outputs" / "output_catalog.json").exists()
    return has_inputs or has_catalog


requires_data = pytest.mark.skipif(
    not data_shipped(),
    reason="inputs/ and outputs/ are not shipped; results are in docs/RESULTS.md",
)
