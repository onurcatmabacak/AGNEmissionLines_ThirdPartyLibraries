# Cross-tool AGN emission-line comparison

## Object `04545183216`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 0.8764492804155621 | 1.5570508144700357 | line_complex_reduced (reported) |
| badass | 3.4999510431446867 | 1.5483115836529187 | line_window_computed |
| fantasy_agn | 2.802711317348821 | 5.333796052124778 | line_window_computed |
| gelato | 2.710640805271729 | 10.049561191758354 | global_reduced (reported) |
| gleam | 598.1929636673625 | 45.12743133142857 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 11 |  | 154 |  |
| Hb4861 | broad | 3.16e+03 | 1.7e+03 | 2.58e+03 | 2.47e+03 | 2.04e+03 |
| Hb4861 | narrow |  | 12.7 | 22.8 | 66.2 | 1.25e+03 |
| Hb4861 | total |  | 1.71e+03 |  |  |  |
| OIII4959 | narrow | 45.5 | 56.3 | 59.1 | 102 | 43 |
| OIII4959 | outflow | 67.8 |  |  |  |  |
| OIII5007 | narrow | 139 | 169 | 179 | 306 | 129 |
| OIII5007 | outflow | 208 |  |  |  |  |
| Ha6563 | broad | 1.26e+04 | 7.3e+03 | 1.12e+04 | 1.13e+04 | 1.06e+04 |
| Ha6563 | narrow | 306 | 134 | 217 | 500 |  |
| Ha6563 | total |  | 7.49e+03 |  |  |  |
| NII6585 | narrow | 4.26 | 0 | 18.6 | -172 |  |
| SII6718 | narrow | 9.89 | 26.7 |  | 53.3 |  |
| SII6732 | narrow | 37.5 | 13.1 |  | 32 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04545183216/fit.log), [output.fits](pyqsofit/04545183216/output.fits), [pyqsofit_model.csv](pyqsofit/04545183216/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04545183216/qsopar.fits), [result.pdf](pyqsofit/04545183216/result.pdf), [spectrum.fits](pyqsofit/04545183216/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04545183216/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04545183216/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04545183216/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04545183216/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04545183216/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04545183216/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04545183216/2-onur/my_sdss.fits), [docker.log](badass/04545183216/docker.log), [fit.log](badass/04545183216/fit.log), [main.py](badass/04545183216/main.py), [spectrum.pdf](badass/04545183216/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04545183216/balmer.csv), [broad.csv](fantasy_agn/04545183216/broad.csv), [coronal.csv](fantasy_agn/04545183216/coronal.csv), [docker.log](fantasy_agn/04545183216/docker.log), [feII_forbidden.csv](fantasy_agn/04545183216/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04545183216/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04545183216/feii_IZw1.csv), [fit.log](fantasy_agn/04545183216/fit.log), [helium.csv](fantasy_agn/04545183216/helium.csv), [hydrogen.csv](fantasy_agn/04545183216/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04545183216/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04545183216/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04545183216/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04545183216/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04545183216/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04545183216/oiii_nii.csv), [uvfe.csv](fantasy_agn/04545183216/uvfe.csv)
- `gelato`: [docker.log](gelato/04545183216/docker.log), [my_sdss-comp.pdf](gelato/04545183216/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04545183216/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04545183216/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04545183216/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04545183216/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04545183216/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.png)

