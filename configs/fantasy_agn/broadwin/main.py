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

unit = "my_sdss.fits"
print(unit)

#  reads an AGN spectrum, corrects for Galactic extinction, redshift, and host galaxy
s=read_sdss(unit)
s.err=np.abs(s.err) #make sure that all errors are positive
s.flux = s.flux * 1e17
# s.DeRedden()
s.CorRed()
# s.fit_host_sdss()
# plt.title(s.name.split('/')[-1].split('.')[0])
# plt.savefig("./output/" + s.name + '_host.pdf')
print(s.err)
# crops a spectrum, and creates automatic path of the input line lists
s.crop(2900,8000)
automatic_path(s)
create_input_folder(xmin=3000,xmax=7500, path_to_folder='output/')

ampl = 3
min_ampl = 0
max_ampl = 50
fwhm_br = 1500
fwhm_na = 500
min_fwhm_br = 400
min_fwhm_na = 100
max_fwhm_br = 6000
max_fwhm_na = 1500
offset = 0
min_offset = -1500      # allow blue-shifted wing components
max_offset = 500
# defines fitting model
# cont = continuum(s,min_refer=5350, refer=5550, max_refer=5650,min_index1=-3.7, max_index1=1,max_index2=3)
cont = continuum(s)
broad = create_model(['hydrogen.csv', 'helium.csv'], prefix='br', amplitude=ampl, min_amplitude=min_ampl, max_amplitude=max_ampl, fwhm=fwhm_br, min_fwhm=min_fwhm_br, max_fwhm=max_fwhm_br, offset=offset, min_offset=min_offset, max_offset=max_offset)
narrow = create_tied_model(name='OIII5007',files=['narrow_basic.csv','hydrogen.csv', 'helium.csv'],prefix='nr',amplitude=ampl, min_amplitude=min_ampl, max_amplitude=max_ampl, fwhm=fwhm_na, min_fwhm=min_fwhm_na, max_fwhm=max_fwhm_na, offset=offset, min_offset=min_offset, max_offset=max_offset)

hbeta_br = create_line(name="HBeta4834_br",pos=4834, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_br, min_fwhm=min_fwhm_br, max_fwhm=max_fwhm_br, offset=offset, min_offset=min_offset, max_offset=max_offset)
OIIIa_br = create_line(name="OIIIa4958_br",pos=4958, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_br, min_fwhm=min_fwhm_br, max_fwhm=max_fwhm_br, offset=offset, min_offset=min_offset, max_offset=max_offset)
OIIIb_br = create_line(name="OIIIb5007_br",pos=5007, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_br, min_fwhm=min_fwhm_br, max_fwhm=max_fwhm_br, offset=offset, min_offset=min_offset, max_offset=max_offset)
halpha_br = create_line(name="HAlpha6551_br",pos=6551, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_br, min_fwhm=min_fwhm_br, max_fwhm=max_fwhm_br, offset=offset, min_offset=min_offset, max_offset=max_offset)
hbeta_na = create_line(name="HBeta4834_na",pos=4834, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_na, min_fwhm=min_fwhm_na, max_fwhm=max_fwhm_na, offset=offset, min_offset=min_offset, max_offset=max_offset)
OIIIa_na = create_line(name="OIIIa4958_na",pos=4958, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_na, min_fwhm=min_fwhm_na, max_fwhm=max_fwhm_na, offset=offset, min_offset=min_offset, max_offset=max_offset)
OIIIb_na = create_line(name="OIIIb5007_na",pos=5007, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_na, min_fwhm=min_fwhm_na, max_fwhm=max_fwhm_na, offset=offset, min_offset=min_offset, max_offset=max_offset)
halpha_na = create_line(name="HAlpha6551_na",pos=6551, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_na, min_fwhm=min_fwhm_na, max_fwhm=max_fwhm_na, offset=offset, min_offset=min_offset, max_offset=max_offset)

# fe=create_feii_model(max_fwhm=6000)
model = cont + OIIIb_br + OIIIb_na + hbeta_br + halpha_br + hbeta_na + halpha_na + create_feii_model(fwhm=1000, min_fwhm=300, max_fwhm=6000, offset=0, min_offset=-800, max_offset=800)

# fits a spectrum with the above model, iterate 2 times
s.fit(model, ntrial=10)
print("fit ok")

