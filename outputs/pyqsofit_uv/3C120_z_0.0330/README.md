# PyQSOFit UV/optical fit — 3C 120

Input: `inputs/3C120_z_0.0330/raw/hst_8700_stis_3c120d0_g430l-g750l_o62o_cspec.fits`,
the real HST/STIS G430L+G750L HASP spectrum (2993–10247 Å, 1440 s, CC BY 4.0).
The host-free PyQSOFit model uses the calibrated HST errors and the source
redshift z=0.033.

Key line results (`pyqsofit_lines.csv`, units 1e-17 erg cm^-2 s^-1):

| line | components | flux | FWHM |
|---|---|---:|---:|
| Hβ | broad + narrow | **28435.8** | 2675.9 km/s (broad) |
| [O III] 5007 | core + wing | **18362.7** | 846.9 km/s (core) |
| Hβ/[O III] 5007 | total/total | **1.55** | — |

Local fit χ² values in `result.pdf`: Hβ 2.43, Hα 2.86.  The global
continuum+Fe II model is not a perfect description of the full 2993–10247 Å
range, so use the line totals, not individual components.  Hα is fitted but
is not used in the crossmission comparison.

See `../crossmission/xray_optical_comparison.md` for the RXTE Fe Kα comparison.
