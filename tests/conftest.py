"""Shared test fixtures.

The repository ships no observations and no bulk products (see
`docs/RESULTS.md`), so the test-suite is deliberately data-independent: it covers
the registry, the layout helpers, the S/N definitions and the statistics code,
not the committed spectra.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# A conftest.py inside tests/ makes pytest put tests/ on sys.path instead of the
# repository root, so `import pipeline...` in the test modules needs this.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
