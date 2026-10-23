#!/usr/bin/env python3
"""Compare pipeline x1d, 3x3, and PSF NIR extractions (S/N and FWHM)."""
from __future__ import annotations
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs/J0100p2802_z_6.3270/nir_linefit"
CASES = {"pipeline x1d": BASE, "QSO 3x3": BASE / "centered", "PSF r=3": BASE / "psf"}


def read(d, comp="broad"):
    for p in d.glob("*.measurements.csv"):
        with p.open() as fh:
            for r in csv.DictReader(fh):
                if r["line"] == "Halpha6563" and r["component"] == comp:
                    return r
    return None


def main():
    rows = [(k, read(d)) for k, d in CASES.items()]
    rows = [(k, r) for k, r in rows if r]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    x = range(len(rows))
    axes[0].bar(x, [float(r["snr"]) for _, r in rows], color="C2")
    axes[0].set_xticks(x); axes[0].set_xticklabels([k for k, _ in rows], rotation=20)
    axes[0].set_ylabel("broad Hα S/N"); axes[0].set_title("NIR Hα detection")
    axes[1].bar(x, [float(r["fwhm_kms"]) for _, r in rows], color="C0")
    axes[1].set_xticks(x); axes[1].set_xticklabels([k for k, _ in rows], rotation=20)
    axes[1].set_ylabel("broad Hα FWHM (km/s)"); axes[1].set_title("NIR Hα width")
    for ax in axes:
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out = ROOT / "docs/nir_extraction_comparison.png"
    fig.savefig(out, dpi=150); fig.savefig(out.with_suffix(".pdf"))
    print("wrote", out)
    for k, r in rows:
        print(k, "S/N", r["snr"], "FWHM", r["fwhm_kms"])


if __name__ == "__main__":
    raise SystemExit(main())
