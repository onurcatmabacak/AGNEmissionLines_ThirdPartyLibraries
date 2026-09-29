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
import json
import math
import re
from pathlib import Path

import numpy as np

REST = {
    "OII3727": 3727.0, "Hb4861": 4861.0, "OIII4959": 4959.0, "OIII5007": 5007.0,
    "Ha6563": 6563.0, "NII6548": 6549.0, "NII6585": 6585.0,
    "SII6718": 6718.0, "SII6732": 6732.0,
}
# half-width (Angstrom, rest frame) for integrating a narrow component; keeps
# close doublets ([NII]/Ha, [SII] pair) from overlapping.
NARROW_HALF = {"OII3727": 20, "Hb4861": 20, "OIII4959": 20, "OIII5007": 20,
               "Ha6563": 10, "NII6548": 6, "NII6585": 10, "SII6718": 6, "SII6732": 6}
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


def _rec(tag, tool, line, component, flux=np.nan, fwhm=np.nan, ew=np.nan, center=np.nan,
         flux_err=np.nan):
    return {"tag": tag, "tool": tool, "line": line, "component": component,
            "flux_1e17": flux, "flux_err_1e17": flux_err, "fwhm_kms": fwhm,
            "ew_a": ew, "center_a": center, "flux_unit": "1e-17"}


# ---------------------------------------------------------------------------
# Common, tool-agnostic reduced chi-square.
#
# Every tool reports a different statistic (and PyQSOFit's shrinks when its
# internal error floor is raised).  To rank fits fairly we rebuild each tool's
# total model on the *same* prepared spectrum and the *same* calibrated errors:
# the prepared ``inputs/badass/my_sdss.fits`` (ivar is calibrated for 1e-17
# units) provides the common data vector.  Models are put on the rest-frame
# grid and compared over the main optical line windows.
# ---------------------------------------------------------------------------
def _load_common_data(obj_dir: Path, z: float):
    from astropy.io import fits
    d = fits.open(obj_dir / "inputs" / "badass" / "my_sdss.fits")[1].data
    obs = 10.0 ** np.asarray(d["loglam"], float)
    flux = np.asarray(d["flux"], float) * 1e17          # cgs -> 1e-17
    ivar = np.asarray(d["ivar"], float)
    return obs / (1.0 + z), flux, ivar


def _tool_model_rest(obj_dir: Path, tool: str, out: Path, wave_rest: np.ndarray, z: float = 0.0):
    """Return this tool's total model sampled on ``wave_rest`` (1e-17 units)."""
    if tool == "pyqsofit":
        p = out / "pyqsofit_model.csv"
        if not p.exists():
            return None
        arr = np.genfromtxt(p, delimiter=",", names=True)
        if arr.size == 0:
            return None
        return np.interp(wave_rest, np.atleast_1d(arr["wave"]), np.atleast_1d(arr["model"]))
    if tool == "badass":
        f = next(out.rglob("best_model_components.fits"), None)
        if f is None:
            return None
        from astropy.io import fits
        d = fits.open(f)[1].data
        return np.interp(wave_rest, np.asarray(d["WAVE"], float), np.asarray(d["MODEL"], float))
    if tool == "fantasy_agn":
        p = out / "my_sdss_model.csv"
        if not p.exists():
            return None
        arr = np.genfromtxt(p, delimiter=",", skip_header=1)
        if arr.ndim != 2 or arr.shape[1] < 5:
            return None
        return np.interp(wave_rest, arr[:, 1], arr[:, 4])
    if tool == "gelato":
        from astropy.io import fits
        f = out / "my_sdss-results.fits"
        if not f.exists():
            return None
        d = fits.open(f)["SUMMARY"].data
        # GELATO stores its model in the observed frame; the common grid is rest.
        w = 10.0 ** np.asarray(d["loglam"], float) / (1.0 + z)
        return np.interp(wave_rest, w, np.asarray(d["MODEL"], float))
    if tool == "gleam":
        from astropy.table import Table
        tables = sorted(out.glob("linefits*.fits"))
        if not tables:
            return None
        model = np.zeros_like(wave_rest)
        # GLEAM's per-line constant continuum is local to each line; take the
        # nearest line's value (overwrite, never sum) so overlapping windows from
        # duplicate lines do not double-count the continuum.
        cont_model = np.full_like(wave_rest, np.nan)
        for f in tables:
            try:
                t = Table.read(f)
            except Exception:
                continue
            names = {c.lower(): c for c in t.colnames}
            for r in t:
                def gv(n):
                    try:
                        return float(r[names[n]])
                    except Exception:
                        return np.nan
                wl, sig, amp = gv("wl"), gv("sigma"), gv("height")
                if np.isfinite(wl) and np.isfinite(sig) and sig > 0 and np.isfinite(amp):
                    model += amp * np.exp(-0.5 * ((wave_rest - wl) / sig) ** 2)
                cont = gv("cont")
                if np.isfinite(wl) and np.isfinite(cont):
                    cont_model[np.abs(wave_rest - wl) < CHI2_HALF] = cont
        model[np.isfinite(cont_model)] += cont_model[np.isfinite(cont_model)]
        return model
    return None


