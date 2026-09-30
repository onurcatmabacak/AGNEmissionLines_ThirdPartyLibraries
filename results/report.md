# Cross-tool AGN emission-line comparison

## Object `04545183216`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 254.7742998445117 | 0.4119222782039338 | line_complex_reduced (reported) |
| badass | 3.7437908151077752 | 1.5376319825876903 | line_window_computed |
| fantasy_agn | 260.43862931146913 | 5.081087118724047 | line_window_computed |
| gelato | 41.05490707340578 | 29.567887789063523 | global_reduced (reported) |
| gleam | 429.42647124210475 | 6.647965448571429 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0.00804 |  |  |  |
| OII3727 | narrow |  | 30.2 |  | 136 |  |
| OII3727 | total |  |  |  |  | 35.5 |
| Hb4861 | broad | 3.81e+03 | 1.29e+03 | 2.46e+03 |  |  |
| Hb4861 | narrow |  | 186 | 9.68 | 668 |  |
| Hb4861 | total |  | 1.58e+03 |  |  | 282 |
| OIII4959 | broad |  | 55.2 |  |  |  |
| OIII4959 | narrow | 44.7 | 0 | 106 | -8.69 |  |
| OIII4959 | outflow | 90.6 |  |  |  |  |
| OIII4959 | total |  | 55.2 |  |  | 47.9 |
| OIII5007 | broad |  | 166 |  |  |  |
| OIII5007 | narrow | 137 | 0 | 321 | -26.1 |  |
| OIII5007 | outflow | 277 |  |  |  |  |
| OIII5007 | total |  | 166 |  |  | 144 |
| Ha6563 | broad | 1.05e+04 | 1.23e+03 | 1.07e+04 |  |  |
| Ha6563 | narrow | 467 | 832 | 149 | 2.3e+03 |  |
| Ha6563 | total |  | 7.34e+03 |  |  | 173 |
| NII6585 | narrow | 4.34 | 0 | 0 | 1.99e+03 |  |
| SII6718 | narrow | 23 | 0 |  | 110 |  |
| SII6732 | narrow | 12.8 | 0.0122 |  | -83.4 |  |

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
| pyqsofit | 118.72679802427243 | 11.397230250141813 | line_complex_reduced (reported) |
| badass | 9.906621545544994 | 4.073058620591634 | line_window_computed |
| fantasy_agn | 22.916875272462534 | 14.152910793517327 | line_window_computed |
| gelato | 2.5083735567406897 | 11.504602485892967 | global_reduced (reported) |
| gleam | 135.55673039394844 | 6.557355025 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 48.6 |  | 73.7 |  |
| OII3727 | total |  |  |  |  | 68 |
| Hb4861 | broad | 997 | 0 | 434 | 1.06e+03 |  |
| Hb4861 | narrow |  | 591 | 608 | 246 |  |
| Hb4861 | total |  | 922 |  |  | 1.01e+03 |
| OIII4959 | broad |  | 95 |  |  |  |
| OIII4959 | narrow | 64.3 | 0 | 91.8 | 33.6 |  |
| OIII4959 | outflow | 34.4 |  |  |  |  |
| OIII4959 | total |  | 95 |  |  | 96.3 |
| OIII5007 | broad |  | 286 |  |  |  |
| OIII5007 | narrow | 197 | 0 | 278 | 101 |  |
| OIII5007 | outflow | 105 |  |  |  |  |
| OIII5007 | total |  | 286 |  |  | 289 |
| Ha6563 | broad | 2.88e+03 | 1.48e+03 | 2.68e+03 | 3.81e+03 | 3.45e+03 |
| Ha6563 | narrow | 1.42e+03 | 1.03e+03 | 1.28e+03 | 1.44e+03 | 1.38e+03 |
| Ha6563 | total |  | 4.48e+03 |  |  |  |
| NII6585 | narrow | 1.21e+03 | 10.7 | 55.5 | 374 |  |
| NII6585 | total |  |  |  |  | 208 |
| SII6718 | narrow | 41.9 | 4.46 |  | 98 |  |
| SII6718 | total |  |  |  |  | 38.4 |
| SII6732 | narrow | 67.6 | 5.04 |  | 41.5 |  |
| SII6732 | total |  |  |  |  | 22.4 |

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
| pyqsofit | 108.31271051162899 | 1.7010315507708564 | line_complex_reduced (reported) |
| badass | 33.32089156730962 | 16.025617211314202 | line_window_computed |
| fantasy_agn | 104.87515055514854 | 15.305729409793274 | line_window_computed |
| gelato | 6.710162881222786 | 17.43465278091642 | global_reduced (reported) |
| gleam | 257.8700000019865 | 53.05698748538461 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 0 |  | 344 |  |
| OII3727 | total |  |  |  |  | 102 |
| Hb4861 | broad | 4.97e+03 | 0 | 2.41e+03 | 3.31e+03 | 2.92e+03 |
| Hb4861 | narrow |  | 1.96e+03 | 1.54e+03 | 777 | 433 |
| Hb4861 | total |  | 3.06e+03 |  |  |  |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 272 | 282 | 362 | 204 |  |
| OIII4959 | outflow | 138 |  |  |  |  |
| OIII4959 | total |  | 446 |  |  | 302 |
| OIII5007 | broad |  | 0 |  |  |  |
| OIII5007 | narrow | 833 | 849 | 1.1e+03 | 613 |  |
| OIII5007 | outflow | 423 |  |  |  |  |
| OIII5007 | total |  | 1.34e+03 |  |  | 906 |
| Ha6563 | broad | 1.46e+04 | 4.52e+03 | 8.32e+03 | 1.15e+04 |  |
| Ha6563 | narrow | 1.94e+03 | 2.66e+03 | 3.25e+03 | 3.5e+03 |  |
| Ha6563 | total |  | 1.29e+04 |  |  | 1.24e+04 |
| NII6585 | narrow | 649 | 29.3 | 1.87 | 923 |  |
| SII6718 | narrow | 2.41 | 0 |  | 246 |  |
| SII6732 | narrow | 23.7 | 25.5 |  | 78.7 |  |

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
| pyqsofit | 89.8268962401634 | 0.5117031477089717 | line_complex_reduced (reported) |
| badass | 65.04570066967182 | 36.551232941965615 | line_window_computed |
| fantasy_agn | 69.29059284808437 | 30.93493345799394 | line_window_computed |
| gelato | 5.0739047792208725 | 9.622495426687959 | global_reduced (reported) |
| gleam | 49.35288759555973 | 5.925211703333333 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 3.33 |  |  |  |
| OII3727 | narrow |  | 99.6 |  | 150 |  |
| OII3727 | total |  |  |  |  | 125 |
| Hb4861 | broad | 1.67e+03 | 3.78 | 569 | 506 |  |
| Hb4861 | narrow |  | 350 | 97.2 | 119 |  |
| Hb4861 | total |  | 545 |  |  | 119 |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 150 | 177 | 227 | 122 |  |
| OIII4959 | outflow | 104 |  |  |  |  |
| OIII4959 | total |  | 280 |  |  | 220 |
| OIII5007 | broad |  | 0 |  |  |  |
| OIII5007 | narrow | 459 | 532 | 688 | 366 |  |
| OIII5007 | outflow | 319 |  |  |  |  |
| OIII5007 | total |  | 842 |  |  | 659 |
| Ha6563 | broad | 3.32e+03 | 0 | 2.61e+03 | 2.7e+03 | 2.4e+03 |
| Ha6563 | narrow | 505 | 834 | 628 | 663 | 421 |
| Ha6563 | total |  | 3.35e+03 |  |  |  |
| NII6585 | narrow | 404 | 50.6 | 453 | 585 |  |
| NII6585 | total |  |  |  |  | 351 |
| SII6718 | narrow | 90.9 | 34.7 |  | 118 |  |
| SII6718 | total |  |  |  |  | 89.9 |
| SII6732 | narrow | 61.9 | 0 |  | 77.8 |  |
| SII6732 | total |  |  |  |  | 56.4 |

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
| pyqsofit | 162.77246367432835 | 10.434943236620626 | line_complex_reduced (reported) |
| badass | 30.772800259772406 | 16.08337800957427 | line_window_computed |
| fantasy_agn | 162.51985640240662 | 2.8744151045402186 | line_window_computed |
| gelato | 17.427925977367536 | 10.679560271699224 | global_reduced (reported) |
| gleam | 579.8507956887239 | 8.926452763076922 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 10.2 |  | 27.2 |  |
| Hb4861 | broad | 350 | 0.0397 | 436 |  | 360 |
| Hb4861 | narrow |  | 267 | 220 | 379 | 108 |
| Hb4861 | total |  | 423 |  |  |  |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 0.176 | 27.6 | 56.4 | 20.4 |  |
| OIII4959 | outflow | 39.6 |  |  |  |  |
| OIII4959 | total |  | 43.7 |  |  | 25.1 |
| OIII5007 | broad |  | 0 |  |  |  |
| OIII5007 | narrow | 0.54 | 81.2 | 169 | 61.2 |  |
| OIII5007 | outflow | 121 |  |  |  |  |
| OIII5007 | total |  | 131 |  |  |  |
| Ha6563 | broad | 1.34e+03 | 11.3 | 1.22e+03 |  |  |
| Ha6563 | narrow | 930 | 402 | 358 | 1.21e+03 |  |
| Ha6563 | total |  | 1.62e+03 |  |  | 898 |
| NII6585 | narrow | 283 | 0.00613 | 50.2 | 287 |  |
| SII6718 | narrow | 26.4 | 0 |  | 15.1 |  |
| SII6718 | total |  |  |  |  | 13.3 |
| SII6732 | narrow | 22.7 | 0.000711 |  | -22.4 |  |

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
| pyqsofit | 154.21981699996329 | 0.6307392851090011 | line_complex_reduced (reported) |
| badass | 16.56440701444993 | 6.077258166153778 | line_window_computed |
| fantasy_agn | 153.96843051726194 | 10.56293695089248 | line_window_computed |
| gelato | 3.4920469247793275 | 7.976494530202093 | global_reduced (reported) |
| gleam | 197.47034131423155 | 5.617181918333334 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 50.9 |  |  |  |
| OII3727 | narrow |  | 0 |  | 98 |  |
| OII3727 | total |  |  |  |  | 36.1 |
| Hb4861 | broad | 1.87e+03 | 0 | 1.1e+03 | 1.26e+03 |  |
| Hb4861 | narrow |  | 691 | 468 | 296 |  |
| Hb4861 | total |  | 1.07e+03 |  |  | 637 |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 109 | 77.4 | 115 | 48 |  |
| OIII4959 | outflow | 1.68 |  |  |  |  |
| OIII4959 | total |  | 122 |  |  | 93.7 |
| OIII5007 | broad |  | 0 |  |  |  |
| OIII5007 | narrow | 333 | 233 | 348 | 144 |  |
| OIII5007 | outflow | 5.14 |  |  |  |  |
| OIII5007 | total |  | 367 |  |  | 281 |
| Ha6563 | broad | 5.11e+03 | 967 | 3.68e+03 | 4.83e+03 | 3.44e+03 |
| Ha6563 | narrow | 1.19e+03 | 1.02e+03 | 1.1e+03 | 1.45e+03 | 129 |
| Ha6563 | total |  | 4.66e+03 |  |  |  |
| NII6585 | narrow | 357 | 0 | 0 | 141 |  |
| NII6585 | total |  |  |  |  | 45.4 |
| SII6718 | narrow | 3.28 | 16.9 |  | 94.5 |  |
| SII6718 | total |  |  |  |  | 29.4 |
| SII6732 | narrow | 53.1 | 0 |  | 66.2 |  |
| SII6732 | total |  |  |  |  | 20.1 |

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
| pyqsofit | 11.783823148081737 | 0.4534889394744983 | line_complex_reduced (reported) |
| badass | 14.657788853830619 | 7.095120587225127 | line_window_computed |
| fantasy_agn | 29.92661796302919 | 18.22879258904259 | line_window_computed |
| gelato | 4.213439824543534 | 8.063410344882952 | global_reduced (reported) |
| gleam | 58.33161068560424 | 4.262436038333333 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 186 |  |  |  |
| OII3727 | narrow |  | 97.9 |  | 182 |  |
| OII3727 | total |  |  |  |  | 62.4 |
| Hb4861 | broad | 2.23e+03 | 321 | 1.09e+03 | 1.65e+03 |  |
| Hb4861 | narrow |  | 920 | 737 | 406 |  |
| Hb4861 | total |  | 1.75e+03 |  |  | 1.06e+03 |
| OIII4959 | broad |  | 0.335 |  |  |  |
| OIII4959 | narrow | 81.3 | 101 | 117 | 90 |  |
| OIII4959 | outflow | 59.2 |  |  |  |  |
| OIII4959 | total |  | 160 |  |  | 107 |
| OIII5007 | broad |  | 1.01 |  |  |  |
| OIII5007 | narrow | 249 | 303 | 355 | 270 |  |
| OIII5007 | outflow | 181 |  |  |  |  |
| OIII5007 | total |  | 480 |  |  | 322 |
| Ha6563 | broad | 5.88e+03 | 678 | 4.36e+03 | 5.24e+03 | 4.57e+03 |
| Ha6563 | narrow | 1.08e+03 | 1.39e+03 | 1.24e+03 | 1.68e+03 | 270 |
| Ha6563 | total |  | 6.26e+03 |  |  |  |
| NII6585 | narrow | 886 | 0 | 127 | 481 |  |
| NII6585 | total |  |  |  |  | 174 |
| SII6718 | narrow | 4.04 | 13.8 |  | 90.3 |  |
| SII6718 | total |  |  |  |  | 43.9 |
| SII6732 | narrow | 67 | 5.56 |  | 61.9 |  |
| SII6732 | total |  |  |  |  | 22.6 |

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
| pyqsofit | 101.57639216774618 | 2.073758452348709 | line_complex_reduced (reported) |
| badass | 40.77287648278703 | 17.946222331387315 | line_window_computed |
| fantasy_agn | 102.33728271550177 | 21.180463692491845 | line_window_computed |
| gelato | 2.517967205637623 | 6.444395134420421 | global_reduced (reported) |
| gleam | 140.03497471617663 | 22.51900747 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 111 |  | 192 |  |
| OII3727 | total |  |  |  |  | 124 |
| Hb4861 | broad | 2.7e+03 | 963 | 1.89e+03 | 1.95e+03 | 523 |
| Hb4861 | narrow |  | 513 | 262 | 203 | 44 |
| Hb4861 | total |  | 1.76e+03 |  |  |  |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 178 | 195 | 293 | 182 |  |
| OIII4959 | outflow | 141 |  |  |  |  |
| OIII4959 | total |  | 308 |  |  | 264 |
| OIII5007 | broad |  | 0 |  |  |  |
| OIII5007 | narrow | 545 | 587 | 888 | 546 |  |
| OIII5007 | outflow | 433 |  |  |  |  |
| OIII5007 | total |  | 928 |  |  | 792 |
| Ha6563 | broad | 7.6e+03 | 3.59e+03 | 7.28e+03 | 8.16e+03 |  |
| Ha6563 | narrow | 1.1e+03 | 969 | 763 | 1.23e+03 |  |
| Ha6563 | total |  | 7.47e+03 |  |  | 3.68e+03 |
| NII6585 | narrow | 851 | 0 | 74.9 | 203 |  |
| NII6585 | total |  |  |  |  | 89.5 |
| SII6718 | narrow | 0.0391 | 17.5 |  | 154 |  |
| SII6718 | total |  |  |  |  | 68.4 |
| SII6732 | narrow | 202 | 0 |  | 109 |  |
| SII6732 | total |  |  |  |  | 31.1 |

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
| pyqsofit | 99.12430740418795 | 0.38174923991115733 | line_complex_reduced (reported) |
| badass | 32.90932159287843 | 21.11372272115262 | line_window_computed |
| fantasy_agn | 165.66788291953583 | 56.219384487484035 | line_window_computed |
| gelato | 1.9176211594444164 | 6.595611511688038 | global_reduced (reported) |
| gleam | 23.805160913502043 | 35.99569704428571 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 415 |  | 407 |  |
| OII3727 | total |  |  |  |  | 379 |
| Hb4861 | broad | 1.97e+03 | 0 | 1.01e+03 | 1.12e+03 | 197 |
| Hb4861 | narrow |  | 601 | 160 | 172 | 140 |
| Hb4861 | total |  | 936 |  |  |  |
| OIII4959 | broad |  | 9.84 |  |  |  |
| OIII4959 | narrow | 381 | 380 | 398 | 366 |  |
| OIII4959 | outflow | 59.5 |  |  |  |  |
| OIII4959 | total |  | 390 |  |  | 410 |
| OIII5007 | broad |  | 29.6 |  |  |  |
| OIII5007 | narrow | 1.17e+03 | 1.14e+03 | 1.21e+03 | 1.1e+03 |  |
| OIII5007 | outflow | 182 |  |  |  |  |
| OIII5007 | total |  | 1.17e+03 |  |  | 1.23e+03 |
| Ha6563 | broad | 4.74e+03 | 0 | 4.52e+03 | 4.46e+03 |  |
| Ha6563 | narrow | 579 | 0 | 618 | 657 |  |
| Ha6563 | total |  | 0 |  |  | 982 |
| NII6585 | narrow | 174 | 661 | 191 | 177 |  |
| NII6585 | total |  |  |  |  | 357 |
| SII6718 | narrow | 166 | 0 |  | 184 |  |
| SII6718 | total |  |  |  |  | 162 |
| SII6732 | narrow | 150 | 47.5 |  | 160 |  |
| SII6732 | total |  |  |  |  | 143 |

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
| pyqsofit | 246.76164862849868 | 0.7763708644725396 | line_complex_reduced (reported) |
| badass | 19.08120702460722 | 16.28097493257583 | line_window_computed |
| fantasy_agn | 69.82759179837777 | 42.65602723518327 | line_window_computed |
| gelato | 1.3151841421812198 | 2.8277704482034385 | global_reduced (reported) |
| gleam | 36.35738196239399 | 25.74418603857143 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 112 |  | 109 |  |
| OII3727 | total |  |  |  |  | 105 |
| Hb4861 | broad | 412 | 34.9 | 210 | 153 | 38.7 |
| Hb4861 | narrow |  | 127 | 3.77 | 47.2 | 28.1 |
| Hb4861 | total |  | 230 |  |  |  |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 84.7 | 133 | 140 | 78.3 |  |
| OIII4959 | outflow | 59.5 |  |  |  |  |
| OIII4959 | total |  | 133 |  |  | 139 |
| OIII5007 | broad |  | 0 |  |  |  |
| OIII5007 | narrow | 259 | 399 | 423 | 235 |  |
| OIII5007 | outflow | 182 |  |  |  |  |
| OIII5007 | total |  | 399 |  |  | 417 |
| Ha6563 | broad | 1.18e+03 | 387 | 1.23e+03 | 1.14e+03 |  |
| Ha6563 | narrow | 222 | 374 | 0 | 276 |  |
| Ha6563 | total |  | 1.63e+03 |  |  | 416 |
| NII6585 | narrow | 195 | 0.0179 | 131 | 214 |  |
| NII6585 | total |  |  |  |  | 296 |
| SII6718 | narrow | 61.8 | 27.9 |  | 73.6 |  |
| SII6718 | total |  |  |  |  | 57.2 |
| SII6732 | narrow | 55 | 0 |  | 61.3 |  |
| SII6732 | total |  |  |  |  | 57.9 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/06872228427/fit.log), [output.fits](pyqsofit/06872228427/output.fits), [pyqsofit_model.csv](pyqsofit/06872228427/pyqsofit_model.csv), [qsopar.fits](pyqsofit/06872228427/qsopar.fits), [result.pdf](pyqsofit/06872228427/result.pdf), [spectrum.fits](pyqsofit/06872228427/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/06872228427/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/06872228427/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/06872228427/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/06872228427/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/06872228427/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/06872228427/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/06872228427/2-onur/my_sdss.fits), [docker.log](badass/06872228427/docker.log), [fit.log](badass/06872228427/fit.log), [main.py](badass/06872228427/main.py), [spectrum.pdf](badass/06872228427/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/06872228427/balmer.csv), [broad.csv](fantasy_agn/06872228427/broad.csv), [coronal.csv](fantasy_agn/06872228427/coronal.csv), [docker.log](fantasy_agn/06872228427/docker.log), [feII_forbidden.csv](fantasy_agn/06872228427/feII_forbidden.csv), [feII_model.csv](fantasy_agn/06872228427/feII_model.csv), [feii_IZw1.csv](fantasy_agn/06872228427/feii_IZw1.csv), [fit.log](fantasy_agn/06872228427/fit.log), [helium.csv](fantasy_agn/06872228427/helium.csv), [hydrogen.csv](fantasy_agn/06872228427/hydrogen.csv), [my_sdss.pdf](fantasy_agn/06872228427/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/06872228427/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/06872228427/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/06872228427/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/06872228427/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/06872228427/oiii_nii.csv), [uvfe.csv](fantasy_agn/06872228427/uvfe.csv)
- `gelato`: [docker.log](gelato/06872228427/docker.log), [my_sdss-comp.pdf](gelato/06872228427/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/06872228427/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/06872228427/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/06872228427/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/06872228427/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/06872228427/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.png)