## Object `04570362657`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 2.506924685860208 | 2.284813159329287 | line_complex_reduced (reported) |
| badass | 6.124984551901928 | 2.826145229196997 | line_window_computed |
| fantasy_agn | 10.309146683072777 | 19.196873879535012 | line_window_computed |
| gelato | 2.5436079740787623 | 11.503415793145738 | global_reduced (reported) |
| gleam | 254.30970071939896 | 40.49655703 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 38.2 |  | 73.9 |  |
| OII3727 | total |  |  |  |  | 75.5 |
| Hb4861 | broad | 1.42e+03 | 976 | 1.11e+03 | 1.07e+03 | 1.03e+03 |
| Hb4861 | narrow |  | 0 | 95.7 | 246 | 826 |
| Hb4861 | total |  | 976 |  |  |  |
| OIII4959 | broad |  |  |  |  | 97.1 |
| OIII4959 | narrow | 43 | 73.5 | 68.4 | 34.3 |  |
| OIII4959 | outflow | 42.5 |  |  |  |  |
| OIII5007 | narrow | 132 | 221 | 207 | 103 |  |
| OIII5007 | outflow | 130 |  |  |  |  |
| OIII5007 | total |  |  |  |  | 291 |
| Ha6563 | broad | 5.78e+03 | 3.73e+03 | 4.34e+03 | 3.8e+03 | 2.04e+03 |
| Ha6563 | narrow | 200 | 312 | 563 | 1.44e+03 | 3.69e+03 |
| Ha6563 | total |  | 4.21e+03 |  |  |  |
| NII6585 | narrow | 116 | 0 | 281 | 390 | 69.1 |
| SII6718 | narrow | 41.9 | 0 |  | 96.7 |  |
| SII6732 | narrow | 32.4 | 28.4 |  | 42.6 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04570362657/fit.log), [output.fits](pyqsofit/04570362657/output.fits), [pyqsofit_model.csv](pyqsofit/04570362657/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04570362657/qsopar.fits), [result.pdf](pyqsofit/04570362657/result.pdf), [spectrum.fits](pyqsofit/04570362657/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04570362657/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04570362657/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04570362657/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04570362657/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04570362657/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04570362657/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04570362657/2-onur/my_sdss.fits), [docker.log](badass/04570362657/docker.log), [fit.log](badass/04570362657/fit.log), [main.py](badass/04570362657/main.py), [spectrum.pdf](badass/04570362657/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04570362657/balmer.csv), [broad.csv](fantasy_agn/04570362657/broad.csv), [coronal.csv](fantasy_agn/04570362657/coronal.csv), [docker.log](fantasy_agn/04570362657/docker.log), [feII_forbidden.csv](fantasy_agn/04570362657/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04570362657/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04570362657/feii_IZw1.csv), [fit.log](fantasy_agn/04570362657/fit.log), [helium.csv](fantasy_agn/04570362657/helium.csv), [hydrogen.csv](fantasy_agn/04570362657/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04570362657/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04570362657/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04570362657/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04570362657/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04570362657/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04570362657/oiii_nii.csv), [uvfe.csv](fantasy_agn/04570362657/uvfe.csv)
- `gelato`: [docker.log](gelato/04570362657/docker.log), [my_sdss-comp.pdf](gelato/04570362657/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04570362657/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04570362657/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04570362657/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04570362657/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04570362657/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.png)

