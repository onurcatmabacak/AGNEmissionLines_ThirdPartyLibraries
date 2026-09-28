#!/usr/bin/env python3
"""Per-object, globally parallel, quality-driven line-fitting search.

Unlike ``parallel_search.py`` (which tunes one global config on a small tuning
set), this tunes **each object on itself**: for every object it evaluates that
tool's whole candidate grid, refines the winner, and applies the per-object
winner in a final pass.  Every (object, tool, candidate) evaluation is flattened
into one CPU pool.

Ranking uses the physical objective from ``auto_tune.objective``:
``chi2_common + PENALTY_WEIGHT * line_penalty`` (missing/wrong [OIII] doublet
ratio or an unphysical broad Balmer decrement).  The fitting codes are CPU-only;
there is no GPU path.

Usage
-----
    python pipeline/per_object_search.py                      # all 10 objects
    python pipeline/per_object_search.py --objects 04592939295
    python pipeline/per_object_search.py --tools pyqsofit badass --rounds 1
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


def scoped_one(tag: str, runs: Path, workdir: Path) -> Path:
    scope = workdir / f"obj_{tag}"
    if scope.exists():
        shutil.rmtree(scope)
    return at.scoped_input([tag], runs, scope)


def eval_tasks(tasks, pool, scopes, runs, results, repo):
    """tasks: list of (tag, tool, knobs, variant). Returns (tag, tool, knobs, variant, score)."""
    out = []
    with ThreadPoolExecutor(max_workers=pool) as ex:
        futures = {}
        for tag, tool, knobs, variant in tasks:
            label = f"at_{tag}_{tool}_{variant}"
            fut = ex.submit(at.run_pipeline, [tool], {tool: variant}, scopes[tag],
                            label, repo, 1, runs, results)
            futures[fut] = (tag, tool, knobs, variant, label)
        for fut in as_completed(futures):
            tag, tool, knobs, variant, label = futures[fut]
            try:
                fut.result()
            except Exception as exc:  # noqa: BLE001
                print(f"[perobj] WARNING {label}: {exc}")
            rows = at.read_scores(results, label)
            out.append((tag, tool, knobs, variant, at.mean_objective(rows, tool, [tag])))
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tools", nargs="*", default=at.TOOL_ORDER, choices=at.TOOL_ORDER)
    p.add_argument("--objects", nargs="*", default=None)
    p.add_argument("--rounds", type=int, default=2)
    p.add_argument("--pool", type=int, default=(os.cpu_count() or 4) + 4)
    p.add_argument("--final-jobs", type=int, default=os.cpu_count() or 4)
    p.add_argument("--runs", type=Path, default=ROOT / "runs")
    p.add_argument("--results", type=Path, default=ROOT / "results")
    p.add_argument("--input", type=Path, default=ROOT / "input")
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--workdir", type=Path, default=ROOT / "work" / "per_object")
    p.add_argument("--stage1-only", action="store_true")
    p.add_argument("--no-prepare", action="store_true")
    args = p.parse_args(argv)
    args.workdir.mkdir(parents=True, exist_ok=True)

    if not args.no_prepare:
        subprocess.run([sys.executable, str(ROOT / "pipeline" / "prepare_inputs.py"),
                        "--fits", str(args.input), "--out", str(args.runs),
                        "--gelato-json", str(ROOT / "Gelato" / "my_sdss.json"),
                        "--gleam-static", str(ROOT / "Gleam")], cwd=args.repo, check=True)

    all_tags = at.discover_tags(args.runs)
    tags = [t for t in (args.objects or all_tags) if t in all_tags]
    if not tags:
        print(f"[perobj] no prepared objects (have {all_tags})")
        return 1
    scopes = {t: scoped_one(t, args.runs, args.workdir) for t in tags}
    print(f"[perobj] objects={tags}")
    print(f"[perobj] tools={args.tools} pool={args.pool} rounds={args.rounds}")

    # ---- Stage 1: every (object, tool, candidate) through one global pool ----
    seen: dict[str, set] = {t: set() for t in tags}
    tasks = []
    for tag in tags:
        for tool in args.tools:
            for knobs in at.enumerate_candidates(tool):
                variant, _, rendered = at._materialise(tool, knobs)
                if rendered in seen[tag]:
                    continue
                seen[tag].add(rendered)
                tasks.append((tag, tool, knobs, variant))
    print(f"[perobj] stage 1: {len(tasks)} (object, tool, candidate) runs")
    t0 = time.time()
    res = eval_tasks(tasks, args.pool, scopes, args.runs, args.results, args.repo)
    print(f"[perobj] stage 1 finished in {time.time() - t0:.0f}s")

    best: dict[tuple[str, str], tuple[dict, str, float]] = {}
    for tag, tool, knobs, variant, score in res:
        key = (tag, tool)
        if key not in best or score < best[key][2]:
            best[key] = (knobs, variant, score)
    for (tag, tool), (knobs, variant, score) in sorted(best.items()):
        print(f"[perobj]   {tag} {tool:12s} best {variant:42s} score={score:.3f}")

    # ---- Stage 2: refine each (object, tool) with early stop, pooled ----
    # queue[(tag,tool)] = list of (knobs, variant); one neighbour per pair/round.
    def neighbour_queue(tag, tool, knobs):
        q = []
        for nk in at.neighbours(tool, knobs):
            variant, _, rendered = at._materialise(tool, nk)
            if rendered in seen[tag]:
                continue
            seen[tag].add(rendered)
            q.append((nk, variant))
        return q

    queues = {key: neighbour_queue(key[0], key[1], best[key][0]) for key in best}
    for rnd in range(1, args.rounds + 1):
        batch = [(key[0], key[1], queues[key][0][0], queues[key][0][1])
                 for key in best if queues.get(key)]
        if not batch:
            break
        print(f"[perobj] round {rnd}: {len(batch)} neighbour runs")
        rres = eval_tasks(batch, args.pool, scopes, args.runs, args.results, args.repo)
        improved = False
        for tag, tool, knobs, variant, score in rres:
            key = (tag, tool)
            if score < best[key][2] - 1e-9:
                best[key] = (knobs, variant, score)
                queues[key] = neighbour_queue(tag, tool, knobs)
                improved = True
                print(f"[perobj]   {tag} {tool}: improved -> {variant} ({score:.3f})")
            else:
                queues[key].pop(0)
        if not improved:
            print("[perobj] no improvement; stopping refinement")
            break

    summary = {f"{tag}|{tool}": {"knobs": b[0], "variant": b[1], "score": b[2]}
               for (tag, tool), b in best.items()}
    (args.workdir / "best_configs.json").write_text(json.dumps(summary, indent=2))
    print(f"[perobj] wrote {args.workdir / 'best_configs.json'}")

    if args.stage1_only:
        return 0

    # ---- Final: apply each object's winners to the shared runs/results tree ----
    print("[perobj] final per-object run")
    for tag in tags:
        variants = {tool: best[(tag, tool)][1] for tool in args.tools if (tag, tool) in best}
        if not variants:
            continue
        cmd = ["bash", str(args.repo / "run_pipeline.sh"), "--no-build", "--no-report",
               "--tools", " ".join(args.tools), "--jobs", str(args.final_jobs)]
        for t, v in variants.items():
            cmd += ["--variant", f"{t}={v}"]
        env = {**os.environ, "INPUT_DIR": str(scopes[tag]),
               "RUNS_DIR": str(args.runs), "RESULTS_DIR": str(args.results)}
        print(f"[perobj] final {tag}: {variants}")
        subprocess.run(cmd, cwd=args.repo, env=env, check=False)

    # Rebuild the aggregate results/report over the whole tree.
    for script in ("collect_results.py", "score_fits.py", "make_report.py"):
        subprocess.run([sys.executable, str(ROOT / "pipeline" / script),
                        "--runs", str(args.runs), "--results", str(args.results)],
                       cwd=args.repo, check=False)
    print("[perobj] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
