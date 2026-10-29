import csv
import json
from pathlib import Path

import pytest

from pipeline.io_layout import iter_sources
from pipeline.validate_outputs import validate


def test_catalog_matches_schema_and_filesystem():
    errors = validate(check_hashes=True, strict_unknown=True)
    assert errors == []


def test_every_source_key_has_manifest():
    for src in iter_sources():
        p = Path(src["_path"]) / "source.json"
        assert p.is_file(), src["key"]
        assert src["key"] == p.parent.name


def _rows(path, key="line"):
    with path.open(newline="") as fh:
        return {r[key]: r for r in csv.DictReader(fh)}


def test_qsofitmore_golden():
    g = json.loads((Path("tests/golden/science_metrics.json")).read_text())["qsofitmore_line"]
    rows = _rows(Path("outputs/qsofitmore_line/04592649654_z_0.5874/qsofitmore_lines.csv"))
    assert float(rows["Hbeta"]["area_1e17"]) == pytest.approx(g["hbeta_total_1e17"], rel=1e-8)
    assert float(rows["OIII5007"]["area_1e17"]) == pytest.approx(g["oiii5007_total_1e17"], rel=1e-8)
    ratio = float(rows["Hbeta"]["area_1e17"]) / float(rows["OIII5007"]["area_1e17"])
    assert ratio == pytest.approx(g["hb_oiii_ratio"], rel=1e-8)
    with Path("outputs/qsofitmore_line/04592649654_z_0.5874/qsofitmore_mc_summary.csv").open() as fh:
        assert sum(1 for _ in fh) > 1


def test_xray_golden():
    g = json.loads((Path("tests/golden/science_metrics.json")).read_text())
    x = _rows(Path("outputs/xmm_xspec/PDS456_z_0.1840/xmm_lines.csv"), "fit_id")["joint_pl_line"]
    assert float(x["delta_chi2"]) == pytest.approx(g["xmm_pds456"]["fe_ka_delta_chi2"], rel=1e-6)
    assert float(x["significance_sigma"]) == pytest.approx(g["xmm_pds456"]["fe_ka_significance_sigma"], rel=1e-6)
    assert float(x["flux_erg_cm2_s"]) == pytest.approx(g["xmm_pds456"]["fe_ka_flux_erg_cm2_s"], rel=1e-6)
    assert float(x["ew_rest_keV"]) * 1e3 == pytest.approx(g["xmm_pds456"]["fe_ka_ew_rest_eV"], rel=1e-6)

    r = _rows(Path("outputs/rxte_xspec/3C120_z_0.0330/rxte_lines.csv"), "fit_id")["line_3_20"]
    assert float(r["delta_chi2"]) == pytest.approx(g["rxte_3c120"]["fe_ka_delta_chi2"], rel=1e-5)
    assert float(r["significance_sigma"]) == pytest.approx(g["rxte_3c120"]["fe_ka_significance_sigma"], rel=1e-5)
    assert float(r["flux_erg_cm2_s"]) == pytest.approx(g["rxte_3c120"]["fe_ka_flux_erg_cm2_s"], rel=1e-8)
    assert float(r["ew_rest_keV"]) * 1e3 == pytest.approx(g["rxte_3c120"]["fe_ka_ew_rest_eV"], rel=1e-5)


def test_manga_golden():
    g = json.loads((Path("tests/golden/science_metrics.json")).read_text())["manga_ngc1194"]
    d = json.loads(Path("outputs/manga_dap/NGC1194_z_0.0136/subset_comparison.json").read_text())
    assert d["bpt"]["n"] == g["n_bins"]
    assert d["bpt"]["agreement_fraction"] == pytest.approx(g["bpt_agreement_fraction"])
    assert d["line_statistics"]["ha"]["median_ratio"] == pytest.approx(g["ha_median_ratio"], rel=1e-12)
    assert d["line_statistics"]["hb"]["median_ratio"] == pytest.approx(g["hb_median_ratio"], rel=1e-12)
    assert d["line_statistics"]["oiii_5007"]["median_ratio"] == pytest.approx(g["oiii_5007_median_ratio"], rel=1e-12)


def test_crossmission_golden():
    g = json.loads((Path("tests/golden/science_metrics.json")).read_text())
    for source, expected in (("3C120_z_0.0330", g["crossmission_3c120"]),
                             ("PDS456_z_0.1840", g["crossmission_pds456"])):
        d = json.loads((Path("outputs") / "crossmission" / source /
                        "xray_optical_comparison.json").read_text())
        assert d["optical_line"] == expected["optical_line"]
        assert d["quality"] == expected["quality"]
        assert d["optical_flux_erg_cm2_s"] == pytest.approx(expected["optical_flux_erg_cm2_s"], rel=1e-8)
        assert d["optical_to_xray_flux_ratio"] == pytest.approx(expected["optical_to_xray_flux_ratio"], rel=1e-6)
        ew = d["optical"]["ew_rest_A"][d["optical_line"]]["ew_rest_A"]
        assert ew == pytest.approx(expected["optical_ew_rest_A"], rel=1e-6)
        assert (Path("outputs") / "crossmission" / source /
                "xray_optical_comparison.png").is_file()
