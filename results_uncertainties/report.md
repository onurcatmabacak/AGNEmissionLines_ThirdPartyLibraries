# Cross-tool AGN emission-line comparison

## Object `04545183216`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 278.21364281015883 | 2.9624865023489892 | line_complex_reduced (reported) |
| badass | 3.8105267908081424 | 1.587791466952446 | line_window_computed |
| fantasy_agn | 250.3765052779885 | 8.639200094881273 | line_window_computed |
| gelato | 41.73740538848138 | 29.063670808916054 | global_reduced (reported) |
| gleam | 802.619735275447 | 25.89464366055556 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 24.9 |  |  |  |
| OII3727 | narrow |  | 0 |  | 135 | 51.2 |
| Hb4861 | broad | 2.29e+03 | 1.74e+03 | 2.48e+03 | 483 |  |
| Hb4861 | narrow |  | 0 | 0.181 |  |  |
| Hb4861 | outflow |  | 1.74e+03 |  |  |  |
| OIII4959 | broad |  | 0 | 26.2 |  |  |
| OIII4959 | narrow | 40.5 | 34.3 | 73.1 | 34.6 | 37.2 |
| OIII4959 | outflow | 65.2 | 53.7 |  |  |  |
| OIII5007 | broad |  | 0 | 79.5 |  |  |
| OIII5007 | narrow | 125 | 103 | 220 | 99 | 112 |
| OIII5007 | outflow | 201 | 162 |  |  |  |
| Ha6563 | broad | 1.26e+04 | 0 | 6.94e+03 | 2.29e+03 |  |
| Ha6563 | narrow | 398 | 960 | 206 |  |  |
| Ha6563 | outflow |  | 7.2e+03 |  |  |  |
| NII6585 | narrow | 1.29 |  | 357 | 2.27e+03 |  |
| SII6718 | narrow | 24.7 |  |  | 113 |  |
| SII6732 | narrow | 24.8 |  |  | -70.5 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04545183216/fit.log), [output.fits](pyqsofit/04545183216/output.fits), [pyqsofit_model.csv](pyqsofit/04545183216/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04545183216/qsopar.fits), [result.pdf](pyqsofit/04545183216/result.pdf), [spectrum.fits](pyqsofit/04545183216/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04545183216/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04545183216/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04545183216/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04545183216/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04545183216/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04545183216/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04545183216/2-onur/my_sdss.fits), [docker.log](badass/04545183216/docker.log), [fit.log](badass/04545183216/fit.log), [main.py](badass/04545183216/main.py), [spectrum.pdf](badass/04545183216/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04545183216/balmer.csv), [broad.csv](fantasy_agn/04545183216/broad.csv), [coronal.csv](fantasy_agn/04545183216/coronal.csv), [feII_forbidden.csv](fantasy_agn/04545183216/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04545183216/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04545183216/feii_IZw1.csv), [fit.log](fantasy_agn/04545183216/fit.log), [helium.csv](fantasy_agn/04545183216/helium.csv), [hydrogen.csv](fantasy_agn/04545183216/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04545183216/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04545183216/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04545183216/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04545183216/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04545183216/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04545183216/oiii_nii.csv), [uvfe.csv](fantasy_agn/04545183216/uvfe.csv)
- `gelato`: [docker.log](gelato/04545183216/docker.log), [my_sdss-comp.pdf](gelato/04545183216/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04545183216/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04545183216/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04545183216/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04545183216/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04545183216/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.png)

