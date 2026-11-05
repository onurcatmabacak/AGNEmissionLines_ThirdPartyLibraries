#Before starting, we call some of the standard python packages, such as matplotlib, pandas, numpy, etc.
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)
from natsort import natsorted
import numpy as np
import pandas as pd
import os
import glob
import json
from multiprocessing import Pool, cpu_count

os.makedirs("./output", exist_ok=True)  # Creates folder, doesn't raise error if it already exists

# Below command import the above mentioned reading commands
from fantasy_agn.tools import read_sdss, read_text, read_gama_fits

# Below command import the necessary commands, which will be described later
from fantasy_agn.models import create_input_folder, automatic_path

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

s.CorRed()

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
plt.xlim(2900, 7500)
plt.savefig("output/result.pdf", format="pdf")

create_input_folder(xmin=3000,xmax=7500, path_to_folder='output/')
# cont=continuum(s, min_refer=5690, refer=5700, max_refer=5710)
cont=continuum(s)
broad=create_fixed_model(['hydrogen.csv'], name='br')
he=create_fixed_model(['helium.csv'], name='he',fwhm=3000, min_fwhm=1000, max_fwhm=5000)
narrow=create_tied_model(name='OIII5007',files=['narrow_basic.csv','hydrogen.csv'],prefix='nr', fwhm=1000,min_offset=0, max_offset=300, min_fwhm=100, max_fwhm=1200,fix_oiii_ratio=True, position=5008, included=True,min_amplitude=0.2)
fe=create_feii_model(name='feii', fwhm=1800, min_fwhm=1000, max_fwhm=2000, offset=0, min_offset=-3000, max_offset=3000)
#fe.amp_b4p.min=10 #An example how to force the amplitude of a selected FeII multiplet.

# Code fits simultaneously all features.
model = cont+broad+narrow+fe+he

s.fit(model, ntrial=2)

plt.style.context(['nature', 'notebook'])
plt.figure(figsize=(18,8))
plt.plot(s.wave, s.flux, color="#929591", label='Obs', lw=2)
plt.plot(s.wave, model(s.wave), color="#F10C45",label='Model',lw=3)
plt.plot(s.wave, model(s.wave)-s.flux-1, '-',color="#929591", label='Residual', lw=2)
plt.axhline(y=-70, color='deepskyblue', linestyle='--', lw=2)

plt.plot(s.wave, cont(s.wave),'--',color="#042E60",label='Continuum', lw=3)
plt.plot(s.wave, narrow(s.wave),label='Narrow',color="#25A36F",lw=3)
plt.plot(s.wave, broad(s.wave), label='Broad H', lw=3, color="#2E5A88")
plt.plot(s.wave, he(s.wave), label='Broad He I', lw=3, color="orange")
plt.plot(s.wave, fe(s.wave),'-',color="#CB416B",label='Fe II model', lw=3)

plt.xlabel('Rest Wavelength',fontsize=20)
plt.ylabel('Flux',fontsize=20)
plt.xlim(2900,7500)
plt.ylim(-3,9)
plt.tick_params(which='both', direction="in")
plt.yticks(fontsize=20)
plt.xticks(np.arange(3000, 7500, step=500),fontsize=20)
plt.legend(loc='upper left',  prop={'size': 16}, frameon=False, ncol=2)

plt.savefig('./fantasy_fit.pdf')

print(model)

print(s.gres.format())
s.save_json() #saving parameters

# Integrate total FeII model,
flux_feII=np.sum(fe(s.wave))
print("FeII total flux=",flux_feII)

# Mask the wavelength range of interess (e.g. Ha line) and integrate broad component.
x=s.wave
mask_ha=(x>6300)&(x<6700)
Ha_broad=np.sum(broad(s.wave)[mask_ha])
print("Ha_broad=",Ha_broad)
