# Cross-tool AGN emission-line comparison

## Object `04545183216`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 255.4406704023552 | 1.1860206209127893 | line_complex_reduced (reported) |
| badass | 4.5592306304680665 | 1.9500338676528068 | line_window_computed |
| fantasy_agn | 207.95211344367428 | 51.68606453262763 | line_window_computed |
| gelato | 35.11333194841261 | 29.057939789326014 | global_reduced (reported) |
| gleam | 389.7649538386702 | 11.671924680833333 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 0 |  | 134 | 35.4 |
| Hb4861 | broad | 3.16e+03 | 1.86e+03 | 1.41e+03 | 486 |  |
| Hb4861 | narrow |  | 0 | 0 |  | 288 |
| Hb4861 | outflow |  | 1.86e+03 |  |  |  |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 73.6 | 0 |  | 34.8 | 30.9 |
| OIII4959 | outflow | 108 | 0 |  |  |  |
| OIII5007 | broad |  | 0 | 320 |  |  |
| OIII5007 | narrow | 226 | 0 | 138 | 99.5 | 168 |
| OIII5007 | outflow | 332 | 0 |  |  |  |
| Ha6563 | broad | 1.08e+04 | 5.3e+03 | 3.5e+03 | 2.29e+03 |  |
| Ha6563 | narrow | 458 | 518 | 191 |  | 5.25e+03 |
| Ha6563 | outflow |  | 7.78e+03 |  |  |  |
| NII6585 | narrow | 0.263 |  |  | 2.27e+03 | -657 |
| SII6718 | narrow | 7.33 |  |  | 112 |  |
| SII6732 | narrow | 7.35 |  |  | -69 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04545183216/fit.log), [output.fits](pyqsofit/04545183216/output.fits), [pyqsofit_model.csv](pyqsofit/04545183216/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04545183216/qsopar.fits), [result.pdf](pyqsofit/04545183216/result.pdf), [spectrum.fits](pyqsofit/04545183216/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04545183216/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04545183216/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04545183216/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04545183216/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04545183216/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04545183216/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04545183216/2-onur/my_sdss.fits), [docker.log](badass/04545183216/docker.log), [fit.log](badass/04545183216/fit.log), [main.py](badass/04545183216/main.py), [spectrum.pdf](badass/04545183216/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04545183216/balmer.csv), [broad.csv](fantasy_agn/04545183216/broad.csv), [coronal.csv](fantasy_agn/04545183216/coronal.csv), [docker.log](fantasy_agn/04545183216/docker.log), [feII_forbidden.csv](fantasy_agn/04545183216/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04545183216/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04545183216/feii_IZw1.csv), [fit.log](fantasy_agn/04545183216/fit.log), [helium.csv](fantasy_agn/04545183216/helium.csv), [hydrogen.csv](fantasy_agn/04545183216/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04545183216/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04545183216/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04545183216/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04545183216/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04545183216/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04545183216/oiii_nii.csv), [uvfe.csv](fantasy_agn/04545183216/uvfe.csv)
- `gelato`: [docker.log](gelato/04545183216/docker.log), [my_sdss-comp.pdf](gelato/04545183216/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04545183216/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04545183216/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04545183216/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04545183216/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04545183216/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04545183216/linefits.sdss.sdss.fiber1.001.png)

