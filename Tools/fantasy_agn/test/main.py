from astropy.io import fits

file_path = "spec-2770-54510-0433.fits"  # Update with your actual path

# try:
#     with fits.open(file_path) as hdulist:
#         hdulist.info()  # Print file structure
# except Exception as e:
#     print(f"Error: {e}")

hdulist = fits.open(file_path, ignore_missing_simple=True, ignore_missing_end=True)
hdu = hdulist[1]
data = hdu.data
print(hdu, "\n\n", data)