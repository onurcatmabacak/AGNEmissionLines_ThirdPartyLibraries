import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Tools" / "nustar_xspec"))

from run_nustar_xspec import caldb_config_text  # noqa: E402


def test_caldb_config_is_a_mission_instrument_table():
    text = caldb_config_text()
    lines = [line for line in text.splitlines() if line.strip()]
    assert len(lines) == 2
    assert lines[0].startswith("NUSTAR FPMA CALDB data/nustar/fpm caldb.indx")
    assert lines[1].startswith("NUSTAR FPMB CALDB data/nustar/fpm caldb.indx")
    assert "CALDB =" not in text
