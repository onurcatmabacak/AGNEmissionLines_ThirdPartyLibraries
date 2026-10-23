;----------------------------------------------------------------------
function cap_diff, a
on_error, 2
;
; Emulates the matlab function diff(a).
; This function works for both vectors and arrays.
; V1.0: Michele Cappellari, Oxford, 23 October 2007
; V1.1: Simplified code. MC, Oxford, 1 November 2011
; V1.11: Renamed CAP_DIFF to avoid potential naming conflicts.
;    MC, Paranal, 8 November 2013

s = size(a)
case s[0] of
    1 : d = a[1:*] - a
    2 : d = a[*,1:*] - a
endcase

return, d
end
;----------------------------------------------------------------------
