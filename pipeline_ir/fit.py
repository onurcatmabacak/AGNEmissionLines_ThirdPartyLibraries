"""Local continuum + Gaussian line fitting with analytic doublet ties.

This is the first working IR line tool (``local_gaussian``).  It is deliberately
tool-agnostic: the router hands it a group of lines and a spectrum, and it
returns flux/FWHM/EW with covariance-based uncertainties.  Later suites add
BADASS/PAHFIT/CLASS wrappers behind the same interface.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy.optimize import least_squares

from .lines import Line, BY_NAME, TIES
from .spectrum import Spectrum, C_KMS


@dataclass
class Component:
    name: str
    line: Line
    center: float          # observed micron
    sigma0: float          # observed micron
    sigma_lo: float
    sigma_hi: float
    amp_tie: tuple[int, float] | None = None
    center_tie: int | None = None
    sigma_tie: int | None = None
    amp0: float = 1.0
    broad: bool = False


@dataclass
class Measurement:
    line: str
    component: str
    flux: float
    flux_err: float
    flux_limit: float
    fwhm_kms: float
    fwhm_err: float
    center_um: float
    ew_a: float
    snr: float
    detected: bool
    status: str
    chi2_red: float
    n_pix: int


def _sigma_from_kms(center_um: float, kms: float) -> float:
    return center_um * kms / C_KMS


def _build_components(group: list, z: float, res_um: float) -> list[Component]:
    comps: list[Component] = []
    for cov in group:
        ln = cov.line
        c = ln.rest_um * (1 + z)
        sig_res = max(res_um, _sigma_from_kms(c, 120.0))
        # narrow component
        comps.append(Component(ln.name, ln, c, max(sig_res, _sigma_from_kms(c, 250.0)),
                               max(0.5 * sig_res, _sigma_from_kms(c, 80.0)),
                               _sigma_from_kms(c, 1500.0)))
    # broad components for H-alpha / H-beta / Pa-alpha / Pa-beta / Br-gamma
    # first slice: broad/narrow decomposition for H-alpha/H-beta only
    broad_names = {"Halpha6563", "Hbeta4861", "MgII2798", "CIV1549", "CIII1908", "Lyalpha1216", "NV1240", "SiIV1397", "OVI1034"}
    for i, comp in enumerate(list(comps)):
        if comp.name in broad_names:
            c = comp.center
            comps.append(Component(comp.name + "_broad", comp.line, c,
                                   _sigma_from_kms(c, 3000.0),
                                   _sigma_from_kms(c, 700.0),
                                   _sigma_from_kms(c, 12000.0),
                                   center_tie=i, broad=True))
    # doublet amplitude ties
    for g, ties in TIES.items():
        idx = {c.name: i for i, c in enumerate(comps)}
        for child, (parent, ratio) in ties.items():
            if child in idx and parent in idx and comps[idx[child]].amp_tie is None:
                comps[idx[child]].amp_tie = (idx[parent], ratio)
    # tie narrow-line kinematics within a blend group (same narrow-line system)
    for i, c in enumerate(comps):
        if c.broad:
            continue
        for j, d in enumerate(comps[:i]):
            if (not d.broad) and d.line.blend_group and c.line.blend_group == d.line.blend_group:
                if c.center_tie is None:
                    c.center_tie = j
                if c.sigma_tie is None:
                    c.sigma_tie = j
                break
    return comps


def _window(spec: Spectrum, comps: list[Component]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    halves = []
    for c in comps:
        halves.append(max(5.0 * c.sigma0, _sigma_from_kms(c.center, 900.0)))
    lo = min(c.center - h for c, h in zip(comps, halves))
    hi = max(c.center + h for c, h in zip(comps, halves))
    m = spec.mask & (spec.wave_um >= lo) & (spec.wave_um <= hi)
    return spec.wave_um[m], spec.flux[m], spec.error[m]


def fit_group(spec: Spectrum, group: list, z: float) -> tuple[list[Measurement], float]:
    res_um = spec.wave_um[spec.mask]
    if res_um.size > 3:
        res_um = float(np.nanmedian(np.diff(res_um)))
    else:
        res_um = 1e-4
    comps = _build_components(group, z, res_um)
    x, y, e = _window(spec, comps)
    good = np.isfinite(x) & np.isfinite(y) & np.isfinite(e) & (e > 0)
    x, y, e = x[good], y[good], e[good]
    if x.size < 8:
        return [_failed(c, "too_few_pixels") for c in comps], np.nan
    x0 = float(np.mean(x))
    cont0 = float(np.median(y))
    noise = float(np.median(e))
    span = max(float(np.ptp(x)), 1e-3)
    # free-parameter layout
    free_amp = [i for i, c in enumerate(comps) if c.amp_tie is None]
    free_ctr = [i for i, c in enumerate(comps) if c.center_tie is None]
    free_sig = [i for i, c in enumerate(comps) if c.sigma_tie is None]
    p0, lo, hi = [cont0, 0.0], [-10 * abs(cont0) - 10 * noise, -10 * abs(cont0) / span - 10 * noise / span], [10 * abs(cont0) + 10 * noise, 10 * abs(cont0) / span + 10 * noise / span]
    for i in free_amp:
        c = comps[i]
        peak = max(float(np.max(y - cont0)), noise)
        p0.append(max(0.2 * peak, 0.05 * peak))
        lo.append(0.0)
        hi.append(max(10 * peak, 10 * noise))
    for i in free_ctr:
        c = comps[i]
        p0.append(0.0)
        lo.append(_sigma_from_kms(c.center, -1200.0))
        hi.append(_sigma_from_kms(c.center, 1200.0))
    for i in free_sig:
        c = comps[i]
        p0.append(c.sigma0)
        lo.append(c.sigma_lo)
        hi.append(c.sigma_hi)
    p0 = np.asarray(p0, float)
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    p0 = np.clip(p0, lo + 1e-12, hi - 1e-12)

    def unpack(p):
        a, b = p[0], p[1]
        k = 2
        amp = np.zeros(len(comps)); ctr = np.zeros(len(comps))
        for i in free_amp:
            amp[i] = p[k]; k += 1
        for i in free_ctr:
            ctr[i] = p[k]; k += 1
        sig = np.zeros(len(comps))
        for i in free_sig:
            sig[i] = p[k]; k += 1
        # resolve ties
        for i, c in enumerate(comps):
            if c.amp_tie is not None:
                j, r = c.amp_tie
                amp[i] = amp[j] * r
            if c.center_tie is not None:
                ctr[i] = ctr[c.center_tie]
            if c.sigma_tie is not None:
                sig[i] = sig[c.sigma_tie]
        return a, b, amp, ctr, sig

    def model(p):
        a, b, amp, ctr, sig = unpack(p)
        m = a + b * (x - x0)
        for i, c in enumerate(comps):
            m = m + amp[i] * np.exp(-0.5 * ((x - c.center - ctr[i]) / sig[i]) ** 2)
        return m

    def resid(p):
        return (model(p) - y) / e

    try:
        out = least_squares(resid, p0, bounds=(lo, hi), loss="soft_l1",
                            f_scale=max(noise, 1e-6), max_nfev=4000)
    except Exception as exc:  # noqa: BLE001
        return [_failed(c, f"fit_error:{type(exc).__name__}") for c in comps], np.nan
    a, b, amp, ctr, sig = unpack(out.x)
    r = resid(out.x)
    dof = max(1, x.size - len(out.x))
    chi2 = float(np.sum(r * r))
    chi2red = chi2 / dof
    try:
        J = out.jac
        cov = np.linalg.pinv(J.T @ J) * max(chi2red, 1.0)
        perr = np.sqrt(np.clip(np.diag(cov), 0, np.inf))
    except Exception:  # noqa: BLE001
        perr = np.full(len(out.x), np.nan)
    # map parameter errors back to free amplitude/sigma positions
    err_amp = {}; err_sig = {}
    k = 2
    for i in free_amp:
        err_amp[i] = perr[k]; k += 1
    k += len(free_ctr)
    for i in free_sig:
        err_sig[i] = perr[k]; k += 1
    for i, c in enumerate(comps):
        if c.sigma_tie is not None:
            err_sig[i] = err_sig.get(c.sigma_tie, np.nan)
    rows = []
    for i, c in enumerate(comps):
        s = abs(sig[i])
        flux = amp[i] * s * math.sqrt(2 * math.pi) * 1e4  # per A -> per um
        if c.amp_tie is not None:
            j, ratio = c.amp_tie
            ea = err_amp.get(j, np.nan) * ratio
        else:
            ea = err_amp.get(i, np.nan)
        es = err_sig.get(i, np.nan)
        ferr = abs(flux) * math.sqrt((ea / amp[i]) ** 2 + (es / s) ** 2) if (amp[i] > 0 and s > 0 and np.isfinite(ea) and np.isfinite(es)) else np.nan
        # 3-sigma upper limit on the integrated flux
        lim = 3.0 * (ea if np.isfinite(ea) else noise) * s * math.sqrt(2 * math.pi) * 1e4
        fwhm = 2.354820045 * s / c.center * C_KMS
        fwhm_err = fwhm * (es / s) if (s > 0 and np.isfinite(es)) else np.nan
        snr = flux / ferr if (np.isfinite(ferr) and ferr > 0) else (flux / lim if lim > 0 else np.nan)
        detected = bool(np.isfinite(snr) and snr >= 3.0 and amp[i] > 0)
        cont = a + b * (c.center - x0)
        ew = (flux / cont) if (cont != 0 and np.isfinite(flux)) else np.nan  # A
        rows.append(Measurement(
            line=c.line.name, component="broad" if c.broad else "narrow",
            flux=float(flux) if detected else float("nan"),
            flux_err=float(ferr) if np.isfinite(ferr) else float("nan"),
            flux_limit=float(lim) if not detected else float("nan"),
            fwhm_kms=float(fwhm), fwhm_err=float(fwhm_err) if np.isfinite(fwhm_err) else float("nan"),
            center_um=float(c.center + ctr[i]), ew_a=float(ew),
            snr=float(snr) if np.isfinite(snr) else float("nan"),
            detected=detected, status="ok" if detected else "upper_limit",
            chi2_red=float(chi2red), n_pix=int(x.size)))
    return rows, chi2red


def _failed(c: Component, status: str) -> Measurement:
    return Measurement(c.line.name, "broad" if c.broad else "narrow",
                       float("nan"), float("nan"), float("nan"), float("nan"),
                       float("nan"), c.center, float("nan"), float("nan"),
                       False, status, float("nan"), 0)
