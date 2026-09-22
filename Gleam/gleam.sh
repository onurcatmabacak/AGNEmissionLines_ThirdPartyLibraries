#!/bin/bash

# Options:
#   --path TEXT      Path to recursively look for metadata files and spectra.
#                    See --spectra for overrides.
#   --spectra TEXT   Filter for spectra file paths. e.g.
#                    "./**/spec1d.Cosmos.Keck.P1.*.fits" to select all sources
#                    in the Cosmos sample observed with Keck in pointing P1.
#   --config TEXT    Configuration file in YAML format.
#   --plot           Save plots of spectrum with emission lines fits next to the
#                    corresponding spectrum file.
#   --inspect        Show interactive plots.
#   --verbose        Print full output from LMFIT.
#   --bin INTEGER    Bin the spectrum before fitting.
#   --nproc INTEGER  Number of threads.
#   --help           Show this message and exit.

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