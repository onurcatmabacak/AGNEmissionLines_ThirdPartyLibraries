# Cross-tool AGN emission-line comparison

## Object `04545183216`

| tool | reduced chi^2 | statistic |
|---|---:|---|
| pyqsofit | 2.7988727369076147 | line_complex_reduced (reported) |
| badass | 2.075759641447285 | line_window_computed |
| fantasy_agn | 10.961799432857054 | line_window_computed |
| gelato | nan | n/a (degenerate summary) |
| gleam | 31.575066142857146 | mean_line_reduced (reported) |

_lowest &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 0 |  | 163 |  |
| OII3727 | total |  |  |  |  | 51.2 |
| Hb4861 | broad | 2.32e+03 | 0 | 2.46e+03 | -177 |  |
| Hb4861 | narrow |  | 349 | 0 |  |  |
| Hb4861 | outflow |  | 895 |  |  |  |
| OIII4959 | broad |  | 898 |  |  |  |
| OIII4959 | narrow | 1.32 | 0 |  | 70.3 |  |
| OIII4959 | outflow | 6.68 | 898 |  |  |  |
| OIII5007 | broad |  | 0 | 335 |  |  |
| OIII5007 | narrow | 145 | 0 | 122 | 201 |  |
| OIII5007 | outflow | 189 | 0 |  |  |  |
| OIII5007 | total |  |  |  |  | 178 |
| Ha6563 | broad | 1.26e+04 | 5.92e+03 | 6.94e+03 | -128 |  |
| Ha6563 | narrow | 398 | 405 | 562 |  |  |
| Ha6563 | outflow |  | 7.63e+03 |  |  |  |
| NII6585 | narrow | 1.29 |  |  | 152 |  |
| SII6718 | narrow | 24.7 |  |  | -147 |  |
| SII6732 | narrow | 24.8 |  |  | -165 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04545183216/fit.log), [output.fits](pyqsofit/04545183216/output.fits), [qsopar.fits](pyqsofit/04545183216/qsopar.fits), [result.pdf](pyqsofit/04545183216/result.pdf), [spectrum.fits](pyqsofit/04545183216/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04545183216/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04545183216/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04545183216/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04545183216/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04545183216/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04545183216/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04545183216/2-onur/my_sdss.fits), [docker.log](badass/04545183216/docker.log), [fit.log](badass/04545183216/fit.log), [main.py](badass/04545183216/main.py), [spectrum.pdf](badass/04545183216/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04545183216/balmer.csv), [broad.csv](fantasy_agn/04545183216/broad.csv), [coronal.csv](fantasy_agn/04545183216/coronal.csv), [feII_forbidden.csv](fantasy_agn/04545183216/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04545183216/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04545183216/feii_IZw1.csv), [fit.log](fantasy_agn/04545183216/fit.log), [helium.csv](fantasy_agn/04545183216/helium.csv), [hydrogen.csv](fantasy_agn/04545183216/hydrogen.csv), [my_sdss_model.csv](fantasy_agn/04545183216/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04545183216/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04545183216/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04545183216/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04545183216/oiii_nii.csv), [uvfe.csv](fantasy_agn/04545183216/uvfe.csv)
- `gelato`: [docker.log](gelato/04545183216/docker.log), [my_sdss-comp.pdf](gelato/04545183216/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04545183216/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04545183216/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04545183216/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04545183216/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04545183216/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.png)

## Object `04570362657`

| tool | reduced chi^2 | statistic |
|---|---:|---|
| pyqsofit | 4.9793280308972765 | line_complex_reduced (reported) |
| badass | 8.192949037831315 | line_window_computed |
| fantasy_agn | 22.710794958752587 | line_window_computed |
| gelato | nan | n/a (degenerate summary) |
| gleam | 4.0555008575 | mean_line_reduced (reported) |

