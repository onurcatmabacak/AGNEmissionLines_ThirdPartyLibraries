# MaNGA DAP comparison — NGC1194_z_0.0136

- ours: `/app/ours/manga_dap_maps.fits.gz` (DAPTYPE `HYB10-MILESHC-MASTARHC2`, DAP 4.5.0, DRP v3_1_1)
- reference: `/app/ref/manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz` (DAPTYPE `HYB10-MILESHC-MASTARHC2`, DAP 3.1.0, DRP v3_1_1)

## Key-line statistics

| quantity | N | median ratio ours/ref | 16–84% | median fractional diff | robust scatter | Pearson r | median error ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| ha | 2678 | 1.0004 | 0.9953–1.0077 | +0.0004 | 0.0047 | 1.0000 | 1.000 |
| hb | 2285 | 1.0010 | 0.9904–1.0153 | +0.0010 | 0.0091 | 1.0000 | 1.000 |
| oiii_5007 | 2652 | 1.0001 | 0.9991–1.0014 | +0.0001 | 0.0008 | 1.0000 | 1.000 |
| nii_6584 | 2666 | 1.0001 | 0.9982–1.0028 | +0.0001 | 0.0016 | 1.0000 | 1.000 |
| sii_6716 | 2531 | 1.0000 | 0.9975–1.0028 | +0.0000 | 0.0017 | 1.0000 | 1.000 |
| sii_6731 | 2566 | 1.0000 | 0.9968–1.0033 | +0.0000 | 0.0021 | 1.0000 | 1.000 |
| sii_total | 2641 | 1.0001 | 0.9973–1.0036 | +0.0001 | 0.0020 | 1.0000 | 1.000 |

## BPT

- class agreement: 98.85% over 2269 spaxels classified in both products
- AGN/star-forming/composite group agreement: 99.65%
- ours: {'n_classified': 2289, 'n_total': 5476, 'star_forming': 9, 'star_forming_fraction': 0.003931847968545216, 'composite': 83, 'composite_fraction': 0.036260375709917, 'seyfert': 1945, 'seyfert_fraction': 0.8497160332022717, 'liner': 231, 'liner_fraction': 0.10091743119266056, 'agn_unclassified': 21, 'agn_unclassified_fraction': 0.009174311926605505}
- reference: {'n_classified': 2300, 'n_total': 5476, 'star_forming': 14, 'star_forming_fraction': 0.00608695652173913, 'composite': 80, 'composite_fraction': 0.034782608695652174, 'seyfert': 1955, 'seyfert_fraction': 0.85, 'liner': 235, 'liner_fraction': 0.10217391304347827, 'agn_unclassified': 16, 'agn_unclassified_fraction': 0.006956521739130435}

## Kinematics

| quantity | N | median offset (ours-ref) | robust scatter | Pearson r | median error ratio |
|---|---:|---:|---:|---:|---:|
| stellar_velocity | 2688 | +0.000 | 0.000 | 1.0000 | 1.000 |
| stellar_sigma | 2688 | +0.000 | 0.000 | 1.0000 | 1.000 |
| gas_velocity_ha | 2688 | -0.001 | 0.082 | 0.9023 | 1.000 |
| gas_sigma_ha | 2601 | +0.024 | 0.277 | 0.9706 | 1.000 |

## Interpretation

* The H-alpha, H-beta, [O III], [N II] and [S II] fluxes agree closely when the
  same LOGCUBE and DAPTYPE are used; the residual differences are the expected
  effect of the code-version change (DAP 3.1.0 -> 4.5.0), not a different
  reduction or a different binning.
* The formal-error ratio is a diagnostic of the covariance implementation.  A
  ratio near unity means the two MAPS report comparable precision; it is not
  an independent validation of the errors because both derive from the same
  data and the same SASUKE likelihood.
* BPT classes are discrete.  Spaxels near a boundary can change class for a
  small flux difference; the confusion matrix in `comparison_bpt.json` is the
  honest summary.  The AGN/star-forming/composite group agreement is more
  robust than the Seyfert/LINER sub-class agreement.
* The kinematic zero point is tied to the NSA redshift in both runs.  A small
  median velocity offset therefore reflects the pPXF/line-fit setup, not a
  different systemic redshift.
* Spaxels are correlated by the HYB10 bins; do not interpret the spaxel count
  as an independent-sample size.
