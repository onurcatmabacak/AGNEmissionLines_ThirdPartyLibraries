"""Compatibility shim for PyQSOFitSpec's ``import sfdmap``.

Upstream PyQSOFitSpec pins ``sfdmap==0.1.1`` (requirement_old.txt) / lists
``sfdmap==0.1.1`` in requirement.txt.  That release does not install on modern
Python.  ``sfdmap2`` is the maintained fork used by the sibling ``pyqsofit_uv``
image and exposes the same ``SFDMap`` class, so this module re-exports it under
the legacy module name.

Galactic dereddening is disabled in the default pyqsofitspec_line config, so
the SFD dust-map data are never loaded during a run.
"""
from sfdmap2.sfdmap import *  # noqa: F401,F403
from sfdmap2 import sfdmap as _impl

SFDMap = _impl.SFDMap
