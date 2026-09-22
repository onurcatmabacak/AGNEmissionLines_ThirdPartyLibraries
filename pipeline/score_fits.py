#!/usr/bin/env python3
"""Extract a tool-agnostic score + line measurements from each tool's output.

Reads the tidy run tree ``runs/<tag>/outputs/<tool>/`` and writes:

    results/scores.csv   tag, tool, chi2_red, chi2_kind, n_lines
    results/lines.csv    tag, tool, line, component, flux_1e17, fwhm_kms, ew_a, center_a, flux_unit

"Best = lowest chi-square": reduced chi-square is the primary metric.  It is only
strictly comparable between tools that publish a data+model grid, so ``chi2_kind``
records what was actually measured:

    pyqsofit   mean of the per-complex line reduced chi-square (Hb, Ha)   [reported]
    badass     computed (DATA vs MODEL) over the line windows             [grid]
    fantasy    computed (flux vs model) over the line windows             [grid]
    gleam      mean per-line reduced chi-square from the log              [reported]
    gelato     n/a  (its saved SUMMARY model/chi2 are numerically degenerate)

Line fluxes are integrated per kinematic component and normalised to
1e-17 erg s-1 cm-2 wherever the tool's convention is known.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path

import numpy as np

REST = {
    "OII3727": 3727.0, "Hb4861": 4861.0, "OIII4959": 4959.0, "OIII5007": 5007.0,
    "Ha6563": 6563.0, "NII6585": 6585.0, "SII6718": 6718.0, "SII6732": 6732.0,
}
# half-width (Angstrom, rest frame) for integrating a narrow component; keeps
# close doublets ([NII]/Ha, [SII] pair) from overlapping.
NARROW_HALF = {"OII3727": 20, "Hb4861": 20, "OIII4959": 20, "OIII5007": 20,
               "Ha6563": 10, "NII6585": 10, "SII6718": 6, "SII6732": 6}
BROAD_HALF = 150.0
CHI2_HALF = 30.0
TOOLS = ("pyqsofit", "badass", "fantasy_agn", "gelato", "gleam")


def _f(x, default=float("nan")):
    if hasattr(x, "value"):
        x = x.value
    try:
        v = float(x)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def _nearest_line(center):
    if not math.isfinite(center):
        return None
    best = min(REST, key=lambda k: abs(REST[k] - center))
    return best if abs(REST[best] - center) < 12 else None


def _integrate(wave, y, line, component):
    """Integrate a component over the line window (rest frame)."""
    half = BROAD_HALF if component in ("broad", "outflow", "total") else NARROW_HALF.get(line, 15)
    m = np.isfinite(y) & (np.abs(wave - REST[line]) < half)
    return float(np.trapz(y[m], wave[m])) if m.sum() > 1 else np.nan


def _line_chi2(wave, flux, model, err):
    good = np.isfinite(flux) & np.isfinite(model) & (err > 0)
    win = np.zeros_like(good)
    for w0 in REST.values():
        win |= np.abs(wave - w0) < CHI2_HALF
    m = good & win
    if m.sum() < 3:
        return np.nan
    return float(np.sum(((flux[m] - model[m]) / err[m]) ** 2) / max(m.sum() - 1, 1))


def _rec(tag, tool, line, component, flux=np.nan, fwhm=np.nan, ew=np.nan, center=np.nan):
    return {"tag": tag, "tool": tool, "line": line, "component": component,
            "flux_1e17": flux, "fwhm_kms": fwhm, "ew_a": ew, "center_a": center, "flux_unit": "1e-17"}


# --------------------------- PyQSOFit ----------------------------------------
def parse_pyqsofit(out: Path, tag: str):
    import warnings
    warnings.filterwarnings("ignore")
    from astropy.io import fits

    f = out / "output.fits"
    if not f.exists():
        return None, []
    d = fits.open(f)[1].data
    chis = [x for x in (_f(d[f"{i}_line_red_chi2"][0]) for i in (1, 2)) if math.isfinite(x)]
    score = {"tag": tag, "tool": "pyqsofit",
             "chi2_red": float(np.mean(chis)) if chis else np.nan,
             "chi2_kind": "line_complex_reduced (reported)"}
    rows = []
    for whole, line in (("Ha_whole_br", "Ha6563"), ("Hb_whole_br", "Hb4861")):
        if f"{whole}_area" in d.columns.names:
            rows.append(_rec(tag, "pyqsofit", line, "broad",
                             flux=_f(d[f"{whole}_area"][0]), fwhm=_f(d[f"{whole}_fwhm"][0]),
                             ew=_f(d[f"{whole}_ew"][0])))
    comps = {
        "OIII5007w_1": ("OIII5007", "outflow"), "OIII5007c_1": ("OIII5007", "narrow"),
        "OIII4959w_1": ("OIII4959", "outflow"), "OIII4959c_1": ("OIII4959", "narrow"),
        "Ha_na_1": ("Ha6563", "narrow"), "NII6585_1": ("NII6585", "narrow"),
        "SII6718_1": ("SII6718", "narrow"), "SII6732_1": ("SII6732", "narrow"),
    }
    for col, (line, comp) in comps.items():
        k = f"{col}_scale"
        if k not in d.columns.names:
            continue
        center_log = _f(d[f"{col}_centerwave"][0])
        center_a = math.exp(center_log) if math.isfinite(center_log) else np.nan
        # scale is the Gaussian peak in 1e-17 units; integrate over lambda
        sig = _f(d[f"{col}_sigma"][0])
        flux = _f(d[k][0]) * sig * math.sqrt(2 * math.pi) * center_a if math.isfinite(center_a) else np.nan
        rows.append(_rec(tag, "pyqsofit", line, comp, flux=flux, center=center_a))
    return score, rows


# --------------------------- BADASS3 -----------------------------------------
def parse_badass(out: Path, tag: str):
    comp_file = None
    for cand in out.rglob("best_model_components.fits"):
        comp_file = cand
        break
    rows = []
    if comp_file is not None:
        import warnings
        warnings.filterwarnings("ignore")
        from astropy.io import fits
        d = fits.open(comp_file)[1].data
        wave = np.asarray(d["WAVE"], float)
        data = np.asarray(d["DATA"], float)
        model = np.asarray(d["MODEL"], float)
        noise = np.asarray(d["NOISE"], float)
        chi2 = _line_chi2(wave, data, model, np.abs(noise))
        cmap = {
            "BR_H_ALPHA": ("Ha6563", "broad"), "NA_H_ALPHA": ("Ha6563", "narrow"),
            "H_ALPHA_COMP": ("Ha6563", "outflow"),
            "BR_H_BETA": ("Hb4861", "broad"), "NA_H_BETA": ("Hb4861", "narrow"),
            "H_BETA_COMP": ("Hb4861", "outflow"),
            "BR_OIII_b": ("OIII5007", "broad"), "NA_OIII_b": ("OIII5007", "narrow"),
            "OIII_b_COMP": ("OIII5007", "outflow"),
            "BR_OIII_a": ("OIII4959", "broad"), "NA_OIII_a": ("OIII4959", "narrow"),
            "OIII_a_COMP": ("OIII4959", "outflow"),
            "BR_OII": ("OII3727", "broad"), "NA_OII": ("OII3727", "narrow"),
        }
        for col, (line, comp) in cmap.items():
            if col in d.columns.names:
                rows.append(_rec(tag, "badass", line, comp,
                                 flux=_integrate(wave, np.asarray(d[col], float), line, comp)))
        score = {"tag": tag, "tool": "badass", "chi2_red": chi2, "chi2_kind": "line_window_computed"}
        return score, rows

    # fallback: reported value from the log
    log = out / "fit.log"
    if not log.exists():
        return None, []
    text = log.read_text(errors="ignore")
    m = re.search(r"^RCHI_SQUARED\s+([\d.eE+-]+)", text, re.M)
    score = {"tag": tag, "tool": "badass", "chi2_red": _f(m.group(1)) if m else np.nan,
             "chi2_kind": "global_reduced (reported)"}
    return score, rows


# --------------------------- fantasy_agn -------------------------------------
def parse_fantasy(out: Path, tag: str):
    csvp = out / "my_sdss_model.csv"
    if not csvp.exists():
        return None, []
    try:
        arr = np.genfromtxt(csvp, delimiter=",", skip_header=1)
    except Exception:
        return None, []
    if arr.ndim != 2 or arr.shape[1] < 12:
        return None, []
    wave, flux, err, model = arr[:, 1], arr[:, 2], arr[:, 3], arr[:, 4]
    chi2 = _line_chi2(wave, flux, model, np.abs(err))
    score = {"tag": tag, "tool": "fantasy_agn", "chi2_red": chi2, "chi2_kind": "line_window_computed"}
    rows = []
    for idx, (line, comp) in {
        6: ("OIII5007", "broad"), 7: ("OIII5007", "narrow"),
        8: ("Hb4861", "broad"), 9: ("Hb4861", "narrow"),
        10: ("Ha6563", "broad"), 11: ("Ha6563", "narrow"),
    }.items():
        rows.append(_rec(tag, "fantasy_agn", line, comp,
                         flux=_integrate(wave, arr[:, idx], line, comp)))
    return score, rows


# --------------------------- GELATO ------------------------------------------
def parse_gelato(out: Path, tag: str):
    import warnings
    warnings.filterwarnings("ignore")
    from astropy.io import fits

    f = out / "my_sdss-results.fits"
    if not f.exists():
        return None, []
    p = fits.open(f)["PARAMS"].data
    pairs = [
        ("AGN_[OIII]_5007.0_Flux", "OIII5007", "narrow"),
        ("AGN_[OIII]_4958.0_Flux", "OIII4959", "narrow"),
        ("Balmer_HI_6551.0_Flux", "Ha6563", "broad"),
        ("Balmer_HI_4834.0_Flux", "Hb4861", "broad"),
        ("AGN_[NII]_6585.27_Flux", "NII6585", "narrow"),
        ("AGN_[SII]_6718.29_Flux", "SII6718", "narrow"),
        ("AGN_[SII]_6732.67_Flux", "SII6732", "narrow"),
        ("SF_[OII]_3728.48_Flux", "OII3727", "narrow"),
    ]
    rows = []
    for col, line, comp in pairs:
        if col in p.columns.names:
            disp = col.replace("_Flux", "_Dispersion")
            rows.append(_rec(tag, "gelato", line, comp, flux=_f(p[col][0]) * 1e17,
                             fwhm=_f(p[disp][0]) if disp in p.columns.names else np.nan))
    score = {"tag": tag, "tool": "gelato", "chi2_red": np.nan,
             "chi2_kind": "n/a (degenerate summary)"}
    return score, rows


# --------------------------- GLEAM -------------------------------------------
def parse_gleam(out: Path, tag: str):
    # reduced chi-square is only in the verbose LMFIT log
    chis = []
    log = out / "docker.log"
    if log.exists():
        for blk in re.split(r"\[\[Model\]\]", log.read_text(errors="ignore"))[1:]:
            m = re.search(r"reduced chi-square\s*=\s*([\d.eE+-]+)", blk)
            if m:
                chis.append(_f(m.group(1)))
    score = {"tag": tag, "tool": "gleam",
             "chi2_red": float(np.mean(chis)) if chis else np.nan,
             "chi2_kind": "mean_line_reduced (reported)"}

    # Preferred: GLEAM's own per-line results table (linefits*.fits)
    tables = sorted(out.glob("linefits*.fits"))
    if tables:
        import warnings
        warnings.filterwarnings("ignore")
        from astropy.table import Table

        rows = []
        for f in tables:
            try:
                t = Table.read(f)
            except Exception:
                continue
            names = {c.lower(): c for c in t.colnames}
            wlc = names.get("wavelength") or names.get("wl")
            for r in t:
                wl = _f(r[wlc]) if wlc else np.nan
                line = _nearest_line(wl)
                if line is None:
                    continue
                if "detected" in names and not bool(r[names["detected"]]):
                    continue
                fwhm_a = _f(r[names["fwhm"]]) if "fwhm" in names else np.nan
                # GLEAM reports FWHM in Angstrom (rest frame); convert to km/s
                fwhm_kms = fwhm_a / wl * 299792.458 if (wl and math.isfinite(fwhm_a)) else np.nan
                rows.append(_rec(tag, "gleam", line, "total",
                                 flux=_f(r[names["flux"]]) if "flux" in names else np.nan,
                                 fwhm=fwhm_kms,
                                 ew=_f(r[names["ewrest"]]) if "ewrest" in names else np.nan,
                                 center=wl))
        if rows:
            return score, rows

    # Fallback: parse the verbose log (older runs without the table)
    rows = []
    if log.exists():
        for blk in re.split(r"\[\[Model\]\]", log.read_text(errors="ignore"))[1:]:
            for g in re.finditer(
                r"(g\d+)_amplitude:\s*([\d.eE+-]+).*?\n\s*\1_center:\s*([\d.eE+-]+).*?\n\s*\1_sigma:\s*([\d.eE+-]+)",
                blk, re.S,
            ):
                center = _f(g.group(3))
                line = _nearest_line(center)
                if line:
                    rows.append(_rec(tag, "gleam", line, "total", flux=_f(g.group(2)), center=center))
    return score, rows


PARSERS = {
    "pyqsofit": parse_pyqsofit, "badass": parse_badass, "fantasy_agn": parse_fantasy,
    "gelato": parse_gelato, "gleam": parse_gleam,
}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--runs", type=Path, default=Path("runs"))
    p.add_argument("--results", type=Path, default=Path("results"))
    args = p.parse_args(argv)
    args.results.mkdir(parents=True, exist_ok=True)

    scores, lines = [], []
    for obj in sorted(x for x in args.runs.iterdir() if x.is_dir()):
        outroot = obj / "outputs"
        if not outroot.is_dir():
            continue
        for tool in TOOLS:
            out = outroot / tool
            if not out.is_dir():
                continue
            try:
                sc, lrows = PARSERS[tool](out, obj.name)
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] {tool} {obj.name}: {exc}")
                continue
            if sc:
                scores.append(sc)
                lines.extend(lrows)

    with (args.results / "scores.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["tag", "tool", "chi2_red", "chi2_kind"])
        w.writeheader(); w.writerows(scores)
    with (args.results / "lines.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["tag", "tool", "line", "component",
                                           "flux_1e17", "fwhm_kms", "ew_a", "center_a", "flux_unit"])
        w.writeheader(); w.writerows(lines)
    print(f"scored {len(scores)} tool run(s); extracted {len(lines)} line measurement(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
