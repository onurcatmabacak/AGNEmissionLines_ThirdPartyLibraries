import glob, os, sys, timeit
import matplotlib
import numpy as np

# sys.path.append('../')
from pyqsofit.PyQSOFit import QSOFit
from astropy.io import fits
from astropy.table import Table
import astropy.units as u
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

QSOFit.set_mpl_style()

# Show the versions so we know what works
import astropy
import lmfit
import pyqsofit

print(astropy.__version__)
print(lmfit.__version__)
print(pyqsofit.__version__)

import emcee  # optional, for MCMC

print(emcee.__version__)
print(pyqsofit.__path__)

# Safe emcee initialization and production diagnostics.  PyQSOFit itself
# calls lmfit's emcee integrator; mcmc_support only replaces the walker start
# (see the module docstring for the exact failure it fixes).
import mcmc_support


# Load the spectrum from the FITS file
def load_spectrum(fits_file):
    hdulist = fits.open(fits_file)
    header = hdulist[0].header

    z = header.get('z', 0)  # redshift, default to 0 if not found
    fwhm_res = header.get('fwhm', 0)  # FWHM resolution, default to 0 if not found
    print(f"FWHM Resolution: {fwhm_res} Å")
    ebv = header.get('ebv', 0)  # E(B-V), default to 0 if not found

    flux_norm = 1e17
    flux = hdulist[0].data  # Normalized spectrum
    wavelength = hdulist[1].data  # Wavelength array
    
    # print(fits_file, len(hdulist))

    err = hdulist[2].data if len(hdulist) > 2 else None  # Normalized error spectrum, might not exist
    if err is None:
        err = 0.02 * flux   # fallback only when no calibrated error is supplied
    # print('onuronuronur: \n\n', hdulist[0].data, hdulist[1].data, hdulist[2].data)
    # print(hdulist, err)

    if err is None:
    
        return wavelength * u.AA, flux*flux_norm * u.Unit('erg cm-2 s-1 AA-1'), err, z
    
    else:   
        
        if isinstance(err, np.ndarray):
            return wavelength * u.AA, flux*flux_norm * u.Unit('erg cm-2 s-1 AA-1'), err*flux_norm * u.Unit('erg cm-2 s-1 AA-1'), z
        else:
            print("The value is neither None nor a NumPy array")
            quit()
        


path_ex = '.' #os.path.join(pyqsofit.__path__[0], '..', 'example')

# create a header
hdr0 = fits.Header()
hdr0['Author'] = 'Hengxiao Guo'
primary_hdu = fits.PrimaryHDU(header=hdr0)

"""
In this table, we specify the priors / initial conditions and boundaries for the line fitting parameters.
"""