## Object `04570493016`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 9.122382604876114 | 3.179874366331031 | line_complex_reduced (reported) |
| badass | 6.191692121701213 | 3.019700068206319 | line_window_computed |
| fantasy_agn | 14.525500193704818 | 23.898886008289953 | line_window_computed |
| gelato | 6.609542535174349 | 17.29008206594127 | global_reduced (reported) |
| gleam | 262.12977414488086 | 119.88150179375 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 118 |  | 344 |  |
| OII3727 | total |  |  |  |  | 129 |
| Hb4861 | broad | 5.83e+03 | 2.51e+03 | 3.68e+03 | 3.33e+03 | 1.79e+03 |
| Hb4861 | narrow |  | 257 | 309 | 791 | 2.45e+03 |
| Hb4861 | total |  | 2.76e+03 |  |  |  |
| OIII4959 | narrow | 331 | 266 | 360 | 203 |  |
| OIII4959 | outflow | 147 |  |  |  |  |
| OIII4959 | total |  |  |  |  | 340 |
| OIII5007 | narrow | 1.01e+03 | 802 | 1.09e+03 | 611 |  |
| OIII5007 | outflow | 448 |  |  |  |  |
| OIII5007 | total |  |  |  |  | 1.02e+03 |
| Ha6563 | broad | 1.56e+04 | 1.05e+04 | 1.19e+04 | 1.11e+04 | 5.47e+03 |
| Ha6563 | narrow | 1.06e+03 | 868 | 1.48e+03 | 3.76e+03 | 9.77e+03 |
| Ha6563 | total |  | 1.17e+04 |  |  |  |
| NII6585 | narrow | 429 | 191 | 643 | 1.12e+03 | 67.3 |
| SII6718 | narrow | 7.31 | 57.8 |  | 243 |  |
| SII6732 | narrow | 26.2 | 40.2 |  | 80.1 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04570493016/fit.log), [output.fits](pyqsofit/04570493016/output.fits), [pyqsofit_model.csv](pyqsofit/04570493016/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04570493016/qsopar.fits), [result.pdf](pyqsofit/04570493016/result.pdf), [spectrum.fits](pyqsofit/04570493016/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04570493016/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04570493016/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04570493016/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04570493016/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04570493016/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04570493016/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04570493016/2-onur/my_sdss.fits), [docker.log](badass/04570493016/docker.log), [fit.log](badass/04570493016/fit.log), [main.py](badass/04570493016/main.py), [spectrum.pdf](badass/04570493016/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04570493016/balmer.csv), [broad.csv](fantasy_agn/04570493016/broad.csv), [coronal.csv](fantasy_agn/04570493016/coronal.csv), [docker.log](fantasy_agn/04570493016/docker.log), [feII_forbidden.csv](fantasy_agn/04570493016/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04570493016/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04570493016/feii_IZw1.csv), [fit.log](fantasy_agn/04570493016/fit.log), [helium.csv](fantasy_agn/04570493016/helium.csv), [hydrogen.csv](fantasy_agn/04570493016/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04570493016/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04570493016/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04570493016/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04570493016/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04570493016/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04570493016/oiii_nii.csv), [uvfe.csv](fantasy_agn/04570493016/uvfe.csv)
- `gelato`: [docker.log](gelato/04570493016/docker.log), [my_sdss-comp.pdf](gelato/04570493016/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04570493016/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04570493016/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04570493016/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04570493016/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04570493016/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.png)

## Object `04592503068`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 17.174664340395577 | 3.112398196886896 | line_complex_reduced (reported) |
| badass | 11.566331862234872 | 5.811123008457022 | line_window_computed |
| fantasy_agn | 21.24154665836514 | 33.66017305979453 | line_window_computed |
| gelato | 4.150692584988156 | 9.41251367779913 | global_reduced (reported) |
| gleam | 53.4239812367293 | 18.409232101999997 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 55 |  | 150 | 126 |
| Hb4861 | broad | 1.24e+03 | 385 | 549 | 513 | 564 |
| Hb4861 | narrow |  | 135 | 96.9 | 110 | 89.5 |
| Hb4861 | total |  | 520 |  |  |  |
| OIII4959 | narrow | 149 | 192 | 223 | 106 | 222 |
| OIII4959 | outflow | 93.3 |  |  |  |  |
| OIII5007 | narrow | 456 | 578 | 676 | 320 | 666 |
| OIII5007 | outflow | 286 |  |  |  |  |
| Ha6563 | broad | 3.29e+03 | 2.17e+03 | 2.74e+03 | 2.96e+03 | 2.79e+03 |
| Ha6563 | narrow | 510 | 813 | 468 | 585 | 451 |
| Ha6563 | total |  | 3.04e+03 |  |  |  |
| NII6585 | narrow | 401 | 663 | 405 | 453 | 361 |
| SII6718 | narrow | 90.8 | 65.3 |  | 116 | 73 |
| SII6732 | narrow | 61.9 | 47.2 |  | 77.4 | 43.2 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592503068/fit.log), [output.fits](pyqsofit/04592503068/output.fits), [pyqsofit_model.csv](pyqsofit/04592503068/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592503068/qsopar.fits), [result.pdf](pyqsofit/04592503068/result.pdf), [spectrum.fits](pyqsofit/04592503068/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592503068/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592503068/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592503068/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592503068/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592503068/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592503068/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592503068/2-onur/my_sdss.fits), [docker.log](badass/04592503068/docker.log), [fit.log](badass/04592503068/fit.log), [main.py](badass/04592503068/main.py), [spectrum.pdf](badass/04592503068/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592503068/balmer.csv), [broad.csv](fantasy_agn/04592503068/broad.csv), [coronal.csv](fantasy_agn/04592503068/coronal.csv), [docker.log](fantasy_agn/04592503068/docker.log), [feII_forbidden.csv](fantasy_agn/04592503068/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592503068/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592503068/feii_IZw1.csv), [fit.log](fantasy_agn/04592503068/fit.log), [helium.csv](fantasy_agn/04592503068/helium.csv), [hydrogen.csv](fantasy_agn/04592503068/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592503068/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592503068/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592503068/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592503068/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592503068/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592503068/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592503068/uvfe.csv)
- `gelato`: [docker.log](gelato/04592503068/docker.log), [my_sdss-comp.pdf](gelato/04592503068/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592503068/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592503068/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592503068/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592503068/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592503068/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.png)

