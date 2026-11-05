"""Reference global fit of spectrum.fits (IeRASS J053448.4+212608, z~0.348).

Model (rest-frame param, observed-frame eval):
  - continuum: Legendre poly (fit to line-free windows, fixed)
  - optical FeII (Vestergaard & Wilkes template), log-lambda Gaussian broadened
  - narrow lines (common z, per-line sigma in km/s)
  - broad Halpha/Hbeta (two Gaussian comps each)
"""
import numpy as np
from astropy.io import fits
from lmfit import Parameters, minimize
from numpy.polynomial.legendre import legval

C_KMS = 2.99792458e5
Z0 = 0.34793

FITS_OBJ = fits.open('spectrum.fits')
FLUX = FITS_OBJ[0].data / 1e-17
WAVE = FITS_OBJ[1].data

# Rest-frame continuum windows (line-free)
WINS = [(3020, 3400), (3950, 4030), (5450, 5490), (5500, 5800),
        (5950, 6250), (7000, 7300)]

LINES = {
    'OII_3727':  (3727.1,), 'NeIII_3869': (3868.8,),
    'Hg_4340':   (4340.5,), 'OIII_4363': (4363.2,),
    'HeII_4686': (4685.7,), 'Hb_4861':   (4861.4,),
    'OIII_4959': (4958.9,), 'OIII_5007': (5006.8,),
    'HeI_5876':  (5875.6,), 'OI_6300':   (6300.3,),
    'Ha_6563':   (6562.8,), 'NII_6548':  (6548.0,),
    'NII_6583':  (6583.4,), 'SII_6716':  (6716.4,),
    'SII_6731':  (6730.8,),
}


def gauss(x, amp, mu, sig):
    return amp * np.exp(-0.5 * ((x - mu) / sig) ** 2)


# ---- FeII template prep (log-lambda uniform grid) ----
from scipy.ndimage import gaussian_filter1d
_fe = np.genfromtxt('/tmp/pyqsofit_repo/src/pyqsofit/fe_optical.txt')
FE_LAML = _fe[:, 0]                    # log10 rest lambda
FE_FLUX = _fe[:, 1]
NULL = np.zeros_like(FE_LAML)


def fe_curve(sig_kms):
    """Return (loglam grid, smoothed template) units arbitrary."""
    if sig_kms < 1:
        return FE_LAML, FE_FLUX
    sig_log = sig_kms / (C_KMS * np.log(10.0))
    g = gaussian_filter1d(FE_FLUX, sig_log)
    return FE_LAML, g


def fit_continuum(z=Z0):
    from numpy.polynomial.legendre import legfit
    wr = WAVE / (1 + z)
    mask = np.zeros_like(WAVE, bool)
    for lo, hi in WINS:
        mask |= (wr >= lo) & (wr <= hi)
    t = (wr[mask] - 5500) / 1500
    return legfit(t, FLUX[mask], 5)


def build_residual(z_fixed=Z0):
    coef = fit_continuum(z_fixed)

    def residual(p):
        z = z_fixed + p['dz'].value
        wr = WAVE / (1 + z)
        m = legval((wr - 5500) / 1500, coef)
        # FeII
        fe_norm = p['fe_norm'].value
        if fe_norm > 0:
            lgrid, fe = fe_curve(np.abs(p['fe_sig'].value))
            lamf = 10 ** (lgrid + np.log10(1 + z)) * (1 + p['fe_vo'].value / C_KMS)
            m = m + fe_norm * np.interp(WAVE, lamf, fe)
        # narrow lines
        for name, (lam,) in LINES.items():
            amp = p[f'{name}_amp'].value
            if amp > 0:
                sig = p[f'{name}_sig'].value * lam / C_KMS * (1 + z)
                mu = lam * (1 + z)
                m = m + gauss(WAVE, amp, mu, sig)
        # broad
        for nm, lam in [('Hb', 4861.4), ('Ha', 6562.8)]:
            for k in ('1', '2'):
                a = p[f'{nm}_br{k}_a'].value
                if a > 0:
                    v = p[f'{nm}_br{k}_v'].value
                    s = p[f'{nm}_br{k}_s'].value
                    mu = lam * (1 + z) * (1 + v / C_KMS)
                    m = m + gauss(WAVE, a, mu, s * mu / C_KMS)
        return FLUX - m

    return residual


def make_params(coef):
    p = Parameters()
    p.add('dz', 0.0, min=-0.002, max=0.002)
    p.add('fe_norm', 0.15, min=0, max=20)
    p.add('fe_sig', 400.0, min=30, max=4000)
    p.add('fe_vo', 0.0, min=-2000, max=2000)
    for name in LINES:
        p.add(f'{name}_amp', 0.08, min=0, max=30)
        p.add(f'{name}_sig', 60.0, min=20, max=2500)
    for nm in ['Hb', 'Ha']:
        p.add(f'{nm}_br1_a', 0.4, min=0, max=30); p.add(f'{nm}_br1_v', 0.0, min=-3000, max=3000); p.add(f'{nm}_br1_s', 400.0, min=80, max=20000)
        p.add(f'{nm}_br2_a', 0.4, min=0, max=30); p.add(f'{nm}_br2_v', 0.0, min=-3000, max=3000); p.add(f'{nm}_br2_s', 1200.0, min=150, max=30000)
    return p


def run():
    coef = fit_continuum()
    p = make_params(coef)
    residual = build_residual()
    out = minimize(residual, p, max_nfev=40000)
    print(out.message)
    print('redchi naive:', out.redchi)
    for name, (lam,) in LINES.items():
        a = out.params[f'{name}_amp'].value
        s = out.params[f'{name}_sig'].value
        if a > 0.005:
            print(f'{name:14s} amp={a:7.3f}  sig={s:7.1f} km/s  FWHM={2.3548*s:7.1f} km/s')
        else:
            print(f'{name:14s} amp={a:7.3f}  (negligible)')
    for nm in ['Hb', 'Ha']:
        for k in ('1', '2'):
            a = out.params[f'{nm}_br{k}_a'].value
            print(f'{nm} br{k}: amp={a:7.3f}  voff={out.params[f"{nm}_br{k}_v"].value:8.1f} km/s  FWHM={2.3548*out.params[f"{nm}_br{k}_s"].value:8.1f} km/s')
    print('fe_norm', out.params['fe_norm'].value, ' fe_sig', out.params['fe_sig'].value, 'km/s; fe_vo', out.params['fe_vo'].value)
    print('z =', Z0 + out.params['dz'].value)
    return out


if __name__ == '__main__':
    run()