_lowest &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 0 |  | 151 |  |
| OII3727 | total |  |  |  |  | 67.3 |
| Hb4861 | broad | 1.73e+03 | 1.07e+03 | 1.35e+03 | -289 |  |
| Hb4861 | narrow |  | 0 | 0 |  |  |
| Hb4861 | outflow |  | 1.07e+03 |  |  |  |
| Hb4861 | total |  |  |  |  | 1.04e+03 |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 1.89 | 0 |  | 45.6 |  |
| OIII4959 | outflow | 0.211 | 0 |  |  |  |
| OIII5007 | broad |  | 0 | 112 |  |  |
| OIII5007 | narrow | 239 | 188 | 236 | 130 |  |
| OIII5007 | outflow | 51.9 | 301 |  |  |  |
| OIII5007 | total |  |  |  |  | 304 |
| Ha6563 | broad | 5.42e+03 | 938 | 3.98e+03 | -237 |  |
| Ha6563 | narrow | 769 | 1.04e+03 | 719 |  |  |
| Ha6563 | outflow |  | 4.42e+03 |  |  |  |
| Ha6563 | total |  |  |  |  | 4.46e+03 |
| NII6585 | narrow | 0.625 |  |  | 115 |  |
| SII6718 | narrow | 24.8 |  |  | -111 |  |
| SII6718 | total |  |  |  |  | 37.9 |
| SII6732 | narrow | 24.9 |  |  | -103 |  |
| SII6732 | total |  |  |  |  | 22.3 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04570362657/fit.log), [output.fits](pyqsofit/04570362657/output.fits), [qsopar.fits](pyqsofit/04570362657/qsopar.fits), [result.pdf](pyqsofit/04570362657/result.pdf), [spectrum.fits](pyqsofit/04570362657/spectrum.fits)
- `badass`: [docker.log](badass/04570362657/docker.log), [fit.log](badass/04570362657/fit.log), [spectrum.pdf](badass/04570362657/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04570362657/balmer.csv), [broad.csv](fantasy_agn/04570362657/broad.csv), [coronal.csv](fantasy_agn/04570362657/coronal.csv), [feII_forbidden.csv](fantasy_agn/04570362657/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04570362657/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04570362657/feii_IZw1.csv), [fit.log](fantasy_agn/04570362657/fit.log), [helium.csv](fantasy_agn/04570362657/helium.csv), [hydrogen.csv](fantasy_agn/04570362657/hydrogen.csv), [my_sdss_model.csv](fantasy_agn/04570362657/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04570362657/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04570362657/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04570362657/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04570362657/oiii_nii.csv), [uvfe.csv](fantasy_agn/04570362657/uvfe.csv)
- `gelato`: [docker.log](gelato/04570362657/docker.log), [my_sdss-comp.pdf](gelato/04570362657/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04570362657/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04570362657/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04570362657/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04570362657/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04570362657/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.png)

## Object `04570493016`

| tool | reduced chi^2 | statistic |
|---|---:|---|
| pyqsofit | 4.589109913498399 | line_complex_reduced (reported) |
| badass | 23.531428444161733 | line_window_computed |
| fantasy_agn | 203.59608797700517 | line_window_computed |
| gelato | nan | n/a (degenerate summary) |
| gleam | 19.196097982 | mean_line_reduced (reported) |