## Object `04570362657`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 117.01068572458328 | 1.0992690954661393 | line_complex_reduced (reported) |
| badass | 10.065450899328091 | 4.804092572498654 | line_window_computed |
| fantasy_agn | 87.25887042210574 | 64.61012365351273 | line_window_computed |
| gelato | 13.152115996324914 | 14.21934918894193 | global_reduced (reported) |
| gleam | 138.57354914643435 | 4.775103758749999 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 35.7 |  | 73.7 | 58.2 |
| Hb4861 | broad | 1.24e+03 | 0 | 1.13e+03 | -52 | 824 |
| Hb4861 | narrow |  | 608 | 0 |  | 13.5 |
| Hb4861 | outflow |  | 960 |  |  |  |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 68.2 | 63.1 |  | 122 | 23.5 |
| OIII4959 | outflow | 13.9 | 92.7 |  |  |  |
| OIII5007 | broad |  | 0 | 138 |  |  |
| OIII5007 | narrow | 210 | 186 | 226 | 349 | 265 |
| OIII5007 | outflow | 42.9 | 279 |  |  |  |
| Ha6563 | broad | 5.31e+03 | 3.88e+03 | 4.36e+03 | 1.45e+03 |  |
| Ha6563 | narrow | 773 | 0 | 0 |  | 3.93e+03 |
| Ha6563 | outflow |  | 3.88e+03 |  |  |  |
| NII6585 | narrow | 0.862 |  |  | 1.02e+03 | 63.9 |
| SII6718 | narrow | 22.1 |  |  | 76.2 | 44.1 |
| SII6732 | narrow | 22.2 |  |  | 63.2 | 26.2 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04570362657/fit.log), [output.fits](pyqsofit/04570362657/output.fits), [pyqsofit_model.csv](pyqsofit/04570362657/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04570362657/qsopar.fits), [result.pdf](pyqsofit/04570362657/result.pdf), [spectrum.fits](pyqsofit/04570362657/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04570362657/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04570362657/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04570362657/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04570362657/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04570362657/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04570362657/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04570362657/2-onur/my_sdss.fits), [docker.log](badass/04570362657/docker.log), [fit.log](badass/04570362657/fit.log), [main.py](badass/04570362657/main.py), [spectrum.pdf](badass/04570362657/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04570362657/balmer.csv), [broad.csv](fantasy_agn/04570362657/broad.csv), [coronal.csv](fantasy_agn/04570362657/coronal.csv), [docker.log](fantasy_agn/04570362657/docker.log), [feII_forbidden.csv](fantasy_agn/04570362657/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04570362657/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04570362657/feii_IZw1.csv), [fit.log](fantasy_agn/04570362657/fit.log), [helium.csv](fantasy_agn/04570362657/helium.csv), [hydrogen.csv](fantasy_agn/04570362657/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04570362657/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04570362657/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04570362657/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04570362657/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04570362657/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04570362657/oiii_nii.csv), [uvfe.csv](fantasy_agn/04570362657/uvfe.csv)
- `gelato`: [docker.log](gelato/04570362657/docker.log), [my_sdss-comp.pdf](gelato/04570362657/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04570362657/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04570362657/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04570362657/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04570362657/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04570362657/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04570362657/linefits.sdss.sdss.fiber1.001.png)

## Object `04570493016`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 99.26598012729806 | 12.606820476384971 | line_complex_reduced (reported) |
| badass | 33.193060669546384 | 15.967216195935269 | line_window_computed |
| fantasy_agn | 92.55865814376992 | 195.49937665900123 | line_window_computed |
| gelato | 76.09198526821805 | 42.41432786162395 | global_reduced (reported) |
| gleam | 290.48140972444065 | 249.67912097923076 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 0 |  | 332 | 83.1 |
| Hb4861 | broad | 6.52e+03 | 1.22e+03 | 3.29e+03 | 849 | 204 |
| Hb4861 | narrow |  | 1.63e+03 | 0 |  | 2.84e+03 |
| Hb4861 | outflow |  | 3.73e+03 |  |  |  |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 297 | 276 |  | 301 | 244 |
| OIII4959 | outflow | 23.5 | 426 |  |  |  |
| OIII5007 | broad |  | 0 | 1e+03 |  |  |
| OIII5007 | narrow | 913 | 831 | 0 | 859 | 1.07e+03 |
| OIII5007 | outflow | 72.5 | 1.28e+03 |  |  |  |
| Ha6563 | broad | 1.58e+04 | 4.17e+03 | 6.94e+03 | 5.6e+03 |  |
| Ha6563 | narrow | 1.41e+03 | 2.75e+03 | 831 |  | 1.1e+04 |
| Ha6563 | outflow |  | 1.3e+04 |  |  |  |
| NII6585 | narrow | 7.42 |  |  | 5.28e+03 |  |
| SII6718 | narrow | 10.2 |  |  | 233 |  |
| SII6732 | narrow | 10.2 |  |  | 44.4 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04570493016/fit.log), [output.fits](pyqsofit/04570493016/output.fits), [pyqsofit_model.csv](pyqsofit/04570493016/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04570493016/qsopar.fits), [result.pdf](pyqsofit/04570493016/result.pdf), [spectrum.fits](pyqsofit/04570493016/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04570493016/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04570493016/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04570493016/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04570493016/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04570493016/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04570493016/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04570493016/2-onur/my_sdss.fits), [docker.log](badass/04570493016/docker.log), [fit.log](badass/04570493016/fit.log), [main.py](badass/04570493016/main.py), [spectrum.pdf](badass/04570493016/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04570493016/balmer.csv), [broad.csv](fantasy_agn/04570493016/broad.csv), [coronal.csv](fantasy_agn/04570493016/coronal.csv), [docker.log](fantasy_agn/04570493016/docker.log), [feII_forbidden.csv](fantasy_agn/04570493016/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04570493016/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04570493016/feii_IZw1.csv), [fit.log](fantasy_agn/04570493016/fit.log), [helium.csv](fantasy_agn/04570493016/helium.csv), [hydrogen.csv](fantasy_agn/04570493016/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04570493016/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04570493016/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04570493016/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04570493016/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04570493016/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04570493016/oiii_nii.csv), [uvfe.csv](fantasy_agn/04570493016/uvfe.csv)
- `gelato`: [docker.log](gelato/04570493016/docker.log), [my_sdss-comp.pdf](gelato/04570493016/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04570493016/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04570493016/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04570493016/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04570493016/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04570493016/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04570493016/linefits.sdss.sdss.fiber1.001.png)

