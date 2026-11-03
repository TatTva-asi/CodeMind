import ast

from app.parsing.import_extractor import ImportExtractor


def test_import_aliases():
    source = """
import numpy as np
from pathlib import Path
from app.utils import helper as h
"""

    imports = ImportExtractor().extract(
        ast.parse(source)
    )

    assert imports[0].aliases == {
        "np": "numpy"
    }

    assert imports[1].aliases == {
        "Path": "Path"
    }

    assert imports[2].aliases == {
        "h": "helper"
    }