# `ml_joint` — 3ML joint fit of PDS 456 across UV, optical and MIR

Four instruments enter one likelihood instead of being compared as a ratio of
two hand-picked fluxes.

## Flux points (written by the tool from the committed spectra)

| instrument | energy (keV) | flux density (keV/cm2/s/keV) | error |
|---|---:|---:|---:|
| HST/STIS UV | 0.008266 | 7.492e-22 | 4.64e-24 |
| X-SHOOTER optical | 0.002066 | 2.805e-20 | 4.67e-24 |
| JWST/MIRI MIR | 7.085e-05 | 7.606e-21 | 1.88e-24 |
| XMM EPIC PN X-ray | 2 | 9.274e-13 | 5.57e-15 |

The X-ray point is the EPIC PN count rate in 1.8-2.2 keV divided by the exposure
and the ARF effective area at 2 keV (27 720 counts, so the Poisson error is
negligible; the systematic error is not, see below).

## Joint maximum-likelihood fit (3ML, UV + optical + MIR)

| parameter | value | error |
|---|---:|---:|
| K | 1.614e-20 | 1.01e-23 |
| index | 0.06564 | 7.43e-05 |

alpha_ox = **3.04** +/- 0.00 (2 keV vs 2500 A),
and the fitted UV/optical/MIR slope is alpha = 0.066
(Gamma = 0.93).

## What this actually says - including the failure

**A single power law does not describe this SED.** The three fitted points are
7.5e-22 (UV), 2.8e-20 (optical) and 7.6e-21 (MIR): the UV point sits a factor
~40 *below* the optical, which is what a broad absorption line quasar looks like
(PDS 456 is the archetype), not a power law. The fit therefore returns a nearly
flat index (alpha = 0.07) that is a compromise between
incompatible points, and the alpha_ox derived from it is not a physical
measurement.

What is defensible from this run:

* the flux points themselves, each measured from its own spectrum;
* the demonstration that the joint likelihood machinery works across four
  instruments with a shared model and propagated errors;
* the negative result that an unabsorbed single power law fails by a large
  factor in the UV - which is the physical reason alpha_ox should be measured
  blueward of the absorption, or with an absorbed model.

A four-parameter broken power law was tried first and is *worse*: four flux
points, four parameters, zero degrees of freedom - it put the break at 2e-8 keV,
far outside the data. That is recorded here because the temptation to quote the
broken-power-law numbers as a "break detection" would be exactly the kind of
unsupported claim this repository is built to avoid.