## Object `04592503068`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 58.98620313549449 | 24.849459699582255 | line_complex_reduced (reported) |
| badass | 63.03386102840504 | 35.74296161109063 | line_window_computed |
| fantasy_agn | 65.89306066593872 | 85.65042088687622 | line_window_computed |
| gelato | 25.194552839653074 | 14.545427312175295 | global_reduced (reported) |
| gleam | 51.01387180205962 | 4.061987535714286 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 84.3 |  | 143 | 126 |
| Hb4861 | broad | 1.34e+03 | 85.9 | 705 | 102 |  |
| Hb4861 | narrow |  | 301 | 0 |  | 170 |
| Hb4861 | outflow |  | 550 |  |  |  |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 144 | 176 |  | 171 | 188 |
| OIII4959 | outflow | 68.7 | 278 |  |  |  |
| OIII5007 | broad |  | 0 | 675 |  |  |
| OIII5007 | narrow | 444 | 529 | 0 | 487 | 675 |
| OIII5007 | outflow | 212 | 837 |  |  |  |
| Ha6563 | broad | 3.7e+03 | 0 | 3.42e+03 | 1.19e+03 | 368 |
| Ha6563 | narrow | 456 | 941 | 0 |  | 2.74e+03 |
| Ha6563 | outflow |  | 3.2e+03 |  |  |  |
| NII6585 | narrow | 0.862 |  |  | 1.45e+03 | 333 |
| SII6718 | narrow | 59.1 |  |  | 112 | 85.3 |
| SII6732 | narrow | 59.3 |  |  | 75.6 | 50.9 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592503068/fit.log), [output.fits](pyqsofit/04592503068/output.fits), [pyqsofit_model.csv](pyqsofit/04592503068/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592503068/qsopar.fits), [result.pdf](pyqsofit/04592503068/result.pdf), [spectrum.fits](pyqsofit/04592503068/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592503068/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592503068/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592503068/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592503068/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592503068/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592503068/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592503068/2-onur/my_sdss.fits), [docker.log](badass/04592503068/docker.log), [fit.log](badass/04592503068/fit.log), [main.py](badass/04592503068/main.py), [spectrum.pdf](badass/04592503068/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592503068/balmer.csv), [broad.csv](fantasy_agn/04592503068/broad.csv), [coronal.csv](fantasy_agn/04592503068/coronal.csv), [docker.log](fantasy_agn/04592503068/docker.log), [feII_forbidden.csv](fantasy_agn/04592503068/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592503068/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592503068/feii_IZw1.csv), [fit.log](fantasy_agn/04592503068/fit.log), [helium.csv](fantasy_agn/04592503068/helium.csv), [hydrogen.csv](fantasy_agn/04592503068/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592503068/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592503068/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592503068/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592503068/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592503068/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592503068/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592503068/uvfe.csv)
- `gelato`: [docker.log](gelato/04592503068/docker.log), [my_sdss-comp.pdf](gelato/04592503068/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592503068/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592503068/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592503068/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592503068/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592503068/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592503068/linefits.sdss.sdss.fiber1.001.png)

