import numpy as np
import matplotlib
matplotlib.rcParams['text.usetex'] = False
from astropy import units as u
from astropy.cosmology import FlatLambdaCDM

def CATALOG_settings():
    cat = dict()
    cat['path'] = '/app/AGNfitter/'
    cat['filename'] = '/app/output/catalog.txt'
    cat['filetype'] = 'ASCII'
    cat['name'] = 0
    cat['redshift'] = 1
    cat['freq/wl_list'] = []
    cat['use_central_wavelength'] = True
    cat['freq/wl_format'] = 'wavelength'
    cat['freq/wl_unit'] = u.micron
    cat['flux_in_magAB'] = False
    cat['flux_unit'] = u.mJy
    cat['flux_list'] = list(range(2, 10))
    cat['fluxerr_list'] = list(range(10, 18))
    cat['err+10%flux_moreflex'] = False
    cat['ndflag_bool'] = False
    cat['ndflag_list'] = 'list'
    cat['workingpath'] = '/app/output/'
    cat['output_folder'] = '/app/output/OUTPUT/'
    return cat

def FILTERS_settings():
    filters = dict()
    filters['dict_zarray'] = np.array([])
    filters['path'] = 'models/FILTERS/'
    filters['filterset'] = 'zgt05_8band'
    for i, name in enumerate(['g', 'r', 'i', 'z', 'WISE1', 'WISE2', 'WISE3', 'WISE4']):
        filters[name] = [True, 2 + i]
    filters['add_filters'] = False
    filters['add_filters_dict'] = {'names': [], 'filenames': [], 'freq/wl_format': [], 'freq/wl_unit': [], 'description': []}
    return filters

def MODELS_settings():
    models = dict()
    models['path'] = 'models/'
    models['modelset'] = 'modelsv1'
    models['GALAXY'] = 'BC03_metal'
    models['STARBURST'] = 'S17'
    models['BBB'] = 'THB21'
    models['TORUS'] = 'SKIRTOR_1P'
    models['XRAYS'] = False
    models['RADIO'] = False
    models['Blazar'] = 'None'
    models['PRIOR_energy_balance'] = 'Flexible'
    models['PRIOR_AGNfraction'] = True
    models['PRIOR_midIR_UV'] = False
    models['PRIOR_galaxy_only'] = False
    models['turn_on_AGN'] = True
    return models

def MCMC_settings():
    mc = dict()
    mc['sampling_algorithm'] = 'ultranest'
    mc['Nwalkers'] = 100
    mc['Nburnsets'] = 2
    mc['Nburn'] = 100
    mc['Nmcmc'] = 200
    mc['iprint'] = 50
    mc['live_points'] = 80
    mc['min_ess'] = 80
    mc['num_loops'] = 0
    mc['direction_generation'] = 'de-mix'
    return mc

def OUTPUT_settings():
    out = dict()
    out['plot_format'] = 'pdf'
    out['band_indicators'] = True
    out['realizations_format'] = 'shaded'
    out['plot_tracesburn-in'] = False
    out['plot_tracesmcmc'] = False
    out['Nsample'] = 100
    out['Nthinning'] = 10
    out['writepar_meanwitherrors'] = True
    out['plot_posteriortriangle'] = False
    out['calc_intlum'] = True
    out['save_posterior_luminosities'] = False
    out['save_posteriors'] = True
    out['realizations2int'] = 20
    out['plot_posteriortrianglewithluminosities'] = False
    out['intlum_models'] = ['sb','bbb','bbbdered','gal','AGNfrac_opt','tor','tor+bbb','AGNfrac_IR']
    out['intlum_freqranges_unit'] = u.micron
    out['intlum_freqranges'] = np.array([[8.,1000.],[0.1,1.],[0.1,1.],[0.1,1.],[0.1,1.],[1.,30.],[0.1,30.],[8.,1000.]])
    out['intlum_names'] = ['LIR(8-1000)','Lbb(0.1-1)','Lbbdered(0.1-1)','Lga(01-1)','AGNfrac(0.1-1)','Ltor(1-30)','LAGN(0.1-30)','AGNfrac(8-1000)']
    out['realizations2plot'] = 10
    out['plot_best_fit'] = True
    out['plot_median_fit'] = False
    out['plot_residuals'] = True
    out['saveSEDresiduals'] = True
    out['plotSEDrealizations'] = True
    out['saveSEDrealizations'] = True
    return out
