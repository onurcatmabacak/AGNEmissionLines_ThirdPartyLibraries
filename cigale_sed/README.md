# `cigale_sed` — CIGALE SED/torus fits (Docker)

Dockerised CIGALE 2025.1 with a minimal BC03 + DL2014 + SKIRTOR/Fritz database.
The fit is now **per source** and runs **two AGN torus families**.

## Build / run

```bash
bash pipeline/build_images.sh cigale_sed
.venv/bin/python pipeline/run_new_tools.py --only 04592649654_z_0.5874 \
  --tools cigale_sed --cigale-models skirtor2016,fritz2006 --force
```

Input: `inputs/<source>/photometry/photometry.txt` (one row, CIGALE names).
Output:

```text
outputs/<source>/cigale_sed/
  model_family.csv
  model_family_spread.json
  skirtor2016/...
  fritz2006/...
```

## Caveat fixes

* **Dust attenuation is mandatory.**  `dustatt_modified_starburst` computes
  `dust.luminosity`; without it DL2014/SKIRTOR default to 1 W and the MIR is
  negligible.
* **Two torus families** (`skirtor2016`, `fritz2006`) instead of one; the
  spread is recorded.
* **Per-band χ² diagnostics** (`chi2_optical`, `chi2_wise`, `wise_outlier`)
  flag WISE-contaminated objects rather than hiding them.
* **Per-source catalogues** and outputs follow the canonical layout.

## Results (five eFEDS QSOs)

| source | z | SKIRTOR χ²_ν | Fritz χ²_ν | SKIRTOR frac_AGN | Fritz frac_AGN | note |
|---|---:|---:|---:|---:|---:|---|
| 04545014975 | 1.129 | 2.65 | 1.80 | 0.10 | 0.50 | both acceptable |
| 04570952937 | 0.990 | 3.96 | 0.92 | 0.10 | 0.50 | Fritz preferred |
| 04592566733 | 1.830 | 0.25 | 4.00 | 0.90 | 0.90 | SKIRTOR preferred |
| 04592649654 | 0.587 | 10.90 | 3.69 | 0.10 | 0.50 | SKIRTOR WISE-flagged |
| 04592933676 | 0.651 | 19.22 | 0.72 | 0.10 | 0.90 | SKIRTOR WISE-flagged; Fritz solves it |

The model-family spread is recorded in `model_family_spread.json`; no single
family is presented as the unique answer.  The previously flagged outlier is
well fitted by Fritz (χ²_ν 0.72), so it is a family-dependent result rather
than a data failure.

## Remaining limitations

* **AGNfitter-rx is now the independent second SED engine** (see
  `agnfitter_sed/`); PROSPECTOR-AGN is not integrated.  CIGALE still has no
  X-ray/radio constraints, so torus parameters remain prior-dominated for
  low-AGN-fraction objects.
* CIGALE is cloned at build time; the image is large (~10.4 GB).
