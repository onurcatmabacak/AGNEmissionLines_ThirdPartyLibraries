"""Region-level model fits with FeII, for diagnostics."""
import numpy as np
from astropy.io import fits
from lmfit import Parameters, minimize
from scipy.ndimage import gaussian_filter1d

C_KMS = 2.99792458e5
Z0 = 0.34793
FITS_OBJ = fits.open('spectrum.fits')
FLUX = FITS_OBJ[0].data / 1e-17
WAVE = FITS_OBJ[1].data
ERR = 0.045 * FLUX + 0.02

_fe = np.genfromtxt('/tmp/pyqsofit_repo/src/pyqsofit/fe_optical.txt')
FE_LOGL = _fe[:, 0]
FE_FLUX = _fe[:, 1]


def fe_smoothed(sig_kms):
    sig_log = sig_kms / (C_KMS * np.log(10.0))
    return gaussian_filter1d(FE_FLUX, sig_log)


def gauss(x, amp, mu, sig):
    return amp * np.exp(-0.5 * ((x - mu) / sig) ** 2)


def fit_region(lo, hi, spec):
    """spec: dict with model callable(p, x) and params."""
    m = (WAVE >= lo) & (WAVE <= hi)

    def res(p):
        return (FLUX[m] - spec['model'](p, WAVE[m])) / ERR[m]

    out = minimize(res, spec['params'], max_nfev=60000)
    print(f'=== region {lo}-{hi}: {out.message}; redchi={out.redchi:.3f}')
    return out


def ha_model(p, x):
    z = Z0 + p['dz'].value
    c = p['c0'].value + p['c1'].value * (x - 8800)
    m = c
    # narrow Ha + FeII (tiny) ; [NII] pair fixed ratio 3; SII excluded
    for nm, lam, key in [('Ha', 6562.8, 'Ha'), ('NII1', 6548.0, 'NII1'), ('NII2', 6583.4, 'NII2')]:
        amp = p[f'{nm}_amp'].value
        sig = p[f'{nm}_sig'].value * lam * (1 + z) / C_KMS
        m = m + gauss(x, amp, lam * (1 + z), sig)
    for nm, lam in [('Ha', 6562.8)]:
        for k in ('1', '2'):
            a = p[f'{nm}_br{k}_a'].value
            if a > 0:
                v = p[f'{nm}_br{k}_v'].value
                s = p[f'{nm}_br{k}_s'].value
                # components added in log-lambda for constant km/s width
                m = m + gauss(x, a, lam * (1 + z) * (1 + v / C_KMS), s * lam * (1 + z) / C_KMS)
    return m


def make_ha_params():
    p = Parameters()
    p.add('dz', 0.0, min=-0.002, max=0.002)
    p.add('c0', 2.45, min=1.0, max=4.0)
    p.add('c1', 0.0, min=-2e-3, max=2e-3)
    p.add('Ha_amp', 2.5, min=0, max=20)
    p.add('Ha_sig', 400.0, min=50, max=2500)
    p.add('NII1_amp', 0.3, min=0, max=20)
    p.add('NII2_amp', 0.9, min=0, max=20)
    for nm in ['NII1', 'NII2']:
        p.add(f'{nm}_sig', 400.0, min=50, max=2500)
    p.add('Ha_br1_a', 1.0, min=0, max=30)
    p.add('Ha_br1_v', 0.0, min=-2500, max=2500)
    p.add('Ha_br1_s', 1500.0, min=300, max=8000)
    p.add('Ha_br2_a', 1.0, min=0, max=30)
    p.add('Ha_br2_v', 0.0, min=-2500, max=2500)
    p.add('Ha_br2_s', 4000.0, min=800, max=15000)
    return p