_lowest &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0.00303 |  |  |  |
| OII3727 | narrow |  | 0 |  | 662 |  |
| OII3727 | total |  |  |  |  | 90.3 |
| Hb4861 | broad | 6.41e+03 | 3.52e+03 | 3.17e+03 | -589 |  |
| Hb4861 | narrow |  | 0 | 8.93 |  |  |
| Hb4861 | outflow |  | 3.52e+03 |  |  |  |
| Hb4861 | total |  |  |  |  | 3.06e+03 |
| OIII4959 | broad |  | 1.26e+03 |  |  |  |
| OIII4959 | narrow | 30.8 | 0 |  | 5.53 |  |
| OIII4959 | outflow | 336 | 1.26e+03 |  |  |  |
| OIII4959 | total |  |  |  |  | 207 |
| OIII5007 | broad |  | 0 | 1.27e+03 |  |  |
| OIII5007 | narrow | 1.15e+03 | 817 | 0 | 15.8 |  |
| OIII5007 | outflow | 48.7 | 1.29e+03 |  |  |  |
| OIII5007 | total |  |  |  |  | 1.1e+03 |
| Ha6563 | broad | 1.58e+04 | 0 | 6.94e+03 | -672 |  |
| Ha6563 | narrow | 1.41e+03 | 2.97e+03 | 845 |  |  |
| Ha6563 | outflow |  | 1.13e+04 |  |  |  |
| Ha6563 | total |  |  |  |  | 1.23e+04 |
| NII6585 | narrow | 7.42 |  |  | 520 |  |
| SII6718 | narrow | 10.2 |  |  | -176 |  |
| SII6732 | narrow | 10.2 |  |  | -151 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04570493016/fit.log), [output.fits](pyqsofit/04570493016/output.fits), [qsopar.fits](pyqsofit/04570493016/qsopar.fits), [result.pdf](pyqsofit/04570493016/result.pdf), [spectrum.fits](pyqsofit/04570493016/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04570493016/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04570493016/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04570493016/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04570493016/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04570493016/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04570493016/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04570493016/2-onur/my_sdss.fits), [docker.log](badass/04570493016/docker.log), [fit.log](badass/04570493016/fit.log), [main.py](badass/04570493016/main.py), [spectrum.pdf](badass/04570493016/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04570493016/balmer.csv), [broad.csv](fantasy_agn/04570493016/broad.csv), [coronal.csv](fantasy_agn/04570493016/coronal.csv), [feII_forbidden.csv](fantasy_agn/04570493016/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04570493016/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04570493016/feii_IZw1.csv), [fit.log](fantasy_agn/04570493016/fit.log), [helium.csv](fantasy_agn/04570493016/helium.csv), [hydrogen.csv](fantasy_agn/04570493016/hydrogen.csv), [my_sdss_model.csv](fantasy_agn/04570493016/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04570493016/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04570493016/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04570493016/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04570493016/oiii_nii.csv), [uvfe.csv](fantasy_agn/04570493016/uvfe.csv)
- `gelato`: [docker.log](gelato/04570493016/docker.log), [my_sdss-comp.pdf](gelato/04570493016/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04570493016/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04570493016/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04570493016/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04570493016/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04570493016/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.png)

## Object `04592503068`

| tool | reduced chi^2 | statistic |
|---|---:|---|
| pyqsofit | 17.917807556963858 | line_complex_reduced (reported) |
| badass | 39.68565492071989 | line_window_computed |
| fantasy_agn | 64.29614731035008 | line_window_computed |
| gelato | nan | n/a (degenerate summary) |
| gleam | 14.848840516666668 | mean_line_reduced (reported) |

_lowest &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 10.7 |  |  |  |
| OII3727 | narrow |  | 0 |  | 54.3 |  |
| OII3727 | total |  |  |  |  | 126 |
| Hb4861 | broad | 1.78e+03 | 0 | 650 | -64.9 |  |
| Hb4861 | narrow |  | 101 | 0 |  |  |
| Hb4861 | outflow |  | 287 |  |  |  |
| Hb4861 | total |  |  |  |  | 170 |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 1.47 | 80 |  | 24.1 |  |
| OIII4959 | outflow | 7.55 | 238 |  |  |  |
| OIII4959 | total |  |  |  |  | 188 |
| OIII5007 | broad |  | 0 | 550 |  |  |
| OIII5007 | narrow | 693 | 580 | 505 | 68.9 |  |
| OIII5007 | outflow | 296 | 915 |  |  |  |
| OIII5007 | total |  |  |  |  | 675 |
| Ha6563 | broad | 3.63e+03 | 0 | 2.82e+03 | -321 |  |
| Ha6563 | narrow | 396 | 848 | 344 |  |  |
| Ha6563 | outflow |  | 3.5e+03 |  |  |  |
| Ha6563 | total |  |  |  |  | 2.62e+03 |
| NII6585 | narrow | 1.23 |  |  | 135 |  |
| NII6585 | total |  |  |  |  | 326 |
| SII6718 | narrow | 66.2 |  |  | -147 |  |
| SII6718 | total |  |  |  |  | 85.3 |
| SII6732 | narrow | 66.4 |  |  | -120 |  |
| SII6732 | total |  |  |  |  | 50.9 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592503068/fit.log), [output.fits](pyqsofit/04592503068/output.fits), [qsopar.fits](pyqsofit/04592503068/qsopar.fits), [result.pdf](pyqsofit/04592503068/result.pdf), [spectrum.fits](pyqsofit/04592503068/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592503068/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592503068/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592503068/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592503068/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592503068/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592503068/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592503068/2-onur/my_sdss.fits), [docker.log](badass/04592503068/docker.log), [fit.log](badass/04592503068/fit.log), [main.py](badass/04592503068/main.py), [spectrum.pdf](badass/04592503068/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592503068/balmer.csv), [broad.csv](fantasy_agn/04592503068/broad.csv), [coronal.csv](fantasy_agn/04592503068/coronal.csv), [feII_forbidden.csv](fantasy_agn/04592503068/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592503068/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592503068/feii_IZw1.csv), [fit.log](fantasy_agn/04592503068/fit.log), [helium.csv](fantasy_agn/04592503068/helium.csv), [hydrogen.csv](fantasy_agn/04592503068/hydrogen.csv), [my_sdss_model.csv](fantasy_agn/04592503068/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592503068/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592503068/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592503068/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592503068/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592503068/uvfe.csv)
- `gelato`: [docker.log](gelato/04592503068/docker.log), [my_sdss-comp.pdf](gelato/04592503068/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592503068/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592503068/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592503068/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592503068/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592503068/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.png)

