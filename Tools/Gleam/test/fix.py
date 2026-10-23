from astropy.io import fits
import astropy.units as u

# --- Configuration ---
spectrum_file = '../spec1d.sdss.sdss.fiber1.1.fits'
wl_column_name = 'wl'  # Wavelength column name (e.g., 'wl')
flux_column_name = 'flux' # 👈 ADDED: Flux column name (e.g., 'flux') 
wl_unit = 'Angstrom'    # Wavelength unit
# 👈 ADDED: Standard flux unit for optical spectra
flux_unit = 'erg / (s cm2 Angstrom)' 
# Note: You may need to adjust the exact flux unit string based on your specific FITS convention.
# For example, some files use a scaling factor like '1e-17 erg...' directly in the unit string.

# Open the file and access the table extension
hdul = fits.open(spectrum_file, mode='update')
data_hdu = hdul[1] # Assuming the spectrum is in the second HDU (where the table data is)
col_names = [col.name for col in data_hdu.columns]

# --- 1. Set Wavelength Unit (wl) ---
try:
    wl_col_index = col_names.index(wl_column_name) + 1
    wl_tunit_keyword = f'TUNIT{wl_col_index}'
    data_hdu.header[wl_tunit_keyword] = wl_unit
    print(f"Set {wl_tunit_keyword} ({wl_column_name}) in {spectrum_file} to '{wl_unit}'.")
except ValueError:
    print(f"Error: Wavelength Column '{wl_column_name}' not found.")

# --- 2. Set Flux Unit (flux) ---
try:
    flux_col_index = col_names.index(flux_column_name) + 1
    flux_tunit_keyword = f'TUNIT{flux_col_index}'
    data_hdu.header[flux_tunit_keyword] = flux_unit
    print(f"Set {flux_tunit_keyword} ({flux_column_name}) in {spectrum_file} to '{flux_unit}'.")
except ValueError:
    print(f"Error: Flux Column '{flux_column_name}' not found.")


# --- Save Changes ---
hdul.flush()
hdul.close()

print("\nFITS file headers updated successfully.")