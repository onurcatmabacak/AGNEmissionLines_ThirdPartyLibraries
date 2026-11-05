# Run PyQSOFitSpec
# Modified by: Suk Yee Yong
# Updated: 31 Mar 2026
# Usage: python main.py [PATH_FITSFILE]


import numpy as np
import glob, os, sys, time
from pathlib import Path
from astropy.io import fits
from astropy import units as u
from astropy.io import ascii 
from astropy.table import Table
from PyQSOFitSpec import QSOFit
import warnings
warnings.filterwarnings("ignore")


if len(sys.argv) == 2:
    path_fits = sys.argv[1]
    # Search for all fits in directory
    if os.path.isdir(path_fits):
        spec = sorted(glob.glob(os.path.join(path_fits, "spec-*.fits")))
    # For single file
    else:
        spec = [path_fits]
# Search for all fits in current directory
else:
    spec = sorted(glob.glob(os.path.join(os.getcwd(), "spec-*.fits")))
    assert len(spec) != 0, "No fits file found in current directory!"

#------configs-----------------
# set up paths for each directory 
list_dirpaths = {
    'pyqsofit': os.path.dirname(os.path.abspath(__file__)), # PyQSOFitSpec code in same dir as main.py
    'fits': os.path.dirname(os.path.abspath(spec[0])), # fits file
}
list_dirpaths |= {
    'sfd': list_dirpaths['pyqsofit'], # Dusp reddening map
    'out_fit': list_dirpaths['fits'], # Output fitting
    'out_fig': list_dirpaths['fits'], # Output figures
    'out_result': list_dirpaths['fits'], # Output result
}
save_resultfilename = 'pyqsofitspec_out.csv'

# Set up line fitting options
nboot_fit = 50 # Number of bootstrap to fit individual line
linemodel = 'skewnorm_model' # 'gauss_model', 'skewnorm_model'
save_fig = True
save_fits = False

# To calculate the sigval needed given the FWHM
# fwhm = 600
# print(f"FWHM={fwhm} to log(sigma)={callogsigma(fwhm):g} [km/s]")

# Select lines to fit
newdata = np.rec.array([
    (2798.75, 'MgII', 2700., 2900., 'MgII_br', 1, '[0.004, 0.05]', 0.015, '0', '0.05'),
    # (2798.75, 'MgII', 2700., 2900., 'MgII_na', 1, '[3.3e-4, 8.e-4]', 0.01, '0', '0.002'),
    
    (1908.73, 'CIII', 1700., 1970., 'CIII_br', 1, '[0.004, 0.05]', 0.015, '0', '0.05'),
    # (1908.73, 'CIII', 1700., 1970., 'CIII_na', 1, '[3.3e-4, 1.6e-3]', 0.01, '0', '0.002'),
    # (1892.03,'CIII',1700.,1970.,'SiIII1892',1,'[0.001, 0.015]', 0.003, '0', '0.005'),
    (1857.40,'CIII',1700.,1970.,'AlIII1857',1,'[0.001, 0.015]', 0.003, '0', '0.005'),
    # (1816.98,'CIII',1700.,1970.,'SiII1816',1,'[0.001, 0.015]', 0.01, '0', '0.003'),
    # (1786.7,'CIII',1700.,1970.,'FeII1787',1,'[0.001, 0.015]', 0.01, '0', '0.003'),
    # (1750.26,'CIII',1700.,1970.,'NIII1750',1,'[0.001, 0.015]', 0.01, '0', '0.001'),
    # (1718.55,'CIII',1700.,1900.,'NIV1718',1,'[0.001, 0.015]', 0.01, '0', '0.001'),
    
    (1549.06, 'CIV', 1400., 1700., 'CIV_br', 1, '[0.004, 0.05]', 0.015, '0', '0.05'),
    # (1549.06, 'CIV', 1400., 1700., 'CIV_na', 1, '[3.3e-4, 1.6e-3]', 0.01, '0', '0.002'),
    # (1640.42, 'CIV', 1400., 1700., 'HeII1640', 1, '[0.0005, 0.0017]', 0.008, '0', '0.002'),
    # (1663.48,'CIV',1500.,1700.,'OIII1663',1,'[0.0005, 0.0017]', 0.008, '0', '0.002'),
    (1640.42, 'CIV', 1400., 1700., 'HeII1640_br', 1, '[0.0025, 0.02]', 0.008, '0', '0.002'),
    # (1663.48,'CIV',1500.,1700.,'OIII1663_br',1,'[0.0025, 0.02]', 0.008, '0', '0.002'),
    
    # These are extra lines to demonstrate absorption
    # (1436.06, 'CIV', 1400., 1700., 'CIV_abs', 1, '[0.004, 0.05]', 0.015, '0', '-0.05'),
    # (1556.06, 'CIV', 1400., 1700., 'CIV_na_r', 1, '[5e-4, 0.0017]', 0.01, '0', '-0.02'),
    # (1541.06, 'CIV', 1400., 1700., 'CIV_na_b', 1, '[5e-4, 0.0017]', 0.01, '0', '-0.02'),
    
    # (1402.06, 'SiIV', 1290., 1450., 'SiIV_OIV1', 1, '[0.002, 0.05]', 0.015, '0', '0.05'),
    # (1396.76, 'SiIV', 1290., 1450., 'SiIV_OIV2', 1, '[0.002, 0.05]', 0.015, '0', '0.05'),
    # (1335.30, 'SiIV', 1290., 1450., 'CII1335', 1, '[0.001, 0.015]', 0.01, '0', '0.001'),
    # (1304.35,'SiIV',1290.,1450.,'OI1304',1,'[0.001, 0.015]', 0.01, '0', '0.001'),
    
    # (1215.67, 'Lya', 1150., 1290., 'Lya_br', 1, '[0.004, 0.05]', 0.02, '0', '0.05'),
    # (1215.67, 'Lya', 1150., 1290., 'Lya_na', 1, '[0.0005, 0.0017]', 0.01, '0', '0.002'),
    ],
    formats='float32,a20,float32,float32,a20,float32,a20,float32,a20,a20,',
    names='lambda,compname,minwav,maxwav,linename,ngauss,sigval,voff,iniskw,fvalue')


