from pathlib import Path

import yaml

from pipeline.tool_registry import TOOLS

ROOT = Path(__file__).resolve().parents[1]
CAVEATS = ROOT / "configs" / "caveats.yaml"
REQUIRED = {"tool", "kind", "wave", "status", "severity", "caveat", "evidence", "mitigation"}


def _caveat_tools():
    data = yaml.safe_load(CAVEATS.read_text())
    return {entry["tool"]: entry for entry in data["tools"]}


def test_registry_and_caveats_cover_the_same_tools():
    assert set(_caveat_tools()) == {tool.name for tool in TOOLS}


def test_every_caveat_has_the_fields_build_caveat_matrix_needs():
    for name, entry in _caveat_tools().items():
        missing = REQUIRED - set(entry)
        assert not missing, (name, sorted(missing))
