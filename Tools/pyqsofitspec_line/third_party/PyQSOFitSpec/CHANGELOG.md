# CHANGE LOG

## 2023-09-14
### Added
- setup and requirement details

## 2022-06-19
### Changed
- move line models to `fit_linemodel.py`
- save output results per spectrum

## 2022-06-18
### Added
- `main.py`
  - run spectra in bulk
  - bootstrap error for individual line
  - function to calculate log(sigma) from FWHM
  - optional command line argument for path to fits file
### Changed
- `examply.ipynb` to `main.py`

## 2022-06-16
### Added
- `linemodel` option to fit using different model
### Changed
- color scheme and cleaner visualisation for plots

## 2022-06-15
### Added
- combine updated PyQSOFitv1.1 with PyQSOFit_SBL and clean up
### Fixed
- output of `_DoLineFit` in `_line_mc`

# 2022-05-08 (from PyQSOFit_SBL)
### Added
- CIV abs optional in continuum removal
- Fe emission scaling output functionality
- one more parameter for Gaussians was added to allow of skewness
### Changed
- enabled error output for narrow lines
- fit with skewed Gaussians
- input fitting parameters

## 2022-02-11 and prior (from PyQSOFit)
### Fixed
- the flux error problem, previous error was underestimated by a factor of 1+z
- QSO PCA
- MC parameter unrenewed issue (Thanks Yuming Fu to point this out)


<!-- TEMPLATE
## 2023-MM-DD
### Added
### Changed
### Fixed 
-->
