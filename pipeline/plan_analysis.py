#!/usr/bin/env python3
"""Source-aware analysis planner.

This is the repository's *advisory but source-specific* decision engine.  It
reads a canonical ``source.json``, inspects the available data roles and FITS
coverage, then returns a ranked, cost-aware list of tools with a reason for
each decision.  It does not pretend that a heuristic is a scheduler: the
source manifest's ``tools`` list remains the final authority, but a plan makes
that choice reproducible and reviewable.

Examples
--------
    .venv/bin/python pipeline/plan_analysis.py --source 3C120_z_0.0330
    .venv/bin/python pipeline/plan_analysis.py --source PDS456_z_0.1840 --goal lines
    .venv/bin/python pipeline/plan_analysis.py --source 04592649654_z_0.5874 --json
    .venv/bin/python pipeline/plan_analysis.py --source 3C120_z_0.0330 --write
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.io_layout import iter_sources, load_source, source_files  # noqa: E402
from pipeline.tool_registry import BY_NAME  # noqa: E402

# Cost is a coarse wall-clock class, not a promise.  It lets a beginner avoid
# accidentally launching a 1-hour fit while still allowing the full science run.
COST = {
    "pyqsofit_uv": "short", "qsofitmore_line": "short", "pyqsofitspec_line": "short",
    "ir_linefit": "short", "nir_linefit": "short", "optical_linefit": "short",
    "ppxf_host": "medium", "gandalf_line": "medium", "xmm_xspec": "medium",
    "rxte_xspec": "short", "manga_dap": "medium", "manga_dap_full": "long", "pahfit_mir": "medium",
    "cafe_line": "long", "s3fit_line": "long", "galspec_line": "long",
    "qgfit": "long", "sheap_line": "short", "crossmission": "short",
    "crossband": "short", "cigale_sed": "medium", "agnfitter_sed": "long",
    "sdss_zline": "short",
}
COST_ORDER = {"short": 0, "medium": 1, "long": 2}
DEFAULT_GOAL = "auto"


@dataclass(frozen=True)
class Candidate:
    tool: str
    reason: str
    cost: str
    required: bool = False


def _roles(src: dict) -> set[str]:
    roles = set(src.get("files", {}).keys()) if isinstance(src.get("files"), dict) else set()
    if src.get("kind"):
        roles.add(str(src["kind"]))
    for key in ("photometry", "xray", "optical", "xshooter"):
        if src.get(key):
            roles.add(key)
    return roles


def _coverage(src: dict) -> dict:
    """Best-effort observed wavelength/energy coverage without inventing data."""
    cov = {"optical_um": None, "mir_um": None, "xray_kev": None}
    optical_ranges = []
    from astropy.io import fits
    for p in source_files(src, "xshooter_spectrum") + source_files(src, "optical_spectrum") + source_files(src, "spectrum") + source_files(src, "uv_spectrum"):
        if not p.exists():
            continue
        try:
            with fits.open(p, memmap=False) as h:
                for hdu in h:
                    if getattr(hdu, "columns", None) is None:
                        continue
                    names = {c.upper() for c in hdu.columns.names}
                    if {"WAVELENGTH", "FLUX"} <= names:
                        w = hdu.data["WAVELENGTH"]
                        w = w.ravel() if hasattr(w, "ravel") else w
                        optical_ranges.append([float(min(w)) / 1e4, float(max(w)) / 1e4])
                        break
                    if {"WAVE", "FLUX"} <= names:
                        w = hdu.data["WAVE"]
                        w = w.ravel() if hasattr(w, "ravel") else w
                        unit = str(hdu.columns["WAVE"].unit or "").lower()
                        fac = 1e-3 if "nm" in unit else 1e-4
                        optical_ranges.append([float(min(w)) * fac, float(max(w)) * fac])
                        break
        except Exception:
            pass
    if optical_ranges:
        cov["optical_um"] = [min(x[0] for x in optical_ranges), max(x[1] for x in optical_ranges)]
    for p in source_files(src, "spectra"):
        try:
            with fits.open(p, memmap=False) as h:
                for hdu in h:
                    if getattr(hdu, "columns", None) is None:
                        continue
                    names = {c.lower() for c in hdu.columns.names}
                    if "wavelength" in names and "flux" in names:
                        w = hdu.data["WAVELENGTH"]
                        cov["mir_um"] = [float(min(w)), float(max(w))]
                        break
        except Exception:
            pass
    return cov


def _band_availability(src: dict, cov: dict) -> dict:
    roles = _roles(src)
    text = " ".join(sorted(roles)).lower()
    optical = bool({"optical_spectrum", "xshooter_spectrum", "spectrum", "uv_spectrum"} & roles) or "sdss" in text
    xray = bool({"xray_spectrum", "xray_pca_source", "xray"} & roles)
    mir = bool({"spectra", "mir_table", "jwst_miri", "spitzer_irs", "pacs"} & roles) or "miri" in text or "irs" in text
    fir = bool({"pacs", "spectrum"} & roles) or "fir" in text or "pacs" in text
    ifu = bool({"manga_cube", "manga_rss", "manga_maps_reference"} & roles) or "manga" in text
    phot = bool({"photometry"} & roles) or "photometry" in src
    if cov.get("optical_um") and cov["optical_um"][1] > 1.0:
        mir = mir or cov["optical_um"][1] > 3.0
    return {"optical": optical, "uv": optical, "xray": xray, "mir": mir,
            "fir": fir, "ifu": ifu, "photometry": phot}


def _candidates(src: dict, bands: dict, goal: str) -> list[Candidate]:
    available = set(src.get("tools", []))
    unrestricted = not available  # an input-only manifest still gets a plan
    out: list[Candidate] = []
    def add(tool, reason, required=False):
        if tool not in BY_NAME:
            return
        if not unrestricted and tool not in available:
            return
        out.append(Candidate(tool, reason, COST.get(tool, "medium"), required))

    if goal in ("auto", "lines") and bands["optical"]:
        add("pyqsofit_uv", "rest-UV/optical broad/narrow line decomposition")
        add("optical_linefit", "local Hβ/[O III] fit with tied doublet and broad/narrow components")
        add("qsofitmore_line", "independent UV/optical QSO model (200-draw MC)")
        add("pyqsofitspec_line", "independent skew-normal line model")
        add("s3fit_line", "simultaneous spectrum + SED check (long)")
        add("gandalf_line", "stellar + gas decomposition when host contamination matters")
        add("ppxf_host", "host/stellar kinematics when the continuum is host-dominated")
    if goal in ("auto", "lines") and bands["mir"]:
        add("pahfit_mir", "MIR PAH/dust/gas decomposition")
        add("cafe_line", "NIR/MIR continuum + line/PAH decomposition (long)")
        add("ir_linefit", "local Gaussian MIR/FIR line checks")
    if goal in ("auto", "lines") and bands["fir"]:
        add("fir_linefit", "FIR PACS/HIFI Gaussian line fit")
    if goal in ("auto", "xray") and bands["xray"]:
        add("xmm_xspec", "official XMM-Newton EPIC PPS + XSPEC Fe Kα")
        add("rxte_xspec", "official RXTE PCA stdprod + XSPEC Fe Kα")
    if goal in ("auto", "ifu") and bands["ifu"]:
        add("manga_dap", "official MaNGA DAP subset")
    if goal in ("auto", "sed", "all") and bands["photometry"]:
        add("cigale_sed", "broad-band SED/torus model")
        add("agnfitter_sed", "independent SED/torus posterior")
    if goal in ("auto", "all") and bands["optical"] and bands["xray"]:
        add("crossmission", "same-object Fe Kα vs Hβ/C IV comparison (case study)")
    if goal in ("auto", "all") and bands["mir"] and bands["fir"]:
        add("crossband", "cross-band line-ratio consistency")
    # de-duplicate while preserving the first (highest priority) reason
    seen = set()
    unique = []
    for c in out:
        if c.tool not in seen:
            seen.add(c.tool)
            unique.append(c)
    return unique


def make_plan(src: dict, goal: str = DEFAULT_GOAL, max_cost: str = "long",
              include_expensive: bool = False) -> dict:
    if goal not in ("auto", "lines", "xray", "sed", "host", "ifu", "all"):
        raise ValueError(f"unknown goal: {goal}")
    cov = _coverage(src)
    bands = _band_availability(src, cov)
    candidates = _candidates(src, bands, goal)
    selected, skipped = [], []
    for c in candidates:
        if COST_ORDER[c.cost] > COST_ORDER[max_cost]:
            skipped.append({"tool": c.tool, "reason": f"cost {c.cost} > max_cost {max_cost}"})
        elif c.cost == "long" and not include_expensive and not c.required and goal == "auto":
            skipped.append({"tool": c.tool, "reason": "long run; use --include-expensive or --goal all"})
        else:
            selected.append(asdict(c))
    if not selected:
        skipped.append({"tool": "*", "reason": "no registered tool matches the available data roles"})
    return {
        "plan_schema_version": "1.0.0",
        "source_key": src["key"],
        "name": src.get("name", src["key"]),
        "redshift": src.get("z"),
        "goal": goal,
        "bands": bands,
        "coverage": cov,
        "available_roles": sorted(_roles(src)),
        "selected": selected,
        "skipped": skipped,
        "notes": [
            "The source manifest tools list is the final authority.",
            "Long tools are excluded from auto plans unless --include-expensive is set.",
            "A plan is advisory; validate the actual outputs and caveats before publication.",
        ],
    }


def plan_for_key(key: str, **kw) -> dict:
    return make_plan(load_source(key), **kw)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", nargs="*", default=None)
    p.add_argument("--goal", choices=("auto", "lines", "xray", "sed", "host", "ifu", "all"),
                   default="auto")
    p.add_argument("--max-cost", choices=("short", "medium", "long"), default="long")
    p.add_argument("--include-expensive", action="store_true")
    p.add_argument("--write", action="store_true", help="write work/plans/<source>.json")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    keys = a.source or [s["key"] for s in iter_sources()]
    if not keys:
        print("no sources", file=sys.stderr)
        return 1
    plans = []
    for key in keys:
        try:
            plan = plan_for_key(key, goal=a.goal, max_cost=a.max_cost,
                                include_expensive=a.include_expensive)
        except Exception as exc:  # noqa: BLE001
            print(f"[error] {key}: {exc}", file=sys.stderr)
            continue
        plans.append(plan)
        if a.write:
            out = ROOT / "work" / "plans" / f"{key}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(plan, indent=2) + "\n")
        if not a.json:
            print(f"\n{key}  z={plan['redshift']}  goal={plan['goal']}")
            print("  bands:", ", ".join(k for k, v in plan["bands"].items() if v) or "-")
            for c in plan["selected"]:
                print(f"  -> {c['tool']:18s} [{c['cost']:6s}] {c['reason']}")
            for c in plan["skipped"]:
                print(f"  -- {c['tool']:18s} {c['reason']}")
    if a.json:
        print(json.dumps(plans, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
