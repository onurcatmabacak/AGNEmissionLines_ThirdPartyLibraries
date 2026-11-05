#!/usr/bin/env python3
"""Fit a raw SAS PN spectrum with XSPEC/PyXspec."""
from __future__ import annotations
import argparse, json, math, os
from pathlib import Path
from xspec import AllData, AllModels, Model, Fit, Xset

p = argparse.ArgumentParser()
p.add_argument("--out", type=Path, required=True)
p.add_argument("--z", type=float, required=True)
a = p.parse_args()
out = a.out.resolve()
import os; os.chdir(out)
src = out / "pn_raw_src.ds"
bg = out / "pn_raw_bgd.ds"
rmf = out / "pn_raw_src.rmf"
arf = out / "pn_raw_src.arf"
AllData.clear(); AllData("1:1 " + str(src))
s = AllData(1); s.response = str(rmf); s.response.arf = str(arf); s.background = str(bg)
AllData.ignore("bad"); AllData.ignore("0.0-0.5 10.0-**")
Xset.abund = "wilm"; Fit.statMethod = "chi"; Fit.query = "no"; Fit.nIterations = 1000
Model("tbabs*zpowerlw"); Fit.perform()
base = {"chi2": float(Fit.statistic), "dof": int(Fit.dof),
        "nH": float(AllModels(1).TBabs.nH.values[0]),
        "nH_err": float(AllModels(1).TBabs.nH.sigma),
        "gamma": float(AllModels(1).zpowerlw.PhoIndex.values[0]),
        "gamma_err": float(AllModels(1).zpowerlw.PhoIndex.sigma),
        "norm": float(AllModels(1).zpowerlw.norm.values[0])}
Model("tbabs*(zpowerlw+zgauss)")
z = AllModels(1).zgauss
z.LineE = 6.4 / (1.0 + a.z); z.LineE.frozen = True
z.Sigma = 0.05; z.Sigma.frozen = True
Fit.perform()
line = {"chi2": float(Fit.statistic), "dof": int(Fit.dof),
        "nH": float(AllModels(1).TBabs.nH.values[0]),
        "nH_err": float(AllModels(1).TBabs.nH.sigma),
        "gamma": float(AllModels(1).zpowerlw.PhoIndex.values[0]),
        "gamma_err": float(AllModels(1).zpowerlw.PhoIndex.sigma),
        "line_norm": float(z.norm.values[0]),
        "line_norm_err": float(z.norm.sigma),
        "line_energy": float(z.LineE.values[0]),
        "line_sigma": float(z.Sigma.values[0])}
e_obs = 6.4 / (1.0 + a.z)
line["line_flux_erg_cm2_s"] = line["line_norm"] * e_obs * 1.602176634e-9
line["line_flux_err"] = line["line_norm_err"] * e_obs * 1.602176634e-9
res = {"source": str(src), "z": a.z, "baseline": base, "line": line,
       "dchi2": base["chi2"] - line["chi2"], "ddof": base["dof"] - line["dof"]}
(out / "raw_fit_summary.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps(res, indent=2))