COMMON_ERR_FLOOR = 0.02   # relative flux error floor, shared by every tool


def line_penalty(lrows):
    """Physical-plausibility penalty for an extracted line decomposition.

    Lower is better; 0 is a physically clean decomposition.  It penalises a
    missing or wrong [OIII] 4959/5007 ratio (should be ~1/3) and a broad Balmer
    Halpha/Hbeta ratio outside the case-B range.  This is the metric that stops
    the optimiser from accepting a low chi-square fit that has thrown a line
    away.
    """
    def g(line, comp):
        for r in lrows:
            if r["line"] == line and r["component"] == comp:
                v = r["flux_1e17"]
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    return None
                return v if math.isfinite(v) else None
        return None

    pen = 0.0
    # [OIII] doublet: wherever 5007 is detected, 4959 must be present ~0.33x.
    for comp in ("narrow", "outflow", "broad"):
        f7 = g("OIII5007", comp)
        if f7 is None or f7 <= 0:
            continue
        f9 = g("OIII4959", comp)
        if f9 is None or f9 <= 0:
            pen += 1.0
        elif not (0.22 <= f9 / f7 <= 0.45):
            pen += 1.0
    # Broad Balmer decrement (case B gives Halpha/Hbeta ~ 2.8-3.3).
    ha, hb = g("Ha6563", "broad"), g("Hb4861", "broad")
    if ha and hb and hb > 0 and not (2.0 <= ha / hb <= 6.0):
        pen += 1.0
    return pen


