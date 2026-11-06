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


