#!/bin/bash

# Runtime patch: tie the [OIII] and [NII] doublets (GLEAM has no ratio option).
python3 /app/input/gleam_doublet_patch.py || echo "WARNING: GLEAM doublet patch failed"

# Options:
#   --path TEXT      Path to recursively look for metadata files and spectra.
#   --spectra TEXT   Filter for spectra file paths.
#   --config TEXT    Configuration file in YAML format.
#   --plot           Save plots of spectrum with emission lines fits.
#   --verbose        Print full output from LMFIT.
#   --nproc INTEGER  Number of threads.
gleam --config /app/input/gleamconfig.yaml --path /app/input/ --spectra spec1d.sdss.sdss.fiber1.1.fits --nproc 1 --verbose --plot

# --- Diagnostics: Check the installed NumPy version (Keep this for debugging) ---
python3 -c "import matplotlib; print(f'Matplotlib Version: {matplotlib.__version__}')"
# -------------------------------------------------------------------------------
# GLEAM writes its per-line results table (linefits*.fits) and plots relative to
# the current directory; move them into the mounted /app/output so they survive.
mv /linefits*.fits /app/output/ 2>/dev/null || true
mv /app/input/linefits*.fits /app/output/ 2>/dev/null || true
mv /*.png /app/output/ 2>/dev/null || true
mv /app/input/*.png /app/output/ 2>/dev/null || true
ls -l /app/output
