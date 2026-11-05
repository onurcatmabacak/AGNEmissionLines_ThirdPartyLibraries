import numpy as np
from astropy.io import fits
from astropy import units as u
import matplotlib.pyplot as plt


def read_sdss(filename):
    
    hdulist = fits.open(filename)
    hdu = hdulist[1]
    data = hdu.data
    z = hdulist[2].data["redshift"][0]
    ra = hdulist[0].header["plug_ra"]
    dec = hdulist[0].header["plug_dec"]
    mjd = hdulist[0].header["mjd"]
    plate = hdulist[0].header["plateid"]
    fiber = hdulist[0].header["fiberid"]
    name = filename.split(".")[0]
    try:
        y = data.flux
        x = data.wl
        iv = data.stdev
    except AttributeError:
        y = data.FLUX
        x = data.WL
        iv = data.STDEV
    super_threshold_indices = iv == 0
    iv[super_threshold_indices] = np.median(iv)
    err = 1.0 / np.sqrt(iv)
    flux = y
    wave = x
    c = 299792.458
    wdisp = data["wdisp"]
    frac = wave[1] / wave[0]
    dlam = (frac - 1) * wave
    fwhm = 2.355 * wdisp * dlam
    velscale = np.log(frac) * c
    fwhm = fwhm
    velscale = velscale
    hdulist.close()

    return wave, flux, err, z, ra, dec, mjd, plate, fiber, name

# Input Parameters
redshift = 0.3482135
ebv = 0.45
fwhm_res_nm = 114  # Using FWHM from Bessel B filter as an example (in nm)
fwhm_res_angstrom = fwhm_res_nm * 10  # Convert to Angstrom
flux_norm = 1e0  # Normalization factor for flux

# Parse the text data
wavelength, flux = np.genfromtxt('spec.txt', delimiter='', usecols=(0, 1), skip_header=0, unpack=True)
# obs_wavelength = obs_wavelength / (1.0 + redshift)  # Shift to rest-frame wavelength
#obs_flux *= 1e17  # Scale flux for easier handling
flux /= 1e-17
wavelength = wavelength * u.Angstrom
flux = flux * u.erg / u.s / u.cm**2 / u.AA
# Compute additional columns
ivar = np.ones_like(flux.value)         # assuming uniform inverse variance
wdisp = np.full_like(wavelength.value, 1e-4)  # a constant dispersion value

# Create primary HDU with required header keywords
hdr = fits.Header()
hdr["plug_ra"] = 48.4973354175    # dummy right ascension
hdr["plug_dec"] = 08.399199559    # dummy declination
hdr["mjd"] = 55000        # dummy MJD value
hdr["plateid"] = 1000     # dummy plate id
hdr["fiberid"] = 50       # dummy fiber id
primary_hdu = fits.PrimaryHDU(header=hdr)

# Create binary table for the first extension (HDU1)
col_flux = fits.Column(name='flux', array=flux, format='E')
col_wavelength = fits.Column(name='wl', array=wavelength, format='E')
col_ivar = fits.Column(name='stdev', array=ivar, format='E')
col_wdisp = fits.Column(name='wdisp', array=wdisp, format='E')
cols1 = fits.ColDefs([col_flux, col_wavelength, col_ivar, col_wdisp])
hdu1 = fits.BinTableHDU.from_columns(cols1)

# Create binary table for the second extension (HDU2) with the redshift value
col_z = fits.Column(name='redshift', array=np.array([redshift]), format='E')
hdu2 = fits.BinTableHDU.from_columns([col_z])

# Combine HDUs and write to a new FITS file
hdul = fits.HDUList([primary_hdu, hdu1, hdu2])
hdul.writeto("../spec1d.sdss.sdss.fiber1.1.fits", overwrite=True)

data = read_sdss("../spec1d.sdss.sdss.fiber1.1.fits")
print(data)