## Object `04592517882`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 38.765453028802796 | 2.7463885126734944 | line_complex_reduced (reported) |
| badass | 2.4670894492178594 | 1.2272413195195775 | line_window_computed |
| fantasy_agn | 4.583069014206656 | 8.08367171797202 | line_window_computed |
| gelato | 17.50561520381579 | 10.691382473480434 | global_reduced (reported) |
| gleam | 631.8181630175933 | 18.352697040625003 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  |  |  |  | 227 |
| OII3727 | narrow |  | 0 |  | 25.9 |  |
| Hb4861 | broad | 521 | 407 | 591 |  | 399 |
| Hb4861 | narrow |  | 101 | 94.8 | 379 | 178 |
| Hb4861 | total |  | 509 |  |  |  |
| OIII4959 | narrow | 39.8 | 38.6 | 32.8 | 25.7 |  |
| OIII4959 | outflow | 0.489 |  |  |  |  |
| OIII5007 | narrow | 122 | 116 | 99.4 | 77.3 |  |
| OIII5007 | outflow | 1.5 |  |  |  |  |
| Ha6563 | broad | 1.82e+03 | 1.08e+03 | 1.57e+03 |  | 1.52e+03 |
| Ha6563 | narrow | 595 | 255 | 173 | 1.21e+03 |  |
| Ha6563 | total |  | 1.53e+03 |  |  |  |
| NII6585 | narrow | 118 | 20.2 | 44.1 | 286 |  |
| SII6718 | narrow | 11.6 | 4.24 |  | 14.9 |  |
| SII6732 | narrow | 2.76 | 0.561 |  | -22 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592517882/fit.log), [output.fits](pyqsofit/04592517882/output.fits), [pyqsofit_model.csv](pyqsofit/04592517882/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592517882/qsopar.fits), [result.pdf](pyqsofit/04592517882/result.pdf), [spectrum.fits](pyqsofit/04592517882/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592517882/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592517882/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592517882/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592517882/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592517882/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592517882/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592517882/2-onur/my_sdss.fits), [docker.log](badass/04592517882/docker.log), [fit.log](badass/04592517882/fit.log), [main.py](badass/04592517882/main.py), [spectrum.pdf](badass/04592517882/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592517882/balmer.csv), [broad.csv](fantasy_agn/04592517882/broad.csv), [coronal.csv](fantasy_agn/04592517882/coronal.csv), [docker.log](fantasy_agn/04592517882/docker.log), [feII_forbidden.csv](fantasy_agn/04592517882/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592517882/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592517882/feii_IZw1.csv), [fit.log](fantasy_agn/04592517882/fit.log), [helium.csv](fantasy_agn/04592517882/helium.csv), [hydrogen.csv](fantasy_agn/04592517882/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592517882/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592517882/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592517882/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592517882/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592517882/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592517882/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592517882/uvfe.csv)
- `gelato`: [docker.log](gelato/04592517882/docker.log), [my_sdss-comp.pdf](gelato/04592517882/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592517882/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592517882/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592517882/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592517882/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592517882/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.png)

