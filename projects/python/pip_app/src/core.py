"""A "widely depended" core module (spec §4.1) — uses numpy (a real C-extension dependency) so
pip's download/install step has real, measurable weight worth caching."""
import numpy as np


def checksum_vector(n: int) -> float:
    return float(np.arange(n, dtype=np.float64).sum())
