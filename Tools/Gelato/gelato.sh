#!/bin/bash

INPUT=/app/input
BASE=/app/GELATO/Convenience
JSON=my_sdss.json
FITS=my_sdss.fits

# Per-object redshift: read it from the prepared FITS (HDU2 'z' column, written
# by pipeline/prepare_inputs.py).  The original script hardcoded z=0.3482135 for
# its single target, which silently fit *every* object at the wrong redshift.
z="${GELATO_Z:-}"
if [ -z "$z" ]; then
  z=$(python -c "from astropy.io import fits; d=fits.open('$INPUT/$FITS'); print(float(d[2].data['z'][0]))" 2>/dev/null)
fi
if [ -z "$z" ]; then
  echo "ERROR: could not determine GELATO redshift from $INPUT/$FITS" >&2
  exit 1
fi
echo "GELATO: z=$z  json=$JSON  fits=$FITS"

python $BASE/runGELATO.py $INPUT/$JSON --single $INPUT/$FITS $z
# For a single plot
# python $BASE/plotResults.py $INPUT/$JSON --single $INPUT/$FITS $z
# For a single EW
# python $BASE/ewResults.py $INPUT/$JSON --single $INPUT/$FITS $z
# To generate the results file with a single spectrum
# python $BASE/concatResults.py $INPUT/$JSON --single $INPUT/$FITS $z
