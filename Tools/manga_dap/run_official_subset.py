#!/usr/bin/env python3
"""Official full-method Sasuke DAP fit on a selected set of central bins.

The all-spaxel MaNGA DAP emission-line model on the 2397 HYB10 bins did not
complete within the wall-clock budget (see
outputs/NGC1194_z_0.0136/manga_dap/logs/full_dap_attempt_summary.txt).  This
runner therefore keeps the **full official DAP method** -- 65 MaStar-HC2
templates, ELPMPL11, mdegree=14, deconstruct_bins='ignore' -- and restricts the
official Sasuke fit to the 9 central single-spaxel bins of the completed
Stage-A HYB10/S/N=50 DAP products.

It reuses the official Stage-A products (reduction assessment, binned spectra,
pPXF stellar continuum, EMOM moments, INDXEN indices) and writes a MAPS file
whose emission-line extensions are valid only for the selected bins.  All other
bins are masked.  The published MAPS remains the all-spaxel reference.

This is a subset product, not a full all-spaxel DAP run.  The quality gate in
run.json says so explicitly, and the fast fixed-continuum all-spaxel product
(if present) is relegated to aux_fastmode/ with a FASTMODE quality flag.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import time
import traceback
from pathlib import Path

os.environ.setdefault("MANGADRP_VER", "v3_1_1")
os.environ.setdefault("MANGADAP_VER", "4.5.0")
os.environ.setdefault("MANGA_SPECTRO_REDUX", "/app/redux")
os.environ.setdefault("MANGA_SPECTRO_ANALYSIS", "/app/output/dap")

import numpy as np
import matplotlib
matplotlib.use("Agg")
from astropy.io import fits
from matplotlib import pyplot as plt

import sys
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from manga_maps import (  # noqa: E402
    CLASS_COLORS, CLASS_NAMES, KEY_LINES, bpt_fractions, classify_bpt,
    jsonable, key_fluxes, line_kinematics, load_maps, plot_spectrum_fit,
    robust_compare, sha256_file, stellar_arrays, write_csv, write_json,
)
from fast_eline import find_binned_products, load_binned  # noqa: E402

C_KMS = 299792.458
PLATE = 9193
IFU = 12701


def _fmt(v):
    try:
        v = float(v)
    except Exception:
        return ""
    return "" if (math.isnan(v) or math.isinf(v)) else v


def _copy_stage_a(stage_a_dir: Path, dap_root: Path, daptype: str):
    src_common = stage_a_dir / "common"
    if not src_common.exists():
        raise FileNotFoundError(f"Stage-A common directory not found: {src_common}")
    dst_common = dap_root / "common"
    if not dst_common.exists():
        shutil.copytree(src_common, dst_common)
    src_refs = list(stage_a_dir.glob(f"*/{PLATE}/{IFU}/ref"))
    dst_ref = dap_root / daptype / str(PLATE) / str(IFU) / "ref"
    dst_ref.mkdir(parents=True, exist_ok=True)
    if src_refs:
        for p in src_refs[0].glob("*"):
            if p.is_file() and not (dst_ref / p.name).exists():
                shutil.copy2(p, dst_ref / p.name)
    return dap_root / "common" / str(PLATE) / str(IFU)


def _select_central_bins(bsp_path: Path, nbin: int) -> tuple[np.ndarray, np.ndarray]:
    with fits.open(bsp_path, memmap=False) as h:
        bins = h["BINS"].data.copy()
    sky = bins["SKY_COO"]
    nspax = bins["NBIN"]
    r = np.hypot(sky[:, 0], sky[:, 1])
    # Prefer single-spaxel bins so the full-method fit is a true central-bin
    # measurement and does not explode into a large per-spaxel remap.
    order = np.argsort(np.where(nspax == 1, r, r + 1e6))[:nbin]
    return bins["BINID"][order].astype(int), order.astype(int)


def _patch_sasuke(selected_ids: np.ndarray):
    from mangadap.proc.sasuke import Sasuke
    from mangadap.proc.spectralfitting import EmissionLineFit
    original = Sasuke.fit_SpatiallyBinnedSpectra
    original_select = EmissionLineFit.select_binned_spectra_to_fit

    def patched_select(binned_spectra, *args, **kwargs):
        good = np.asarray(original_select(binned_spectra, *args, **kwargs), dtype=bool).copy()
        ids = binned_spectra["BINS"].data["BINID"].astype(int)
        good &= np.isin(ids, selected_ids)
        return good

    EmissionLineFit.select_binned_spectra_to_fit = staticmethod(patched_select)

    def patched(self, binned_spectra, good_bins=None, good_spax=None, **kwargs):
        if good_bins is None:
            good_bins = np.ones(binned_spectra.nbins, dtype=bool)
        else:
            good_bins = np.asarray(good_bins, dtype=bool).copy()
        ids = binned_spectra["BINS"].data["BINID"].astype(int)
        good_bins &= np.isin(ids, selected_ids)
        print(f"  official Sasuke subset: fitting {int(np.sum(good_bins))}/"
              f"{len(good_bins)} bins", flush=True)
        return original(self, binned_spectra, good_bins=good_bins,
                        good_spax=good_spax, **kwargs)

    Sasuke.fit_SpatiallyBinnedSpectra = patched
    return Sasuke


def _subset_comparison(ours: dict, ref: dict, f_ours: dict, f_ref: dict,
                       selected_ids: np.ndarray, bins: dict, out: Path) -> dict:
    binid_map = ours["binid"][0]
    rows = []
    for k, binid in enumerate(selected_ids):
        sel = binid_map == int(binid)
        ys, xs = np.where(sel)
        if len(ys) == 0:
            continue
        iy, ix = int(ys[0]), int(xs[0])
        row = {"bin_index": int(k), "binid": int(binid), "nspax": int(sel.sum()),
               "row": iy, "col": ix,
               "ra_deg": float(ours["ra"][iy, ix]),
               "dec_deg": float(ours["dec"][iy, ix]),
               "x_arcsec": float(ours["skycoo"][0][iy, ix]),
               "y_arcsec": float(ours["skycoo"][1][iy, ix])}
        for key in KEY_LINES:
            a = f_ours[key][iy, ix]
            ae = f_ours[f"{key}_err"][iy, ix]
            # Reference value: median over the spaxels belonging to this bin.
            vals = f_ref[key][ys, xs]
            errs = f_ref[f"{key}_err"][ys, xs]
            good = np.isfinite(vals) & (vals > 0)
            b = float(np.median(vals[good])) if np.any(good) else np.nan
            be = float(np.median(errs[good])) if np.any(good) else np.nan
            row[f"{key}_flux"] = _fmt(a)
            row[f"{key}_flux_err"] = _fmt(ae)
            row[f"{key}_ref_median"] = _fmt(b)
            row[f"{key}_ref_err_median"] = _fmt(be)
            row[f"{key}_ratio"] = _fmt(a / b) if np.isfinite(a) and np.isfinite(b) and b > 0 else ""
        # BPT based on our bin values and the reference median values.
        co, _, _, _ = classify_bpt(np.array([f_ours["o3_hb"][iy, ix]]),
                                   np.array([f_ours["n2_ha"][iy, ix]]),
                                   np.array([f_ours["s2_ha"][iy, ix]]),
                                   np.array([f_ours["oi_ha"][iy, ix]]))
        ro, _, _, _ = classify_bpt(np.array([np.nanmedian(f_ref["o3_hb"][ys, xs])]),
                                   np.array([np.nanmedian(f_ref["n2_ha"][ys, xs])]),
                                   np.array([np.nanmedian(f_ref["s2_ha"][ys, xs])]),
                                   np.array([np.nanmedian(f_ref["oi_ha"][ys, xs])]))
        row["bpt_ours"] = str(co[0])
        row["bpt_ref"] = str(ro[0])
        row["bpt_agree"] = bool(co[0] == ro[0])
        rows.append(row)
    write_csv(out / "subset_bins.csv", rows)
    stats = {}
    for key in KEY_LINES:
        stats[key] = robust_compare(
            np.array([r.get(f"{key}_flux", np.nan) for r in rows], dtype=float),
            np.array([r.get(f"{key}_flux_err", np.nan) for r in rows], dtype=float),
            np.array([r.get(f"{key}_ref_median", np.nan) for r in rows], dtype=float),
            np.array([r.get(f"{key}_ref_err_median", np.nan) for r in rows], dtype=float),
        )
    agree = sum(bool(r["bpt_agree"]) for r in rows)
    bpt = {
        "n": len(rows), "n_agree": agree,
        "agreement_fraction": (agree / len(rows)) if rows else None,
        "ours": {c: sum(r["bpt_ours"] == c for r in rows) for c in CLASS_NAMES},
        "reference": {c: sum(r["bpt_ref"] == c for r in rows) for c in CLASS_NAMES},
    }
    return {"line_statistics": stats, "bpt": bpt, "bins": rows}


def _subset_plots(result: dict, f_ours: dict, f_ref: dict, selected_ids: np.ndarray,
                  ours: dict, out: Path):
    rows = result["bins"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 9))
    for ax, key, label in zip(axes.ravel(), KEY_LINES,
                              ("H-alpha", "H-beta", "[O III] 5007", "[N II] 6584",
                               "[S II] 6716", "[S II] 6731")):
        a = np.array([r.get(f"{key}_flux", np.nan) for r in rows], dtype=float)
        b = np.array([r.get(f"{key}_ref_median", np.nan) for r in rows], dtype=float)
        good = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
        ax.scatter(b[good], a[good], s=35, color="C0", edgecolors="k", linewidths=0.4)
        if np.sum(good) >= 2:
            lo = max(min(np.min(a[good]), np.min(b[good])) * 0.7, 1e-3)
            hi = max(np.max(a[good]), np.max(b[good])) * 1.4
            ax.plot([lo, hi], [lo, hi], "k--", lw=1.0)
            ax.set_xscale("log"); ax.set_yscale("log")
            ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
            med = float(np.median(a[good] / b[good]))
            ax.set_title(f"{label}: N={np.sum(good)}, median ratio={med:.3f}", fontsize=9)
        else:
            ax.set_title(label + ": insufficient overlap", fontsize=9)
        ax.set_xlabel("published MAPS (median over bin spaxels)")
        ax.set_ylabel("official DAP subset fit")
        ax.grid(alpha=0.2)
    fig.suptitle("Official full-method SASUKE subset vs published DAP MAPS", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out / "subset_flux_comparison.png", dpi=150)
    fig.savefig(out / "subset_flux_comparison.pdf")
    plt.close(fig)

    # BPT: our 9 bins and the reference medians.
    fig, ax = plt.subplots(figsize=(6.2, 5.8))
    for source, marker, label in (("ours", "o", "official subset fit"),
                                  ("ref", "s", "published MAPS (bin median)")):
        xs = []
        ys = []
        for r in rows:
            if source == "ours":
                hi = r.get("ha_flux"); hb = r.get("hb_flux")
                o3 = r.get("oiii_5007_flux"); n2 = r.get("nii_6584_flux")
            else:
                hi = r.get("ha_ref_median"); hb = r.get("hb_ref_median")
                o3 = r.get("oiii_5007_ref_median"); n2 = r.get("nii_6584_ref_median")
            if all(v not in ("", None) and np.isfinite(float(v)) and float(v) > 0
                   for v in (hi, hb, o3, n2)):
                xs.append(math.log10(float(n2) / float(hi)))
                ys.append(math.log10(float(o3) / float(hb)))
        ax.scatter(xs, ys, marker=marker, s=42, alpha=0.8, label=label,
                   edgecolors="k", linewidths=0.4)
    xx = np.linspace(-2.5, 0.45, 300)
    ax.plot(xx, 0.61 / (xx - 0.05) + 1.30, "k--", lw=1.0, label="Kauffmann+2003")
    ax.plot(xx, 0.61 / (xx - 0.47) + 1.19, "k-", lw=1.0, label="Kewley+2001")
    ax.set_xlim(-2.5, 0.45); ax.set_ylim(-1.5, 1.6)
    ax.set_xlabel(r"$\log_{10}$([N II]/H$\alpha$)")
    ax.set_ylabel(r"$\log_{10}$([O III]/H$\beta$)")
    ax.set_title("N2-BPT: 9 central bins", fontsize=10)
    ax.legend(fontsize=7); ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out / "subset_bpt.png", dpi=150)
    fig.savefig(out / "subset_bpt.pdf")
    plt.close(fig)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", default="/app/input")
    p.add_argument("--stage-a-dir", required=True,
                   help="directory containing the completed Stage-A dap/ tree")
    p.add_argument("--out", required=True)
    p.add_argument("--config", default="/app/config")
    p.add_argument("--reference", required=True)
    p.add_argument("--n-bins", type=int, default=9)
    p.add_argument("--source-key", default="NGC1194_z_0.0136")
    args = p.parse_args(argv)

    from mangadap.datacube.manga import MaNGADataCube
    from mangadap.config.manga import MaNGAAnalysisPlan
    from mangadap.survey.manga_dap import manga_dap
    from mangadap import __version__ as mangadap_version

    config = json.loads((Path(args.config) / "config.json").read_text())
    source = config["source"]
    daptype = config["dap"]["daptype"]
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "fits").mkdir(exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)
    stage_a_dir = Path(args.stage_a_dir).resolve()
    work = out / "work_subset"
    dap_root = work / "dap"
    dap_root.mkdir(parents=True, exist_ok=True)
    common = _copy_stage_a(stage_a_dir, dap_root, daptype)
    bsp_path, cont_path = find_binned_products(dap_root, PLATE, IFU)
    binned = load_binned(bsp_path, cont_path)
    selected_ids, selected_order = _select_central_bins(bsp_path, args.n_bins)
    bins = binned["bins"]
    print(f"selected {len(selected_ids)} central single-spaxel bins: {selected_ids.tolist()}")
    print("sky coords (arcsec):", [tuple(round(float(v), 2) for v in bins['SKY_COO'][i])
                                   for i in selected_order])

    cube_path = Path(args.input_dir).resolve() / "raw" / f"manga-{PLATE}-{IFU}-LOGCUBE.fits.gz"
    if not cube_path.exists():
        cube_path = Path(args.input_dir).resolve() / f"manga-{PLATE}-{IFU}-LOGCUBE.fits.gz"
    meta = config["metadata"]
    cube = MaNGADataCube(str(cube_path), z=float(meta["z"]),
                         vdisp=float(meta.get("vdisp_kms_initial", 100.0)),
                         ell=float(meta["ell"]), pa=float(meta["pa_deg"]),
                         reff=float(meta["reff_arcsec"]))
    try:
        cube.load_rss()
    except Exception as exc:
        print(f"WARNING: LOGRSS not loaded: {exc}")

    plan_path = Path(args.config) / "plan_subset.toml"
    # Patch before the plan is parsed: EmissionLineModelDef captures the bound
    # fit method at parse time.
    _patch_sasuke(selected_ids)
    plan = MaNGAAnalysisPlan.from_toml(str(plan_path), cube=cube,
                                       analysis_path=str(dap_root))
    log_path = out / "logs" / "manga_dap_subset.log"
    t0 = time.perf_counter()
    err = None
    try:
        manga_dap(cube, plan, log=str(log_path), verbose=1)
    except Exception:
        err = traceback.format_exc()
    runtime = time.perf_counter() - t0
    method_dir = dap_root / daptype / str(PLATE) / str(IFU)
    maps_path = method_dir / f"manga-{PLATE}-{IFU}-MAPS-{daptype}.fits.gz"
    model_path = method_dir / f"manga-{PLATE}-{IFU}-LOGCUBE-{daptype}.fits.gz"
    if not maps_path.exists():
        raise RuntimeError("official subset DAP did not produce a MAPS file\n" + (err or ""))

    ours_maps = load_maps(maps_path)
    ref_maps = load_maps(Path(args.reference))
    f_ours = key_fluxes(ours_maps)
    f_ref = key_fluxes(ref_maps)
    comp = _subset_comparison(ours_maps, ref_maps, f_ours, f_ref,
                              selected_ids, bins, out)
    write_json(out / "subset_comparison.json", comp)
    write_csv(out / "subset_comparison_lines.csv",
              [{"quantity": k, **v} for k, v in comp["line_statistics"].items()])
    _subset_plots(comp, f_ours, f_ref, selected_ids, ours_maps, out)

    # Line summary for the selected bins (one value per bin).
    summary = []
    for key in KEY_LINES:
        vals = []
        for r in comp["bins"]:
            v = r.get(f"{key}_flux")
            if v not in ("", None):
                vals.append(float(v))
        if vals:
            summary.append({"line": key, "n_bins": len(vals),
                            "median_flux_1e17": _fmt(np.median(vals)),
                            "min_flux_1e17": _fmt(np.min(vals)),
                            "max_flux_1e17": _fmt(np.max(vals))})
    write_csv(out / "subset_line_summary.csv", summary)

    # Copy the subset MAPS and the Stage-A binned spectra/continuum.
    shutil.copy2(maps_path, out / "fits" / "dap_subset_maps.fits.gz")
    shutil.copy2(bsp_path, out / "fits" / "dap_binned_spectra.fits.gz")
    shutil.copy2(cont_path, out / "fits" / "dap_stellar_continuum.fits.gz")
    stage_a_moments = stage_a_dir.parent / "fits" / "manga_dap_moments_maps.fits.gz"
    if stage_a_moments.exists():
        shutil.copy2(stage_a_moments, out / "fits" / "dap_stage_a_moments_maps.fits.gz")
    # Central fit figure and spectrum.
    from run_manga_dap import extract_central_spectrum
    row, col = int(comp["bins"][0]["row"]), int(comp["bins"][0]["col"])
    # Find the bin row/col in the MAPS grid nearest the selected central bin.
    sel = ours_maps["binid"][0] == int(selected_ids[0])
    yy, xx = np.where(sel)
    row, col = int(yy[0]), int(xx[0])
    obs = {"obs_wave": binned["wave"], "obs_flux": binned["flux"][selected_order[0]],
           "obs_ferr": binned["ferr"][selected_order[0]],
           "obs_good": binned["good"][selected_order[0]]}
    spectra = extract_central_spectrum(cube_path, model_path, ours_maps, row, col,
                                       out / "fits" / "dap_subset_central_spectra.fits",
                                       observed_arrays=obs)
    plot_spectrum_fit(spectra, out / "figures" / "dap_subset_spectrum_fit.png",
                      title=f"Official DAP/Sasuke subset fit (bin {selected_ids[0]})")

    # The model cube and copied Stage-A tree are large intermediates; the
    # selected MAPS, binned spectra and continuum have been copied above.
    if work.exists():
        shutil.rmtree(work)
        print("  removed intermediate subset tree")

    stats = {
        "n_selected_bins": len(selected_ids),
        "selected_binids": [int(v) for v in selected_ids],
        "bpt": comp["bpt"],
        "subset_line_statistics": comp["line_statistics"],
        "all_spaxel_reference": str(Path(args.reference)),
    }
    write_json(out / "subset_stats.json", stats)

    run = {
        "tool": "manga_dap",
        "source_key": args.source_key,
        "status": "ok_subset",
        "product": "official full-method SASUKE fit on selected central bins",
        "dap_version": mangadap_version,
        "daptype": daptype,
        "stages_completed": ["reduction_assessment", "HYB10_binning",
                             "ppxf_stellar_kinematics", "emission_line_moments",
                             "spectral_indices", "sasuke_full_method_subset"],
        "n_selected_bins": len(selected_ids),
        "selected_binids": [int(v) for v in selected_ids],
        "runtime_seconds": runtime,
        "all_spaxel_dap_completed": False,
        "quality_gate": {
            "subset_acceptance": True,
            "all_spaxel_acceptance": False,
            "fast_mode_used_for_all_spaxel_maps": True,
            "fast_mode_flag": "FASTMODE_NOT_PRODUCTION",
            "fast_mode_acceptance": False,
            "reason": ("The full 2397-bin all-spaxel DAP emission-line model exceeded "
                       "the 58 min wall-clock budget and was killed. This product is the "
                       "official full-method Sasuke fit on 9 central single-spaxel bins; "
                       "the published official MAPS is the all-spaxel reference. The fast "
                       "fixed-continuum all-spaxel product is auxiliary only and is flagged."),
        },
        "subset_comparison": comp,
        "config": config,
        "inputs": {"stage_a_dir": str(stage_a_dir),
                   "reference_maps": str(Path(args.reference)),
                   "reference_sha256": sha256_file(Path(args.reference)),
                   "logcube": str(cube_path)},
        "outputs": sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()),
    }
    write_json(out / "run.json", run)
    write_json(out / "effective_config.json", {
        "configuration": config, "plan": plan_path.name,
        "selected_bins": [int(v) for v in selected_ids],
        "quality_gate": run["quality_gate"], "versions": {"sdss-mangadap": mangadap_version},
    })
    prov = [
        f"# MaNGA DAP official subset — {source['name']} ({source['plateifu']})",
        "",
        "This is an **official full-method DAP/Sasuke subset**, not a full all-spaxel run.",
        "",
        f"- Stage A: official DAP rdxqa, HYB10/S/N=50 binning, pPXF, EMOM, INDXEN (175 bins).",
        f"- Stage B: official default EmissionLineModel (65 MaStar-HC2 templates, ELPMPL11,",
        f"  mdegree=14, deconstruct_bins='ignore') restricted to the {len(selected_ids)} central",
        "  single-spaxel bins by a documented `good_bins` selection.",
        f"- Selected BINIDs: {selected_ids.tolist()}",
        f"- Runtime (Stage B): {runtime:.1f} s.",
        "",
        "## Quality gate",
        "",
        "The full all-spaxel 2397-bin emission-line model exceeded the wall-clock budget",
        "(58 min, killed at 157/2397 spectra).  Therefore:",
        "",
        "* `all_spaxel_dap_completed = false`",
        "* the accepted production result is this **9-bin official subset**;",
        "* the published SDSS DAP MAPS is the all-spaxel reference;",
        "* the fast fixed-continuum all-spaxel product, if present, is in `aux_fastmode/`",
        "  and is flagged `FASTMODE_NOT_PRODUCTION`; it is not an acceptance product.",
        "",
        "## Comparison",
        "",
        f"The comparison against the published MAPS is in `subset_comparison.json` and",
        f"`subset_comparison_lines.csv`.  See `subset_bins.csv` for the 9 bin measurements.",
        "",
        "## Limitations",
        "",
        "* Nine central bins are not a spatially complete DAP map.  The all-spaxel maps are",
        "  the published reference, not this run.",
        "* The DAP is a narrow-line single-Gaussian model (no broad lines, Fe II or Balmer",
        "  continuum).",
        "* Formal errors are from the DAP SASUKE covariance, not an independent error budget.",
        "",
        "## Reproduction",
        "",
        "Use the committed `fits/dap_binned_spectra.fits.gz` and",
        "`fits/dap_stellar_continuum.fits.gz` with `Tools/manga_dap/run_official_subset.py`",
        "and the committed `plan_subset.toml`.",
    ]
    (out / "provenance.md").write_text("\n".join(prov) + "\n")
    print(f"subset status=ok_subset bins={len(selected_ids)} runtime={runtime:.1f}s out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