line_priors = np.rec.array([
    # Rest wavelengths are vacuum (PyQSOFit divides the observed wave by 1+z).
    (6564.61, 'Ha', 6400, 6800, 'Ha_br', 2, 0.0, 0.0, 1e10, 5e-3, 0.0015, 0.05, 0.015, 0, 0, 0, 0.05, 1),
    (6564.61, 'Ha', 6400, 6800, 'Ha_na', 1, 0.0, 0.0, 1e10, 1e-3, 5e-4, 0.0012, 0.01, 1, 1, 0, 0.002, 1),
    (6549.85, 'Ha', 6400, 6800, 'NII6549', 1, 0.0, 0.0, 1e10, 1e-3, 2.3e-4, 0.0012, 5e-3, 1, 1, 1, 0.001, 1),
    (6585.28, 'Ha', 6400, 6800, 'NII6585', 1, 0.0, 0.0, 1e10, 1e-3, 2.3e-4, 0.0012, 5e-3, 1, 1, 1, 0.003, 1),
    # [SII] ratio is density-dependent -> leave it free (findex 0).
    (6718.29, 'Ha', 6400, 6800, 'SII6718', 1, 0.0, 0.0, 1e10, 1e-3, 2.3e-4, 0.0012, 5e-3, 1, 1, 0, 0.001, 1),
    (6732.67, 'Ha', 6400, 6800, 'SII6732', 1, 0.0, 0.0, 1e10, 1e-3, 2.3e-4, 0.0012, 5e-3, 1, 1, 0, 0.001, 1),
    (4862.68, 'Hb', 4640, 5100, 'Hb_br', 2, 0.0, 0.0, 1e10, 5e-3, 0.0015, 0.02, 0.01, 0, 0, 0, 0.01, 1),
    (4862.68, 'Hb', 4640, 5100, 'Hb_na', 1, 0.0, 0.0, 1e10, 1e-3, 2.3e-4, 0.0012, 0.01, 1, 1, 0, 0.002, 1),
    # The [OIII] 4959/5007 doublet shares velocity (vindex), width (windex) and a
    # fixed flux ratio (findex 3 for narrow, 4 for outflow; fvalue 0.33 / 1.0).
    # Without the ratio tie the narrow 4959 line collapses to ~0.
    (4960.30, 'Hb', 4640, 5100, 'OIII4959c', 1, 0.0, 0.0, 1e10, 1e-3, 2.3e-4, 0.0012, 0.01, 1, 1, 3, 0.33, 1),
    (5008.24, 'Hb', 4640, 5100, 'OIII5007c', 1, 0.0, 0.0, 1e10, 1e-3, 2.3e-4, 0.0012, 0.01, 1, 1, 3, 1.0, 1),
    (4960.30, 'Hb', 4640, 5100, 'OIII4959w',   1, 0.0, 0.0, 1e10, 3e-3, 2.3e-4, 0.006,  0.01,  2, 2, 4, 0.33, 1),
    (5008.24, 'Hb', 4640, 5100, 'OIII5007w',   1, 0.0, 0.0, 1e10, 3e-3, 2.3e-4, 0.006,  0.01,  2, 2, 4, 1.0, 1),
    (4687.02, 'Hb', 4640, 5100, 'HeII4687_br', 1, 0.0, 0.0, 1e10, 5e-3, 0.004,  0.05,   0.005, 0, 0, 0, 0.001, 1),
    (4687.02, 'Hb', 4640, 5100, 'HeII4687_na', 1, 0.0, 0.0, 1e10, 1e-3, 2.3e-4, 0.0012, 0.005, 1, 1, 0, 0.001, 1),

    # (3934.78, 'CaII', 3900, 3960, 'CaII3934' , 2, 0.0, 0.0, 1e10, 1e-3, 3.333e-4, 0.0012, 0.01, 99, 0, 0, -0.001, 1),

    # (3782.48, 'OII', 3650, 3800, 'OII3728', 1, 0.0, 0.0, 1e10, 1e-3, 3.333e-4, 0.0012, 0.01, 1, 1, 0, 0.001, 1),

    # (3426.84, 'NeV', 3380, 3480, 'NeV3426',    1, 0.0, 0.0, 1e10, 1e-3, 3.333e-4, 0.0012, 0.01, 0, 0, 0, 0.001, 1),
    # (3426.84, 'NeV', 3380, 3480, 'NeV3426_br', 1, 0.0, 0.0, 1e10, 5e-3, 0.0025,   0.02,   0.01, 0, 0, 0, 0.001, 1),

    (2798.75, 'MgII', 2700, 2900, 'MgII_br', 2, 0.0, 0.0, 1e10, 5e-3, 0.0015, 0.05, 0.015, 0, 0, 0, 0.05, 1),
    (2798.75, 'MgII', 2700, 2900, 'MgII_na', 1, 0.0, 0.0, 1e10, 1e-3, 5e-4, 0.0012, 0.01, 1, 1, 0, 0.002, 1),

    (1908.73, 'CIII', 1700, 1970, 'CIII_br', 2, 0.0, 0.0, 1e10, 5e-3, 0.0015, 0.008, 0.015, 99, 0, 0, 0.01, 1),
    (1908.73, 'CIII', 1700, 1970, 'CIII_na',   1, 0.0, 0.0, 1e10, 1e-3, 5e-4,  0.0012, 0.01,  1, 1, 0, 0.002, 1),
    # Satellites in the C III] complex.  Leaving these out made the broad
    # C III] component absorb Si III]/Al III/Si II/Fe II flux and inflated the
    # apparent C III] area by 1.5-2.9x relative to SDSS ZLINE.
    (1892.03, 'CIII', 1700, 1970, 'SiIII1892', 1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015, 0.003, 1, 1, 0, 0.002, 1),
    (1857.40, 'CIII', 1700, 1970, 'AlIII1857', 1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015, 0.003, 1, 1, 0, 0.002, 1),
    (1816.98, 'CIII', 1700, 1970, 'SiII1816',  1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015, 0.01,  1, 1, 0, 0.0002, 1),
    (1786.70, 'CIII', 1700, 1970, 'FeII1787',  1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015, 0.01,  1, 1, 0, 0.0002, 1),
    (1750.26, 'CIII', 1700, 1970, 'NIII1750',  1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015, 0.01,  1, 1, 0, 0.001, 1),
    #(1892.03, 'CIII', 1700, 1970, 'SiIII1892', 1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015,  0.003, 1, 1, 0, 0.005, 1),
    #(1857.40, 'CIII', 1700, 1970, 'AlIII1857', 1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015,  0.003, 1, 1, 0, 0.005, 1),
    #(1816.98, 'CIII', 1700, 1970, 'SiII1816',  1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015,  0.01,  1, 1, 0, 0.0002, 1),
    #(1786.7,  'CIII', 1700, 1970, 'FeII1787',  1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015,  0.01,  1, 1, 0, 0.0002, 1),
    #(1750.26, 'CIII', 1700, 1970, 'NIII1750',  1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015,  0.01,  1, 1, 0, 0.001, 1),
    #(1718.55, 'CIII', 1700, 1900, 'NIV1718',   1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015,  0.01,  1, 1, 0, 0.001, 1),

    (1549.06, 'CIV', 1500, 1700, 'CIV_br', 2, 0.0, 0.0, 1e10, 5e-3, 0.0015, 0.05, 0.015, 0, 0, 0, 0.05, 1),
    (1549.06, 'CIV', 1500, 1700, 'CIV_na', 1, 0.0, 0.0, 1e10, 1e-3, 5e-4, 0.0012, 0.01, 1, 1, 0, 0.002, 1),
    (1640.42, 'CIV', 1500, 1700, 'HeII1640',    1, 0.0, 0.0, 1e10, 1e-3, 5e-4,   0.0012, 0.008, 1, 1, 0, 0.002, 1),
    #(1663.48, 'CIV', 1500, 1700, 'OIII1663',    1, 0.0, 0.0, 1e10, 1e-3, 5e-4,   0.0012, 0.008, 1, 1, 0, 0.002, 1),
    #(1640.42, 'CIV', 1500, 1700, 'HeII1640_br', 1, 0.0, 0.0, 1e10, 5e-3, 0.0025, 0.02,   0.008, 1, 1, 0, 0.002, 1),
    #(1663.48, 'CIV', 1500, 1700, 'OIII1663_br', 1, 0.0, 0.0, 1e10, 5e-3, 0.0025, 0.02,   0.008, 1, 1, 0, 0.002, 1),

    (1402.06, 'SiIV', 1290, 1450, 'SiIV_OIV1', 1, 0.0, 0.0, 1e10, 5e-3, 0.002, 0.05,  0.015, 1, 1, 0, 0.05, 1),
    (1396.76, 'SiIV', 1290, 1450, 'SiIV_OIV2', 1, 0.0, 0.0, 1e10, 5e-3, 0.002, 0.05,  0.015, 1, 1, 0, 0.05, 1),
    (1335.30, 'SiIV', 1290, 1450, 'CII1335',   1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015, 0.01,  1, 1, 0, 0.001, 1),
    (1304.35, 'SiIV', 1290, 1450, 'OI1304',    1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.015, 0.01,  1, 1, 0, 0.001, 1),

    (1215.67, 'Lya', 1150, 1290, 'Lya_br', 3, 0.0, 0.0, 1e10, 5e-3, 0.002, 0.05, 0.02, 0, 0, 0, 0.05, 1),
    (1240.14, 'Lya', 1150, 1290, 'NV1240', 1, 0.0, 0.0, 1e10, 2e-3, 0.001, 0.01, 0.005, 0, 0, 0, 0.002, 1),
    (1215.67, 'Lya', 1150, 1290, 'Lya_na', 1, 0.0, 0.0, 1e10, 1e-3, 5e-4, 0.0012, 0.01, 0, 0, 0, 0.002, 1),
    ],

    formats='float32,    a20,  float32, float32,      a20,  int32, float32, float32, float32, float32, float32, float32, float32,   int32,  int32,  int32, float32, int32',
    names=' lambda, compname,   minwav,  maxwav, linename, ngauss,  inisca,  minsca,  maxsca,  inisig,  minsig,  maxsig,    voff,  vindex, windex, findex,  fvalue,  vary')

