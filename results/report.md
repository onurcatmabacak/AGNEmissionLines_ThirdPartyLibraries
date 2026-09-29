# Cross-tool AGN emission-line comparison

## Object `04545183216`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 278.6809153386391 | 2.5089438366305528 | line_complex_reduced (reported) |
| badass | 3.5939900213578215 | 1.4900484356642798 | line_window_computed |
| fantasy_agn | 256.4902847149535 | 3.2769352392817566 | line_window_computed |
| gelato | 41.073455576251 | 29.572015759348766 | global_reduced (reported) |
| gleam | 443.0882956544116 | 3.2949559907142856 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 30.8 |  | 137 |  |
| OII3727 | total |  |  |  |  | 35.5 |
| Hb4861 | broad | 2.28e+03 | 1.32e+03 | 2.53e+03 |  |  |
| Hb4861 | narrow |  | 187 | 62.3 | 669 |  |
| Hb4861 | total |  | 1.61e+03 |  |  | 288 |
| OIII4959 | broad |  | 0 | 48.4 |  |  |
| OIII4959 | narrow | 45.7 | 35.3 | 41.8 | -11.3 |  |
| OIII4959 | outflow | 44.3 |  |  |  |  |
| OIII4959 | total |  | 55.6 |  |  | 47.9 |
| OIII5007 | broad |  | 0 | 146 |  |  |
| OIII5007 | narrow | 140 | 106 | 127 | -33.9 |  |
| OIII5007 | outflow | 136 |  |  |  |  |
| OIII5007 | total |  | 167 |  |  | 144 |
| Ha6563 | broad | 1.29e+04 | 0 | 1.07e+04 |  |  |
| Ha6563 | narrow | 435 | 791 | 265 | 2.3e+03 |  |
| Ha6563 | total |  | 5.82e+03 |  |  | 183 |
| NII6585 | narrow | 9.3 | 134 | 0 | 1.99e+03 |  |
| SII6718 | narrow | 16.2 | 0.0277 |  | 109 |  |
| SII6732 | narrow | 51.9 | 0 |  | -83.8 |  |

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
| pyqsofit | 121.41416556472304 | 2.818411324920504 | line_complex_reduced (reported) |
| badass | 9.183909243788545 | 4.264456439713385 | line_window_computed |
| fantasy_agn | 22.688161207676256 | 15.80323904510864 | line_window_computed |
| gelato | 2.537856418828333 | 11.506087159454037 | global_reduced (reported) |
| gleam | 140.5263320832684 | 3.54271628 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0.00972 |  |  |  |
| OII3727 | narrow |  | 0 |  | 74.1 |  |
| OII3727 | total |  |  |  |  | 58.2 |
| Hb4861 | broad | 1.58e+03 | 10.1 | 453 | 1.06e+03 |  |
| Hb4861 | narrow |  | 619 | 623 | 249 |  |
| Hb4861 | total |  | 978 |  |  | 796 |
| OIII4959 | broad |  | 0 | 20.1 |  |  |
| OIII4959 | narrow | 44.4 | 68 | 57.9 | 34.2 |  |
| OIII4959 | outflow | 43.6 |  |  |  |  |
| OIII4959 | total |  | 99.8 |  |  | 98.6 |
| OIII5007 | broad |  | 0 | 61 |  |  |
| OIII5007 | narrow | 136 | 200 | 175 | 103 |  |
| OIII5007 | outflow | 133 |  |  |  |  |
| OIII5007 | total |  | 300 |  |  | 296 |
| Ha6563 | broad | 4.65e+03 | 3.55e+03 | 2.58e+03 | 3.81e+03 | 3.61e+03 |
| Ha6563 | narrow | 858 | 0 | 1.2e+03 | 1.45e+03 | 828 |
| Ha6563 | total |  | 3.55e+03 |  |  |  |
| NII6585 | narrow | 503 | 59.7 | 123 | 379 |  |
| NII6585 | total |  |  |  |  | 176 |
| SII6718 | narrow | 29.6 | 10.5 |  | 97.5 |  |
| SII6718 | total |  |  |  |  | 49.9 |
| SII6732 | narrow | 48.9 | 0 |  | 41.7 |  |
| SII6732 | total |  |  |  |  | 26.2 |

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
| pyqsofit | 112.2448628287333 | 3.397246396491919 | line_complex_reduced (reported) |
| badass | 31.184540575180076 | 15.191785966227647 | line_window_computed |
| fantasy_agn | 114.5771802823041 | 16.175871154570416 | line_window_computed |
| gelato | 6.709913554364907 | 17.43981645660039 | global_reduced (reported) |
| gleam | 269.7407445020783 | 6.6731719925 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 229 |  |  |  |
| OII3727 | narrow |  | 0 |  | 344 |  |
| OII3727 | total |  |  |  |  | 87 |
| Hb4861 | broad | 5.78e+03 | 1.19e+03 | 2.3e+03 | 3.31e+03 | 2.79e+03 |
| Hb4861 | narrow |  | 1.6e+03 | 1.65e+03 | 777 | 200 |
| Hb4861 | total |  | 3.61e+03 |  |  |  |
| OIII4959 | broad |  | 0 | 39.8 |  |  |
| OIII4959 | narrow | 327 | 305 | 339 | 204 |  |
| OIII4959 | outflow | 136 |  |  |  |  |
| OIII4959 | total |  | 438 |  |  | 336 |
| OIII5007 | broad |  | 0 | 121 |  |  |
| OIII5007 | narrow | 1e+03 | 919 | 1.03e+03 | 612 |  |
| OIII5007 | outflow | 416 |  |  |  |  |
| OIII5007 | total |  | 1.32e+03 |  |  | 1.01e+03 |
| Ha6563 | broad | 1.48e+04 | 4.62e+03 | 7.61e+03 | 1.15e+04 | 1.11e+04 |
| Ha6563 | narrow | 1.78e+03 | 2.68e+03 | 3.29e+03 | 3.49e+03 | 1.16e+03 |
| Ha6563 | total |  | 1.29e+04 |  |  |  |
| NII6585 | narrow | 511 | 0 | 123 | 923 |  |
| NII6585 | total |  |  |  |  | 314 |
| SII6718 | narrow | 1.02 | 0 |  | 247 |  |
| SII6732 | narrow | 30.3 | 22.5 |  | 77.7 |  |

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
| pyqsofit | 89.85575990175737 | 3.2060501218488664 | line_complex_reduced (reported) |
| badass | 65.3705688558329 | 38.071377348954876 | line_window_computed |
| fantasy_agn | 62.05559847146493 | 43.98385847651698 | line_window_computed |
| gelato | 5.065963767369376 | 9.630919225798582 | global_reduced (reported) |
| gleam | 49.328798580946085 | 5.91851771 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0.528 |  |  |  |
| OII3727 | narrow |  | 105 |  | 150 |  |
| OII3727 | total |  |  |  |  | 125 |
| Hb4861 | broad | 1.67e+03 | 0 | 347 | 507 |  |
| Hb4861 | narrow |  | 327 | 295 | 120 |  |
| Hb4861 | total |  | 506 |  |  | 119 |
| OIII4959 | broad |  | 0 | 234 |  |  |
| OIII4959 | narrow | 149 | 207 | 7.39 | 122 |  |
| OIII4959 | outflow | 105 |  |  |  |  |
| OIII4959 | total |  | 300 |  |  | 220 |
| OIII5007 | broad |  | 0 | 709 |  |  |
| OIII5007 | narrow | 456 | 624 | 22.1 | 368 |  |
| OIII5007 | outflow | 320 |  |  |  |  |
| OIII5007 | total |  | 904 |  |  | 660 |
| Ha6563 | broad | 3.32e+03 | 319 | 1.51e+03 | 2.7e+03 | 2.4e+03 |
| Ha6563 | narrow | 510 | 954 | 878 | 666 | 421 |
| Ha6563 | total |  | 3.35e+03 |  |  |  |
| NII6585 | narrow | 401 | 0.0189 | 1.79e-11 | 586 |  |
| NII6585 | total |  |  |  |  | 351 |
| SII6718 | narrow | 90.9 | 0 |  | 117 |  |
| SII6718 | total |  |  |  |  | 89.9 |
| SII6732 | narrow | 61.9 | 22.1 |  | 77.2 |  |
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
| pyqsofit | 181.40671009536334 | 2.221567840861312 | line_complex_reduced (reported) |
| badass | 7.895678654323758 | 3.7393807744958245 | line_window_computed |
| fantasy_agn | 156.2339445345203 | 2.9039461986012602 | line_window_computed |
| gelato | 17.50561520381579 | 10.691382473480434 | global_reduced (reported) |
| gleam | 614.4643676682849 | 6.761781600588235 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 6.11 |  | 25.9 |  |
| OII3727 | total |  |  |  |  | 17.5 |
| Hb4861 | broad | 609 | 98.6 | 468 |  |  |
| Hb4861 | narrow |  | 266 | 231 | 379 |  |
| Hb4861 | total |  | 508 |  |  | 402 |
| OIII4959 | broad |  | 0 | 51.7 |  |  |
| OIII4959 | narrow | 2.79 | 30.6 | 3.5 | 25.7 |  |
| OIII4959 | outflow | 38.5 |  |  |  |  |
| OIII4959 | total |  | 47.9 |  |  |  |
| OIII5007 | broad |  | 0 | 157 |  |  |
| OIII5007 | narrow | 8.53 | 90.1 | 10.6 | 77.3 |  |
| OIII5007 | outflow | 118 |  |  |  |  |
| OIII5007 | total |  | 144 |  |  |  |
| Ha6563 | broad | 1.8e+03 | 0 | 1.36e+03 |  |  |
| Ha6563 | narrow | 762 | 480 | 435 | 1.21e+03 |  |
| Ha6563 | total |  | 1.35e+03 |  |  | 1.5e+03 |
| NII6585 | narrow | 93.9 | 0 | 0 | 286 |  |
| SII6718 | narrow | 14.2 | 0 |  | 14.9 |  |
| SII6732 | narrow | 0.0775 | 0 |  | -22 |  |

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
| pyqsofit | 165.34098132591689 | 3.02865776761992 | line_complex_reduced (reported) |
| badass | 20.51760636606131 | 7.649462925561983 | line_window_computed |
| fantasy_agn | 154.69331957539384 | 8.497564741856383 | line_window_computed |
| gelato | 3.497073192433206 | 7.9827052158699106 | global_reduced (reported) |
| gleam | 189.10566505570048 | 6.561451852857142 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0.0042 |  |  |  |
| OII3727 | narrow |  | 52.8 |  | 97.8 |  |
| OII3727 | total |  |  |  |  | 36.1 |
| Hb4861 | broad | 2.82e+03 | 429 | 1.21e+03 | 1.26e+03 | 628 |
| Hb4861 | narrow |  | 557 | 440 | 295 | 15.6 |
| Hb4861 | total |  | 1.29e+03 |  |  |  |
| OIII4959 | broad |  | 3.04 | 50.4 |  |  |
| OIII4959 | narrow | 92.5 | 84.1 | 58.5 | 48.8 |  |
| OIII4959 | outflow | 3.78 |  |  |  |  |
| OIII4959 | total |  | 136 |  |  | 93.7 |
| OIII5007 | broad |  | 9.13 | 153 |  |  |
| OIII5007 | narrow | 283 | 253 | 177 | 146 |  |
| OIII5007 | outflow | 11.6 |  |  |  |  |
| OIII5007 | total |  | 410 |  |  | 281 |
| Ha6563 | broad | 5.05e+03 | 926 | 3.71e+03 | 4.83e+03 |  |
| Ha6563 | narrow | 1.2e+03 | 1e+03 | 1.05e+03 | 1.46e+03 |  |
| Ha6563 | total |  | 4.64e+03 |  |  | 3.4e+03 |
| NII6585 | narrow | 371 | 0 | 45.9 | 141 |  |
| NII6585 | total |  |  |  |  | 58.8 |
| SII6718 | narrow | 2.75 | 13.1 |  | 93 |  |
| SII6718 | total |  |  |  |  | 29.3 |
| SII6732 | narrow | 53.9 | 3.59 |  | 67.2 |  |
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
| pyqsofit | 9.795454019755992 | 2.7863695553157113 | line_complex_reduced (reported) |
| badass | 14.722286725686796 | 7.145589367435795 | line_window_computed |
| fantasy_agn | 25.75347240236986 | 19.465591886671834 | line_window_computed |
| gelato | 4.204828307749551 | 8.068442809724317 | global_reduced (reported) |
| gleam | 58.30209087188553 | 4.241710693333333 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 221 |  |  |  |
| OII3727 | narrow |  | 67.8 |  | 181 |  |
| OII3727 | total |  |  |  |  | 62.4 |
| Hb4861 | broad | 4.08e+03 | 465 | 1.03e+03 | 1.65e+03 |  |
| Hb4861 | narrow |  | 861 | 844 | 406 |  |
| Hb4861 | total |  | 1.8e+03 |  |  | 1.06e+03 |
| OIII4959 | broad |  | 0 | 124 |  |  |
| OIII4959 | narrow | 107 | 101 | 0 | 89.9 |  |
| OIII4959 | outflow | 4.53 |  |  |  |  |
| OIII4959 | total |  | 160 |  |  | 107 |
| OIII5007 | broad |  | 0 | 377 |  |  |
| OIII5007 | narrow | 327 | 304 | 0 | 270 |  |
| OIII5007 | outflow | 13.9 |  |  |  |  |
| OIII5007 | total |  | 481 |  |  | 322 |
| Ha6563 | broad | 5.94e+03 | 627 | 3.52e+03 | 5.25e+03 | 4.44e+03 |
| Ha6563 | narrow | 1.06e+03 | 1.39e+03 | 1.39e+03 | 1.67e+03 | 328 |
| Ha6563 | total |  | 6.18e+03 |  |  |  |
| NII6585 | narrow | 846 | 0 | 45.5 | 479 |  |
| NII6585 | total |  |  |  |  | 232 |
| SII6718 | narrow | 11.7 | 23.2 |  | 92.3 |  |
| SII6718 | total |  |  |  |  | 43.9 |
| SII6732 | narrow | 67.2 | 0.00192 |  | 63.9 |  |
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
| pyqsofit | 108.6700012126676 | 5.832820998493082 | line_complex_reduced (reported) |
| badass | 9.657246150902445 | 4.036961824240215 | line_window_computed |
| fantasy_agn | 105.72308423629345 | 12.75071890489186 | line_window_computed |
| gelato | 2.523086729207244 | 6.4509944831035835 | global_reduced (reported) |
| gleam | 143.85604230430886 | 8.590674842000002 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 120 |  | 190 |  |
| OII3727 | total |  |  |  |  | 124 |
| Hb4861 | broad | 2.99e+03 | 0 | 1.95e+03 | 1.95e+03 | 523 |
| Hb4861 | narrow |  | 784 | 333 | 204 | 44 |
| Hb4861 | total |  | 1.31e+03 |  |  |  |
| OIII4959 | broad |  | 129 | 77.4 |  |  |
| OIII4959 | narrow | 252 | 196 | 233 | 183 |  |
| OIII4959 | outflow | 0.441 |  |  |  |  |
| OIII4959 | total |  | 325 |  |  | 264 |
| OIII5007 | broad |  | 386 | 234 |  |  |
| OIII5007 | narrow | 772 | 591 | 705 | 549 |  |
| OIII5007 | outflow | 1.35 |  |  |  |  |
| OIII5007 | total |  | 977 |  |  | 792 |
| Ha6563 | broad | 7.6e+03 | 3.21e+03 | 6.85e+03 | 8.16e+03 | 3.78e+03 |
| Ha6563 | narrow | 1.1e+03 | 922 | 883 | 1.23e+03 | 247 |
| Ha6563 | total |  | 7.29e+03 |  |  |  |
| NII6585 | narrow | 851 | 0 | 123 | 202 |  |
| NII6585 | total |  |  |  |  | 129 |
| SII6718 | narrow | 0.119 | 0 |  | 156 |  |
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
| pyqsofit | 82.80904659952367 | 2.4471208183477144 | line_complex_reduced (reported) |
| badass | 180.3884093548456 | 110.58145130820799 | line_window_computed |
| fantasy_agn | 157.7659718988859 | 61.790914902285394 | line_window_computed |
| gelato | 1.9120004941918498 | 6.602820513454798 | global_reduced (reported) |
| gleam | 26.004532251587513 | 4.189678322 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 152 |  |  |  |
| OII3727 | narrow |  | 343 |  | 407 |  |
| OII3727 | total |  |  |  |  | 379 |
| Hb4861 | broad | 2.46e+03 | 338 | 935 | 1.12e+03 | 182 |
| Hb4861 | narrow |  | 574 | 187 | 171 | 145 |
| Hb4861 | total |  | 1.23e+03 |  |  |  |
| OIII4959 | broad |  | 0 | 145 |  |  |
| OIII4959 | narrow | 373 | 360 | 267 | 366 |  |
| OIII4959 | outflow | 59.6 |  |  |  |  |
| OIII4959 | total |  | 570 |  |  | 410 |
| OIII5007 | broad |  | 0 | 438 |  |  |
| OIII5007 | narrow | 1.14e+03 | 1.08e+03 | 808 | 1.1e+03 |  |
| OIII5007 | outflow | 182 |  |  |  |  |
| OIII5007 | total |  | 1.71e+03 |  |  | 1.23e+03 |
| Ha6563 | broad | 4.74e+03 | 1.23e+03 | 4.3e+03 | 4.46e+03 | 1.78e+03 |
| Ha6563 | narrow | 582 | 769 | 448 | 655 | 533 |
| Ha6563 | total |  | 4.31e+03 |  |  |  |
| NII6585 | narrow | 174 | 109 | 173 | 177 |  |
| NII6585 | total |  |  |  |  | 167 |
| SII6718 | narrow | 166 | 27.1 |  | 184 |  |
| SII6718 | total |  |  |  |  | 162 |
| SII6732 | narrow | 150 | 50.5 |  | 160 |  |
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
| pyqsofit | 251.70827559317084 | 2.5034158444589947 | line_complex_reduced (reported) |
| badass | 19.79976621535167 | 16.502046578481874 | line_window_computed |
| fantasy_agn | 63.41571392438628 | 42.73866693449478 | line_window_computed |
| gelato | 1.3041292525746846 | 2.8352847321365275 | global_reduced (reported) |
| gleam | 47.824954934559706 | 3.705399648 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 112 |  | 109 |  |
| OII3727 | total |  |  |  |  | 105 |
| Hb4861 | broad | 672 | 21.7 | 315 | 153 | 44.4 |
| Hb4861 | narrow |  | 131 | 33.9 | 47 | 33.7 |
| Hb4861 | total |  | 224 |  |  |  |
| OIII4959 | broad |  | 16 | 148 |  |  |
| OIII4959 | narrow | 137 | 129 | 0 | 78.6 |  |
| OIII4959 | outflow | 1.73 |  |  |  |  |
| OIII4959 | total |  | 145 |  |  | 139 |
| OIII5007 | broad |  | 48 | 448 |  |  |
| OIII5007 | narrow | 420 | 389 | 0 | 236 |  |
| OIII5007 | outflow | 5.28 |  |  |  |  |
| OIII5007 | total |  | 437 |  |  | 417 |
| Ha6563 | broad | 1.12e+03 | 170 | 505 | 1.14e+03 | 723 |
| Ha6563 | narrow | 223 | 382 | 148 | 276 | 228 |
| Ha6563 | total |  | 1.58e+03 |  |  |  |
| NII6585 | narrow | 198 | 0 | 261 | 214 |  |
| NII6585 | total |  |  |  |  | 212 |
| SII6718 | narrow | 62 | 11.3 |  | 73.4 |  |
| SII6718 | total |  |  |  |  | 60.9 |
| SII6732 | narrow | 54.6 | 14.8 |  | 61.3 |  |
| SII6732 | total |  |  |  |  | 52.7 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/06872228427/fit.log), [output.fits](pyqsofit/06872228427/output.fits), [pyqsofit_model.csv](pyqsofit/06872228427/pyqsofit_model.csv), [qsopar.fits](pyqsofit/06872228427/qsopar.fits), [result.pdf](pyqsofit/06872228427/result.pdf), [spectrum.fits](pyqsofit/06872228427/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/06872228427/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/06872228427/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/06872228427/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/06872228427/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/06872228427/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/06872228427/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/06872228427/2-onur/my_sdss.fits), [docker.log](badass/06872228427/docker.log), [fit.log](badass/06872228427/fit.log), [main.py](badass/06872228427/main.py), [spectrum.pdf](badass/06872228427/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/06872228427/balmer.csv), [broad.csv](fantasy_agn/06872228427/broad.csv), [coronal.csv](fantasy_agn/06872228427/coronal.csv), [docker.log](fantasy_agn/06872228427/docker.log), [feII_forbidden.csv](fantasy_agn/06872228427/feII_forbidden.csv), [feII_model.csv](fantasy_agn/06872228427/feII_model.csv), [feii_IZw1.csv](fantasy_agn/06872228427/feii_IZw1.csv), [fit.log](fantasy_agn/06872228427/fit.log), [helium.csv](fantasy_agn/06872228427/helium.csv), [hydrogen.csv](fantasy_agn/06872228427/hydrogen.csv), [my_sdss.pdf](fantasy_agn/06872228427/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/06872228427/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/06872228427/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/06872228427/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/06872228427/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/06872228427/oiii_nii.csv), [uvfe.csv](fantasy_agn/06872228427/uvfe.csv)
- `gelato`: [docker.log](gelato/06872228427/docker.log), [my_sdss-comp.pdf](gelato/06872228427/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/06872228427/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/06872228427/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/06872228427/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/06872228427/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/06872228427/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.png)
