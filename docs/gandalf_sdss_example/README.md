# GANDALF SDSS-example validation

This directory contains a validation run of `Tools/gandalf_line/` on the
public GANDALF v1.5 SDSS example `spSpec-51908-0277-120.fit` (z=0.0859), not on
the repository's eFEDS QSO target.  It demonstrates the H-alpha / [N II]
branch, which is outside the observed coverage of the z=0.587 target.

Command (from the repository root):

```bash
cp /tmp/gandalf_release_v1.5/SDSS_example/spSpec-51908-0277-120.fit /tmp/gandalf_sdss_in/spectrum.fits
bash Pipelines/run_gandalf_line_docker.sh /tmp/gandalf_sdss_in /tmp/gandalf_sdss_out gandalf_sdss_51908
```

The committed files are the line table, fit figure and run summary from that
temporary output directory.  PPXF accepted the
stellar kinematics (V=75.9 km/s, sigma=62.9 km/s, 7 templates, chi2=0.605)
and the GANDALF gas fit reached residual chi2_nu=0.852.