## Object `04570362657`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 119.94536845836443 | 5.611980523029315 | line_complex_reduced (reported) |
| badass | nan | nan | global_reduced (reported) |
| fantasy_agn | 112.67838753905424 | 9.445062951688888 | line_window_computed |
| gelato | 12.852400826783628 | 14.220320144358517 | global_reduced (reported) |
| gleam | 153.68541602697627 | 4.946040602999999 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  |  |  | 73.5 | 67.3 |
| Hb4861 | broad | 1.54e+03 |  | 1.14e+03 | -53.5 |  |
| Hb4861 | narrow |  |  | 298 |  | 1.04e+03 |
| OIII4959 | broad |  |  | 80.1 |  |  |
| OIII4959 | narrow | 69 |  | 15.7 | 122 | 79.2 |
| OIII4959 | outflow | 17.8 |  |  |  |  |
| OIII5007 | broad |  |  | 243 |  |  |
| OIII5007 | narrow | 212 |  | 46.6 | 348 | 238 |
| OIII5007 | outflow | 54.8 |  |  |  |  |
| Ha6563 | broad | 5.42e+03 |  | 3.82e+03 | 1.46e+03 |  |
| Ha6563 | narrow | 769 |  | 880 |  | 4.46e+03 |
| NII6585 | narrow | 0.625 |  | 0.00179 | 1.02e+03 |  |
| SII6718 | narrow | 24.8 |  |  | 76.9 | 37.9 |
| SII6732 | narrow | 24.9 |  |  | 61.9 | 22.3 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04570362657/fit.log), [output.fits](pyqsofit/04570362657/output.fits), [pyqsofit_model.csv](pyqsofit/04570362657/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04570362657/qsopar.fits), [result.pdf](pyqsofit/04570362657/result.pdf), [spectrum.fits](pyqsofit/04570362657/spectrum.fits)
- `badass`: [docker.log](badass/04570362657/docker.log), [fit.log](badass/04570362657/fit.log), [spectrum.pdf](badass/04570362657/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04570362657/balmer.csv), [broad.csv](fantasy_agn/04570362657/broad.csv), [coronal.csv](fantasy_agn/04570362657/coronal.csv), [feII_forbidden.csv](fantasy_agn/04570362657/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04570362657/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04570362657/feii_IZw1.csv), [fit.log](fantasy_agn/04570362657/fit.log), [helium.csv](fantasy_agn/04570362657/helium.csv), [hydrogen.csv](fantasy_agn/04570362657/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04570362657/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04570362657/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04570362657/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04570362657/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04570362657/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04570362657/oiii_nii.csv), [uvfe.csv](fantasy_agn/04570362657/uvfe.csv)
- `gelato`: [docker.log](gelato/04570362657/docker.log), [my_sdss-comp.pdf](gelato/04570362657/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04570362657/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04570362657/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04570362657/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04570362657/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04570362657/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.png)