## Object `04592517882`

| tool | reduced chi^2 | statistic |
|---|---:|---|
| pyqsofit | 8.167508834252414 | line_complex_reduced (reported) |
| badass | 6.866626092778352 | line_window_computed |
| fantasy_agn | 9.506059591828919 | line_window_computed |
| gelato | nan | n/a (degenerate summary) |
| gleam | 2.167812873333333 | mean_line_reduced (reported) |

_lowest &chi;&sup2;: **gleam**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 0 |  | -49.3 |  |
| Hb4861 | broad | 518 | 0 | 666 | 12.5 |  |
| Hb4861 | narrow |  | 106 | 0 |  |  |
| Hb4861 | outflow |  | 311 |  |  |  |
| Hb4861 | total |  |  |  |  | 384 |
| OIII4959 | broad |  | 156 |  |  |  |
| OIII4959 | narrow | 26.1 | 0 |  | -28.5 |  |
| OIII4959 | outflow | 7.55 | 156 |  |  |  |
| OIII4959 | total |  |  |  |  | -48.1 |
| OIII5007 | broad |  | 0 | 159 |  |  |
| OIII5007 | narrow | 145 | 61.4 | 2 | -81.3 |  |
| OIII5007 | outflow | 0.605 | 99.2 |  |  |  |
| Ha6563 | broad | 2.21e+03 | 85.5 | 1.32e+03 | -168 |  |
| Ha6563 | narrow | 776 | 383 | 446 |  |  |
| Ha6563 | outflow |  | 1.76e+03 |  |  |  |
| Ha6563 | total |  |  |  |  | 1.57e+03 |
| NII6585 | narrow | 0.0636 |  |  | -166 |  |
| SII6718 | narrow | 0.433 |  |  | -1.03e+03 |  |
| SII6732 | narrow | 0.434 |  |  | 0.333 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592517882/fit.log), [output.fits](pyqsofit/04592517882/output.fits), [qsopar.fits](pyqsofit/04592517882/qsopar.fits), [result.pdf](pyqsofit/04592517882/result.pdf), [spectrum.fits](pyqsofit/04592517882/spectrum.fits)
- `badass`: [docker.log](badass/04592517882/docker.log), [fit.log](badass/04592517882/fit.log), [spectrum.pdf](badass/04592517882/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592517882/balmer.csv), [broad.csv](fantasy_agn/04592517882/broad.csv), [coronal.csv](fantasy_agn/04592517882/coronal.csv), [feII_forbidden.csv](fantasy_agn/04592517882/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592517882/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592517882/feii_IZw1.csv), [fit.log](fantasy_agn/04592517882/fit.log), [helium.csv](fantasy_agn/04592517882/helium.csv), [hydrogen.csv](fantasy_agn/04592517882/hydrogen.csv), [my_sdss_model.csv](fantasy_agn/04592517882/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592517882/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592517882/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592517882/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592517882/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592517882/uvfe.csv)
- `gelato`: [docker.log](gelato/04592517882/docker.log), [my_sdss-comp.pdf](gelato/04592517882/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592517882/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592517882/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592517882/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592517882/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592517882/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.png)

## Object `04592660180`

| tool | reduced chi^2 | statistic |
|---|---:|---|
| pyqsofit | 4.352208469528408 | line_complex_reduced (reported) |
| badass | 11.275745313962254 | line_window_computed |
| fantasy_agn | 29.89743816863686 | line_window_computed |
| gelato | nan | n/a (degenerate summary) |
| gleam | 4.6008153875 | mean_line_reduced (reported) |