#------functions-----------------
def callogsigma(fwhm):
    """Calculate log(sigma) from FWHM in km/s"""
    return np.log(fwhm/(2.*300000.*np.sqrt(2.*np.log(2))) + 1.)

def run_qsofit(lam, flux, err, z, plateid=None, mjd=None, fiberid=None, MC=False, save_fig=False):
    """Run QSOFit and return emission line properties [[line1_prop1, ...], [line1_prop_err1, ...]], ..."""
    
    t0 = time.time()
    q = QSOFit(lam, flux, err, z, plateid=int(plateid), mjd=int(mjd), fiberid=int(fiberid), path=list_dirpaths['pyqsofit'])
    q.Fit(
        name=None, nsmooth=1, and_or_mask=False, deredden=False, reject_badpix=False, wave_range=None, 
        wave_mask=None, decomposition_host=False, Mi=None, npca_gal=5, npca_qso=20, Fe_uv_op=True, poly=True, 
        BC=False, rej_abs=False, initial_guess=None, MC=MC, n_trials=5, linemodel=linemodel, linefit=True, 
        save_result=True, plot_fig=save_fig, save_fig=save_fig, plot_line_name=True, plot_legend=True, 
        dustmap_path=list_dirpaths['sfd'], save_fig_path=list_dirpaths['out_fig'], save_fits_path=list_dirpaths['out_fit'], save_fits_name=save_fits
    )
    print(f"\tFit time >> {time.time() - t0:.4f} s")
    
    # output results from q.Fit
    ciii_br_prop = q.get_line_profile("CIII_br", "broad")[:,:nprop_columns]
    # ciii_na_prop = q.get_line_profile("CIII_na", "narrow")[:,:nprop_columns]
    civ_br_prop = q.get_line_profile("CIV_br", "broad")[:,:nprop_columns]
    # civ_na_prop = q.get_line_profile("CIV_na", "narrow")[:,:nprop_columns]
    mgii_br_prop = q.get_line_profile("MgII_br", "broad")[:,:nprop_columns]
    # mgii_na_prop = q.get_line_profile("MgII_na", "narrow")[:,:nprop_columns]
    # aliii_prop = q.get_line_profile("AlIII1857", "broad")[:,:nprop_columns]
    
    return ciii_br_prop, civ_br_prop, mgii_br_prop

def line_dict(line, comp, line_prop):
    """Create key value pairs of lines"""
    
    line_prop = np.asarray(line_prop)
    line_kv = {}
    # Shape line_prop [NSAMPLE, 2, nprop_columns]
    if np.ndim(line_prop) == 2:
        line_prop = line_prop[np.newaxis, :]
    line_val, line_val_err = zip(*line_prop[:,0]), zip(*line_prop[:,1])
    
    for p, l, le in zip(prop_columns, line_val, line_val_err):
        line_kv |= {f'{line}_{p}_{comp}': l, f'{line}_{p}_{comp}_err': le}
    
    return line_kv