## Object `04570493016`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 101.23646516672395 | 12.606820476384971 | line_complex_reduced (reported) |
| badass | 32.2001306814038 | 15.567932248080906 | line_window_computed |
| fantasy_agn | 89.65534574888395 | 73.56913164858604 | line_window_computed |
| gelato | 89.26734881727724 | 42.41905274215345 | global_reduced (reported) |
| gleam | 443.2242468404478 | 37.008706810769226 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 72 |  |  |  |
| OII3727 | narrow |  | 81.2 |  | 332 | 90.3 |
| Hb4861 | broad | 6.52e+03 | 1.23e+03 | 2.99e+03 | 849 | 329 |
| Hb4861 | narrow |  | 1.59e+03 | 1.08e+03 |  | 3e+03 |
| Hb4861 | outflow |  | 3.65e+03 |  |  |  |
| OIII4959 | broad |  | 0 | 205 |  |  |
| OIII4959 | narrow | 297 | 284 | 134 | 296 | 184 |
| OIII4959 | outflow | 23.5 | 432 |  |  |  |
| OIII5007 | broad |  | 0 | 622 |  |  |
| OIII5007 | narrow | 913 | 856 | 403 | 847 |  |
| OIII5007 | outflow | 72.5 | 1.3e+03 |  |  |  |
| Ha6563 | broad | 1.58e+04 | 4.54e+03 | 6.95e+03 | 5.57e+03 |  |
| Ha6563 | narrow | 1.41e+03 | 2.68e+03 | 449 |  | 1.23e+04 |
| Ha6563 | outflow |  | 1.29e+04 |  |  |  |
| NII6585 | narrow | 7.42 |  | 686 | 5.29e+03 |  |
| SII6718 | narrow | 10.2 |  |  | 233 |  |
| SII6732 | narrow | 10.2 |  |  | 43.6 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04570493016/fit.log), [output.fits](pyqsofit/04570493016/output.fits), [pyqsofit_model.csv](pyqsofit/04570493016/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04570493016/qsopar.fits), [result.pdf](pyqsofit/04570493016/result.pdf), [spectrum.fits](pyqsofit/04570493016/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04570493016/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04570493016/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04570493016/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04570493016/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04570493016/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04570493016/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04570493016/2-onur/my_sdss.fits), [docker.log](badass/04570493016/docker.log), [fit.log](badass/04570493016/fit.log), [main.py](badass/04570493016/main.py), [spectrum.pdf](badass/04570493016/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04570493016/balmer.csv), [broad.csv](fantasy_agn/04570493016/broad.csv), [coronal.csv](fantasy_agn/04570493016/coronal.csv), [feII_forbidden.csv](fantasy_agn/04570493016/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04570493016/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04570493016/feii_IZw1.csv), [fit.log](fantasy_agn/04570493016/fit.log), [helium.csv](fantasy_agn/04570493016/helium.csv), [hydrogen.csv](fantasy_agn/04570493016/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04570493016/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04570493016/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04570493016/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04570493016/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04570493016/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04570493016/oiii_nii.csv), [uvfe.csv](fantasy_agn/04570493016/uvfe.csv)
- `gelato`: [docker.log](gelato/04570493016/docker.log), [my_sdss-comp.pdf](gelato/04570493016/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04570493016/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04570493016/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04570493016/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04570493016/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04570493016/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.png)

## Object `04592503068`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 59.53848931871266 | 20.458319343970167 | line_complex_reduced (reported) |
| badass | 22.29405683376105 | 10.843592707204845 | line_window_computed |
| fantasy_agn | 56.24755293173986 | 47.6333701127223 | line_window_computed |
| gelato | 27.90915186660648 | 14.550687890427291 | global_reduced (reported) |
| gleam | 63.271328751907475 | 3.434542163333333 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 89.3 |  | 144 | 126 |
| Hb4861 | broad | 1.33e+03 | 92.2 | 698 | 101 |  |
| Hb4861 | narrow |  | 288 | 93.2 |  | 170 |
| Hb4861 | outflow |  | 537 |  |  |  |
| OIII4959 | broad |  | 51.2 | 205 |  |  |
| OIII4959 | narrow | 125 | 189 | 2.66e-14 | 172 | 220 |
| OIII4959 | outflow | 68.9 | 240 |  |  |  |
| OIII5007 | broad |  | 154 | 622 |  |  |
| OIII5007 | narrow | 385 | 568 | 3.26e-15 | 490 | 661 |
| OIII5007 | outflow | 212 | 722 |  |  |  |
| Ha6563 | broad | 3.63e+03 | 0 | 2.55e+03 | 1.19e+03 | 368 |
| Ha6563 | narrow | 396 | 946 | 533 |  | 2.74e+03 |
| Ha6563 | outflow |  | 3.16e+03 |  |  |  |
| NII6585 | narrow | 1.23 |  | 0 | 1.45e+03 | 333 |
| SII6718 | narrow | 66.2 |  |  | 112 | 85.3 |
| SII6732 | narrow | 66.4 |  |  | 75.2 | 50.9 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592503068/fit.log), [output.fits](pyqsofit/04592503068/output.fits), [pyqsofit_model.csv](pyqsofit/04592503068/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592503068/qsopar.fits), [result.pdf](pyqsofit/04592503068/result.pdf), [spectrum.fits](pyqsofit/04592503068/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592503068/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592503068/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592503068/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592503068/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592503068/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592503068/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592503068/2-onur/my_sdss.fits), [docker.log](badass/04592503068/docker.log), [fit.log](badass/04592503068/fit.log), [main.py](badass/04592503068/main.py), [spectrum.pdf](badass/04592503068/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592503068/balmer.csv), [broad.csv](fantasy_agn/04592503068/broad.csv), [coronal.csv](fantasy_agn/04592503068/coronal.csv), [feII_forbidden.csv](fantasy_agn/04592503068/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592503068/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592503068/feii_IZw1.csv), [fit.log](fantasy_agn/04592503068/fit.log), [helium.csv](fantasy_agn/04592503068/helium.csv), [hydrogen.csv](fantasy_agn/04592503068/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592503068/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592503068/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592503068/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592503068/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592503068/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592503068/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592503068/uvfe.csv)
- `gelato`: [docker.log](gelato/04592503068/docker.log), [my_sdss-comp.pdf](gelato/04592503068/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592503068/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592503068/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592503068/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592503068/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592503068/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.png)

