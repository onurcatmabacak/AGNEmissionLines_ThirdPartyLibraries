import json
from pathlib import Path

from pipeline.plan_analysis import make_plan
from pipeline.io_layout import load_source


def test_planner_3c120_has_optical_xray_and_crossmission():
    p = make_plan(load_source("3C120_z_0.0330"), goal="auto")
    tools = {c["tool"] for c in p["selected"]}
    assert {"pyqsofit_uv", "rxte_xspec", "crossmission"} <= tools
    assert "cafe_line" not in tools
    assert p["bands"]["xray"] and p["bands"]["optical"]


def test_planner_pds456_has_local_hbeta():
    p = make_plan(load_source("PDS456_z_0.1840"), goal="lines")
    tools = {c["tool"] for c in p["selected"]}
    assert "optical_linefit" in tools
    assert "xmm_xspec" not in tools  # goal=lines does not add X-ray


def test_planner_respects_cost_cap():
    p = make_plan(load_source("PDS456_z_0.1840"), goal="auto", max_cost="short")
    assert all(c["cost"] == "short" for c in p["selected"])
    assert any(c["tool"] == "optical_linefit" for c in p["selected"])


def test_statistical_report_is_small_n_and_does_not_fit_a_correlation():
    d = json.loads(Path("docs/statistical_results.json").read_text())
    assert d["crossmission"]
    assert all(x["sample_size"] == 2 for x in d["crossmission"])
    assert "no correlation" in " ".join(d["warnings"]).lower()
    assert d["pds456_local_hbeta"]["quality"] == "provisional"


def test_every_registered_tool_has_capabilities():
    from pipeline.tool_registry import TOOLS
    from pipeline.tool_capabilities import THREADS, FULL_CAPABILITY
    names = {t.name for t in TOOLS}
    assert names <= set(THREADS)
    assert names <= set(FULL_CAPABILITY)
