# GANDALF low-z SDSS production validation

This directory mirrors the headline products of the canonical low-z run of
`Tools/gandalf_line/` on the public GANDALF v1.5 SDSS example
`spSpec-51908-0277-120.fit` (z=0.0858772).  The authoritative, complete output
is `outputs/gandalf_line/spSpec-51908-0277-120_z_0.0859/`; the raw input and
provenance are in `inputs/spSpec-51908-0277-120_z_0.0859/`.

The copied files are `gandalf_lines.csv`, `gandalf_fit.png`, `run.json` and
`line_yield_summary.txt`.  Regenerate all of them with:

```bash
.venv/bin/python pipeline/run_new_tools.py \
  --only spSpec-51908-0277-120_z_0.0859 --tools gandalf_line --force
```

Result: pPXF accepted the stellar kinematics (V=72.54 +/- 6.50 km/s,
sigma=79.87 +/- 9.80 km/s, 5 nonzero templates, chi2/dof=0.720, 3439 good
pixels), and the native GANDALF gas fit reached residual chi2_nu=0.847.
H-alpha is measured at 1390.85 +/- 16.86 and H-beta at 244.00 +/- 4.43
(1e-17 erg s^-1 cm^-2).  GDL runtime is 70.6 s; pipeline wall time is 81.7 s
(59-71 s GDL across repeated runs, depending on host load).