## Object `04592517882`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 153.16916607542097 | 10.955323972157792 | line_complex_reduced (reported) |
| badass | 7.359427298158567 | 3.5735456939756176 | line_window_computed |
| fantasy_agn | 146.71771723875858 | 9.273283692099355 | line_window_computed |
| gelato | 16.708445632022624 | 11.367535354304394 | global_reduced (reported) |
| gleam | 335.2422772685428 | 14.74600092090909 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 4.74 |  | 25.5 | 18.8 |
| Hb4861 | broad | 563 | 0 | 580 | 196 |  |
| Hb4861 | narrow |  | 289 | 0 |  | 332 |
| Hb4861 | outflow |  | 445 |  |  |  |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 1.39 | 28.1 |  | 17.4 | -40.4 |
| OIII4959 | outflow | 0.376 | 44 |  |  |  |
| OIII5007 | broad |  | 0 | 224 |  |  |
| OIII5007 | narrow | 4.27 | 82.8 | 0 | 49.8 |  |
| OIII5007 | outflow | 1.16 | 132 |  |  |  |
| Ha6563 | broad | 2.21e+03 | 556 | 1.47e+03 | 1.2e+03 |  |
| Ha6563 | narrow | 776 | 446 | 332 |  | 3.49e+03 |
| Ha6563 | outflow |  | 1.69e+03 |  |  |  |
| NII6585 | narrow | 0.0636 |  |  | 370 | -1.17e+03 |
| SII6718 | narrow | 0.433 |  |  | 14.1 | 25.5 |
| SII6732 | narrow | 0.434 |  |  | -23.5 |  |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592517882/fit.log), [output.fits](pyqsofit/04592517882/output.fits), [pyqsofit_model.csv](pyqsofit/04592517882/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592517882/qsopar.fits), [result.pdf](pyqsofit/04592517882/result.pdf), [spectrum.fits](pyqsofit/04592517882/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592517882/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592517882/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592517882/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592517882/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592517882/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592517882/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592517882/2-onur/my_sdss.fits), [docker.log](badass/04592517882/docker.log), [fit.log](badass/04592517882/fit.log), [main.py](badass/04592517882/main.py), [spectrum.pdf](badass/04592517882/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592517882/balmer.csv), [broad.csv](fantasy_agn/04592517882/broad.csv), [coronal.csv](fantasy_agn/04592517882/coronal.csv), [docker.log](fantasy_agn/04592517882/docker.log), [feII_forbidden.csv](fantasy_agn/04592517882/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592517882/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592517882/feii_IZw1.csv), [fit.log](fantasy_agn/04592517882/fit.log), [helium.csv](fantasy_agn/04592517882/helium.csv), [hydrogen.csv](fantasy_agn/04592517882/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592517882/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592517882/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592517882/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592517882/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592517882/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592517882/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592517882/uvfe.csv)
- `gelato`: [docker.log](gelato/04592517882/docker.log), [my_sdss-comp.pdf](gelato/04592517882/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592517882/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592517882/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592517882/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592517882/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592517882/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592517882/linefits.sdss.sdss.fiber1.001.png)

## Object `04592660180`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 152.74087875741864 | 0.8047403549606946 | line_complex_reduced (reported) |
| badass | 13.946211003078746 | 4.947791781143592 | line_window_computed |
| fantasy_agn | 123.84802724058109 | 46.598857678661176 | line_window_computed |
| gelato | 43.109374197119514 | 24.692054979842553 | global_reduced (reported) |
| gleam | 195.20190805486243 | 1.5675529757142856 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 39.7 |  | 79.7 | 36.3 |
| Hb4861 | broad | 1.56e+03 | 0 | 1.11e+03 | 369 |  |
| Hb4861 | narrow |  | 666 | 0 |  | 635 |
| Hb4861 | outflow |  | 1.05e+03 |  |  |  |
| OIII4959 | broad |  | 144 |  |  |  |
| OIII4959 | narrow | 87.5 | 0 |  | 68.9 | 55.8 |
| OIII4959 | outflow | 34.7 | 144 |  |  |  |
| OIII5007 | broad |  | 432 | 351 |  |  |
| OIII5007 | narrow | 269 | 0 | 0 | 197 | 308 |
| OIII5007 | outflow | 107 | 432 |  |  |  |
| Ha6563 | broad | 5.78e+03 | 2.15e+03 | 3.49e+03 | 2.07e+03 | 3.42e+03 |
| Ha6563 | narrow | 1.06e+03 | 1.02e+03 | 758 |  | 98.9 |
| Ha6563 | outflow |  | 4.94e+03 |  |  |  |
| NII6585 | narrow | 3.31 |  |  | 1.79e+03 | 45 |
| SII6718 | narrow | 28.7 |  |  | 65.5 | 28.2 |
| SII6732 | narrow | 28.7 |  |  | 68.1 | 19.1 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592660180/fit.log), [output.fits](pyqsofit/04592660180/output.fits), [pyqsofit_model.csv](pyqsofit/04592660180/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592660180/qsopar.fits), [result.pdf](pyqsofit/04592660180/result.pdf), [spectrum.fits](pyqsofit/04592660180/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592660180/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592660180/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592660180/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592660180/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592660180/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592660180/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592660180/2-onur/my_sdss.fits), [docker.log](badass/04592660180/docker.log), [fit.log](badass/04592660180/fit.log), [main.py](badass/04592660180/main.py), [spectrum.pdf](badass/04592660180/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592660180/balmer.csv), [broad.csv](fantasy_agn/04592660180/broad.csv), [coronal.csv](fantasy_agn/04592660180/coronal.csv), [docker.log](fantasy_agn/04592660180/docker.log), [feII_forbidden.csv](fantasy_agn/04592660180/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592660180/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592660180/feii_IZw1.csv), [fit.log](fantasy_agn/04592660180/fit.log), [helium.csv](fantasy_agn/04592660180/helium.csv), [hydrogen.csv](fantasy_agn/04592660180/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592660180/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592660180/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592660180/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592660180/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592660180/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592660180/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592660180/uvfe.csv)
- `gelato`: [docker.log](gelato/04592660180/docker.log), [my_sdss-comp.pdf](gelato/04592660180/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592660180/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592660180/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592660180/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592660180/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592660180/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592660180/linefits.sdss.sdss.fiber1.001.png)

