from pathlib import Path
import tempfile

import numpy as np
from astropy.io import fits

from pipeline.prepare_inputs import read_spectrum, write_pyqsofit


