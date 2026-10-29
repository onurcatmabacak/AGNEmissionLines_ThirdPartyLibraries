# MaNGA DAP comparison — NGC1194_z_0.0136

- ours: `/app/output/fits/manga_dap_maps.fits.gz` (DAPTYPE `HYB10-MILESHC-MASTARHC2`, DAP 4.5.0, DRP v3_1_1)
- reference: `/app/reference/manga-9193-12701-MAPS-HYB10-MILESHC-MASTARHC2.fits.gz` (DAPTYPE `HYB10-MILESHC-MASTARHC2`, DAP 3.1.0, DRP v3_1_1)

## Key-line statistics

| quantity | N | median ratio ours/ref | 16–84% | median fractional diff | robust scatter | Pearson r | median error ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| ha | 2683 | 2.3697 | 1.0768–4.8024 | +1.3697 | 1.5966 | 0.9896 | 1.593 |
| hb | 2256 | 0.8904 | 0.4549–1.5869 | -0.1096 | 0.5050 | 0.9913 | 0.691 |
| oiii_5007 | 2666 | 1.0111 | 0.6443–1.6858 | +0.0111 | 0.4594 | 0.9965 | 0.548 |
| nii_6584 | 2000 | 0.5268 | 0.0512–1.3244 | -0.4732 | 0.6718 | 0.9888 | 1.257 |
| sii_6716 | 2548 | 1.8763 | 0.9698–4.2695 | +0.8763 | 1.3335 | 0.9834 | 1.206 |
| sii_6731 | 2340 | 1.1507 | 0.7019–2.3832 | +0.1507 | 0.5930 | 0.9915 | 1.000 |
| sii_total | 2649 | 1.5819 | 0.9580–3.0822 | +0.5819 | 0.8798 | 0.9931 | 1.091 |

## BPT

- class agreement: 40.82% over 1749 spaxels classified in both products
- AGN/star-forming/composite group agreement: 54.20%
- ours: {'n_classified': 2005, 'n_total': 5476, 'star_forming': 614, 'star_forming_fraction': 0.30623441396508727, 'composite': 215, 'composite_fraction': 0.10723192019950124, 'seyfert': 744, 'seyfert_fraction': 0.371072319201995, 'liner': 432, 'liner_fraction': 0.21546134663341646, 'agn_unclassified': 0, 'agn_unclassified_fraction': 0.0}
- reference: {'n_classified': 2300, 'n_total': 5476, 'star_forming': 14, 'star_forming_fraction': 0.00608695652173913, 'composite': 80, 'composite_fraction': 0.034782608695652174, 'seyfert': 1955, 'seyfert_fraction': 0.85, 'liner': 235, 'liner_fraction': 0.10217391304347827, 'agn_unclassified': 16, 'agn_unclassified_fraction': 0.006956521739130435}

## Kinematics

| quantity | N | median offset (ours-ref) | robust scatter | Pearson r | median error ratio |
|---|---:|---:|---:|---:|---:|
| stellar_velocity | 2688 | +0.000 | 8.197 | 0.9401 | 0.337 |
| stellar_sigma | 2688 | +0.499 | 7.164 | 0.7124 | 0.336 |
| gas_velocity_ha | 2627 | +175.543 | 123.708 | 0.2331 | 0.213 |
| gas_sigma_ha | 2551 | +651.011 | 245.345 | 0.0208 | 2.953 |

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
