"""CLI: route an SDSS/IR spectrum and fit its IR/optical emission lines."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .spectrum import read_spectrum, Spectrum
from .router import route, Route
from .fit import fit_group, Measurement


def _figure(spec: Spectrum, rt: Route, rows: list[Measurement], out: Path):
    fig, ax = plt.subplots(figsize=(12, 5))
    m = spec.mask
    ax.plot(spec.wave_um[m], spec.flux[m], color="0.35", lw=0.7, label="observed")
    for r in rows:
        if r.detected:
            ln = next((c for c in rt.lines if c.line.name == r.line), None)
            if ln is not None:
                ax.axvline(ln.obs_um, color="C3", alpha=0.5, lw=0.8)
                ax.text(ln.obs_um, np.nanmax(spec.flux[m]) * 0.92,
                        f"{r.line}\n{r.component}", rotation=90, fontsize=6,
                        ha="right", va="top", color="C3")
    ax.set_xlabel("observed wavelength (um)")
    ax.set_ylabel("flux (1e-17 erg s-1 cm-2 A-1)")
    ax.set_title(f"{spec.object_id}  z={spec.z:.4f}  band={spec.band}  suites={','.join(rt.suites) or '-'}")
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(out.with_suffix(".png"), dpi=130, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def run_one(path: Path, outdir: Path, z=None, band=None, dry=False):
    spec = read_spectrum(path, z_override=z, band=band)
    rt = route(spec)
    outdir.mkdir(parents=True, exist_ok=True)
    stem = outdir / spec.object_id
    (stem.with_suffix(".route.json")).write_text(json.dumps({
        "object_id": spec.object_id, "z": spec.z, "band": spec.band,
        "status": rt.status, "suites": rt.suites, "resolution": rt.resolution,
        "wave_min_um": rt.wave_min, "wave_max_um": rt.wave_max,
        "reasons": rt.reasons,
        "lines": [{"line": c.line.name, "rest_um": c.line.rest_um, "obs_um": c.obs_um,
                   "suite": c.suite, "covered": c.covered, "measurable": c.measurable,
                   "snr_est": c.snr_est, "reason": c.reason} for c in rt.lines],
        "groups": {k: [c.line.name for c in v] for k, v in rt.groups.items()},
    }, indent=2, default=float))
    if dry:
        print(f"[router] {spec.object_id} z={spec.z:.4f} band={spec.band} "
              f"status={rt.status} suites={rt.suites} groups={list(rt.groups)}")
        return []
    rows: list[Measurement] = []
    for key, group in rt.groups.items():
        mrows, chi2 = fit_group(spec, group, spec.z)
        rows.extend(mrows)
    csvp = stem.with_suffix(".measurements.csv")
    with csvp.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["object_id", "z", "band", "line", "component", "flux_1e17",
                    "flux_err", "flux_limit", "fwhm_kms", "fwhm_err", "center_um",
                    "ew_a", "snr", "detected", "status", "chi2_red", "n_pix"])
        for r in rows:
            w.writerow([spec.object_id, spec.z, spec.band, r.line, r.component,
                        r.flux, r.flux_err, r.flux_limit, r.fwhm_kms, r.fwhm_err,
                        r.center_um, r.ew_a, r.snr, int(r.detected), r.status,
                        r.chi2_red, r.n_pix])
    _figure(spec, rt, rows, stem.with_suffix(".fit"))
    print(f"[fit] {spec.object_id} z={spec.z:.4f} {spec.band}: {len(rows)} components "
          f"({sum(r.detected for r in rows)} detected) -> {csvp}")
    return rows


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fits", nargs="*", default=[])
    p.add_argument("--input-dir", type=Path, default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--out", type=Path, default=Path("results_ir"))
    p.add_argument("--z", type=float, default=None)
    p.add_argument("--band", default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    files = [Path(f) for f in args.fits]
    if args.input_dir:
        files += sorted(args.input_dir.glob("*.fits"))
    if args.limit:
        files = files[:args.limit]
    if not files:
        p.error("give --fits and/or --input-dir")
    allrows = []
    for f in files:
        allrows += run_one(f, args.out, z=args.z, band=args.band, dry=args.dry_run)
    if allrows:
        print(f"[done] {len(allrows)} component measurements across {len(files)} spectra")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
