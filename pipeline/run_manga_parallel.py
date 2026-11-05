#!/usr/bin/env python3
"""Run the official MaNGA DAP on several cubes concurrently.

sdss-mangadap is single-core and has no parallel switch (verified against the
installed package: no ``ncpu``/``multiprocessing`` anywhere), so the only
speed-up that stays *official* is to run independent cubes in parallel.  This
runner does exactly that: one container per cube, each with its own output
tree, and a single summary at the end.

    python pipeline/run_manga_parallel.py --jobs 4 \
        inputs/NGC1194_z_0.0136 inputs/NGC4395_z_0.0010 ...

Each job is the existing wrapper ``pipeline/runners/run_manga_dap_docker.sh``
with ``--full``, so the products are byte-identical to a serial run; only the
wall-clock changes.  Intra-cube sharding (splitting the pPXF stage of one
cube) is *not* implemented — see ``docs/MANGA_SHARDING.md`` for the design and
why it needs an upstream/patched seam plus a full validation run.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.io_layout import ensure_output  # noqa: E402


def run_one(source_dir: Path, jobs_out: Path, extra: list[str]) -> dict:
    key = source_dir.name
    out = ensure_output(key, "manga_dap")
    cmd = ["bash", str(ROOT / "pipeline" / "runners" / "run_manga_dap_docker.sh"),
           str(source_dir), str(out), "--full", *extra]
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    ok = proc.returncode == 0 and (out / "run.json").exists()
    return {
        "source": key,
        "ok": ok,
        "rc": proc.returncode,
        "seconds": time.time() - t0,
        "out": str(out),
        "tail": (proc.stderr or proc.stdout)[-400:] if not ok else "",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sources", nargs="+", type=Path,
                    help="source directories under inputs/, e.g. inputs/NGC1194_z_0.0136")
    ap.add_argument("--jobs", type=int, default=3,
                    help="cubes to run concurrently (each is one core)")
    ap.add_argument("--extra", default="", help="extra arguments forwarded to the wrapper")
    args = ap.parse_args(argv)

    extra = args.extra.split() if args.extra else []
    started = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futures = {ex.submit(run_one, s, ROOT / "outputs", extra): s for s in args.sources}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            print(f"[{r['source']}] {'ok' if r['ok'] else 'FAILED'} "
                  f"rc={r['rc']} {r['seconds']:.0f}s -> {r['out']}", flush=True)
            if not r["ok"]:
                print("  " + r["tail"].replace("\n", "\n  "), flush=True)

    ok = sum(1 for r in results if r["ok"])
    print(f"\n{ok}/{len(results)} cubes completed in {time.time() - started:.0f}s "
          f"(jobs={args.jobs})")
    for r in sorted(results, key=lambda x: x["source"]):
        print(f"  {r['source']:<28} {'ok' if r['ok'] else 'FAILED'}  {r['seconds']:8.0f}s")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
