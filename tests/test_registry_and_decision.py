from pathlib import Path

from pipeline.tool_registry import TOOLS, BY_NAME
from pipeline.decide_tools import choose


def test_registry_unique_and_runners_exist():
    names = [t.name for t in TOOLS]
    assert len(names) == len(set(names))
    for t in TOOLS:
        runner = Path(t.runner)
        assert runner.exists(), (t.name, runner)
        if t.config.endswith(".json"):
            assert Path(t.config).exists(), (t.name, t.config)


def test_crossmission_registered():
    t = BY_NAME["crossmission"]
    assert t.kind == "ratio"
    assert t.runner == "pipeline/compare_xray_optical.py"
    assert Path(t.config).exists()


def test_decision_engine_xray_and_uv():
    d = choose("xray", 0.184, 0.5e-3, 10e-3)  # 0.5-10 keV expressed in um-equivalent
    assert "xmm_xspec" in d["tools"]
    assert "rxte_xspec" in d["tools"]
    d = choose("lines", 0.184, 0.1, 0.3)
    assert "pyqsofit_uv" in d["tools"]
