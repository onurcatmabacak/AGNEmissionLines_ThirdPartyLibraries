"""Blue-region fit (rest 2967-4200): [NeV]3350, [NeV]3426, [OII]3727, [NeIII]3869.
Determines narrow-line sigma (km/s) with a spline continuum."""
import numpy as np
from astropy.io import fits
from lmfit import Parameters, minimize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

C_KMS = 2.99792458e5
Z0 = 0.34793
FLUX = fits.open('spectrum.fits')[0].data / 1e-17
WAVE = fits.open('spectrum.fits')[1].data
ERR = 0.048 * FLUX + 0.02

KNOTS = np.array([4120, 4330, 4560, 4790, 4900, 5120, 5300, 5480, 5662])
KNOTVALS = np.array([np.median(FLUX[(WAVE > k - 35) & (WAVE < k + 35)]) for k in KNOTS])
LINES = [('NeV3346', 3346.8), ('NeV3426', 3426.8), ('OII3727', 3727.1), ('NeIII3869', 3868.8)]


def model(p, x):
    z = Z0 + p['dz'].value
    m = np.interp(x, KNOTS, [p[f'y{i}'].value for i in range(len(KNOTS))])
    sig = p['sig'].value / C_KMS
    for nm, lam in LINES:
        m = m + p[f'{nm}_amp'].value * np.exp(-0.5 * ((x - lam * (1 + z)) / (sig * lam * (1 + z))) ** 2)
    return m


def make_params():
    p = Parameters()
    p.add('dz', 0.0, min=-0.0012, max=0.0012)
    p.add('sig', 300.0, min=30, max=2500)
    for i, k in enumerate(KNOTS):
        p.add(f'y{i}', value=KNOTVALS[i], min=1.0, max=5.0)
    for nm, init in [('NeV3346', 0.03), ('NeV3426', 0.05), ('OII3727', 0.7), ('NeIII3869', 0.12)]:
        p.add(f'{nm}_amp', init, min=0, max=10)
    return p


def run():
    m = (WAVE >= 4060) & (WAVE <= 5660)

    def res(p_):
        return (FLUX[m] - model(p_, WAVE[m])) / ERR[m]

    out = minimize(res, make_params(), max_nfev=50000)
    print(out.message, 'redchi', out.redchi)
    print('dz', out.params['dz'].value, 'sig', out.params['sig'].value, 'FWHM km/s', 2.3548 * out.params['sig'].value)
    for nm, lam in LINES:
        print(nm, 'amp', round(out.params[f'{nm}_amp'].value, 3))
    fig, axes = plt.subplots(2, 1, figsize=(16, 6), sharex=True)
    axes[0].plot(WAVE[m], FLUX[m], 'k-', lw=0.9)
    axes[0].plot(WAVE[m], model(out.params, WAVE[m]), 'r-', lw=0.9)
    axes[1].plot(WAVE[m], (FLUX[m] - model(out.params, WAVE[m])) / ERR[m], 'b-', lw=0.7)
    axes[1].axhline(0, color='k', lw=0.5)
    plt.tight_layout()
    plt.savefig('/tmp/plots/blue_fit.png', dpi=110)
    return out


if __name__ == '__main__':
    run()