## Object `04592660180`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 5.726303766057565 | 3.0959849132801143 | line_complex_reduced (reported) |
| badass | 3.8277363895860472 | 1.4939430853979958 | line_window_computed |
| fantasy_agn | 7.4007964112145235 | 18.08394335924019 | line_window_computed |
| gelato | 3.545553641365755 | 7.983066075554687 | global_reduced (reported) |
| gleam | 355.3204152552002 | 71.50373821625 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 32.2 |  | 97.8 | 49.7 |
| Hb4861 | broad | 3.03e+03 | 946 | 1.52e+03 | 1.26e+03 | 1.33e+03 |
| Hb4861 | narrow |  | 110 | 100 | 297 | 636 |
| Hb4861 | total |  | 1.06e+03 |  |  |  |
| OIII4959 | narrow | 88.4 | 74.3 | 91.8 | 49.1 |  |
| OIII4959 | outflow | 23.4 |  |  |  |  |
| OIII4959 | total |  |  |  |  | 77.5 |
| OIII5007 | narrow | 271 | 223 | 278 | 148 |  |
| OIII5007 | outflow | 71.6 |  |  |  |  |
| OIII5007 | total |  |  |  |  | 233 |
| Ha6563 | broad | 5.6e+03 | 3.72e+03 | 4.87e+03 | 4.82e+03 | 3.88e+03 |
| Ha6563 | narrow | 739 | 444 | 644 | 1.46e+03 | 1.86e+03 |
| Ha6563 | total |  | 4.33e+03 |  |  |  |
| NII6585 | narrow | 219 | 84.2 | 184 | 144 | 86.9 |
| SII6718 | narrow | 25.5 | 23.3 |  | 92.1 |  |
| SII6732 | narrow | 47.3 | 21 |  | 67.6 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592660180/fit.log), [output.fits](pyqsofit/04592660180/output.fits), [pyqsofit_model.csv](pyqsofit/04592660180/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592660180/qsopar.fits), [result.pdf](pyqsofit/04592660180/result.pdf), [spectrum.fits](pyqsofit/04592660180/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592660180/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592660180/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592660180/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592660180/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592660180/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592660180/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592660180/2-onur/my_sdss.fits), [docker.log](badass/04592660180/docker.log), [fit.log](badass/04592660180/fit.log), [main.py](badass/04592660180/main.py), [spectrum.pdf](badass/04592660180/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592660180/balmer.csv), [broad.csv](fantasy_agn/04592660180/broad.csv), [coronal.csv](fantasy_agn/04592660180/coronal.csv), [docker.log](fantasy_agn/04592660180/docker.log), [feII_forbidden.csv](fantasy_agn/04592660180/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592660180/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592660180/feii_IZw1.csv), [fit.log](fantasy_agn/04592660180/fit.log), [helium.csv](fantasy_agn/04592660180/helium.csv), [hydrogen.csv](fantasy_agn/04592660180/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592660180/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592660180/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592660180/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592660180/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592660180/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592660180/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592660180/uvfe.csv)
- `gelato`: [docker.log](gelato/04592660180/docker.log), [my_sdss-comp.pdf](gelato/04592660180/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592660180/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592660180/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592660180/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592660180/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592660180/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.png)