# Header
hdr1 = fits.Header()
hdr1['lambda'] = 'Vacuum Wavelength in Ang'
hdr1['minwav'] = 'Lower complex fitting wavelength range'
hdr1['maxwav'] = 'Upper complex fitting wavelength range'
hdr1['ngauss'] = 'Number of Gaussians for the line'

# Can be set to negative for absorption lines if you want
hdr1['inisca'] = 'Initial guess of line scale [flux]'
hdr1['minsca'] = 'Lower range of line scale [flux]'
hdr1['maxsca'] = 'Upper range of line scale [flux]'

hdr1['inisig'] = 'Initial guess of linesigma [lnlambda]'
hdr1['minsig'] = 'Lower range of line sigma [lnlambda]'
hdr1['maxsig'] = 'Upper range of line sigma [lnlambda]'

hdr1['voff  '] = 'Limits on velocity offset from the central wavelength [lnlambda]'
hdr1['vindex'] = 'Entries w/ same NONZERO vindex constrained to have same velocity'
hdr1['windex'] = 'Entries w/ same NONZERO windex constrained to have same width'
hdr1['findex'] = 'Entries w/ same NONZERO findex have constrained flux ratios'
hdr1['fvalue'] = 'Relative scale factor for entries w/ same findex'

hdr1['vary'] = 'Whether or not to vary the parameter (set to 0 to fix the line parameter to initial values)'

# Save line info
hdu1 = fits.BinTableHDU(data=line_priors, header=hdr1, name='line_priors')

"""
In this table, we specify the windows and priors / initial conditions and boundaries for the continuum fitting parameters.
"""

conti_windows = np.rec.array([
    (1150., 1170.), 
    (1275., 1290.),
    (1350., 1360.),
    (1445., 1465.),
    (1690., 1705.),
    (1705., 1730.),
    (1950., 1975.),
    (1970., 2400.),
    (2480., 2675.),
    (2925., 3400.),
    (3775., 3832.),
    (4000., 4050.),
    (4200., 4230.),
    (4435., 4640.),
    (5100., 5535.),
    (6005., 6035.),
    (6110., 6250.),
    (6800., 7000.),
    (7160., 7180.),
    (7500., 7800.),
    (8050., 8150.), # Continuum fitting windows (to avoid emission line, etc.)  [AA]
    ], 
    formats = 'float32,  float32',
    names =    'min,     max')

hdu2 = fits.BinTableHDU(data=conti_windows, name='conti_windows')

conti_priors = np.rec.array([
    ('Fe_uv_norm',  0.0,   0.0,   1e10,  1), # Normalization of the MgII Fe template [flux]
    ('Fe_uv_FWHM',  3000,  1200,  18000, 1), # FWHM of the MgII Fe template [AA]
    ('Fe_uv_shift', 0.0,   -0.01, 0.01,  1), # Wavelength shift of the MgII Fe template [lnlambda]
    ('Fe_op_norm',  0.0,   0.0,   1e10,  1), # Normalization of the Hbeta/Halpha Fe template [flux]
    ('Fe_op_FWHM',  3000,  1200,  18000, 1), # FWHM of the Hbeta/Halpha Fe template [AA]
    ('Fe_op_shift', 0.0,   -0.01, 0.01,  1), # Wavelength shift of the Hbeta/Halpha Fe template [lnlambda]
    ('PL_norm',     1.0,   0.0,   1e10,  1), # Normalization of the power-law (PL) continuum f_lambda = (lambda/3000)^-alpha
    ('PL_slope',    -1.5,  -5.0,  3.0,   1), # Slope of the power-law (PL) continuum
    ('Blamer_norm', 0.0,   0.0,   1e10,  1), # Normalization of the Balmer continuum at < 3646 AA [flux] (Dietrich et al. 2002)
    ('Balmer_Te',   15000, 10000, 50000, 1), # Te of the Balmer continuum at < 3646 AA [K?]
    ('Balmer_Tau',  0.5,   0.1,   2.0,   1), # Tau of the Balmer continuum at < 3646 AA
    ('conti_a_0',   0.0,   None,  None,  1), # 1st coefficient of the polynomial continuum
    ('conti_a_1',   0.0,   None,  None,  1), # 2nd coefficient of the polynomial continuum
    ('conti_a_2',   0.0,   None,  None,  1), # 3rd coefficient of the polynomial continuum
    # Note: The min/max bounds on the conti_a_0 coefficients are ignored by the code,
    # so they can be determined automatically for numerical stability.
    ],

    formats = 'a20,  float32, float32, float32, int32',
    names = 'parname, initial,   min,     max,     vary')

hdr3 = fits.Header()
hdr3['ini'] = 'Initial guess of line scale [flux]'
hdr3['min'] = 'FWHM of the MgII Fe template'
hdr3['max'] = 'Wavelength shift of the MgII Fe template'

hdr3['vary'] = 'Whether or not to vary the parameter (set to 0 to fix the continuum parameter to initial values)'


