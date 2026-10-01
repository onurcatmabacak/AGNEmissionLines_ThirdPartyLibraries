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
s.fit_host_sdss(mask_host=True)   # subtract the SDSS host+QSO eigenspectrum model
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
max_ampl = 200          # was 50 -> broad Halpha amplitude pinned at the bound
fwhm_br = 1500
fwhm_na = 500
min_fwhm_br = 1200      # broad lines must be genuinely broad
min_fwhm_na = 70
max_fwhm_br = 8000
max_fwhm_na = 600       # was 2000 -> narrow Balmer FWHM inflated to 2-4x the [OIII]/[NII] width
offset = 0
min_offset = -1500      # allow blue-shifted wing components
max_offset = 500
# Narrow forbidden/Balmer lines are at the systemic velocity: keep them tight
# (a free +-1500 km/s let [OIII] drift to -790 km/s, off the observed doublet).
min_offset_na = -400
max_offset_na = 400
# defines fitting model
# cont = continuum(s,min_refer=5350, refer=5550, max_refer=5650,min_index1=-3.7, max_index1=1,max_index2=3)
cont = continuum(s)
broad = create_model(['hydrogen.csv', 'helium.csv'], prefix='br', amplitude=ampl, min_amplitude=min_ampl, max_amplitude=max_ampl, fwhm=fwhm_br, min_fwhm=min_fwhm_br, max_fwhm=max_fwhm_br, offset=offset, min_offset=min_offset, max_offset=max_offset)
narrow = create_tied_model(name='OIII5007',files=['narrow_basic.csv','hydrogen.csv', 'helium.csv'],prefix='nr',amplitude=ampl, min_amplitude=min_ampl, max_amplitude=max_ampl, fwhm=fwhm_na, min_fwhm=min_fwhm_na, max_fwhm=max_fwhm_na, offset=offset, min_offset=min_offset, max_offset=max_offset)

# Rest-frame AIR wavelengths: read_sdss converts vacuum->air and CorRed()
# divides by (1+z), so the internal frame is rest-frame air.
WB_HB, WB_HA, WB_O3A, WB_O3B, WB_N2A, WB_N2B = 4861.33, 6562.82, 4958.90, 5006.84, 6548.05, 6583.46

hbeta_br = create_line(name="HBeta4863_br",pos=WB_HB, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_br, min_fwhm=min_fwhm_br, max_fwhm=max_fwhm_br, offset=offset, min_offset=min_offset, max_offset=max_offset)
OIIIb_br = create_line(name="OIIIb5007_br",pos=WB_O3B, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_br, min_fwhm=min_fwhm_br, max_fwhm=max_fwhm_br, offset=offset, min_offset=min_offset, max_offset=max_offset)
# [OIII] 4959 is tied to 5007: 1/3 flux, same width and velocity.
OIIIa_br = create_line(name="OIIIa4959_br",pos=WB_O3A, ampl=OIIIb_br.ampl/3.0, fwhm=OIIIb_br.fwhm, offset=OIIIb_br.offs_kms)
halpha_br = create_line(name="HAlpha6565_br",pos=WB_HA, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_br, min_fwhm=min_fwhm_br, max_fwhm=max_fwhm_br, offset=offset, min_offset=min_offset, max_offset=max_offset)
hbeta_na = create_line(name="HBeta4863_na",pos=WB_HB, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_na, min_fwhm=min_fwhm_na, max_fwhm=max_fwhm_na, offset=offset, min_offset=min_offset_na, max_offset=max_offset_na)
OIIIb_na = create_line(name="OIIIb5007_na",pos=WB_O3B, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_na, min_fwhm=min_fwhm_na, max_fwhm=max_fwhm_na, offset=offset, min_offset=min_offset_na, max_offset=max_offset_na)
OIIIa_na = create_line(name="OIIIa4959_na",pos=WB_O3A, ampl=OIIIb_na.ampl/3.0, fwhm=OIIIb_na.fwhm, offset=OIIIb_na.offs_kms)
halpha_na = create_line(name="HAlpha6565_na",pos=WB_HA, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=fwhm_na, min_fwhm=min_fwhm_na, max_fwhm=max_fwhm_na, offset=offset, min_offset=min_offset_na, max_offset=max_offset_na)
# [NII] doublet, tied to the narrow width/velocity, ratio 6583/6548 = 3.
NII6583_na = create_line(name="NII6583_na",pos=WB_N2B, ampl=ampl, min_ampl=min_ampl, max_ampl=max_ampl, fwhm=OIIIb_na.fwhm, offset=OIIIb_na.offs_kms)
NII6548_na = create_line(name="NII6548_na",pos=WB_N2A, ampl=NII6583_na.ampl/3.0, fwhm=OIIIb_na.fwhm, offset=OIIIb_na.offs_kms)
# Link Balmer kinematics.  Broad Halpha/Hbeta share one profile; narrow
# Balmer shares the forbidden-line ([OIII]/[NII]) width and velocity, which is
# how the narrow lines are defined physically.
halpha_br.fwhm = hbeta_br.fwhm
halpha_br.offs_kms = hbeta_br.offs_kms
hbeta_na.fwhm = OIIIb_na.fwhm
hbeta_na.offs_kms = OIIIb_na.offs_kms
halpha_na.fwhm = OIIIb_na.fwhm
halpha_na.offs_kms = OIIIb_na.offs_kms
# The narrow-line region is Case B: link the narrow Balmer decrement.
halpha_na.ampl = hbeta_na.ampl * 2.86

