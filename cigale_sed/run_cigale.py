#!/usr/bin/env python3
"""Minimal CIGALE SED/torus fit for a photometric catalogue."""
from __future__ import annotations
import csv
import os
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from astropy.table import Table
from configobj import ConfigObj


def call(args):
    # Fresh process for each CIGALE command: main() sets the multiprocessing
    # start method, which can only be done once per process.
    code = "from pcigale import main; main()"
    r = subprocess.run([sys.executable, "-c", code] + args,
                       capture_output=True, text=True, cwd="/app/output",
                       env=os.environ.copy())
    print(r.stdout[-3000:])
    if r.returncode:
        print("STDERR:", r.stderr[-5000:])
        raise SystemExit(f"pcigale {args} failed with {r.returncode}")


def main():
    work = Path("/app/output"); work.mkdir(parents=True, exist_ok=True)
    cfg_path = work / "pcigale.ini"
    # pcigale init creates pcigale.ini + pcigale.ini.spec; then we fill the
    # template and let genconf add the module parameter sections.
    call(["-c", str(cfg_path), "init"])
    cfg = ConfigObj(str(cfg_path), encoding="utf-8")
    data_file = Path("/app/input/photometry.txt")
    cfg["data_file"] = str(data_file)
    cfg["parameters_file"] = ""
    agn_model = os.environ.get("CIGALE_AGN_MODEL", "skirtor2016")
    if agn_model not in ("skirtor2016", "fritz2006"):
        raise SystemExit(f"unsupported CIGALE_AGN_MODEL={agn_model}")
    cfg["sed_modules"] = ["sfhdelayed", "bc03", "dustatt_modified_starburst",
                          "dl2014", agn_model, "redshifting"]
    cfg["analysis_method"] = "pdf_analysis"
    cfg["cores"] = "4"
    cfg.write()
    call(["-c", str(cfg_path), "genconf"])

    # Modest but meaningful model grid (a single value per parameter would
    # produce exactly one model per object, i.e. no actual SED fit).
    grid = {
        "sfhdelayed": {
            "tau_main": [1000.0, 3000.0],
            "age_main": [2000, 5000, 10000],
            "tau_burst": [50.0],
            "age_burst": [20],
            "f_burst": [0.0, 0.1, 0.3],
            "normalise": True,
        },
        "bc03": {
            "imf": 0,
            "metallicity": [0.008, 0.02],
            "separation_age": 10,
        },
        "dustatt_modified_starburst": {
            "E_BV_lines": [0.0, 0.05, 0.1, 0.3, 0.6, 1.0],
            "E_BV_factor": [0.44],
            "uv_bump_wavelength": [217.5],
            "uv_bump_width": [35.0],
            "uv_bump_amplitude": [0.0, 1.0],
            "powerlaw_slope": [0.0],
            "Ext_law_emission_lines": [1],
            "Rv": [3.1],
            "filters": "galex.FUV & generic.bessell.B & generic.bessell.V",
        },
        "dl2014": {
            "qpah": [1.0, 2.5, 4.0],
            "umin": [1.0, 5.0, 10.0],
            "alpha": [2.0],
            "gamma": [0.1],
        },
        "skirtor2016": {
            "t": [3, 7, 11],
            "pl": [1.0],
            "q": [1.0],
            "oa": [40],
            "R": [20],
            "Mcl": [0.97],
            "i": [30],
            "disk_type": 1,
            "fracAGN": [0.1, 0.3, 0.5, 0.7, 0.9, 0.99],
            "law": [0],
            "EBV": [0.0, 0.03, 0.1],
            "temperature": [100.0],
            "emissivity": [1.6],
        },
        "fritz2006": {
            "r_ratio": [60.0],
            "tau": [1.0, 3.0],
            "beta": [-0.5],
            "gamma": [4.0],
            "opening_angle": [100.0],
            "psy": [30.1, 70.1],
            "disk_type": 1,
            "delta": [-0.36],
            "fracAGN": [0.1, 0.5, 0.9, 0.99],
            "law": [0],
            "EBV": [0.03],
            "temperature": [100.0],
            "emissivity": [1.6],
        },
    }
    cfg = ConfigObj(str(cfg_path), encoding="utf-8")
    for module, params in grid.items():
        if module not in (agn_model, "sfhdelayed", "bc03",
                          "dustatt_modified_starburst", "dl2014"):
            continue
        for key, value in params.items():
            cfg["sed_modules_params"][module][key] = value
    cfg["analysis_params"]["save_best_sed"] = True
    cfg.write()
    print("=== generated pcigale.ini sections ===")
    print(Path(cfg_path).read_text()[:4000])
    call(["-c", str(cfg_path), "run"])
    plot_results(work, agn_model)
    return 0


