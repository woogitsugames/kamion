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


def metric_patch_field(east, north, scale_m=6.0, salt=17):
    """Smooth deterministic metre-scale variation anchored in world coordinates.

    Small / large arrays sample the same field, so chunking cannot create seams.
    Four integer hashes per coarse-cell sample, with separable smooth interpolation.
    """
    x, y = np.asarray(east, np.float32) / scale_m, np.asarray(north, np.float32) / scale_m
    ix, iy = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    def hashed(dx, dy):
        h = ((ix[None, :] + dx).astype(np.uint32) * np.uint32(1597334677)
             ^ (iy[:, None] + dy).astype(np.uint32) * np.uint32(3812015801) ^ np.uint32(salt))
        h ^= h >> np.uint32(16)
        h *= np.uint32(2246822519)
        return (h & np.uint32(0xFFFFFF)).astype(np.float32) / float(0xFFFFFF)
    a, b = hashed(0, 0), hashed(1, 0)
    c, d = hashed(0, 1), hashed(1, 1)
    return ((a + (b - a) * fx[None, :]) * (1 - fy[:, None])
            + (c + (d - c) * fx[None, :]) * fy[:, None]).astype(np.float32)


def osm_tree_species(tags, default="linden"):
    """Use explicit OSM botanical tags; unspecified species remain WORKING_VALUE."""
    text = " ".join(str(tags.get(k, "")) for k in ("species", "genus", "species:pl", "species:en")).casefold()
    for species, names in {"pine": ("pinus", "pine", "sosna"), "birch": ("betula", "birch", "brzoza"),
                           "linden": ("tilia", "linden", "lipa"), "maple": ("acer", "maple", "klon"),
                           "alder": ("alnus", "alder", "olsza", "olcha")}.items():
        if any(name in text for name in names):
            return species
    return default
