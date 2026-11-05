"""Empirical error estimation + region diagnostics for spectrum.fits."""
import numpy as np
from astropy.io import fits
from scipy.ndimage import gaussian_filter1d

FITS_OBJ = fits.open('spectrum.fits')
FLUX = FITS_OBJ[0].data / 1e-17
WAVE = FITS_OBJ[1].data


def get_noise():
    """Per-pixel noise from high-frequency residuals, smoothed over 201 px."""
    # high-pass with Gaussian sigma=6 px (smoothing structure is ~3 px)
    smooth = gaussian_filter1d(FLUX, 6.0)
    hp = FLUX - smooth
    # local rms
    sq = gaussian_filter1d(hp ** 2, 61.0)
    noise = np.sqrt(np.maximum(sq, 1e-20))
    return noise


if __name__ == '__main__':
    noise = get_noise()
    print('noise range:', noise.min(), noise.max())
    # print rel noise every 500 A
    for lo in range(4000, 9500, 500):
        m = (WAVE >= lo) & (WAVE < lo + 500)
        print(f'{lo}-{lo+500}: mean flux {FLUX[m].mean():.3f}  noise {noise[m].mean():.3f}  rel {noise[m].mean()/FLUX[m].mean():.3f}')
