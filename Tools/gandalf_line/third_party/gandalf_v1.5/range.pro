;----------------------------------------------------------------------
FUNCTION range, x1, x2, n, OPEN=open
compile_opt idl2
on_error, 2
;
; RANGE(x1,x2) = x1,x1+1,...,x2. In this case x1, x2 should be integers.
; RANGE(x1,x2,n) = x1,x1+dx,...,x2 with N integer the result has length N.
; The result will have the type of x1, but if three parameters are used
; the result will be at least of type float.
; Use keyword /OPEN to exclude the extremes of the interval.
;
; EXAMPLE:
;   IDL> print, range(0,1,5)
;       0.000000  0.250000  0.500000  0.750000  1.00000
;   IDL> print, range(0,1,5,/OPEN)
;       0.100000  0.300000  0.500000  0.700000  0.90000
;
; V1.0: Michele Cappellari, Leiden, 16 October 2001
; V1.1: added /OPEN keyword, MC, Leiden, 9 March 2003

t = size(x1,/TYPE)
if keyword_set(open) then $ ; Open interval: excluding the extremes
    v = x1 + (x2-x1)*(0.5+indgen(n, TYPE=t))/n $
else $
    case n_params() of
        2: if x1 lt x2 then $
                v = x1 + indgen(x2-x1+1, TYPE=t) $
            else $
                v = x1 - indgen(x1-x2+1, TYPE=t)
        3: v = x1 + (x2-x1)/(n-1.0)*indgen(n, TYPE=t)
        else: message, '2 or 3 parameters are needed'
    endcase

return, v
END
;----------------------------------------------------------------------