## Object `04592939295`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 5.440470207945354 | 1.7259931863991622 | line_complex_reduced (reported) |
| badass | 5.456150016922869 | 2.364015912236044 | line_window_computed |
| fantasy_agn | 22.524676934299773 | 52.010312800813445 | line_window_computed |
| gelato | 4.460975642192411 | 7.985145180290975 | global_reduced (reported) |
| gleam | 244.22531453903036 | 57.406962025 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 84.1 |  | 182 |  |
| OII3727 | total |  |  |  |  | 88.5 |
| Hb4861 | broad | 3.61e+03 | 1.48e+03 | 1.79e+03 | 1.67e+03 | 1.57e+03 |
| Hb4861 | narrow |  | 134 | 47.9 | 402 | 958 |
| Hb4861 | total |  | 1.61e+03 |  |  |  |
| OIII4959 | narrow | 99.6 | 108 | 27.3 | 91.8 | 107 |
| OIII4959 | outflow | 79.6 |  |  |  |  |
| OIII5007 | narrow | 305 | 325 | 82.1 | 276 | 320 |
| OIII5007 | outflow | 244 |  |  |  |  |
| Ha6563 | broad | 7.55e+03 | 4.97e+03 | 5.94e+03 | 5.14e+03 | 4.52e+03 |
| Ha6563 | narrow | 342 | 643 | 27.8 | 1.67e+03 | 1.82e+03 |
| Ha6563 | total |  | 5.75e+03 |  |  |  |
| NII6585 | narrow | 183 | 312 | 30.1 | 576 |  |
| NII6585 | total |  |  |  |  | 495 |
| SII6718 | narrow | 39 | 61 |  | 93.3 |  |
| SII6732 | narrow | 34.6 | 0 |  | 66 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592939295/fit.log), [output.fits](pyqsofit/04592939295/output.fits), [pyqsofit_model.csv](pyqsofit/04592939295/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592939295/qsopar.fits), [result.pdf](pyqsofit/04592939295/result.pdf), [spectrum.fits](pyqsofit/04592939295/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592939295/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592939295/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592939295/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592939295/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592939295/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592939295/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592939295/2-onur/my_sdss.fits), [docker.log](badass/04592939295/docker.log), [fit.log](badass/04592939295/fit.log), [main.py](badass/04592939295/main.py), [spectrum.pdf](badass/04592939295/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592939295/balmer.csv), [broad.csv](fantasy_agn/04592939295/broad.csv), [coronal.csv](fantasy_agn/04592939295/coronal.csv), [docker.log](fantasy_agn/04592939295/docker.log), [feII_forbidden.csv](fantasy_agn/04592939295/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592939295/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592939295/feii_IZw1.csv), [fit.log](fantasy_agn/04592939295/fit.log), [helium.csv](fantasy_agn/04592939295/helium.csv), [hydrogen.csv](fantasy_agn/04592939295/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592939295/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592939295/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592939295/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592939295/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592939295/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592939295/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592939295/uvfe.csv)
- `gelato`: [docker.log](gelato/04592939295/docker.log), [my_sdss-comp.pdf](gelato/04592939295/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592939295/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592939295/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592939295/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592939295/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592939295/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.png)

## Object `04592975881`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 3.5087404819887857 | 2.2330344984478705 | line_complex_reduced (reported) |
| badass | 10.570238803912822 | 4.635472655775341 | line_window_computed |
| fantasy_agn | 14.277048925101559 | 26.087122846009223 | line_window_computed |
| gelato | 2.497712778976531 | 6.394134160579407 | global_reduced (reported) |
| gleam | 283.9080206152634 | 121.33939315750001 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 65.6 |  | 190 |  |
| OII3727 | total |  |  |  |  | 142 |
| Hb4861 | broad | 3.29e+03 | 1.59e+03 | 2.17e+03 | 1.95e+03 | 2.07e+03 |
| Hb4861 | narrow |  | 0 | 97.5 | 213 | 263 |
| Hb4861 | total |  | 1.59e+03 |  |  |  |
| OIII4959 | narrow | 176 | 218 | 281 | 184 |  |
| OIII4959 | outflow | 117 |  |  |  |  |
| OIII4959 | total |  |  |  |  | 267 |
| OIII5007 | narrow | 538 | 657 | 850 | 552 |  |
| OIII5007 | outflow | 359 |  |  |  |  |
| OIII5007 | total |  |  |  |  | 800 |
| Ha6563 | broad | 9.22e+03 | 6.19e+03 | 7.96e+03 | 8.11e+03 | 6.78e+03 |
| Ha6563 | narrow | 636 | 11.8 | 635 | 1.27e+03 | 1.66e+03 |
| Ha6563 | total |  | 6.31e+03 |  |  |  |
| NII6585 | narrow | 245 | 53.7 | 322 | 225 | 146 |
| SII6718 | narrow | 15.4 | 0 |  | 148 |  |
| SII6732 | narrow | 88 | 4.01 |  | 111 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592975881/fit.log), [output.fits](pyqsofit/04592975881/output.fits), [pyqsofit_model.csv](pyqsofit/04592975881/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592975881/qsopar.fits), [result.pdf](pyqsofit/04592975881/result.pdf), [spectrum.fits](pyqsofit/04592975881/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592975881/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592975881/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592975881/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592975881/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592975881/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592975881/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592975881/2-onur/my_sdss.fits), [docker.log](badass/04592975881/docker.log), [fit.log](badass/04592975881/fit.log), [main.py](badass/04592975881/main.py), [spectrum.pdf](badass/04592975881/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592975881/balmer.csv), [broad.csv](fantasy_agn/04592975881/broad.csv), [coronal.csv](fantasy_agn/04592975881/coronal.csv), [docker.log](fantasy_agn/04592975881/docker.log), [feII_forbidden.csv](fantasy_agn/04592975881/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592975881/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592975881/feii_IZw1.csv), [fit.log](fantasy_agn/04592975881/fit.log), [helium.csv](fantasy_agn/04592975881/helium.csv), [hydrogen.csv](fantasy_agn/04592975881/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592975881/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592975881/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592975881/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592975881/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592975881/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592975881/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592975881/uvfe.csv)
- `gelato`: [docker.log](gelato/04592975881/docker.log), [my_sdss-comp.pdf](gelato/04592975881/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592975881/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592975881/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592975881/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592975881/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592975881/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.png)

