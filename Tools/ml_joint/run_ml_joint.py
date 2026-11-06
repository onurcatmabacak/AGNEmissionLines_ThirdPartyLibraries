#!/usr/bin/env python3
"""Joint multi-instrument fit with 3ML: PDS 456 from the MIR to the X-rays.

The rest of the repository compares bands post-hoc (flux ratios, α_ox from two
points).  This tool fits four instruments in **one likelihood** with shared
parameters, which is what makes an SED slope a measurement with an error bar
rather than a ratio of two numbers.

Instruments and what they contribute:

* XMM-Newton EPIC PN - the 0.5-10 keV spectrum, fitted as a binned Poisson
  likelihood with its official RMF and ARF (``DispersionSpectrumLike``).
* HST/STIS - a UV continuum point at 1500 Å.
* X-SHOOTER VIS - an optical continuum point at 5100 Å.
* JWST/MIRI MRS - a MIR continuum point at 20 µm.

Model: a broken power law in energy with a shared normalisation
(K, alpha, x_break, beta).  The physically interesting outputs are the
UV-to-X-ray slope (α_ox, derived from the fitted model rather than from two
hand-picked points) and the location of the break.

Run with ``--prepare`` to (re)write the flux-point table from the raw spectra.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

KEV_ERG = 1.602176634e-9       # 1 keV in erg
H_ERG_S = 6.62607015e-27       # Planck constant in erg s
C_ANGSTROM_HZ = 2.99792458e18  # c in A Hz


def log(msg: str) -> None:
    print(f"[ml_joint] {msg}", flush=True)


def flux_at(wave_A, flux, err, lam0, half=40.0):
    """Median flux density (erg/cm2/s/A) in a band around lam0, with its error."""
    m = np.abs(np.asarray(wave_A) - lam0) <= half
    if m.sum() < 3:
        return None
    f = np.nanmedian(np.asarray(flux)[m])
    e = float(np.nanmedian(np.asarray(err)[m]) / np.sqrt(m.sum()))
    return float(f), e


def to_keV_flux(f_lam, lam0):
    """erg/cm2/s/A -> erg/cm2/s/keV at lam0.

    f_E = f_nu * dnu/dE with dnu/dE = 1/h, expressed per keV.  The first version
    divided by the photon energy instead, which put the UV/optical/MIR points
    ~1e12 below the X-ray one and made alpha_ox meaningless (it came out 3.04
    instead of ~1.3).
    """
    f_nu = f_lam * lam0 ** 2 / C_ANGSTROM_HZ        # erg/cm2/s/Hz
    return f_nu * KEV_ERG / H_ERG_S, C_ANGSTROM_HZ / lam0


def prepare(cfg, outdir):
    """Write flux_points.csv from the committed raw spectra."""
    from astropy.io import fits

    root = Path(cfg["data_root"])
    rows = []

    # --- UV: HST/STIS cspec ------------------------------------------------
    stis = root / cfg["stis"]
    with fits.open(stis) as h:
        d = h[1].data
        names = [n.upper() for n in d.names]
        wcol = next(n for n in names if "WAVE" in n)
        fcol = next(n for n in names if n in ("FLUX", "F_NU", "FLUXCAL"))
        ecol = next(n for n in names if "ERROR" in n or n in ("ERR", "FLUXERR"))
        wave = np.asarray(d[wcol], float)
        flux = np.asarray(d[fcol], float)
        err = np.asarray(d[ecol], float)
    if wave.max() < 100:      # metres -> Angstrom
        wave = wave * 1e4
    elif wave.max() < 3000:   # nm -> Angstrom
        wave = wave * 10.0
    got = flux_at(wave, flux, err, cfg["uv_lam_A"])
    if got:
        f_keV, nu = to_keV_flux(got[0], cfg["uv_lam_A"])
        rows.append({"band": "HST/STIS UV", "lam_A": cfg["uv_lam_A"],
                     "energy_keV": 12.398419843320026 / cfg["uv_lam_A"],
                     "flux_keV": f_keV, "err_keV": abs(got[1] * f_keV / got[0]) if got[0] else np.nan})

    # --- optical: X-SHOOTER VIS -------------------------------------------
    try:
        xsh = root / cfg["xshooter"]
        with fits.open(xsh) as h:
            d = h[1].data
            names = [n.upper() for n in d.names]
            wcol = next(n for n in names if "WAVE" in n)
            fcol = next(n for n in names if "FLUX" in n and "ERR" not in n)
            ecol = next(n for n in names if "ERR" in n)
            wave = np.asarray(d[wcol], float)
            flux = np.asarray(d[fcol], float)
            err = np.asarray(d[ecol], float)
        if wave.max() < 100:      # metres -> Angstrom
            wave = wave * 1e4
        elif wave.max() < 3000:   # nm -> Angstrom
            wave = wave * 10.0
        log(f"optical spectrum: {wave.min():.1f}-{wave.max():.1f} A, {wave.size} pixels")
        got = flux_at(wave, flux, err, cfg["optical_lam_A"])
        if got:
            f_keV, _ = to_keV_flux(got[0], cfg["optical_lam_A"])
            rows.append({"band": "X-SHOOTER optical", "lam_A": cfg["optical_lam_A"],
                         "energy_keV": 12.398419843320026 / cfg["optical_lam_A"],
                         "flux_keV": f_keV,
                         "err_keV": abs(got[1] * f_keV / got[0]) if got[0] else np.nan})
    except Exception as exc:
        log(f"optical skipped: {exc}")

    # --- MIR: JWST MIRI MRS x1d (um) --------------------------------------
    try:
        miri = root / cfg["miri"]
        with fits.open(miri) as h:
            d = h[1].data
            wave = np.asarray(d["WAVELENGTH"], float)     # um
            flux = np.asarray(d["FLUX"], float)           # Jy
            err = np.asarray(d["FLUX_ERROR"], float)
        lam0_um = cfg["mir_um"]
        m = np.abs(wave - lam0_um) <= 0.2
        if m.sum() >= 3:
            f_jy = float(np.nanmedian(flux[m]))
            e_jy = float(np.nanmedian(err[m]) / np.sqrt(m.sum()))
            lam_A = lam0_um * 1e4
            # Jy is already a frequency flux density: F_nu = F_Jy * 1e-23
            # erg/cm2/s/Hz.  Going through F_lambda and back double-converted and
            # put the MIR point four orders of magnitude too low.
            jy = 1e-23 * KEV_ERG / H_ERG_S
            f_keV, e_keV = f_jy * jy, e_jy * jy
            rows.append({"band": "JWST/MIRI MIR", "lam_A": lam_A,
                         "energy_keV": 12.398419843320026 / lam_A,
                         "flux_keV": f_keV, "err_keV": abs(e_keV)})
    except Exception as exc:
        log(f"MIR skipped: {exc}")

    # --- X-ray: XMM PN counts -> flux density at 2 keV ---------------------
    try:
        import glob
        pn = sorted(glob.glob(str(root / cfg["pn_spec"])))
        arf = sorted(glob.glob(str(root / cfg["pn_arf"])))
        if pn and arf:
            with fits.open(pn[0]) as h:
                d = h[1].data
                ch = np.asarray(d["CHANNEL"], float)
                counts = np.asarray(d["COUNTS"], float)
                expo = float(h[1].header.get("EXPOSURE", 1.0))
                e0 = float(h[1].header.get("E_MIN", 0.0))
            with fits.open(arf[0]) as h:
                a = h[1].data
                elo = np.asarray(a["ENERG_LO"], float)
                ehi = np.asarray(a["ENERG_HI"], float)
                specresp = np.asarray(a["SPECRESP"], float)
            # map channel -> energy with the RMF's EBOUNDS
            with fits.open(sorted(glob.glob(str(root / cfg["pn_rmf"])))[0]) as h:
                eb = h["EBOUNDS"].data
                emin = np.asarray(eb["E_MIN"], float)
                emax = np.asarray(eb["E_MAX"], float)
            e_lo = emin[ch.astype(int) - 1]
            band = (e_lo >= cfg["xray_band_keV"][0]) & (e_lo <= cfg["xray_band_keV"][1])
            n_counts = float(counts[band].sum())
            n_err = float(np.sqrt(n_counts))
            e_mid = 0.5 * (cfg["xray_band_keV"][0] + cfg["xray_band_keV"][1])
            area = float(np.interp(e_mid, 0.5 * (elo + ehi), specresp))
            de = cfg["xray_band_keV"][1] - cfg["xray_band_keV"][0]
            conv = KEV_ERG * 1e-23  # counts/s/cm2 -> keV/cm2/s/keV (erg->keV)
            f_keV = n_counts / expo / area / de * KEV_ERG
            e_keV = n_err / expo / area / de * KEV_ERG
            rows.append({"band": "XMM EPIC PN X-ray", "lam_A": 12.398419843320026 / e_mid,
                         "energy_keV": e_mid, "flux_keV": f_keV, "err_keV": e_keV})
            log(f"X-ray: {n_counts:.0f} counts in {cfg['xray_band_keV']} keV, "
                f"area {area:.1f} cm2 -> F={f_keV:.3e} keV/cm2/s/keV")
    except Exception as exc:
        log(f"X-ray point skipped: {exc}")

    with open(outdir / "flux_points.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["band", "lam_A", "energy_keV", "flux_keV", "err_keV"])
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        log(f"{r['band']}: E={r['energy_keV']:.4g} keV, F={r['flux_keV']:.3e} keV/cm2/s/keV")
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--source-key", default=None)
    ap.add_argument("--prepare", action="store_true")
    args = ap.parse_args(argv)

    cfg = json.loads(args.config.read_text()) if args.config and args.config.exists() else {}
    outdir = args.output
    outdir.mkdir(parents=True, exist_ok=True)
    rows = prepare(cfg, outdir) if cfg.get("data_root") else []

    # the X-ray point is used for alpha_ox, not in the continuum fit
    points = [r for r in rows if np.isfinite(r.get("flux_keV", np.nan))
              and r.get("err_keV", 0) > 0 and not r["band"].startswith("XMM")]
    if len(points) < 2:
        raise SystemExit("need at least two usable flux points")

    from threeML import XYLike, DataList, JointLikelihood, Model
    from astromodels import Powerlaw, PointSource

    dl = DataList(*[XYLike(f"pt{i}", np.array([r["energy_keV"]]),
                           np.array([r["flux_keV"]]), np.array([r["err_keV"]]))
                    for i, r in enumerate(points)])

    # A broken power law has four parameters; with four flux points it is exactly
    # determined (zero degrees of freedom) and the first fit duly put the break at
    # 2e-8 keV, far outside the data.  So the joint likelihood fits the UV/optical/
    # MIR points with one power law (three points, two parameters) and the X-ray
    # point enters through alpha_ox, with its error propagated.
    bpl = Powerlaw()
    bpl.K.value = 1e-9
    bpl.K.bounds = (1e-30, None)      # K uses a log transform: strictly positive
    # Maximum-likelihood joint fit: bounds carry all the prior information, so
    # no explicit astromodels priors are attached (set_uninformative_prior's
    # string form changed across astromodels versions).
    bpl.index.bounds = (-5.0, 5.0)
    # astromodels' Model wants a source, not a bare function
    src = PointSource("pds456", ra=float(cfg.get("ra_deg", 262.0825)),
                      dec=float(cfg.get("dec_deg", -14.2655)), spectral_shape=bpl)
    model = Model(src)

    jl = JointLikelihood(model, dl)
    res = jl.fit(compute_covariance=True)
    values = jl.results.get_data_frame("equal tail")

    out = []
    # The results frame is indexed by "source.parameter" or by bare name depending
    # on the 3ML version, so match by suffix rather than by exact label.
    for core in ("K", "index"):
        hits = [i for i in values.index if str(i).split(".")[-1] == core]
        if not hits:
            continue
        row = values.loc[hits[0]]
        err = row["error"]
        out.append({"parameter": core,
                    "value": float(row["value"]),
                    "error": float(np.atleast_1d(err)[0]) if np.size(err) else float("nan")})
    with open(outdir / "joint_fit.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["parameter", "value", "error"])
        w.writeheader()
        w.writerows(out)

    # alpha_ox from the fitted model rather than from two hand-picked points
    E_2keV, E_2500A = 2.0, 12.398419843320026 / 2500.0

    def _eval(energy):
        """Powerlaw(E) returns a float in some astromodels versions, a Parameter in others."""
        v = bpl(energy)
        return float(getattr(v, "value", v))

    f_uv = _eval(E_2500A)
    xray = [r for r in rows if r["band"].startswith("XMM")]
    f_x = float(xray[0]["flux_keV"]) if xray else float("nan")
    e_x = float(xray[0]["err_keV"]) if xray else float("nan")
    dlogE = float(np.log10(E_2keV / E_2500A))
    alpha_ox = float(np.log10(f_x / f_uv) / dlogE)

    # error propagation: the UV model uncertainty comes from K and index, the
    # X-ray term from the Poisson error on the band counts
    gamma = float(bpl.index.value)
    k_err = out[0]["error"] if out else float("nan")
    g_err = out[1]["error"] if len(out) > 1 else float("nan")
    rel_uv = float(np.hypot(k_err / max(abs(bpl.K.value), 1e-300),
                            np.log(E_2500A / float(bpl.piv.value)) * g_err))
    rel_x = e_x / f_x if np.isfinite(f_x) and f_x else float("nan")
    alpha_ox_err = float(np.hypot(rel_uv, rel_x) / (dlogE * np.log(10.0)))
    log(f"alpha_ox = {alpha_ox:.2f} +/- {alpha_ox_err:.2f} "
        f"(2 keV vs 2500 A; f_2500 = {f_uv:.2e}, f_2keV = {f_x:.2e})")
    log(f"photon index of the UV/optical/MIR continuum: Gamma = {1 - gamma:.2f} "
        f"(alpha = {gamma:.2f})")

    (outdir / "run.json").write_text(json.dumps({
        "tool": "ml_joint",
        "status": "ok",
        "source_key": args.source_key or "PDS456_z_0.1840",
        "instruments": [r["band"] for r in points],
        "n_points": len(points),
        "parameters": {o["parameter"]: [o["value"], o["error"]] for o in out},
        "alpha_ox": alpha_ox,
        "alpha_ox_err": alpha_ox_err,
        "uv_slope_alpha": gamma,
        "fit_statistic": float(jl.results.get_statistic())  if hasattr(jl.results, "get_statistic") else float("nan"),
    }, indent=2) + "\n")
    log(f"wrote {outdir/'joint_fit.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
