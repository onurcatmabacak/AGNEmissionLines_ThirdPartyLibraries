# `cigale_sed` — CIGALE SED/torus pilot (P5a)

Dockerised **CIGALE 2025.1** fit of stellar + dust + AGN-torus emission to the
five z > 0.5 eFEDS QSOs.  This is the first P5a SED/torus tool; AGNfitter-RX
and PROSPECTOR-AGN are not yet implemented.

The image is intentionally built from a **minimal CIGALE database**:
`filters`, `bc03`, `dl2014`, `nebular`, `skirtor2016`.  It is large (~10.1 GB)
because the BC03, DL2014 and SKIRTOR template grids are included.

## Build

```bash
bash pipeline/build_images.sh cigale_sed
```

The build clones CIGALE, installs Git-LFS and pulls the LFS data (the nebular
continuum is stored in LFS), then runs `database_builder` for the modules above.
The CIGALE revision is whatever `master` is at build time (2025.1 in this
image); no DB download is available from CIGALE, so the DB is built locally.

## Run

```bash
bash run_cigale_sed_docker.sh input_sed results_ir/sed_zgt05
```

`input_sed/photometry.txt` is the catalog; the container writes `pcigale.ini`,
`pcigale.ini.spec`, `out/`, `sed_fit.png`, `sed_fit.pdf` and
`sed_summary.csv` into the output directory.

## Model setup

* SFH: `sfhdelayed` (delayed exponential; optional burst).
* Stellar: `bc03` (Salpeter IMF; two metallicities).
* Attenuation: `dustatt_modified_starburst`.  **This module is essential**: it
  computes `dust.luminosity` from the absorbed stellar light.  Without it
  `dl2014`/`skirtor2016` default to a 1 W dust luminosity and the AGN/dust
  emission is negligible against the stellar SED.
* Dust emission: `dl2014`.
* AGN: `skirtor2016` (torus, polar dust, AGN disk; type-1 inclination 30°).
* `redshifting` (IGM included).
* Analysis: CIGALE `pdf_analysis`, 4 cores, best SED saved.

The grid is 1,049,760 models.  It covers delayed-SFH age/e-folding/burst
fraction, BC03 metallicity, attenuation, DL2014 PAH/radiation field, and
SKIRTOR torus optical depth, AGN fraction 0.1–0.99, polar-dust E(B−V) and
inclination.  Runtime is ~2 minutes on 4 cores.

## Results (`results_ir/sed_zgt05`)

| id | z | χ²_ν | frac_AGN | note |
|---|---|---|---|---|
| 4545014975 | 1.129 | 1.56 | 0.10 | good optical + WISE |
| 4570952937 | 0.990 | 2.55 | 0.10 | acceptable; W1/W2 slightly low |
| 4592566733 | 1.830 | 0.19 | 0.90 | excellent; AGN-dominated |
| 4592649654 | 0.587 | 6.45 | 0.10 | W4 low by ~40 % |
| 4592933676 | 0.651 | 9.95 | 0.10 | optical g/r too low, z too high |

`sed_fit.png`/`.pdf` show the observed SDSS+WISE photometry and the CIGALE best
band fluxes; `sed_summary.csv` records χ², AGN fraction, torus/AGN/dust
luminosities, M⋆ and SFR.

## Caveats

* **One model family only.**  No AGNfitter-RX, PROSPECTOR-AGN or X-ray/radio
  constraints; the torus parameters are prior-dominated for the objects with
  frac_AGN = 0.1.
* **Photometric errors are nominal** (0.05 mag SDSS, 0.125 mag WISE); no
  catalogue errors exist in `SPALL`.  CIGALE adds a 10 % floor.
* The five objects are not a statistical sample; this is a pipeline pilot.
* Object 4592933676 is an optical outlier: the model does not reproduce the
  blue SDSS shape while keeping the WISE points.  It is retained and flagged
  rather than tuned away.
* The `u` band is absent; no X-ray, radio or optical spectra enter the fit.
* CIGALE's `best` values are reported; the full posterior is in
  `out/results.fits` (`bayes.*` columns).