## Object `04592939295`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 32.437927023157165 | 5.59123083454728 | line_complex_reduced (reported) |
| badass | 15.29564418438009 | 7.434035307202122 | line_window_computed |
| fantasy_agn | 40.04208104178897 | 48.29251605837722 | line_window_computed |
| gelato | 39.14752068797436 | 21.339203092698945 | global_reduced (reported) |
| gleam | 55.72127561043142 | 2.9242077183333333 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 285 |  |  |  |
| OII3727 | narrow |  | 38.8 |  | 170 | 61.5 |
| Hb4861 | broad | 2.1e+03 | 549 | 1.69e+03 | 412 | 1.15e+03 |
| Hb4861 | narrow |  | 822 | 0 |  | 40.4 |
| Hb4861 | outflow |  | 1.82e+03 |  |  |  |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 101 | 96.9 |  | 73.5 | 79.1 |
| OIII4959 | outflow | 31 | 153 |  |  |  |
| OIII5007 | broad |  | 0 | 733 |  |  |
| OIII5007 | narrow | 311 | 292 | 0 | 210 | 341 |
| OIII5007 | outflow | 95.3 | 461 |  |  |  |
| Ha6563 | broad | 6.95e+03 | 675 | 5.48e+03 | 2.07e+03 | 268 |
| Ha6563 | narrow | 4.27 | 1.37e+03 | 833 |  | 4.55e+03 |
| Ha6563 | outflow |  | 6.18e+03 |  |  |  |
| NII6585 | narrow | 746 |  |  | 2.57e+03 | 190 |
| SII6718 | narrow | 1.89 |  |  | 112 | 39.5 |
| SII6732 | narrow | 1.9 |  |  | 71.2 | 20.9 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592939295/fit.log), [output.fits](pyqsofit/04592939295/output.fits), [pyqsofit_model.csv](pyqsofit/04592939295/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592939295/qsopar.fits), [result.pdf](pyqsofit/04592939295/result.pdf), [spectrum.fits](pyqsofit/04592939295/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592939295/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592939295/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592939295/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592939295/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592939295/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592939295/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592939295/2-onur/my_sdss.fits), [docker.log](badass/04592939295/docker.log), [fit.log](badass/04592939295/fit.log), [main.py](badass/04592939295/main.py), [spectrum.pdf](badass/04592939295/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592939295/balmer.csv), [broad.csv](fantasy_agn/04592939295/broad.csv), [coronal.csv](fantasy_agn/04592939295/coronal.csv), [docker.log](fantasy_agn/04592939295/docker.log), [feII_forbidden.csv](fantasy_agn/04592939295/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592939295/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592939295/feii_IZw1.csv), [fit.log](fantasy_agn/04592939295/fit.log), [helium.csv](fantasy_agn/04592939295/helium.csv), [hydrogen.csv](fantasy_agn/04592939295/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592939295/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592939295/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592939295/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592939295/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592939295/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592939295/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592939295/uvfe.csv)
- `gelato`: [docker.log](gelato/04592939295/docker.log), [my_sdss-comp.pdf](gelato/04592939295/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592939295/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592939295/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592939295/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592939295/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592939295/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592939295/linefits.sdss.sdss.fiber1.001.png)

