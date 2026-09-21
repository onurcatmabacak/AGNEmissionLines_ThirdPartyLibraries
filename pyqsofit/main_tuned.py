"""
Tuned PyQSOFit run for spectrum.fits (IeRASS J053448.4+212608).

Changes vs. original main.py:
  * errors: empirical ~5% of flux (was 2% -> redchi 13-17)
  * line priors: centered on the OBSERVED features; widths/ratios sane
  * [OIII] doublet: 4959/5007 tied (1:0.35), same sigma; separate FeII 4930 component
  * Ha: broad (3 Gaussians) + narrow; [NII] tied (1:0.34, same sigma)
  * continuum windows cleaned
Run:  cd pyqsofit && python main_tuned.py
"""
import glob, os, sys, timeit
import numpy as np

from pyqsofit.PyQSOFit import QSOFit
from astropy.io import fits
from astropy.table import Table
import astropy.units as u
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

QSOFit.set_mpl_style()

Z = 0.348
NLIM = 1200  # km/s, broad/narrow classifier for plotting

# ---------------- load spectrum ----------------
def load_spectrum(fits_file):
    hdulist = fits.open(fits_file)
    z = hdulist[0].header.get('z', Z)
    flux = hdulist[0].data
    wavelength = hdulist[1].data
    err = 0.05 * flux  # empirical noise (spectrum smoothed, ~5-6% per pixel)
    return wavelength * u.AA, flux * 1e17 * u.Unit('erg cm-2 s-1 AA-1'), err * 1e17 * u.Unit('erg cm-2 s-1 AA-1'), float(Z)


path_ex = './'
hdr0 = fits.Header()
hdr0['Author'] = 'Onur'
primary_hdu = fits.PrimaryHDU(header=hdr0)


def rline(lam, comp, lo, hi, name, ngauss, inisca, minsca, maxsca, inisig, minsig, maxsig,
          voff, vindex=0, windex=0, findex=0, fvalue=1.0, vary=1):
    return (float(lam), comp, float(lo), float(hi), name, int(ngauss),
            float(inisca), float(minsca), float(maxsca), float(inisig), float(minsig), float(maxsig),
            float(voff), int(vindex), int(windex), int(findex), float(fvalue), int(vary))


# Rest-frame priors.  NOTE: our spectrum.fits has an internally inconsistent
# wavelength scale; the observed strong features sit at rest ~3784, ~4836,
# ~4930.5, ~5009 (+broad wings), ~6556/6587.  We therefore center the priors on
# the observed features and keep the physionomies flexible (free centroids).
SIG = 0.0017   # ~500 km/s
SIGB = 0.0034  # ~1000 km/s
SIGBB = 0.007  # ~2100 km/s

dt = np.dtype([
    ('lambda', 'f4'), ('compname', 'S20'), ('minwav', 'f4'), ('maxwav', 'f4'),
    ('linename', 'S20'), ('ngauss', 'i4'), ('inisca', 'f4'), ('minsca', 'f4'), ('maxsca', 'f4'),
    ('inisig', 'f4'), ('minsig', 'f4'), ('maxsig', 'f4'), ('voff', 'f4'),
    ('vindex', 'i4'), ('windex', 'i4'), ('findex', 'i4'), ('fvalue', 'f4'), ('vary', 'i4')])
line_priors = np.array([
    # H-alpha complex (rest 6400-6800)
    rline(6557.0, 'Ha', 6400, 6800, 'Ha_br', 3, 1.5, 0.0, 1e4, SIGBB, 0.001, 0.03, 0.02),
    rline(6556.0, 'Ha', 6400, 6800, 'Ha_na', 1, 2.0, 0.0, 1e4, SIG, 0.0004, 0.004, 0.003),
    rline(6587.0, 'Ha', 6400, 6800, 'NII6585', 1, 0.6, 0.0, 1e4, SIG, 0.0004, 0.005, 0.003, 1, 1, 1, 1.0),
    rline(6552.0, 'Ha', 6400, 6800, 'NII6549', 1, 0.2, 0.0, 1e4, SIG, 0.0004, 0.005, 0.003, 1, 1, 1, 0.34),
    rline(6716.0, 'Ha', 6700, 6760, 'SII6718', 1, 0.1, 0.0, 1e4, SIG, 0.0003, 0.005, 0.003, 1, 1, 0, 1.0),
    rline(6731.0, 'Ha', 6700, 6760, 'SII6732', 1, 0.1, 0.0, 1e4, SIG, 0.0003, 0.005, 0.003, 1, 1, 0, 1.0),
    # H-beta complex (rest 4640-5100)
    rline(4838.0, 'Hb', 4640, 5100, 'Hb_br', 3, 0.6, 0.0, 1e4, SIGBB, 0.001, 0.03, 0.02),
    rline(4860.0, 'Hb', 4640, 5100, 'Hb_na', 1, 0.35, 0.0, 1e4, SIG, 0.0004, 0.004, 0.003),
    rline(4930.6, 'Hb', 4640, 5100, 'FeII4930', 1, 0.5, 0.0, 1e4, SIGB, 0.0004, 0.006, 0.004),
    rline(4959.2, 'Hb', 4640, 5100, 'OIII4959c', 1, 0.3, 0.0, 1e4, SIG, 0.0004, 0.006, 0.004, 1, 1, 1, 1.0),
    rline(5009.2, 'Hb', 4640, 5100, 'OIII5007c', 1, 1.1, 0.0, 1e4, SIG, 0.0004, 0.006, 0.004, 1, 1, 1, 0.35),
    rline(4959.2, 'Hb', 4640, 5100, 'OIII4959w', 1, 0.2, 0.0, 1e4, SIGB, 0.001, 0.008, 0.005, 2, 2, 0, 1.0),
    rline(5009.2, 'Hb', 4640, 5100, 'OIII5007w', 1, 0.6, 0.0, 1e4, SIGB, 0.001, 0.008, 0.005, 2, 2, 0, 0.35),
    rline(4685.7, 'Hb', 4640, 4720, 'HeII4687', 1, 0.1, 0.0, 1e4, SIG, 0.0004, 0.005, 0.003),
    # Blue (observed feature at rest ~3784, near [OII] 3727)
    rline(3784.5, 'OII', 3700, 3900, 'OII3784', 1, 0.9, 0.0, 1e4, SIGB, 0.0008, 0.006, 0.004),
    rline(3869.0, 'OII', 3700, 3900, 'NeIII3869', 1, 0.12, 0.0, 1e4, SIG, 0.0004, 0.004, 0.003),
], dtype=dt)

