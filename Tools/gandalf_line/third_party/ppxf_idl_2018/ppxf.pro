;#############################################################################
;
; Copyright (C) 2001-2018, Michele Cappellari
; E-mail: cappellari_at_astro.ox.ac.uk
;
; Updated versions of the software are available from my web page
; http://purl.org/cappellari/software
;
; If you have found this software useful for your research,
; I would appreciate an acknowledgment to the use of the
; "Penalized Pixel-Fitting method by Cappellari & Emsellem (2004)
;  as upgraded in Cappellari (2017)".
;
; This software is provided as is without any warranty whatsoever.
; Permission to use, for non-commercial purposes is granted.
; Permission to modify for personal or internal use is granted,
; provided this copyright and disclaimer are included unchanged
; at the beginning of the file. All other rights are reserved.
;
;#############################################################################
;+
; NAME:
;   PPXF
;
; PURPOSE:
;   Extract galaxy stellar kinematics (V, sigma, h3, h4, h5, h6,...)
;   or the stellar population and gas emission by fitting a template
;   to an observed spectrum in pixel space, using the
;   Penalized Pixel-Fitting (pPXF) method originally described in
;   Cappellari M., & Emsellem E., 2004, PASP, 116, 138
;       http://adsabs.harvard.edu/abs/2004PASP..116..138C
;   and upgraded in Cappellari M., 2017, MNRAS, 466, 798
;       http://adsabs.harvard.edu/abs/2017MNRAS.466..798C
;
;   The following key optional features are also available:
;   1) An optimal template, positive linear combination of different
;      input templates, can be fitted together with the kinematics.
;   2) One can enforce smoothness on the template weights during the fit.
;      This is useful to attach a physical meaning to the weights
;      e.g. in terms of the star formation history of a galaxy.
;   3) One can fit multple kinematic components for both the stars and the
;      gas emission lines. Both the stellar and gas LOSVD can be penalized
;      and can be described by a general Gauss-Hermite series.
;   4) Additive and/or multiplicative polynomials can be included to adjust
;      the continuum shape of the template to the observed spectrum.
;   5) Iterative sigma clipping can be used to clean the spectrum.
;   6) It is possible to fit a mirror-symmetric LOSVD to two spectra at
;      the same time. This is useful for spectra taken at point-symmetric
;      spatial positions with respect to the center of an equilibrium
;      stellar system.
;   7) One can include sky spectra in the fit, to deal with cases
;      where the sky dominates the observed spectrum and an accurate
;      sky subtraction is critical.
;   8) One can derive an estimate of the reddening in the spectrum.
;   9) The covariance matrix can be input instead of the error spectrum,
;      to account for correlated errors in the spectral pixels.
;
; CALLING SEQUENCE:
;   PPXF, templates, galaxy, noise, velScale, start, sol, $
;       BESTFIT=bestFit, BIAS=bias, CHI2DOF=chi2dof, /CLEAN, COMPONENT=component, $
;       DEGREE=degree, ERROR=error, GOODPIXELS=goodPixels, LAMBDA=lambda, /LINEAR, $
;       MATRIX=matrix, MDEGREE=mdegree, MOMENTS=moments, MPOLYWEIGHTS=mpolyweights, $
;       /PLOT, POLYWEIGHTS=polyWeights, /QUIET, REDDENING=reddening, REGUL=regul, $
;       REG_DIM=reg_dim, REG_ORD=reg_ord, SKY=sky, VSYST=vsyst, WEIGHTS=weights
;
; NOTE: some of the new options above have not yet been documented.
;       Their usage can now be inferred from the PPXF examples.
;
; INPUT PARAMETERS:
;   TEMPLATES: vector containing the spectrum of a single template star or more
;       commonly an array of dimensions TEMPLATES[nPixels,nTemplates] containing
;       different templates to be optimized during the fit of the kinematics.
;       nPixels has to be >= the number of galaxy pixels.
;     - To apply linear regularization to the WEIGHTS via the keyword REGUL,
;       TEMPLATES should be an array of two TEMPLATES[nPixels,nAge], three
;       TEMPLATES[nPixels,nAge,nMetal] or four TEMPLATES[nPixels,nAge,nMetal,nAlpha]
;       dimensions, depending on the number of population variables one wants to study.
;       This can be useful to try to attach a physical meaning to the output WEIGHTS, in
;       term of the galaxy star formation history and chmemical composition distribution.
;       In that case the templates may represent single stellar population SSP models
;       and should be arranged in sequence of increasing age, metallicity or alpha along
;       the second, third or fourth dimension of the array respectively.
;     - TEMPLATES and GALAXY do not need to span the same wavelength range. However
;       an error will be returned by PPXF, if the velocity shift in pixels,
;       required to match the galaxy with the templates, becomes larger than
;       nPixels. In that case one has to truncate either the galaxy or the
;       templates to make the two rest-frame spectral ranges more similar.
;   GALAXY: vector containing the spectrum of the galaxy to be measured. The
;       star and the galaxy spectra have to be logarithmically rebinned but the
;       continuum does *not* have to be subtracted. The rebinning may be
;       performed with the LOG_REBIN routine that is distributed with PPXF.
;     - For high redshift galaxies, one should bring the spectra close to the
;       restframe wavelength, before doing the PPXF fit, to prevent too large
;       velocity shifts of the templates. This can be done by dividing the
;       observed wavelenghts by (1+z), where z is a rough estimate of the
;       galaxy redshift, before the logarithmic rebinning.
;       See Section 2.4 of Cappellari (2017) for details.
;     - GALAXY can also be an array of dimensions GALAXY[nGalPixels,2] containing
;       two spectra to be fitted, at the same time, with a reflection-symmetric
;       LOSVD. This is useful for spectra taken at point-symmetric spatial
;       positions with respect to the center of an equilibrium stellar system.
;       For a discussion of the usefulness of this two-sided fitting
;       see e.g. Section 3.6 of Rix & White (1992, MNRAS, 254, 389).
;     - IMPORTANT: 1) For the two-sided fitting the VSYST keyword has to be used.
;       2) Make sure the spectra are rescaled to be not too many order of
;       magnitude different from unity, to avoid over or underflow problems
;       in the calculation. E.g. units of erg/(s cm^2 A) may cause problems!
;   NOISE: vector containing the 1*sigma error (per pixel) in the galaxy spectrum,
;       or covariance matrix describing the correlated errors in the galaxy spectrum.
;       Of course this vector/matrix must have the same units as the galaxy spectrum.
;     - If GALAXY is a Nx2 array, NOISE has to be an array with the same dimensions.
;     - When NOISE has dimensions NxN it is assumed to contain the covariance matrix
;       with elements sigma(i,j). When the errors in the spectrum are uncorrelated
;       it is mathematically equivalent to input in PPXF an error vector NOISE=errvec
;       or a NxN diagonal matrix NOISE=DIAG_MATRIX(errvec^2) (note squared!).
;     - IMPORTANT: the penalty term of the pPXF method is based on the *relative*
;       change of the fit residuals. For this reason the penalty will work as
;       expected even if no reliable estimate of the NOISE is available
;       (see Cappellari & Emsellem [2004] for details).
;       If no reliable noise is available this keyword can just be set to:
;           NOISE = galaxy*0+1 ; Same weight for all pixels
;   VELSCALE: velocity scale of the spectra in km/s per pixel. It has to be the
;       same for both the galaxy and the template spectra.
;     - VELSCALE is *defined* in pPXF by VELSCALE = c*Delta[alog(lambda)],
;       which is approximately VELSCALE ~ c*Delta(lambda)/lambda.
;       See Section 2.3 of Cappellari (2017) for details.
;   START: two elements vector [velStart,sigmaStart] with the initial estimate
;       for the velocity and the velocity dispersion in km/s.
;     - Unless a good initial guess is available, it is recommended to set the
;       starting sigma >= 3*velscale in km/s (i.e. 3 pixels). In fact when the
;       sigma is very low, and far from the true solution, the chi^2 of the fit
;       becomes weakly sensitive to small variations in sigma (see pPXF paper).
;       In some instances the near-constancy of chi^2 may cause premature
;       convergence of the optimization.
;     - In the case of two-sided fitting a good starting value for the
;       velocity is velStart=0.0 (in this case VSYST will generally be nonzero).
;       Alternatively on should keep in mind that velStart refers to the first
;       input galaxy spectrum, while the second will have velocity -velStart.
;
; KEYWORDS:
;   BESTFIT: a named variable to receive a vector with the best fitting
;       template: this is a linear combination of the templates, convolved with
;       the best fitting LOSVD, with added polynomial continuum terms.
;   BIAS: This parameter biases the (h3,h4,...) measurements towards zero
;       (Gaussian LOSVD) unless their inclusion significantly decreses the
;       error in the fit. Set this to BIAS=0.0 not to bias the fit: the
;       solution (including [V,sigma]) will be noisier in that case. The
;       default BIAS should provide acceptable results in most cases, but it
;       would be safe to test it with Monte Carlo simulations. This keyword
;       precisely corresponds to the parameter \lambda in the Cappellari &
;       Emsellem (2004) paper. Note that the penalty depends on the *relative*
;       change of the fit residuals, so it is insensitive to proper scaling
;       of the NOISE vector. A nonzero BIAS can be safely used even without a
;       reliable NOISE spectrum, or with equal weighting for all pixels.
;   /CLEAN: set this keyword to use the iterative sigma clipping method
;       described in Section 2.1 of Cappellari et al. (2002, ApJ, 578, 787).
;       This is useful to remove from the fit unmasked bad pixels, residual
;       gas emissions or cosmic rays.
;     - IMPORTANT: This is recommended *only* if a reliable estimate of the
;       NOISE spectrum is available. See also note below for SOL.
;   DEGREE: degree of the *additive* Legendre polynomial used to correct
;       the template continuum shape during the fit (default: 4).
;       Set DEGREE = -1 not to include any additive polynomial.
;   ERROR: a named variable that will contain a vector of *formal* errors
;       (1*sigma) for the fitted parameters in the output vector SOL. This
;       option can be used when speed is essential, to obtain an order of
;       magnitude estimate of the uncertainties, but we *strongly* recommend to
;       run Monte Carlo simulations to obtain more reliable errors. In fact these
;       errors can be severely underestimated in the region where the penalty
;       effect is most important (sigma < 2*velScale).
;     - These errors are meaningless unless Chi^2/DOF~1 (see parameter SOL below).
;       However if one *assume* that the fit is good, a corrected estimate of the
;       errors is: errorCorr = error*sqrt(chi^2/DOF) = error*sqrt(sol[6]).
;     - IMPORTANT: when running Monte Carlo simulations to determine the error,
;       the penalty (BIAS) should be set to zero, or better to a very small value.
;       See Section 3.4 of Cappellari & Emsellem (2004) for an explanation.
;   GOODPIXELS: integer vector containing the indices of the good pixels in the
;       GALAXY spectrum (in increasing order). Only these pixels are included in
;       the fit. If the /CLEAN keyword is set, in output this vector will be updated
;       to contain the indices of the pixels that were actually used in the fit.
;     - IMPORTANT: in all likely situations this keyword *has* to be specified.
;   LAMBDA: When the keyword REDDENING is used, the user has to pass in this
;       keyword a vector with the same dimensions of GALAXY, giving the restframe
;       wavelength in Angstrom of every pixel in the input galaxy spectrum.
;       If one uses my LOG_REBIN routine to rebin the spectrum before the PPXF fit:
;           LOG_REBIN, lamRange, galaxy, galaxyNew, logLam
;       the wavelength can be obtained as lambda = EXP(logLam).
;   /LINEAR: set this keyword to keep *all* nonlinear parameters fixed and *only*
;       perform a linear fit for the templates and additive polynomials weights.
;       The output solution is a copy of the input one and the errors are zero.
;   MATRIX: Design matrix[nPixels, DEGREE+nTemplates] of the linear system.
;     - matrix[nPixels, 0:DEGREE-1] contains the additive polynomials if DEGREE >= 0.
;     - matrix[nPixels, DEGREE:*] contains the templates convolved by the LOSVD
;       and multiplied by the multiplicative polynomials if MDEGREE > 0.
;     - matrix[nPixels, -nGas:*] contains the nGas emission line templates if
;       given. In the latter case the best fitting gas emission line spectrum is
;           lines = matrix[*, -nGas:*] # weights[-nGas:*]
;   MDEGREE: degree of the *multiplicative* Legendre polynomial (with mean of 1)
;       used to correct the continuum shape during the fit (default: 0). The
;       zero degree multiplicative polynomial is always included in the fit as
;       it corresponds to the weights assigned to the templates.
;       Note that the computation time is longer with multiplicative
;       polynomials than with the same number of additive polynomials.
;     - IMPORTANT: Multiplicative polynomials cannot be used when
;       the REDDENING keyword is set.
;   MOMENTS: Order of the Gauss-Hermite moments to fit. Set this keyword to 4
;       to fit [h3,h4] and to 6 to fit [h3,h4,h5,h6]. Note that in all cases
;       the G-H moments are fitted (nonlinearly) *together* with [V,sigma].
;     - If MOMENTS=2 or MOMENTS is not set then only [V,sigma] are
;       fitted and the other parameters are returned as zero.
;     - If MOMENTS is negative then the kinematics of the given COMPONENT are
;       kept fixed to the input values.
;     - EXAMPLE: We want to keep fixed component 0, which has an LOSVD described
;       by [V, sigma, h3, h4] and is modelled with 100 spectral templates;
;       At the same time we fit [V, sigma] for COMPONENT=1, which is described
;       by 5 templates (this situation may arise when fitting stellar templates
;       with pre-determined stellar kinematics, while fitting the gas emission).
;       We should give in input to PPXF the following parameters:
;           COMPONENT = [replicate(0, 100), replicate(1, 5)]
;           MOMENTS = [-4, 2]  ; moments to fit for component 0 and 1 respectively
;           START = [[V, sigma, h3, h4], [V, sigma, 0, 0]]
;   /PLOT: set this keyword to plot the best fitting solution and the residuals
;       at the end of the fit.
;   POLYWEIGHTS: vector with the weights of the additive Legendre polynomials.
;       The best fitting additive polynomial can be explicitly evaluated as
;           x = cap_range(-1d,1d,n_elements(galaxy))
;           apoly = 0d ; Additive polynomial
;           for j=0,DEGREE do apoly += legendre(x,j)*polyWeights[j]
;     - When doing a two-sided fitting (see help for GALAXY parameter), the additive
;       polynomials are allowed to be different for the left and right spectrum.
;       In that case the output weights of the additive polynomials alternate between
;       the first (left) spectrum and the second (right) spectrum.
;   /QUIET: set this keyword to suppress verbose output of the best fitting
;       parameters at the end of the fit.
;   REDDENING: Set this keyword to an initail estimate of the reddening E(B-V)>=0
;       to fit a positive reddening together with the kinematics and the templates.
;       After the fit the input estimate is replaced with the best fitting E(B-V) value.
;       The fit assumes the exctinction curve of Calzetti et al. (2000, ApJ, 533, 682)
;       but any other prescriptions could be trivially implemented by modifying the
;       function PPXF_REDDENING_CURVE below.
;     - IMPORTANT: The MDEGREE keyword cannot be used when REDDENING is set.
;   REGUL: If this keyword is nonzero, the program applies first or second order
;       linear regularization to the WEIGHTS during the PPXF fit.
;       Regularization is done in one, two or three dimensions depending on whether
;       the array of TEMPLATES has two, three or four dimensions respectively.
;       Large REGUL values correspond to smoother WEIGHTS output. The WEIGHTS tend
;       to a linear trend for large REGUL. When this keyword is nonzero the solution
;       will be a trade-off between smoothness of WEIGHTS and goodness of fit.
;     - The effect of the regularization scheme is the following:
;       With REG_ORD=1 it enforces the numerical first derivatives between
;       neighbouring weights (in the 1-dim case) to be equal to
;       w[j] - w[j+1] = 0 with an error Delta=1/REGUL.
;       With REG_ORD=2 it enforce the numerical second derivatives between
;       neighbouring weights (in the 1-dim case) to be equal to
;       w[j-1] - 2*w[j] + w[j+1] = 0 with an error Delta=1/REGUL.
;       It may be helpful to define REGUL=1/Delta and view Delta as the
;       regularization error.
;     - IMPORTANT: Delta needs to be smaller but of the same order of magnitude
;       of the typical WEIGHTS to play an effect on the regularization.
;       One way to achieve this is:
;           (i) Divide the TEMPLATES array by a scalar in such a way that the typical
;               template has a median of one (e.g. TEMPLATES/=median(TEMPLATES));
;          (ii) Do the same for the input GALAXY spectrum (e.g. GALAXY/=median(GALAXY)).
;               In this situation a sensible guess for Delta will be a few percent.
;     - Here is a possible recipe for chosing the regularization parameter REGUL:
;          (i) Perform an un-regularized fit (REGUL=0) and then rescale the input
;              NOISE spectrum so that Chi^2/DOF = Chi^2/N_ELEMENTS(goodPixels) = 1.
;              This is achieved by rescaling the input NOISE spectrum as
;              NOISE = NOISE*sqrt(Chi^2/DOF) = NOISE*sqrt(SOL[6]);
;         (ii) Increase REGUL and iteratively redo the pPXF fit until the Chi^2
;              increases from the unregularized Chi^2 = N_ELEMENTS(goodPixels)
;              value by DeltaChi^2 = sqrt(2*n_elements(goodPixels)).
;       The derived regularization corresponds to the maximum one still consistent
;       with the observations and the derived star formation history will be the
;       smoothest (minimum curvature) that is still consistent with the observations.
;     - For a detailed explanation see Section 3.5 of Cappellari (2017).
;   REG_ORD: Order of the derivative that is minimized by the regularization.
;       The following two rotationally symmetric estimators are supported:
;       REG_ORD=1: minimizes integral of squared gradient: Grad[w] # Grad[w].
;       REG_ORD=2: minimizes integral of squared curvature: Laplacian[w]^2.
;   REG_DIM: When using regularization with more than one kinematic component
;       (using the COMPONENT keyword), the regularization is only applied to the
;       first one (COMPONENT=0). This is useful to fit the stellar population
;       and gas emission together.
;       In this situation one has to use the REG_DIM keyword, to give PPXF the
;       dimensions of the population parameters (e.g. nAge, nMetal, nAlpha).
;       One should creates the initial array of population templates like
;       e.g. TEMPLATES[nPixels, nAge, nMetal, nAlpha] and define
;           s1 = size(TEMPLATES,/DIM)
;           reg_dim = s1[1:*] = [nAge, nMetal, nAlpha]
;       The array of stellar templates is then reshaped into a 2-dim array as
;           TEMPLATES = reform(TEMPLATES, s1[0], product(reg_dim))
;       and the gas emission templates are appended as extra columns at the end.
;       An usage example is given in ppxf_population_gas_example_sdss.pro.
;     - When using regularization with a single component (the COMPONENT keyword
;       is not used or contains identical values), the number of population
;       templates along different dimensions (e.g. nAge, nMetal, nAlpha) is
;       inferred from the dimensions of the TEMPLATES array and this keyword is
;       not necessary.
;   SKY: vector containing the spectrum of the sky to be included in the fit, or array
;       of dimensions SKY[nPixels,nSky] containing different sky spectra to add to
;       the model of the observed GALAXY spectrum. The SKY has to be log-rebinned as
;       the GALAXY spectrum and needs to have the same number of pixels.
;     - The sky is generally subtracted from the data before the PPXF fit. However,
;       for oservations very heavily dominated by the sky spectrum, where a very
;       accurate sky subtraction is critical, it may be useful *not* to subtract
;       the sky from the spectrum, but to include it in the fit using this keyword.
;   VSYST: galaxy systemic velocity (zero by default). The input initial guess
;       and the output velocities are measured with respect to this velocity.
;       The value assigned to this keyword is *crucial* for the two-sided fitting.
;       In this case VSYST can be determined from a previous normal one-sided
;       fit to the galaxy velocity profile. After that initial fit, VSYST
;       can be defined as the measured velocity at the galaxy center.
;       More accurately VSYST is the value which has to be subtracted to obtain
;       a nearly anti-symmetric velocity profile at the two opposite sides of
;       the galaxy nucleus.
;     - IMPORTANT: this value is generally *different* from the systemic
;       velocity one can get from the literature. Do not try to use that!
;   WEIGHTS: a named variable to receive the value of the weights by which each
;       template was multiplied to best fit the galaxy spectrum. The optimal
;       template can be computed with an array-vector multiplication:
;           TEMP = TEMPLATES # WEIGHTS (in IDL syntax)
;     - When the SKY keyword is used WEIGHTS[0:nTemplates-1] contains the weights
;       for the templates, while WEIGHTS[nTemplates:*] gives the ones for the sky.
;       In that case the best fitting galaxy template and sky are given by:
;           TEMP = TEMPLATES # WEIGHTS[0:nTemplates-1]
;           BESTSKY = SKY # WEIGHTS[nTemplates:*]
;     - When doing a two-sided fitting (see help for GALAXY parameter) *together*
;       with the SKY keyword, the sky weights are allowed to be different for the
;       left and right spectrum. In that case the output sky weights alternate
;       between the first (left) spectrum and the second (right) spectrum.
;
; OUTPUT PARAMETER:
;   SOL: seven elements vector containing in output the values of
;       [Vel, Sigma, h3, h4, h5, h6, Chi^2/DOF] of the best fitting solution, where DOF
;       is the number of Degrees of Freedom (number of fitted spectral pixels).
;     - When fitting multiple kinematic COMPONENT, sol[6, ncomp] contains the solution
;       for all different components, one after the other, sorted by COMPONENT.
;     - Vel is the velocity, Sigma is the velocity dispersion, h3-h6 are the
;       Gauss-Hermite coefficients. The model parameter are fitted simultaneously.
;     - IMPORTANT: pPXF does not directly measure velocities, instead it measures
;       shifts in spectral pixels. Given that the spectral pixels are equally spaced
;       in logarithmic units, this implies that pPXF measures shifts of np.log(lam).
;       As one is generally interested in velocities in km/s, Vel is
;       *defined* in pPXF by Vel = c*alog(lam_obs/lam_0), which reduces
;       to the well known Doppler formula Vel = c*dLam/lam_0 for small dLam.
;       In this way pPXF returns meaningful velocities for nearby galaxies,
;       or when a spectrum was de-redshifted before extracting the kinematics.
;       However Vel is not a well-defined quantity at large redshifts and one
;       should transform it into redshift for meaninful results.
;       Given the above definition, the precise relation between the output pPXF
;       velocity and redshift is Vel = c*alog(1 + z), which reduces to the well
;       known approximation z ~ Vel/c in the limit of small Vel.
;       See Section 2.3 of Cappellari (2017) for a detailed explanation.
;     - I hardcoded the following safety limits on the fitting parameters:
;         a) Vel is constrained to be +/-2000 km/s from the first input guess
;         b) velScale/100 < Sigma < 1000 km/s
;         c) -0.3 < [h3, h4, ...] < 0.3 (limits are extreme value for real galaxies)
;     - In the case of two-sided LOSVD fitting the output values refer
;       to the first input galaxy spectrum, while the second spectrum will
;       have by construction kinematics parameters [-Vel, Sigma, -h3, h4, -h5, h6].
;       If VSYST is nonzero (as required for two-sided fitting), then the
;       output velocity is measured with respect to VSIST.
;     - IMPORTANT: if Chi^2/DOF is not ~1 it means that the errors are not
;       properly estimated, or that the template is bad and it is *not* safe
;       to set the /CLEAN keyword.
;     - When MDEGREE > 0 then SOL contains in output the 7+MDEGREE elements
;       [Vel, Sigma, h3, h4, h5, h6, Chi^2/DOF, cx1, cx2, ..., cxn], where cx1, cx2, ..., cxn
;       are the coefficients of the multiplicative Legendre polynomials
;       of order 1, 2, ..., n. The polynomial can be explicitly evaluated as:
;           x = cap_range(-1d,1d,n_elements(galaxy))
;           mpoly = 1d ; Multiplicative polynomial
;           for j=1,MDEGREE do mpoly += legendre(x,j)*sol[6+j]
;
;--------------------------------
; IMPORTANT: Proper usage of pPXF
;--------------------------------
;
; The PPXF routine can give sensible quick results with the default BIAS
; parameter, however, like in any penalized/filtered/regularized method, the
; optimal amount of penalization generally depends on the problem under study.
;
; The general rule here is that the penalty should leave the line-of-sight
; velocity-distribution (LOSVD) virtually unaffected, when it is well
; sampled and the signal-to-noise ratio (S/N) is sufficiently high.
;
; EXAMPLE: If you expect an LOSVD with up to a high h4 ~ 0.2 and your
; adopted penalty (BIAS) biases the solution towards a much lower h4 ~ 0.1,
; even when the measured sigma > 3*velScale and the S/N is high, then you
; are *misusing* the pPXF method!
;
; THE RECIPE: The following is a simple practical recipe for a sensible
; determination of the penalty in pPXF:
;
; 1. Choose a minimum (S/N)_min level for your kinematics extraction and
;    spatially bin your data so that there are no spectra below (S/N)_min;
;
; 2. Perform a fit of your kinematics *without* penalty (PPXF keyword BIAS=0).
;    The solution will be noisy and may be affected by spurious solutions,
;    however this step will allow you to check the expected mean ranges in
;    the Gauss-Hermite parameters [h3,h4] for the galaxy under study;
;
; 3. Perform a Monte Carlo simulation of your spectra, following e.g. the
;    included ppxf_simulation_example.pro routine. Adopt as S/N in the simulation
;    the chosen value (S/N)_min and as input [h3,h4] the maximum representative
;    values measured in the non-penalized pPXF fit of the previous step;
;
; 4. Choose as penalty (BIAS) the *largest* value such that, for sigma > 3*velScale,
;    the mean difference delta between the output [h3,h4] and the input [h3,h4]
;    is well within (e.g. delta~rms/3) the rms scatter of the simulated values
;    (see e.g. Fig.2 of Emsellem et al. 2004, MNRAS, 352, 721).
;
;--------------------------------
;
; REQUIRED ROUTINES:
;       RANGE: by M. Cappellari (included in the PPXF distribution)
;       BVLS: by M. Cappellari from http://purl.org/cappellari/idl
;       MPFIT: by C.B. Markwardt http://purl.com/net/mpfit
;       ROBUST_SIGMA: by H. Freudenreich, which is included in
;           The IDL Astronomy User's Library http://idlastro.gfsc.nasa.gov/
;       CGPLOT: by David Fanning http://www.idlcoyote.com/, included in
;           The IDL Astronomy User's Library http://idlastro.gfsc.nasa.gov/
;
; MODIFICATION HISTORY:
;   V1.0.0: Created by Michele Cappellari, Leiden, 10 October 2001.
;   V3.4.7: First released version. MC, Leiden, 8 December 2003
;   V3.5.0: Included /OVERSAMPLE option. MC, Leiden, 11 December 2003
;   V3.6.0: Added MDEGREE option for multiplicative polynomials.
;           Linear implementation: fast, works well in most cases, but
;           can fail in certain cases. MC, Leiden, 19 March 2004
;   V3.7.0: Revised implementation of MDEGREE option. Nonlinear implementation:
;           straightforward, robust, but slower. MC, Leiden, 23 March 2004
;   V3.7.1: Updated documentation. MC, Leiden, 31 March 2004
;   V3.7.2: Corrected program stop after fit when MOMENTS=2.
;           Bug was introduced in V3.7.0. MC, Leiden, 28 April 2004
;   V3.7.3: Corrected bug: keyword ERROR was returned in pixels
;           instead of km/s. Decreased lower limit on fitted dispersion.
;           Thanks to Igor V. Chilingarian. MC, Leiden, 7 August 2004
;   V4.0.0: Introduced optional two-sided fitting assuming a reflection-symmetric
;           LOSVD for two input spectra. MC, Vicenza, 16 August 2004
;   V4.1.0: Corrected implementation of two-sided fitting of the LOSVD.
;           Thanks to Stefan van Dongen for reporting problems.
;           MC, Leiden, 3 September 2004
;   V4.1.1: Increased maximum number of iterations ITMAX in BVLS.
;           Thanks to Jesus Falcon-Barroso for reporting problems.
;           Introduced error message when velocity shift is too big.
;           Corrected output when MOMENTS=0. MC, Leiden, 21 September 2004
;   V4.1.2: Handle special case where a single template without additive
;           polynomials is fitted to the galaxy. MC, Leiden, 11 November 2004
;   V4.1.3: Updated documentation. MC, Vicenza, 30 December 2004
;   V4.1.4: Make sure input NOISE is a positive vector. MC, Leiden, 12 January 2005
;   V4.1.5: Verify that GOODPIXELS is monotonic and does not contain duplicated values.
;           After feedback from Richard McDermid. MC, Leiden, 10 February 2005
;   V4.1.6: Print number of nonzero templates. Do not print outliers in /QUIET mode.
;           MC, Leiden, 20 January 2006
;   V4.1.7: Updated documentation with important note on penalty determination.
;           MC, Oxford, 6 October 2007
;   V4.2.0: Introduced optional fitting of SKY spectrum. Many thanks to
;           Anne-Marie Weijmans for testing. MC, Oxford, 15 March 2008
;   V4.2.1: Use LA_LEAST_SQUARES (IDL 5.6) instead of SVDC when fitting
;           a single template. Please let me know if you need to use PPXF
;           with an older IDL version. MC, Oxford, 17 May 2008
;   V4.2.2: Added keyword POLYWEIGHTS. MC, Windhoek, 3 July 2008
;   V4.2.3: Corrected error message for too big velocity shift.
;           MC, Oxford, 27 November 2008
;   V4.3.0: Introduced REGUL keyword to perform linear regularization of WEIGHTS
;           in one or two dimensions. MC, Oxford, 4 Mach 2009
;   V4.4.0: Introduced Calzetti et al. (2000) PPXF_REDDENING_CURVE function to
;           estimate the reddening from the fit. MC, Oxford, 18 September 2009
;   V4.5.0: Dramatic speed up in the convolution of long spectra.
;           MC, Oxford, 13 April 2010
;   V4.6.0: Important fix to /CLEAN procedure: bad pixels are now properly
;           updated during the 3sigma iterations. MC, Oxford, 12 April 2011
;   V4.6.1: Use Coyote Graphics (http://www.idlcoyote.com/) by David W. Fanning.
;           The required routines are now included in NASA IDL Astronomy Library.
;           MC, Oxford, 29 July 2011
;   V4.6.2: Included option for 3D regularization and updated documentation of
;           REGUL keyword. MC, Oxford, 17 October 2011
;   V4.6.3: Do not change TEMPLATES array in output when REGUL is nonzero.
;           From feedback of Richard McDermid. MC, Oxford 25 October 2011
;   V4.6.4: Increased oversampling factor to 30x, when the /OVERSAMPLE keyword
;           is used. Updated corresponding documentation. Thanks to Nora
;           Lu"tzgendorf for test cases illustrating errors in the recovered
;           velocity when the sigma is severely undersampled.
;           MC, Oxford, 9 December 2011
;   V4.6.5: Expanded documentation of REGUL keyword. MC, Oxford, 15 November 2012
;   V4.6.6: Uses CAP_RANGE to avoid potential naming conflicts.
;           MC, Paranal, 8 November 2013
;   V4.6.7: Fixed G-H moments penalization when using multiplicative polynomials.
;           Improved /CLEAN loop. MC, Oxford, 6 December 2013
;   V4.7.0: A PPXF version adapted for multiple kinematic components existed for years.
;           It was updated in JAN/2012 for the paper by Johnston et al. (2013, MNRAS).
;           This version merges those changes with the public PPXF version, making
;           sure that all previous PPXF options are still supported.
;           MC, Oxford, 9 January 2014
;   V4.7.1: Fixed potential program stop introduced in V4.7.0.
;           MC, Portsmouth, 22 January 2014
;   V4.7.2: Replaced REBIN with INTERPOLATE with /OVERSAMPLE keyword. This is to
;           account for the fact that the Line Spread Function of the observed galaxy
;           spectrum already includes pixel convolution. Thanks to Mike Blanton
;           for the suggestion. MC, Oxford, 6 May 2014
;   V4.7.3: Allow for an input covariance matrix instead of an error spectrum.
;           MC, Oxford, 7 May 2014
;   V4.7.4: Fixed program stop with REDDENING keyword, introduced in V4.7.
;           Thanks to Se'bastien Comero'n (Finland) for reprorting the bug.
;           MC, Oxford, 23 May 2014
;   V4.7.5: Relaxed limit on maximum initial velocity shift.
;           MC, Oxford, 3 September 2014
;   V4.7.6: Properly normalize LOSVD with OVERSAMPLE. MC, Oxford, 16 September 2014
;   V4.7.7: Reverted change introduced in V4.7.2. Thanks to Nora Lu"tzgendorf
;           for reporting problems with /OVERSAMPLE. MC, Sydney, 5 February 2015
;   V4.7.8: Updated documentation of MOMENTS for negative values.
;           MC, Oxford, 9 November 2015
;   V4.7.9: Included design MATRIX in output and correspondingly updated documentation.
;           MC, Oxford, 16 November 2015
;   V4.7.10: Expanded explanation of the relation between output velocity and redshift.
;           MC, Oxford, 21 January 2016
;   V5.0.0: Compute the Fourier Transform of the LOSVD analytically:
;           Major improvement in velocity accuracy when sigma < velscale.
;           Removed OVERSAMPLE keyword, which is now unnecessary.
;           Removed limit on velocity shift of templates.
;           Updated documentation.
;           MC, Oxford, 2 August 2016
;   V5.0.1: Fixed obvious bug with multiple kinematic components, introduced in V.5.0.0.
;           MC, Oxford, 10 August 2016
;   V5.0.2: Updated references to published pPXF paper. MC, Oxford, 2 February 2017
;   V5.1.0: Improved curvature criterion for regularization when dim > 1.
;           MC, Oxford, 27 March 2017
;   V5.2.0: Included REG_ORD keyword to allow for both first and second order
;           regularization. Created separated functions ppxf_regularization
;           and ppxf_losvd_rfft. MC, Oxford, 3 April 2017
;   V5.2.1: Fixed program stop (from V5.0) with reflection-symmetric LOSVD fit.
;           MC, Oxford, 11 April 2017
;   V5.2.2: Return standard chi^2/DOF instead of robust estimate.
;           Print number of Jacobian calls and convergence status.
;           Allow for MDEGREE=-1 with REDDENING keyword. MC, Oxford, 4 July 2017
;   V5.2.3: Re-introduced /LINEAR keyword to only perform a linear fit and
;           skip the non-linear optimization.
;           Reduced bounds on multiplicative polynomials coefficients.
;           MC, Oxford, 28 November 2017
;   V5.2.4: Replaced COMPLEX with DCOMPLEX in PPXF_LOSVD_RFFT.
;           MC, Oxford, 2 March 2018
;-
;----------------------------------------------------------------------------
FUNCTION ppxf_reddening_curve, lambda, ebv
compile_opt idl2, hidden
;
; Reddening curve of Calzetti et al. (2000, ApJ, 533, 682; here C+00).
; This is reliable between 0.12 and 2.2 micrometres.
; - LAMBDA is the restframe wavelength in Angstrom of each pixel in the
; input galaxy spectrum (1 Angstrom = 1d-4 micrometres)
; - EBV is the assumed E(B-V) colour excess to redden the spectrum.
; In output the vector FRAC gives the fraction by which the flux at each
; wavelength has to be multiplied, to model the dust reddening effect.

k1 = lambda*0
ilam = 1e4/lambda ; Convert Angstrom to micrometres and take 1/lambda
rv = 4.05d ; C+00 equation (5)

w1 = where(lambda ge 6300d, m1, COMPLEMENT=w2, NCOMPLEMENT=m2)
; C+00 equation (3) but extrapolate for lam>2.2
if m1 gt 0 then k1[w1] = rv + 2.659d*(1.040d*ilam[w1] - 1.857d)
; C+00 equation (4) (in Horner form) but extrapolate for lam<0.12
if m2 gt 0 then k1[w2] = rv + $
    ilam[w2]*((0.029249d*ilam[w2] - 0.526482d)*ilam[w2] + 4.01243d) - 5.7328d
fact = 10d^(-0.4d*ebv*(k1>0))  ; Calzetti+00 equation (2) with opposite sign

return, fact ; The model spectrum has to be multiplied by this vector
END
;----------------------------------------------------------------------------
FUNCTION ppxf_convol_fft, f, k_ft
compile_opt idl2, hidden

nf = n_elements(f)
npad = 2L^ceil(alog(nf)/alog(2))
f1 = dblarr(npad)
f1[0] = f
k_ft = shift(k_ft, -(npad-1)/2)
con = real_part(fft(fft(f1, -1)*k_ft, 1))

return, con[0:nf-1]
END
;----------------------------------------------------------------------------
FUNCTION ppxf_BVLS_Solve, A, b, npoly
compile_opt idl2, hidden

; No need to enforce positivity constraints if fitting one single template:
; use faster linear least-squares solution instead of BVLS.
;
s = size(a)
if s[0] eq 1 then $ ; A is a vector, not an array
    soluz = total(A*b)/total(A^2) $
else if s[2] eq npoly+1 then $ ; Fitting a single template
    soluz = la_least_squares(transpose(A), b) $
else begin               ; Fitting multiple templates
    bnd = dblarr(2, s[2], /NOZERO)
    if npoly gt 0 then bnd[0, 0:npoly-1] = -1e9 ; No bounds on Legendre polynomials
    bnd[0, npoly:*] = 0d  ; Positivity constraints on the templates (and sky spectra)
    bnd[1, *] = 1d9
    BVLS, A, B, bnd, soluz, ITMAX=15*s[2], IERR=ierr
    if ierr ne 0 then message, 'BVLS Error n. ' + strtrim(ierr, 2)
endelse

return, soluz
END
;----------------------------------------------------------------------------
FUNCTION ppxf_losvd_rfft, pars, nspec, moments, nf, ncomp, vsyst
compile_opt idl2, hidden

; Analytic Fourier Transform (of real input) of the Gauss-Hermite LOSVD.
; Equation (38) of Cappellari M., 2017, MNRAS, 466, 798
; http://adsabs.harvard.edu/abs/2017MNRAS.466..798C

npad = 2L^ceil(alog(nf)/alog(2))
losvd_ft = dcomplexarr(npad, ncomp, nspec, /NOZERO)
w = 2*!dpi/npad*cap_range(-(npad/2d - 1), npad/2d, npad)  ; No FFT of real input in IDL: full frequency range
p = 0
for j=0, ncomp-1 do begin
    for k=0, nspec-1 do begin    ; nspec=2 for two-sided fitting, otherwise nspec=1
        s = (k eq 0) ? 1d : -1d  ; s=+1 for left spectrum, s=-1 for right one
        vel = vsyst + s*pars[0+p]
        sig = pars[1+p]
        a = -vel/sig
        w1 = w*sig
        w2 = w1^2
        losvd_ft[*, j, k] = exp(dcomplex(-0.5d*w2, a*w1))

        ; Hermite polynomials normalized as in Appendix A of van der Marel & Franx (1993).
        ; Coefficients for h5, h6 are given e.g. in Appendix C of Cappellari et al. (2002)
        ;
        if moments[j] gt 2 then begin
            poly = 1d + dcomplex(pars[3+p]/Sqrt(24d)*(w2*(4d*w2-12d)+3d), $ ; H4 real
                                 s*pars[2+p]/Sqrt(3d)*(w1*(2d*w2-3d)))      ; H3 imaginary
            if moments[j] eq 6 then $
                poly -= dcomplex(pars[5+p]/Sqrt(720d)*(w2*(w2*(8d*w2-60d)+90d)-15d), $ ; H6 real
                                 s*pars[4+p]/Sqrt(60d)*(w1*(w2*(4d*w2-20d)+15d)))      ; H5 imginary
            losvd_ft[*, j, k] *= poly
        endif
    endfor
    p += moments[j]
endfor

return, losvd_ft
END
;----------------------------------------------------------------------------
PRO ppxf_regularization, c, degree, npix, nspec, reg_dim, reg_ord, regul
compile_opt idl2, hidden

; Add first or second order 1D, 2D or 3D linear regularization.
; Equation (25) of Cappellari M., 2017, MNRAS, 466, 798
; http://adsabs.harvard.edu/abs/2017MNRAS.466..798C

i = indgen(reg_dim) + (degree+1)*nspec
p = npix*nspec
dim = n_elements(reg_dim)
case reg_ord of
    1: begin    ; Minimize integral of (Grad[w] # Grad[w])
        diff = [1d, -1d]*regul
        case dim of
            1: for j=0, reg_dim[0]-2 do c[p++, i[j:j+1]] = diff
            2: for k=0, reg_dim[1]-1 do $
                   for j=0, reg_dim[0]-1 do begin
                       if j lt reg_dim[0]-1 then c[p++, i[j:j+1, k]] = diff
                       if k lt reg_dim[1]-1 then c[p++, i[j, k:k+1]] = diff
                   endfor
            3: for q=0, reg_dim[2]-1 do $
                   for k=0, reg_dim[1]-1 do $
                       for j=0, reg_dim[0]-1 do begin
                           if j lt reg_dim[0]-1 then c[p++, i[j:j+1, k, q]] = diff
                           if k lt reg_dim[1]-1 then c[p++, i[j, k:k+1, q]] = diff
                           if q lt reg_dim[2]-1 then c[p++, i[j, k, q:q+1]] = diff
                       endfor
        endcase
    end
    2: begin    ; Minimize integral of Laplacian[w]^2
        diff = [-1d, 2d, -1d]*regul
        case dim of
            1: for j=1, reg_dim[0]-2 do c[p++, i[j-1:j+1]] = diff
            2: for k=0, reg_dim[1]-1 do $
                   for j=0, reg_dim[0]-1 do begin
                       if j gt 0 && j lt reg_dim[0]-1 then c[p, i[j-1:j+1, k]] = diff
                       if k gt 0 && k lt reg_dim[1]-1 then c[p, i[j, k-1:k+1]] += diff
                       p++
                   endfor
            3: for q=0, reg_dim[2]-1 do $
                   for k=0, reg_dim[1]-1 do $
                       for j=0, reg_dim[0]-1 do begin
                           if j gt 0 && j lt reg_dim[0]-1 then c[p, i[j-1:j+1, k, q]] = diff
                           if k gt 0 && k lt reg_dim[1]-1 then c[p, i[j, k-1:k+1, q]] += diff
                           if q gt 0 && q lt reg_dim[2]-1 then c[p, i[j, k, q-1:q+1]] += diff
                           p++
                       endfor
        endcase
    end
endcase

END
;----------------------------------------------------------------------------
FUNCTION ppxf_linear_fit, pars, $
    BESTFIT=bestFit, BIAS=bias, CLEAN=clean, DEGREE=degree, $
    GALAXY=galaxy, GOODPIXELS=goodPixels, MDEGREE=mdegree, $
    NOISE=noise, QUIET=quiet, SKY=sky, STAR=star, VSYST=vsyst, WEIGHTS=weights, $
    REGUL=regul, REG_DIM=reg_dim, REG_ORD=reg_ord, LAMBDA=lambda, MATRIX=matrix, $
    NCOMP=ncomp, COMPONENT=component, MOMENTS=moments
compile_opt idl2, hidden

; This function implements the procedure described in
; Sec.3.3 of Cappellari M., 2017, MNRAS, 466, 798
; http://adsabs.harvard.edu/abs/2017MNRAS.466..798C

s = size(galaxy)
nspec = s[0]
npix = s[1]
npars = n_elements(pars) - mdegree*nspec  ; Parameters of the LOSVD only
if n_elements(lambda) gt 1 then npars -= 1 ; Fitting reddening

; pars = [vel, sigma, h3, h4, ..., m1, m2, ...]    ; Velocities are in pixels
;
nf = (size(star))[1]
losvd_ft = ppxf_losvd_rfft(pars, nspec, moments, nf, ncomp, vsyst)

; The zeroth order multiplicative term is already included in the
; linear fit of the templates. The polynomial below has mean of 1.
;
x = cap_range(-1d, 1d, npix) ; X needs to be within [-1, 1] for Legendre Polynomials
mpoly = 1d  ; The loop below can be null if mdegree < 1
for j=1, mdegree do $
    if nspec eq 2 then $ ; Different multiplicative poly for left and right spectra
        mpoly += legendre(x, j) # pars[npars+2*j-[2, 1]] $
    else mpoly += legendre(x, j) * pars[npars+j-1]

; Multiplicative polynomials do not make sense when fitting reddening.
; In that case one has to assume the spectrum is well calibrated.
;
if n_elements(lambda) gt 1 then mpoly = ppxf_reddening_curve(lambda, pars[npars])

; Fill the columns of the design matrix of the least-squares problem
;
s = size(star)
ss = size(sky)
nsky = (ss[0] lt 2) ? ss[0] : ss[2] ; Number of sky spectra
ntemp = (s[0] eq 2) ? s[2] : 1     ; Number of template spectra
npoly = (degree + 1)*nspec         ; Number of additive polynomials
ncols = npoly + nsky*nspec + ntemp
nrows = npix*nspec
if regul gt 0 then begin
    case reg_ord of
        1: nreg = n_elements(reg_dim)*product(reg_dim)
        2: nreg = product(reg_dim)
    endcase
    nrows += nreg
endif

c = dblarr(npix*nspec, ncols)  ; This array is used for estimating predictions

for j=0, degree do begin ; Fill first columns of the Design Matrix
    leg = legendre(x, j)
    c[0, j] = leg
    if nspec eq 2 then c[npix, npoly/nspec+j] = leg ; poly for right spectrum
endfor

tmp = dblarr(s[1], nspec, /NOZERO)
for j=0, ntemp-1 do begin
    for k=0, nspec-1 do $
        tmp[*, k] = ppxf_convol_fft(star[*, j], losvd_ft[*, component[j], k])
    c[0, npoly+j] = (mpoly*tmp[0:npix-1, *])[*] ; reform into a vector
endfor

if nsky gt 0 then begin
    k = npoly + ntemp
    c[0, k] = sky
    if nspec eq 2 then c[npix, k+nsky] = sky
endif

a = dblarr(nrows, ncols)    ; This array is used for the actual solution of the system

s3 = size(noise)
if s3[1] eq s3[2] then begin ; input NOISE is a npix*npix covariance matrix
    a[0, 0] = noise # c
    b = noise # galaxy
endif else begin             ; input NOISE is a 1sigma error vector
    for j=0, ncols-1 do a[0, j] = c[*, j]/noise ; Weight all columns with errors
    b = galaxy/noise
endelse

if regul gt 0 then $
    ppxf_regularization, a, degree, npix, nspec, reg_dim, reg_ord, regul

; Select the spectral region to fit and solve the overconditioned system
; using SVD/BVLS. Use unweighted array for estimating bestfit predictions.
; Iterate to exclude pixels deviating more than 3*sigma if /CLEAN keyword is set.
;
repeat begin
    if regul gt 0 then begin
        aa = a[[goodPixels, cap_range(npix*nspec, nrows-1)], *]
        bb = [b[goodPixels], replicate(0d, nreg)]
    endif else begin
        aa = a[goodPixels, *]
        bb = b[goodPixels]
    endelse
    weights = ppxf_BVLS_Solve(aa, bb, npoly)
    bestfit = c # weights
    if s3[1] eq s3[2] then $ ; input NOISE is a npix*npix covariance matrix
        err = (noise # (galaxy - bestfit))[goodPixels] $
    else $                    ; input NOISE is a 1sigma error vector
        err = ((galaxy - bestfit)/noise)[goodPixels]
    if keyword_set(clean) then begin
        tmp = where(abs(err) gt 3, m, COMPLEM=w) ; select errors larger than 3*sigma
        if (m ne 0) then begin
            if ~keyword_set(quiet) then print, 'Outliers:', m
            goodPixels = goodPixels[w]
        endif
    endif else break
endrep until (m eq 0)

matrix = c  ; Return LOSVD-convolved templates matrix

; Penalize the solution towards (h3, h4, ...) = 0 if the inclusion of
; these additional terms does not significantly decrease the error.
; The lines below implement eq.(8)-(9) in Cappellari & Emsellem (2004)
;
if cap_any(moments gt 2) && bias ne 0 then begin
    p = 0
    D2 = 0d
    for j=0, ncomp-1 do begin
        if moments[j] gt 2 then $
            D2 += total(pars[2+p:moments[j]-1+p]^2)  ; eq.(8)
        p += moments[j]
    endfor
    err += bias*robust_sigma(err, /ZERO)*sqrt(D2)  ; eq.(9)
endif

return, err
END
;----------------------------------------------------------------------------
PRO ppxf, templates, galaxy, noise1, velScale, start, sol, $
    BESTFIT=bestFit, BIAS=bias, CLEAN=clean, DEGREE=degree, ERROR=error, $
    GOODPIXELS=goodPixels, MATRIX=matrix, MDEGREE=mdegree, MOMENTS=moments1, $
    POLYWEIGHTS=polyweights, PLOT=plot, QUIET=quiet, SKY=sky, VSYST=vsyst, $
    WEIGHTS=weights, REGUL=regul, LAMBDA=lambda, LINEAR=linear, $
    REDDENING=reddening, COMPONENT=component1, REG_DIM=reg_dim1, $
    REG_ORD=reg_ord, _EXTRA=ex, MPOLYWEIGHTS=mpolyweights, CHI2DOF=chi2
compile_opt idl2
on_error, 2

; Do extensive checking of possible input errors
;
s1 = size(templates)
if s1[0] ge 3 then begin
    reg_dim = s1[2:s1[0]]
    star = reform(templates, s1[1], product(reg_dim))
    s1 = size(star)
endif else begin
    star = templates
    if n_elements(reg_dim1) ne 0 then reg_dim = reg_dim1
endelse

if n_elements(component1) le 1 then $
    component = dblarr(s1[2]) $ ; all templates have the same LOSVD
else begin
    if n_elements(component1) ne s1[2] then $
        message, 'There must be one kinematic COMPONENT per template'
    component = component1
endelse
tmp = component[uniq(component, sort(component))] ; kinematic components
ncomp = n_elements(tmp)
if ~array_equal(tmp, indgen(ncomp)) then $
    message, 'must be 0 < COMPONENT < NCOMP-1'
if n_elements(regul) ne 0 and n_elements(reg_dim) eq 0 then $
    if ncomp eq 1 then begin
        ss = size(templates)
        reg_dim = ss[2:ss[0]]
    endif else message, 'reg_dim must be specified'
if n_elements(reg_ord) eq 0 then $
    reg_ord = 2 $
else if reg_ord ne 1 and reg_ord ne 2 then $
            message, 'REG_ORD must be either 1 or 2'
if n_elements(moments1) eq 1 then $
    moments = replicate(moments1, ncomp) $ ; all LOSVD have the same number of G-H moments
else $
    moments = moments1
if n_elements(moments) ne ncomp then $
    message, 'MOMENTS must be an array of length NCOMP'
absmom = abs(moments)

if n_elements(regul) eq 0 then begin
    regul = 0
    reg_dim = 0
endif
s2 = size(galaxy)
s3 = size(noise1)
s4 = size(sky)
if (s1[0] gt 2 || s2[0] gt 2 || s3[0] gt 2) then message, 'Wrong input dimensions'
if s3[1] gt 0 and s3[1] eq s3[2] then begin ; NOISE is a 2-dim covariance matrix
    if s3[1] ne s2[1] then message, 'Covariance Matrix must have size xpix*npix'
    noise = noise1   ; Do not modify input covariance matrix
    la_choldc, noise, /UPPER ; Cholesky factor of symmetric, positive-definite covariance matrix
    for j=0, s3[1]-2 do noise[j, j+1:*] = 0 ; Upper triangular elements should be zero
    noise = la_invert(noise) ; Invert Cholesky factor
endif else begin   ; NOISE is an error spectrum
    if ~array_equal(s2, s3) then message, 'GALAXY and NOISE must have the same size/type'
    if ~array_equal(noise1 gt 0, 1) then message, 'NOISE must be a positive error vector or covariance matrix'
    noise = noise1
endelse
if (s1[1] lt s2[1]) then message, 'STAR length cannot be smaller than GALAXY'
if n_elements(reddening) gt 0 then begin
    if ~array_equal(size(lambda), s2) then $
        message, 'LAMBDA and GALAXY must have the same size/type'
    if n_elements(mdegree) gt 0 then $
        if mdegree gt 0 then $
            message, 'MDEGREE cannot be used with REDDENING keyword'
endif else lambda = 0
if s4[0] gt 0 && s4[1] ne s2[1] then message, 'SKY must have the same size as GALAXY'
degree = ~n_elements(degree) ? 4 : degree > (-1)
mdegree = ~n_elements(mdegree) ? 0 : mdegree > 0
nGood = n_elements(goodPixels)
if nGood le 0 then begin
    nGood = s2[1]
    goodPixels = indgen(nGood)
endif else begin
    if ~array_equal((goodPixels[1:*] - goodPixels) gt 0, 1) then $
        message, 'GOODPIXELS is not monotonic or contains duplicated values'
    if goodPixels[0] lt 0 || goodPixels[nGood-1] gt s2[1]-1 then $
        message, 'GOODPIXELS are outside the data range'
endelse
if n_elements(bias) le 0 then bias = 0.7d*sqrt(500d/n_elements(goodPixels)) ; pPXF paper pg.144 left
if n_elements(moments) eq 0 then moments = 2 else begin
    for j=0, ncomp-1 do $
        if total(absmom[j] eq [2, 4, 6]) eq 0 then $
            message, 'MOMENTS should be 2, 4 or 6 (or negative to keep kinematics fixed)'
endelse
if ncomp gt 1 && ncomp ne (size(start, /dim))[1] then $
    message, 'Each component must have a starting guess in START'
if s2[0] eq 2 then goodPixels = [goodPixels, s2[1]-1+goodPixels]  ; two-sided fitting of LOSVD
if n_elements(vsyst) eq 0 then begin
    if s2[0] eq 2 then message, 'VSYST must be defined for two-sided fitting'
    vsyst = 0d
endif

ngh = total(absmom)
npars = ngh + mdegree*s2[0] + n_elements(reddening)

; Explicitly specify the step for the numerical derivatives
; in MPFIT routine and force safety limits on the fitting parameters.
;
; Set [h3, h4, ...] and mult. polynomials to zero as initial guess
; and constrain -0.3 < [h3, h4, ...] < 0.3
;
parinfo = replicate({step:1d-3, limits:[-0.3d, 0.3d], limited:[1, 1], value:0d, fixed:0}, npars)

p = 0
for j=0, ncomp-1 do begin
    start1 = start[0:1, j]/velScale  ; Convert velocity scale to pixels
    parinfo[0+p].limits = start1[0] + [-2d3, 2d3]/velScale ; +/-2000 km/s from first guess
    parinfo[1+p].limits = [0.01d, 1d3/velScale] ; hard-coded velScale/100<sigma<1000 km/s
    parinfo[[0, 1]+p].value = start1
    parinfo[[0, 1]+p].step = 1d-2
    if moments[j] lt 0 then begin
        parinfo[p:p+absmom[j]-1].fixed = 1
        if absmom[j] gt 2 then $
            parinfo[p+2:p+absmom[j]-1].value = start[2:*, j]
    endif
    p += absmom[j]
endfor

if mdegree gt 0 then begin
    parinfo[ngh:*].limits = [-0.5d, 0.5d] ; force <50% corrections
endif else if n_elements(reddening) gt 0 then begin
    parinfo[ngh].value = reddening
    parinfo[ngh].limits = [0d, 10d] ; force positive E(B-V) < 10 mag
endif

; Here the actual calculation starts.
; If required, once the minimum is found, clean the pixels deviating
; more than 3*sigma from the best fit and repeat the minimization
; until the set of cleaned pixels does not change any more.
;
if keyword_set(linear) then begin
    if mdegree gt 0 then message, 'MDEGREE must be zero with /LINEAR'
    res = parinfo.value
    perror = res*0
    niter = 0
    status = 1
    ncalls = 1
endif else begin
    good = goodPixels
    for j=0, 4 do begin ; Do at most five cleaning iterations
        if n_elements(sky) eq 0 then $
            functArgs = {BIAS:bias, DEGREE:degree, GALAXY:double(galaxy), $
                GOODPIXELS:goodPixels, MDEGREE:mdegree, NOISE:double(noise), $
                STAR:double(star), VSYST:vsyst/velScale, $
                REGUL:regul, REG_DIM:reg_dim, REG_ORD:reg_ord, LAMBDA:lambda, $
                NCOMP:ncomp, COMPONENT:component, MOMENTS:absmom} $
        else $
            functArgs = {BIAS:bias, DEGREE:degree, GALAXY:double(galaxy), $
                GOODPIXELS:goodPixels, MDEGREE:mdegree, NOISE:double(noise), $
                SKY:double(sky), STAR:double(star), VSYST:vsyst/velScale, $
                REGUL:regul, REG_DIM:reg_dim, REG_ORD:reg_ord, LAMBDA:lambda, $
                NCOMP:ncomp, COMPONENT:component, MOMENTS:absmom}
        res = mpfit('ppxf_linear_fit', ERRMSG=errmsg, $
            FTOL=1d-4, FUNCTARGS=functArgs, NFEV=ncalls, NITER=niter, $
            PARINFO=parinfo, PERROR=perror, STATUS=status, /QUIET)
        if errmsg ne '' then message, errmsg
        if ~keyword_set(clean) then break
        goodOld = goodPixels
        goodPixels = good
        tmp = ppxf_linear_fit(res, BIAS=bias, /CLEAN, $
            DEGREE=degree, GALAXY=galaxy, $
            GOODPIXELS=goodPixels, MDEGREE=mdegree, NOISE=noise, $
            QUIET=quiet, SKY=sky, STAR=star, VSYST=vsyst/velScale, $
            REGUL=regul, REG_DIM=reg_dim, REG_ORD=reg_ord, LAMBDA=lambda, $
            NCOMP=ncomp, COMPONENT=component, MOMENTS=absmom)
        if array_equal(goodOld, goodPixels) then break
    endfor
endelse

; Evaluate scatter at the bestfit (with BIAS=0)
; and also get the output BESTFIT, WEIGHTS and MATRIX.
;
err = ppxf_linear_fit(res, BESTFIT=bestFit, BIAS=0, DEGREE=degree, $
    GALAXY=galaxy, GOODPIXELS=goodPixels, MDEGREE=mdegree, $
    NOISE=noise, SKY=sky, STAR=star, VSYST=vsyst/velScale, WEIGHTS=weights, $
    REGUL=regul, REG_DIM=reg_dim, REG_ORD=reg_ord, LAMBDA=lambda, MATRIX=matrix, $
    NCOMP=ncomp, COMPONENT=component, MOMENTS=absmom)

chi2 = total(err^2)/(n_elements(goodpixels) - n_elements(res)) ; Chi^2/DOF
sol = dblarr(7+mdegree*s2[0], ncomp)
error = sol
p = 0
for j=0, ncomp-1 do begin
    sol[0, j] = res[p:absmom[j]+p-1]
    sol[0:1, j] *= velScale ; Bring velocity scale back to km/s
    error[0, j] = perror[p:absmom[j]+p-1]
    error[0:1, j] *= velScale ; Convert errors to km/s
    p += absmom[j]
endfor

sol[6, 0] = chi2 ; for backward compatibility (better to use CHI2DOF keyword)
if mdegree ge 1 then begin
    sol[7:*, 0] = res[ngh:*] ; for backward compatibility (better to use MPOLYWEIGHTS keyword)
    mpolyweights = res[ngh:*]
endif

if n_elements(reddening) gt 0 then reddening = res[ngh] ; Replace input with best fit
if degree ge 0 then polyweights = weights[0:(degree+1)*s2[0]-1] ; output weights for the additive polynomials
weights = weights[(degree+1)*s2[0]:*] ; output weights for the templates (or sky) only

; Print final results on the screen.
;
if ~keyword_set(quiet) then begin
    print, 'Component', 'V', 'sigma', 'h3', 'h4', 'h5', 'h6', FORMAT='(8a10)'
    for j=0, ncomp-1 do $
        print, j, sol[0:5, j], FORMAT='(i10, 2f10.0, 4f10.3)'
    print, 'Jac calls: ', niter, '; Func calls: ', ncalls, '; Status: ', status, FORMAT='(3(a, g0))'
    print, 'chi2/DOF:', chi2
    nw = n_elements(weights)
    if n_elements(reddening) gt 0 then print, 'Reddening E(B-V): ', reddening, FORMAT='(a, g0.3)'
    print, 'Nonzero Templates: ', total(weights gt 0), ' / ', nw, FORMAT='(2(a, g0))'
    if n_elements(weights) le 20 then begin
        print, 'Templates weights:'
        print, weights, FORMAT='(10g11.3)'
    endif
endif

; Plot final data-model comparison if required.
;
if keyword_set(plot) then begin
    mn = min(bestfit[goodPixels], MAX=mx)
    resid = mn + galaxy - bestfit
    cgplot, galaxy, XTITLE='pixels', YTITLE='counts', /XSTYLE, /YNOZERO, _EXTRA=ex, $
        YRANGE=[min(resid[goodPixels]), mx], YSTYLE=2, XRANGE=[-0.02, 1.02]*s2[1]*s2[0]
    cgplot, bestfit, COLOR='red', THICK=2, /OVERPLOT
    n = n_elements(goodPixels)
    cgplot, goodPixels, replicate(mn, n*s2[0]), PSYM=3, COLOR='lime green', /OVERPLOT
    cgplot, goodPixels, resid[goodPixels], PSYM=4, COLOR='lime green', SYMSIZE=0.3, /OVERPLOT
    w = where((goodPixels[1:*] - goodPixels) gt 1, m)
    for j=0, m-1 do begin
        x = cap_range(goodPixels[w[j]], goodPixels[w[j]+1])
        cgplot, x, resid[x], COLOR='blue', /OVERPLOT
    endfor
    w = (m gt 0) ? [0, w, w+1, n-1] : [0, n-1]  ; Add first and last point
    for j=0, n_elements(w)-1 do $
        cgplot, goodPixels[w[[j, j]]], [mn, bestfit[goodPixels[w[j]]]], COLOR='lime green', /OVERPLOT
    wait, 0.01 ; Ensure screen refresh under windows
endif

END
;----------------------------------------------------------------------------
