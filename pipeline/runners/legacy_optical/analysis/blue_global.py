"""Rest-frame experiment: blue-to-mid region (rest 2967-5500) with FeII template.

Tests: which lines are real, what sigma, whether [OIII]4959/5007 ratio is
consistent with the doublet, and whether FeII explains the continuum bumps.
"""
import numpy as np
from astropy.io import fits
from lmfit import Parameters, minimize
from scipy.ndimage import gaussian_filter1d
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

C = 2.99792458e5
Z0 = 0.3486
FLUX = fits.open('spectrum.fits')[0].data / 1e-17
WAVE = fits.open('spectrum.fits')[1].data
WR = WAVE / (1 + Z0)
ERR = 0.048 * FLUX + 0.02

FE = np.genfromtxt('/tmp/pyqsofit_repo/src/pyqsofit/fe_optical.txt')
FE_LOGL = FE[:, 0]
FE_FLUX = FE[:, 1]


def fe_smoothed(sig_kms):
    return gaussian_filter1d(FE_FLUX, sig_kms / (C * np.log(10.0)))


# rest-frame spline knots (line-free)
KNOTS = np.array([3000, 3300, 3600, 3900, 4050, 4200, 4405, 4510, 4620, 5160, 5260, 5360, 5460])


def main():
    kvals = np.array([np.median(FLUX[(WR > k - 30) & (WR < k + 30)]) for k in KNOTS])
    p = Parameters()
    p.add('dz', 0.0, min=-0.0015, max=0.0015)
    p.add('fe_norm', 0.05, min=0, max=5)
    p.add('fe_sig', 400.0, min=50, max=3000)
    p.add('fe_vo', 0.0, min=-1500, max=1500)
    p.add('sig_na', 400.0, min=50, max=2500)
    p.add('sig_br', 2000.0, min=200, max=25000)
    for i, k in enumerate(KNOTS):
        p.add(f'y{i}', value=kvals[i], min=1.0, max=6.0)
    for nm, init in [('OII3727', 0.5), ('NeIII3869', 0.1), ('Hg4340', 0.05), ('OIII4363', 0.05),
                     ('HeII4686', 0.05), ('Hb4861', 0.3), ('OIII4959', 0.4), ('OIII5007', 1.2)]:
        p.add(f'{nm}_amp', init, min=0, max=30)
        p.add(f'{nm}_sig', 500.0, min=50, max=3000)
    p.add('Hb_br_a', 0.3, min=0, max=30)
    p.add('Hb_br_s', 2500.0, min=300, max=25000)
    p.add('Hb_br_v', 0.0, min=-2000, max=2000)

    lam_rest = {  # for constr: OIII4959 & 5007 free sigma, no ratio constraint (test)
        'OII3727': 3727.1, 'NeIII3869': 3868.8, 'Hg4340': 4340.5, 'OIII4363': 4363.2,
        'HeII4686': 4685.7, 'Hb4861': 4861.4, 'OIII4959': 4958.9, 'OIII5007': 5006.8}

    def model(p_, x):
        z = Z0 + p_['dz'].value
        m = np.interp(x / (1 + z), KNOTS, [p_[f'y{i}'].value for i in range(len(KNOTS))])
        # FeII
        if p_['fe_norm'].value > 0:
            lamf = 10 ** (FE_LOGL + np.log10(1 + z)) * (1 + p_['fe_vo'].value / C)
            m = m + p_['fe_norm'].value * np.interp(x, lamf, fe_smoothed(p_['fe_sig'].value))
        # narrows
        for nm, lam in lam_rest.items():
            sig = p_[f'{nm}_sig'].value * lam / C * (1 + z)
            m = m + p_[f'{nm}_amp'].value * np.exp(-0.5 * ((x - lam * (1 + z)) / sig) ** 2)
        # broad Hb
        if p_['Hb_br_a'].value > 0:
            sig = p_['Hb_br_s'].value * 4861.4 / C * (1 + z)
            mu = 4861.4 * (1 + z) * (1 + p_['Hb_br_v'].value / C)
            m = m + p_['Hb_br_a'].value * np.exp(-0.5 * ((x - mu) / sig) ** 2)
        return m

    msk = (WR >= 2967) & (WR <= 5500)

    def res(p_):
        return (FLUX[msk] - model(p_, WAVE[msk])) / ERR[msk]

    out = minimize(res, p, max_nfev=120000)
    print(out.message, 'redchi', out.redchi)
    for nm in lam_rest:
        a = out.params[f'{nm}_amp'].value
        s = out.params[f'{nm}_sig'].value
        print(f'{nm:10s} amp={a:7.3f}  sig={s:7.1f} km/s (FWHM {2.3548*s:7.1f})')
    print('Hb_br: a=%.3f s=%.1f v=%.1f' % (out.params['Hb_br_a'].value, out.params['Hb_br_s'].value, out.params['Hb_br_v'].value))
    print('fe_norm=%.3f fe_sig=%.1f fe_vo=%.1f' % (out.params['fe_norm'].value, out.params['fe_sig'].value, out.params['fe_vo'].value))
    print('dz', out.params['dz'].value, '-> z', Z0 + out.params['dz'].value)
    # save components for plotting
    fig, axes = plt.subplots(2, 1, figsize=(16, 7), sharex=True)
    xx = WAVE[msk]
    axes[0].plot(WR[msk], FLUX[msk], 'k-', lw=0.8)
    axes[0].plot(WR[msk], model(out.params, xx), 'r-', lw=0.9)
    axes[1].plot(WR[msk], (FLUX[msk] - model(out.params, xx)) / ERR[msk], 'b-', lw=0.6)
    axes[1].axhline(0, color='k', lw=0.5)
    plt.tight_layout()
    plt.savefig('/tmp/plots/blue_global.png', dpi=110)
    return out


if __name__ == '__main__':
    main()
