"""Tuned region fits with physically-motivated constraints (ratios, ties)."""
import numpy as np
from astropy.io import fits
from lmfit import Parameters, minimize
from scipy.ndimage import gaussian_filter1d

C_KMS = 2.99792458e5
Z0 = 0.34790
FITS_OBJ = fits.open('spectrum.fits')
FLUX = FITS_OBJ[0].data / 1e-17
WAVE = FITS_OBJ[1].data
ERR = 0.048 * FLUX + 0.02

_fe = np.genfromtxt('/tmp/pyqsofit_repo/src/pyqsofit/fe_optical.txt')
FE_LOGL = _fe[:, 0]
FE_FLUX = _fe[:, 1]


def fe_smoothed(sig_kms):
    sig_log = sig_kms / (C_KMS * np.log(10.0))
    return gaussian_filter1d(FE_FLUX, sig_log)


def gauss(x, amp, mu, sig):
    return amp * np.exp(-0.5 * ((x - mu) / sig) ** 2)


def fit_region(lo, hi, model, params, label):
    m = (WAVE >= lo) & (WAVE <= hi)

    def res(p):
        return (FLUX[m] - model(p, WAVE[m])) / ERR[m]

    out = minimize(res, params, max_nfev=80000)
    print(f'=== {label} [{lo}-{hi}]: {out.message}; redchi={out.redchi:.3f}')
    return out


# ---------------- Ha region: Ha na+br, [NII] (fixed 1:3), [SII] (free ratio) ----
def ha_model(p, x):
    z = Z0 + p['dz'].value
    m = p['c0'].value + p['c1'].value * (x - 8840)
    sig_na = p['sig_na'].value / C_KMS
    # narrow lines share z and sigma
    for nm, lam, amp in [('Ha', 6562.8, p['Ha_amp'].value),
                         ('NIIa', 6548.0, p['NIIb_amp'].value / 3.0),
                         ('NIIb', 6583.4, p['NIIb_amp'].value),
                         ('SIIa', 6716.4, p['SIIa_amp'].value),
                         ('SIIb', 6730.8, p['SIIb_amp'].value)]:
        m = m + gauss(x, amp, lam * (1 + z), sig_na * lam * (1 + z))
    # broad Ha: two comps, common voff
    for k, vmax in (('1', 1), ('2', 2)):
        a = p[f'Ha_br{k}_a'].value
        if a > 0:
            s = p[f'Ha_br{k}_s'].value
            v = p['Ha_br_vo'].value * vmax
            m = m + gauss(x, a, 6562.8 * (1 + z) * (1 + v / C_KMS), s * 6562.8 * (1 + z) / C_KMS)
    return m


def make_ha_params():
    p = Parameters()
    p.add('dz', 0.0, min=-0.0008, max=0.0008)
    p.add('c0', 2.4, min=1.2, max=4.0)
    p.add('c1', 0.0, min=-2e-3, max=2e-3)
    p.add('sig_na', 350.0, min=80, max=1200)
    for nm, init in [('Ha', 2.5), ('NIIb', 0.7), ('SIIa', 0.12), ('SIIb', 0.08)]:
        p.add(f'{nm}_amp', init, min=0, max=30)
    p.add('Ha_br1_a', 1.2, min=0, max=30)
    p.add('Ha_br1_s', 1500.0, min=300, max=7000)
    p.add('Ha_br2_a', 0.8, min=0, max=30)
    p.add('Ha_br2_s', 4000.0, min=1000, max=15000)
    p.add('Ha_br_vo', 0.0, min=-800, max=800)
    return p


