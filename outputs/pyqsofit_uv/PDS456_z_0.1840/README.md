# PyQSOFit UV fit — PDS 456

Input: `inputs/PDS456_z_0.1840/raw/hst_8264_stis_pds456_sg140l-sg230l_o58s_cspec.fits`,
the real HST/STIS G140L+G230L HASP spectrum (1139–3137 Å, 1921 s, CC BY 4.0).
The host-free PyQSOFit model uses the calibrated HST errors and z=0.184.

The spectrum covers rest-frame Lyα/N V, C IV 1549 and C III] 1909.  At z=0.184,
Hβ is at 5758 Å and Mg II at 3315 Å, both outside the STIS range.  The broad
C IV fit is therefore the only line available for the XMM comparison:

| line | flux (1e-17) | FWHM | S/N |
|---|---:|---:|---:|
| C IV 1549 broad | 94122.9 | 34807 km/s | **1.77** |
| Lyα broad | 39243.5 | 15127 km/s | 1.03 |

**Quality: tentative.**  The C IV S/N is below 3, the broad profile is
blended/absorption-affected, and the width is not a reliable velocity
measurement.  Local fit χ² values in `result.pdf`: Lyα 1.44, Si IV 1.26,
C IV 1.56.  Do not treat this as a detection-grade broad-line measurement and
do not fit an X-ray/optical correlation with it.