def hb_model(p, x):
    z = Z0 + p['dz'].value
    c = p['c0'].value + p['c1'].value * (x - 6620)
    m = c
    fe = p['fe_norm'].value
    if fe > 0:
        lamf = 10 ** (FE_LOGL + np.log10(1 + z)) * (1 + p['fe_vo'].value / C_KMS)
        m = m + fe * np.interp(x, lamf, fe_smoothed(p['fe_sig'].value))
    for nm, lam, key in [('Hb', 4861.4, 'Hb'), ('OIII1', 4958.9, 'OIII1'), ('OIII2', 5006.8, 'OIII2')]:
        amp = p[f'{nm}_amp'].value
        sig = p[f'{nm}_sig'].value * lam * (1 + z) / C_KMS
        m = m + gauss(x, amp, lam * (1 + z), sig)
    for nm, lam in [('OIII1', 4958.9), ('OIII2', 5006.8)]:
        a = p[f'{nm}_w_a'].value
        if a > 0:
            v = p[f'{nm}_w_v'].value
            s = p[f'{nm}_w_s'].value
            m = m + gauss(x, a, lam * (1 + z) * (1 + v / C_KMS), s * lam * (1 + z) / C_KMS)
    for nm, lam in [('Hb', 4861.4)]:
        for k in ('1', '2'):
            a = p[f'{nm}_br{k}_a'].value
            if a > 0:
                v = p[f'{nm}_br{k}_v'].value
                s = p[f'{nm}_br{k}_s'].value
                m = m + gauss(x, a, lam * (1 + z) * (1 + v / C_KMS), s * lam * (1 + z) / C_KMS)
    return m


def make_hb_params():
    p = Parameters()
    p.add('dz', 0.0, min=-0.002, max=0.002)
    p.add('c0', 2.45, min=1.0, max=4.0)
    p.add('c1', 0.0, min=-2e-3, max=2e-3)
    p.add('fe_norm', 0.1, min=0, max=10)
    p.add('fe_sig', 400.0, min=50, max=4000)
    p.add('fe_vo', 0.0, min=-1500, max=1500)
    p.add('Hb_amp', 0.4, min=0, max=20)
    p.add('Hb_sig', 400.0, min=50, max=2500)
    p.add('OIII1_amp', 0.3, min=0, max=20)
    p.add('OIII2_amp', 1.0, min=0, max=20)
    for nm in ['OIII1', 'OIII2']:
        p.add(f'{nm}_sig', 500.0, min=50, max=2500)
        p.add(f'{nm}_w_a', 0.3, min=0, max=30)
        p.add(f'{nm}_w_v', 0.0, min=-2000, max=2000)
        p.add(f'{nm}_w_s', 1500.0, min=300, max=8000)
    p.add('Hb_br1_a', 0.4, min=0, max=30)
    p.add('Hb_br1_v', 0.0, min=-2500, max=2500)
    p.add('Hb_br1_s', 1500.0, min=300, max=8000)
    p.add('Hb_br2_a', 0.4, min=0, max=30)
    p.add('Hb_br2_v', 0.0, min=-2500, max=2500)
    p.add('Hb_br2_s', 4000.0, min=800, max=15000)
    return p


if __name__ == '__main__':
    import sys
    # Ha region
    out = fit_region(8600, 9050, {'model': ha_model, 'params': make_ha_params()})
    print('Ha narrow: amp %.3f sig %.1f km/s (FWHM %.1f)' % (out.params['Ha_amp'].value, out.params['Ha_sig'].value, 2.3548*out.params['Ha_sig'].value))
    for k in ('1', '2'):
        print(f'Ha br{k}: a={out.params["Ha_br1_a".replace("1",k)].value:.3f} v={out.params[f"Ha_br{k}_v"].value:.1f} FWHM={2.3548*out.params[f"Ha_br{k}_s"].value:.1f}')
    for nm in ['NII1', 'NII2']:
        print(f'{nm}: amp={out.params[f"{nm}_amp"].value:.3f} sig={out.params[f"{nm}_sig"].value:.1f}')
    print('dz', out.params['dz'].value)
    # Hb region
    out = fit_region(6300, 7000, {'model': hb_model, 'params': make_hb_params()})
    for nm in ['Hb', 'OIII1', 'OIII2']:
        print(f'{nm}: amp={out.params[f"{nm}_amp"].value:.3f} sig={out.params[f"{nm}_sig"].value:.1f} FWHM={2.3548*out.params[f"{nm}_sig"].value:.1f} ; wing a={out.params[f"{nm}_w_a"].value:.3f} v={out.params[f"{nm}_w_v"].value:.1f} FWHM={2.3548*out.params[f"{nm}_w_s"].value:.1f}')
    print('Hb br1: a=%.3f v=%.1f FWHM=%.1f' % (out.params['Hb_br1_a'].value, out.params['Hb_br1_v'].value, 2.3548*out.params['Hb_br1_s'].value))
    print('Hb br2: a=%.3f v=%.1f FWHM=%.1f' % (out.params['Hb_br2_a'].value, out.params['Hb_br2_v'].value, 2.3548*out.params['Hb_br2_s'].value))
    print('fe_norm %.4f fe_sig %.1f' % (out.params['fe_norm'].value, out.params['fe_sig'].value))
    print('dz', out.params['dz'].value)