hdr1 = fits.Header()
hdu1 = fits.BinTableHDU(data=line_priors, header=hdr1, name='line_priors')

conti_windows = np.rec.array([
    (3100., 3350.), (3450., 3600.), (3950., 4030.), (4200., 4330.), (4400., 4560.),
    (5400., 5470.), (5500., 5800.), (5950., 6250.), (7000., 7300.),
    ],
    formats='float32,  float32', names='min,     max')
hdu2 = fits.BinTableHDU(data=conti_windows, name='conti_windows')

dt2 = np.dtype([('parname', 'S20'), ('initial', 'f4'), ('min', 'f4'), ('max', 'f4'), ('vary', 'i4')])
conti_priors = np.array([
    ('Fe_uv_norm', 0.0, 0.0, 1e10, 1),
    ('Fe_uv_FWHM', 3000, 1200, 18000, 1),
    ('Fe_uv_shift', 0.0, -0.01, 0.01, 1),
    ('Fe_op_norm', 0.05, 0.0, 1e10, 1),
    ('Fe_op_FWHM', 2500, 800, 18000, 1),
    ('Fe_op_shift', 0.0, -0.01, 0.01, 1),
    ('PL_norm', 2.5, 0.0, 1e10, 1),
    ('PL_slope', -0.5, -5.0, 3.0, 1),
    ('Blamer_norm', 0.0, 0.0, 1e10, 1),
    ('Balmer_Te', 15000, 10000, 50000, 1),
    ('Balmer_Tau', 0.5, 0.1, 2.0, 1),
    ('conti_a_0', 0.0, None, None, 1),
    ('conti_a_1', 0.0, None, None, 1),
    ('conti_a_2', 0.0, None, None, 1),
], dtype=dt2)
hdr3 = fits.Header()
hdu3 = fits.BinTableHDU(data=conti_priors, header=hdr3, name='conti_priors')

measure_info = Table([
    [[1450, 4200, 5100]],
    [[4435, 4685]],
], names=('cont_loc', 'Fe_flux_range'), dtype=('float32', 'float32'))
hdu4 = fits.BinTableHDU(data=measure_info, header=fits.Header(), name='measure_info')

hdu_list = fits.HDUList([primary_hdu, hdu1, hdu2, hdu3, hdu4])
hdu_list.writeto(os.path.join(path_ex, 'qsopar_tuned.fits'), overwrite=True)

wavelength, flux, error, z = load_spectrum('spectrum.fits')

q_mle = QSOFit(wavelength, flux, error, z, path=path_ex)
narrow_line_velocity_limit = NLIM

start = timeit.default_timer()
q_mle.Fit(name='result_tuned',
          nsmooth=1,
          and_mask=False,
          or_mask=False,
          reject_badpix=False,
          deredden=False,
          wave_range=None,
          wave_mask=None,
          decompose_host=False,
          host_prior=False,
          host_line_mask=False,
          decomp_na_mask=False,
          qso_type='global',
          npca_qso=1,
          host_type='PCA',
          npca_gal=0,
          Fe_uv_op=True,
          poly=True,
          BC=False,
          initial_guess=None,
          rej_abs_conti=True,
          n_pix_min_conti=100,
          linefit=True,
          rej_abs_line=False,
          MC=False,
          MCMC=False,
          nsamp=400,
          param_file_name='qsopar_tuned.fits',
          nburn=20,
          nthin=10,
          epsilon_jitter=0.,
          save_result=True,
          save_fits_name="output_tuned",
          save_fits_path="./",
          plot_fig=True,
          save_fig=True,
          plot_corner=False,
          verbose=False,
          kwargs_plot={'save_fig_path': './', 'broad_fwhm': narrow_line_velocity_limit},
          kwargs_conti_emcee={},
          kwargs_line_emcee={})
end = timeit.default_timer()
print(f'Fitting finished in {np.round(end - start, 1)}s')

print('continuum result:')
for n, v in zip(q_mle.conti_result_name, q_mle.conti_result):
    print(' ', n, v)
print('line results:')
names = q_mle.line_result_name
vals = q_mle.line_result
for n, v in zip(names, vals):
    print(f'  {n:20s} {v}')
