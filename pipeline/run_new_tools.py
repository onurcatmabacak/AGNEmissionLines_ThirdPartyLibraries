#!/usr/bin/env python3
"""Run the NIR/MIR/FIR/SED and RXTE/PCA tools over the canonical source registry.

Examples
--------
    .venv/bin/python pipeline/run_new_tools.py --list
    .venv/bin/python pipeline/run_new_tools.py --tools ir_linefit pahfit_mir
    .venv/bin/python pipeline/run_new_tools.py --only NGC253_z_0.0008 --force
    .venv/bin/python pipeline/run_new_tools.py --tools cigale_sed --cigale-models skirtor2016

Outputs are always ``outputs/<tool>/<source_key>/``.  Inputs are never copied
into outputs; PyQSOFit/pPXF-native files are generated under
``work/prepared/<source_key>/``.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pipeline.io_layout import (  # noqa: E402
    OUTPUT_ROOT, WORK_ROOT, ensure_output, iter_sources, load_source,
    output_dir, prepared_dir, source_files,
)
from pipeline.plan_analysis import make_plan  # noqa: E402
from pipeline.tool_capabilities import THREADS, is_threaded, DEPENDENT_TOOLS  # noqa: E402
from pipeline.resources import (  # noqa: E402
    ResourceSnapshot, env_for_threads, jobs_for_singles, threads_for_tool,
)

PREREQUISITES = {
    "s3fit_line": ["pyqsofit_uv"],
    "crossmission": ["xmm_xspec", "rxte_xspec", "optical_linefit", "pyqsofit_uv"],
    "crossband": ["pahfit_mir", "fir_linefit"],
}

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
ALL_TOOLS = ("ir_linefit", "pyqsofit_uv", "qsofitmore_line", "pyqsofitspec_line", "ppxf_host",
             "gandalf_line", "nir_linefit", "pahfit_mir", "fir_linefit", "cafe_line",
             "crossband", "cigale_sed", "agnfitter_sed", "s3fit_line", "galspec_line",
             "qgfit", "sheap_line", "manga_dap", "xmm_xspec", "rxte_xspec",
             "crossmission", "optical_linefit", "manga_dap_full", "xmm_sas_raw", "bxa_xspec", "radio_line", "submm_line")

# Tools that can use more than one CPU thread.  They are run one at a time in
# --phased mode so that they get the full machine; the remaining tools are then
# run concurrently at one thread each.
MULTICORE_TOOLS = {t for t, n in THREADS.items() if n > 1}


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
    paths = source_files(src, "spectrum") or source_files(src, "optical_spectrum")
    if not paths:
        raise FileNotFoundError("no spectrum/optical_spectrum role")
    out = prepared_dir(src["key"], "pyqsofit")
    out.mkdir(parents=True, exist_ok=True)
    spec = read_spectrum(paths[0])
    # Canonical source redshift wins over any missing/nominal FITS header value.
    if src.get("z") is not None:
        spec["z"] = float(src["z"])
    # Atomic replacement: Snakemake can prepare this shared file from several
    # rules concurrently; a reader must never see a half-written FITS.
    import os
    import tempfile
    fd, tmp = tempfile.mkstemp(prefix="spectrum.", suffix=".fits", dir=out)
    os.close(fd)
    try:
        write_pyqsofit(spec, Path(tmp))
        os.replace(tmp, out / "spectrum.fits")
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
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
    return run(
        [str(ROOT / "pipeline" / "runners" / "run_pyqsofit_uv_docker.sh"), str(inp), str(out)],
        logp,
        env={"PYQSOFIT_SOURCE_KEY": str(src["key"])},
    )


def tool_optical_linefit(src: dict, out: Path, logp: Path) -> int:
    """Local H-beta/[O III] fit; used where a global QSO fit misallocates flux."""
    files = source_files(src, "xshooter_spectrum") or source_files(src, "optical_spectrum") or source_files(src, "spectrum")
    if not files:
        return _skip("no optical spectrum")
    cmd = [str(ROOT / "pipeline" / "runners" / "run_optical_linefit_docker.sh"),
           str(files[0]), str(out), "--z", str(src["z"]), "--name", str(src["key"])]
    return run(cmd, logp)


def tool_qsofitmore(src: dict, out: Path, logp: Path, config: str | None = None,
                    mc_trails: int | None = None) -> int:
    """QSOFITMORE UV/optical fit on the raw SDSS spectrum.

    The raw COADD is used rather than the PyQSOFit prepared copy because the
    preparation sanitises zero-IVAR pixels to the median variance, which would
    silently extend the red end past 6564 A and pull in the H-alpha complex.
    """
    raw = Path(src["_path"]) / "raw"
    if not raw.exists():
        raw = prep_pyqsofit(src)
    cmd = [str(ROOT / "pipeline" / "runners" / "run_qsofitmore_line_docker.sh"),
           str(raw), str(out)]
    if config:
        cmd += ["--config", str(config)]
    if mc_trails is not None:
        cmd += ["--mc-trails", str(mc_trails)]
    if src.get("z") is not None:
        cmd += ["--z", str(src["z"])]
    return run(cmd, logp, env={"QSOFITMORE_SOURCE_KEY": str(src["key"])})


def tool_pyqsofitspec(src: dict, out: Path, logp: Path, nboot: int | None = None,
                      config: str | None = None) -> int:
    """PyQSOFitSpec bootstrap line fit (skew-normal profiles) on the prepared spectrum."""
    inp = prep_pyqsofit(src)
    cmd = [str(ROOT / "pipeline" / "runners" / "run_pyqsofitspec_line_docker.sh"),
           str(inp), str(out), "--name", str(src["name"]), "--z", str(src["z"])]
    cmd += ["--config", config or str(ROOT / "configs" / "pyqsofitspec_line" / "default")]
    if nboot is not None:
        cmd += ["--nboot", str(nboot)]
    return run(cmd, logp)


def tool_manga_dap(src: dict, out: Path, logp: Path, full: bool = False) -> int:
    """Official MaNGA DAP; full=True runs the all-spaxel long path."""
    refs = source_files(src, "manga_maps_reference")
    if not refs:
        return _skip("no published DAP MAPS reference")
    cmd = [str(ROOT / "pipeline" / "runners" / "run_manga_dap_docker.sh"),
           str(Path(src["_path"])), str(out),
           "--reference", str(refs[0])]
    if full:
        cmd += ["--full"]
    else:
        cmd += ["--n-bins", "9"]
    return run(cmd, logp)


def tool_xmm_sas_raw(src: dict, out: Path, logp: Path) -> int:
    files = source_files(src, "xray_spectrum")
    if not files:
        return _skip("no raw SAS products")
    return run([str(ROOT / "pipeline" / "runners" / "run_xmm_sas_fit_docker.sh"),
                str(out), "--z", str(src["z"])], logp)


def tool_xmm(src: dict, out: Path, logp: Path) -> int:
    """Official XMM-Newton EPIC PPS fit (HEASoft/PyXspec)."""
    xray = src.get("xray", {}).get("dir")
    if not xray:
        return _skip("no XMM xray directory")
    inp = Path(src["_path"]) / xray
    cmd = [str(ROOT / "pipeline" / "runners" / "run_xmm_xspec_docker.sh"),
           str(inp), str(out), "--source-key", str(src["key"])]
    if src.get("z") is not None:
        cmd += ["--redshift", str(src["z"])]
    return run(cmd, logp)


def tool_rxte(src: dict, out: Path, logp: Path) -> int:
    """Official RXTE/PCA stdprod fit (HEASoft/PyXspec)."""
    paths = source_files(src, "xray_pca_source")
    if not paths:
        return _skip("no RXTE/PCA source spectrum")
    inp = paths[0].parent
    cmd = [str(ROOT / "pipeline" / "runners" / "run_rxte_xspec_docker.sh"),
           str(inp), str(out), "--source-key", str(src["key"])]
    if src.get("name"):
        cmd += ["--source-name", str(src["name"])]
    if src.get("z") is not None:
        cmd += ["--redshift", str(src["z"])]
    if src.get("rxte_config"):
        cmd += ["--config", str(ROOT / "configs" / "rxte_xspec" / str(src["rxte_config"]))]
    return run(cmd, logp)


def tool_crossmission(src: dict, out: Path, logp: Path) -> int:
    """Same-object X-ray Fe K-alpha vs UV/optical line comparison."""
    if not (source_files(src, "spectrum") or source_files(src, "optical_spectrum")):
        return _skip("no UV/optical spectrum")
    if not (out.parent / "pyqsofit_uv").exists():
        return _skip("no pyqsofit_uv output")
    cmd = [sys.executable, str(ROOT / "pipeline" / "compare_xray_optical.py"),
           "--source", str(src["key"]), "--out", str(out)]
    return run(cmd, logp)


def tool_ppxf(src: dict, out: Path, logp: Path) -> int:
    inp = prep_pyqsofit(src)
    return run([str(ROOT / "pipeline" / "runners" / "run_ppxf_host_docker.sh"), str(inp), str(out)], logp)


def tool_gandalf(src: dict, out: Path, logp: Path) -> int:
    inp = prep_pyqsofit(src)
    return run([str(ROOT / "pipeline" / "runners" / "run_gandalf_line_docker.sh"), str(inp), str(out), str(src["key"])], logp)


def tool_galspec(src: dict, out: Path, logp: Path, config: str | None = None,
                 sampler: str | None = None, mcmc_steps: int | None = None,
                 nwalkers: int | None = None, nburn: int | None = None) -> int:
    cmd = [str(ROOT / "pipeline" / "runners" / "run_galspec_line_docker.sh"),
           str(Path(src["_path"])), str(out), "--object", str(src["key"])]
    if src.get("z") is not None:
        cmd += ["--z", str(src["z"])]
    if config:
        cmd += ["--config", config]
    if sampler:
        cmd += ["--sampler", sampler]
    if mcmc_steps is not None:
        cmd += ["--mcmc-steps", str(mcmc_steps)]
    if nwalkers is not None:
        cmd += ["--nwalkers", str(nwalkers)]
    if nburn is not None:
        cmd += ["--nburn", str(nburn)]
    return run(cmd, logp)


def tool_qgfit(src: dict, out: Path, logp: Path) -> int:
    """Run QGfit on the canonical source directory."""
    cmd = [str(ROOT / "pipeline" / "runners" / "run_qgfit_docker.sh"),
           str(Path(src["_path"])), str(out)]
    if src.get("z") is not None:
        cmd += ["--z", str(src["z"])]
    return run(cmd, logp)


def tool_sheap(src: dict, out: Path, logp: Path) -> int:
    """Run SHEAP on the canonical source directory (CPU JAX)."""
    cmd = [str(ROOT / "pipeline" / "runners" / "run_sheap_line_docker.sh"),
           str(Path(src["_path"])), str(out)]
    if src.get("z") is not None:
        cmd += ["--z", str(src["z"])]
    return run(cmd, logp)


def tool_cafe(src: dict, out: Path, logp: Path) -> int:
    inp = Path(src["_path"]) / "raw"
    if not list(inp.glob("*_x1d.fits")):
        return _skip("no JWST x1d for CAFE")
    cmd = [str(ROOT / "pipeline" / "runners" / "run_cafe_line_docker.sh"),
           str(inp), str(out), str(src["z"])]
    extra = list(src.get("cafe_args", []))
    if extra:
        cmd += extra
    else:
        cmd += ["--max-wave", "27.8", "--no-outlier-clip",
                "--mc-samples", "200", "--mc-seed", "20250101"]
    return run(cmd, logp)


def tool_nir(src: dict, out: Path, logp: Path) -> int:
    raw = Path(src["_path"]) / "raw"
    rc = run([str(ROOT / "pipeline" / "runners" / "run_nir_linefit_docker.sh"), str(raw), str(out), str(src["z"])], logp)
    centered = source_files(src, "centered")
    if centered:
        sub = out / "centered"
        rc |= run([str(ROOT / "pipeline" / "runners" / "run_nir_linefit_docker.sh"), str(centered[0].parent),
                   str(sub), str(src["z"])], logp.with_name(logp.stem + "_centered.log"))
    psf = source_files(src, "centered_psf")
    if psf:
        sub = out / "psf"
        rc |= run([str(ROOT / "pipeline" / "runners" / "run_nir_linefit_docker.sh"), str(psf[0].parent),
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
                cmd = [str(ROOT / "pipeline" / "runners" / "run_pahfit_mir_docker.sh"), str(raw), str(seed),
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
            cmd = [str(ROOT / "pipeline" / "runners" / "run_pahfit_mir_docker.sh"), str(raw), str(sub),
                   str(src["z"]), *_pahfit_config_arg(v.get("config", v["name"])),
                   *v.get("args", [])]
            if src.get("kind") == "jwst_miri":
                cmd += ["--instrument", MIRI_ALL]
            if v.get("init_from"):
                cmd += ["--init-from", "/app/output/" + v["init_from"]]
            rc |= run(cmd, logp.with_name(logp.stem + f"_{v['name']}.log"))
        return rc
    args = list(src.get("pahfit_args", []))
    if "spitzer_irs" in str(src.get("kind", "")):
        # Keep the common-aperture convention but do not discard source args.
        args = (["--tbl", "--smooth-um", "0.1",
                 "--tbl-aperture-arcsec2", "1.0", "--instrument", SPITZER_IRS]
                + args)
    if src.get("kind") == "jwst_miri":
        args += ["--instrument", MIRI_ALL]
    cfg_name = src.get("pahfit_config", "default")
    return run([str(ROOT / "pipeline" / "runners" / "run_pahfit_mir_docker.sh"), str(raw), str(out),
                str(src["z"]), *_pahfit_config_arg(cfg_name), *args], logp)


def tool_fir(src: dict, out: Path, logp: Path) -> int:
    raw = Path(src["_path"]) / "raw"
    pacs = source_files(src, "pacs")
    spec = source_files(src, "spectrum")
    if pacs:
        # run_fir prefers .fits.gz in the directory; pass a directory containing
        # only the PACS products to avoid mixing HIFI/IRS files.
        import shutil
        stage = WORK_ROOT / src["key"] / "fir"
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir(parents=True, exist_ok=True)
        for p in pacs:
            (stage / p.name).write_bytes(p.read_bytes())
        target = stage
    elif spec:
        target = spec[0]
    else:
        return _skip("no FIR spectrum")
    return run([str(ROOT / "pipeline" / "runners" / "run_fir_linefit_docker.sh"), str(target), str(out), str(src["z"])], logp)


def tool_crossband(src: dict, out: Path, logp: Path) -> int:
    paths = source_files(src, "ratios")
    if not paths and src.get("crossband") == "generated":
        gen = ROOT / "pipeline" / "build_crossband_from_outputs.py"
        r = run([sys.executable, str(gen), src["key"]], logp.with_name("crossband_build.log"))
        if r:
            return r
        candidate = prepared_dir(src["key"], "crossband") / "crossband.csv"
        if candidate.exists():
            paths = [candidate]
    if not paths:
        return _skip("no crossband input")
    return run([str(ROOT / "pipeline" / "runners" / "run_crossband_docker.sh"), str(paths[0]), str(out)], logp)


def tool_agnfitter(src: dict, out: Path, logp: Path) -> int:
    inp = Path(src["_path"]) / "photometry"
    if not (inp / "photometry.txt").exists():
        return _skip("no photometry")
    return run([str(ROOT / "pipeline" / "runners" / "run_agnfitter_sed_docker.sh"), str(inp), str(out)], logp)


def tool_s3fit(src: dict, out: Path, logp: Path, config: str | None = None,
               n_mocks: int | None = None, mode: str | None = None,
               threads: int | None = None) -> int:
    cmd = [str(ROOT / "pipeline" / "runners" / "run_s3fit_line_docker.sh"),
           str(Path(src["_path"])), str(out)]
    if src.get("z") is not None:
        cmd += ["--z", str(src["z"])]
    if config:
        cmd += ["--config", config]
    if n_mocks is not None:
        cmd += ["--n-mocks", str(n_mocks)]
    if mode:
        cmd += ["--mode", mode]
    if threads is not None:
        cmd += ["--threads", str(threads)]
    # The runner auto-mounts the sibling pyqsofit_uv output when available.
    return run(cmd, logp)


def tool_cigale(src: dict, out: Path, logp: Path, models: list[str]) -> int:
    inp = Path(src["_path"]) / "photometry"
    if not (inp / "photometry.txt").exists():
        return _skip("no photometry")
    rc = 0
    for model in models:
        sub = out / model
        rc |= run([str(ROOT / "pipeline" / "runners" / "run_cigale_sed_docker.sh"), str(inp), str(sub)],
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


class SkipTool(Exception):
    """Raised when a tool has no applicable input; not a failure."""


def _skip(msg: str):
    raise SkipTool(msg)


def _job_tools(src: dict, args) -> list[str]:
    if args.auto:
        plan = make_plan(src, goal=args.goal, max_cost=args.max_cost,
                         include_expensive=args.include_expensive)
        return [c["tool"] for c in plan["selected"]]
    return [t for t in args.tools if t in src.get("tools", [])]


def _run_phased(sources: list[dict], args) -> int:
    """One multicore job at a time, then single-core jobs concurrently.

    Each worker is a fresh ``run_new_tools.py`` subprocess, so logs and Docker
    mounts stay isolated and an exception in one tool cannot corrupt another.
    """
    multi = set((args.multicore_tools or "").split(",")) if args.multicore_tools else set(MULTICORE_TOOLS)
    multi = {x.strip() for x in multi if x.strip()}
    unknown = multi - set(THREADS)
    if unknown:
        log(f"[error] unknown --multicore-tools: {', '.join(sorted(unknown))}")
        return 2
    jobs = []
    for src in sources:
        key = src["key"]
        for tool in _job_tools(src, args):
            out = output_dir(key, tool)
            logp = WORK_ROOT.parent / "logs" / key / f"{tool}.log"
            jobs.append((src, tool, out, logp))
    if args.dry_run:
        have = {(s["key"], t) for s, t, _, _ in jobs}
        for src, tool, out, logp in jobs:
            if tool in multi:
                stage = f"multicore/{threads_for_tool(tool, args.threads, ResourceSnapshot.detect())}"
            else:
                stage = "final" if tool in DEPENDENT_TOOLS else "parallel"
            log(f"[{stage}] {src['key']}/{tool} -> {out.relative_to(ROOT)}")
        for src, tool, out, logp in jobs:
            for dep in PREREQUISITES.get(tool, []):
                if dep in src.get("tools", []) and (src["key"], dep) not in have:
                    log(f"[producer] {src['key']}/{dep} -> {output_dir(src['key'], dep).relative_to(ROOT)}")
                    have.add((src["key"], dep))
        return 0
    base = [sys.executable, str(ROOT / "pipeline" / "run_new_tools.py")]
    common = []
    if args.force:
        common.append("--force")
    if args.cigale_models:
        common += ["--cigale-models", args.cigale_models]
    if args.s3fit_config:
        common += ["--s3fit-config", args.s3fit_config]
    if args.s3fit_n_mocks is not None:
        common += ["--s3fit-n-mocks", str(args.s3fit_n_mocks)]
    if args.s3fit_mode:
        common += ["--s3fit-mode", args.s3fit_mode]
    if args.galspec_config:
        common += ["--galspec-config", args.galspec_config]
    if args.galspec_sampler:
        common += ["--galspec-sampler", args.galspec_sampler]
    if args.galspec_mcmc_steps is not None:
        common += ["--galspec-mcmc-steps", str(args.galspec_mcmc_steps)]
    if args.galspec_nwalkers is not None:
        common += ["--galspec-nwalkers", str(args.galspec_nwalkers)]
    if args.galspec_nburn is not None:
        common += ["--galspec-nburn", str(args.galspec_nburn)]
    if args.qsofitmore_config:
        common += ["--qsofitmore-config", args.qsofitmore_config]
    if args.qsofitmore_mc_trails is not None:
        common += ["--qsofitmore-mc-trails", str(args.qsofitmore_mc_trails)]
    if args.pyqsofitspec_config:
        common += ["--pyqsofitspec-config", args.pyqsofitspec_config]
    if args.pyqsofitspec_nboot is not None:
        common += ["--pyqsofitspec-nboot", str(args.pyqsofitspec_nboot)]

    def command(src, tool, nthreads: int = 1):
        cmd = base + ["--only", src["key"], "--tools", tool] + common
        if tool == "s3fit_line":
            cmd += ["--s3fit-threads", str(max(1, int(nthreads)))]
        return cmd

    snapshot = ResourceSnapshot.detect()
    log(f"[resources] cpus={snapshot.cpu_count} budget={snapshot.cpu_budget} "
        f"mem={snapshot.memory_available_gb:.1f}GB gpu={snapshot.gpu_count}")
    rc = 0
    # Dependencies that are not explicitly in the selected job list are run
    # first, serially, so S3Fit and crossmission never read a stale/missing
    # producer product.
    have = {(s["key"], t) for s, t, _, _ in jobs}
    producer_jobs = []
    producer_pairs = set()
    # A selected producer must run before its consumer even when the producer
    # is also in the requested tool list (e.g. s3fit_line + pyqsofit_uv).
    dependency_tools = {dep for src, tool, _, _ in jobs
                        for dep in PREREQUISITES.get(tool, [])
                        if dep in src.get("tools", [])}
    for src, tool, out, logp in jobs:
        if tool in dependency_tools and (src["key"], tool) not in producer_pairs:
            producer_jobs.append((src, tool, out, logp))
            producer_pairs.add((src["key"], tool))
        for dep in PREREQUISITES.get(tool, []):
            if dep not in src.get("tools", []):
                continue
            if (src["key"], dep) not in have:
                dep_out = output_dir(src["key"], dep)
                dep_log = WORK_ROOT.parent / "logs" / src["key"] / f"{dep}.log"
                producer_jobs.append((src, dep, dep_out, dep_log))
                have.add((src["key"], dep))
            producer_pairs.add((src["key"], dep))
    jobs = [j for j in jobs if (j[0]["key"], j[1]) not in producer_pairs]
    def parent_log(logp: Path) -> Path:
        return logp.with_name(logp.stem + ".runner.log")

    failed_deps = set()
    for src, tool, out, logp in producer_jobs:
        log(f"[producer] {src['key']}/{tool}")
        r = run(command(src, tool, 1), parent_log(logp), env_for_threads(1))
        if r:
            failed_deps.add((src["key"], tool))
            rc = 1
    # A consumer whose producer failed must not run against stale data.
    jobs = [j for j in jobs
            if not any((j[0]["key"], d) in failed_deps for d in PREREQUISITES.get(j[1], []))]
    # Multicore phase: one tool at a time, full thread budget.
    for src, tool, out, logp in jobs:
        if tool not in multi:
            continue
        nthreads = threads_for_tool(tool, args.threads, snapshot)
        log(f"[multicore {nthreads}] {src['key']}/{tool}")
        rc |= run(command(src, tool, nthreads), parent_log(logp), env=env_for_threads(nthreads))
    # Single-core phase: parallel, one thread per worker.  Post-processing
    # tools that consume another tool's output run after this phase.
    singles = [(s, t, o, l) for s, t, o, l in jobs
               if t not in multi and t not in DEPENDENT_TOOLS]
    final = [(s, t, o, l) for s, t, o, l in jobs if t in DEPENDENT_TOOLS]
    if singles:
        njobs = jobs_for_singles([t for _, t, _, _ in singles], args.jobs, snapshot)
        log(f"[parallel {njobs}] {len(singles)} single-core jobs")
        with ThreadPoolExecutor(max_workers=njobs) as ex:
            futures = {ex.submit(run, command(s, t, 1), parent_log(l), env_for_threads(1)): (s, t)
                       for s, t, o, l in singles}
            for fut in as_completed(futures):
                s, t = futures[fut]
                try:
                    r = fut.result()
                except Exception as exc:  # noqa: BLE001
                    log(f"[error] {s['key']}/{t}: {exc}")
                    r = 1
                if r:
                    log(f"[failed] {s['key']}/{t}")
                    rc = 1
                else:
                    log(f"[ok] {s['key']}/{t}")
    # Dependency-bearing post-processing runs only after the producers.
    for s, t, o, l in final:
        log(f"[final] {s['key']}/{t}")
        rc |= run(command(s, t, 1), parent_log(l), env_for_threads(1))
    return rc


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tools", nargs="*", choices=ALL_TOOLS, default=list(ALL_TOOLS))
    p.add_argument("--only", "--source", nargs="*", default=None, help="source keys or globs")
    p.add_argument("--auto", action="store_true",
                   help="use the source-aware planner instead of --tools")
    p.add_argument("--plan", action="store_true",
                   help="print the source-aware plan and exit")
    p.add_argument("--goal", choices=("auto", "lines", "xray", "sed", "host", "ifu", "all"),
                   default="auto", help="planner goal (with --auto/--plan)")
    p.add_argument("--max-cost", choices=("short", "medium", "long"), default="long")
    p.add_argument("--include-expensive", action="store_true",
                   help="allow long tools in an auto plan")
    p.add_argument("--phased", action="store_true",
                   help="run multicore tools serially, then single-core tools in parallel")
    p.add_argument("--jobs", default="auto",
                   help="parallel single-core jobs in --phased mode (default: auto)")
    p.add_argument("--threads", default="auto",
                   help="multicore threads, or auto based on cgroups/memory (default: auto)")
    p.add_argument("--multicore-tools", default=None,
                   help="comma-separated tool names treated as multicore")
    p.add_argument("--resource-report", action="store_true",
                   help="print detected resources and exit")
    p.add_argument("--list", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--cigale-models", default="skirtor2016",
                   help="comma-separated CIGALE AGN models")
    p.add_argument("--qsofitmore-config", default=None,
                   help="QSOFITMORE config directory (default: configs/qsofitmore_line/default)")
    p.add_argument("--qsofitmore-mc-trails", type=int, default=None,
                   help="QSOFITMORE Monte Carlo realizations (default from config.json: 200)")
    p.add_argument("--pyqsofitspec-config", default=None,
                   help="PyQSOFitSpec config directory (default: configs/pyqsofitspec_line/default)")
    p.add_argument("--pyqsofitspec-nboot", type=int, default=None,
                   help="PyQSOFitSpec bootstrap realisations (default from config.json: 50)")
    p.add_argument("--s3fit-config", default=None,
                   help="S3Fit config directory (default: configs/s3fit_line/default)")
    p.add_argument("--s3fit-n-mocks", type=int, default=None,
                   help="S3Fit Monte-Carlo mock spectra (default from fit_config.json: 10)")
    p.add_argument("--s3fit-threads", type=int, default=None,
                   help="S3Fit internal threads (default: config; --phased passes --threads)")
    p.add_argument("--s3fit-mode", choices=("spec+sed", "spec"), default=None,
                   help="S3Fit fitting mode (default from fit_config.json)")
    p.add_argument("--galspec-config", default=None,
                   help="GalSpec config directory (default: configs/galspec_line/default)")
    p.add_argument("--galspec-sampler", choices=("mcmc", "nested", "lsq"), default=None,
                   help="GalSpec sampling mode override")
    p.add_argument("--galspec-mcmc-steps", type=int, default=None,
                   help="GalSpec emcee production steps (long run)")
    p.add_argument("--galspec-nwalkers", type=int, default=None)
    p.add_argument("--galspec-nburn", type=int, default=None)
    args = p.parse_args(argv)
    if args.resource_report:
        print(json.dumps(ResourceSnapshot.detect().report(), indent=2))
        return 0
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
    if args.plan:
        for src in sources:
            plan = make_plan(src, goal=args.goal, max_cost=args.max_cost,
                             include_expensive=args.include_expensive)
            log(f"\n{src['key']}  goal={plan['goal']}")
            for c in plan["selected"]:
                log(f"  -> {c['tool']:18s} [{c['cost']:6s}] {c['reason']}")
            for c in plan["skipped"]:
                log(f"  -- {c['tool']:18s} {c['reason']}")
        return 0
    if args.phased:
        return _run_phased(sources, args)

    rc = 0
    for src in sources:
        key = src["key"]
        log(f"\n=== {key}  z={src['z']}  kind={src.get('kind')}")
        if args.auto:
            plan = make_plan(src, goal=args.goal, max_cost=args.max_cost,
                             include_expensive=args.include_expensive)
            tools = [c["tool"] for c in plan["selected"]]
            log(f"[auto] {len(tools)} selected: {', '.join(tools) or '-'}")
        else:
            tools = args.tools
        for tool in tools:
            if not args.auto and tool not in src.get("tools", []):
                continue
            out = output_dir(key, tool)
            logp = WORK_ROOT.parent / "logs" / key / f"{tool}.log"
            log(f"[{key}] {tool} -> {out.relative_to(ROOT)}")
            if args.dry_run:
                continue
            backup = None
            if args.force and out.exists() and tool != "xmm_sas_raw":
                import shutil
                backup = out.with_name(out.name + ".preforce")
                if backup.exists():
                    shutil.rmtree(backup)
                out.rename(backup)
            elif args.force and tool == "xmm_sas_raw":
                log("[force] xmm_sas_raw: preserving raw spectra; overwriting fit products only")
            ensure_output(key, tool)
            # Serial mode must honour the same producer graph as --phased and
            # Snakemake.  A consumer must never silently use a missing/stale
            # producer (S3Fit previously did exactly that).
            prereq_ok = True
            for dep in PREREQUISITES.get(tool, []):
                if dep not in src.get("tools", []) or dep == tool:
                    continue
                dep_out = out.parent / dep
                if dep_out.exists() and not args.force:
                    continue
                dep_cmd = [sys.executable, str(Path(__file__)),
                           "--only", key, "--tools", dep]
                if args.force:
                    dep_cmd.append("--force")
                dep_log = logp.with_name(f"{tool}__{dep}.pre.log")
                log(f"[prerequisite] {key}/{dep}")
                if run(dep_cmd, dep_log) != 0:
                    log(f"[failed] prerequisite {key}/{dep}")
                    prereq_ok = False
                    break
            if not prereq_ok:
                import shutil
                if out.exists():
                    shutil.rmtree(out)
                if backup is not None:
                    backup.rename(out)
                rc = 1
                continue
            fn = {
                "ir_linefit": lambda: tool_ir(src, out, logp),
                "pyqsofit_uv": lambda: tool_pyqsofit(src, out, logp),
                "optical_linefit": lambda: tool_optical_linefit(src, out, logp),
                "qsofitmore_line": lambda: tool_qsofitmore(src, out, logp,
                                                           args.qsofitmore_config,
                                                           args.qsofitmore_mc_trails),
                "pyqsofitspec_line": lambda: tool_pyqsofitspec(src, out, logp,
                                                               args.pyqsofitspec_nboot,
                                                               args.pyqsofitspec_config),
                "manga_dap": lambda: tool_manga_dap(src, out, logp),
                "manga_dap_full": lambda: tool_manga_dap(src, out, logp, full=True),
                "xmm_xspec": lambda: tool_xmm(src, out, logp),
                "xmm_sas_raw": lambda: tool_xmm_sas_raw(src, out, logp),
                "rxte_xspec": lambda: tool_rxte(src, out, logp),
                "crossmission": lambda: tool_crossmission(src, out, logp),
                "ppxf_host": lambda: tool_ppxf(src, out, logp),
                "gandalf_line": lambda: tool_gandalf(src, out, logp),
                "galspec_line": lambda: tool_galspec(src, out, logp,
                                                     args.galspec_config,
                                                     args.galspec_sampler,
                                                     args.galspec_mcmc_steps,
                                                     args.galspec_nwalkers,
                                                     args.galspec_nburn),
                "cafe_line": lambda: tool_cafe(src, out, logp),
                "qgfit": lambda: tool_qgfit(src, out, logp),
                "sheap_line": lambda: tool_sheap(src, out, logp),
                "nir_linefit": lambda: tool_nir(src, out, logp),
                "pahfit_mir": lambda: tool_pahfit(src, out, logp),
                "fir_linefit": lambda: tool_fir(src, out, logp),
                "crossband": lambda: tool_crossband(src, out, logp),
                "cigale_sed": lambda: tool_cigale(src, out, logp,
                                                   [x.strip() for x in args.cigale_models.split(",") if x.strip()]),
                "agnfitter_sed": lambda: tool_agnfitter(src, out, logp),
                "s3fit_line": lambda: tool_s3fit(src, out, logp,
                                                 args.s3fit_config, args.s3fit_n_mocks,
                                                 args.s3fit_mode,
                                                 args.s3fit_threads or (threads_for_tool(
                                                     "s3fit_line", args.threads,
                                                     ResourceSnapshot.detect()))),
            }[tool]
            try:
                r = fn()
            except SkipTool as exc:
                import shutil
                log(f"[skip] {key}/{tool}: {exc}")
                if out.exists():
                    shutil.rmtree(out)
                if backup is not None:
                    backup.rename(out)
                continue
            except Exception as exc:  # noqa: BLE001
                import shutil
                log(f"[error] {key}/{tool}: {exc}")
                if out.exists():
                    shutil.rmtree(out)
                if backup is not None:
                    backup.rename(out)
                r = 1
            if r:
                import shutil
                log(f"[failed] {key}/{tool} rc={r}  log={logp}")
                if out.exists():
                    shutil.rmtree(out)
                if backup is not None:
                    backup.rename(out)
                rc = 1
            else:
                if backup is not None:
                    import shutil
                    shutil.rmtree(backup)
                log(f"[ok] {key}/{tool}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
