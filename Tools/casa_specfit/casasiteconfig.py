# CASA site config: never try to auto-download measures/IERS data at import.
#
# The conda-forge casatools build attempts a network data update on first
# import, and that endpoint returned HTTP 500 during the image build.  With
# auto-updates off, imports are deterministic and offline; the measures tables
# are only needed for coordinate/time conversions, which this tool does not use
# (it fits a spectrum extracted from a FITS cube).
measures_auto_update = False
data_auto_update = False
