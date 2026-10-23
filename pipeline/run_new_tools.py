#!/usr/bin/env python3
"""Run the NIR/MIR/FIR/SED tools over the canonical source registry.

Examples
--------
    .venv/bin/python pipeline/run_new_tools.py --list
    .venv/bin/python pipeline/run_new_tools.py --tools ir_linefit pahfit_mir
    .venv/bin/python pipeline/run_new_tools.py --only NGC253_z_0.0008 --force
    .venv/bin/python pipeline/run_new_tools.py --tools cigale_sed --cigale-models skirtor2016

Outputs are always ``outputs/<source_key>/<tool>/``.  Inputs are never copied
into outputs; PyQSOFit/pPXF-native files are generated under
``work/prepared/<source_key>/``.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pipeline.io_layout import (  # noqa: E402
    OUTPUT_ROOT, WORK_ROOT, ensure_output, iter_sources, load_source,
    output_dir, prepared_dir, source_files,
)

MIRI_ALL = ",".join([
    "jwst.miri.mrs.ch1.A", "jwst.miri.mrs.ch1.B", "jwst.miri.mrs.ch1.C",
    "jwst.miri.mrs.ch2.A", "jwst.miri.mrs.ch2.B", "jwst.miri.mrs.ch2.C",
    "jwst.miri.mrs.ch3.A", "jwst.miri.mrs.ch3.B", "jwst.miri.mrs.ch3.C",
    "jwst.miri.mrs.ch4.A", "jwst.miri.mrs.ch4.B", "jwst.miri.mrs.ch4.C",
])
SPITZER_IRS = ",".join([
    "spitzer.irs.sl.2", "spitzer.irs.sl.1",
    "spitzer.irs.ll.2", "spitzer.irs.ll.1",
])
ALL_TOOLS = ("ir_linefit", "pyqsofit_uv", "ppxf_host", "gandalf_line",
             "nir_linefit", "pahfit_mir", "fir_linefit", "crossband",
             "cigale_sed", "agnfitter_sed", "s3fit_line")


def log(msg: str):
    print(msg, flush=True)


def run(cmd: list[str], logpath: Path, env: dict | None = None) -> int:
    logpath.parent.mkdir(parents=True, exist_ok=True)
    e = os.environ.copy()
    if env:
        e.update(env)
    log(f"$ {' '.join(str(c) for c in cmd)}")
    with logpath.open("w") as fh:
        fh.write("$ " + " ".join(str(c) for c in cmd) + "\n")
        fh.flush()
        p = subprocess.run([str(c) for c in cmd], cwd=ROOT, env=e,
                           stdout=fh, stderr=subprocess.STDOUT)
    return p.returncode


def prep_pyqsofit(src: dict) -> Path:
    from pipeline.prepare_inputs import read_spectrum, write_pyqsofit
    paths = source_files(src, "spectrum")
    if not paths:
        raise FileNotFoundError("no spectrum role")
    out = prepared_dir(src["key"], "pyqsofit")
    out.mkdir(parents=True, exist_ok=True)
    spec = read_spectrum(paths[0])
    write_pyqsofit(spec, out / "spectrum.fits")
    return out


def tool_ir(src: dict, out: Path, logp: Path) -> int:
    paths = source_files(src, "spectrum") + source_files(src, "spectra") \
        + source_files(src, "mir_table") + source_files(src, "pacs")
    paths = [p for p in paths if p.exists()]
    if not paths:
        return _skip("no spectrum")
    cmd = [sys.executable, "-m", "pipeline_ir.run", "--fits", *[str(p) for p in paths],
           "--z", str(src["z"]), "--out", str(out)]
    return run(cmd, logp, env={"PYTHONPATH": f"{ROOT / 'Tools'}:{ROOT}"})


def tool_pyqsofit(src: dict, out: Path, logp: Path) -> int:
    inp = prep_pyqsofit(src)
    return run([str(ROOT / "Pipelines" / "run_pyqsofit_uv_docker.sh"), str(inp), str(out)], logp)


def tool_ppxf(src: dict, out: Path, logp: Path) -> int:
    inp = prep_pyqsofit(src)
    return run([str(ROOT / "Pipelines" / "run_ppxf_host_docker.sh"), str(inp), str(out)], logp)


def tool_gandalf(src: dict, out: Path, logp: Path) -> int:
    inp = prep_pyqsofit(src)
    return run([str(ROOT / "Pipelines" / "run_gandalf_line_docker.sh"), str(inp), str(out), str(src["key"])], logp)


def tool_nir(src: dict, out: Path, logp: Path) -> int:
    raw = Path(src["_path"]) / "raw"
    rc = run([str(ROOT / "Pipelines" / "run_nir_linefit_docker.sh"), str(raw), str(out), str(src["z"])], logp)
    centered = source_files(src, "centered")
    if centered:
        sub = out / "centered"
        rc |= run([str(ROOT / "Pipelines" / "run_nir_linefit_docker.sh"), str(centered[0].parent),
                   str(sub), str(src["z"])], logp.with_name(logp.stem + "_centered.log"))
    psf = source_files(src, "centered_psf")
    if psf:
        sub = out / "psf"
        rc |= run([str(ROOT / "Pipelines" / "run_nir_linefit_docker.sh"), str(psf[0].parent),
                   str(sub), str(src["z"])], logp.with_name(logp.stem + "_psf.log"))
    return rc


def _pahfit_config_arg(name: str) -> list[str]:
    """Pass a variant config into the container when the file exists."""
    host = ROOT / "configs" / "pahfit_mir" / name / "config.json"
    if host.exists():
        return ["--config", f"/app/configs/pahfit_mir/{name}/config.json"]
    return []


def tool_pahfit(src: dict, out: Path, logp: Path) -> int:
    raw = Path(src["_path"]) / "raw"
    variants = src.get("pahfit_variants")
    if variants:
        rc = 0
        for v in variants:
            sub = out / v["name"]
            # Optional seed fit, then warm-start the full fit from its ECSV.
            if v.get("seed_args"):
                seed = sub / "seed"
                cmd = [str(ROOT / "Pipelines" / "run_pahfit_mir_docker.sh"), str(raw), str(seed),
                       str(src["z"]), *v.get("seed_args", [])]
                if src.get("kind") == "jwst_miri":
                    cmd += ["--instrument", MIRI_ALL]
                rc |= run(cmd, logp.with_name(logp.stem + f"_{v['name']}_seed.log"))
            if v.get("seed_from"):
                seed_dir = sub / "seed"
                seed_dir.mkdir(parents=True, exist_ok=True)
                src_ecsv = out / v["seed_from"] / "pahfit_output.ecsv"
                if src_ecsv.exists():
                    (seed_dir / "pahfit_output.ecsv").write_bytes(src_ecsv.read_bytes())
            cmd = [str(ROOT / "Pipelines" / "run_pahfit_mir_docker.sh"), str(raw), str(sub),
                   str(src["z"]), *_pahfit_config_arg(v["name"]), *v.get("args", [])]
            if src.get("kind") == "jwst_miri":
                cmd += ["--instrument", MIRI_ALL]
            if v.get("init_from"):
                cmd += ["--init-from", "/app/output/" + v["init_from"]]
            rc |= run(cmd, logp.with_name(logp.stem + f"_{v['name']}.log"))
        return rc
    args = list(src.get("pahfit_args", []))
    if "spitzer_irs" in str(src.get("kind", "")):
        args = ["--tbl", "--smooth-um", "0.1", "--instrument", SPITZER_IRS]
    if src.get("kind") == "jwst_miri":
        args += ["--instrument", MIRI_ALL]
    return run([str(ROOT / "Pipelines" / "run_pahfit_mir_docker.sh"), str(raw), str(out),
                str(src["z"]), *_pahfit_config_arg("default"), *args], logp)


def tool_fir(src: dict, out: Path, logp: Path) -> int:
    raw = Path(src["_path"]) / "raw"
    pacs = source_files(src, "pacs")
    spec = source_files(src, "spectrum")
    if pacs:
        # run_fir prefers .fits.gz in the directory; pass a directory containing
        # only the PACS products to avoid mixing HIFI/IRS files.
        stage = WORK_ROOT / src["key"] / "fir"
        stage.mkdir(parents=True, exist_ok=True)
        for p in pacs:
            (stage / p.name).write_bytes(p.read_bytes())
        target = stage
    elif spec:
        target = spec[0]
    else:
        return _skip("no FIR spectrum")
    return run([str(ROOT / "Pipelines" / "run_fir_linefit_docker.sh"), str(target), str(out), str(src["z"])], logp)


def tool_crossband(src: dict, out: Path, logp: Path) -> int:
    paths = source_files(src, "ratios")
    if not paths and src.get("crossband") == "generated":
        gen = ROOT / "pipeline" / "build_crossband_from_outputs.py"
        r = run([sys.executable, str(gen), src["key"]], logp.with_name("crossband_build.log"))
        if r:
            return r
        candidate = Path(src["_path"]) / "crossband.csv"
        if candidate.exists():
            paths = [candidate]
    if not paths:
        return _skip("no crossband input")
    return run([str(ROOT / "Pipelines" / "run_crossband_docker.sh"), str(paths[0]), str(out)], logp)


def tool_agnfitter(src: dict, out: Path, logp: Path) -> int:
    inp = Path(src["_path"]) / "photometry"
    if not (inp / "photometry.txt").exists():
        return _skip("no photometry")
    return run([str(ROOT / "Pipelines" / "run_agnfitter_sed_docker.sh"), str(inp), str(out)], logp)


def tool_s3fit(src: dict, out: Path, logp: Path, config: str | None = None,
               n_mocks: int | None = None, mode: str | None = None) -> int:
    cmd = [str(ROOT / "Pipelines" / "run_s3fit_line_docker.sh"),
           str(Path(src["_path"])), str(out)]
    if src.get("z") is not None:
        cmd += ["--z", str(src["z"])]
    if config:
        cmd += ["--config", config]
    if n_mocks is not None:
        cmd += ["--n-mocks", str(n_mocks)]
    if mode:
        cmd += ["--mode", mode]
    # The runner auto-mounts the sibling pyqsofit_uv output when available.
    return run(cmd, logp)


def tool_cigale(src: dict, out: Path, logp: Path, models: list[str]) -> int:
    inp = Path(src["_path"]) / "photometry"
    if not (inp / "photometry.txt").exists():
        return _skip("no photometry")
    rc = 0
    for model in models:
        sub = out / model
        rc |= run([str(ROOT / "Pipelines" / "run_cigale_sed_docker.sh"), str(inp), str(sub)],
                  logp.with_name(logp.stem + f"_{model}.log"),
                  env={"CIGALE_AGN_MODEL": model})
    # Aggregate the model-family spread from the per-model summaries.
    import csv as _csv
    rows = []
    for model in models:
        f = out / model / "sed_summary.csv"
        if f.exists():
            with f.open() as fh:
                rows += list(_csv.DictReader(fh))
    if rows:
        with (out / "model_family.csv").open("w", newline="") as fh:
            w = _csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        keys = ("fracAGN", "agn_luminosity_W", "agn_torus_luminosity_W",
                "dust_luminosity_W", "m_star_Msun", "sfr_Msun_per_yr")
        spread = {}
        for k in keys:
            vals = []
            for r in rows:
                try:
                    vals.append(float(r[k]))
                except Exception:
                    pass
            if vals:
                spread[k] = {"min": min(vals), "max": max(vals),
                             "spread": max(vals) - min(vals)}
        (out / "model_family_spread.json").write_text(__import__("json").dumps(spread, indent=2))
    return rc


def _skip(msg: str) -> int:
    log(f"[skip] {msg}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tools", nargs="*", choices=ALL_TOOLS, default=list(ALL_TOOLS))
    p.add_argument("--only", nargs="*", default=None, help="source keys or globs")
    p.add_argument("--list", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--cigale-models", default="skirtor2016",
                   help="comma-separated CIGALE AGN models")
    p.add_argument("--s3fit-config", default=None,
                   help="S3Fit config directory (default: configs/s3fit_line/default)")
    p.add_argument("--s3fit-n-mocks", type=int, default=None,
                   help="S3Fit Monte-Carlo mock spectra (default from fit_config.json: 10)")
    p.add_argument("--s3fit-mode", choices=("spec+sed", "spec"), default=None,
                   help="S3Fit fitting mode (default from fit_config.json)")
    args = p.parse_args(argv)
    if args.list:
        for s in iter_sources():
            print(s["key"], s.get("kind"), "tools=" + ",".join(s.get("tools", [])))
        return 0
    pats = set(args.only or [])
    sources = [s for s in iter_sources()
               if not pats or s["key"] in pats or any(__import__("fnmatch").fnmatch(s["key"], q) for q in pats)]
    if not sources:
        log("no sources selected")
        return 1
    rc = 0
    for src in sources:
        key = src["key"]
        log(f"\n=== {key}  z={src['z']}  kind={src.get('kind')}")
        for tool in args.tools:
            if tool not in src.get("tools", []):
                continue
            out = output_dir(key, tool)
            if args.force and out.exists():
                import shutil
                shutil.rmtree(out)
            ensure_output(key, tool)
            logp = WORK_ROOT.parent / "logs" / key / f"{tool}.log"
            log(f"[{key}] {tool} -> {out.relative_to(ROOT)}")
            if args.dry_run:
                continue
            fn = {
                "ir_linefit": lambda: tool_ir(src, out, logp),
                "pyqsofit_uv": lambda: tool_pyqsofit(src, out, logp),
                "ppxf_host": lambda: tool_ppxf(src, out, logp),
                "gandalf_line": lambda: tool_gandalf(src, out, logp),
                "nir_linefit": lambda: tool_nir(src, out, logp),
                "pahfit_mir": lambda: tool_pahfit(src, out, logp),
                "fir_linefit": lambda: tool_fir(src, out, logp),
                "crossband": lambda: tool_crossband(src, out, logp),
                "cigale_sed": lambda: tool_cigale(src, out, logp,
                                                   [x.strip() for x in args.cigale_models.split(",") if x.strip()]),
                "agnfitter_sed": lambda: tool_agnfitter(src, out, logp),
                "s3fit_line": lambda: tool_s3fit(src, out, logp,
                                                 args.s3fit_config, args.s3fit_n_mocks,
                                                 args.s3fit_mode),
            }[tool]
            try:
                r = fn()
            except Exception as exc:  # noqa: BLE001
                log(f"[error] {key}/{tool}: {exc}")
                r = 1
            if r:
                log(f"[failed] {key}/{tool} rc={r}  log={logp}")
                rc = 1
            else:
                log(f"[ok] {key}/{tool}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