_lowest &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 0.0191 |  | 390 |  |
| OII3727 | total |  |  |  |  | 42.8 |
| Hb4861 | broad | 2.99e+03 | 612 | 1.43e+03 | -450 |  |
| Hb4861 | narrow |  | 148 | 0 |  |  |
| Hb4861 | outflow |  | 1.03e+03 |  |  |  |
| Hb4861 | total |  |  |  |  | 1.05e+03 |
| OIII4959 | broad |  | 640 |  |  |  |
| OIII4959 | narrow | 1.8 | 0 |  | -294 |  |
| OIII4959 | outflow | 7.55 | 640 |  |  |  |
| OIII4959 | total |  |  |  |  | 35.1 |
| OIII5007 | broad |  | 0.00868 | 257 |  |  |
| OIII5007 | narrow | 275 | 171 | 234 | -840 |  |
| OIII5007 | outflow | 144 | 270 |  |  |  |
| OIII5007 | total |  |  |  |  | 326 |
| Ha6563 | broad | 5.67e+03 | 1.15e+03 | 4.44e+03 | -3.32e+03 |  |
| Ha6563 | narrow | 1.07e+03 | 863 | 881 |  |  |
| Ha6563 | outflow |  | 4.62e+03 |  |  |  |
| Ha6563 | total |  |  |  |  | 3.99e+03 |
| NII6585 | narrow | 5.63 |  |  | 2.32e+03 |  |
| SII6718 | narrow | 23.4 |  |  | -291 |  |
| SII6718 | total |  |  |  |  | 20.5 |
| SII6732 | narrow | 23.5 |  |  | 218 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592660180/fit.log), [output.fits](pyqsofit/04592660180/output.fits), [qsopar.fits](pyqsofit/04592660180/qsopar.fits), [result.pdf](pyqsofit/04592660180/result.pdf), [spectrum.fits](pyqsofit/04592660180/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592660180/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592660180/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592660180/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592660180/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592660180/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592660180/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592660180/2-onur/my_sdss.fits), [docker.log](badass/04592660180/docker.log), [fit.log](badass/04592660180/fit.log), [main.py](badass/04592660180/main.py), [spectrum.pdf](badass/04592660180/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592660180/balmer.csv), [broad.csv](fantasy_agn/04592660180/broad.csv), [coronal.csv](fantasy_agn/04592660180/coronal.csv), [feII_forbidden.csv](fantasy_agn/04592660180/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592660180/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592660180/feii_IZw1.csv), [fit.log](fantasy_agn/04592660180/fit.log), [helium.csv](fantasy_agn/04592660180/helium.csv), [hydrogen.csv](fantasy_agn/04592660180/hydrogen.csv), [my_sdss_model.csv](fantasy_agn/04592660180/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592660180/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592660180/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592660180/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592660180/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592660180/uvfe.csv)
- `gelato`: [docker.log](gelato/04592660180/docker.log), [my_sdss-comp.pdf](gelato/04592660180/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592660180/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592660180/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592660180/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592660180/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592660180/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.png)

## Object `04592939295`

| tool | reduced chi^2 | statistic |
|---|---:|---|
| pyqsofit | 5.066736055087005 | line_complex_reduced (reported) |
| badass | 10.16085424794107 | line_window_computed |
| fantasy_agn | 48.588464729463745 | line_window_computed |
| gelato | nan | n/a (degenerate summary) |
| gleam | 8.967142162857144 | mean_line_reduced (reported) |

