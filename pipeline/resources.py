#!/usr/bin/env python3
"""Resource-aware thread/job policy.

The repository must not assume a fixed four cores/eight threads.  This module
reads the actual process affinity, cgroup CPU/memory limits (v1 and v2) and the
available GPU, then chooses a conservative thread count for a multicore tool
and a safe number of concurrent single-core jobs.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.tool_capabilities import THREADS  # noqa: E402

# Conservative resident-memory estimates for one concurrent instance (GB).
# These are planning guards, not measured benchmarks.  Tools that exceed the
# host budget are serialized rather than allowed to trigger the OOM killer.
MEMORY_GB = {
    "s3fit_line": 8.0, "galspec_line": 6.0, "qgfit": 8.0,
    "pahfit_mir": 4.0, "cafe_line": 6.0, "manga_dap": 8.0,
    "manga_dap_full": 8.0, "agnfitter_sed": 8.0, "ppxf_host": 3.0,
    "gandalf_line": 3.0, "optical_linefit": 2.0, "ir_linefit": 2.0,
    "sheap_line": 4.0, "pyqsofit_uv": 2.0, "qsofitmore_line": 3.0,
    "pyqsofitspec_line": 3.0, "xmm_xspec": 2.0, "rxte_xspec": 2.0,
    "crossmission": 1.0, "crossband": 1.0, "fir_linefit": 1.0,
    "nir_linefit": 1.0, "cigale_sed": 3.0, "sdss_zline": 0.0,
}


@dataclass(frozen=True)
class ResourceSnapshot:
    cpu_count: int
    cpu_limit: int
    memory_total_gb: float
    memory_available_gb: float
    cgroup_cpu: str | None
    cgroup_memory: str | None
    gpu_count: int
    gpu_names: list[str]
    hostname: str

    @classmethod
    def detect(cls) -> "ResourceSnapshot":
        affinity = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)
        cpu_count = max(1, int(affinity))
        cgroup_cpu = None
        quota_limit = cpu_count
        for path in (Path("/sys/fs/cgroup/cpu.max"),
                     Path("/sys/fs/cgroup/cpu/cpu.cfs_quota_us")):
            try:
                text = path.read_text().strip()
            except OSError:
                continue
            if path.name == "cpu.max":
                quota, period = text.split()[:2]
                if quota != "max":
                    quota_limit = max(1, int(math.ceil(int(quota) / int(period))))
                    cgroup_cpu = f"{quota}/{period}"
            elif text and int(text) > 0:
                period_path = path.with_name("cpu.cfs_period_us")
                period = int(period_path.read_text().strip()) if period_path.exists() else 100000
                quota_limit = max(1, int(math.ceil(int(text) / period)))
                cgroup_cpu = f"{text}/{period}"
            break
        cpu_limit = min(cpu_count, quota_limit)

        mem_total_kb = _meminfo_kb("MemTotal")
        mem_avail_kb = _meminfo_kb("MemAvailable")
        cgroup_memory = None
        for path in (Path("/sys/fs/cgroup/memory.max"),
                     Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")):
            try:
                text = path.read_text().strip()
                if text and text != "max" and int(text) < (1 << 60):
                    cgroup_memory = text
                    mem_avail_kb = min(mem_avail_kb, int(int(text) / 1024)) if mem_avail_kb else int(int(text) / 1024)
                    break
            except (OSError, ValueError):
                continue
        total_gb = mem_total_kb / (1024 ** 2) if mem_total_kb else 0.0
        avail_gb = mem_avail_kb / (1024 ** 2) if mem_avail_kb else total_gb
        gpu_names = []
        if shutil.which("nvidia-smi"):
            try:
                out = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                    capture_output=True, text=True, timeout=5, check=False).stdout.strip()
                gpu_names = [x.strip() for x in out.splitlines() if x.strip()]
            except Exception:
                pass
        return cls(cpu_count=cpu_count, cpu_limit=cpu_limit,
                   memory_total_gb=round(total_gb, 2),
                   memory_available_gb=round(avail_gb, 2),
                   cgroup_cpu=cgroup_cpu, cgroup_memory=cgroup_memory,
                   gpu_count=len(gpu_names), gpu_names=gpu_names,
                   hostname=os.uname().nodename)

    @property
    def cpu_budget(self) -> int:
        # Leave one core free on small machines and two on larger ones for the
        # OS, Docker daemon and the parent scheduler.
        reserve = 1 if self.cpu_limit <= 4 else 2
        return max(1, self.cpu_limit - reserve)

    @property
    def memory_budget_gb(self) -> float:
        return max(0.5, self.memory_available_gb - 2.0)

    def report(self) -> dict:
        return {**asdict(self), "cpu_budget": self.cpu_budget,
                "memory_budget_gb": round(self.memory_budget_gb, 2)}


def _meminfo_kb(key: str) -> int:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith(key + ":"):
                return int(line.split()[1])
    except OSError:
        pass
    return 0


def parse_count(value, snapshot: ResourceSnapshot, upper: int | None = None):
    """Parse an integer or ``auto`` into a bounded count."""
    if value is None or str(value).lower() == "auto":
        n = snapshot.cpu_budget
    else:
        n = max(1, int(value))
    return min(n, upper) if upper is not None else n


def threads_for_tool(tool: str, requested, snapshot: ResourceSnapshot) -> int:
    declared = int(THREADS.get(tool, 1))
    if declared <= 1:
        return 1
    n = parse_count(requested, snapshot)
    # Do not start a high-memory tool if the host cannot hold one instance.
    mem_cap = max(1, int(snapshot.memory_budget_gb / max(MEMORY_GB.get(tool, 2.0), 0.5)))
    return max(1, min(n, declared, snapshot.cpu_budget, mem_cap))


def jobs_for_singles(tools, requested, snapshot: ResourceSnapshot) -> int:
    tools = list(tools)
    if not tools:
        return 1
    n = parse_count(requested, snapshot)
    mem_cap = max(1, int(snapshot.memory_budget_gb / max(max(MEMORY_GB.get(t, 1.0) for t in tools), 0.5)))
    return max(1, min(n, snapshot.cpu_budget, mem_cap, len(tools)))


def env_for_threads(n: int) -> dict[str, str]:
    n = str(max(1, int(n)))
    return {
        "OMP_NUM_THREADS": n, "OPENBLAS_NUM_THREADS": n,
        "MKL_NUM_THREADS": n, "NUMEXPR_NUM_THREADS": n,
        "VECLIB_MAXIMUM_THREADS": n, "NUMBA_NUM_THREADS": n,
        "MANGA_DAP_NPROC": n,
    }


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    s = ResourceSnapshot.detect()
    if a.json:
        print(json.dumps(s.report(), indent=2))
    else:
        r = s.report()
        print(f"host={r['hostname']} cpus={r['cpu_count']} cgroup={r['cgroup_cpu'] or '-'}")
        print(f"memory={r['memory_total_gb']:.1f} GB total / {r['memory_available_gb']:.1f} GB available")
        print(f"gpu={r['gpu_count']} ({', '.join(r['gpu_names']) or 'none'})")
        print(f"budget: {r['cpu_budget']} CPUs, {r['memory_budget_gb']:.1f} GB")
        for t in sorted(THREADS):
            if THREADS[t] > 1:
                print(f"  {t:18s} declared={THREADS[t]} selected={threads_for_tool(t, 'auto', s)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