## Object `04592517882`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 154.74028259125458 | 10.955323972157792 | line_complex_reduced (reported) |
| badass | nan | nan | global_reduced (reported) |
| fantasy_agn | 155.74860904000886 | 2.711310385815121 | line_window_computed |
| gelato | 21.201351695894726 | 11.385344115732321 | global_reduced (reported) |
| gleam | 833.6591638170344 | 2.7666911217647057 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  |  |  | 24.9 |  |
| Hb4861 | broad | 563 |  | 494 | 195 |  |
| Hb4861 | narrow |  |  | 207 |  | 384 |
| OIII4959 | broad |  |  | 50.9 |  |  |
| OIII4959 | narrow | 1.39 |  | 3.1 | 30.2 |  |
| OIII4959 | outflow | 0.376 |  |  |  |  |
| OIII5007 | broad |  |  | 154 |  |  |
| OIII5007 | narrow | 4.27 |  | 9.38 | 86.2 |  |
| OIII5007 | outflow | 1.16 |  |  |  |  |
| Ha6563 | broad | 2.21e+03 |  | 1.4e+03 | 1.2e+03 |  |
| Ha6563 | narrow | 776 |  | 423 |  | 1.57e+03 |
| NII6585 | narrow | 0.0636 |  | 0 | 369 |  |
| SII6718 | narrow | 0.433 |  |  | 13 |  |
| SII6732 | narrow | 0.434 |  |  | -22.5 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592517882/fit.log), [output.fits](pyqsofit/04592517882/output.fits), [pyqsofit_model.csv](pyqsofit/04592517882/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592517882/qsopar.fits), [result.pdf](pyqsofit/04592517882/result.pdf), [spectrum.fits](pyqsofit/04592517882/spectrum.fits)
- `badass`: [docker.log](badass/04592517882/docker.log), [fit.log](badass/04592517882/fit.log), [spectrum.pdf](badass/04592517882/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592517882/balmer.csv), [broad.csv](fantasy_agn/04592517882/broad.csv), [coronal.csv](fantasy_agn/04592517882/coronal.csv), [feII_forbidden.csv](fantasy_agn/04592517882/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592517882/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592517882/feii_IZw1.csv), [fit.log](fantasy_agn/04592517882/fit.log), [helium.csv](fantasy_agn/04592517882/helium.csv), [hydrogen.csv](fantasy_agn/04592517882/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592517882/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592517882/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592517882/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592517882/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592517882/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592517882/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592517882/uvfe.csv)
- `gelato`: [docker.log](gelato/04592517882/docker.log), [my_sdss-comp.pdf](gelato/04592517882/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592517882/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592517882/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592517882/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592517882/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592517882/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.png)

