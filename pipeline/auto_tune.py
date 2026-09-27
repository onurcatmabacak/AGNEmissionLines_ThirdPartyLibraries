#!/usr/bin/env python3
"""Iteratively tune the five AGN fitting tools toward their best fit.

The pipeline fits each spectrum once with a static configuration.  This driver
turns that into a search: it renders parameter variants of each tool's config,
runs them across a small set of tuning objects, scores every run with the common
reduced chi-square from ``pipeline/score_fits.py``, keeps the winner per tool,
refines it with a coordinate-descent pass, and finally re-runs the winning
configuration on every object to produce the comparison report.

Objective
---------
``chi2_common`` is the primary objective: it rebuilds each tool's total model on
the same prepared spectrum with the same calibrated errors, so it cannot be
gamed by inflating a tool's internal error floor.  When a tool does not expose a
usable model we fall back to its reported reduced chi-square.

Usage
-----
    # full automatic run (tune on up to 3 objects, then fit everything)
    python pipeline/auto_tune.py

    # tune only PyQSOFit on 2 objects, two refinement rounds
    python pipeline/auto_tune.py --tools pyqsofit --limit 2 --rounds 2

    # show the candidate grid without running anything
    python pipeline/auto_tune.py --dry-run

    # skip the final full-quality run
    python pipeline/auto_tune.py --stage1-only
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIGS = ROOT / "configs"


# ---------------------------------------------------------------------------
# Per-tool knob spaces and renderers
# ---------------------------------------------------------------------------
# Every knob has a default matching the shipped base config.  ``CANDIDATES``
# lists the stage-1 variants; ``knob_values`` drives coordinate-descent
# refinement.  Renderers patch the base file text in place and must be total:
# missing knobs fall back to the default.

PYQ = {
    "file": "main.py",
    "base": ROOT / "pyqsofit" / "main.py",
    "defaults": {"error_floor": "0.02", "fe_op": "True", "reject_badpix": "True"},
    "candidates": [
        {},                                                   # base
        {"error_floor": "0.03"},
        {"error_floor": "0.05"},
        {"fe_op": "False"},
        {"error_floor": "0.03", "fe_op": "False"},
        {"error_floor": "0.02", "reject_badpix": "False"},
    ],
    "knob_values": {
        "error_floor": ["0.02", "0.03", "0.05"],
        "fe_op": ["True", "False"],
        "reject_badpix": ["True", "False"],
    },
}


def render_pyqsofit(text: str, k: dict) -> str:
    ef = k["error_floor"]
    text, n = re.subn(r"\b(err|error)\s*=\s*0\.0[0-9]+\s*\*\s*flux", rf"\1 = {ef} * flux", text)
    assert n >= 1, "pyqsofit: error floor not found"
    text, n = re.subn(r"Fe_uv_op\s*=\s*(True|False)", f"Fe_uv_op={k['fe_op']}", text)
    assert n == 1, "pyqsofit: Fe_uv_op not found"
    text, n = re.subn(r"reject_badpix\s*=\s*(True|False)", f"reject_badpix={k['reject_badpix']}", text)
    assert n == 1, "pyqsofit: reject_badpix not found"
    return text


BADASS = {
    "file": "main.py",
    "base": ROOT / "badass" / "main.py",
    "defaults": {"fit_stat": "OLS", "broad_disp_min": "600", "n_basinhop": "5", "tie_disp": "False"},
    "candidates": [
        {},
        {"fit_stat": "RCHI2"},
        {"broad_disp_min": "1500"},
        {"broad_disp_min": "2500"},
        {"broad_disp_min": "1500", "fit_stat": "RCHI2"},
        {"tie_disp": "True"},
        {"n_basinhop": "20"},
    ],
    "knob_values": {
        "fit_stat": ["OLS", "RCHI2"],
        "broad_disp_min": ["600", "1000", "1500", "2500"],
        "n_basinhop": ["5", "20"],
        "tie_disp": ["False", "True"],
    },
}


def render_badass(text: str, k: dict) -> str:
    text, n = re.subn(r'"fit_stat":\s*"(OLS|RCHI2|ML)"', f'"fit_stat": "{k["fit_stat"]}"', text)
    assert n == 1, "badass: fit_stat not found"
    # broad line dispersion: raise the lower bound so broad forbidden components
    # cannot collapse onto the narrow lines.  Match the broad default (600,6000)
    # exactly so the narrow disp_plim is left untouched.
    text, n = re.subn(r'"disp_plim":\s*\(\s*600\s*,\s*6000\s*\)',
                      f'"disp_plim": ({k["broad_disp_min"]}, 6000)', text)
    assert n == 1, "badass: broad disp_plim not found"
    text, n = re.subn(r'BADASS_NBASINHOP",\s*\d+\)', f'BADASS_NBASINHOP", {k["n_basinhop"]})', text)
    assert n == 1, "badass: n_basinhop not found"
    text, n = re.subn(r'"tie_line_disp":\s*(True|False)', f'"tie_line_disp": {k["tie_disp"]}', text)
    assert n == 1, "badass: tie_line_disp not found"
    return text


FANTASY = {
    "file": "main.py",
    "base": ROOT / "fantasy_agn" / "main.py",
    "defaults": {"min_fwhm_br": "700", "max_fwhm_br": "6000", "feii": "True", "ntrial": "10"},
    "candidates": [
        {},
        {"min_fwhm_br": "400"},
        {"min_fwhm_br": "1200"},
        {"feii": "False"},
        {"min_fwhm_br": "400", "feii": "False"},
        {"ntrial": "20"},
    ],
    "knob_values": {
        "min_fwhm_br": ["400", "700", "1200"],
        "max_fwhm_br": ["3000", "6000"],
        "feii": ["True", "False"],
        "ntrial": ["10", "20"],
    },
}


def render_fantasy(text: str, k: dict) -> str:
    text, n = re.subn(r"min_fwhm_br\s*=\s*\d+", f"min_fwhm_br = {k['min_fwhm_br']}", text)
    assert n == 1, "fantasy: min_fwhm_br not found"
    text, n = re.subn(r"max_fwhm_br\s*=\s*\d+", f"max_fwhm_br = {k['max_fwhm_br']}", text)
    assert n == 1, "fantasy: max_fwhm_br not found"
    fe = "" if k["feii"] == "False" else " + create_feii_model(fwhm=1000, min_fwhm=300, max_fwhm=6000, offset=0, min_offset=-800, max_offset=800)"
    text, n = re.subn(r" \+ create_feii_model\([^)]*\)", lambda m: fe, text)
    assert n == 1, "fantasy: feii model not found"
    text, n = re.subn(r"s\.fit\(model,\s*ntrial=\d+\)", f"s.fit(model, ntrial={k['ntrial']})", text)
    assert n == 1, "fantasy: ntrial not found"
    return text


GELATO = {
    "file": "my_sdss.json",
    "base": ROOT / "Gelato" / "my_sdss.json",
    "defaults": {"FThresh": 0.95, "TieDispersion": False, "LineRegion": 300, "NBoot": 0},
    "candidates": [
        {},
        {"FThresh": 0.80},
        {"FThresh": 0.90},
        {"TieDispersion": True},
        {"LineRegion": 200},
        {"LineRegion": 500},
    ],
    "knob_values": {
        "FThresh": [0.80, 0.90, 0.95],
        "TieDispersion": [False, True],
        "LineRegion": [200, 300, 500],
    },
}


def render_gelato(text: str, k: dict) -> str:
    cfg = json.loads(text)
    cfg["NBoot"] = int(k["NBoot"])          # 0 skips the expensive bootstrap
    cfg["FThresh"] = float(k["FThresh"])
    cfg["LineRegion"] = int(k["LineRegion"])
    for g in cfg.get("EmissionGroups", []):
        if g.get("Name") == "AGN":
            g["TieDispersion"] = bool(k["TieDispersion"])
    return json.dumps(cfg, indent=4)


GLEAM = {
    "file": "gleamconfig.yaml",
    "base": ROOT / "Gleam" / "gleamconfig.yaml",
    "defaults": {"resolution": "8.0", "cont_width": "70", "tolerance": "26.0", "w": "3.0", "SN_limit": "2"},
    "candidates": [
        {},
        {"resolution": "3.0"},
        {"resolution": "5.0"},
        {"resolution": "3.0", "cont_width": "40"},
        {"w": "10.0"},
        {"tolerance": "15.0"},
        {"resolution": "3.0", "w": "10.0"},
    ],
    "knob_values": {
        "resolution": ["2.5", "3.0", "5.0", "8.0"],
        "cont_width": ["40", "70", "100"],
        "tolerance": ["15.0", "26.0", "40.0"],
        "w": ["3.0", "6.0", "10.0"],
        "SN_limit": ["2", "3"],
    },
}


def render_gleam(text: str, k: dict) -> str:
    text, n = re.subn(r"resolution:\s*[0-9.]+\s*Angstrom", f"resolution: {k['resolution']} Angstrom", text)
    assert n >= 1, "gleam: resolution not found"
    text, n = re.subn(r"cont_width:\s*[0-9.]+\s*Angstrom", f"cont_width: {k['cont_width']} Angstrom", text)
    assert n >= 1, "gleam: cont_width not found"
    text, n = re.subn(r"tolerance:\s*[0-9.]+\s*Angstrom", f"tolerance: {k['tolerance']} Angstrom", text)
    assert n >= 1, "gleam: tolerance not found"
    text, n = re.subn(r"\bw:\s*[0-9.]+\s*Angstrom", f"w: {k['w']} Angstrom", text)
    assert n >= 1, "gleam: w not found"
    text, n = re.subn(r"SN_limit:\s*[0-9.]+", f"SN_limit: {k['SN_limit']}", text)
    assert n >= 1, "gleam: SN_limit not found"
    return text


TOOLS = {
    "pyqsofit": (PYQ, render_pyqsofit),
    "badass": (BADASS, render_badass),
    "fantasy_agn": (FANTASY, render_fantasy),
    "gelato": (GELATO, render_gelato),
    "gleam": (GLEAM, render_gleam),
}
TOOL_ORDER = ["pyqsofit", "badass", "fantasy_agn", "gelato", "gleam"]


# ---------------------------------------------------------------------------
# Config materialisation
# ---------------------------------------------------------------------------
def _materialise(tool: str, knobs: dict) -> tuple[str, Path, str]:
    """Write a variant config; return (variant_name, path, rendered_text)."""
    spec, render = TOOLS[tool]
    merged = dict(spec["defaults"])
    merged.update(knobs)
    text = spec["base"].read_text()
    rendered = render(text, merged)
    key = "_".join(f"{k2}{v}" for k2, v in sorted(merged.items()) if k2 in knobs) or "base"
    key = re.sub(r"[^0-9A-Za-z_.=-]", "", key)[:80]
    variant = f"auto_{tool}_{key}"
    dest = CONFIGS / tool / variant / spec["file"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(rendered)
    return variant, dest, rendered


def enumerate_candidates(tool: str) -> list[dict]:
    return [dict(c) for c in TOOLS[tool][0]["candidates"]]


def neighbours(tool: str, knobs: dict) -> list[dict]:
    """Change one knob at a time to each of its other values."""
    out = []
    values = TOOLS[tool][0]["knob_values"]
    for name, vals in values.items():
        for v in vals:
            cand = dict(knobs)
            cand[name] = v
            if cand != knobs and cand not in out:
                out.append(cand)
    return out


# ---------------------------------------------------------------------------
# Running and scoring
# ---------------------------------------------------------------------------
def run_pipeline(tools: list[str], variants: dict[str, str], input_dir: Path, label: str,
                 repo: Path, jobs: int, runs_dir: Path, results_dir: Path) -> None:
    cmd = ["bash", str(repo / "run_pipeline.sh"), "--no-build", "--no-report",
           "--tools", " ".join(tools), "--jobs", str(jobs), "--label", label]
    for t, v in variants.items():
        cmd += ["--variant", f"{t}={v}"]
    env = {"INPUT_DIR": str(input_dir), "RUNS_DIR": str(runs_dir),
           "RESULTS_DIR": str(results_dir)}
    print(f"[auto_tune] run {label}: {' '.join(cmd)}")
    rc = subprocess.run(cmd, cwd=repo, env={**os.environ, **env}).returncode
    if rc != 0:
        # Do not abort the whole search for one failing candidate; the caller
        # scores it from whatever it produced (usually -> inf, so it loses).
        print(f"[auto_tune] WARNING: {label} exited with rc={rc}")


def read_scores(results: Path, label: str) -> dict:
    p = results / label / "scores.csv"
    if not p.exists():
        return {}
    import csv
    out = {}
    with p.open() as fh:
        for r in csv.DictReader(fh):
            out[(r["tag"], r["tool"])] = r
    return out


def objective(row: dict) -> float:
    for key in ("chi2_common", "chi2_red"):
        try:
            v = float(row.get(key, "nan"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(v) and v > 0:
            return v
    return float("inf")


def mean_objective(rows: dict, tool: str, tags: list[str]) -> float:
    vals = []
    for tag in tags:
        r = rows.get((tag, tool))
        if r is not None:
            vals.append(objective(r))
    vals = [v for v in vals if math.isfinite(v)]
    return sum(vals) / len(vals) if vals else float("inf")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def stage1(tool: str, tags: list[str], runs: Path, results: Path, repo: Path, input_dir: Path,
           jobs: int, workdir: Path,
           seen: set | None = None) -> list[tuple[dict, str, float]]:
    """Evaluate the full candidate grid; return [(knobs, best_variant, score)]."""
    seen = seen if seen is not None else set()
    evaluated = []
    for knobs in enumerate_candidates(tool):
        variant, _, rendered = _materialise(tool, knobs)
        if rendered in seen:
            continue
        seen.add(rendered)
        label = f"at_{tool}_{variant}"
        run_pipeline([tool], {tool: variant}, input_dir, label, repo, jobs, runs, results)
        rows = read_scores(results, label)
        score = mean_objective(rows, tool, tags)
        print(f"[auto_tune]   {tool:12s} {variant:40s} mean chi2_common = {score:.3f}")
        evaluated.append((knobs, variant, score))
        # keep the per-object scores for the final per-object map
        src = results / label / "scores.csv"
        if src.exists():
            shutil.copy2(src, workdir / f"{label}.scores.csv")
    evaluated.sort(key=lambda x: x[2])
    return evaluated


def refine(tool: str, best: dict, tags: list[str], runs: Path, results: Path, repo: Path,
           input_dir: Path, jobs: int, workdir: Path, rounds: int,
           seen: set | None = None) -> tuple[dict, str, float]:
    seen = seen if seen is not None else set()
    best_knobs, best_variant, best_score = best
    for rnd in range(1, rounds + 1):
        improved = False
        for cand in neighbours(tool, best_knobs):
            variant, _, rendered = _materialise(tool, cand)
            if variant == best_variant or rendered in seen:
                continue
            seen.add(rendered)
            label = f"at_{tool}_{variant}"
            run_pipeline([tool], {tool: variant}, input_dir, label, repo, jobs, runs, results)
            rows = read_scores(results, label)
            score = mean_objective(rows, tool, tags)
            print(f"[auto_tune]   round {rnd} {tool:12s} {variant:40s} mean chi2_common = {score:.3f}")
            if score < best_score - 1e-9:
                best_knobs, best_variant, best_score = cand, variant, score
                improved = True
                break
        if not improved:
            break
    return best_knobs, best_variant, best_score


def scoped_input(tags: list[str], runs_or_manifest_root: Path, dest: Path) -> Path:
    """Create an input dir with symlinks to the source spectra of ``tags``."""
    (dest / "input").mkdir(parents=True, exist_ok=True)
    for tag in tags:
        man = runs_or_manifest_root / tag / "manifest.json"
        src = None
        if man.exists():
            src = json.loads(man.read_text()).get("source")
        if not src:
            continue
        # Resolve to an absolute path: the manifest may store a relative path
        # (e.g. "input/spec.fits"), and a relative symlink target is resolved
        # against the *link's* directory, which would be broken.
        sp = Path(src)
        if not sp.is_absolute():
            sp = Path.cwd() / sp
        if sp.exists():
            link = dest / "input" / sp.name
            if not link.exists():
                link.symlink_to(sp.resolve())
    return dest / "input"


def discover_tags(runs: Path) -> list[str]:
    return sorted(p.name for p in runs.iterdir() if (p / "manifest.json").exists())


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tools", nargs="*", default=TOOL_ORDER, choices=TOOL_ORDER)
    p.add_argument("--limit", type=int, default=3, help="number of objects used for tuning")
    p.add_argument("--objects", nargs="*", default=None,
                   help="explicit object tags to tune on (overrides --limit)")
    p.add_argument("--rounds", type=int, default=2, help="coordinate-descent rounds per tool")
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--runs", type=Path, default=ROOT / "runs")
    p.add_argument("--results", type=Path, default=ROOT / "results")
    p.add_argument("--input", type=Path, default=ROOT / "input")
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--workdir", type=Path, default=ROOT / "work" / "auto_tune")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--stage1-only", action="store_true")
    p.add_argument("--no-prepare", action="store_true",
                   help="skip prepare_inputs (use when several searches run in parallel)")
    args = p.parse_args(argv)

    args.workdir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        for tool in args.tools:
            print(f"\n=== {tool} ({TOOLS[tool][0]['file']}) ===")
            for c in enumerate_candidates(tool):
                merged = dict(TOOLS[tool][0]["defaults"]); merged.update(c)
                print("  ", merged)
        return 0

    # Prepare (unless several searches already share one preparation).  This
    # picks up spectra newly dropped into input/ and writes runs/<tag>/manifest.json.
    if args.no_prepare:
        print("[auto_tune] skipping prepare (--no-prepare)")
    else:
        print("[auto_tune] preparing inputs")
        subprocess.run([sys.executable, str(ROOT / "pipeline" / "prepare_inputs.py"),
                        "--fits", str(args.input), "--out", str(args.runs),
                        "--gelato-json", str(ROOT / "Gelato" / "my_sdss.json"),
                        "--gleam-static", str(ROOT / "Gleam")], cwd=args.repo, check=True)

    tags = discover_tags(args.runs)
    if not tags:
        print(f"no spectra could be prepared from {args.input}")
        return 1
    if args.objects:
        tune_tags = [t for t in args.objects if t in tags]
        if not tune_tags:
            print(f"none of --objects {args.objects} are prepared (available: {tags})")
            return 1
    else:
        tune_tags = tags[: args.limit]
    print(f"[auto_tune] tuning on {tune_tags} ({len(tags)} available)")

    # Scope the tuning runs to the chosen objects.
    scope = args.workdir / "tuning_input"
    if scope.exists():
        shutil.rmtree(scope)
    input_dir = scoped_input(tune_tags, args.runs, scope)

    best_per_tool: dict[str, dict] = {}
    for tool in args.tools:
        seen: set = set()
        evaluated = stage1(tool, tune_tags, args.runs, args.results, args.repo, input_dir,
                           args.jobs, args.workdir, seen=seen)
        if args.rounds > 0:
            chosen = refine(tool, evaluated[0], tune_tags, args.runs, args.results, args.repo,
                            input_dir, args.jobs, args.workdir, args.rounds, seen=seen)
        else:
            chosen = evaluated[0]
        best_per_tool[tool] = {"knobs": chosen[0], "mean_chi2_common": chosen[2]}
        print(f"[auto_tune] {tool}: best = {chosen[0]}  (mean chi2_common={chosen[2]:.3f})")

    # Materialise the winners under a stable variant name and re-run everything.
    final_variants = {}
    for tool, info in best_per_tool.items():
        variant, _, _ = _materialise(tool, info["knobs"])
        info["variant"] = variant
        final_variants[tool] = variant
    (args.workdir / "best_configs.json").write_text(json.dumps(best_per_tool, indent=2))
    print(f"[auto_tune] wrote {args.workdir / 'best_configs.json'}")

    if not args.stage1_only:
        print("[auto_tune] final full-quality run with the winning configurations")
        cmd = ["bash", str(args.repo / "run_pipeline.sh"), "--no-build",
               "--tools", " ".join(args.tools), "--jobs", str(args.jobs)]
        for t, v in final_variants.items():
            cmd += ["--variant", f"{t}={v}"]
        env = {**os.environ, "INPUT_DIR": str(args.input),
               "RUNS_DIR": str(args.runs), "RESULTS_DIR": str(args.results)}
        subprocess.run(cmd, cwd=args.repo, env=env, check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
