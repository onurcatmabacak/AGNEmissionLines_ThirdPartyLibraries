from astropy.io import fits
import numpy as np

file = 'my_sdss_onur.fits'
hdulist = fits.open(file)
header = hdulist[0].header

print(header)

z = float(hdulist[2].data["z"][0])
print(z)

flux_norm = 1.0e-17
spec = hdulist[1].data["flux"] / flux_norm
wave = 10 ** hdulist[1].data["loglam"]
err = 0.1 * spec

print(hdulist[1].data["flux"])
print(hdulist[1].data["loglam"])
print(hdulist[1].data["ivar"])

 flux = np.log10(hdulist[1].data["flux"])



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
col_loglam = fits.Column(name='loglam', array=loglam, format='E')
col_ivar = fits.Column(name='ivar', array=ivar, format='E')
col_wdisp = fits.Column(name='wdisp', array=wdisp, format='E')
cols1 = fits.ColDefs([col_flux, col_loglam, col_ivar, col_wdisp])
hdu1 = fits.BinTableHDU.from_columns(cols1)

# Create binary table for the second extension (HDU2) with the redshift value
col_z = fits.Column(name='z', array=np.array([redshift]), format='E')
hdu2 = fits.BinTableHDU.from_columns([col_z])

# Combine HDUs and write to a new FITS file
hdul = fits.HDUList([primary_hdu, hdu1, hdu2])
hdul.writeto("my_sdss.fits", overwrite=True)

data = read_sdss("my_sdss.fits")
print(data)