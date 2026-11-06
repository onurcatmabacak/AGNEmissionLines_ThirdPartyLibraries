import csv
import json
from pathlib import Path

import pytest

from pipeline.io_layout import iter_sources
from pipeline.validate_outputs import validate


def _rows(path, key="line"):
    with path.open(newline="") as fh:
        return {r[key]: r for r in csv.DictReader(fh)}