## Object `04592979214`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 14.313645972732749 | 2.3454305926020385 | line_complex_reduced (reported) |
| badass | 14.473510734869256 | 6.972958950183405 | line_window_computed |
| fantasy_agn | 40.90625865340928 | 56.125548781309924 | line_window_computed |
| gelato | 1.8217851903243467 | 6.587364123351637 | global_reduced (reported) |
| gleam | 28.177379685769566 | 44.582382152 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 265 |  | 407 | 392 |
| Hb4861 | broad | 2.61e+03 | 1.06e+03 | 994 | 1.12e+03 | 1.12e+03 |
| Hb4861 | narrow |  | 289 | 155 | 171 | 148 |
| Hb4861 | total |  | 1.35e+03 |  |  |  |
| OIII4959 | narrow | 368 | 385 | 397 | 366 | 405 |
| OIII4959 | outflow | 64.2 |  |  |  |  |
| OIII5007 | narrow | 1.13e+03 | 1.16e+03 | 1.2e+03 | 1.1e+03 | 1.21e+03 |
| OIII5007 | outflow | 196 |  |  |  |  |
| Ha6563 | broad | 4.84e+03 | 3.9e+03 | 4.48e+03 | 4.45e+03 | 4.19e+03 |
| Ha6563 | narrow | 583 | 853 | 599 | 650 | 591 |
| Ha6563 | total |  | 4.9e+03 |  |  |  |
| NII6585 | narrow | 177 | 329 | 179 | 182 | 167 |
| SII6718 | narrow | 166 | 97.5 |  | 184 | 137 |
| SII6732 | narrow | 151 | 80.1 |  | 160 | 118 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592979214/fit.log), [output.fits](pyqsofit/04592979214/output.fits), [pyqsofit_model.csv](pyqsofit/04592979214/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592979214/qsopar.fits), [result.pdf](pyqsofit/04592979214/result.pdf), [spectrum.fits](pyqsofit/04592979214/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592979214/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592979214/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592979214/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592979214/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592979214/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592979214/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592979214/2-onur/my_sdss.fits), [docker.log](badass/04592979214/docker.log), [fit.log](badass/04592979214/fit.log), [main.py](badass/04592979214/main.py), [spectrum.pdf](badass/04592979214/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592979214/balmer.csv), [broad.csv](fantasy_agn/04592979214/broad.csv), [coronal.csv](fantasy_agn/04592979214/coronal.csv), [docker.log](fantasy_agn/04592979214/docker.log), [feII_forbidden.csv](fantasy_agn/04592979214/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592979214/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592979214/feii_IZw1.csv), [fit.log](fantasy_agn/04592979214/fit.log), [helium.csv](fantasy_agn/04592979214/helium.csv), [hydrogen.csv](fantasy_agn/04592979214/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592979214/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592979214/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592979214/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592979214/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592979214/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592979214/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592979214/uvfe.csv)
- `gelato`: [docker.log](gelato/04592979214/docker.log), [my_sdss-comp.pdf](gelato/04592979214/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592979214/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592979214/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592979214/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592979214/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592979214/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.png)

