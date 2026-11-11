"""ADR0088: reproducible canopy openings and stable leaf-card LOD selection.

These are WORKING_VALUE art parameters, verified against photographed silhouettes,
not a botanical measurement. Geometry and triangle counts are measured separately.
"""
from __future__ import annotations

import math
import numpy as np


def crown_opening(position, centre, height, phase):
    """Two coherent small windows between branch groups, not per-leaf salt noise."""
    x, y, z = (float(position[i] - centre[i]) / height for i in range(3))
    if math.hypot(x, y) < .045:
        return False  # keep foliage hugging the stem; a birch must not become a bare pole
    angle = math.atan2(y, x) + phase
    band = z - .075 * math.sin(angle * 1.3 + phase)
    return math.cos(2 * angle) > .70 and -.13 < band < .12


def leaf_lod_indices(count, seed, share=.40):
    """LOD1 reuses the exact LOD0 candidate positions; stable independent seed."""
    if count <= 0:
        return np.zeros(0, dtype=int)
    rng = np.random.default_rng(seed)
    chosen = np.flatnonzero(rng.random(count) < share)
    return chosen if len(chosen) else np.array([count // 2], dtype=int)
