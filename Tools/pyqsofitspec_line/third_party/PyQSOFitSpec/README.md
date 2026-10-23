# PyQSOFitSpec
A Python package for fitting quasar spectra with bootstrapped emission-line models

## Overview
PyQSOFitSpec is a spectral fitting toolkit for quasars, built on top of the original PyQSOFit framework. It extends the standard approach by introducing alternative emission-line fitting models and a bootstrap-based refitting strategy.

## Key Features
- Extended emission-line fitting models (defined in `fit_linemodel.py`)
- Bootstrap-based refitting of spectra to estimate uncertainties
- Outputs mean and standard deviation of line properties

See `CHANGELOG.md` for detailed updates.


## Background: PyQSOFit
We provide a brief guide of the Python QSO fitting code (PyQSOFit) to measure spectral properties of SDSS quasars. The code is currently transferred from Yue's IDL to Python. The package includes the main routine, Fe II templates, an input line-fitting parameter list, host galaxy templates, and dust reddening map to extract spectral measurements from the raw fits. Monte Carlo estimation of the measurement uncertainties of the fitting results can be conducted with the same fitting code.

The code takes an input spectrum (observed-frame wavelength, flux density and error arrays) and the redshift as input parameters, performs the fitting in the rest frame, and outputs the best-fit parameters and quality-checking plots to the paths specified by the user.

The code uses an input line-fitting parameter list to specify the fitting range and parameter constraints of the individual emission line components. An example of such a file is provided in the example.ipynb. Within the code, the user can switch on/off components to fit to the pseudo-continuum. For example, for some objects the UV/optical Fe II emission cannot be well constrained and the user may want to exclude this component in the continuum fit. The code is highly flexible and can be modified to meet the specific needs of the user.


## Installation
Requires Python &ge; 3.11.

Clone the repository:
```bash
git clone https://github.com/yongsukyee/PyQSOFitSpec.git
cd PyQSOFitSpec
````

Install dependencies:
```bash
pip install -r requirement.txt
```

Install `kapteyn`:
```bash
pip install https://www.astro.rug.nl/software/kapteyn/kapteyn-3.4.tar.gz
```


## Usage

### Run the fitter
```bash
python main.py [PATH_FITSFILE]
```
- `PATH_FITSFILE` (optional): Path to a FITS file or a directory containing FITS files. If omitted, the current directory is used.

> [!WARNING]
> Large numbers of input files and high `nboot_fit` values may cause `OSError: too many open files`.
> - Reduce one or both if this occurs.

### Configuration
Main configuration options are set in `main.py`. Important parameters include:
- `nboot_fit`: Number of bootstrap iterations per spectrum
- `linemodel`: Emission-line model name defined in `fit_linemodel.py`

Custom emission-line models can be added in: `fit_linemodel.py`

### Output
Results are saved to: `pyqsofitspec_out.csv`
- Each input file is processed independently
- Existing results are reused, allowing interrupted runs to be resumed
> [!TIP]
> Back up the output CSV file `pyqsofitspec_out.csv` before rerunning to preserve previous results.

### Example

Example spectra are provided in the `example/` directory.

The following reproduces a case where broad emission lines are fitted with a single skewed normal profile:
```bash
python main.py example
```


## TODO
- In `PyQSOFitSpec.py`:
  - [ ] Return `line_prop` and `get_line_profile` as dictionaries for easier access
  - [ ] Cache templates (Fe II, PCA, line parameters) for faster, lazy loading
  - [ ] Update color schemes for `decomposition_host` and `BC`
- In `main.py`:
  - [ ] Parallelize fitting to improve performance
  - [ ] Refactor and separate configs if `nboot_fit`
  - [ ] Simplify `run_qsofit` output handling so manual inclusion or exclusion of fitted lines is not required
- [ ] Create config files for configs in `main.py`


## Acknowledgements
This code is adapted from:
- PyQSOFit v1.1: <https://github.com/legolason/PyQSOFit>
- PyQSOFit_SBL: <https://github.com/JackHon55/PyQSOFit_SBL>

Archived demo notebooks adapted from the original repositories are available under `archive/`.


## Cite the original authors of the PyQSOFit code
```bibtex
@MISC{2018ascl.soft09008G,
       author = {{Guo}, Hengxiao and {Shen}, Yue and {Wang}, Shu},
        title = "{PyQSOFit: Python code to fit the spectrum of quasars}",
     keywords = {Software},
 howpublished = {Astrophysics Source Code Library, record ascl:1809.008},
         year = 2018,
        month = sep,
          eid = {ascl:1809.008},
        pages = {ascl:1809.008},
archivePrefix = {ascl},
       eprint = {1809.008},
       adsurl = {https://ui.adsabs.harvard.edu/abs/2018ascl.soft09008G},
      adsnote = {Provided by the SAO/NASA Astrophysics Data System}
}
```
