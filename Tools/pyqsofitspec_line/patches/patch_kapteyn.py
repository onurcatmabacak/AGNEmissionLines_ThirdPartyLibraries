"""Build-only patch: compile only the `kmpfit` extension of kapteyn 3.4.

kapteyn 3.4's `wcs`/`ascarray`/`profiles` extensions declare the NumPy C API
with their own `src/c_numpy.pxd` (`void import_array()`), which no longer
compiles against numpy >= 1.25.  PyQSOFitSpec only imports
`from kapteyn import kmpfit`, and `kapteyn/__init__.py` does not import the
other submodules, so dropping those extensions is sufficient.
"""
import sys
from pathlib import Path

p = Path(sys.argv[1]) / "setup.py"
src = p.read_text()
old = "    return cythonize(extensions)"
new = ("    # pyqsofitspec_line: kmpfit-only build (see patch_kapteyn.py)\n"
       "    extensions = [e for e in extensions if e.name in ('kmpfit',)]\n"
       "    return cythonize(extensions)")
assert src.count(old) == 1, "unexpected setup.py layout"
p.write_text(src.replace(old, new))
print("patched", p)
