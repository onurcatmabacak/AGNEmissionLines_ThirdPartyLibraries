from astropy.io import fits
import numpy as np

# Open the existing FITS file
with fits.open('my_sdss.fits') as hdul:
    # Assume the binary table is in extension 1
    table_hdu = hdul[1]

    # Verify that extension 1 is a binary table
    if not isinstance(table_hdu, fits.BinTableHDU):
        raise ValueError("Extension 1 is not a binary table.")
    
    # Check if 'and_mask' already exists to avoid overwriting
    if 'and_mask' in table_hdu.columns.names:
        raise ValueError("Column 'and_mask' already exists in the table.")
    
    # Get the number of rows in the table
    n_rows = len(table_hdu.data)
    
    # Create a new mask array, initialized to zeros (customize as needed)
    mask_data = np.zeros(n_rows, dtype=np.int32)
    
    # Define the new column for 'and_mask' (32-bit integer format 'J')
    mask_col = fits.Column(name='and_mask', format='J', array=mask_data)
    
    # Combine existing columns with the new 'and_mask' column
    new_columns = table_hdu.columns + mask_col
    
    # Create a new binary table HDU with the updated columns
    new_table_hdu = fits.BinTableHDU.from_columns(new_columns)
    
    # Replace the old table with the updated one
    hdul[1] = new_table_hdu
    
    # Save to a new FITS file (use overwrite=True to modify the original cautiously)
    hdul.writeto('my_sdss_onur.fits', overwrite=True)