# creates a file to save the fitting results of the original spectra
d={'wave':s.wave,'flux':s.flux,'error':s.err,'model':model(s.wave),'cont':cont(s.wave), 'OIIIb_br':OIIIb_br(s.wave), 'OIIIb_na':OIIIb_na(s.wave), 'hbeta_br':hbeta_br(s.wave), 'hbeta_na':hbeta_na(s.wave), 'halpha_br':halpha_br(s.wave), 'halpha_na':halpha_na(s.wave)}

df=pd.DataFrame(d)
df.to_csv("./output/" + s.name+'_model.csv')
dicte=zip(s.gres.parnames, s.gres.parvals)
res=dict(dicte)
res['redshift']= float(s.z)
res['RA']=float(s.ra)
res['dec']=float(s.dec)
res['fiber']=str(s.fiber)
res['mjd']=float(s.mjd)
res['plate']=str(s.plate)

# creates a file to save the fitting results of the original spectra
with open("./output/" + s.name + '_pars.json', 'w') as fp:
    json.dump(res, fp)

# creates N=500 mock spectra, fits the same model, and write the fitting results.
s.monte_carlo(nsample=50)
print("mcmc ok")

i=0
x_tics=np.linspace(3000,7500, 10)

for file in natsorted(glob.glob('./output/my*model.csv')):

    print(file)

    df=pd.read_csv(file)
    fluxnorm = 1
    # plt.style.use(['nature', 'science'])

    fig, ax =plt.subplots(figsize=(12,8))

    plt.plot(df.wave, df.flux * fluxnorm, '-', color="grey", label='Obs', lw=2)
    plt.plot(df.wave, df.model * fluxnorm, '-', color="black", label='Model', lw=2)

    plt.plot(df.wave, df.cont * fluxnorm, '-', color="red", label='Cont.', lw=2)
    # plt.plot(df.wave, df.narrow * fluxnorm, '-', color='lightblue', label='Narrow',lw=2)
    # plt.plot(df.wave, df.broad * fluxnorm, '-', color="magenta",label='Broad H', lw=2)
    # plt.plot(df.wave, df.fe * fluxnorm, '-', color='brown', label='Fe II', lw=2) 
    # plt.plot(df.wave, df.OIIIa_br * fluxnorm, '-', color='g', label='OIIIa BR', lw=1) 
    # plt.plot(df.wave, df.OIIIa_na * fluxnorm, '--', color='g', label='OIIIa NA', lw=1) 
    plt.plot(df.wave, df.OIIIb_br * fluxnorm, '-', color='r', label='OIIIb BR', lw=1) 
    plt.plot(df.wave, df.OIIIb_na * fluxnorm, '--', color='r', label='OIIIb NA', lw=1) 
    plt.plot(df.wave, df.hbeta_br * fluxnorm, '-', color='b', label='HBeta BR', lw=1) 
    plt.plot(df.wave, df.hbeta_na * fluxnorm, '--', color='b', label='HBeta NA', lw=1) 
    plt.plot(df.wave, df.halpha_br * fluxnorm, '-', color='k', label='HAlpha BR', lw=1) 
    plt.plot(df.wave, df.halpha_na * fluxnorm, '--', color='k', label='HAlpha NA', lw=1) 


    try:
        plt.plot(df.wave, df.fe_forb * fluxnorm, '-', color='xkcd:black', label='[Fe II]', lw=4)
    except:
        pass

    plt.xticks(x_tics, fontsize=24)
    plt.yticks(fontsize=24)
    plt.tick_params(which='both', direction="in")

    plt.ylim(-0.5, df.model.max() * fluxnorm * 1.1)
    plt.xlim(4500,7000)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())

    plt.legend(loc='upper left',  prop={'size': 16}, frameon=False, ncol=4)
    plt.xlabel(r'Rest wavelength ($\rm{\AA}$)', fontsize=24)
    plt.ylabel(r'$F_{\lambda}$ ($10^{-17}$ $\rm{erg s}^{-1}\rm{cm}^{-2}\rm{\AA}^{-1}$)', fontsize=24)

    plt.tight_layout()
    plt.savefig("./output/my_sdss.pdf", dpi=1200, bbox_inches='tight', format="pdf")
    i+=1
    # plt.show()
    # plt.close()
    # plt.clf()

print(model)