#Before starting, we call some of the standard python packages, such as matplotlib, pandas, numpy, etc.
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)

import numpy as np
import pandas as pd
import os
import glob

os.makedirs("./output", exist_ok=True)  # Creates folder, doesn't raise error if it already exists

# Below command import the above mentioned reading commands
from fantasy_agn.tools import read_sdss, read_text, read_gama_fits

# Below command import the necessary commands, which will be described later
from fantasy_agn.models import create_input_folder

from fantasy_agn.models import create_feii_model, create_model, create_tied_model, continuum, create_line, create_fixed_model

# This command reads the spectrum with the listed name, from the folder of this notebook or
# from the given path e.g.,'/path/to/files/spec*.txt'

s=read_sdss('my_sdss.fits')

# We use for input models selected line lists, for which we provide air wavelengths; if your spectrum is in vacuum
# wavelengths, this command transform them to air wavelengths: s.vac_to_air()
# NOTE that read_sdss() transform to air wavelengths by default.

# DeRedden() command corrects for the Galactic extinction, based on coordinates of the object provided in the fits,
# which will be automatically derived from dust map data from Schlegel, Finkbeiner, Davis (1998).
# If coordinates are not available you could manually insert them using simple commands s.ra=xxx.xxx, s.dec=xxx.xxx

# s.ra=29.519807539582 #example input of arbitrary rightascension
# s.dec=-0.872742349310271 #example input of arbitrary declination

# s.DeRedden()

# CorRed() corrects for the cosmological redshift, based on redshift of the object provided in the fits.
# If coordinates are not available you could manually insert them using simple command s.z=x.xxx

# s.z=0.0804 #example input of arbitrary redshift

# s.CorRed()

# Useful tip is to avoid using very small flux units.
# e.g., SDSS spectra are given in 1e-17 erg/s/cm2/A and these are already scaled within read_sdss()
# s.crop(2900,10000)
s.flux=s.flux * (10**17)
print(s.wave)
#s.restore() #command which restor to the original spectrum, before host-galaxy removal;
# s.fit_host_sdss()
# s.host_no_mask = s.host
# s.restore() #command to restore the spectrum before host galaxy fitting and substraction
# s.fit_host_sdss(mask_host=True, custom=False)

#Let's plot the spectrum for visual inspection.

# plt.style.context(['nature', 'notebook'])
# plt.figure(figsize=(12,6))
plt.plot(s.wave, s.flux, color="grey", label='Obs', lw=1)
# plt.plot(s.wave, s.host_no_mask, color="red", label='Host no mask', lw=0.5)
# plt.plot(s.wave, s.host, color="blue", label='Host masked', lw=0.5)
plt.legend(loc='upper left',  prop={'size': 12}, frameon=False, ncol=2)
plt.xlim(2900, 10100)
plt.savefig("output/result.pdf", format="pdf")