## Object `04592975881`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 110.13596349426044 | 8.234895963295743 | line_complex_reduced (reported) |
| badass | 7.1667501973608045 | 3.1642624557118957 | line_window_computed |
| fantasy_agn | 93.47515768731398 | 50.95388790700432 | line_window_computed |
| gelato | 44.51153977396583 | 30.904311787389556 | global_reduced (reported) |
| gleam | 141.75848052276802 | 4.744971415714285 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **badass**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 106 |  | 157 | 124 |
| Hb4861 | broad | 2.14e+03 | 437 | 1.82e+03 | 410 |  |
| Hb4861 | narrow |  | 623 | 0 |  | 451 |
| Hb4861 | outflow |  | 1.75e+03 |  |  |  |
| OIII4959 | broad |  | 88.6 |  |  |  |
| OIII4959 | narrow | 186 | 201 |  | 193 | 225 |
| OIII4959 | outflow | 98.3 | 290 |  |  |  |
| OIII5007 | broad |  | 266 | 843 |  |  |
| OIII5007 | narrow | 572 | 605 | 555 | 550 | 786 |
| OIII5007 | outflow | 303 | 871 |  |  |  |
| Ha6563 | broad | 9.42e+03 | 3.61e+03 | 6.94e+03 | 2.41e+03 | 3.58e+03 |
| Ha6563 | narrow | 595 | 1.01e+03 | 828 |  | 133 |
| Ha6563 | outflow |  | 7.58e+03 |  |  |  |
| NII6585 | narrow | 6.26 |  |  | 2.39e+03 | 108 |
| SII6718 | narrow | 58.5 |  |  | 199 | 73.1 |
| SII6732 | narrow | 58.7 |  |  | 48.6 | 32.2 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592975881/fit.log), [output.fits](pyqsofit/04592975881/output.fits), [pyqsofit_model.csv](pyqsofit/04592975881/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592975881/qsopar.fits), [result.pdf](pyqsofit/04592975881/result.pdf), [spectrum.fits](pyqsofit/04592975881/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592975881/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592975881/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592975881/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592975881/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592975881/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592975881/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592975881/2-onur/my_sdss.fits), [docker.log](badass/04592975881/docker.log), [fit.log](badass/04592975881/fit.log), [main.py](badass/04592975881/main.py), [spectrum.pdf](badass/04592975881/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592975881/balmer.csv), [broad.csv](fantasy_agn/04592975881/broad.csv), [coronal.csv](fantasy_agn/04592975881/coronal.csv), [docker.log](fantasy_agn/04592975881/docker.log), [feII_forbidden.csv](fantasy_agn/04592975881/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592975881/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592975881/feii_IZw1.csv), [fit.log](fantasy_agn/04592975881/fit.log), [helium.csv](fantasy_agn/04592975881/helium.csv), [hydrogen.csv](fantasy_agn/04592975881/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592975881/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592975881/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592975881/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592975881/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592975881/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592975881/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592975881/uvfe.csv)
- `gelato`: [docker.log](gelato/04592975881/docker.log), [my_sdss-comp.pdf](gelato/04592975881/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592975881/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592975881/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592975881/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592975881/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592975881/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592975881/linefits.sdss.sdss.fiber1.001.png)