_lowest &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 0 |  | 118 |  |
| OII3727 | total |  |  |  |  | 68.8 |
| Hb4861 | broad | 4.3e+03 | 1.79e+03 | 1.73e+03 | -116 |  |
| Hb4861 | narrow |  | 0 | 0 |  |  |
| Hb4861 | outflow |  | 1.79e+03 |  |  |  |
| Hb4861 | total |  |  |  |  | 1.36e+03 |
| OIII4959 | broad |  | 781 |  |  |  |
| OIII4959 | narrow | 1.12 | 0 |  | 19.9 |  |
| OIII4959 | outflow | 327 | 781 |  |  |  |
| OIII4959 | total |  |  |  |  | 59.3 |
| OIII5007 | broad |  | 0 | 707 |  |  |
| OIII5007 | narrow | 313 | 241 | 0 | 57 |  |
| OIII5007 | outflow | 195 | 380 |  |  |  |
| OIII5007 | total |  |  |  |  | 350 |
| Ha6563 | broad | 7.23e+03 | 1.25e+03 | 5.18e+03 | -330 |  |
| Ha6563 | narrow | 4.27 | 1.38e+03 | 835 |  |  |
| Ha6563 | outflow |  | 6.19e+03 |  |  |  |
| Ha6563 | total |  |  |  |  | 5.09e+03 |
| NII6585 | narrow | 745 |  |  | -230 |  |
| NII6585 | total |  |  |  |  | 103 |
| SII6718 | narrow | 0.0686 |  |  | -65.8 |  |
| SII6718 | total |  |  |  |  | 28.4 |
| SII6732 | narrow | 0.0688 |  |  | -81.2 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592939295/fit.log), [output.fits](pyqsofit/04592939295/output.fits), [qsopar.fits](pyqsofit/04592939295/qsopar.fits), [result.pdf](pyqsofit/04592939295/result.pdf), [spectrum.fits](pyqsofit/04592939295/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592939295/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592939295/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592939295/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592939295/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592939295/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592939295/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592939295/2-onur/my_sdss.fits), [docker.log](badass/04592939295/docker.log), [fit.log](badass/04592939295/fit.log), [main.py](badass/04592939295/main.py), [spectrum.pdf](badass/04592939295/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592939295/balmer.csv), [broad.csv](fantasy_agn/04592939295/broad.csv), [coronal.csv](fantasy_agn/04592939295/coronal.csv), [feII_forbidden.csv](fantasy_agn/04592939295/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592939295/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592939295/feii_IZw1.csv), [fit.log](fantasy_agn/04592939295/fit.log), [helium.csv](fantasy_agn/04592939295/helium.csv), [hydrogen.csv](fantasy_agn/04592939295/hydrogen.csv), [my_sdss_model.csv](fantasy_agn/04592939295/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592939295/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592939295/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592939295/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592939295/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592939295/uvfe.csv)
- `gelato`: [docker.log](gelato/04592939295/docker.log), [my_sdss-comp.pdf](gelato/04592939295/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592939295/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592939295/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592939295/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592939295/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592939295/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.png)

## Object `04592975881`

| tool | reduced chi^2 | statistic |
|---|---:|---|
| pyqsofit | 4.407229412125145 | line_complex_reduced (reported) |
| badass | 24.71610061485699 | line_window_computed |
| fantasy_agn | 51.72384989334458 | line_window_computed |
| gelato | nan | n/a (degenerate summary) |
| gleam | 10.499363056 | mean_line_reduced (reported) |

_lowest &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 0.213 |  | 347 |  |
| OII3727 | total |  |  |  |  | 132 |
| Hb4861 | broad | 3.35e+03 | 949 | 1.93e+03 | -185 |  |
| Hb4861 | narrow |  | 129 | 0 |  |  |
| Hb4861 | outflow |  | 1.32e+03 |  |  |  |
| Hb4861 | total |  |  |  |  | 1.4e+03 |
| OIII4959 | broad |  | 1.06e+03 |  |  |  |
| OIII4959 | narrow | 0.397 | 0 |  | 53.1 |  |
| OIII4959 | outflow | 1.27 | 1.06e+03 |  |  |  |
| OIII4959 | total |  |  |  |  | 199 |
| OIII5007 | broad |  | 0.00154 | 683 |  |  |
| OIII5007 | narrow | 735 | 569 | 551 | 152 |  |
| OIII5007 | outflow | 246 | 899 |  |  |  |
| OIII5007 | total |  |  |  |  | 805 |
| Ha6563 | broad | 9.6e+03 | 4.11e+03 | 6.94e+03 | -186 |  |
| Ha6563 | narrow | 504 | 746 | 830 |  |  |
| Ha6563 | outflow |  | 7.36e+03 |  |  |  |
| Ha6563 | total |  |  |  |  | 5.12e+03 |
| NII6585 | narrow | 3.66 |  |  | 170 |  |
| SII6718 | narrow | 59.5 |  |  | -129 |  |
| SII6732 | narrow | 59.6 |  |  | -156 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592975881/fit.log), [output.fits](pyqsofit/04592975881/output.fits), [qsopar.fits](pyqsofit/04592975881/qsopar.fits), [result.pdf](pyqsofit/04592975881/result.pdf), [spectrum.fits](pyqsofit/04592975881/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592975881/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592975881/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592975881/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592975881/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592975881/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592975881/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592975881/2-onur/my_sdss.fits), [docker.log](badass/04592975881/docker.log), [fit.log](badass/04592975881/fit.log), [main.py](badass/04592975881/main.py), [spectrum.pdf](badass/04592975881/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592975881/balmer.csv), [broad.csv](fantasy_agn/04592975881/broad.csv), [coronal.csv](fantasy_agn/04592975881/coronal.csv), [feII_forbidden.csv](fantasy_agn/04592975881/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592975881/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592975881/feii_IZw1.csv), [fit.log](fantasy_agn/04592975881/fit.log), [helium.csv](fantasy_agn/04592975881/helium.csv), [hydrogen.csv](fantasy_agn/04592975881/hydrogen.csv), [my_sdss_model.csv](fantasy_agn/04592975881/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592975881/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592975881/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592975881/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592975881/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592975881/uvfe.csv)
- `gelato`: [docker.log](gelato/04592975881/docker.log), [my_sdss-comp.pdf](gelato/04592975881/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592975881/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592975881/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592975881/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592975881/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592975881/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.png)