## Object `04592660180`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 167.76007733661316 | 4.719470396035726 | line_complex_reduced (reported) |
| badass | 15.86588222652833 | 5.8521717480850555 | line_window_computed |
| fantasy_agn | 151.54963533261764 | 10.699193873938563 | line_window_computed |
| gelato | 51.450752450549736 | 24.695558628823882 | global_reduced (reported) |
| gleam | 247.9380459514825 | 5.710792839 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 0 |  | 89.2 | 42.8 |
| Hb4861 | broad | 2.8e+03 | 363 | 1.31e+03 | 370 | 244 |
| Hb4861 | narrow |  | 579 | 323 |  | 1.09e+03 |
| Hb4861 | outflow |  | 1.31e+03 |  |  |  |
| OIII4959 | broad |  | 0 | 26 |  |  |
| OIII4959 | narrow | 80.2 | 75.1 | 94.7 | 69.1 | 86.4 |
| OIII4959 | outflow | 33.4 | 118 |  |  |  |
| OIII5007 | broad |  | 0 | 78.7 |  |  |
| OIII5007 | narrow | 247 | 226 | 287 | 197 | 259 |
| OIII5007 | outflow | 103 | 356 |  |  |  |
| Ha6563 | broad | 5.67e+03 | 1.08e+03 | 4.26e+03 | 2.07e+03 |  |
| Ha6563 | narrow | 1.07e+03 | 1.01e+03 | 864 |  | 3.99e+03 |
| Ha6563 | outflow |  | 4.65e+03 |  |  |  |
| NII6585 | narrow | 5.63 |  | 109 | 1.79e+03 |  |
| SII6718 | narrow | 23.4 |  |  | 65.4 | 20.5 |
| SII6732 | narrow | 23.5 |  |  | 66 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592660180/fit.log), [output.fits](pyqsofit/04592660180/output.fits), [pyqsofit_model.csv](pyqsofit/04592660180/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592660180/qsopar.fits), [result.pdf](pyqsofit/04592660180/result.pdf), [spectrum.fits](pyqsofit/04592660180/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592660180/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592660180/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592660180/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592660180/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592660180/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592660180/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592660180/2-onur/my_sdss.fits), [docker.log](badass/04592660180/docker.log), [fit.log](badass/04592660180/fit.log), [main.py](badass/04592660180/main.py), [spectrum.pdf](badass/04592660180/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592660180/balmer.csv), [broad.csv](fantasy_agn/04592660180/broad.csv), [coronal.csv](fantasy_agn/04592660180/coronal.csv), [feII_forbidden.csv](fantasy_agn/04592660180/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592660180/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592660180/feii_IZw1.csv), [fit.log](fantasy_agn/04592660180/fit.log), [helium.csv](fantasy_agn/04592660180/helium.csv), [hydrogen.csv](fantasy_agn/04592660180/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592660180/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592660180/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592660180/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592660180/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592660180/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592660180/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592660180/uvfe.csv)
- `gelato`: [docker.log](gelato/04592660180/docker.log), [my_sdss-comp.pdf](gelato/04592660180/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592660180/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592660180/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592660180/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592660180/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592660180/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.png)