# ---------------- Hb region: Hb na+br, [OIII] na (1:3) + wing, HeII, FeII ----
def hb_model(p, x):
    z = Z0 + p['dz'].value
    m = p['c0'].value + p['c1'].value * (x - 6620)
    fe = p['fe_norm'].value
    if fe > 0:
        lamf = 10 ** (FE_LOGL + np.log10(1 + z)) * (1 + p['fe_vo'].value / C_KMS)
        m = m + fe * np.interp(x, lamf, fe_smoothed(p['fe_sig'].value))
    sig_na = p['sig_na'].value / C_KMS
    for nm, lam, amp in [('Hb', 4861.4, p['Hb_amp'].value),
                         ('HeII', 4685.7, p['HeII_amp'].value),
                         ('OIIIa', 4958.9, p['OIIIb_amp'].value / 3.0),
                         ('OIIIb', 5006.8, p['OIIIb_amp'].value)]:
        m = m + gauss(x, amp, lam * (1 + z), sig_na * lam * (1 + z))
    # [OIII] wings (blue-shift allowed), each own width but same voff
    for nm, lam in [('OIIIa', 4958.9), ('OIIIb', 5006.8)]:
        a = p['OIII_w_amp'].value / 3.0 * (1 if nm == 'OIIIb' else 1)
        if p['OIII_w_amp'].value > 0:
            m = m + gauss(x, a, lam * (1 + z) * (1 + p['OIII_w_vo'].value / C_KMS),
                          p['OIII_w_s'].value * lam * (1 + z) / C_KMS)
    # broad Hb: two comps, common voff
    for k, vmax in (('1', 1), ('2', 2)):
        a = p[f'Hb_br{k}_a'].value
        if a > 0:
            s = p[f'Hb_br{k}_s'].value
            v = p['Hb_br_vo'].value * vmax
            m = m + gauss(x, a, 4861.4 * (1 + z) * (1 + v / C_KMS), s * 4861.4 * (1 + z) / C_KMS)
    return m


def make_hb_params():
    p = Parameters()
    p.add('dz', 0.0, min=-0.0008, max=0.0008)
    p.add('c0', 2.42, min=1.2, max=4.0)
    p.add('c1', 0.0, min=-2e-3, max=2e-3)
    p.add('fe_norm', 0.05, min=0, max=10)
    p.add('fe_sig', 400.0, min=50, max=4000)
    p.add('fe_vo', 0.0, min=-1500, max=1500)
    p.add('sig_na', 350.0, min=80, max=1200)
    for nm, init in [('Hb', 0.25), ('HeII', 0.0), ('OIIIb', 1.0)]:
        p.add(f'{nm}_amp', init, min=0, max=30)
    p.add('OIII_w_amp', 0.4, min=0, max=30)
    p.add('OIII_w_vo', 0.0, min=-2000, max=500)
    p.add('OIII_w_s', 1200.0, min=300, max=7000)
    p.add('Hb_br1_a', 0.5, min=0, max=30)
    p.add('Hb_br1_s', 1500.0, min=300, max=7000)
    p.add('Hb_br2_a', 0.3, min=0, max=30)
    p.add('Hb_br2_s', 4000.0, min=1000, max=15000)
    p.add('Hb_br_vo', 0.0, min=-800, max=800)
    return p


if __name__ == '__main__':
    out = fit_region(8600, 9100, ha_model, make_ha_params(), 'Ha')
    for nm in ['Ha', 'NIIb', 'SIIa', 'SIIb']:
        print(f'  {nm}: amp={out.params[f"{nm}_amp"].value:.3f}')
    print('  sig_na %.1f km/s (FWHM %.1f)' % (out.params['sig_na'].value, 2.3548 * out.params['sig_na'].value))
    for k in ('1', '2'):
        print(f'  Ha br{k}: a={out.params[f"Ha_br{k}_a"].value:.3f} FWHM={2.3548*out.params[f"Ha_br{k}_s"].value:.1f}')
    print('  br voff', out.params['Ha_br_vo'].value, 'dz', out.params['dz'].value)

    out = fit_region(6300, 7000, hb_model, make_hb_params(), 'Hb')
    for nm in ['Hb', 'HeII', 'OIIIb']:
        print(f'  {nm}: amp={out.params[f"{nm}_amp"].value:.3f}')
    print('  sig_na %.1f km/s (FWHM %.1f)' % (out.params['sig_na'].value, 2.3548 * out.params['sig_na'].value))
    print(f'  OIII wing: a={out.params["OIII_w_amp"].value:.3f} voff={out.params["OIII_w_vo"].value:.1f} FWHM={2.3548*out.params["OIII_w_s"].value:.1f}')
    for k in ('1', '2'):
        print(f'  Hb br{k}: a={out.params[f"Hb_br{k}_a"].value:.3f} FWHM={2.3548*out.params[f"Hb_br{k}_s"].value:.1f}')
    print('  Hb br voff', out.params['Hb_br_vo'].value, 'fe', out.params['fe_norm'].value, out.params['fe_sig'].value, 'dz', out.params['dz'].value)