hdu3 = fits.BinTableHDU(data=conti_priors, header=hdr3, name='conti_priors')

"""
In this table, we allow user to customized some key parameters in our result measurements.
"""

measure_info = Table(
    [
        [[1350, 1450, 3000, 4200, 5100]],
        [[
            # [2240, 2650], 
            [4435, 4685],
        ]]
    ],
    names=([
        'cont_loc',
        'Fe_flux_range'
    ]),
    dtype=([
        'float32',
        'float32'
    ])
)
hdr4 = fits.Header()
hdr4['cont_loc'] = 'The wavelength of continuum luminosity in results'
hdr4['Fe_flux_range'] = 'Fe emission wavelength range calculated in results'

hdu4 = fits.BinTableHDU(data=measure_info, header=hdr4, name='measure_info')

hdu_list = fits.HDUList([primary_hdu, hdu1, hdu2, hdu3, hdu4])
hdu_list.writeto(os.path.join(path_ex, 'qsopar.fits'), overwrite=True)

Table(line_priors)

path_out = "./"

# Required
wavelength, flux, error, z = load_spectrum('spectrum.fits')
# Use the calibrated error array from the prepared spectrum.  The old
# unconditional 0.02*flux floor made every pixel S/N=50 and biased the
# broad UV complexes.  An optional floor is available for experiments.
_floor = float(os.environ.get("PYQSOFIT_ERR_FLOOR", "0"))
if _floor > 0:
    error = np.maximum(error, _floor * flux)
# Per-object redshift: take it from the FITS header (the original analysis had
# this hardcoded to 0.348 for its single target). PYQSOFIT_Z overrides it.
z = float(os.environ.get("PYQSOFIT_Z", z))
# Drop priors whose observed wavelength is outside the prepared spectrum.
_wmin = float(np.nanmin(wavelength.value))
_wmax = float(np.nanmax(wavelength.value))
for _row in line_priors:
    if not (_wmin < float(_row['lambda']) * (1 + z) < _wmax):
        _row['vary'] = 0
print(wavelength, flux, error, z)

# # Optional
# ra = data[0].header['plug_ra']  # RA
# dec = data[0].header['plug_dec']  # DEC
# plateid = data[0].header['plateid']  # SDSS plate ID
# mjd = data[0].header['mjd']  # SDSS MJD
# fiberid = data[0].header['fiberid']  # SDSS fiber ID

# Prepare data
q_mle = QSOFit(wavelength, flux, error, z, path=path_ex)

# ---------------------------------------------------------------------------
# Uncertainty mode.  MC and MCMC are mutually exclusive in PyQSOFit.
# ---------------------------------------------------------------------------
MC_ENABLED = os.environ.get("PYQSOFIT_MC", "0") == "1"
MCMC_ENABLED = os.environ.get("PYQSOFIT_MCMC", "0") == "1"
if MC_ENABLED and MCMC_ENABLED:
    raise SystemExit("PYQSOFIT_MC=1 and PYQSOFIT_MCMC=1 are mutually exclusive")
MCMC_CFG = mcmc_support.mcmc_env_config()
NSAMP = int(os.environ.get("PYQSOFIT_NSAMP", "50"))
NBURN = int(os.environ.get("PYQSOFIT_NBURN", "20"))
NTHIN = int(os.environ.get("PYQSOFIT_NTHIN", "10"))
MCMC_RUNS = []
if MCMC_ENABLED:
    if NSAMP <= NBURN:
        raise SystemExit(
            f"PYQSOFIT_NSAMP={NSAMP} must exceed PYQSOFIT_NBURN={NBURN}"
        )
    import pyqsofit.PyQSOFit as _pyqsofit_module

    MCMC_RUNS = mcmc_support.install_safe_emcee(
        _pyqsofit_module,
        nwalkers=MCMC_CFG["nwalkers"],
        seed=MCMC_CFG["seed"],
        progress=False,
    )
    print(
        "MCMC enabled: nsamp=%d nburn=%d nthin=%d nwalkers=%d seed=%s"
        % (NSAMP, NBURN, NTHIN, MCMC_CFG["nwalkers"], MCMC_CFG["seed"])
    )

# Double check the installation path with the PCA / Fe template files
# print('install path:', q_mle.install_path)

# Change it if you installed them somewhere else
#q_mle.install_path = '...'
narrow_line_velocity_limit = 1200

start = timeit.default_timer()
# Do the fitting

