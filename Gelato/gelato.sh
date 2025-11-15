#!/bin/bash

INPUT=/app/input
z=0.3482135
BASE=/app/GELATO/Convenience
JSON=my_sdss.json
FITS=my_sdss.fits

python $BASE/runGELATO.py $INPUT/$JSON --single $INPUT/$FITS $z
# For a single plot
# python $BASE/plotResults.py $INPUT/$JSON --single $INPUT/$FITS $z
# For a single EW
# python $BASE/ewResults.py $INPUT/$JSON --single $INPUT/$FITS $z
# To generate the results file with a single spectrum
# python $BASE/concatResults.py $INPUT/$JSON --single $INPUT/$FITS $z