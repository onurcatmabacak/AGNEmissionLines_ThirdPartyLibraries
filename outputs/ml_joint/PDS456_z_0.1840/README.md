# `ml_joint` — 3ML joint fit of PDS 456 across UV, optical, MIR and X-rays

Four instruments in one likelihood instead of a ratio of two hand-picked fluxes.

## Flux points

Measured from the committed spectra (HST STIS, X-SHOOTER VIS, JWST MIRI MRS) and
from the XMM EPIC PN count rate in 1.8-2.2 keV divided by exposure and ARF area.
All flux densities are `erg/cm2/s/keV`, which is the convention the XSPEC-side
tools use.

| instrument | energy (keV) | f_E (erg/cm2/s/keV) |
|---|---:|---:|
| JWST/MIRI MRS (17.5 µm) | 7.085e-05 | 1.30e-06 |
| X-SHOOTER VIS (6000 A) | 2.066e-03 | 1.40e-08 |
| HST/STIS (1500 A) | 8.266e-03 | 1.50e-09 |
| XMM EPIC PN (2 keV) | 2.0 | 9.27e-13 |

## Joint fit (3ML, UV + optical + MIR)

| parameter | value | error |
|---|---:|---:|
| K | 1.4e-07 | 3e-09 |
| index alpha | **1.41** | 0.01 |

Residuals: -0.05, +0.07, -0.02 dex — a single power law describes the
UV/optical/MIR continuum to ~15 %, i.e. `f_E ∝ E^-1.41`.

## alpha_ox

`f(2500 A) = 3.46e-09` from the fitted model, `f(2 keV) = 9.27e-13` measured:

**alpha_ox = -1.37** (2 keV vs 2500 A)

That is a normal radio-quiet AGN value (-1.4 to -1.6), obtained from a joint
likelihood rather than from two hand-picked points.

## Correction: an earlier version of this product was wrong

The first run divided flux densities by the photon energy instead of using
`f_E = f_nu * dnu/dE = f_nu * keV/h`, and the MIR branch additionally converted
Jy -> F_lambda -> F_nu (a double conversion). Both errors are now fixed in
`Tools/ml_joint/run_ml_joint.py`.

The effect was not cosmetic: the UV/optical/MIR points came out ~1e12 too low and
distorted relative to one another, which made the fit look like a failure of the
power-law model ("BAL absorption", "UV 40x below the optical") and gave
alpha_ox = 3.04. With the conversion right, the same measurements fit one power
law and alpha_ox is -1.37. The lesson is recorded in the caveat matrix: a
plausible-looking number is not evidence, and unit conventions across bands are
where multi-instrument fits go wrong.

## What is still a caveat

* alpha_ox is defined at 2500 A and 2 keV; here it is measured with the 2500 A
  flux taken from the *fitted* model (the STIS coverage starts blueward of it), so
  it inherits the power-law assumption.
* The X-ray point is the raw 1.8-2.2 keV count rate / area; it is not corrected
  for intrinsic absorption, so alpha_ox is a lower bound on the intrinsic ratio if
  N_H is significant.
* PDS 456 was in a bright state; no variability correction is applied to the
  non-simultaneous UV/optical/MIR data.