## Object `04592939295`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 35.9616224810953 | 6.14800639915693 | line_complex_reduced (reported) |
| badass | 12.723764920983706 | 6.15203858524364 | line_window_computed |
| fantasy_agn | 37.37260405845741 | 14.880302236005264 | line_window_computed |
| gelato | 45.66968474939139 | 21.343489696339148 | global_reduced (reported) |
| gleam | 108.70917487329908 | 5.476127938571429 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 142 |  | 170 | 68.8 |
| Hb4861 | broad | 4.35e+03 | 673 | 1.68e+03 | 412 |  |
| Hb4861 | narrow |  | 813 | 462 |  | 1.36e+03 |
| Hb4861 | outflow |  | 1.91e+03 |  |  |  |
| OIII4959 | broad |  | 0 | 123 |  |  |
| OIII4959 | narrow | 70.5 | 109 | 16.8 | 74.7 | 101 |
| OIII4959 | outflow | 52.8 | 161 |  |  |  |
| OIII5007 | broad |  | 0 | 373 |  |  |
| OIII5007 | narrow | 217 | 327 | 50.4 | 213 | 302 |
| OIII5007 | outflow | 162 | 483 |  |  |  |
| Ha6563 | broad | 7.23e+03 | 5.56e+03 | 5.01e+03 | 2.06e+03 | 288 |
| Ha6563 | narrow | 4.27 | 0 | 802 |  | 5.01e+03 |
| Ha6563 | outflow |  | 5.56e+03 |  |  |  |
| NII6585 | narrow | 745 |  | 186 | 2.57e+03 | 183 |
| SII6718 | narrow | 0.0686 |  |  | 113 | 28.4 |
| SII6732 | narrow | 0.0688 |  |  | 70.1 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592939295/fit.log), [output.fits](pyqsofit/04592939295/output.fits), [pyqsofit_model.csv](pyqsofit/04592939295/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592939295/qsopar.fits), [result.pdf](pyqsofit/04592939295/result.pdf), [spectrum.fits](pyqsofit/04592939295/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592939295/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592939295/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592939295/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592939295/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592939295/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592939295/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592939295/2-onur/my_sdss.fits), [docker.log](badass/04592939295/docker.log), [fit.log](badass/04592939295/fit.log), [main.py](badass/04592939295/main.py), [spectrum.pdf](badass/04592939295/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592939295/balmer.csv), [broad.csv](fantasy_agn/04592939295/broad.csv), [coronal.csv](fantasy_agn/04592939295/coronal.csv), [feII_forbidden.csv](fantasy_agn/04592939295/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592939295/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592939295/feii_IZw1.csv), [fit.log](fantasy_agn/04592939295/fit.log), [helium.csv](fantasy_agn/04592939295/helium.csv), [hydrogen.csv](fantasy_agn/04592939295/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592939295/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592939295/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592939295/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592939295/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592939295/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592939295/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592939295/uvfe.csv)
- `gelato`: [docker.log](gelato/04592939295/docker.log), [my_sdss-comp.pdf](gelato/04592939295/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592939295/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592939295/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592939295/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592939295/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592939295/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.png)

## Object `04592975881`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 129.3808345286753 | 14.525615746741876 | line_complex_reduced (reported) |
| badass | 7.791251326886371 | 3.3150119291922038 | line_window_computed |
| fantasy_agn | 101.19425645229734 | 25.28583539785534 | line_window_computed |
| gelato | 56.135773300281116 | 30.89734574845302 | global_reduced (reported) |
| gleam | 301.89845141300515 | 9.10406774777778 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 111 |  | 155 | 132 |
| Hb4861 | broad | 3.43e+03 | 0 | 2.03e+03 | 411 |  |
| Hb4861 | narrow |  | 748 | 162 |  | 1.4e+03 |
| Hb4861 | outflow |  | 1.53e+03 |  |  |  |
| OIII4959 | broad |  | 113 | 90.7 |  |  |
| OIII4959 | narrow | 91.8 | 196 | 203 | 192 | 248 |
| OIII4959 | outflow | 189 | 309 |  |  |  |
| OIII5007 | broad |  | 339 | 275 |  |  |
| OIII5007 | narrow | 283 | 589 | 616 | 550 | 743 |
| OIII5007 | outflow | 582 | 929 |  |  |  |
| Ha6563 | broad | 9.6e+03 | 4.78e+03 | 6.94e+03 | 2.41e+03 | 819 |
| Ha6563 | narrow | 504 | 871 | 778 |  | 5.39e+03 |
| Ha6563 | outflow |  | 7.57e+03 |  |  |  |
| NII6585 | narrow | 3.66 |  | 246 | 2.39e+03 | 125 |
| SII6718 | narrow | 59.5 |  |  | 202 |  |
| SII6732 | narrow | 59.6 |  |  | 48.9 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592975881/fit.log), [output.fits](pyqsofit/04592975881/output.fits), [pyqsofit_model.csv](pyqsofit/04592975881/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592975881/qsopar.fits), [result.pdf](pyqsofit/04592975881/result.pdf), [spectrum.fits](pyqsofit/04592975881/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592975881/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592975881/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592975881/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592975881/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592975881/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592975881/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592975881/2-onur/my_sdss.fits), [docker.log](badass/04592975881/docker.log), [fit.log](badass/04592975881/fit.log), [main.py](badass/04592975881/main.py), [spectrum.pdf](badass/04592975881/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592975881/balmer.csv), [broad.csv](fantasy_agn/04592975881/broad.csv), [coronal.csv](fantasy_agn/04592975881/coronal.csv), [feII_forbidden.csv](fantasy_agn/04592975881/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592975881/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592975881/feii_IZw1.csv), [fit.log](fantasy_agn/04592975881/fit.log), [helium.csv](fantasy_agn/04592975881/helium.csv), [hydrogen.csv](fantasy_agn/04592975881/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592975881/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592975881/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592975881/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592975881/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592975881/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592975881/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592975881/uvfe.csv)
- `gelato`: [docker.log](gelato/04592975881/docker.log), [my_sdss-comp.pdf](gelato/04592975881/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592975881/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592975881/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592975881/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592975881/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592975881/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.png)

