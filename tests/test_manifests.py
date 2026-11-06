"""Every source manifest must say where its data came from.

The repository ships no observations, so a manifest is the *only* thing that
makes a result reproducible: if it does not carry a retrievable pointer, the
numbers in docs/RESULTS.md can never be regenerated.  These tests keep that
contract honest without touching the network.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = sorted((ROOT / "inputs").glob("*/source.json"))


def test_there_are_manifests():
    assert MANIFESTS, "no inputs/*/source.json found"


@pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: p.parent.name)
def test_manifest_has_identity_and_tools(path):
    d = json.loads(path.read_text())
    assert d["key"] == path.parent.name, "key must match the directory name"
    assert d.get("kind"), "kind is required (drives the planner)"
    assert isinstance(d.get("z"), (int, float)), "z is required"
    assert d.get("tools"), "a manifest must list at least one tool"


@pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: p.parent.name)
def test_manifest_is_retrievable(path):
    """Non-synthetic sources need a URL and an archive/identifier pair."""
    d = json.loads(path.read_text())
    if d.get("synthetic"):
        assert d.get("generator"), "a synthetic source must name its generator"
        return
    urls = d.get("urls") or {}
    assert urls, "no urls: the data could never be re-fetched"
    assert any(str(u).startswith(("http://", "https://")) for u in urls.values()), \
        f"no http(s) pointer in {sorted(urls)}"
    retrieval = d.get("retrieval") or {}
    assert retrieval.get("archive"), "retrieval.archive is required"
    assert retrieval.get("identifier"), "retrieval.identifier is required"
