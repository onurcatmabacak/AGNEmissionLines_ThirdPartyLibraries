from astropy.io import fits
import numpy as np

file = 'ExampleObjList.fits'
hdulist = fits.open(file)
header = hdulist[0].header

print(header)

print(hdulist.info())

for key, val in header.items():
    print(f"{key:8} = {val}")

for i, hdu in enumerate(hdulist):
    print(f"\n=== HDU {i}: {hdu.name} ===")
    for key, value in hdu.header.items():
        print(f"{key} = {value}")

cols = hdulist[1].columns
for col in cols:
    print(f"{col.name}: format={col.format}, unit={col.unit}")