q_mle.Fit(name='result',  # customize the name of given targets. Default: plate-mjd-fiber
          # prepocessing parameters
          nsmooth=1,  # do n-pixel smoothing to the raw input flux and err spectra
          and_mask=False,  # delete the and masked pixels
          or_mask=False,  # delete the or masked pixels
          reject_badpix=True,  # do not delete narrow-line pixels as outliers
          deredden=False,  # correct the Galactic extinction
          wave_range=None,  # trim input wavelength
          wave_mask=None,  # 2-D array, mask the given range(s)

          # host decomposition parameters (Galaxy PCA templates are staged as ./pca)
          decompose_host=(os.environ.get("PYQSOFIT_HOST", "0") == "1"),  # UV fit is host-free; pPXF handles the host
          host_prior=True, # prior-informed decomposition; without it 6/10 fits rejected the host (negative flux)
          host_prior_scale=0.2, # scale of prior panelty. Usually, 0.2 works fine for SDSS spectra. Adjust it smaller if you find the prior affect the fitting results too much.

          host_line_mask=True, # Mask the galaxy line region when subtracting the host
          decomp_na_mask=True, # Mask narrow lines when decomposing
          qso_type='CZBIN1', # prior-informed decomposition only ships CZBIN1/DZBIN1 priors
          npca_qso=10, # number of quasar templates
          host_type='PCA', # template name for galaxy
          npca_gal=5, # number of galaxy templates (Yip+2004, ~98% variance)
          
          # continuum model fit parameters
          Fe_uv_op=True,  # If True, fit continuum with UV and optical FeII template
          poly=True,  # If True, fit continuum with the polynomial component to account for the dust reddening
          BC=False,  # If True, fit continuum with Balmer continua from 1000 to 3646A
          initial_guess=None,  # Initial parameters for continuum model, read the annotation of this function for detail
          rej_abs_conti=True,  # If True, it will iterately reject 3 sigma outlier absorption pixels in the continuum
          n_pix_min_conti=100,  # Minimum number of negative pixels for host continuuum fit to be rejected.

          # emission line fit parameters
          linefit=True,  # If True, the emission line will be fitted
          rej_abs_line=True, # If True, it will iterately reject 3 sigma outlier absorption pixels in the emission lines

          # fitting method selection
          # PYQSOFIT_MC=1 turns on Monte-Carlo resampling for parameter/flux
          # uncertainties (off during the search for speed).
          MC=MC_ENABLED,
          # If True, do Monte Carlo resampling of the spectrum based on the input error array to produce the MC error array
          # PYQSOFIT_MCMC=1 turns on full emcee MCMC sampling of the posterior.
          MCMC=MCMC_ENABLED,
          # If True, do Markov Chain Monte Carlo sampling of the posterior probability densities to produce the error array
          nsamp=NSAMP,
          # The number of trials of the MC process (if MC=True) or number samples to run MCMC chain (if MCMC=True)

          # advanced fitting parameters
          param_file_name='qsopar.fits',  # Name of the qso fitting parameter FITS file.
          nburn=NBURN,  # The number of burn-in samples to run MCMC chain
          nthin=NTHIN,  # To set the MCMC chain returns every n samples
          epsilon_jitter=0.,
          # Initial jitter for every initial guass to avoid local minimum. (Under test, not recommanded to change)

          # customize the results
          save_result=True,  # If True, all the fitting results will be saved to a fits file
          save_fits_name="output",  # The output name of the result fits
          save_fits_path="./",  # The output path of the result fits
          plot_fig=True,  # If True, the fitting results will be plotted
          save_fig=True,  # If True, the figure will be saved
          plot_corner=False,  # production corner/trace figures are written below, not left as unsaved pyplot objects

          # debugging mode
          verbose=True,  # turn on (True) or off (False) debugging output

          # sublevel parameters for figure plot and emcee
          kwargs_plot={
              'save_fig_path': './',  # The output path of the figure
              'broad_fwhm'   : narrow_line_velocity_limit  # km/s, lower limit that code decide if a line component belongs to broad component
          },
          kwargs_conti_emcee={'seed': MCMC_CFG["seed"]},
          kwargs_line_emcee={'seed': MCMC_CFG["seed"]})

end = timeit.default_timer()

print(f'Fitting finished in {np.round(end - start, 1)}s')

