# Line Fitting Models
from scipy.stats import skewnorm
import numpy as np


def gauss_model(xval, pp):
    """The single Gaussian model used to fit the emission lines 
    Parameter: the scale factor, central wavelength in logwave, line FWHM in logwave
    """
    term1 = np.exp(-(xval - pp[1])**2/(2.*pp[2]**2))
    yval = pp[0]*term1/(np.sqrt(2.*np.pi)*pp[2])
    return yval


def skewnorm_model(xval, pp):
    """The single skew normal model used to fit the emission lines 
    Parameter: the scale factor, central wavelength in logwave, line FWHM in logwave, skewness
    """
    yval = pp[0]*skewnorm.pdf(xval, pp[3], pp[1], pp[2])
    return yval