## Object `04592979214`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 50.39172518103782 | 6.339053969802422 | line_complex_reduced (reported) |
| badass | 158.11786880674202 | 97.19217471552965 | line_window_computed |
| fantasy_agn | 54.21624498905932 | 238.58435701616023 | line_window_computed |
| gelato | 18.958317197007297 | 10.474329668111713 | global_reduced (reported) |
| gleam | 29.842510487631156 | 4.352540801666668 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 11.5 |  |  |  |
| OII3727 | narrow |  | 402 |  | 406 | 380 |
| Hb4861 | broad | 2.27e+03 | 377 | 1.25e+03 | -67.4 | 2.01e+03 |
| Hb4861 | narrow |  | 508 | 0 |  | 155 |
| Hb4861 | outflow |  | 1.16e+03 |  |  |  |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 62.9 | 313 |  | 439 | 401 |
| OIII4959 | outflow | 91.7 | 495 |  |  |  |
| OIII5007 | broad |  | 0 | 554 |  |  |
| OIII5007 | narrow | 193 | 942 | 0 | 1.25e+03 | 1.24e+03 |
| OIII5007 | outflow | 282 | 1.49e+03 |  |  |  |
| Ha6563 | broad | 4.96e+03 | 1.43e+03 | 4.34e+03 | 540 | 4.16e+03 |
| Ha6563 | narrow | 21.2 | 847 | 360 |  | 523 |
| Ha6563 | outflow |  | 4.83e+03 |  |  |  |
| NII6585 | narrow | 103 |  |  | 179 | 125 |
| SII6718 | narrow | 160 |  |  | 162 | 157 |
| SII6732 | narrow | 160 |  |  | 139 | 137 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/04592979214/fit.log), [output.fits](pyqsofit/04592979214/output.fits), [pyqsofit_model.csv](pyqsofit/04592979214/pyqsofit_model.csv), [qsopar.fits](pyqsofit/04592979214/qsopar.fits), [result.pdf](pyqsofit/04592979214/result.pdf), [spectrum.fits](pyqsofit/04592979214/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/04592979214/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/04592979214/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/04592979214/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/04592979214/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/04592979214/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/04592979214/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/04592979214/2-onur/my_sdss.fits), [docker.log](badass/04592979214/docker.log), [fit.log](badass/04592979214/fit.log), [main.py](badass/04592979214/main.py), [spectrum.pdf](badass/04592979214/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/04592979214/balmer.csv), [broad.csv](fantasy_agn/04592979214/broad.csv), [coronal.csv](fantasy_agn/04592979214/coronal.csv), [docker.log](fantasy_agn/04592979214/docker.log), [feII_forbidden.csv](fantasy_agn/04592979214/feII_forbidden.csv), [feII_model.csv](fantasy_agn/04592979214/feII_model.csv), [feii_IZw1.csv](fantasy_agn/04592979214/feii_IZw1.csv), [fit.log](fantasy_agn/04592979214/fit.log), [helium.csv](fantasy_agn/04592979214/helium.csv), [hydrogen.csv](fantasy_agn/04592979214/hydrogen.csv), [my_sdss.pdf](fantasy_agn/04592979214/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/04592979214/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/04592979214/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/04592979214/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/04592979214/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/04592979214/oiii_nii.csv), [uvfe.csv](fantasy_agn/04592979214/uvfe.csv)
- `gelato`: [docker.log](gelato/04592979214/docker.log), [my_sdss-comp.pdf](gelato/04592979214/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/04592979214/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/04592979214/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/04592979214/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/04592979214/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/04592979214/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/04592979214/linefits.sdss.sdss.fiber1.001.png)

## Object `06872228427`

| tool | common reduced chi^2 | own reduced chi^2 | statistic |
|---|---:|---:|---|
| pyqsofit | 29.249537853759605 | 14.16008482702199 | line_complex_reduced (reported) |
| badass | 72.14890253160762 | 48.07694425213223 | line_window_computed |
| fantasy_agn | 61.14404674250307 | 89.6887359724181 | line_window_computed |
| gelato | 12.737708403955493 | 5.316662100051872 | global_reduced (reported) |
| gleam | 48.10847358802781 | 0.8502886257142859 | mean_line_reduced (reported) |

_lowest common &chi;&sup2;: **gelato**_

| line | component | pyqsofit | badass | fantasy_agn | gelato | gleam |
|---|---|---:|---:|---:|---:|---:|
| OII3727 | broad |  | 0 |  |  |  |
| OII3727 | narrow |  | 113 |  | 107 | 103 |
| Hb4861 | broad | 434 | 130 | 150 | -28.1 |  |
| Hb4861 | narrow |  | 39.3 | 0 |  | 47.6 |
| Hb4861 | outflow |  | 191 |  |  |  |
| OIII4959 | broad |  | 0 |  |  |  |
| OIII4959 | narrow | 68.6 | 116 |  | 145 | 143 |
| OIII4959 | outflow | 44.6 | 184 |  |  |  |
| OIII5007 | broad |  | 0 | 20.6 |  |  |
| OIII5007 | narrow | 211 | 350 | 413 | 414 | 418 |
| OIII5007 | outflow | 137 | 554 |  |  |  |
| Ha6563 | broad | 1.51e+03 | 216 | 1.45e+03 | 257 | 932 |
| Ha6563 | narrow | 0.0101 | 335 | 0 |  | 172 |
| Ha6563 | outflow |  | 1.56e+03 |  |  |  |
| NII6585 | narrow | 164 |  |  | 259 | 192 |
| SII6718 | narrow | 57.4 |  |  | 77.3 | 58.5 |
| SII6732 | narrow | 57.6 |  |  | 62.8 | 51.1 |