# ---------------------------------------------------------------------------
# Production MCMC products.  PyQSOFit keeps the emcee chains only in memory;
# the patched minimizer records them so we can persist a reproducible audit
# trail (chains, acceptance, autocorrelation time, run metadata).
# ---------------------------------------------------------------------------
if MCMC_ENABLED:
    import csv as _csv
    import json as _json
    import platform as _platform

    _mcmc_lines = [
        ("Hb_br", "broad"), ("Hb_na", "narrow"),
        ("OIII5007w", "broad"), ("OIII5007c", "narrow"),
        ("MgII_br", "broad"), ("MgII_na", "narrow"),
    ]
    _npost = int(len(q_mle.gauss_result_all)) if len(getattr(q_mle, "gauss_result_all", [])) else 0
    # line_prop_from_name integrates and splines each component, so evaluating
    # it on every one of the (often >10^5) posterior rows is needlessly slow.
    # Use a reproducible random subset for the line-flux posterior; the full
    # parameter chains stay in the npz.
    _line_n = min(int(os.environ.get("PYQSOFIT_MCMC_LINE_SAMPLES", "2000")), _npost)
    _line_idx = (
        np.sort(np.random.default_rng(int(MCMC_CFG["seed"])).choice(_npost, _line_n, replace=False))
        if _line_n > 0 else np.array([], int)
    )
    _line_post = {
        f"{_nm}__{_ct}": {"area": np.full(_line_n, np.nan),
                          "fwhm": np.full(_line_n, np.nan),
                          "snr": np.full(_line_n, np.nan)}
        for _nm, _ct in _mcmc_lines
    }
    # Recompute tied/expression parameters per draw.  PyQSOFit's own
    # gauss_result_all freezes e.g. [O III] 5007 at its MLE, so using it
    # directly would report a zero-width posterior for every tied line.
    _original_gauss_all = q_mle.gauss_result_all
    q_mle.gauss_result_all = mcmc_support.corrected_line_samples(q_mle, MCMC_RUNS, _line_idx)
    for _j in range(_line_n):
        for _nm, _ct in _mcmc_lines:
            try:
                _f, _s, _e, _p, _a, _sn = q_mle.line_prop_from_name(_nm, _ct, sample_index=_j)
                _key = f"{_nm}__{_ct}"
                _line_post[_key]["area"][_j] = float(_a)
                _line_post[_key]["fwhm"][_j] = float(_f)
                _line_post[_key]["snr"][_j] = float(_sn)
            except Exception:
                pass
    q_mle.gauss_result_all = _original_gauss_all

    # Full posterior line-flux arrays live in the compressed npz.
    _extra = {}
    for _key, _vals in _line_post.items():
        for _prop, _arr in _vals.items():
            _extra[f"line_{_key}__{_prop}"] = _arr
    _extra["line_keys"] = np.array(list(_line_post), dtype=object)
    _extra["line_posterior_index"] = _line_idx
    mcmc_support.write_npz(MCMC_RUNS, "pyqsofit_mcmc_samples.npz", extra=_extra)

    # The CSV is a readable, reproducible thinning of the full posterior; the
    # npz remains the authoritative full-resolution product.
    _csv_n = min(5000, _line_n)
    _csv_idx = np.unique(np.linspace(0, max(_line_n - 1, 0), _csv_n).astype(int)) if _csv_n else np.array([], int)
    _sample_rows = []
    for _j in _csv_idx:
        for _nm, _ct in _mcmc_lines:
            _vals = _line_post[f"{_nm}__{_ct}"]
            _sample_rows.append({
                "sample": int(_line_idx[_j]),
                "line": _nm,
                "component": _ct,
                "area_1e17": float(_vals["area"][_j]),
                "fwhm_kms": float(_vals["fwhm"][_j]),
                "snr": float(_vals["snr"][_j]),
                "weight": 1.0,
                "full_posterior_size": int(_npost),
            })
    if _sample_rows:
        with open("pyqsofit_mcmc_samples.csv", "w", newline="") as _fh:
            _w = _csv.DictWriter(_fh, fieldnames=list(_sample_rows[0]))
            _w.writeheader()
            _w.writerows(_sample_rows)

    # Summary table, including the committed MC values when they are present
    # in the sibling ../mc directory (the default production layout).
    _mc_summary_path = os.environ.get(
        "PYQSOFIT_MC_SUMMARY", os.path.join("..", "mc", "pyqsofit_mc_summary.csv")
    )
    _mc_rows = {}
    if os.path.exists(_mc_summary_path):
        try:
            with open(_mc_summary_path, newline="") as _fh:
                for _row in _csv.DictReader(_fh):
                    _mc_rows[(_row.get("line"), _row.get("component"))] = _row
        except Exception as _e:
            print("could not read MC summary for comparison:", _e)

    _summary_rows = []
    for _nm, _ct in _mcmc_lines:
        _arr = _line_post[f"{_nm}__{_ct}"]["area"]
        _finite = _arr[np.isfinite(_arr)]
        if _finite.size == 0:
            continue
        _mle_f, _mle_s, _mle_e, _mle_p, _mle_a, _mle_sn = q_mle.line_prop_from_name(_nm, _ct)
        _row = {
            "line": _nm,
            "component": _ct,
            "n_posterior": int(_finite.size),
            "mcmc_median": float(np.nanmedian(_finite)),
            "mcmc_p16": float(np.nanpercentile(_finite, 16)),
            "mcmc_p84": float(np.nanpercentile(_finite, 84)),
            "mcmc_mean": float(np.nanmean(_finite)),
            "mcmc_std": float(np.nanstd(_finite)),
            "mle_area": float(_mle_a),
        }
        _mc = _mc_rows.get((_nm, _ct))
        if _mc:
            _row.update({
                "mc_n": _mc.get("n"),
                "mc_median": _mc.get("median"),
                "mc_p16": _mc.get("p16"),
                "mc_p84": _mc.get("p84"),
            })
        _summary_rows.append(_row)
    if _summary_rows:
        with open("pyqsofit_mcmc_summary.csv", "w", newline="") as _fh:
            _fieldnames = sorted({key for row in _summary_rows for key in row})
            _w = _csv.DictWriter(_fh, fieldnames=_fieldnames)
            _w.writeheader()
            _w.writerows(_summary_rows)

    # Corner and trace figures.  Full multipage PDFs cover every complex;
    # compact PNGs use the first non-continuum complex (MgII in this config).
    # Figure failures must not discard the chains/diagnostics written above.
    try:
        mcmc_support.save_corner_pdf(MCMC_RUNS, "pyqsofit_mcmc_corner.pdf")
        mcmc_support.save_trace_pdf(MCMC_RUNS, "pyqsofit_mcmc_trace.pdf")
        _line_runs = [run for run in MCMC_RUNS if run["label"] != "continuum"]
        _main_run = _line_runs[0] if _line_runs else (MCMC_RUNS[0] if MCMC_RUNS else None)
        if _main_run is not None:
            mcmc_support.save_corner_png(_main_run, "pyqsofit_mcmc_corner.png")
            mcmc_support.save_trace_png(_main_run, "pyqsofit_mcmc_trace.png")
        _line_corner = {
            f"{_nm} ({_ct})": _line_post[f"{_nm}__{_ct}"]["area"]
            for _nm, _ct in _mcmc_lines
            if np.any(np.isfinite(_line_post[f"{_nm}__{_ct}"]["area"]))
        }
        if _line_corner:
            mcmc_support.save_line_corner(_line_corner, "pyqsofit_mcmc_line_corner.png")
    except Exception as _e:
        print("MCMC figure generation failed:", _e)

    _summary = mcmc_support.summarize_runs(MCMC_RUNS)
    _meta = {
        "tool": "pyqsofit_uv",
        "engine": "PyQSOFit emcee (lmfit Minimizer.emcee)",
        "versions": {
            "python": _platform.python_version(),
            "pyqsofit": pyqsofit.__version__,
            "lmfit": lmfit.__version__,
            "emcee": emcee.__version__,
            "astropy": astropy.__version__,
        },
        "input_spectrum": os.environ.get("PYQSOFIT_INPUT", "spectrum.fits"),
        "source_key": os.environ.get("PYQSOFIT_SOURCE_KEY", ""),
        "image": os.environ.get("PYQSOFIT_IMAGE", ""),
        "git_commit": os.environ.get("PYQSOFIT_GIT_COMMIT", ""),
        "redshift": float(z),
        "wave_range_observed": [float(np.nanmin(wavelength.value)), float(np.nanmax(wavelength.value))],
        "mcmc_config": {
            "nsamp": int(NSAMP), "nburn": int(NBURN), "nthin": int(NTHIN),
            "nwalkers": int(MCMC_CFG["nwalkers"]), "seed": int(MCMC_CFG["seed"]),
            "retained_steps": int((NSAMP - NBURN) // NTHIN),
            "line_posterior_samples": int(_line_n),
        },
        "fit_wall_seconds": float(end - start),
        "outputs": [
            "pyqsofit_mcmc_samples.csv", "pyqsofit_mcmc_samples.npz",
            "pyqsofit_mcmc_summary.csv", "pyqsofit_mcmc_corner.pdf",
            "pyqsofit_mcmc_corner.png", "pyqsofit_mcmc_trace.pdf",
            "pyqsofit_mcmc_trace.png", "pyqsofit_mcmc_line_corner.png",
            "pyqsofit_mcmc_config.json", "run.json",
        ],
    }
    _run = mcmc_support.write_run_json(MCMC_RUNS, "run.json", meta=_meta)
    mcmc_support.write_effective_config(
        "pyqsofit_mcmc_config.json",
        {"status": _run["status"], "created_utc": _run["created_utc"],
         "mcmc_config": _meta["mcmc_config"], "versions": _meta["versions"],
         "input_spectrum": _meta["input_spectrum"], "source_key": _meta["source_key"],
         "redshift": _meta["redshift"], "convergence": _summary},
    )
    print("MCMC diagnostics (acceptance / tau / ESS):")
    for _label, _diag in _summary.items():
        print(
            f"  {_label}: nvarys={_diag['nvarys']} acc={_diag['acceptance_mean']:.3f}"
            f"+/-{_diag['acceptance_std']:.3f} tau_max={_diag['tau_max']}"
            f" ess_min={_diag['ess_min']} converged={_diag['converged']}"
        )
    print("wrote pyqsofit_mcmc_samples.csv/.npz, summary, corner/trace figures, run.json")

# Dump the total model and its continuum/line parts on the (rest-frame) fitting
# grid.  The cross-tool scorer (pipeline/score_fits.py) reads this to compute a
# common, error-inflation-proof chi-square that does not depend on PyQSOFit's
# internal error floor.
try:
    from astropy.table import Table as _Table
    _conti = np.asarray(q_mle.f_conti_model)
    _line = np.asarray(q_mle.f_line_model)
    _cols = {
        'wave': np.asarray(q_mle.wave),
        'flux': np.asarray(q_mle.line_flux) + _conti,  # host-subtracted input flux
        'model': _conti + _line,                        # AGN-only model
        'conti': _conti,
        'line': _line,
    }
    # If the host was decomposed, the AGN-only model must have the host added
    # back to be comparable with the observed (host-included) spectrum.
    _host = getattr(q_mle, 'host', None)
    if _host is not None and np.asarray(_host).shape == _conti.shape:
        _cols['host'] = np.asarray(_host)
        _cols['model_total'] = _cols['model'] + np.asarray(_host)
    _Table(_cols).write('pyqsofit_model.csv', format='ascii.csv', overwrite=True)
    print('wrote pyqsofit_model.csv')
except Exception as _e:
    print('could not write pyqsofit_model.csv:', _e)

# Continuum fitting results
print(q_mle.conti_result_name)
print('')
print(q_mle.conti_result)

# Gaussian fitting results
print(q_mle.gauss_result_name)
print('')
print(q_mle.gauss_result)

# Gaussian fitting results
print(q_mle.gauss_result_name[::2])
print('')
print(q_mle.gauss_result_all)
print(np.shape(q_mle.gauss_result_all))

# line fitting results
print(q_mle.line_result_name)
print('')
print(q_mle.line_result)

fig, ax = plt.subplots(1, 1, figsize=(8, 5))

if q_mle.MCMC:
    gauss_result = q_mle.gauss_result[::2]
else:
    gauss_result = q_mle.gauss_result

# Plot individual line components
for p in range(int(len(gauss_result) / 3)):
    if q_mle.CalFWHM(gauss_result[3 * p + 2]) < narrow_line_velocity_limit:  # < 1200 km/s narrow
        color = 'g'  # narrow
    else:
        color = 'r'  # broad
    ax.plot(q_mle.wave, q_mle.Onegauss(np.log(q_mle.wave), gauss_result[p * 3:(p + 1) * 3]), color=color)

# Plot total line model
# ax.plot(q_mle.wave, q_mle.Manygauss(np.log(q_mle.wave), gauss_result), 'b', lw=2)
# ax.plot(q_mle.wave, q_mle.line_flux, 'k')
# ax.set_xlim(4640, 5100)
# ax.set_xlabel(r'$\rm Rest \, Wavelength$ ($\rm \AA$)', fontsize=20)
# ax.set_ylabel(r'$\rm f_{\lambda}$ ($\rm 10^{-17} erg\;s^{-1}\;cm^{-2}\;\AA^{-1}$)', fontsize=20)
# plt.savefig("result.pdf", format="pdf")
"""
Line properties
"""

# The line_prop function is used to calculate the broad line properties
# (defined, by default, as ln sigma > 0.0012 (1200 km/s) )

# OLD WAY: If you want to calculate the paramters of broad Hb
# then find all the broad Hb component, i.e., Hb_br_[1,2,3]_[scale,centerwave,sigma]
# for here q.line_result_name[12:15], q.line_result[12:15] is the broad Hb
# If MCMC=False, this would be:
# fwhm, sigma, ew, peak, area = q.line_prop(q.linelist[6][0], q.line_result[12:15], 'broad')

# NEW WAY: using line_prop_from_name convenience function
fwhm, sigma, ew, peak, area, snr = q_mle.line_prop_from_name('Hb_br', 'broad')

print("Broad Hb:")
print("FWHM (km/s)", np.round(fwhm, 1))
print("Sigma (km/s)", np.round(sigma, 1))
print("EW (A)", np.round(ew, 1))
print("Peak (A)", np.round(peak, 1))
print("Area (10^(-17) erg/s/cm^2)", np.round(area, 1))
print("SNR", np.round(snr, 1))
print("")

# NEW WAY: using line_prop_from_name convenience function
fwhm, sigma, ew, peak, area, snr = q_mle.line_prop_from_name('Hb_na', 'narrow')

print("Narrow Hb:")
print("FWHM (km/s)", np.round(fwhm, 1))
print("Sigma (km/s)", np.round(sigma, 1))
print("EW (A)", np.round(ew, 1))
print("Peak (A)", np.round(peak, 1))
print("Area (10^(-17) erg/s/cm^2)", np.round(area, 1))
print("SNR", np.round(snr, 1))
print("")

# OLD WAY: If you want to calculate the  the narrow [OIII]5007
# If MCMC=False, this would be:
# the coresponding parameters are  q.line_result_name[21:24], q.line_result[21:24]
# fwhm, sigma, ew, peak, area = q.line_prop(q.linelist[6][0], q.line_result[21:24], 'narrow')

fwhm, sigma, ew, peak, area, snr = q_mle.line_prop_from_name('OIII5007w', 'broad')

print("Broad [OIII]5007:")
print("FWHM (km/s)", np.round(fwhm, 1))
print("Sigma (km/s)", np.round(sigma, 1))
print("EW (A)", np.round(ew, 1))
print("Peak (A)", np.round(peak, 1))
print("Area (10^(-17) erg/s/cm^2)", np.round(area, 1))
print("SNR", np.round(snr, 1))
print("")

fwhm, sigma, ew, peak, area, snr = q_mle.line_prop_from_name('OIII5007c', 'narrow')

print("Narrow [OIII]5007:")
print("FWHM (km/s)", np.round(fwhm, 1))
print("Sigma (km/s)", np.round(sigma, 1))
print("EW (A)", np.round(ew, 1))
print("Peak (A)", np.round(peak, 1))
print("Area (10^(-17) erg/s/cm^2)", np.round(area, 1))
print("SNR", np.round(snr, 1))

# Statistical uncertainty visualization.  PyQSOFit's MC/MCMC samples are held
# in memory; write compact per-realization line fluxes so the uncertainty is
# inspectable instead of only being collapsed into a single error bar.
try:
    if getattr(q_mle, "MC", False) and len(getattr(q_mle, "gauss_result_all", [])):
        import csv as _csv
        import numpy as _np
        _mc_lines = [("Hb_br", "broad"), ("Hb_na", "narrow"),
                     ("OIII5007w", "broad"), ("OIII5007c", "narrow"),
                     ("MgII_br", "broad"), ("MgII_na", "narrow")]
        _mc_rows = []
        for _i in range(len(q_mle.gauss_result_all)):
            for _nm, _ct in _mc_lines:
                try:
                    _f, _s, _e, _p, _a, _sn = q_mle.line_prop_from_name(_nm, _ct, sample_index=_i)
                    _mc_rows.append({"sample": _i, "line": _nm, "component": _ct,
                                     "area_1e17": float(_a), "fwhm_kms": float(_f),
                                     "snr": float(_sn)})
                except Exception:
                    pass
        if _mc_rows:
            with open("pyqsofit_mc_samples.csv", "w", newline="") as _fh:
                _w = _csv.DictWriter(_fh, fieldnames=list(_mc_rows[0]))
                _w.writeheader(); _w.writerows(_mc_rows)
            _sum = []
            for _nm, _ct in _mc_lines:
                _v = _np.array([_r["area_1e17"] for _r in _mc_rows
                                if _r["line"] == _nm and _r["component"] == _ct], float)
                if _v.size:
                    _sum.append({"line": _nm, "component": _ct, "n": int(_v.size),
                                 "median": float(_np.nanmedian(_v)),
                                 "p16": float(_np.nanpercentile(_v, 16)),
                                 "p84": float(_np.nanpercentile(_v, 84))})
            with open("pyqsofit_mc_summary.csv", "w", newline="") as _fh:
                _w = _csv.DictWriter(_fh, fieldnames=list(_sum[0])); _w.writeheader(); _w.writerows(_sum)
            _fig, _axs = plt.subplots(1, 3, figsize=(11, 3.2))
            for _ax, (_nm, _ct) in zip(_axs, _mc_lines[:3]):
                _v = _np.array([_r["area_1e17"] for _r in _mc_rows
                                if _r["line"] == _nm and _r["component"] == _ct], float)
                _v = _v[_np.isfinite(_v)]
                if _v.size:
                    _ax.hist(_v, bins=min(20, max(5, _v.size // 5)), color="C0", alpha=0.75)
                    _ax.axvline(_np.median(_v), color="C3", lw=1)
                    _ax.set_title(f"{_nm} ({_ct})")
                    _ax.set_xlabel("area (1e-17 erg/s/cm2)")
            _fig.suptitle("PyQSOFit Monte Carlo realizations")
            _fig.tight_layout()
            _fig.savefig("pyqsofit_mc.png", dpi=140)
            _fig.savefig("pyqsofit_mc.pdf"); plt.close(_fig)
            print("wrote pyqsofit_mc_samples.csv / pyqsofit_mc_summary.csv / pyqsofit_mc.png")
except Exception as _e:
    print("could not write PyQSOFit MC products:", _e)

# Compact per-line table for cross-tool comparison.  Both broad and narrow
# components are recorded; the narrow C III]/Mg II areas are the quantities
# directly comparable to SDSS ZLINE.
try:
    import csv as _csv
    _recs = []
    for _name in ("MgII_br", "MgII_na", "CIII_br", "CIII_na",
                  "CIV_br", "CIV_na", "Lya_br", "Lya_na",
                  "Hb_br", "Hb_na", "OIII5007w", "OIII5007c"):
        _comp = "broad" if _name.endswith("_br") or _name.endswith("w") else "narrow"
        try:
            _fwhm, _sigma, _ew, _peak, _area, _snr = q_mle.line_prop_from_name(_name, _comp)
            _recs.append({"line": _name, "component": _comp,
                          "area_1e17": float(_area), "fwhm_kms": float(_fwhm),
                          "snr": float(_snr)})
        except Exception:
            continue
    with open("pyqsofit_lines.csv", "w", newline="") as _fh:
        _w = _csv.DictWriter(_fh, fieldnames=["line", "component", "area_1e17", "fwhm_kms", "snr"])
        _w.writeheader(); _w.writerows(_recs)
    print("wrote pyqsofit_lines.csv")
except Exception as _e:
    print("could not write pyqsofit_lines.csv:", _e)