## Object `04592979214`

| tool | reduced chi^2 | statistic |
|---|---:|---|
| pyqsofit | 9.665266013427717 | line_complex_reduced (reported) |
| badass | 98.03965461296927 | line_window_computed |
| fantasy_agn | 196.30796550307448 | line_window_computed |
| gelato | nan | n/a (degenerate summary) |
| gleam | 21.076565823333333 | mean_line_reduced (reported) |

_lowest &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 174 |  |  |  |
| OII3727 | narrow |  | 0 |  | 113 |  |
| OII3727 | total |  |  |  |  | 380 |
| Hb4861 | broad | 2.1e+03 | 1.1e+03 | 1.25e+03 | -118 |  |
| Hb4861 | narrow |  | 47.3 | 0 |  |  |
| Hb4861 | outflow |  | 1.24e+03 |  |  |  |
| Hb4861 | total |  |  |  |  | 284 |
| OIII4959 | broad |  | 551 |  |  |  |
| OIII4959 | narrow | 1.09 | 3.11 |  | 22.6 |  |
| OIII4959 | outflow | 0.973 | 560 |  |  |  |
| OIII4959 | total |  |  |  |  | 401 |
| OIII5007 | broad |  | 0.491 | 622 |  |  |
| OIII5007 | narrow | 473 | 1.03e+03 | 0 | 64.6 |  |
| OIII5007 | outflow | 425 | 1.62e+03 |  |  |  |
| OIII5007 | total |  |  |  |  | 1.24e+03 |
| Ha6563 | broad | 5.16e+03 | 1.18e+03 | 4.34e+03 | -151 |  |
| Ha6563 | narrow | 21.5 | 753 | 348 |  |  |
| Ha6563 | outflow |  | 4.44e+03 |  |  |  |
| Ha6563 | total |  |  |  |  | 1.87e+03 |
| NII6585 | narrow | 105 |  |  | 132 |  |
| NII6585 | total |  |  |  |  | 253 |
| SII6718 | narrow | 161 |  |  | -86 |  |
| SII6718 | total |  |  |  |  | 157 |
| SII6732 | narrow | 161 |  |  | -81.2 |  |
| SII6732 | total |  |  |  |  | 137 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592979214/fit.log), [output.fits](pyqsofit/04592979214/output.fits), [qsopar.fits](pyqsofit/04592979214/qsopar.fits), [result.pdf](pyqsofit/04592979214/result.pdf), [spectrum.fits](pyqsofit/04592979214/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592979214/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592979214/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592979214/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592979214/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592979214/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592979214/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592979214/2-onur/my_sdss.fits), [docker.log](badass/04592979214/docker.log), [fit.log](badass/04592979214/fit.log), [main.py](badass/04592979214/main.py), [spectrum.pdf](badass/04592979214/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592979214/balmer.csv), [broad.csv](fantasy_agn/04592979214/broad.csv), [coronal.csv](fantasy_agn/04592979214/coronal.csv), [feII_forbidden.csv](fantasy_agn/04592979214/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592979214/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592979214/feii_IZw1.csv), [fit.log](fantasy_agn/04592979214/fit.log), [helium.csv](fantasy_agn/04592979214/helium.csv), [hydrogen.csv](fantasy_agn/04592979214/hydrogen.csv), [my_sdss_model.csv](fantasy_agn/04592979214/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592979214/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592979214/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592979214/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592979214/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592979214/uvfe.csv)
- `gelato`: [docker.log](gelato/04592979214/docker.log), [my_sdss-comp.pdf](gelato/04592979214/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592979214/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592979214/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592979214/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592979214/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592979214/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.png)

