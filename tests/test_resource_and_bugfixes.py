import csv
from pathlib import Path

import pytest
from astropy.io import fits

from pipeline.resources import ResourceSnapshot, jobs_for_singles, threads_for_tool


def snap(cpu=8, mem=16.0):
    return ResourceSnapshot(cpu_count=cpu, cpu_limit=cpu, memory_total_gb=mem,
                            memory_available_gb=mem, cgroup_cpu=None,
                            cgroup_memory=None, gpu_count=0, gpu_names=[],
                            hostname="test")


def test_resource_policy_is_bounded_by_cpu_and_memory():
    s = snap(cpu=8, mem=16)
    assert 1 <= threads_for_tool("s3fit_line", "auto", s) <= s.cpu_budget
    assert 1 <= threads_for_tool("s3fit_line", 999, s) <= 8
    assert 1 <= jobs_for_singles(["pyqsofit_uv", "qsofitmore_line"], "auto", s) <= s.cpu_budget


def test_resource_policy_does_not_oversubscribe_small_host():
    s = snap(cpu=2, mem=3)
    assert threads_for_tool("s3fit_line", "auto", s) == 1
    assert jobs_for_singles(["pyqsofit_uv", "qsofitmore_line"], "auto", s) == 1


def test_xmm_rest_ew_is_xspec_consistent():
    p = Path("outputs/PDS456_z_0.1840/xmm_xspec/xmm_lines.csv")
    with p.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    row = next(r for r in rows if r["fit_id"] == "joint_pl_line")
    z = 0.184
    assert float(row["ew_rest_keV"]) == pytest.approx(float(row["ew_xspec_obs_keV"]) * (1 + z), rel=0.02)


def test_pds_hbeta_ew_is_rest_frame():
    import json
    d = json.loads(Path("outputs/PDS456_z_0.1840/optical_linefit/optical_lines_summary.json").read_text())
    assert d["Hbeta_ew_rest_A"] == pytest.approx(d["Hbeta_ew_obs_A"] * 1.184, rel=1e-6)


def test_pyqsofit_out_of_coverage_line_is_frozen():
    p = Path("outputs/04545014975_z_1.1289/pyqsofit_uv/qsopar.fits")
    with fits.open(p) as h:
        rows = h["line_priors"].data
    vals = [int(r["vary"]) for r in rows if str(r["linename"]).startswith("OIII5007")]
    assert vals and all(v == 0 for v in vals)