def common_chi2(obj_dir: Path, tool: str, out: Path, z: float):
    """Reduced chi-square of the tool model against the common data vector.

    The raw inverse variance is combined in quadrature with a *fixed, common*
    relative flux floor (``COMMON_ERR_FLOOR``).  No tool controls this floor, so
    it cannot be gamed, while it keeps the metric from being dominated by the
    continuum S/N off the line cores.
    """
    try:
        wave_rest, flux, ivar = _load_common_data(obj_dir, z)
    except Exception:
        return np.nan
    try:
        model = _tool_model_rest(obj_dir, tool, out, wave_rest, z)
    except Exception:
        return np.nan
    if model is None:
        return np.nan
    sig = 1.0 / np.sqrt(np.clip(ivar, 1e-30, None))
    sig = np.sqrt(sig ** 2 + (COMMON_ERR_FLOOR * np.abs(flux)) ** 2)
    good = np.isfinite(flux) & np.isfinite(model) & (ivar > 0)
    win = np.zeros_like(good)
    for w0 in REST.values():
        win |= np.abs(wave_rest - w0) < CHI2_HALF
    m = good & win
    if m.sum() < 3:
        return np.nan
    return float(np.sum(((flux[m] - model[m]) / sig[m]) ** 2) / max(m.sum() - 1, 1))


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
                             ew=_f(d[f"{whole}_ew"][0]),
                             flux_err=_f(d[f"{whole}_area_err"][0]) if f"{whole}_area_err" in d.columns.names else np.nan))
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
        scale = _f(d[k][0])
        flux = scale * sig * math.sqrt(2 * math.pi) * center_a if math.isfinite(center_a) else np.nan
        # MC/MCMC error propagation: flux ~ scale * sigma * center.
        flux_err = np.nan
        if (f"{col}_scale_err" in d.columns.names and f"{col}_sigma_err" in d.columns.names
                and math.isfinite(flux) and scale != 0 and sig != 0):
            se = _f(d[f"{col}_scale_err"][0])
            ge = _f(d[f"{col}_sigma_err"][0])
            if math.isfinite(se) and math.isfinite(ge):
                flux_err = abs(flux) * math.sqrt((se / scale) ** 2 + (ge / sig) ** 2)
        rows.append(_rec(tag, "pyqsofit", line, comp, flux=flux, flux_err=flux_err, center=center_a))
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
        # Parameter-table errors (fit.log): PARAM  VALUE  ERROR  ...; the log
        # keeps the line name's case, so match case-insensitively.
        perr = {}
        log = out / "fit.log"
        if log.exists():
            for m in re.finditer(r"^(\S+_FLUX)\s+([-\d.eE+]+)\s+([-\d.eE+]+)",
                                 log.read_text(errors="ignore"), re.M):
                perr[m.group(1).upper()] = _f(m.group(3))
        for col, (line, comp) in cmap.items():
            if col in d.columns.names:
                rows.append(_rec(tag, "badass", line, comp,
                                 flux=_integrate(wave, np.asarray(d[col], float), line, comp),
                                 flux_err=perr.get(f"{col}_FLUX".upper(), np.nan)))
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
        with csvp.open() as fh:
            header = [h.strip() for h in fh.readline().rstrip("\n").split(",")]
            arr = np.genfromtxt(fh, delimiter=",", comments=None)
    except Exception:
        return None, []
    if arr.ndim != 2 or arr.shape[1] < 5:
        return None, []
    col = {name: i for i, name in enumerate(header)}

    def get(name):
        return arr[:, col[name]] if name in col else None

    wave, flux, err, model = get("wave"), get("flux"), get("error"), get("model")
    if wave is None or flux is None or err is None or model is None:
        return None, []
    chi2 = _line_chi2(wave, flux, model, np.abs(err))
    score = {"tag": tag, "tool": "fantasy_agn", "chi2_red": chi2, "chi2_kind": "line_window_computed"}
    # Read components by column name (the model now includes the [OIII] doublet
    # and [NII], so positional indices are no longer stable).
    cmap = {
        "OIIIb_br": ("OIII5007", "broad"), "OIIIb_na": ("OIII5007", "narrow"),
        "OIIIa_br": ("OIII4959", "broad"), "OIIIa_na": ("OIII4959", "narrow"),
        "hbeta_br": ("Hb4861", "broad"), "hbeta_na": ("Hb4861", "narrow"),
        "halpha_br": ("Ha6563", "broad"), "halpha_na": ("Ha6563", "narrow"),
        "NII6583_na": ("NII6585", "narrow"), "NII6548_na": ("NII6548", "narrow"),
    }
    rows = []
    for name, (line, comp) in cmap.items():
        a = get(name)
        if a is not None:
            rows.append(_rec(tag, "fantasy_agn", line, comp,
                             flux=_integrate(wave, np.asarray(a, float), line, comp)))
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
            # GELATO now receives 1e-17 flux, so its fluxes are already in 1e-17
            # units.  With NBoot>1 every row is a bootstrap sample: use the
            # median (matching GELATO's own saved SUMMARY model).
            vals = np.asarray(p[col], float)
            flux = _f(np.nanmedian(vals))
            # With NBoot>1 every row is a bootstrap sample -> flux uncertainty.
            flux_err = _f(np.nanstd(vals, ddof=1)) if vals.size > 1 else np.nan
            fwhm = _f(np.nanmedian(np.asarray(p[disp], float))) if disp in p.columns.names else np.nan
            rows.append(_rec(tag, "gelato", line, comp, flux=flux, flux_err=flux_err, fwhm=fwhm))
    rchi = _f(np.nanmedian(np.asarray(p["rChi2"], float))) if "rChi2" in p.columns.names else np.nan
    score = {"tag": tag, "tool": "gelato", "chi2_red": rchi,
             "chi2_kind": "global_reduced (reported)"}
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
                # A line named '*_broad' in the GLEAM line table is the broad
                # counterpart added by prepare_inputs/Gleam line_table.fits.
                raw_name = str(r[names["line"]]) if "line" in names else ""
                component = "broad" if raw_name.endswith("_broad") else "narrow"
                rows.append(_rec(tag, "gleam", line, component,
                                 flux=_f(r[names["flux"]]) if "flux" in names else np.nan,
                                 flux_err=_f(r[names["flux_err"]]) if "flux_err" in names else np.nan,
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
        z = 0.0
        man = obj / "manifest.json"
        if man.exists():
            try:
                z = float(json.loads(man.read_text()).get("z", 0.0))
            except Exception:
                z = 0.0
        for tool in TOOLS:
            out = outroot / tool
            if not out.is_dir():
                continue
            # Skip tools that were never run (prepare_inputs creates empty
            # output dirs for every tool, which would otherwise score as n/a).
            if not any(f.is_file() for f in out.rglob("*")):
                continue
            try:
                sc, lrows = PARSERS[tool](out, obj.name)
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] {tool} {obj.name}: {exc}")
                continue
            if sc:
                sc["chi2_common"] = common_chi2(obj, tool, out, z)
                sc["line_penalty"] = line_penalty(lrows)
                comps = {r["component"] for r in lrows}
                sc["has_broad"] = int("broad" in comps)
                sc["has_narrow"] = int("narrow" in comps)
                scores.append(sc)
                lines.extend(lrows)

    with (args.results / "scores.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["tag", "tool", "chi2_red", "chi2_kind",
                                           "chi2_common", "line_penalty",
                                           "has_broad", "has_narrow"])
        w.writeheader(); w.writerows(scores)
    with (args.results / "lines.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["tag", "tool", "line", "component",
                                           "flux_1e17", "flux_err_1e17", "fwhm_kms",
                                           "ew_a", "center_a", "flux_unit"])
        w.writeheader(); w.writerows(lines)
    print(f"scored {len(scores)} tool run(s); extracted {len(lines)} line measurement(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