## Object `06872228427`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 36.452370835492296 | 1.8395955511415951 | line_complex_reduced (reported) |
| badass | 6.866600157031294 | 4.92631585608877 | line_window_computed |
| fantasy_agn | 19.490932222467862 | 26.47900868773614 | line_window_computed |
| gelato | 1.0619774160175262 | 2.794472106066657 | global_reduced (reported) |
| gleam | 43.05954249260949 | 9.623841876 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 100 |  | 109 | 105 |
| Hb4861 | broad | 269 | 162 | 212 | 153 | 154 |
| Hb4861 | narrow |  | 52.8 | 36.1 | 47 | 31.9 |
| Hb4861 | total |  | 215 |  |  |  |
| OIII4959 | narrow | 77.8 | 131 | 133 | 77.9 |  |
| OIII4959 | outflow | 69 |  |  |  |  |
| OIII4959 | total |  |  |  |  | 138 |
| OIII5007 | narrow | 238 | 394 | 402 | 234 | 415 |
| OIII5007 | outflow | 211 |  |  |  |  |
| Ha6563 | broad | 1.13e+03 | 973 | 994 | 1.12e+03 | 1e+03 |
| Ha6563 | narrow | 227 | 283 | 262 | 284 | 241 |
| Ha6563 | total |  | 1.34e+03 |  |  |  |
| NII6585 | narrow | 201 | 269 | 235 | 224 | 208 |
| SII6718 | narrow | 62.5 | 39.8 |  | 73.4 | 49.9 |
| SII6732 | narrow | 55.6 | 0 |  | 61.2 | 42.1 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/06872228427/fit.log), [output.fits](pyqsofit/06872228427/output.fits), [pyqsofit_model.csv](pyqsofit/06872228427/pyqsofit_model.csv), [qsopar.fits](pyqsofit/06872228427/qsopar.fits), [result.pdf](pyqsofit/06872228427/result.pdf), [spectrum.fits](pyqsofit/06872228427/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/06872228427/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/06872228427/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/06872228427/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/06872228427/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/06872228427/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/06872228427/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/06872228427/2-onur/my_sdss.fits), [docker.log](badass/06872228427/docker.log), [fit.log](badass/06872228427/fit.log), [main.py](badass/06872228427/main.py), [spectrum.pdf](badass/06872228427/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/06872228427/balmer.csv), [broad.csv](fantasy_agn/06872228427/broad.csv), [coronal.csv](fantasy_agn/06872228427/coronal.csv), [docker.log](fantasy_agn/06872228427/docker.log), [feII_forbidden.csv](fantasy_agn/06872228427/feII_forbidden.csv), [feII_model.csv](fantasy_agn/06872228427/feII_model.csv), [feii_IZw1.csv](fantasy_agn/06872228427/feii_IZw1.csv), [fit.log](fantasy_agn/06872228427/fit.log), [helium.csv](fantasy_agn/06872228427/helium.csv), [hydrogen.csv](fantasy_agn/06872228427/hydrogen.csv), [my_sdss.pdf](fantasy_agn/06872228427/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/06872228427/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/06872228427/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/06872228427/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/06872228427/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/06872228427/oiii_nii.csv), [uvfe.csv](fantasy_agn/06872228427/uvfe.csv)
- `gelato`: [docker.log](gelato/06872228427/docker.log), [my_sdss-comp.pdf](gelato/06872228427/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/06872228427/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/06872228427/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/06872228427/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/06872228427/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/06872228427/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.png)
