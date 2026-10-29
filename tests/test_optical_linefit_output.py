import json
from pathlib import Path


def test_optical_linefit_pds_result():
    p = Path("outputs/optical_linefit/PDS456_z_0.1840/optical_lines_summary.json")
    d = json.loads(p.read_text())
    assert d["Hbeta_total_1e17"] > 0
    assert d["OIII5007_total_1e17"] > 0
    assert d["quality"] in ("accepted", "provisional", "tentative")
    assert d["chi2_red"] > 0
    assert Path("outputs/optical_linefit/PDS456_z_0.1840/optical_fit.png").is_file()
