function mask_emission_lines,npix,Vsys,emission_setup,velscale,l0_gal,lstep_gal,sigma=sigma,log10=log10
c = 299792.458d
goodpixels = range(0,npix-1)
tmppixels = goodpixels
for i = 0,n_elements(emission_setup.i)-1 do begin
    if (emission_setup.action[i] eq 'm') then begin
        print,'--> masking ' + emission_setup.name[i]
        if (emission_setup.name[i] ne 'sky') then $
          meml_cpix = ceil((alog(emission_setup.lambda[i])-l0_gal)/lstep_gal+Vsys/velscale)
        if (emission_setup.name[i] ne 'sky' and keyword_set(log10)) then $
          meml_cpix = ceil((alog10(emission_setup.lambda[i])-l0_gal)/lstep_gal+Vsys/velscale)
        if (emission_setup.name[i] eq 'sky') then $
          meml_cpix = ceil((alog(emission_setup.lambda[i])-l0_gal)/lstep_gal)
        if (emission_setup.name[i] eq 'sky' and keyword_set(log10)) then $
          meml_cpix = ceil((alog10(emission_setup.lambda[i])-l0_gal)/lstep_gal)
        if keyword_set(sigma) then msigma = 3*sigma/velscale
        if not keyword_set(sigma) then msigma = 3*emission_setup.s[i]/velscale
        meml_bpix = meml_cpix - msigma
        meml_rpix = meml_cpix + msigma
        ; A wide PPXF mask can overlap the array edge even when the line
        ; centre is outside.  Test the centre explicitly, otherwise such a
        ; line would later be fitted outside the prepared window.
        if (meml_cpix lt min(goodpixels) or meml_cpix gt max(goodpixels)) then begin
            print,'this line is outside your wavelength range. We shall ignore it'
            emission_setup.action[i] = 'i'
        endif else begin
            w = where(goodpixels ge meml_bpix and goodpixels le meml_rpix)
            if (w[0] ne -1) then tmppixels[w] = -1
        endelse
    endif
endfor
w = where(tmppixels ne -1)
goodpixels = goodpixels[w]
return,goodpixels
end
