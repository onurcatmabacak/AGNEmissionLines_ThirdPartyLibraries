; Native GANDALF v1.5 driver for the gandalf_line tool.
;
; Input is a FITS file prepared by run_gandalf.py:
;   HDU0  galaxy flux density on a rest-frame log10 grid (1e-17 units)
;   HDU1  1-sigma error (same units)
;   HDU2  good-pixel mask (1 = use, 0 = reject)
;   HDU3  stellar templates, (npix_temp, n_temp), same log10 step
; Header: L0GAL, DLGAL, L0TEMPL, Z, INTDISP.
;
; The driver first attempts the canonical PPXF stellar-kinematics step and
; falls back to a fixed stellar LOSVD when PPXF cannot constrain it (common
; for AGN-dominated QSO continua).  GANDALF itself is always run natively
; with FOR_ERRORS=1, so the quoted errors are the MPFIT covariance errors.
pro gandalf_line_run, input=input, output=output, setup=setup, $
    mdegree=mdegree, degree=degree, int_disp=int_disp, $
    ppxf_mask_sigma=ppxf_mask_sigma, gandalf_mask_sigma=gandalf_mask_sigma, $
    use_ppxf=use_ppxf, ppxf_degree=ppxf_degree, ppxf_mdegree=ppxf_mdegree, $
    fixed_v=fixed_v, fixed_sigma=fixed_sigma, ppxf_sigma_min=ppxf_sigma_min, $
    ppxf_sigma_max=ppxf_sigma_max, ppxf_v_max=ppxf_v_max, $
    ppxf_chi2_max=ppxf_chi2_max, ppxf_sigma_snr_min=ppxf_sigma_snr_min, $
    ppxf_min_templates=ppxf_min_templates
  compile_opt idl2
  c = 299792.4580d

  if n_elements(mdegree) eq 0 then mdegree = 3
  if n_elements(degree) eq 0 then degree = 0
  if n_elements(int_disp) eq 0 then int_disp = 61.5d
  if n_elements(ppxf_mask_sigma) eq 0 then ppxf_mask_sigma = 200.0d
  if n_elements(gandalf_mask_sigma) eq 0 then gandalf_mask_sigma = 200.0d
  if n_elements(use_ppxf) eq 0 then use_ppxf = 1
  if n_elements(ppxf_degree) eq 0 then ppxf_degree = 0
  if n_elements(ppxf_mdegree) eq 0 then ppxf_mdegree = 3
  if n_elements(fixed_v) eq 0 then fixed_v = 0.0d
  if n_elements(fixed_sigma) eq 0 then fixed_sigma = 300.0d
  if n_elements(ppxf_sigma_min) eq 0 then ppxf_sigma_min = 30.0d
  if n_elements(ppxf_sigma_max) eq 0 then ppxf_sigma_max = 800.0d
  if n_elements(ppxf_v_max) eq 0 then ppxf_v_max = 500.0d
  if n_elements(ppxf_chi2_max) eq 0 then ppxf_chi2_max = 3.0d
  if n_elements(ppxf_sigma_snr_min) eq 0 then ppxf_sigma_snr_min = 3.0d
  if n_elements(ppxf_min_templates) eq 0 then ppxf_min_templates = 2

  galaxy = mrdfits(input, 0, hdr_gal, /silent)
  error  = mrdfits(input, 1, /silent)
  mask_arr = mrdfits(input, 2, /silent)
  ; mrdfits returns FITS images transposed; restore (npix_temp, n_temp)
  templates = transpose(mrdfits(input, 3, /silent))

  l0_gal = sxpar(hdr_gal, 'L0GAL')
  lstep_gal = sxpar(hdr_gal, 'DLGAL')
  l0_templ = sxpar(hdr_gal, 'L0TEMPL')
  z = sxpar(hdr_gal, 'Z')
  npix = n_elements(galaxy)
  velscale = c*lstep_gal*alog(10.0d)
  offset = -(l0_gal-l0_templ)*c*alog(10.0d)
  print, 'gandalf_line: npix=', npix, ' ntemp=', (size(templates))[2], $
         ' velscale=', velscale, ' l0=', l0_gal, ' z=', z

  readcol, setup, eml_i, eml_name, eml_lambda, eml_action, eml_kind, $
      eml_a, eml_v, eml_s, eml_fit, f='(i,a,f,a,a,f,f,f,a)', $
      skipline=2, comment='#', /silent
  emission_setup = create_struct('i', eml_i, 'name', eml_name, $
      'lambda', eml_lambda, 'action', eml_action, 'kind', eml_kind, $
      'a', eml_a, 'v', eml_v, 's', eml_s, 'fit', eml_fit)

  ; ------------------------------------------------------------------
  ; 1) Canonical PPXF stellar-kinematics step (optional; may fail on QSOs)
  ; ------------------------------------------------------------------
  ppxf_ok = 0
  ppxf_attempted = keyword_set(use_ppxf)
  ppxf_v = !values.d_nan
  ppxf_sigma = !values.d_nan
  ppxf_v_err = !values.d_nan
  ppxf_sigma_err = !values.d_nan
  ppxf_sigma_snr = !values.d_nan
  ppxf_chi2 = !values.d_nan
  ppxf_nz = 0
  ppxf_npix = 0
  ppxf_msg = 'not attempted'
  if keyword_set(use_ppxf) then begin
    gp = mask_emission_lines(npix, 0.0d, emission_setup, velscale, $
         l0_gal, lstep_gal, sigma=ppxf_mask_sigma, /log10)
    keep = bytarr(npix)
    keep[gp] = 1
    good_ppxf = where(keep and (mask_arr gt 0))
    ppxf_npix = n_elements(good_ppxf)
    if ppxf_npix gt 100 then begin
      start = [0.0d + offset, 300.0d]
      catch, err
      if err ne 0 then begin
        catch, /cancel
        ppxf_msg = 'PPXF exception: ' + !error_state.msg
        print, ppxf_msg
      endif else begin
        PPXF, templates, galaxy, error, velscale, start, sol_try, $
            goodpixels=good_ppxf, moments=2, degree=ppxf_degree, $
            mdegree=ppxf_mdegree, WEIGHTS=wtry, CHI2DOF=chi2try, $
            ERROR=ppxf_err, QUIET=1
        catch, /cancel
        ppxf_v = sol_try[0]
        ppxf_sigma = sol_try[1]
        ppxf_chi2 = chi2try
        ppxf_nz = n_elements(where(wtry gt 0))
        if n_elements(ppxf_err) ge 2 then begin
          ppxf_v_err = ppxf_err[0, 0]
          ppxf_sigma_err = ppxf_err[1, 0]
        endif
        if ppxf_sigma_err gt 0 then $
          ppxf_sigma_snr = ppxf_sigma/ppxf_sigma_err $
        else ppxf_sigma_snr = !values.d_nan
        reasons = ''
        if ppxf_sigma lt ppxf_sigma_min then $
          reasons = reasons + ' sigma<min'
        if ppxf_sigma gt ppxf_sigma_max then $
          reasons = reasons + ' sigma>max'
        if abs(ppxf_v) gt ppxf_v_max then $
          reasons = reasons + ' |V|>max'
        if ppxf_nz lt ppxf_min_templates then $
          reasons = reasons + ' nz<min'
        if ppxf_chi2 gt ppxf_chi2_max then $
          reasons = reasons + ' chi2/dof>max'
        if ppxf_sigma_err le 0 then begin
          reasons = reasons + ' sigma_err<=0'
        endif else begin
          if ppxf_sigma_snr lt ppxf_sigma_snr_min then $
            reasons = reasons + ' sigma/sigma_err<min'
        endelse
        if reasons eq '' then begin
          ppxf_ok = 1
          ppxf_msg = 'accepted'
          sol_star = [ppxf_v, ppxf_sigma, 0.0d, 0.0d, 0.0d, 0.0d]
        endif else begin
          ppxf_msg = 'rejected:' + reasons + ' (V=' + $
              strtrim(string(ppxf_v, format='(F9.3)'), 2) + ' km/s, sigma=' + $
              strtrim(string(ppxf_sigma, format='(F9.3)'), 2) + ' km/s, ' + $
              'sigma_err=' + strtrim(string(ppxf_sigma_err, format='(F9.3)'), 2) + $
              ' km/s, nz=' + strtrim(string(ppxf_nz), 2) + ', chi2/dof=' + $
              strtrim(string(ppxf_chi2, format='(F9.3)'), 2) + ')'
        endelse
      endelse
    endif else begin
      ppxf_msg = 'rejected: too few good pixels for PPXF'
    endelse
  endif
  if not ppxf_ok then begin
    sol_star = [fixed_v, fixed_sigma, 0.0d, 0.0d, 0.0d, 0.0d]
    print, 'gandalf_line: using fixed stellar kinematics V=', fixed_v, $
           ' sigma=', fixed_sigma, ' (', ppxf_msg, ')'
  endif else begin
    print, 'gandalf_line: using PPXF stellar kinematics V=', ppxf_v, $
           ' +/- ', ppxf_v_err, ' sigma=', ppxf_sigma, ' +/- ', $
           ppxf_sigma_err, ' ntemp=', ppxf_nz
  endelse

  ; ------------------------------------------------------------------
  ; 2) Unmask the lines to be fitted; keep sky/NaD/weak lines masked
  ; ------------------------------------------------------------------
  mask_only = ['sky', 'NaI', 'NI5198', 'NI5200', 'HeII4686', 'ArIV4711']
  for i = 0, n_elements(emission_setup.i)-1 do begin
    if (emission_setup.action[i] eq 'm') then begin
      nm = strtrim(emission_setup.name[i], 2)
      if (total(nm eq mask_only) eq 0) then emission_setup.action[i] = 'f'
    endif
  endfor
  ; drop main lines tied to a reference that is not itself being fitted
  ; (e.g. [O II] tied to [O III] when the red edge cuts through [O III])
  for ipass = 1, 3 do begin
    for ii = 0, n_elements(emission_setup.i)-1 do begin
      if (emission_setup.action[ii] eq 'f') then begin
        fk = strmid(emission_setup.fit[ii], 0, 1)
        if (fk eq 't' or fk eq 'v' or fk eq 's') then begin
          k_ref = fix(strmid(emission_setup.fit[ii], 1))
          wr = where(emission_setup.i eq k_ref and emission_setup.action eq 'f')
          if (wr[0] eq -1) then emission_setup.action[ii] = 'i'
        endif
      endif
    endfor
  endfor
  ; drop satellite lines whose main line is not in the fit
  for ii = 0, n_elements(emission_setup.i)-1 do begin
    if (strmid(emission_setup.kind[ii], 0, 1) eq 'd') then begin
      k_mline = fix(strmid(emission_setup.kind[ii], 1))
      wm = where(emission_setup.i eq k_mline and emission_setup.action eq 'f')
      if (wm[0] eq -1) then emission_setup.action[ii] = 'i'
    endif
  endfor
  ; goodpixels for GANDALF: mask sky/NaD/weak lines, keep all fit lines
  gp = mask_emission_lines(npix, 0.0d, emission_setup, velscale, $
       l0_gal, lstep_gal, sigma=gandalf_mask_sigma, /log10)
  keep = bytarr(npix)
  keep[gp] = 1
  goodpixels = where(keep and (mask_arr gt 0))
  print, 'gandalf_line: ', n_elements(goodpixels), ' good pixels for GANDALF'

  ; keep only the lines actually fitted
  i_f = where(emission_setup.action eq 'f')
  if (i_f[0] eq -1) then message, 'no emission lines left to fit'
  dummy = emission_setup
  emission_setup = create_struct('i', dummy.i[i_f], 'name', dummy.name[i_f], $
      'lambda', dummy.lambda[i_f], 'action', dummy.action[i_f], $
      'kind', dummy.kind[i_f], 'a', dummy.a[i_f], 'v', dummy.v[i_f], $
      's', dummy.s[i_f], 'fit', dummy.fit[i_f])
  emission_setup.v = sol_star[0] - offset + emission_setup.v
  print, 'gandalf_line: fitting ', emission_setup.name

  ; ------------------------------------------------------------------
  ; 3) Native GANDALF fit with formal errors
  ; ------------------------------------------------------------------
  sol = sol_star
  GANDALF, templates, galaxy, error, velscale, sol, emission_setup, $
      l0_gal, lstep_gal, GOODPIXELS=goodpixels, MDEGREE=mdegree, DEGREE=degree, $
      INT_DISP=int_disp, BESTFIT=bestfit, EMISSION_TEMPLATES=emission_templates, $
      WEIGHTS=weights, ERROR=esol, FOR_ERRORS=1, /LOG10, L0_TEMPL=l0_templ, $
      QUIET=0

  ; ------------------------------------------------------------------
  ; 4) Outputs
  ; ------------------------------------------------------------------
  emission = total(emission_templates, 2)
  resid = galaxy - bestfit
  writefits, output + '/gandalf_fit.fits', galaxy, hdr_gal
  writefits, output + '/gandalf_fit.fits', bestfit, /append
  writefits, output + '/gandalf_fit.fits', emission, /append
  writefits, output + '/gandalf_fit.fits', resid, /append
  writefits, output + '/gandalf_fit.fits', goodpixels, /append
  writefits, output + '/gandalf_fit.fits', weights, /append
  writefits, output + '/gandalf_fit.fits', sol_star, /append
  writefits, output + '/gandalf_fit.fits', sol, /append
  writefits, output + '/gandalf_fit.fits', esol, /append
  writefits, output + '/gandalf_fit.fits', emission_templates, /append

  i_l = where(emission_setup.kind eq 'l')
  nlines = n_elements(i_l)
  openw, lun, output + '/gandalf_lines_raw.csv', /get_lun
  printf, lun, 'name,lambda_rest,flux,eflux,ampl,eampl,vel,evel,sigma,esigma,snr,fit_kind,kind'
  for k = 0, nlines-1 do begin
    j = i_l[k]
    if (esol[4*k] gt 0) then snr = sol[4*k]/esol[4*k] else $
      if (esol[4*k+1] gt 0) then snr = sol[4*k+1]/esol[4*k+1] else snr = 0.0d
    line = strtrim(emission_setup.name[j], 2) + ',' + $
        strtrim(string(emission_setup.lambda[j], format='(F12.4)'), 2) + ',' + $
        strtrim(string(sol[4*k], format='(E16.8)'), 2) + ',' + $
        strtrim(string(esol[4*k], format='(E16.8)'), 2) + ',' + $
        strtrim(string(sol[4*k+1], format='(E16.8)'), 2) + ',' + $
        strtrim(string(esol[4*k+1], format='(E16.8)'), 2) + ',' + $
        strtrim(string(sol[4*k+2], format='(F12.4)'), 2) + ',' + $
        strtrim(string(esol[4*k+2], format='(F12.4)'), 2) + ',' + $
        strtrim(string(sol[4*k+3], format='(F12.4)'), 2) + ',' + $
        strtrim(string(esol[4*k+3], format='(F12.4)'), 2) + ',' + $
        strtrim(string(snr, format='(F12.4)'), 2) + ',' + $
        strtrim(emission_setup.fit[j], 2) + ',' + strtrim(emission_setup.kind[j], 2)
    printf, lun, line
  endfor
  free_lun, lun

  openw, lun, output + '/gandalf_meta.txt', /get_lun
  printf, lun, 'ppxf_attempted=' + strtrim(string(ppxf_attempted), 2)
  printf, lun, 'ppxf_ok=' + strtrim(string(ppxf_ok), 2)
  printf, lun, 'ppxf_message=' + ppxf_msg
  printf, lun, 'ppxf_npix=' + strtrim(string(ppxf_npix), 2)
  printf, lun, 'ppxf_v=' + strtrim(string(ppxf_v, format='(E16.8)'), 2)
  printf, lun, 'ppxf_sigma=' + strtrim(string(ppxf_sigma, format='(E16.8)'), 2)
  printf, lun, 'ppxf_v_err=' + strtrim(string(ppxf_v_err, format='(E16.8)'), 2)
  printf, lun, 'ppxf_sigma_err=' + strtrim(string(ppxf_sigma_err, format='(E16.8)'), 2)
  printf, lun, 'ppxf_sigma_snr=' + strtrim(string(ppxf_sigma_snr, format='(E16.8)'), 2)
  printf, lun, 'ppxf_chi2=' + strtrim(string(ppxf_chi2, format='(E16.8)'), 2)
  printf, lun, 'ppxf_nz=' + strtrim(string(ppxf_nz), 2)
  printf, lun, 'stellar_v=' + strtrim(string(sol_star[0], format='(E16.8)'), 2)
  printf, lun, 'stellar_sigma=' + strtrim(string(sol_star[1], format='(E16.8)'), 2)
  printf, lun, 'npix=' + strtrim(string(npix), 2)
  printf, lun, 'ntemp=' + strtrim(string((size(templates))[2]), 2)
  printf, lun, 'nlines=' + strtrim(string(nlines), 2)
  printf, lun, 'ngood=' + strtrim(string(n_elements(goodpixels)), 2)
  printf, lun, 'l0_gal=' + strtrim(string(l0_gal, format='(E16.8)'), 2)
  printf, lun, 'lstep_gal=' + strtrim(string(lstep_gal, format='(E16.8)'), 2)
  printf, lun, 'velscale=' + strtrim(string(velscale, format='(E16.8)'), 2)
  free_lun, lun
  print, 'gandalf_line: wrote outputs to ' + output
end
