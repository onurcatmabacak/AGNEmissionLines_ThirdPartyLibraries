#!/usr/bin/env python3
"""Apply per-object winners from a previous per_object_search run.

Reads ``work/per_object/best_configs.json`` (keys ``"<tag>|<tool>"``) and runs
``run_pipeline.sh`` once per object with *that object's* winning variants, then
rebuilds the aggregate results/report.  This is the final pass of
``per_object_search.py`` split out so a completed search can be re-applied
without redoing the expensive stage-1/refinement.

Requires the run_pipeline fix that runs only the objects in ``INPUT_DIR`` (a
pre-populated ``runs/`` must not be re-run with the wrong per-object config).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import auto_tune as at  # noqa: E402

ROOT = at.ROOT


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--best", type=Path, default=ROOT / "work" / "per_object" / "best_configs.json")
    p.add_argument("--tools", nargs="*", default=at.TOOL_ORDER, choices=at.TOOL_ORDER)
    p.add_argument("--input", type=Path, default=ROOT / "input")
    p.add_argument("--runs", type=Path, default=ROOT / "runs")
    p.add_argument("--results", type=Path, default=ROOT / "results")
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--workdir", type=Path, default=ROOT / "work" / "per_object")
    p.add_argument("--final-jobs", type=int, default=os.cpu_count() or 4)
    args = p.parse_args(argv)

    raw = json.loads(args.best.read_text())
    best: dict[str, dict] = {}
    for key, info in raw.items():
        tag, tool = key.split("|", 1)
        best.setdefault(tag, {})[tool] = info["variant"]
    tags = [t for t in at.discover_tags(args.runs) if t in best]
    print(f"[apply] {len(tags)} objects, {sum(len(v) for v in best.values())} (object, tool) winners")

    # Per-object scoped input dirs, built directly from the raw spectra.  We do
    # NOT read runs/<tag>/manifest.json here: a partially-applied previous pass
    # can have re-pointed those manifests at the scopes themselves.
    scopes = {}
    for tag in tags:
        scope = args.workdir / f"obj_{tag}"
        if scope.exists():
            shutil.rmtree(scope)
        (scope / "input").mkdir(parents=True, exist_ok=True)
        matches = [f for f in args.input.glob("*.fits") if tag in f.name]
        for f in matches:
            link = scope / "input" / f.name
            if not link.exists():
                link.symlink_to(f.resolve())
        if not matches:
            print(f"[apply] WARNING: no spectrum matching {tag} in {args.input}")
        scopes[tag] = scope / "input"

    for tag in tags:
        variants = {t: v for t, v in best[tag].items() if t in args.tools}
        if not variants:
            continue
        cmd = ["bash", str(args.repo / "run_pipeline.sh"), "--no-build", "--no-report",
               "--tools", " ".join(args.tools), "--jobs", str(args.final_jobs)]
        for t, v in variants.items():
            cmd += ["--variant", f"{t}={v}"]
        env = {**os.environ, "INPUT_DIR": str(scopes[tag]),
               "RUNS_DIR": str(args.runs), "RESULTS_DIR": str(args.results)}
        print(f"[apply] {tag}: {variants}")
        subprocess.run(cmd, cwd=args.repo, env=env, check=False)

    for script in ("collect_results.py", "score_fits.py", "make_report.py"):
        subprocess.run([sys.executable, str(ROOT / "pipeline" / script),
                        "--runs", str(args.runs), "--results", str(args.results)],
                       cwd=args.repo, check=False)
    print("[apply] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