## Object `04592979214`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 52.271352714068 | 14.122103317299526 | line_complex_reduced (reported) |
| badass | 153.38009402528525 | 94.25219807029268 | line_window_computed |
| fantasy_agn | 49.57437739069657 | 177.71361327409565 | line_window_computed |
| gelato | 52.8815022437711 | 22.826837894817622 | global_reduced (reported) |
| gleam | 36.95041035774557 | 4.540421837999999 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gleam**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 11.5 |  |  |  |
| OII3727 | narrow |  | 402 |  | 402 | 380 |
| Hb4861 | broad | 2e+03 | 377 | 1.16e+03 | 203 | 155 |
| Hb4861 | narrow |  | 508 | 152 |  | 2.01e+03 |
| Hb4861 | outflow |  | 1.16e+03 |  |  |  |
| OIII4959 | broad |  | 0 | 205 |  |  |
| OIII4959 | narrow | 61.1 | 313 | 0 | 10.4 | 408 |
| OIII4959 | outflow | 89.9 | 495 |  |  |  |
| OIII5007 | broad |  | 0 | 622 |  |  |
| OIII5007 | narrow | 188 | 942 | 0 | 29.7 | 1.22e+03 |
| OIII5007 | outflow | 277 | 1.49e+03 |  |  |  |
| Ha6563 | broad | 5.16e+03 | 1.43e+03 | 4.75e+03 | 1.13e+03 | 4.16e+03 |
| Ha6563 | narrow | 21.5 | 847 | 0 |  | 523 |
| Ha6563 | outflow |  | 4.83e+03 |  |  |  |
| NII6585 | narrow | 105 |  | 0 | 1.47e+03 | 125 |
| SII6718 | narrow | 161 |  |  | 180 | 157 |
| SII6732 | narrow | 161 |  |  | 155 | 137 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592979214/fit.log), [output.fits](pyqsofit/04592979214/output.fits), [pyqsofit_model.csv](pyqsofit/04592979214/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592979214/qsopar.fits), [result.pdf](pyqsofit/04592979214/result.pdf), [spectrum.fits](pyqsofit/04592979214/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592979214/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592979214/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592979214/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592979214/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592979214/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592979214/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592979214/2-onur/my_sdss.fits), [docker.log](badass/04592979214/docker.log), [fit.log](badass/04592979214/fit.log), [main.py](badass/04592979214/main.py), [spectrum.pdf](badass/04592979214/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592979214/balmer.csv), [broad.csv](fantasy_agn/04592979214/broad.csv), [coronal.csv](fantasy_agn/04592979214/coronal.csv), [feII_forbidden.csv](fantasy_agn/04592979214/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592979214/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592979214/feii_IZw1.csv), [fit.log](fantasy_agn/04592979214/fit.log), [helium.csv](fantasy_agn/04592979214/helium.csv), [hydrogen.csv](fantasy_agn/04592979214/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592979214/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592979214/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592979214/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592979214/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592979214/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592979214/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592979214/uvfe.csv)
- `gelato`: [docker.log](gelato/04592979214/docker.log), [my_sdss-comp.pdf](gelato/04592979214/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592979214/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592979214/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592979214/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592979214/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592979214/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.png)

