"""Coverage-based router: observed spectrum + redshift -> line groups + suites."""
from __future__ import annotations

from dataclasses import dataclass, field
import math

import numpy as np

from .lines import LINES, Line, BY_NAME, band_of
from .spectrum import Spectrum, C_KMS


@dataclass
class LineCoverage:
    line: Line
    obs_um: float
    suite: str
    covered: bool
    measurable: bool
    snr_est: float
    reason: str = ""


@dataclass
class Route:
    object_id: str
    z: float
    band: str
    status: str
    suites: list[str] = field(default_factory=list)
    lines: list[LineCoverage] = field(default_factory=list)
    groups: dict[str, list[LineCoverage]] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    resolution: float = math.nan
    wave_min: float = math.nan
    wave_max: float = math.nan


def _resolution(spec: Spectrum) -> float:
    w = spec.wave_um[spec.mask]
    if w.size < 3:
        return math.nan
    dw = np.diff(w)
    return float(np.nanmedian(w[:-1] / dw))


def _local_stats(spec: Spectrum, obs_um: float, half_kms: float = 700.0):
    c = obs_um
    half = max(half_kms / C_KMS * c, 3.0 * float(np.nanmedian(np.diff(spec.wave_um[spec.mask]))) if spec.mask.sum() > 3 else 0.005)
    m = spec.mask & (np.abs(spec.wave_um - c) <= half)
    if m.sum() < 4:
        return math.nan, math.nan, 0.0
    f = spec.flux[m]
    e = spec.error[m]
    cont = float(np.nanmedian(f))
    # local noise from the median error (robust to line emission)
    noise = float(np.nanmedian(e))
    snr = cont / noise if noise > 0 else math.nan
    return cont, noise, float(m.sum())


def route(spec: Spectrum) -> Route:
    if not np.isfinite(spec.z) or spec.z <= 0:
        return Route(spec.object_id, spec.z, spec.band, "z_missing",
                     reasons=["redshift missing or non-positive; cannot map rest-frame lines"],
                     wave_min=spec.wave_min, wave_max=spec.wave_max)
    res = _resolution(spec)
    out: list[LineCoverage] = []
    reasons: list[str] = []
    for ln in LINES:
        obs = ln.rest_um * (1.0 + spec.z)
        within = spec.wave_min <= obs <= spec.wave_max
        if not within:
            continue
        cont, noise, goodfrac = _local_stats(spec, obs)
        covered = np.isfinite(cont) and goodfrac >= 5  # goodfrac is the pixel count
        snr = cont / noise if (noise and np.isfinite(noise) and noise > 0) else math.nan
        measurable = covered and np.isfinite(snr) and snr > 3.0
        reason = "" if covered else "window has fewer than 5 good pixels"
        if covered and not measurable:
            reason = f"local continuum S/N {snr:.1f} < 3"
        out.append(LineCoverage(ln, obs, ln.suite or band_of(obs), covered, measurable, snr, reason))
    if not out:
        return Route(spec.object_id, spec.z, spec.band, "no_coverage",
                     reasons=[f"no registry line falls in {spec.wave_min:.2f}-{spec.wave_max:.2f} um at z={spec.z:.4f}"],
                     resolution=res, wave_min=spec.wave_min, wave_max=spec.wave_max)
    covered = [c for c in out if c.covered]
    if not covered:
        reasons.append("registry lines are geometrically covered but no usable window")
        return Route(spec.object_id, spec.z, spec.band, "no_usable_line",
                     lines=out, reasons=reasons, resolution=res,
                     wave_min=spec.wave_min, wave_max=spec.wave_max)
    suites = sorted({c.suite for c in covered})
    # group by (suite, blend_group) for simultaneous fitting
    groups: dict[str, list[LineCoverage]] = {}
    for c in covered:
        if not c.measurable:
            continue
        g = c.line.blend_group or c.line.name
        key = f"{c.suite}:{g}"
        groups.setdefault(key, []).append(c)
    # Split groups whose members are far apart in wavelength: a shared
    # diagnostic label (e.g. [Fe II] 1.26/1.64 um) is not a blend.
    split: dict[str, list[LineCoverage]] = {}
    for key, members in groups.items():
        obs = sorted(m.obs_um for m in members)
        if obs and obs[-1] / obs[0] > 1.05:
            for m in members:
                split[f"{m.suite}:{m.line.name}"] = [m]
        else:
            split[key] = members
    groups = split
    if not groups:
        reasons.append("no measurable line (all covered windows below S/N 3)")
    return Route(spec.object_id, spec.z, spec.band, "ok" if groups else "no_measurable_line",
                 suites=suites, lines=out, groups=groups, reasons=reasons,
                 resolution=res, wave_min=spec.wave_min, wave_max=spec.wave_max)
