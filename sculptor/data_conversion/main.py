from astropy.io import fits
import numpy as np
import astropy.units as u
import pandas as pd

def read_sdss_fits(filename):
        """Read in an SDSS/BOSS fits spectrum as a SpecOneD object.

        :param filename: Filename of the fits file.
        :type filename: str
        :return:

        :raises ValueError: Raises an error when the filename could not be \
        read in.
        """

        # Open the fits file
        try:
            hdu = fits.open(filename)
        except:
            raise ValueError("Filename not found", str(filename))

        fluxden = np.array(hdu[1].data['flux'], dtype=np.float64)
        dispersion = 10**np.array(hdu[1].data['loglam'], dtype=np.float64)
        ivar = np.array(hdu[1].data['ivar'], dtype=np.float64)
        fluxden_err = 1/np.sqrt(ivar)

        mask = np.ones(dispersion.shape, dtype=bool)

        # Add header information to SpecOneD
        header_df = pd.DataFrame(list(hdu[0].header.items()),
                                 index=list(hdu[0].header.keys()),
                                 columns=['property', 'value'])
        header_df.drop(columns='property', inplace=True)
        header = header_df
        fits_header = hdu[0].header

        dispersion_unit = 1. * u.AA
        fluxden_unit = 1e-17 * u.erg / u.s / u.cm ** 2 / u.AA

        return header, fluxden * fluxden_unit, dispersion * dispersion_unit, fluxden_err * fluxden_unit

# Input Parameters
redshift = 0.348

# Parse the text data
obs_wavelength, obs_fluxden = np.genfromtxt('spec.txt', delimiter='', usecols=(0, 1), skip_header=0, unpack=True)

# obs_wavelength = obs_wavelength / (1.0 + redshift) * u.AA
obs_wavelength = obs_wavelength * u.AA
obs_fluxden = obs_fluxden * 1e17 * u.Unit('erg cm-2 s-1 AA-1')

ivar = 1.0 / (0.1 * obs_fluxden)**2.0

# Ensure all arrays have the same length
assert len(obs_wavelength) == len(obs_fluxden) == len(ivar), "Arrays must have the same length"

# Convert wavelength to log10 scale (SDSS spectra are log-linear)
loglam = np.log10(obs_wavelength.value)

# Create column definitions for the binary table
col1 = fits.Column(name='flux', format='D', array=obs_fluxden.value)  # Flux density (double precision)
col2 = fits.Column(name='loglam', format='D', array=loglam)  # Log10 of wavelength (double precision)
col3 = fits.Column(name='ivar', format='D', array=ivar)  # Inverse variance (double precision)

# Create the binary table HDU
cols = fits.ColDefs([col1, col2, col3])
table_hdu = fits.BinTableHDU.from_columns(cols)

# Create the primary HDU (empty, but required for valid FITS file)
primary_hdu = fits.PrimaryHDU()

# Set header information in the primary HDU
primary_hdr = primary_hdu.header
primary_hdr['Z'] = redshift  # Store redshift
primary_hdr['BUNIT'] = '10^-17 erg/s/cm^2/Ang'  # Flux units
primary_hdr['COMMENT'] = 'FITS file with flux, loglam, and ivar in binary table'

# Create HDUList and save to file
hdulist = fits.HDUList([primary_hdu, table_hdu])
hdulist.writeto('spectrum.fits', overwrite=True)
print("FITS file 'spectrum.fits' created successfully.")

data = read_sdss_fits(filename='spectrum.fits')
print(data)