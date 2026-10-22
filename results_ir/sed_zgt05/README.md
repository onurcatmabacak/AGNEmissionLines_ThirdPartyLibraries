# CIGALE SED/torus pilot — five z > 0.5 eFEDS QSOs

`bash run_cigale_sed_docker.sh input_sed results_ir/sed_zgt05`

Files:

* `sed_fit.png` / `sed_fit.pdf` — observed SDSS + WISE photometry (blue) and
  the CIGALE best-fit band fluxes (orange), one panel per object.
* `sed_summary.csv` — redshift, χ², reduced χ², AGN fraction, torus optical
  depth, polar-dust E(B−V), AGN/torus/dust luminosities, M⋆ and SFR.
* `pcigale.ini`, `pcigale.ini.spec` — exact configuration and parameter spec.
* `out/results.fits` — full CIGALE results table (best and Bayes values).
* `out/observations.fits` — photometry as ingested by CIGALE.
* `out/<id>_best_model.fits` — best-fit model spectrum for each object.

Summary (best fit):

| id | z | χ²_ν | frac_AGN |
|---|---|---|---|
| 4545014975 | 1.129 | 1.56 | 0.10 |
| 4570952937 | 0.990 | 2.55 | 0.10 |
| 4592566733 | 1.830 | 0.19 | 0.90 |
| 4592649654 | 0.587 | 6.45 | 0.10 |
| 4592933676 | 0.651 | 9.95 | 0.10 |

Two objects are excellent, two are acceptable, and 4592933676 is a flagged
optical outlier.  The pilot uses nominal photometric errors, one SED family
and no X-ray/radio constraints; see `cigale_sed/README.md` for the full
caveat list.