PIVOT_UM = {
    "sloan.sdss.g": 0.47025,
    "sloan.sdss.r": 0.61756,
    "sloan.sdss.i": 0.74900,
    "sloan.sdss.z": 0.89467,
    "wise.W1": 3.37,
    "wise.W2": 4.62,
    "wise.W3": 12.07,
    "wise.W4": 22.19,
}


def _f(row, key):
    try:
        return float(row[key])
    except Exception:
        return float("nan")


def plot_results(work: Path, agn_model: str = "skirtor2016"):
    """Plot observed photometry versus the CIGALE best-fit band fluxes."""
    obs = Table.read(work / "out" / "observations.fits")
    res = Table.read(work / "out" / "results.fits")
    bands = [b for b in PIVOT_UM if b in obs.colnames]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True, sharey=False)
    axes = axes.ravel()
    rows = []
    for i in range(len(obs)):
        ax = axes[i]
        x = np.array([PIVOT_UM[b] for b in bands])
        y = np.array([_f(obs[i], b) for b in bands])
        yerr = np.array([_f(obs[i], b + "_err") for b in bands])
        ymod = np.array([_f(res[i], "best." + b) for b in bands])
        ax.errorbar(x, y, yerr=yerr, fmt="o", ms=5, color="C0",
                    label="observed", zorder=3)
        ax.plot(x, ymod, "s", ms=5, color="C1", label="CIGALE best", zorder=4)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(r"observed wavelength ($\mu$m)")
        ax.set_ylabel("flux density (mJy)")
        ax.grid(True, which="both", alpha=0.25)
        ax.set_title(
            f"{obs['id'][i]}  z={float(obs['redshift'][i]):.3f}  "
            f"chi2_nu={float(res['best.reduced_chi_square'][i]):.2f}",
            fontsize=9,
        )
        if i == 0:
            ax.legend(fontsize=8)
        chi = {}
        for b in bands:
            err = _f(obs[i], b + "_err")
            if np.isfinite(err) and err > 0:
                chi[b] = ((_f(obs[i], b) - _f(res[i], "best." + b)) / err) ** 2
        chi_opt = float(sum(chi.get(b, 0.0) for b in bands if b.startswith("sloan.")))
        chi_wise = float(sum(chi.get(b, 0.0) for b in bands if b.startswith("wise.")))
        rows.append({
            "id": str(obs["id"][i]),
            "agn_model": agn_model,
            "redshift": float(obs["redshift"][i]),
            "chi2": _f(res[i], "best.chi_square"),
            "reduced_chi2": _f(res[i], "best.reduced_chi_square"),
            "fracAGN": _f(res[i], "best.agn.fracAGN"),
            "agn_t": _f(res[i], "best.agn.t"),
            "agn_EBV": _f(res[i], "best.agn.EBV"),
            "agn_luminosity_W": _f(res[i], "best.agn.luminosity"),
            "agn_torus_luminosity_W": _f(res[i], "best.agn.torus_dust_luminosity"),
            "dust_luminosity_W": _f(res[i], "best.dust.luminosity"),
            "m_star_Msun": _f(res[i], "best.stellar.m_star"),
            "sfr_Msun_per_yr": _f(res[i], "best.sfh.sfr"),
            "chi2_optical": chi_opt,
            "chi2_wise": chi_wise,
            "wise_outlier": bool(np.isfinite(chi_wise) and chi_wise > 3.0 * 4),
        })
    for ax in axes[len(obs):]:
        ax.axis("off")
    fig.suptitle("CIGALE SED/torus fits — SDSS + WISE", fontsize=12)
    fig.tight_layout()
    fig.savefig(work / "sed_fit.png", dpi=150)
    fig.savefig(work / "sed_fit.pdf")
    with open(work / "sed_summary.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