## Object `06872228427`

| tool | reduced chi^2 | statistic |
|---|---:|---|
| pyqsofit | 13.245184409694872 | line_complex_reduced (reported) |
| badass | 17.58427776511103 | line_window_computed |
| fantasy_agn | 87.1353167167565 | line_window_computed |
| gelato | nan | n/a (degenerate summary) |
| gleam | 2.9561540149999996 | mean_line_reduced (reported) |

_lowest &chi;&sup2;: **pyqsofit**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 39 |  |  |  |
| OII3727 | narrow |  | 0.000669 |  | -72.2 |  |
| OII3727 | total |  |  |  |  | 103 |
| Hb4861 | broad | 601 | 0.00727 | 197 | 74.2 |  |
| Hb4861 | narrow |  | 42.9 | 0 |  |  |
| Hb4861 | outflow |  | 111 |  |  |  |
| Hb4861 | total |  |  |  |  | 47.6 |
| OIII4959 | broad |  | 294 |  |  |  |
| OIII4959 | narrow | 1.09 | 0 |  | -19.1 |  |
| OIII4959 | outflow | 0.369 | 294 |  |  |  |
| OIII4959 | total |  |  |  |  | 143 |
| OIII5007 | broad |  | 0.0463 | 144 |  |  |
| OIII5007 | narrow | 385 | 375 | 394 | -54.6 |  |
| OIII5007 | outflow | 0.442 | 375 |  |  |  |
| OIII5007 | total |  |  |  |  | 418 |
| Ha6563 | broad | 1.51e+03 | 1.33e+03 | 1.45e+03 | 302 |  |
| Ha6563 | narrow | 0.00403 | 16.5 | 0 |  |  |
| Ha6563 | outflow |  | 1.4e+03 |  |  |  |
| Ha6563 | total |  |  |  |  | 988 |
| NII6585 | narrow | 164 |  |  | 242 |  |
| NII6585 | total |  |  |  |  | 152 |
| SII6718 | narrow | 57.4 |  |  | 230 |  |
| SII6718 | total |  |  |  |  | 53.4 |
| SII6732 | narrow | 57.5 |  |  | 244 |  |
| SII6732 | total |  |  |  |  | 59.7 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/06872228427/fit.log), [output.fits](pyqsofit/06872228427/output.fits), [qsopar.fits](pyqsofit/06872228427/qsopar.fits), [result.pdf](pyqsofit/06872228427/result.pdf), [spectrum.fits](pyqsofit/06872228427/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/06872228427/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/06872228427/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/06872228427/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/06872228427/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/06872228427/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/06872228427/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/06872228427/2-onur/my_sdss.fits), [docker.log](badass/06872228427/docker.log), [fit.log](badass/06872228427/fit.log), [main.py](badass/06872228427/main.py), [spectrum.pdf](badass/06872228427/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/06872228427/balmer.csv), [broad.csv](fantasy_agn/06872228427/broad.csv), [coronal.csv](fantasy_agn/06872228427/coronal.csv), [feII_forbidden.csv](fantasy_agn/06872228427/feII_forbidden.csv), [feII_model.csv](fantasy_agn/06872228427/feII_model.csv), [feii_IZw1.csv](fantasy_agn/06872228427/feii_IZw1.csv), [fit.log](fantasy_agn/06872228427/fit.log), [helium.csv](fantasy_agn/06872228427/helium.csv), [hydrogen.csv](fantasy_agn/06872228427/hydrogen.csv), [narrow_basic.csv](fantasy_agn/06872228427/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/06872228427/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/06872228427/oiii_nii.csv), [uvfe.csv](fantasy_agn/06872228427/uvfe.csv)
- `gelato`: [docker.log](gelato/06872228427/docker.log), [my_sdss-comp.pdf](gelato/06872228427/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/06872228427/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/06872228427/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/06872228427/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/06872228427/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/06872228427/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.png)
