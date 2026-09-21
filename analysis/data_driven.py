"""Data-driven reference fit of the strong emission features.

Treats line centroids as FREE parameters (because the wavelength scale of
spectrum.fits is internally inconsistent with a single redshift; see
DIAGNOSTICS.md).  The numbers here are what any fitting tool should recover
if its line windows are centered on the observed features.
"""
import numpy as np
from astropy.io import fits
from lmfit import Parameters, minimize
from scipy.ndimage import gaussian_filter1d
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

C = 2.99792458e5
FLUX = fits.open('spectrum.fits')[0].data / 1e-17
WAVE = fits.open('spectrum.fits')[1].data
ERR = 0.048 * FLUX + 0.02

FE = np.genfromtxt('/tmp/pyqsofit_repo/src/pyqsofit/fe_optical.txt')
FE_LOGL = FE[:, 0]
FE_FLUX = FE[:, 1]


def fe_smoothed(sig_kms):
    return gaussian_filter1d(FE_FLUX, sig_kms / (C * np.log(10.0)))


def fit_gauss(lo, hi, ncomp, a0, mu0, s0, c0=2.4):
    """Fit a region with ncomp Gaussians + linear continuum."""
    m = (WAVE >= lo) & (WAVE <= hi)
    p = Parameters()
    p.add('c0', c0, min=0.5, max=6.0)
    p.add('c1', 0.0, min=-2e-3, max=2e-3)
    for k in range(ncomp):
        p.add(f'a{k}', a0[k], min=0, max=50)
        p.add(f'mu{k}', mu0[k], min=mu0[k] - 20, max=mu0[k] + 20)
        p.add(f's{k}', s0[k], min=1.5, max=25)

    def model(p_, x):
        out = p_['c0'].value + p_['c1'].value * (x - 7300)
        for k in range(ncomp):
            out = out + p_[f'a{k}'].value * np.exp(-0.5 * ((x - p_[f'mu{k}'].value) / p_[f's{k}'].value) ** 2)
        return out

    def res(p_):
        return (FLUX[m] - model(p_, WAVE[m])) / ERR[m]

    out = minimize(res, p, max_nfev=60000)
    print(f'--- {lo}-{hi}: redchi={out.redchi:.2f}')
    for k in range(ncomp):
        a = out.params[f'a{k}'].value
        mu = out.params[f'mu{k}'].value
        s = out.params[f's{k}'].value
        print(f'   comp{k}: a={a:6.3f}  mu={mu:8.2f} A  sigma={s:5.2f} A  FWHM_obj={2.3548*s:5.1f} A  FWHM_kms={2.3548*s/mu*C:6.0f}')
    print(f'   cont: c0={out.params["c0"].value:.3f} c1={out.params["c1"].value:.6f}')
    return out, model


if __name__ == '__main__':
    # Blue [OII]-like line region
    fit_gauss(4970, 5250, 2, [1.0, 0.15], [5102, 5227], [6, 6])
    # Hb-complex region: 3 lines + continuum
    fit_gauss(6430, 6900, 3, [0.5, 0.8, 1.4], [6522, 6648, 6752], [9, 5, 7])
    # Ha region: 2 comps (narrow Ha + broad) + NII blend modeled via 2 comps
    fit_gauss(8700, 8980, 3, [4.0, 1.2, 0.4], [8847, 8840, 8880], [12, 55, 8])