#------header-----------------
hdr = fits.Header()
hdr['lambda'] = 'Vacuum Wavelength in Ang'
hdr['minwav'] = 'Lower complex fitting wavelength range'
hdr['maxwav'] = 'Upper complex fitting wavelength range'
hdr['ngauss'] = 'Number of Gaussians for the line'
hdr['inisig'] = 'Initial guess of linesigma [in lnlambda]'
hdr['minsig'] = 'Lower range of line sigma [lnlambda]'  
hdr['maxsig'] = 'Upper range of line sigma [lnlambda]'
hdr['voff  '] = 'Limits on velocity offset from the central wavelength [lnlambda]'
hdr['iniskw'] = 'Initial guess of lineskew'
hdr['vindex'] = 'Entries w/ same NONZERO vindex constrained to have same velocity'
hdr['windex'] = 'Entries w/ same NONZERO windex constrained to have same width'
hdr['findex'] = 'Entries w/ same NONZERO findex have constrained flux ratios'
hdr['fvalue'] = 'Relative scale factor for entries w/ same findex'
#------save line info-----------
hdu = fits.BinTableHDU(data=newdata, header=hdr, name='data')
hdu.writeto(os.path.join(list_dirpaths['pyqsofit'], 'qsopar2.fits'), overwrite=True)

# Create output result file
open(os.path.join(list_dirpaths['out_result'], save_resultfilename), 'w').close()

# Add properties and relevant lines to store
prop_columns = ['fwhm', 'sigma', 'skew', 'ew', 'peak']
nprop_columns = len(prop_columns)

# Fit each spectra
print(f"-----PyQSOFitSpec-----")
print(f"Line model >> {linemodel}")
print(f"FITS in directory >> {list_dirpaths['fits']}")
t0 = time.time()
spec_array = []
for ns, i in enumerate(spec, start=1):
    print(f"FIT SPEC#{ns} >> {i}")
    data = fits.open(i)
    lam = 10**data[1].data['loglam']        # OBS wavelength [A]
    flux = data[1].data['flux']             # OBS flux [erg/s/cm^2/A]
    err = 1./np.sqrt(data[1].data['ivar'])  # 1 sigma error
    z = data[2].data['z'][0]                # Redshift
    data.close()
    spec_filename = Path(i).stem
    
    if nboot_fit == 0:
        ciii_br_prop, civ_br_prop, mgii_br_prop = run_qsofit(lam, flux, err, z, *spec_filename.split('-')[-3:], MC=True, save_fig=save_fig)
    else:
        value_meanstd = lambda value: [np.mean(value, axis=0), np.std(value, axis=0)] # Get value [mean, std]
        ciii_br_prop_nboot = []
        civ_br_prop_nboot = []
        mgii_br_prop_nboot = []
        for nb in range(nboot_fit):
            print(f"#{nb} Iteration")
            flux_noise = [np.random.normal(f, fe) for f, fe in zip(flux, err)] # Resample flux by adding noise
            ciii_br_prop, civ_br_prop, mgii_br_prop = run_qsofit(lam, flux_noise, err, z, *spec_filename.split('-')[-3:], MC=False, save_fig=save_fig if nb==0 else False)
            # Store only values from bootstrap
            ciii_br_prop_nboot.append(ciii_br_prop[0])
            civ_br_prop_nboot.append(civ_br_prop[0])
            mgii_br_prop_nboot.append(mgii_br_prop[0])
        ciii_br_prop = value_meanstd(ciii_br_prop_nboot)
        civ_br_prop = value_meanstd(civ_br_prop_nboot)
        mgii_br_prop = value_meanstd(mgii_br_prop_nboot)
    
    # Write output result
    with open(os.path.join(list_dirpaths['out_result'], save_resultfilename), 'a') as f:
        f.seek(0, os.SEEK_END)
        Table({'spectra': [spec_filename], **line_dict('ciii', 'br', ciii_br_prop), **line_dict('civ', 'br', civ_br_prop), **line_dict('mgii', 'br', mgii_br_prop)}).write(f, format='ascii.csv' if ns==1 else 'ascii.no_header', delimiter=',')


print(f"Number of fitted spec >> {ns}")
print(f"Total time >> {time.time() - t0:.4f} s")
print(f"Saved output results >> {os.path.join(list_dirpaths['out_result'], save_resultfilename)}")

