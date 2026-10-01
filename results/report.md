# Cross-tool AGN emission-line comparison

## Object `04545183216`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 0.8764492804155621 | 1.5570508144700357 | line_complex_reduced (reported) |
| badass | 3.4999510431446867 | 1.5483115836529187 | line_window_computed |
| fantasy_agn | 2.4003239970059345 | 4.759910983034146 | line_window_computed |
| gelato | 2.7052087537145395 | 10.048710055445396 | global_reduced (reported) |
| gleam | 586.292554672851 | 59.66571736642857 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 11 |  | 153 |  |
| Hb4861 | broad | 3.16e+03 | 1.7e+03 | 2.51e+03 | 2.48e+03 | 1.57e+03 |
| Hb4861 | narrow |  | 12.7 | 54.3 | 64.4 | 1.04e+03 |
| Hb4861 | total |  | 1.71e+03 |  |  |  |
| OIII4959 | narrow | 45.5 | 56.3 | 58.9 | 103 | 38.7 |
| OIII4959 | outflow | 67.8 |  |  |  |  |
| OIII5007 | narrow | 139 | 169 | 178 | 308 | 116 |
| OIII5007 | outflow | 208 |  |  |  |  |
| Ha6563 | broad | 1.26e+04 | 7.3e+03 | 1.12e+04 | 1.13e+04 | 1.04e+04 |
| Ha6563 | narrow | 306 | 134 | 168 | 501 |  |
| Ha6563 | total |  | 7.49e+03 |  |  |  |
| NII6585 | narrow | 4.26 | 0 | 5.29 | -171 |  |
| SII6718 | narrow | 9.89 | 26.7 | 32.8 | 52.7 |  |
| SII6732 | narrow | 37.5 | 13.1 | 29.4 | 32.6 |  |

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
| fantasy_agn | 8.10576160604952 | 15.640353888052909 | line_window_computed |
| gelato | 2.5043858542968027 | 11.516359734001503 | global_reduced (reported) |
| gleam | 235.79859256794623 | 83.49377667375 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 38.2 |  | 72.7 |  |
| OII3727 | total |  |  |  |  | 75.2 |
| Hb4861 | broad | 1.42e+03 | 976 | 1.04e+03 | 1.07e+03 | 580 |
| Hb4861 | narrow |  | 0 | 156 | 240 | 817 |
| Hb4861 | total |  | 976 |  |  |  |
| OIII4959 | broad |  |  |  |  | 94.5 |
| OIII4959 | narrow | 43 | 73.5 | 67.9 | 33.7 |  |
| OIII4959 | outflow | 42.5 |  |  |  |  |
| OIII5007 | narrow | 132 | 221 | 206 | 101 |  |
| OIII5007 | outflow | 130 |  |  |  |  |
| OIII5007 | total |  |  |  |  | 283 |
| Ha6563 | broad | 5.78e+03 | 3.73e+03 | 4.45e+03 | 3.8e+03 | 1.98e+03 |
| Ha6563 | narrow | 200 | 312 | 487 | 1.43e+03 | 3.99e+03 |
| Ha6563 | total |  | 4.21e+03 |  |  |  |
| NII6585 | narrow | 116 | 0 | 266 | 382 | 63.3 |
| SII6718 | narrow | 41.9 | 0 | 41 | 96.7 |  |
| SII6732 | narrow | 32.4 | 28.4 | 33.7 | 42.1 |  |

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
| fantasy_agn | 11.080337496665328 | 18.316940529581135 | line_window_computed |
| gelato | 6.617661913421532 | 17.28497940518997 | global_reduced (reported) |
| gleam | 246.17552423645293 | 188.6894632525 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 118 |  | 344 |  |
| OII3727 | total |  |  |  |  | 150 |
| Hb4861 | broad | 5.83e+03 | 2.51e+03 | 3.58e+03 | 3.33e+03 | 1.4e+03 |
| Hb4861 | narrow |  | 257 | 400 | 794 | 2.4e+03 |
| Hb4861 | total |  | 2.76e+03 |  |  |  |
| OIII4959 | narrow | 331 | 266 | 359 | 204 |  |
| OIII4959 | outflow | 147 |  |  |  |  |
| OIII4959 | total |  |  |  |  | 346 |
| OIII5007 | narrow | 1.01e+03 | 802 | 1.09e+03 | 612 |  |
| OIII5007 | outflow | 448 |  |  |  |  |
| OIII5007 | total |  |  |  |  | 1.04e+03 |
| Ha6563 | broad | 1.56e+04 | 1.05e+04 | 1.23e+04 | 1.11e+04 | 5.12e+03 |
| Ha6563 | narrow | 1.06e+03 | 868 | 1.09e+03 | 3.77e+03 | 1.07e+04 |
| Ha6563 | total |  | 1.17e+04 |  |  |  |
| NII6585 | narrow | 429 | 191 | 570 | 1.12e+03 | 62 |
| SII6718 | narrow | 7.31 | 57.8 | 67.2 | 243 |  |
| SII6732 | narrow | 26.2 | 40.2 | 50.4 | 81 |  |

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
| fantasy_agn | 18.0461673239272 | 25.582930936407145 | line_window_computed |
| gelato | 4.1450025834919435 | 9.403693322375586 | global_reduced (reported) |
| gleam | 54.13010553339811 | 26.597709482 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 55 |  | 150 | 118 |
| Hb4861 | broad | 1.24e+03 | 385 | 513 | 513 | 484 |
| Hb4861 | narrow |  | 135 | 132 | 109 | 85.4 |
| Hb4861 | total |  | 520 |  |  |  |
| OIII4959 | narrow | 149 | 192 | 220 | 105 | 227 |
| OIII4959 | outflow | 93.3 |  |  |  |  |
| OIII5007 | narrow | 456 | 578 | 666 | 314 |  |
| OIII5007 | outflow | 286 |  |  |  |  |
| OIII5007 | total |  |  |  |  | 680 |
| Ha6563 | broad | 3.29e+03 | 2.17e+03 | 2.77e+03 | 2.97e+03 | 2.89e+03 |
| Ha6563 | narrow | 510 | 813 | 465 | 580 | 470 |
| Ha6563 | total |  | 3.04e+03 |  |  |  |
| NII6585 | narrow | 401 | 663 | 430 | 448 | 374 |
| SII6718 | narrow | 90.8 | 65.3 | 78.5 | 117 | 72.2 |
| SII6732 | narrow | 61.9 | 47.2 | 53.1 | 77.9 | 42.6 |

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
| fantasy_agn | 4.047019406364966 | 8.218506000538666 | line_window_computed |
| gelato | 17.496466703917836 | 10.699587082004648 | global_reduced (reported) |
| gleam | 588.6465940286677 | 34.875176125454544 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  |  |  |  | 57.9 |
| OII3727 | narrow |  | 0 |  | 27.2 |  |
| Hb4861 | broad | 521 | 407 | 570 | 190 | 417 |
| Hb4861 | narrow |  | 101 | 112 | 190 | 185 |
| Hb4861 | total |  | 509 |  |  |  |
| OIII4959 | narrow | 39.8 | 38.6 | 29 | 25.9 |  |
| OIII4959 | outflow | 0.489 |  |  |  |  |
| OIII5007 | narrow | 122 | 116 | 87.9 | 77.9 |  |
| OIII5007 | outflow | 1.5 |  |  |  |  |
| Ha6563 | broad | 1.82e+03 | 1.08e+03 | 1.64e+03 | 606 | 1.37e+03 |
| Ha6563 | narrow | 595 | 255 | 213 | 606 | 765 |
| Ha6563 | total |  | 1.53e+03 |  |  |  |
| NII6585 | narrow | 118 | 20.2 | 43.3 | 287 | 23.3 |
| SII6718 | narrow | 11.6 | 4.24 | 4.41 | 15.1 |  |
| SII6732 | narrow | 2.76 | 0.561 | 2.54 | -22.4 |  |

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
| fantasy_agn | 6.764507829320612 | 17.163255256269768 | line_window_computed |
| gelato | 3.5383283225862106 | 7.976677799669726 | global_reduced (reported) |
| gleam | 337.189611574856 | 128.88098579375 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 32.2 |  | 98 | 50.1 |
| Hb4861 | broad | 3.03e+03 | 946 | 1.45e+03 | 1.26e+03 | 1.01e+03 |
| Hb4861 | narrow |  | 110 | 169 | 297 | 615 |
| Hb4861 | total |  | 1.06e+03 |  |  |  |
| OIII4959 | narrow | 88.4 | 74.3 | 91.2 | 48.6 |  |
| OIII4959 | outflow | 23.4 |  |  |  |  |
| OIII4959 | total |  |  |  |  | 83.1 |
| OIII5007 | narrow | 271 | 223 | 276 | 146 |  |
| OIII5007 | outflow | 71.6 |  |  |  |  |
| OIII5007 | total |  |  |  |  | 249 |
| Ha6563 | broad | 5.6e+03 | 3.72e+03 | 4.94e+03 | 4.83e+03 | 3.91e+03 |
| Ha6563 | narrow | 739 | 444 | 585 | 1.46e+03 | 2.03e+03 |
| Ha6563 | total |  | 4.33e+03 |  |  |  |
| NII6585 | narrow | 219 | 84.2 | 180 | 144 | 85.2 |
| SII6718 | narrow | 25.5 | 23.3 | 33.8 | 93.9 |  |
| SII6732 | narrow | 47.3 | 21 | 25.6 | 66.7 |  |

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
| fantasy_agn | 10.566039608831261 | 20.805322815038153 | line_window_computed |
| gelato | 4.4691494675475765 | 7.980443169221684 | global_reduced (reported) |
| gleam | 233.31785447610943 | 109.77964931875 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 84.1 |  | 182 |  |
| OII3727 | total |  |  |  |  | 96.1 |
| Hb4861 | broad | 3.61e+03 | 1.48e+03 | 1.7e+03 | 1.67e+03 | 1.1e+03 |
| Hb4861 | narrow |  | 134 | 245 | 403 | 917 |
| Hb4861 | total |  | 1.61e+03 |  |  |  |
| OIII4959 | narrow | 99.6 | 108 | 124 | 92.2 | 111 |
| OIII4959 | outflow | 79.6 |  |  |  |  |
| OIII5007 | narrow | 305 | 325 | 375 | 277 | 334 |
| OIII5007 | outflow | 244 |  |  |  |  |
| Ha6563 | broad | 7.55e+03 | 4.97e+03 | 5.53e+03 | 5.13e+03 | 4.6e+03 |
| Ha6563 | narrow | 342 | 643 | 734 | 1.68e+03 | 2.19e+03 |
| Ha6563 | total |  | 5.75e+03 |  |  |  |
| NII6585 | narrow | 183 | 312 | 515 | 576 |  |
| NII6585 | total |  |  |  |  | 512 |
| SII6718 | narrow | 39 | 61 | 53.4 | 89.8 |  |
| SII6732 | narrow | 34.6 | 0 | 42.1 | 62.1 |  |

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
| fantasy_agn | 11.026552111312764 | 19.193756110451165 | line_window_computed |
| gelato | 2.4900395529327213 | 6.387217991526989 | global_reduced (reported) |
| gleam | 277.4731246278182 | 164.84373761875 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 65.6 |  | 192 |  |
| OII3727 | total |  |  |  |  | 142 |
| Hb4861 | broad | 3.29e+03 | 1.59e+03 | 2.08e+03 | 1.95e+03 | 1.88e+03 |
| Hb4861 | narrow |  | 0 | 153 | 212 | 214 |
| Hb4861 | total |  | 1.59e+03 |  |  |  |
| OIII4959 | narrow | 176 | 218 | 280 | 183 |  |
| OIII4959 | outflow | 117 |  |  |  |  |
| OIII4959 | total |  |  |  |  | 269 |
| OIII5007 | narrow | 538 | 657 | 850 | 549 |  |
| OIII5007 | outflow | 359 |  |  |  |  |
| OIII5007 | total |  |  |  |  | 807 |
| Ha6563 | broad | 9.22e+03 | 6.19e+03 | 8.05e+03 | 8.12e+03 | 6.92e+03 |
| Ha6563 | narrow | 636 | 11.8 | 526 | 1.27e+03 | 1.73e+03 |
| Ha6563 | total |  | 6.31e+03 |  |  |  |
| NII6585 | narrow | 245 | 53.7 | 297 | 226 | 144 |
| SII6718 | narrow | 15.4 | 0 | 72.1 | 147 |  |
| SII6732 | narrow | 88 | 4.01 | 61.9 | 111 |  |

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
| fantasy_agn | 32.82467979202275 | 33.734453121226124 | line_window_computed |
| gelato | 1.8351996907269812 | 6.580005630293359 | global_reduced (reported) |
| gleam | 27.339549225234272 | 61.387472595999995 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 265 |  | 407 | 393 |
| Hb4861 | broad | 2.61e+03 | 1.06e+03 | 1e+03 | 1.12e+03 | 1.01e+03 |
| Hb4861 | narrow |  | 289 | 160 | 172 | 146 |
| Hb4861 | total |  | 1.35e+03 |  |  |  |
| OIII4959 | narrow | 368 | 385 | 399 | 366 | 407 |
| OIII4959 | outflow | 64.2 |  |  |  |  |
| OIII5007 | narrow | 1.13e+03 | 1.16e+03 | 1.21e+03 | 1.1e+03 | 1.22e+03 |
| OIII5007 | outflow | 196 |  |  |  |  |
| Ha6563 | broad | 4.84e+03 | 3.9e+03 | 4.47e+03 | 4.45e+03 | 4.24e+03 |
| Ha6563 | narrow | 583 | 853 | 612 | 653 | 597 |
| Ha6563 | total |  | 4.9e+03 |  |  |  |
| NII6585 | narrow | 177 | 329 | 186 | 182 | 170 |
| SII6718 | narrow | 166 | 97.5 | 149 | 184 | 137 |
| SII6732 | narrow | 151 | 80.1 | 133 | 160 | 118 |

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
| fantasy_agn | 16.938158635129344 | 19.300691700758783 | line_window_computed |
| gelato | 14.475132714017768 | 6.436657407352231 | global_reduced (reported) |
| gleam | 42.78297106589372 | 14.908462658 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | narrow |  | 100 |  | 108 | 101 |
| Hb4861 | broad | 269 | 162 | 174 | 36 | 167 |
| Hb4861 | narrow |  | 52.8 | 64.5 | 36 | 32.1 |
| Hb4861 | total |  | 215 |  |  |  |
| OIII4959 | narrow | 77.8 | 131 | 135 | 132 |  |
| OIII4959 | outflow | 69 |  |  |  |  |
| OIII4959 | total |  |  |  |  | 140 |
| OIII5007 | narrow | 238 | 394 | 409 | 397 |  |
| OIII5007 | outflow | 211 |  |  |  |  |
| OIII5007 | total |  |  |  |  | 419 |
| Ha6563 | broad | 1.13e+03 | 973 | 1.03e+03 | 171 | 1.04e+03 |
| Ha6563 | narrow | 227 | 283 | 228 | 171 | 250 |
| Ha6563 | total |  | 1.34e+03 |  |  |  |
| NII6585 | narrow | 201 | 269 | 224 | 634 | 212 |
| SII6718 | narrow | 62.5 | 39.8 | 45.7 | 69.5 | 48.4 |
| SII6732 | narrow | 55.6 | 0 | 36 | 58 | 40.6 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/06872228427/fit.log), [output.fits](pyqsofit/06872228427/output.fits), [pyqsofit_model.csv](pyqsofit/06872228427/pyqsofit_model.csv), [qsopar.fits](pyqsofit/06872228427/qsopar.fits), [result.pdf](pyqsofit/06872228427/result.pdf), [spectrum.fits](pyqsofit/06872228427/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/06872228427/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/06872228427/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/06872228427/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/06872228427/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/06872228427/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/06872228427/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/06872228427/2-onur/my_sdss.fits), [docker.log](badass/06872228427/docker.log), [fit.log](badass/06872228427/fit.log), [main.py](badass/06872228427/main.py), [spectrum.pdf](badass/06872228427/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/06872228427/balmer.csv), [broad.csv](fantasy_agn/06872228427/broad.csv), [coronal.csv](fantasy_agn/06872228427/coronal.csv), [docker.log](fantasy_agn/06872228427/docker.log), [feII_forbidden.csv](fantasy_agn/06872228427/feII_forbidden.csv), [feII_model.csv](fantasy_agn/06872228427/feII_model.csv), [feii_IZw1.csv](fantasy_agn/06872228427/feii_IZw1.csv), [fit.log](fantasy_agn/06872228427/fit.log), [helium.csv](fantasy_agn/06872228427/helium.csv), [hydrogen.csv](fantasy_agn/06872228427/hydrogen.csv), [my_sdss.pdf](fantasy_agn/06872228427/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/06872228427/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/06872228427/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/06872228427/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/06872228427/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/06872228427/oiii_nii.csv), [uvfe.csv](fantasy_agn/06872228427/uvfe.csv)
- `gelato`: [docker.log](gelato/06872228427/docker.log), [my_sdss-comp.pdf](gelato/06872228427/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/06872228427/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/06872228427/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/06872228427/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/06872228427/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.NII2.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII4.OIII5.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/06872228427/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.png)