## Object `06872228427`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 28.752548622371854 | 14.159931181782383 | line_complex_reduced (reported) |
| badass | 20.995480053600627 | 18.305510113227616 | line_window_computed |
| fantasy_agn | 50.004962800164876 | 45.935738008531466 | line_window_computed |
| gelato | 18.06435856361109 | 7.064354654563669 | global_reduced (reported) |
| gleam | 95.20740360606459 | 15.7782746725 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0.000723 |  |  |  |
| OII3727 | narrow |  | 100 |  | 107 | 103 |
| Hb4861 | broad | 434 | 126 | 185 | 44.7 |  |
| Hb4861 | narrow |  | 69.3 | 31.8 |  | 47.6 |
| Hb4861 | outflow |  | 233 |  |  |  |
| OIII4959 | broad |  | 0.0234 | 92 |  |  |
| OIII4959 | narrow | 68.6 | 130 | 58.7 | 140 | 139 |
| OIII4959 | outflow | 44.6 | 130 |  |  |  |
| OIII5007 | broad |  | 0.0778 | 279 |  |  |
| OIII5007 | narrow | 211 | 391 | 178 | 401 | 416 |
| OIII5007 | outflow | 137 | 391 |  |  |  |
| Ha6563 | broad | 1.51e+03 | 0 | 1.02e+03 | 500 |  |
| Ha6563 | narrow | 0.0214 | 384 | 248 |  | 988 |
| Ha6563 | outflow |  | 1.44e+03 |  |  |  |
| NII6585 | narrow | 163 |  | 188 | 539 | 152 |
| SII6718 | narrow | 57.4 |  |  | 71.3 | 53.4 |
| SII6732 | narrow | 57.5 |  |  | 58.6 | 59.7 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/06872228427/fit.log), [output.fits](pyqsofit/06872228427/output.fits), [pyqsofit_model.csv](pyqsofit/06872228427/pyqsofit_model.csv), [qsopar.fits](pyqsofit/06872228427/qsopar.fits), [result.pdf](pyqsofit/06872228427/result.pdf), [spectrum.fits](pyqsofit/06872228427/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/06872228427/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/06872228427/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/06872228427/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/06872228427/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/06872228427/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/06872228427/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/06872228427/2-onur/my_sdss.fits), [docker.log](badass/06872228427/docker.log), [fit.log](badass/06872228427/fit.log), [main.py](badass/06872228427/main.py), [spectrum.pdf](badass/06872228427/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/06872228427/balmer.csv), [broad.csv](fantasy_agn/06872228427/broad.csv), [coronal.csv](fantasy_agn/06872228427/coronal.csv), [feII_forbidden.csv](fantasy_agn/06872228427/feII_forbidden.csv), [feII_model.csv](fantasy_agn/06872228427/feII_model.csv), [feii_IZw1.csv](fantasy_agn/06872228427/feii_IZw1.csv), [fit.log](fantasy_agn/06872228427/fit.log), [helium.csv](fantasy_agn/06872228427/helium.csv), [hydrogen.csv](fantasy_agn/06872228427/hydrogen.csv), [my_sdss.pdf](fantasy_agn/06872228427/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/06872228427/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/06872228427/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/06872228427/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/06872228427/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/06872228427/oiii_nii.csv), [uvfe.csv](fantasy_agn/06872228427/uvfe.csv)
- `gelato`: [docker.log](gelato/06872228427/docker.log), [my_sdss-comp.pdf](gelato/06872228427/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/06872228427/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/06872228427/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/06872228427/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/06872228427/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/06872228427/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.png)
