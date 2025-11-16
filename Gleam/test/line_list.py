from astropy.table import Table
import astropy.units as u

# --- Line Data ---
wavelengths = [3727, 4861, 4959, 5007, 6563, 6583, 6716, 6731] * u.Angstrom
lines = ["OII", "Hb", "OIII4", "OIII5", "Ha", "NII1", "SII1", "SII2"]

# LaTeX labels for pretty plotting (required by gleam)
latex = [
    r"[OII] $\lambda3727$",
    r"H$\beta$",
    r"[OIII] $\lambda4959$",
    r"[OIII] $\lambda5007$",
    r"H$\alpha$",
    r"[NII] $\lambda6583$",
    r"[SII] $\lambda6716$",
    r"[SII] $\lambda6731$",
]

# Build the table
t = Table()
t["wavelength"] = wavelengths        # must be float (no units)
t["line"] = lines                    # gleam requires column named "line"
t["latex"] = latex                   # gleam requires this for plots

# Save
t.write("../line_table.fits", overwrite=True)

print("Line table written to ../line_table.fits")


print("Successfully generated line_table.fits with 'line' and 'wavelength' columns.")
print("The file is ready for use with gleam.")


t = Table.read("../line_table.fits")
print(t.colnames)
print(t["wavelength"].dtype)
print(getattr(t["wavelength"], 'unit', None))