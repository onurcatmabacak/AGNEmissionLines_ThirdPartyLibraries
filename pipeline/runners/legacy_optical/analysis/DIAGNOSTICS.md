# DIAGNOSTICS — spectrum.fits and the six third-party fits

Author: analysis session, 2026-08-29.
Object: `IeRASS J053448.4+212608`, z ≈ 0.348 (per README).
Data: `spectrum.fits` = flux (HDU0) + wavelength (HDU1), 3709 px,
λ = 4000.06–9999.89 Å (uniform 1.617 Å spacing), flux in erg s⁻¹ cm⁻² Å⁻¹,
header: Z=0.0 (wrong), EBV=0.45, FWHM=1140 (units unclear).

---------------------------------------------------------------------------
## 1. TL;DR

The spectrum **cannot be described by a single redshift** with the standard
AGN line identifications.  Strong, unambiguous features sit at

| observed Å | rest (z=0.348) | if it is … | implied z |
|---|---|---|---|
| 5100.8 | 3784.0 | [OII] λ3727.1 | **0.3686** |
| 6520.3 | 4837.0 | Hβ 4861.4 | 0.3412 |
| 6647.5 | 4931.4 | [OIII] λ4958.9 | **0.3406** |
| 6752.1 | 5009.0 | [OIII] λ5006.8 | 0.3486 |
| 8837.6 | 6556.1 | Hα 6562.8 | 0.3466 |

The decisive contradiction: **the [OIII] doublet λ4959/λ5007 must have a fixed
separation** Δλ = 47.9 Å × (1+z) ≈ 64.5 Å.  Observed line separation =
6752.1 − 6647.5 = **104.6 Å**, i.e. 62% too large.  There is no z for which
the pair at 6647.5/6752.1 is the [OIII] doublet (that would require z ≈ 1.18).
Equally, [OII] λ3727 at z=0.348 would appear at 5024.2 Å — the data shows
**no line there at all**; the strongest blue line is at 5100.8 Å.

Because of this, every tool gets confused, and each ends up with a
different, mutually inconsistent "best" fit (see RESULTS.md).

---------------------------------------------------------------------------
## 2. What the spectrum actually shows (data-driven, no z assumption)

Independent of identification, the features are (observed, FWHM ⊇ instrument):

| feature | centre (Å) | FWHM.obs (Å) | approx. FWHM (km/s) | shape |
|---|---|---|---|---|
| strong narrow blue line | 5100.8 | 27 | ~380 (core) + broad base | symmetric |
| moderate (near rest 4837) | 6520.3 | 46 | ~2100 | broad, blends into FeII region |
| narrow line | 6647.5 | 31 | ~1260 | symmetric |
| narrow line (asymmetric, red shoulder 6820–6850) | 6752.1 | 43 | ~1550–1980 | asymmetric |
| strong Hα-like | 8837.6 | 23 core / ~150 base | ~650 core, wings ±2000 | broad wings, absorption-like dip at 8760–8780 |
| [NeIII]-like bump | 5227.6 | 34 | — | weak |
| [SII]-like blend | ~9048–9067 | — | — | weak doublet-ish |

Continuum (rest 2967–7400): roughly flat, 2.3–2.6 ×10⁻¹⁷, with (a) broad
FeII-like structure rest 4690–5400 (e.g. features at obs 6393, 6940, 7016,
7072, 7209 → rest 4742, 5148, 5205, 5246, 5349 — matches the Vestergaard &
Wilkes optical FeII template to ±1 Å), (b) small peaks near rest 5804/5933/
5995/6090/6185/6276 (obs 7825/8000/8082/8208/8338/8462) of unclear origin,
(c) local "dips" between the emission complexes (obs 6600–6625, 6780–6860).

Numerical sanity checks:
- Noise: pixel-to-pixel scatter ≈ 4.3–7.3% of flux; adjacent-pixel
  autocorrelation ρ ≈ 0.83 → spectrum is heavily smoothed (kernel ~3 px ≈
  5 Å FWHM ≈ 300–450 km/s at 5000–6700 Å).  The `ivar` in the converted FITS
  files (10%) and the header FWHM=1140 km/s are not consistent with the data.
- The fits under `/Gelato/` and `/Gleam/` store the flux in 1e-17 units but
  errors of ~1.0 (GLEAM `stdev=1.0`!) or ignore the error entirely, which is
  why their line fits are meaningless (GLEAM χ² residuals invisible; GELATO
  rChi2 = 1.3e-5 with fluxes in 1e-14).

---------------------------------------------------------------------------
## 3. What this means

Options, in order of desirability:

1. **Get the original (un-converted) spectrum** (ideally the raw 2D/1D fits
   from the telescope/SDSS archive, or whatever the EmissionLineAnalysis
   repo used as input) and regenerate X. We cannot reconstruct a correct
   wavelength scale from the converted file.
2. If only `spec.txt`/`spectrum.fits` exists, the wavelength array must be
   repaired before any of the six tools can be trusted.  The observed
   features at 6752.1 and 8837.6 Å are internally consistent (Hα/[OIII]5007
   ratio within 0.15% → same z ≈ 0.347–0.349), but Hβ/[OIII]4959/[OII] are
   not; a re-binning/stitching bug is suspected in the blue part
   (4000–5200 Å, offsets up to +77 Å).
3. Data-driven fits (treating each strong feature independently of its
   physical label, with free centroids) are the only ones that "work" on
   the file as-is.  The tuned configs in this repo have been updated on
   that basis.