_flux in 1e-17 erg s-1 cm-2_

**products:**
- `pyqsofit`: [fit.log](pyqsofit/06872228427/fit.log), [output.fits](pyqsofit/06872228427/output.fits), [pyqsofit_model.csv](pyqsofit/06872228427/pyqsofit_model.csv), [qsopar.fits](pyqsofit/06872228427/qsopar.fits), [result.pdf](pyqsofit/06872228427/result.pdf), [spectrum.fits](pyqsofit/06872228427/spectrum.fits)
- `badass`: [2-onur_bestfit.html](badass/06872228427/2-onur/MCMC_output_1/2-onur_bestfit.html), [input_spectrum.pdf](badass/06872228427/2-onur/MCMC_output_1/input_spectrum.pdf), [best_model_components.fits](badass/06872228427/2-onur/MCMC_output_1/log/best_model_components.fits), [log_file.txt](badass/06872228427/2-onur/MCMC_output_1/log/log_file.txt), [par_table.fits](badass/06872228427/2-onur/MCMC_output_1/log/par_table.fits), [max_likelihood_fit.pdf](badass/06872228427/2-onur/MCMC_output_1/max_likelihood_fit.pdf), [my_sdss.fits](badass/06872228427/2-onur/my_sdss.fits), [docker.log](badass/06872228427/docker.log), [fit.log](badass/06872228427/fit.log), [main.py](badass/06872228427/main.py), [spectrum.pdf](badass/06872228427/spectrum.pdf)
- `fantasy_agn`: [balmer.csv](fantasy_agn/06872228427/balmer.csv), [broad.csv](fantasy_agn/06872228427/broad.csv), [coronal.csv](fantasy_agn/06872228427/coronal.csv), [docker.log](fantasy_agn/06872228427/docker.log), [feII_forbidden.csv](fantasy_agn/06872228427/feII_forbidden.csv), [feII_model.csv](fantasy_agn/06872228427/feII_model.csv), [feii_IZw1.csv](fantasy_agn/06872228427/feii_IZw1.csv), [fit.log](fantasy_agn/06872228427/fit.log), [helium.csv](fantasy_agn/06872228427/helium.csv), [hydrogen.csv](fantasy_agn/06872228427/hydrogen.csv), [my_sdss.pdf](fantasy_agn/06872228427/my_sdss.pdf), [my_sdss_model.csv](fantasy_agn/06872228427/my_sdss_model.csv), [my_sdss_pars.json](fantasy_agn/06872228427/my_sdss_pars.json), [narrow_basic.csv](fantasy_agn/06872228427/narrow_basic.csv), [narrow_plus.csv](fantasy_agn/06872228427/narrow_plus.csv), [oiii_nii.csv](fantasy_agn/06872228427/oiii_nii.csv), [uvfe.csv](fantasy_agn/06872228427/uvfe.csv)
- `gelato`: [docker.log](gelato/06872228427/docker.log), [my_sdss-comp.pdf](gelato/06872228427/my_sdss-comp.pdf), [my_sdss-fit.pdf](gelato/06872228427/my_sdss-fit.pdf), [my_sdss-results.fits](gelato/06872228427/my_sdss-results.fits), [my_sdss-spec.pdf](gelato/06872228427/my_sdss-spec.pdf)
- `gleam`: [docker.log](gleam/06872228427/docker.log), [linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Ha.Ha_broad.NII1.png), [linefits.sdss.sdss.fiber1.001.Ha.NII1.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Ha.NII1.png), [linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Hb.Hb_broad.png), [linefits.sdss.sdss.fiber1.001.Hb.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.Hb.png), [linefits.sdss.sdss.fiber1.001.OII.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OII.png), [linefits.sdss.sdss.fiber1.001.OIII4.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII4.png), [linefits.sdss.sdss.fiber1.001.OIII5.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.OIII5.png), [linefits.sdss.sdss.fiber1.001.SII1.SII2.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.SII1.SII2.png), [linefits.sdss.sdss.fiber1.001.fits](gleam/06872228427/linefits.sdss.sdss.fiber1.001.fits), [linefits.sdss.sdss.fiber1.001.png](gleam/06872228427/linefits.sdss.sdss.fiber1.001.png)