# fe=create_feii_model(max_fwhm=6000)
# Forbidden [OIII]/[NII] lines are narrow: do not include the broad counterparts
# (with both free, the fit puts all [OIII] flux into the broad component).
model = cont + OIIIb_na + OIIIa_na + NII6583_na + NII6548_na + hbeta_br + halpha_br + hbeta_na + halpha_na + create_feii_model(fwhm=1000, min_fwhm=300, max_fwhm=6000, offset=0, min_offset=-800, max_offset=800)

# fits a spectrum with the above model, iterate 2 times
s.fit(model, ntrial=30)
print("fit ok")

# creates a file to save the fitting results of the original spectra
d={'wave':s.wave,'flux':s.flux,'error':s.err,'model':model(s.wave),'cont':cont(s.wave), 'OIIIb_na':OIIIb_na(s.wave), 'OIIIa_na':OIIIa_na(s.wave), 'NII6583_na':NII6583_na(s.wave), 'NII6548_na':NII6548_na(s.wave), 'hbeta_br':hbeta_br(s.wave), 'hbeta_na':hbeta_na(s.wave), 'halpha_br':halpha_br(s.wave), 'halpha_na':halpha_na(s.wave)}
# fit_host_sdss() subtracts the host from s.flux in place, so add it back for a
# model comparable with the observed (host-included) spectrum.
_host = getattr(s, 'host', None)
if _host is not None and np.asarray(_host).shape == np.asarray(s.wave).shape:
    d['host'] = np.asarray(_host)
    d['model_total'] = np.asarray(d['model']) + np.asarray(_host)

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

# Plot the best-fit model *before* the Monte-Carlo block.  The pipeline runs
# fantasy under FANTASY_TIMEOUT and keeps the run once my_sdss_model.csv exists,
# so a slow Monte-Carlo (nsample refits of the whole model) could otherwise be
# killed before the process reaches the plotting code below.  monte_carlo() only
# writes a params CSV, so plotting the single best-fit model first loses nothing.
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
    plt.plot(df.wave, df.OIIIa_na * fluxnorm, '--', color='g', label='OIIIa 4959 NA', lw=1)
    plt.plot(df.wave, df.OIIIb_na * fluxnorm, '--', color='r', label='OIIIb 5007 NA', lw=1) 
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

# Monte-Carlo uncertainties (optional; FANTASY_MC=0 skips it for fast sweeps).
# Kept last so a slow or hung Monte-Carlo can never suppress the fit products or
# the PDF plot written above.
if os.environ.get("FANTASY_MC", "1") != "0":
    s.monte_carlo(nsample=int(os.environ.get("FANTASY_MC_N", "50")))
    # monte_carlo() writes the sample table to the cwd, which is not the mounted
    # output dir -> copy it so the errors survive.
    import shutil as _shutil
    for _f in (s.name + "_pars.csv", s.name + "_mc_pars.csv"):
        if os.path.exists(_f):
            _shutil.copy(_f, "./output/")
    print("mcmc ok")
else:
    print("skipping monte_carlo (FANTASY_MC=0)")