import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core import checksum_vector  # noqa: E402
from leaf import label  # noqa: E402


def test_checksum_vector():
    assert checksum_vector(5) == 10.0


def test_label():
    assert label().startswith("leaf-v")
