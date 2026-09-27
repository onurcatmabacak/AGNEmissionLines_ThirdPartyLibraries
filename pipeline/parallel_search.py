#!/usr/bin/env python3
"""Globally parallel driver for the AGN tool search (CPU).

``pipeline/auto_tune.py`` evaluates one tool at a time, so the slowest tool's
*serial* candidate chain sets the wall-clock while the cores freed by faster
tools sit idle.  This driver instead flattens every tool's candidate grid into a
single global pool sized to the machine, then refines all tools' winners in
parallel rounds before a final combined run.

The fitting codes are pure CPU (NumPy/SciPy/lmfit/emcee/sherpa) and expose no
CUDA/GPU path, so the GPU is deliberately not used: for these small 1-D spectra a
GPU would only add host<->device transfer overhead.

Usage
-----
    python pipeline/parallel_search.py                    # all tools, 3 objects
    python pipeline/parallel_search.py --pool 8 --limit 3 --rounds 1
    python pipeline/parallel_search.py --tools gelato gleam --limit 1 --rounds 0 --stage1-only
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import auto_tune as at  # noqa: E402

ROOT = at.ROOT


def pool_eval(tasks, pool, input_dir, runs, results, repo, tune_tags):
    """Run every (tool, knobs, variant) task through run_pipeline concurrently.

    Each task uses ``--jobs 1`` so the pool (not run_pipeline) controls total
    concurrency.  Returns [(tool, knobs, variant, mean_chi2_common)].
    """
    out = []
    with ThreadPoolExecutor(max_workers=pool) as ex:
        futures = {}
        for tool, knobs, variant in tasks:
            label = f"at_{tool}_{variant}"
            fut = ex.submit(at.run_pipeline, [tool], {tool: variant}, input_dir,
                            label, repo, 1, runs, results)
            futures[fut] = (tool, knobs, variant, label)
        for fut in as_completed(futures):
            tool, knobs, variant, label = futures[fut]
            try:
                fut.result()
            except Exception as exc:  # noqa: BLE001
                print(f"[parallel] WARNING {label}: {exc}")
            rows = at.read_scores(results, label)
            out.append((tool, knobs, variant, at.mean_objective(rows, tool, tune_tags)))
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tools", nargs="*", default=at.TOOL_ORDER, choices=at.TOOL_ORDER)
    p.add_argument("--limit", type=int, default=3)
    p.add_argument("--objects", nargs="*", default=None)
    p.add_argument("--rounds", type=int, default=1)
    p.add_argument("--pool", type=int, default=os.cpu_count() or 4,
                   help="max concurrent fits (default: number of CPUs)")
    p.add_argument("--final-jobs", type=int, default=os.cpu_count() or 4)
    p.add_argument("--runs", type=Path, default=ROOT / "runs")
    p.add_argument("--results", type=Path, default=ROOT / "results")
    p.add_argument("--input", type=Path, default=ROOT / "input")
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--workdir", type=Path, default=ROOT / "work" / "parallel_search")
    p.add_argument("--stage1-only", action="store_true")
    p.add_argument("--no-prepare", action="store_true")
    args = p.parse_args(argv)
    args.workdir.mkdir(parents=True, exist_ok=True)

    if args.no_prepare:
        print("[parallel] skipping prepare (--no-prepare)")
    else:
        subprocess.run([sys.executable, str(ROOT / "pipeline" / "prepare_inputs.py"),
                        "--fits", str(args.input), "--out", str(args.runs),
                        "--gelato-json", str(ROOT / "Gelato" / "my_sdss.json"),
                        "--gleam-static", str(ROOT / "Gleam")], cwd=args.repo, check=True)

    tags = at.discover_tags(args.runs)
    if not tags:
        print(f"[parallel] no prepared objects in {args.runs}")
        return 1
    if args.objects:
        tune_tags = [t for t in args.objects if t in tags]
    else:
        tune_tags = tags[: args.limit]
    if not tune_tags:
        print("[parallel] no tuning objects")
        return 1

    scope = args.workdir / "tuning_input"
    if scope.exists():
        shutil.rmtree(scope)
    input_dir = at.scoped_input(tune_tags, args.runs, scope)
    print(f"[parallel] tools={args.tools} tuning={tune_tags} pool={args.pool}")

    # ---- Stage 1: all (tool, candidate) tasks through one global pool ----
    seen: set[str] = set()
    tasks = []
    for tool in args.tools:
        for knobs in at.enumerate_candidates(tool):
            variant, _, rendered = at._materialise(tool, knobs)
            if rendered in seen:
                continue
            seen.add(rendered)
            tasks.append((tool, knobs, variant))
    print(f"[parallel] stage 1: {len(tasks)} candidate runs")
    t0 = time.time()
    results = pool_eval(tasks, args.pool, input_dir, args.runs, args.results, args.repo, tune_tags)
    print(f"[parallel] stage 1 finished in {time.time() - t0:.0f}s")

    best: dict[str, tuple[dict, str, float]] = {}
    for tool, knobs, variant, score in sorted(results, key=lambda r: (r[0], r[3])):
        print(f"[parallel]   {tool:12s} {variant:46s} mean chi2_common={score:.3f}")
        if tool not in best or score < best[tool][2]:
            best[tool] = (knobs, variant, score)
    for tool, (knobs, variant, score) in best.items():
        print(f"[parallel] {tool}: best {variant} ({score:.3f})")

    # ---- Stage 2: refinement rounds, pooled across all tools ----
    for rnd in range(1, args.rounds + 1):
        round_tasks = []
        for tool in args.tools:
            if tool not in best:
                continue
            for knobs in at.neighbours(tool, best[tool][0]):
                variant, _, rendered = at._materialise(tool, knobs)
                if rendered in seen:
                    continue
                seen.add(rendered)
                round_tasks.append((tool, knobs, variant))
        if not round_tasks:
            break
        print(f"[parallel] round {rnd}: {len(round_tasks)} neighbour runs")
        rres = pool_eval(round_tasks, args.pool, input_dir, args.runs, args.results, args.repo, tune_tags)
        per: dict[str, list] = {}
        for tool, knobs, variant, score in rres:
            per.setdefault(tool, []).append((score, knobs, variant))
        improved = False
        for tool, cands in per.items():
            score, knobs, variant = min(cands, key=lambda c: c[0])
            if score < best[tool][2] - 1e-9:
                best[tool] = (knobs, variant, score)
                improved = True
                print(f"[parallel]   {tool}: improved -> {variant} ({score:.3f})")
        if not improved:
            print("[parallel] no improvement; stopping refinement")
            break

    summary = {t: {"knobs": b[0], "variant": b[1], "mean_chi2_common": b[2]} for t, b in best.items()}
    (args.workdir / "best_configs.json").write_text(json.dumps(summary, indent=2))
    print(f"[parallel] wrote {args.workdir / 'best_configs.json'}")

    if args.stage1_only:
        return 0

    # ---- Final combined run with the winning configs ----
    argsv = []
    for tool, info in summary.items():
        argsv += ["--variant", f"{tool}={info['variant']}"]
    cmd = ["bash", str(args.repo / "run_pipeline.sh"), "--no-build",
           "--tools", " ".join(args.tools), "--jobs", str(args.final_jobs)] + argsv
    env = {**os.environ, "INPUT_DIR": str(args.input),
           "RUNS_DIR": str(args.runs), "RESULTS_DIR": str(args.results)}
    print(f"[parallel] final run: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=args.repo, env=env, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
