#!/usr/bin/env python3
"""Small decision engine: choose SED, line, host, or ratio tools.

Examples
--------
    python pipeline/decide_tools.py --goal lines --z 0.59 --wave-min 3800 --wave-max 9200
    python pipeline/decide_tools.py --goal sed --z 0.59 --bands SDSS+WISE
    python pipeline/decide_tools.py --goal lines --z 0.18 --wave-min 5 --wave-max 28 --instrument JWST/MIRI

Wavelengths are observed microns unless ``--angstrom`` is given.  The output is
advisory: source manifests still decide which tools actually run.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.tool_registry import TOOLS  # noqa: E402


def choose(goal: str, z: float, wmin: float, wmax: float, instrument: str = "") -> dict:
    rest_min, rest_max = wmin / (1 + z), wmax / (1 + z)
    names: list[str] = []
    reasons: list[str] = []
    if goal in ("sed", "both"):
        names += ["cigale_sed", "agnfitter_sed"]
        reasons.append("broad-band SED/torus: use template SED models; they do not measure individual lines")
    if goal in ("host", "both"):
        names += ["ppxf_host", "gandalf_line"]
        reasons.append("stellar host/continuum decomposition")
    if goal == "xray" or any(k in instrument.upper() for k in ("RXTE", "PCA")):
        names += ["rxte_xspec"]
        reasons.append("X-ray: official RXTE/PCA stdprod fit with HEASoft/PyXspec (Fe K-alpha)")
    if goal in ("lines", "both"):
        # UV/optical coverage
        if rest_max >= 0.10 and rest_min <= 1.0:
            names += ["pyqsofit_uv", "pyqsofitspec_line", "galspec_line", "qgfit", "sheap_line"]
            reasons.append("rest-frame UV/optical broad lines: PyQSOFit/PyQSOFitSpec/GalSpec/QGfit/SHEAP")
            names += ["ir_linefit"]
            reasons.append("generic local-Gaussian optical/UV line check")
        if rest_min < 1.1 and rest_max > 0.35:
            names += ["s3fit_line"]
            reasons.append("simultaneous spectrum+SED line decomposition")
        # NIR
        if rest_max >= 1.0 and rest_min <= 5.0:
            names += ["s3fit_line", "cafe_line", "nir_linefit"]
            reasons.append("NIR: S3Fit/CAFE for joint decomposition; nir_linefit for x1d/PSF spectra")
        # MIR
        if rest_max >= 5.0 and rest_min <= 30.0:
            names += ["cafe_line", "pahfit_mir"]
            reasons.append("MIR: CAFE for continuum/PAH/line; PAHFIT for PAH/dust/gas")
            if rest_max >= 10.0:
                names += ["ir_linefit"]
                reasons.append("MIR fine-structure lines: generic Gaussian fitter")
        # FIR
        if rest_max >= 30.0:
            names += ["fir_linefit"]
            reasons.append("FIR: dedicated PACS/HIFI Gaussian fitter")
        # line-ratio consistency
        if rest_max >= 10.0:
            names += ["crossband"]
            reasons.append("cross-band ratio consistency when multiple lines are measured")
    # Coverage-based caveat for SED tools
    if goal in ("sed", "both"):
        reasons.append("CIGALE/AGNfitter need photometry, not a spectrum; they cannot replace PyQSOFit/CAFE/GANDALF")
    seen = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return {
        "goal": goal, "z": z, "observed_um": [wmin, wmax],
        "rest_um": [rest_min, rest_max], "instrument": instrument,
        "tools": seen, "reasons": reasons,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--goal", choices=["sed", "lines", "host", "both", "xray"], default="lines")
    p.add_argument("--z", type=float, required=True)
    p.add_argument("--wave-min", type=float, required=True)
    p.add_argument("--wave-max", type=float, required=True)
    p.add_argument("--angstrom", action="store_true")
    p.add_argument("--instrument", default="")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    fac = 1e-4 if a.angstrom else 1.0
    out = choose(a.goal, a.z, a.wave_min * fac, a.wave_max * fac, a.instrument)
    if a.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"goal={out['goal']} z={out['z']} rest={out['rest_um'][0]:.4g}-{out['rest_um'][1]:.4g} um")
        for t in out["tools"]:
            tool = next(x for x in TOOLS if x.name == t)
            print(f"  {t:15s} {tool.kind:5s} {tool.uncertainty}")
        print("reasons:")
        for r in out["reasons"]:
            print(" -", r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
